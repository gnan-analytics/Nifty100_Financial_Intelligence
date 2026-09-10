from __future__ import annotations

import re
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]

INPUT_PATH = PROJECT_ROOT / "data" / "raw" / "core" / "analysis.xlsx"
PARSED_OUTPUT_PATH = PROJECT_ROOT / "output" / "analysis_parsed.csv"
FAILURE_OUTPUT_PATH = PROJECT_ROOT / "output" / "parse_failures.csv"


TARGET_FIELDS = [
    "compounded_sales_growth",
    "compounded_profit_growth",
    "stock_price_cagr",
    "roe",
]


# Sprint 5 required pattern:
# (\d+)\s*Years?:?\s*([\d.]+)%
#
# Extended slightly with optional +/- so real source values such as
# "1 Year: -2%" can also be parsed correctly.
YEAR_VALUE_PATTERN = re.compile(
    r"(\d+)\s*Years?\s*:?\s*([+-]?[\d.]+)\s*%",
    flags=re.IGNORECASE,
)


def parse_metric_text(text: object) -> tuple[int, float] | None:
    """
    Parse text such as:
        10 Years: 21%
        5 Years:       24%
        1 Year: -2%

    Returns:
        (period_years, value_pct)

    Returns None for unsupported formats such as:
        TTM: 43%
        Last Year: 12%
    """
    if pd.isna(text):
        return None

    text = str(text).strip()

    match = YEAR_VALUE_PATTERN.search(text)

    if not match:
        return None

    period_years = int(match.group(1))
    value_pct = float(match.group(2))

    return period_years, value_pct


def load_analysis() -> pd.DataFrame:
    """Load analysis."""
    if not INPUT_PATH.exists():
        raise FileNotFoundError(f"Input file not found: {INPUT_PATH}")

    df = pd.read_excel(INPUT_PATH, header=1)

    required_columns = {"company_id", *TARGET_FIELDS}
    missing = required_columns - set(df.columns)

    if missing:
        raise ValueError(f"analysis.xlsx missing required columns: {sorted(missing)}")

    df["company_id"] = df["company_id"].astype(str).str.strip().str.upper()

    return df


def parse_analysis(
    df: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Parse analysis."""
    parsed_rows: list[dict] = []
    failure_rows: list[dict] = []

    for _, row in df.iterrows():
        company_id = row["company_id"]

        for metric_type in TARGET_FIELDS:
            raw_text = row[metric_type]

            result = parse_metric_text(raw_text)

            if result is None:
                failure_rows.append(
                    {
                        "company_id": company_id,
                        "metric_type": metric_type,
                        "raw_text": raw_text,
                        "failure_reason": "NO_YEAR_VALUE_PATTERN_MATCH",
                    }
                )
                continue

            period_years, value_pct = result

            parsed_rows.append(
                {
                    "company_id": company_id,
                    "metric_type": metric_type,
                    "period_years": period_years,
                    "value_pct": value_pct,
                }
            )

    parsed_df = pd.DataFrame(
        parsed_rows,
        columns=[
            "company_id",
            "metric_type",
            "period_years",
            "value_pct",
        ],
    )

    failures_df = pd.DataFrame(
        failure_rows,
        columns=[
            "company_id",
            "metric_type",
            "raw_text",
            "failure_reason",
        ],
    )

    return parsed_df, failures_df


def validate_outputs(
    source_df: pd.DataFrame,
    parsed_df: pd.DataFrame,
    failures_df: pd.DataFrame,
) -> None:
    """Validate outputs."""
    expected_entries = len(source_df) * len(TARGET_FIELDS)

    actual_entries = len(parsed_df) + len(failures_df)

    if actual_entries != expected_entries:
        raise AssertionError(
            f"Entry count mismatch: expected {expected_entries}, "
            f"got {actual_entries}"
        )

    if not parsed_df.empty:
        if parsed_df["company_id"].isna().any():
            raise AssertionError("Parsed output contains missing company_id")

        if parsed_df["metric_type"].isna().any():
            raise AssertionError("Parsed output contains missing metric_type")

        if parsed_df["period_years"].isna().any():
            raise AssertionError("Parsed output contains missing period_years")

        if parsed_df["value_pct"].isna().any():
            raise AssertionError("Parsed output contains missing value_pct")


def cross_validate_cagr(parsed_df: pd.DataFrame) -> pd.DataFrame:
    """
    Compare parsed Sales/Profit CAGR values against the Ratio Engine.

    Mapping:
        compounded_sales_growth  -> revenue_cagr_Nyr
        compounded_profit_growth -> pat_cagr_Nyr

    Divergence greater than 5 percentage points is flagged for manual review.
    """
    import sqlite3

    db_path = PROJECT_ROOT / "db" / "nifty100.db"

    if not db_path.exists():
        raise FileNotFoundError(f"Database not found: {db_path}")

    validation_df = parsed_df[
        parsed_df["metric_type"].isin(
            [
                "compounded_sales_growth",
                "compounded_profit_growth",
            ]
        )
    ].copy()

    validation_df = validation_df[validation_df["period_years"].isin([3, 5, 10])].copy()

    with sqlite3.connect(db_path) as conn:
        ratios = pd.read_sql_query(
            """
            SELECT
                company_id,
                year,
                revenue_cagr_3yr,
                revenue_cagr_5yr,
                revenue_cagr_10yr,
                pat_cagr_3yr,
                pat_cagr_5yr,
                pat_cagr_10yr
            FROM financial_ratios
            """,
            conn,
        )

    if ratios.empty:
        validation_df["ratio_engine_year"] = pd.NA
        validation_df["computed_value_pct"] = pd.NA
        validation_df["divergence_pct_points"] = pd.NA
        validation_df["validation_status"] = "NO_COMPUTED_VALUE"
        return validation_df

    ratios["company_id"] = ratios["company_id"].astype(str).str.strip().str.upper()

    ratios["_year_dt"] = pd.to_datetime(
        ratios["year"],
        format="%Y-%m",
        errors="coerce",
    )

    # Prefer the latest March/full-year row.
    # Fall back to the latest available row if no March row exists.
    latest_rows = []

    for company_id, group in ratios.groupby("company_id"):
        group = group.sort_values("_year_dt", ascending=False)

        march = group[group["year"].astype(str).str.endswith("-03")]

        if not march.empty:
            latest_rows.append(march.iloc[0])
        elif not group.empty:
            latest_rows.append(group.iloc[0])

    if latest_rows:
        latest = pd.DataFrame(latest_rows)
    else:
        latest = ratios.iloc[0:0].copy()

    latest = latest.set_index("company_id")

    computed_values = []
    ratio_years = []
    divergences = []
    statuses = []

    for _, row in validation_df.iterrows():
        company_id = row["company_id"]
        metric_type = row["metric_type"]
        period = int(row["period_years"])
        parsed_value = float(row["value_pct"])

        if company_id not in latest.index:
            ratio_years.append(pd.NA)
            computed_values.append(pd.NA)
            divergences.append(pd.NA)
            statuses.append("NO_COMPUTED_VALUE")
            continue

        ratio_row = latest.loc[company_id]

        if isinstance(ratio_row, pd.DataFrame):
            ratio_row = ratio_row.iloc[0]

        if metric_type == "compounded_sales_growth":
            column = f"revenue_cagr_{period}yr"
        else:
            column = f"pat_cagr_{period}yr"

        computed = ratio_row.get(column, pd.NA)

        ratio_years.append(ratio_row.get("year", pd.NA))

        if pd.isna(computed):
            computed_values.append(pd.NA)
            divergences.append(pd.NA)
            statuses.append("NO_COMPUTED_VALUE")
            continue

        computed = float(computed)

        divergence = abs(parsed_value - computed)

        computed_values.append(round(computed, 4))
        divergences.append(round(divergence, 4))

        if divergence > 5.0:
            statuses.append("REVIEW_GT_5")
        else:
            statuses.append("MATCH")

    validation_df["ratio_engine_year"] = ratio_years
    validation_df["computed_value_pct"] = computed_values
    validation_df["divergence_pct_points"] = divergences
    validation_df["validation_status"] = statuses

    return validation_df[
        [
            "company_id",
            "metric_type",
            "period_years",
            "value_pct",
            "ratio_engine_year",
            "computed_value_pct",
            "divergence_pct_points",
            "validation_status",
        ]
    ]


def main() -> None:
    """Run the module entry point."""
    print("=" * 80)
    print("SPRINT 5 — DAY 29 ANALYSIS TEXT PARSER")
    print("=" * 80)

    source_df = load_analysis()

    parsed_df, failures_df = parse_analysis(source_df)

    validate_outputs(
        source_df,
        parsed_df,
        failures_df,
    )

    cross_validation_df = cross_validate_cagr(parsed_df)

    PARSED_OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    parsed_df.to_csv(
        PARSED_OUTPUT_PATH,
        index=False,
    )

    failures_df.to_csv(
        FAILURE_OUTPUT_PATH,
        index=False,
    )

    cross_validation_path = PROJECT_ROOT / "output" / "cagr_cross_validation.csv"

    cross_validation_df.to_csv(
        cross_validation_path,
        index=False,
    )

    print(f"\nSource rows:        {len(source_df)}")
    print(f"Metrics per row:    {len(TARGET_FIELDS)}")
    print(f"Total text entries: {len(source_df) * len(TARGET_FIELDS)}")
    print(f"Successfully parsed:{len(parsed_df):>5}")
    print(f"Parse failures:     {len(failures_df):>5}")

    print("\nPARSED COUNTS BY METRIC:")
    if not parsed_df.empty:
        print(parsed_df["metric_type"].value_counts().to_string())

    print("\nPARSED PERIODS:")
    if not parsed_df.empty:
        print(parsed_df["period_years"].value_counts().sort_index().to_string())

    print("\nFAILURE TYPES:")
    if not failures_df.empty:
        print(failures_df["metric_type"].value_counts().to_string())
    else:
        print("None")

    print("\nCAGR CROSS-VALIDATION:")
    if not cross_validation_df.empty:
        print(cross_validation_df["validation_status"].value_counts().to_string())

        review_count = cross_validation_df["validation_status"].eq("REVIEW_GT_5").sum()

        print(f"\nManual review flags (>5pp): {review_count}")

    print("\nOutputs:")
    print(PARSED_OUTPUT_PATH)
    print(FAILURE_OUTPUT_PATH)
    print(cross_validation_path)

    print("\nDAY 29 PARSER: PASS")


if __name__ == "__main__":
    main()
