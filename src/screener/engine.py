from pathlib import Path
import sqlite3

import numpy as np
import pandas as pd
import yaml


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DB_PATH = PROJECT_ROOT / "db" / "nifty100.db"
CONFIG_PATH = PROJECT_ROOT / "config" / "screener_config.yaml"


def load_config(config_path=CONFIG_PATH):
    with open(config_path, "r", encoding="utf-8") as file:
        return yaml.safe_load(file)


def load_latest_financial_ratios(conn):
    query = """
    WITH ranked AS (
        SELECT
            fr.*,
            ROW_NUMBER() OVER (
                PARTITION BY fr.company_id
                ORDER BY
                    CASE
                        WHEN fr.return_on_equity_pct IS NOT NULL THEN 0
                        ELSE 1
                    END,
                    fr.year DESC
            ) AS rn
        FROM financial_ratios fr
    )
    SELECT *
    FROM ranked
    WHERE rn = 1
    """

    df = pd.read_sql_query(query, conn)

    if "rn" in df.columns:
        df = df.drop(columns=["rn"])

    return df


def load_latest_profit_loss(conn):
    query = """
    WITH ranked AS (
        SELECT
            p.*,
            ROW_NUMBER() OVER (
                PARTITION BY p.company_id
                ORDER BY
                    CASE
                        WHEN p.sales IS NOT NULL THEN 0
                        ELSE 1
                    END,
                    p.year DESC
            ) AS rn
        FROM profitandloss p
    )
    SELECT
        company_id,
        year AS pnl_year,
        sales,
        net_profit,
        interest
    FROM ranked
    WHERE rn = 1
    """

    return pd.read_sql_query(query, conn)


def load_latest_market_cap(conn):
    query = """
    WITH ranked AS (
        SELECT
            m.*,
            ROW_NUMBER() OVER (
                PARTITION BY m.company_id
                ORDER BY m.year DESC
            ) AS rn
        FROM market_cap m
    )
    SELECT
        company_id,
        year AS market_year,
        market_cap_crore,
        enterprise_value_crore,
        pe_ratio,
        pb_ratio,
        ev_ebitda,
        dividend_yield_pct
    FROM ranked
    WHERE rn = 1
    """

    return pd.read_sql_query(query, conn)


def load_company_metadata(conn):
    query = """
    SELECT
        c.id AS company_id,
        c.company_name,
        s.broad_sector,
        s.sub_sector,
        s.market_cap_category
    FROM companies c
    LEFT JOIN sectors s
        ON c.id = s.company_id
    """

    return pd.read_sql_query(query, conn)


def load_screener_dataframe(db_path=DB_PATH):
    with sqlite3.connect(db_path) as conn:
        ratios = load_latest_financial_ratios(conn)
        pnl = load_latest_profit_loss(conn)
        market = load_latest_market_cap(conn)
        metadata = load_company_metadata(conn)

    df = metadata.merge(
        ratios,
        on="company_id",
        how="left",
    )

    df = df.merge(
        pnl,
        on="company_id",
        how="left",
    )

    df = df.merge(
        market,
        on="company_id",
        how="left",
    )

    if "company_name" in df.columns:
        df["company_name"] = (
            df["company_name"]
            .astype(str)
            .str.replace("\n", " ", regex=False)
            .str.strip()
        )

    df["is_financial"] = (
        df["broad_sector"]
        .fillna("")
        .astype(str)
        .str.strip()
        .str.lower()
        .eq("financials")
    )

    df["interest_coverage_effective"] = (
        df["interest_coverage"].copy()
    )

    debt_free_mask = (
    df["interest"].notna()
    & df["interest"].eq(0)
)

    df.loc[
        debt_free_mask,
        "interest_coverage_effective",
    ] = np.inf

    df["debt_free"] = debt_free_mask

    if "composite_quality_score" not in df.columns:
        df["composite_quality_score"] = 0.0

    return df


def _apply_min_filter(df, column, threshold):
    return df[
        df[column].notna()
        & (df[column] >= threshold)
    ]


def _apply_max_filter(df, column, threshold):
    return df[
        df[column].notna()
        & (df[column] <= threshold)
    ]


def _apply_equal_filter(df, column, threshold):
    return df[
        df[column].notna()
        & np.isclose(
            df[column],
            threshold,
            atol=1e-9,
        )
    ]


def apply_filter(
    df,
    metric_name,
    threshold,
    config,
):
    metric_config = config["metrics"].get(metric_name)

    if metric_config is None:
        raise ValueError(
            f"Unknown screener metric: {metric_name}"
        )

    column = metric_config["column"]
    operator = metric_config["operator"]

    working_df = df.copy()

    if metric_config.get(
        "debt_free_as_infinity",
        False,
    ):
        column = "interest_coverage_effective"

    if (
        metric_config.get("skip_financials", False)
        and operator == "max"
    ):
        financials = working_df[
            working_df["is_financial"]
        ]

        non_financials = working_df[
            ~working_df["is_financial"]
        ]

        non_financials = _apply_max_filter(
            non_financials,
            column,
            threshold,
        )

        return pd.concat(
            [financials, non_financials],
            ignore_index=True,
        )

    if operator == "min":
        return _apply_min_filter(
            working_df,
            column,
            threshold,
        )

    if operator == "max":
        return _apply_max_filter(
            working_df,
            column,
            threshold,
        )

    if operator == "eq":
        return _apply_equal_filter(
            working_df,
            column,
            threshold,
        )

    raise ValueError(
        f"Unsupported operator: {operator}"
    )


def apply_filters(
    df,
    filters,
    config=None,
):
    if config is None:
        config = load_config()

    result = df.copy()

    for metric_name, threshold in filters.items():
        result = apply_filter(
            result,
            metric_name,
            threshold,
            config,
        )

    if "composite_quality_score" in result.columns:
        result = result.sort_values(
            by=[
                "composite_quality_score",
                "company_id",
            ],
            ascending=[
                False,
                True,
            ],
        )

    return result.reset_index(drop=True)


def run_screener(
    filters,
    db_path=DB_PATH,
):
    config = load_config()
    df = load_screener_dataframe(db_path)

    return apply_filters(
        df,
        filters,
        config,
    )


PRESET_EXTRA_COLUMNS = {
    "dividend_payout": "dividend_payout_ratio_pct",
    "revenue_cagr_3yr": "revenue_cagr_3yr",
}


def compare_series(
    series,
    value,
    comparison,
):
    valid = series.notna()

    if comparison == "gt":
        return valid & (series > value)

    if comparison == "ge":
        return valid & (series >= value)

    if comparison == "lt":
        return valid & (series < value)

    if comparison == "le":
        return valid & (series <= value)

    if comparison == "eq":
        return (
            valid
            & np.isclose(
                series,
                value,
                atol=1e-9,
            )
        )

    raise ValueError(
        f"Unsupported comparison: {comparison}"
    )


def get_metric_column(
    metric_name,
    config,
):
    if metric_name in config["metrics"]:
        metric_cfg = config["metrics"][metric_name]

        if metric_cfg.get(
            "debt_free_as_infinity",
            False,
        ):
            return "interest_coverage_effective"

        return metric_cfg["column"]

    if metric_name in PRESET_EXTRA_COLUMNS:
        return PRESET_EXTRA_COLUMNS[
            metric_name
        ]

    raise ValueError(
        f"Unknown preset metric: {metric_name}"
    )


def apply_preset_condition(
    df,
    metric_name,
    rule,
    config,
):
    column = get_metric_column(
        metric_name,
        config,
    )

    value = rule["value"]
    comparison = rule["comparison"]

    if (
        metric_name == "debt_to_equity"
        and comparison in {"lt", "le"}
    ):
        financial_mask = df["is_financial"]

        normal_mask = compare_series(
            df[column],
            value,
            comparison,
        )

        return df[
            financial_mask | normal_mask
        ].copy()

    mask = compare_series(
        df[column],
        value,
        comparison,
    )

    return df[mask].copy()



def load_debt_to_equity_history(
    db_path=DB_PATH,
):
    with sqlite3.connect(db_path) as conn:
        history = pd.read_sql_query(
            """
            SELECT
                company_id,
                year,
                debt_to_equity,
                return_on_equity_pct
            FROM financial_ratios
            WHERE debt_to_equity IS NOT NULL
            ORDER BY company_id, year DESC
            """,
            conn,
        )

    history["period"] = pd.to_datetime(
        history["year"],
        format="%Y-%m",
        errors="coerce",
    )

    rows = []

    for company_id, group in history.groupby(
        "company_id"
    ):
        group = (
            group[
                group["period"].notna()
            ]
            .sort_values(
                "period",
                ascending=False,
            )
            .reset_index(drop=True)
        )

        usable = group[
            group["return_on_equity_pct"].notna()
            & group["debt_to_equity"].notna()
        ]

        if usable.empty:
            rows.append(
                {
                    "company_id": company_id,
                    "latest_de_year": None,
                    "previous_de_year": None,
                    "latest_de": float("nan"),
                    "previous_de": float("nan"),
                    "de_declining_yoy": False,
                }
            )
            continue

        latest = usable.iloc[0]

        target_period = (
            latest["period"]
            - pd.DateOffset(years=1)
        )

        previous = group[
            group["period"].eq(target_period)
            & group["debt_to_equity"].notna()
        ]

        if previous.empty:
            rows.append(
                {
                    "company_id": company_id,
                    "latest_de_year": latest["year"],
                    "previous_de_year": None,
                    "latest_de": latest["debt_to_equity"],
                    "previous_de": float("nan"),
                    "de_declining_yoy": False,
                }
            )
            continue

        previous = previous.iloc[0]

        latest_de = latest["debt_to_equity"]
        previous_de = previous["debt_to_equity"]

        rows.append(
            {
                "company_id": company_id,
                "latest_de_year": latest["year"],
                "previous_de_year": previous["year"],
                "latest_de": latest_de,
                "previous_de": previous_de,
                "de_declining_yoy": bool(
                    latest_de < previous_de
                ),
            }
        )

    return pd.DataFrame(rows)

def apply_turnaround_special_rule(
    df,
    db_path=DB_PATH,
):
    de_history = load_debt_to_equity_history(
        db_path
    )

    result = df.merge(
        de_history,
        on="company_id",
        how="left",
    )

    result["de_declining_yoy"] = (
        result["de_declining_yoy"]
        .fillna(False)
        .astype(bool)
    )

    return result[
        result["de_declining_yoy"]
    ].copy()


def run_preset(
    preset_name,
    db_path=DB_PATH,
):
    config = load_config()
    presets = config.get("presets", {})

    if preset_name not in presets:
        raise ValueError(
            f"Unknown preset: {preset_name}"
        )

    preset = presets[preset_name]

    df = load_screener_dataframe(
        db_path
    )

    result = df.copy()

    for metric_name, rule in preset.get(
        "filters",
        {},
    ).items():
        result = apply_preset_condition(
            result,
            metric_name,
            rule,
            config,
        )

    special_rules = preset.get(
        "special_rules",
        {},
    )

    if special_rules.get(
        "debt_to_equity_declining_yoy",
        False,
    ):
        result = apply_turnaround_special_rule(
            result,
            db_path,
        )

    result["preset_name"] = preset["label"]

    if "composite_quality_score" in result.columns:
        result = result.sort_values(
            [
                "composite_quality_score",
                "company_id",
            ],
            ascending=[
                False,
                True,
            ],
        )

    return result.reset_index(drop=True)


def run_all_presets(
    db_path=DB_PATH,
):
    config = load_config()

    results = {}

    for preset_name in config["presets"]:
        results[preset_name] = run_preset(
            preset_name,
            db_path,
        )

    return results


def preview_all_presets():
    config = load_config()
    results = run_all_presets()

    print("=" * 80)
    print("SPRINT 3 — DAY 16")
    print("PRESET SCREENER VALIDATION")
    print("=" * 80)

    total_pass = 0

    for preset_name, df in results.items():
        label = config["presets"][
            preset_name
        ]["label"]

        count = len(df)

        passed = 5 <= count <= 50

        if passed:
            total_pass += 1

        status = (
            "PASS"
            if passed
            else "REVIEW"
        )

        print()
        print(label)
        print("-" * 60)
        print(f"Companies: {count}")
        print(f"Status: {status}")

        if count > 0:
            columns = [
                "company_id",
                "return_on_equity_pct",
                "debt_to_equity",
                "free_cash_flow_cr",
                "revenue_cagr_5yr",
                "pat_cagr_5yr",
                "composite_quality_score",
            ]

            existing = [
                col
                for col in columns
                if col in df.columns
            ]

            print(
                df[existing]
                .head(5)
                .to_string(index=False)
            )

    print()
    print("=" * 80)

    print(
        f"Presets within 5-50 range: "
        f"{total_pass}/6"
    )

    print("=" * 80)


if __name__ == "__main__":
    preview_all_presets()