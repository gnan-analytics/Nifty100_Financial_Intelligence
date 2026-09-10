import sqlite3
from pathlib import Path

import pandas as pd

from src.analytics.cagr import (
    calculate_series_cagr,
)
from src.analytics.cashflow_kpis import (
    calculate_cfo_pat_ratio,
    calculate_fcf_conversion,
    calculate_free_cash_flow,
)
from src.analytics.ratios import (
    calculate_asset_turnover,
    calculate_debt_to_equity,
    calculate_interest_coverage,
    calculate_net_debt,
    calculate_net_profit_margin,
    calculate_operating_profit_margin,
    calculate_roa,
    calculate_roce,
    calculate_roe,
)

# =========================================================
# CONFIG
# =========================================================

DB_PATH = Path("db/nifty100.db")


# =========================================================
# DB HELPERS
# =========================================================


def load_table(
    conn,
    table_name,
):
    """Load table."""
    return pd.read_sql_query(
        f"SELECT * FROM {table_name}",
        conn,
    )


def ensure_ratio_columns(
    conn,
):
    """
    Add Sprint 2 KPI columns
    if they do not already exist.
    """

    required_columns = {
        "return_on_capital_employed_pct": "REAL",
        "return_on_assets_pct": "REAL",
        "net_debt_cr": "REAL",
        "cfo_pat_ratio": "REAL",
        "fcf_conversion_pct": "REAL",
        "revenue_cagr_3yr": "REAL",
        "revenue_cagr_5yr": "REAL",
        "revenue_cagr_10yr": "REAL",
        "pat_cagr_3yr": "REAL",
        "pat_cagr_5yr": "REAL",
        "pat_cagr_10yr": "REAL",
        "eps_cagr_3yr": "REAL",
        "eps_cagr_5yr": "REAL",
        "eps_cagr_10yr": "REAL",
        "revenue_cagr_3yr_flag": "TEXT",
        "revenue_cagr_5yr_flag": "TEXT",
        "revenue_cagr_10yr_flag": "TEXT",
        "pat_cagr_3yr_flag": "TEXT",
        "pat_cagr_5yr_flag": "TEXT",
        "pat_cagr_10yr_flag": "TEXT",
        "eps_cagr_3yr_flag": "TEXT",
        "eps_cagr_5yr_flag": "TEXT",
        "eps_cagr_10yr_flag": "TEXT",
        "composite_quality_score": "REAL",
    }

    existing = {
        row[1] for row in conn.execute("PRAGMA table_info(financial_ratios)").fetchall()
    }

    for column, sql_type in required_columns.items():

        if column not in existing:

            conn.execute(f"""
                ALTER TABLE financial_ratios
                ADD COLUMN {column} {sql_type}
                """)

            print(f"Added column: {column}")

    conn.commit()


# =========================================================
# BOOK VALUE PER SHARE
# =========================================================


def calculate_book_value_per_share(
    equity_capital,
    reserves,
    face_value,
):
    """Calculate book value per share."""
    if pd.isna(equity_capital) or pd.isna(reserves) or pd.isna(face_value):
        return None

    try:
        equity_capital = float(equity_capital)

        reserves = float(reserves)

        face_value = float(face_value)

    except (
        TypeError,
        ValueError,
    ):
        return None

    if equity_capital == 0 or face_value == 0:
        return None

    shares_crore = equity_capital / face_value

    if shares_crore == 0:
        return None

    return (equity_capital + reserves) / shares_crore


# =========================================================
# QUALITY SCORE
# =========================================================


def calculate_composite_quality_score(
    roe,
    npm,
    debt_to_equity,
    asset_turnover,
    cfo_pat_ratio,
):
    """
    Simple 0-100 quality score.

    Five components, 20 points each.
    """

    score = 0

    if roe is not None and roe >= 15:
        score += 20

    if npm is not None and npm >= 10:
        score += 20

    if debt_to_equity is not None and debt_to_equity <= 1:
        score += 20

    if asset_turnover is not None and asset_turnover >= 0.5:
        score += 20

    if cfo_pat_ratio is not None and cfo_pat_ratio >= 1:
        score += 20

    return float(score)


# =========================================================
# HISTORY HELPER
# =========================================================


def get_history(
    pnl_df,
    company_id,
    current_year,
    column,
):
    """Return history."""
    company_df = pnl_df[pnl_df["company_id"] == company_id].copy()

    company_df = company_df[company_df["year"] <= current_year]

    company_df = company_df.sort_values("year")

    values = company_df[column].tolist()

    return values


# =========================================================
# MASTER COMPANY-YEAR FRAME
# =========================================================


def build_master_years(
    pnl,
    bs,
    cf,
):
    """Build master years."""
    frames = []

    for df in [
        pnl,
        bs,
        cf,
    ]:

        frames.append(
            df[
                [
                    "company_id",
                    "year",
                ]
            ]
        )

    master = (
        pd.concat(
            frames,
            ignore_index=True,
        )
        .drop_duplicates()
        .sort_values(
            [
                "company_id",
                "year",
            ]
        )
        .reset_index(drop=True)
    )

    return master


# =========================================================
# BUILD RATIO DATASET
# =========================================================


def build_financial_ratios(
    companies,
    pnl,
    bs,
    cf,
):
    """Build financial ratios."""
    master = build_master_years(
        pnl,
        bs,
        cf,
    )

    company_lookup = companies.set_index("id").to_dict("index")

    pnl_lookup = pnl.set_index(
        [
            "company_id",
            "year",
        ]
    ).to_dict("index")

    bs_lookup = bs.set_index(
        [
            "company_id",
            "year",
        ]
    ).to_dict("index")

    cf_lookup = cf.set_index(
        [
            "company_id",
            "year",
        ]
    ).to_dict("index")

    output_rows = []

    for _, key in master.iterrows():

        company_id = key["company_id"]

        year = key["year"]

        pnl_row = pnl_lookup.get(
            (
                company_id,
                year,
            ),
            {},
        )

        bs_row = bs_lookup.get(
            (
                company_id,
                year,
            ),
            {},
        )

        cf_row = cf_lookup.get(
            (
                company_id,
                year,
            ),
            {},
        )

        company_row = company_lookup.get(
            company_id,
            {},
        )

        # -----------------------------------------
        # PROFITABILITY
        # -----------------------------------------

        npm = calculate_net_profit_margin(
            pnl_row.get("net_profit"),
            pnl_row.get("sales"),
        )

        opm = calculate_operating_profit_margin(
            pnl_row.get("operating_profit"),
            pnl_row.get("sales"),
        )

        roe = calculate_roe(
            pnl_row.get("net_profit"),
            bs_row.get("equity_capital"),
            bs_row.get("reserves"),
        )

        roce = calculate_roce(
            pnl_row.get("operating_profit"),
            bs_row.get("equity_capital"),
            bs_row.get("reserves"),
            bs_row.get("borrowings"),
        )

        roa = calculate_roa(
            pnl_row.get("net_profit"),
            bs_row.get("total_assets"),
        )

        # -----------------------------------------
        # LEVERAGE
        # -----------------------------------------

        debt_to_equity = calculate_debt_to_equity(
            bs_row.get("borrowings"),
            bs_row.get("equity_capital"),
            bs_row.get("reserves"),
        )

        interest_coverage = calculate_interest_coverage(
            pnl_row.get("operating_profit"),
            pnl_row.get("other_income"),
            pnl_row.get("interest"),
        )

        asset_turnover = calculate_asset_turnover(
            pnl_row.get("sales"),
            bs_row.get("total_assets"),
        )

        net_debt = calculate_net_debt(
            bs_row.get("borrowings"),
            bs_row.get("investments"),
        )

        # -----------------------------------------
        # CASH FLOW
        # -----------------------------------------

        fcf = calculate_free_cash_flow(
            cf_row.get("operating_activity"),
            cf_row.get("investing_activity"),
        )

        cfo_pat_ratio = calculate_cfo_pat_ratio(
            cf_row.get("operating_activity"),
            pnl_row.get("net_profit"),
        )

        fcf_conversion = calculate_fcf_conversion(
            fcf,
            pnl_row.get("operating_profit"),
        )

        # -----------------------------------------
        # BOOK VALUE
        # -----------------------------------------

        book_value_per_share = calculate_book_value_per_share(
            bs_row.get("equity_capital"),
            bs_row.get("reserves"),
            company_row.get("face_value"),
        )

        # -----------------------------------------
        # CAGR
        # -----------------------------------------

        sales_history = get_history(
            pnl,
            company_id,
            year,
            "sales",
        )

        pat_history = get_history(
            pnl,
            company_id,
            year,
            "net_profit",
        )

        eps_history = get_history(
            pnl,
            company_id,
            year,
            "eps",
        )

        cagr_results = {}

        for window in [
            3,
            5,
            10,
        ]:

            revenue_cagr = calculate_series_cagr(
                sales_history,
                window,
            )

            pat_cagr = calculate_series_cagr(
                pat_history,
                window,
            )

            eps_cagr = calculate_series_cagr(
                eps_history,
                window,
            )

            cagr_results[f"revenue_cagr_{window}yr"] = revenue_cagr["value"]

            cagr_results[f"revenue_cagr_{window}yr_flag"] = revenue_cagr["flag"]

            cagr_results[f"pat_cagr_{window}yr"] = pat_cagr["value"]

            cagr_results[f"pat_cagr_{window}yr_flag"] = pat_cagr["flag"]

            cagr_results[f"eps_cagr_{window}yr"] = eps_cagr["value"]

            cagr_results[f"eps_cagr_{window}yr_flag"] = eps_cagr["flag"]

        # -----------------------------------------
        # QUALITY SCORE
        # -----------------------------------------

        quality_score = calculate_composite_quality_score(
            roe,
            npm,
            debt_to_equity,
            asset_turnover,
            cfo_pat_ratio,
        )

        # -----------------------------------------
        # FINAL ROW
        # -----------------------------------------

        row = {
            "company_id": company_id,
            "year": year,
            "net_profit_margin_pct": npm,
            "operating_profit_margin_pct": opm,
            "return_on_equity_pct": roe,
            "return_on_capital_employed_pct": roce,
            "return_on_assets_pct": roa,
            "debt_to_equity": debt_to_equity,
            "interest_coverage": interest_coverage,
            "asset_turnover": asset_turnover,
            "free_cash_flow_cr": fcf,
            "capex_cr": (
                abs(cf_row.get("investing_activity"))
                if (
                    cf_row.get("investing_activity") is not None
                    and not pd.isna(cf_row.get("investing_activity"))
                )
                else None
            ),
            "earnings_per_share": (pnl_row.get("eps")),
            "book_value_per_share": (book_value_per_share),
            "dividend_payout_ratio_pct": (pnl_row.get("dividend_payout")),
            "total_debt_cr": (bs_row.get("borrowings")),
            "cash_from_operations_cr": (cf_row.get("operating_activity")),
            "net_debt_cr": net_debt,
            "cfo_pat_ratio": cfo_pat_ratio,
            "fcf_conversion_pct": (fcf_conversion),
            "composite_quality_score": (quality_score),
        }

        row.update(cagr_results)

        output_rows.append(row)

    return pd.DataFrame(output_rows)


# =========================================================
# WRITE TO SQLITE
# =========================================================


def populate_financial_ratios():
    """Populate financial ratios."""
    with sqlite3.connect(DB_PATH) as conn:

        ensure_ratio_columns(conn)

        companies = load_table(
            conn,
            "companies",
        )

        pnl = load_table(
            conn,
            "profitandloss",
        )

        bs = load_table(
            conn,
            "balancesheet",
        )

        cf = load_table(
            conn,
            "cashflow",
        )

        result = build_financial_ratios(
            companies,
            pnl,
            bs,
            cf,
        )

        print(f"Computed rows: " f"{len(result)}")

        db_columns = [row[1] for row in conn.execute("""
                PRAGMA table_info(
                    financial_ratios
                )
                """).fetchall()]

        for column in db_columns:

            if column not in result.columns:

                result[column] = None

        result = result[db_columns]

        conn.execute("""
            DELETE FROM financial_ratios
            """)

        result.to_sql(
            "financial_ratios",
            conn,
            if_exists="append",
            index=False,
        )

        conn.commit()

        count = conn.execute("""
            SELECT COUNT(*)
            FROM financial_ratios
            """).fetchone()[0]

        print()
        print("=" * 60)
        print("FINANCIAL RATIOS POPULATION")
        print("=" * 60)

        print(f"Rows in financial_ratios: " f"{count}")

        if count >= 1100:

            print("PASS: row count >= 1100")

        else:

            print("WARNING: row count < 1100")

        print()
        print("Null-only column check:")

        for column in result.columns:

            null_count = result[column].isna().sum()

            if null_count == len(result):

                print(f"NULL-ONLY: {column}")


# =========================================================
# ENTRY POINT
# =========================================================

if __name__ == "__main__":
    populate_financial_ratios()
