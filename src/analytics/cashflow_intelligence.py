import sqlite3
from pathlib import Path

import pandas as pd

from src.analytics.cashflow_kpis import (
    calculate_capex_intensity,
    calculate_cfo_quality_score,
)

ROOT = Path(__file__).resolve().parents[2]
DB_PATH = ROOT / "db" / "nifty100.db"

OUTPUT_XLSX = ROOT / "output" / "cashflow_intelligence.xlsx"
DISTRESS_CSV = ROOT / "output" / "distress_alerts.csv"
CAPITAL_ALLOCATION_CSV = ROOT / "output" / "capital_allocation.csv"


def annual_rows(df):
    """Return annual financial rows."""
    if df.empty:
        return df.copy()

    x = df.copy()

    x["year"] = x["year"].astype(str)

    march = x[x["year"].str.endswith("-03")].copy()

    if not march.empty:
        x = march

    x["_date"] = pd.to_datetime(
        x["year"],
        format="%Y-%m",
        errors="coerce",
    )

    return x.dropna(subset=["_date"]).sort_values("_date")


def safe_float(value):
    """Convert a value to float safely."""
    if value is None or pd.isna(value):
        return None

    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def calculate_fcf_cagr(values, years=5):
    """
    Calculate FCF CAGR using the latest requested
    annual observations.

    CAGR is meaningful only when both start and
    end FCF values are positive.
    """

    valid = []

    for value in values:
        value = safe_float(value)

        if value is not None:
            valid.append(value)

    if len(valid) < years:
        return None

    values = valid[-years:]

    start = values[0]
    end = values[-1]

    if start <= 0 or end <= 0:
        return None

    periods = years - 1

    if periods <= 0:
        return None

    return ((end / start) ** (1 / periods) - 1) * 100


def latest_value(df, column):
    """Handle latest value."""
    if df.empty or column not in df.columns:
        return None

    x = annual_rows(df)

    if x.empty:
        return None

    values = pd.to_numeric(
        x[column],
        errors="coerce",
    ).dropna()

    if values.empty:
        return None

    return float(values.iloc[-1])


def latest_two_values(df, column):
    """Handle latest two values."""
    if df.empty or column not in df.columns:
        return []

    x = annual_rows(df)

    values = pd.to_numeric(
        x[column],
        errors="coerce",
    ).dropna()

    return values.tail(2).tolist()


def latest_capital_allocation(df):
    """Handle latest capital allocation."""
    if df.empty:
        return "Data Unavailable"

    x = annual_rows(df)

    if x.empty:
        return "Data Unavailable"

    value = x.iloc[-1].get("pattern_label")

    if pd.isna(value):
        return "Data Unavailable"

    return str(value)


def load_data():
    """Load data."""
    with sqlite3.connect(DB_PATH) as conn:

        companies = pd.read_sql_query(
            """
            SELECT id AS company_id,
                   company_name
            FROM companies
            ORDER BY id
            """,
            conn,
        )

        sectors = pd.read_sql_query(
            """
            SELECT company_id,
                   broad_sector
            FROM sectors
            """,
            conn,
        )

        cashflow = pd.read_sql_query(
            """
            SELECT *
            FROM cashflow
            """,
            conn,
        )

        pnl = pd.read_sql_query(
            """
            SELECT *
            FROM profitandloss
            """,
            conn,
        )

        balance = pd.read_sql_query(
            """
            SELECT *
            FROM balancesheet
            """,
            conn,
        )

        ratios = pd.read_sql_query(
            """
            SELECT *
            FROM financial_ratios
            """,
            conn,
        )

    allocation = pd.read_csv(CAPITAL_ALLOCATION_CSV)

    frames = [
        companies,
        sectors,
        cashflow,
        pnl,
        balance,
        ratios,
        allocation,
    ]

    for df in frames:
        if "company_id" in df.columns:
            df["company_id"] = df["company_id"].astype(str).str.strip().str.upper()

    return (
        companies,
        sectors,
        cashflow,
        pnl,
        balance,
        ratios,
        allocation,
    )


def build_company_intelligence(
    company_id,
    sector,
    cashflow,
    pnl,
    balance,
    ratios,
    allocation,
):
    """Build company intelligence."""
    cf = cashflow[cashflow["company_id"] == company_id]

    pl = pnl[pnl["company_id"] == company_id]

    bs = balance[balance["company_id"] == company_id]

    rt = ratios[ratios["company_id"] == company_id]

    ca = allocation[allocation["company_id"] == company_id]

    cf_annual = annual_rows(cf)
    pl_annual = annual_rows(pl)
    rt_annual = annual_rows(rt)

    # ---------------------------------------------
    # 5Y CFO QUALITY
    # ---------------------------------------------

    quality_values = []

    if not rt_annual.empty:
        quality_values = (
            pd.to_numeric(
                rt_annual["cfo_pat_ratio"],
                errors="coerce",
            )
            .dropna()
            .tail(5)
            .tolist()
        )

    quality = calculate_cfo_quality_score(quality_values)

    # ---------------------------------------------
    # LATEST CAPEX INTENSITY
    # ---------------------------------------------

    latest_cf = cf_annual.iloc[-1] if not cf_annual.empty else None

    latest_pl = pl_annual.iloc[-1] if not pl_annual.empty else None

    if latest_cf is not None and latest_pl is not None:
        capex = calculate_capex_intensity(
            latest_cf.get("investing_activity"),
            latest_pl.get("sales"),
        )
    else:
        capex = {
            "value": None,
            "label": None,
        }

    # ---------------------------------------------
    # 5Y FCF CAGR
    # ---------------------------------------------

    fcf_values = []

    if not rt_annual.empty:
        fcf_values = (
            pd.to_numeric(
                rt_annual["free_cash_flow_cr"],
                errors="coerce",
            )
            .dropna()
            .tail(5)
            .tolist()
        )

    fcf_cagr = calculate_fcf_cagr(
        fcf_values,
        years=5,
    )

    # ---------------------------------------------
    # LATEST FCF CONVERSION
    # ---------------------------------------------

    fcf_conversion = latest_value(
        rt,
        "fcf_conversion_pct",
    )

    # ---------------------------------------------
    # DISTRESS
    #
    # Latest CFO < 0 AND latest CFF > 0
    # ---------------------------------------------

    distress = False

    latest_cfo = None
    latest_cff = None

    if latest_cf is not None:

        latest_cfo = safe_float(latest_cf.get("operating_activity"))

        latest_cff = safe_float(latest_cf.get("financing_activity"))

        if latest_cfo is not None and latest_cff is not None:
            distress = latest_cfo < 0 and latest_cff > 0

    # ---------------------------------------------
    # DELEVERAGING
    #
    # Latest CFF < 0 AND borrowings declining YoY
    # ---------------------------------------------

    deleveraging = False

    borrowings = latest_two_values(
        bs,
        "borrowings",
    )

    if latest_cff is not None and latest_cff < 0 and len(borrowings) == 2:
        previous_borrowing = borrowings[0]
        latest_borrowing = borrowings[1]

        deleveraging = latest_borrowing < previous_borrowing

    # ---------------------------------------------
    # CAPITAL ALLOCATION
    # ---------------------------------------------

    allocation_label = latest_capital_allocation(ca)

    return {
        "company_id": company_id,
        "sector": sector,
        "cfo_quality_score": (quality["average_ratio"]),
        "cfo_quality_label": (
            quality["label"] if quality["label"] else "Data Unavailable"
        ),
        "capex_intensity_pct": (capex["value"]),
        "capex_label": (capex["label"] if capex["label"] else "Data Unavailable"),
        "fcf_cagr_5yr": fcf_cagr,
        "fcf_conversion_pct": (fcf_conversion),
        "distress_flag": distress,
        "deleveraging_flag": deleveraging,
        "capital_allocation_label": (allocation_label),
        "_latest_cfo": latest_cfo,
        "_latest_cff": latest_cff,
        "_latest_net_profit": (
            latest_value(
                pl,
                "net_profit",
            )
        ),
    }


def main():
    """Run the module entry point."""
    (
        companies,
        sectors,
        cashflow,
        pnl,
        balance,
        ratios,
        allocation,
    ) = load_data()

    company_master = companies.merge(
        sectors,
        on="company_id",
        how="left",
    )

    rows = []

    for _, company in company_master.iterrows():

        rows.append(
            build_company_intelligence(
                company_id=company["company_id"],
                sector=company["broad_sector"],
                cashflow=cashflow,
                pnl=pnl,
                balance=balance,
                ratios=ratios,
                allocation=allocation,
            )
        )

    result = pd.DataFrame(rows)

    required_columns = [
        "company_id",
        "sector",
        "cfo_quality_score",
        "cfo_quality_label",
        "capex_intensity_pct",
        "capex_label",
        "fcf_cagr_5yr",
        "fcf_conversion_pct",
        "distress_flag",
        "deleveraging_flag",
        "capital_allocation_label",
    ]

    OUTPUT_XLSX.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    result[required_columns].to_excel(
        OUTPUT_XLSX,
        index=False,
    )

    distress = result[result["distress_flag"]][
        [
            "company_id",
            "sector",
            "_latest_cfo",
            "_latest_cff",
            "_latest_net_profit",
        ]
    ].copy()

    distress = distress.rename(
        columns={
            "_latest_cfo": "cfo",
            "_latest_cff": "cff",
            "_latest_net_profit": "net_profit",
        }
    )

    distress.to_csv(
        DISTRESS_CSV,
        index=False,
    )

    print("=" * 80)
    print("SPRINT 5 - DAY 31 CASH FLOW INTELLIGENCE")
    print("=" * 80)

    print(
        "\nCompanies:",
        len(result),
    )

    print("\nCFO QUALITY:")
    print(result["cfo_quality_label"].value_counts(dropna=False).to_string())

    print("\nCAPEX LABEL:")
    print(result["capex_label"].value_counts(dropna=False).to_string())

    print(
        "\nDistress companies:",
        int(result["distress_flag"].sum()),
    )

    print(
        "Deleveraging companies:",
        int(result["deleveraging_flag"].sum()),
    )

    print(
        "\nFCF CAGR available:",
        result["fcf_cagr_5yr"].notna().sum(),
    )

    print(
        "FCF conversion available:",
        result["fcf_conversion_pct"].notna().sum(),
    )

    print(
        "\nCapital allocation unavailable:",
        (result["capital_allocation_label"] == "Data Unavailable").sum(),
    )

    print(f"\nCreated: {OUTPUT_XLSX}")

    print(f"Created: {DISTRESS_CSV}")

    print("\nDAY 31 GENERATOR: PASS")


if __name__ == "__main__":
    main()
