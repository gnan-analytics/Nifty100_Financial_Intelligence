import sqlite3
from pathlib import Path

import pandas as pd
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DB_PATH = PROJECT_ROOT / "db" / "nifty100.db"


def _connect():
    return sqlite3.connect(DB_PATH)


@st.cache_data(ttl=600)
def _table_exists(table_name):
    with _connect() as conn:
        row = conn.execute(
            """
            SELECT name
            FROM sqlite_master
            WHERE type = 'table'
              AND name = ?
            """,
            (table_name,),
        ).fetchone()

    return row is not None


# ============================================================
# COMPANIES
# companies.id = NSE ticker / company identifier
# ============================================================


@st.cache_data(ttl=600)
def get_companies():
    """Return companies."""
    with _connect() as conn:
        return pd.read_sql_query(
            """
            SELECT
                id AS company_id,
                id AS ticker,
                company_logo,
                company_name,
                chart_link,
                about_company,
                website,
                nse_profile,
                bse_profile,
                face_value,
                book_value,
                roce_percentage,
                roe_percentage
            FROM companies
            ORDER BY company_name
            """,
            conn,
        )


@st.cache_data(ttl=600)
def get_company(ticker):
    """Return company."""
    with _connect() as conn:
        return pd.read_sql_query(
            """
            SELECT
                id AS company_id,
                id AS ticker,
                company_logo,
                company_name,
                chart_link,
                about_company,
                website,
                nse_profile,
                bse_profile,
                face_value,
                book_value,
                roce_percentage,
                roe_percentage
            FROM companies
            WHERE UPPER(id) = UPPER(?)
            """,
            conn,
            params=[ticker],
        )


# ============================================================
# FINANCIAL RATIOS
# ============================================================


@st.cache_data(ttl=600)
def get_ratios(ticker, year=None):
    """Return ratios."""
    params = [ticker]

    query = """
        SELECT *
        FROM financial_ratios
        WHERE UPPER(company_id) = UPPER(?)
    """

    if year is not None:
        query += """
            AND year = ?
        """
        params.append(year)

    query += """
        ORDER BY year
    """

    with _connect() as conn:
        return pd.read_sql_query(
            query,
            conn,
            params=params,
        )


# ============================================================
# PROFIT & LOSS
# ============================================================


@st.cache_data(ttl=600)
def get_pl(ticker):
    """Return pl."""
    with _connect() as conn:
        return pd.read_sql_query(
            """
            SELECT *
            FROM profitandloss
            WHERE UPPER(company_id) = UPPER(?)
            ORDER BY year
            """,
            conn,
            params=[ticker],
        )


# ============================================================
# BALANCE SHEET
# ============================================================


@st.cache_data(ttl=600)
def get_bs(ticker):
    """Return bs."""
    with _connect() as conn:
        return pd.read_sql_query(
            """
            SELECT *
            FROM balancesheet
            WHERE UPPER(company_id) = UPPER(?)
            ORDER BY year
            """,
            conn,
            params=[ticker],
        )


# ============================================================
# CASH FLOW
# ============================================================


@st.cache_data(ttl=600)
def get_cf(ticker):
    """Return cf."""
    with _connect() as conn:
        return pd.read_sql_query(
            """
            SELECT *
            FROM cashflow
            WHERE UPPER(company_id) = UPPER(?)
            ORDER BY year
            """,
            conn,
            params=[ticker],
        )


# ============================================================
# SECTORS
# ============================================================


@st.cache_data(ttl=600)
def get_sectors():
    """Return sectors."""
    with _connect() as conn:
        return pd.read_sql_query(
            """
            SELECT
                s.*,
                c.company_name
            FROM sectors s
            LEFT JOIN companies c
                ON s.company_id = c.id
            ORDER BY
                s.broad_sector,
                c.company_name
            """,
            conn,
        )


@st.cache_data(ttl=600)
def get_sector_for_company(ticker):
    """Return sector for company."""
    with _connect() as conn:
        return pd.read_sql_query(
            """
            SELECT
                s.*,
                c.company_name
            FROM sectors s
            LEFT JOIN companies c
                ON s.company_id = c.id
            WHERE UPPER(s.company_id) = UPPER(?)
            """,
            conn,
            params=[ticker],
        )


# ============================================================
# PEER GROUPS
# ============================================================


@st.cache_data(ttl=600)
def get_peer_groups():
    """Return peer groups."""
    with _connect() as conn:
        return pd.read_sql_query(
            """
            SELECT DISTINCT
                peer_group_name
            FROM peer_groups
            ORDER BY peer_group_name
            """,
            conn,
        )


@st.cache_data(ttl=600)
def get_peers(group_name):
    """Return peers."""
    with _connect() as conn:
        return pd.read_sql_query(
            """
            SELECT
                pg.id AS peer_id,
                pg.peer_group_name,
                pg.company_id,
                pg.is_benchmark,
                c.company_name,
                c.company_logo,
                c.about_company,
                c.website
            FROM peer_groups pg
            LEFT JOIN companies c
                ON pg.company_id = c.id
            WHERE pg.peer_group_name = ?
            ORDER BY
                pg.is_benchmark DESC,
                c.company_name
            """,
            conn,
            params=[group_name],
        )


@st.cache_data(ttl=600)
def get_peer_percentiles(group_name=None):
    """Return peer percentiles."""
    if not _table_exists("peer_percentiles"):
        return pd.DataFrame()

    query = """
        SELECT *
        FROM peer_percentiles
    """

    params = []

    if group_name is not None:
        query += """
            WHERE peer_group_name = ?
        """
        params.append(group_name)

    query += """
        ORDER BY
            peer_group_name,
            company_id,
            metric
    """

    with _connect() as conn:
        return pd.read_sql_query(
            query,
            conn,
            params=params,
        )


# ============================================================
# MARKET CAP / VALUATION
# ============================================================


@st.cache_data(ttl=600)
def get_market_cap(ticker=None):
    """Return market cap."""
    query = """
        SELECT *
        FROM market_cap
    """

    params = []

    if ticker is not None:
        query += """
            WHERE UPPER(company_id) = UPPER(?)
        """
        params.append(ticker)

    query += """
        ORDER BY
            company_id,
            year
    """

    with _connect() as conn:
        return pd.read_sql_query(
            query,
            conn,
            params=params,
        )


@st.cache_data(ttl=600)
def get_valuation(ticker):
    """Return valuation."""
    valuation_path = PROJECT_ROOT / "output" / "valuation_summary.xlsx"

    if not valuation_path.exists():
        return pd.DataFrame()

    df = pd.read_excel(valuation_path)

    ticker_column = None

    for candidate in [
        "company_id",
        "ticker",
        "symbol",
    ]:
        if candidate in df.columns:
            ticker_column = candidate
            break

    if ticker_column is None:
        return pd.DataFrame()

    return df[df[ticker_column].astype(str).str.upper().eq(str(ticker).upper())].copy()


# ============================================================
# PROS & CONS
# ============================================================


@st.cache_data(ttl=600)
def get_pros_cons(ticker):
    """Return pros cons."""
    with _connect() as conn:
        return pd.read_sql_query(
            """
            SELECT *
            FROM prosandcons
            WHERE UPPER(company_id) = UPPER(?)
            """,
            conn,
            params=[ticker],
        )


# ============================================================
# DOCUMENTS / ANNUAL REPORTS
# ============================================================


@st.cache_data(ttl=600)
def get_documents(ticker):
    """Return documents."""
    with _connect() as conn:
        return pd.read_sql_query(
            """
            SELECT *
            FROM documents
            WHERE UPPER(company_id) = UPPER(?)
            ORDER BY year DESC
            """,
            conn,
            params=[ticker],
        )


# ============================================================
# CAPITAL ALLOCATION
# ============================================================


@st.cache_data(ttl=600)
def get_capital_allocation():
    """Return capital allocation."""
    csv_path = PROJECT_ROOT / "output" / "capital_allocation.csv"

    if csv_path.exists():
        return pd.read_csv(csv_path)

    return pd.DataFrame()


# ============================================================
# LATEST RATIOS — ALL COMPANIES
# ============================================================


@st.cache_data(ttl=600)
def get_latest_ratios_all():
    """Return latest ratios all."""
    with _connect() as conn:
        return pd.read_sql_query(
            """
            WITH ranked AS (
                SELECT
                    fr.*,
                    ROW_NUMBER() OVER (
                        PARTITION BY
                            fr.company_id
                        ORDER BY
                            CASE
                                WHEN
                                    fr.return_on_equity_pct
                                    IS NOT NULL
                                THEN 0
                                ELSE 1
                            END,
                            fr.year DESC
                    ) AS rn
                FROM financial_ratios fr
            )
            SELECT *
            FROM ranked
            WHERE rn = 1
            ORDER BY company_id
            """,
            conn,
        )


# ============================================================
# LATEST MARKET CAP — ALL COMPANIES
# ============================================================


@st.cache_data(ttl=600)
def get_latest_market_cap_all():
    """Return latest market cap all."""
    with _connect() as conn:
        return pd.read_sql_query(
            """
            WITH ranked AS (
                SELECT
                    mc.*,
                    ROW_NUMBER() OVER (
                        PARTITION BY
                            mc.company_id
                        ORDER BY
                            mc.year DESC
                    ) AS rn
                FROM market_cap mc
            )
            SELECT *
            FROM ranked
            WHERE rn = 1
            ORDER BY company_id
            """,
            conn,
        )


# ============================================================
# LATEST P&L — ALL COMPANIES
# ============================================================


@st.cache_data(ttl=600)
def get_latest_pl_all():
    """Return latest pl all."""
    with _connect() as conn:
        return pd.read_sql_query(
            """
            WITH ranked AS (
                SELECT
                    p.*,
                    ROW_NUMBER() OVER (
                        PARTITION BY
                            p.company_id
                        ORDER BY
                            p.year DESC
                    ) AS rn
                FROM profitandloss p
            )
            SELECT *
            FROM ranked
            WHERE rn = 1
            ORDER BY company_id
            """,
            conn,
        )


# ============================================================
# DASHBOARD MASTER DATASET
# ============================================================


@st.cache_data(ttl=600)
def get_dashboard_master():
    """Return dashboard master."""
    companies = get_companies()
    sectors = get_sectors()
    ratios = get_latest_ratios_all()
    market = get_latest_market_cap_all()
    pl = get_latest_pl_all()

    sector_columns = [
        "company_id",
        "broad_sector",
        "sub_sector",
        "index_weight_pct",
        "market_cap_category",
    ]

    sector_columns = [col for col in sector_columns if col in sectors.columns]

    ratio_columns = [
        col
        for col in ratios.columns
        if col
        not in [
            "id",
            "rn",
        ]
    ]

    market_columns = [
        col
        for col in market.columns
        if col
        not in [
            "id",
            "rn",
            "year",
        ]
    ]

    pl_columns = [
        "company_id",
        "sales",
        "net_profit",
        "opm_percentage",
        "interest",
        "dividend_payout",
    ]

    pl_columns = [col for col in pl_columns if col in pl.columns]

    df = companies.merge(
        sectors[sector_columns],
        on="company_id",
        how="left",
    )

    df = df.merge(
        ratios[ratio_columns],
        on="company_id",
        how="left",
        suffixes=(
            "",
            "_ratio",
        ),
    )

    df = df.merge(
        market[market_columns],
        on="company_id",
        how="left",
        suffixes=(
            "",
            "_market",
        ),
    )

    df = df.merge(
        pl[pl_columns],
        on="company_id",
        how="left",
        suffixes=(
            "",
            "_pl",
        ),
    )

    return df


# ============================================================
# YEAR-SPECIFIC DASHBOARD DATA
# ============================================================


@st.cache_data(ttl=600)
def get_ratios_all_for_year(year):
    """Return ratios all for year."""
    year_text = str(year)

    with _connect() as conn:
        return pd.read_sql_query(
            """
            WITH ranked AS (
                SELECT
                    fr.*,
                    ROW_NUMBER() OVER (
                        PARTITION BY fr.company_id
                        ORDER BY
                            CASE
                                WHEN fr.return_on_equity_pct
                                     IS NOT NULL
                                THEN 0
                                ELSE 1
                            END,
                            fr.year DESC
                    ) AS rn
                FROM financial_ratios fr
                WHERE SUBSTR(fr.year, 1, 4) = ?
            )
            SELECT *
            FROM ranked
            WHERE rn = 1
            ORDER BY company_id
            """,
            conn,
            params=[year_text],
        )


@st.cache_data(ttl=600)
def get_market_cap_all_for_year(year):
    """Return market cap all for year."""
    year_text = str(year)

    with _connect() as conn:
        return pd.read_sql_query(
            """
            WITH ranked AS (
                SELECT
                    mc.*,
                    ROW_NUMBER() OVER (
                        PARTITION BY mc.company_id
                        ORDER BY mc.year DESC
                    ) AS rn
                FROM market_cap mc
                WHERE SUBSTR(mc.year, 1, 4) = ?
            )
            SELECT *
            FROM ranked
            WHERE rn = 1
            ORDER BY company_id
            """,
            conn,
            params=[year_text],
        )


@st.cache_data(ttl=600)
def get_pl_all_for_year(year):
    """Return pl all for year."""
    year_text = str(year)

    with _connect() as conn:
        return pd.read_sql_query(
            """
            WITH ranked AS (
                SELECT
                    p.*,
                    ROW_NUMBER() OVER (
                        PARTITION BY p.company_id
                        ORDER BY p.year DESC
                    ) AS rn
                FROM profitandloss p
                WHERE SUBSTR(p.year, 1, 4) = ?
            )
            SELECT *
            FROM ranked
            WHERE rn = 1
            ORDER BY company_id
            """,
            conn,
            params=[year_text],
        )


@st.cache_data(ttl=600)
def get_dashboard_year(year):
    """Return dashboard year."""
    companies = get_companies()
    sectors = get_sectors()
    ratios = get_ratios_all_for_year(year)
    market = get_market_cap_all_for_year(year)
    pl = get_pl_all_for_year(year)

    sector_cols = [
        "company_id",
        "broad_sector",
        "sub_sector",
        "index_weight_pct",
        "market_cap_category",
    ]

    ratio_cols = [col for col in ratios.columns if col not in ["id", "rn"]]

    market_cols = [col for col in market.columns if col not in ["id", "rn", "year"]]

    pl_cols = [
        "company_id",
        "sales",
        "net_profit",
        "opm_percentage",
        "interest",
        "dividend_payout",
    ]

    sector_cols = [col for col in sector_cols if col in sectors.columns]

    pl_cols = [col for col in pl_cols if col in pl.columns]

    df = companies.merge(
        sectors[sector_cols],
        on="company_id",
        how="left",
    )

    if not ratios.empty:
        df = df.merge(
            ratios[ratio_cols],
            on="company_id",
            how="left",
            suffixes=("", "_ratio"),
        )

    if not market.empty:
        df = df.merge(
            market[market_cols],
            on="company_id",
            how="left",
            suffixes=("", "_market"),
        )

    if not pl.empty:
        df = df.merge(
            pl[pl_cols],
            on="company_id",
            how="left",
            suffixes=("", "_pl"),
        )

    return df


# ============================================================
# SCREENER DATA
# ============================================================


@st.cache_data(ttl=600)
def get_screener_data():
    """Return screener data."""
    companies = get_companies()
    sectors = get_sectors()
    ratios = get_latest_ratios_all()
    market = get_latest_market_cap_all()
    pl = get_latest_pl_all()

    df = companies[
        [
            "company_id",
            "company_name",
        ]
    ].copy()

    sector_cols = [
        "company_id",
        "broad_sector",
        "sub_sector",
    ]

    ratio_cols = [
        "company_id",
        "return_on_equity_pct",
        "debt_to_equity",
        "free_cash_flow_cr",
        "revenue_cagr_5yr",
        "pat_cagr_5yr",
        "operating_profit_margin_pct",
        "interest_coverage",
        "dividend_payout_ratio_pct",
        "composite_quality_score",
    ]

    market_cols = [
        "company_id",
        "pe_ratio",
        "pb_ratio",
        "dividend_yield_pct",
        "market_cap_crore",
    ]

    pl_cols = [
        "company_id",
        "sales",
        "net_profit",
    ]

    sector_cols = [c for c in sector_cols if c in sectors.columns]

    ratio_cols = [c for c in ratio_cols if c in ratios.columns]

    market_cols = [c for c in market_cols if c in market.columns]

    pl_cols = [c for c in pl_cols if c in pl.columns]

    df = df.merge(
        sectors[sector_cols],
        on="company_id",
        how="left",
    )

    df = df.merge(
        ratios[ratio_cols],
        on="company_id",
        how="left",
    )

    df = df.merge(
        market[market_cols],
        on="company_id",
        how="left",
    )

    df = df.merge(
        pl[pl_cols],
        on="company_id",
        how="left",
    )

    return df


# ============================================================
# PEER DASHBOARD DATA
# ============================================================


@st.cache_data(ttl=600)
def get_peer_dashboard(group_name):
    """Return peer dashboard."""
    peers = get_peers(group_name)

    if peers.empty:
        return pd.DataFrame()

    ratios = get_latest_ratios_all()

    keep = [
        "company_id",
        "return_on_equity_pct",
        "return_on_capital_employed_pct",
        "net_profit_margin_pct",
        "debt_to_equity",
        "free_cash_flow_cr",
        "pat_cagr_5yr",
        "revenue_cagr_5yr",
        "composite_quality_score",
    ]

    keep = [col for col in keep if col in ratios.columns]

    df = peers.merge(
        ratios[keep],
        on="company_id",
        how="left",
    )

    return df


# ============================================================
# TREND ANALYSIS DATA
# ============================================================


@st.cache_data(ttl=600)
def get_company_trends(ticker):
    """Return company trends."""
    ratios = get_ratios(ticker)
    pl = get_pl(ticker)

    frames = []

    if not pl.empty:
        cols = [
            "year",
            "sales",
            "net_profit",
            "operating_profit",
            "opm_percentage",
            "eps",
        ]

        cols = [c for c in cols if c in pl.columns]

        frames.append(pl[cols].copy())

    if not ratios.empty:
        cols = [
            "year",
            "return_on_equity_pct",
            "return_on_capital_employed_pct",
            "net_profit_margin_pct",
            "debt_to_equity",
            "free_cash_flow_cr",
            "asset_turnover",
        ]

        cols = [c for c in cols if c in ratios.columns]

        ratio_df = ratios[cols].copy()

        if frames:
            frames[0] = frames[0].merge(
                ratio_df,
                on="year",
                how="outer",
            )
        else:
            frames.append(ratio_df)

    if not frames:
        return pd.DataFrame()

    result = frames[0]

    result = result.sort_values("year")

    return result


# ============================================================
# SECTOR ANALYSIS DATA
# ============================================================


@st.cache_data(ttl=600)
def get_sector_dashboard():
    """Return sector dashboard."""
    companies = get_companies()
    sectors = get_sectors()
    ratios = get_latest_ratios_all()
    market = get_latest_market_cap_all()
    pl = get_latest_pl_all()

    df = companies[
        [
            "company_id",
            "company_name",
        ]
    ].copy()

    sector_cols = [
        "company_id",
        "broad_sector",
        "sub_sector",
    ]

    ratio_cols = [
        "company_id",
        "return_on_equity_pct",
        "return_on_capital_employed_pct",
        "net_profit_margin_pct",
        "debt_to_equity",
        "revenue_cagr_5yr",
        "pat_cagr_5yr",
    ]

    market_cols = [
        "company_id",
        "market_cap_crore",
        "pe_ratio",
        "pb_ratio",
        "dividend_yield_pct",
    ]

    pl_cols = [
        "company_id",
        "sales",
        "net_profit",
    ]

    df = df.merge(
        sectors[[c for c in sector_cols if c in sectors.columns]],
        on="company_id",
        how="left",
    )

    df = df.merge(
        ratios[[c for c in ratio_cols if c in ratios.columns]],
        on="company_id",
        how="left",
    )

    df = df.merge(
        market[[c for c in market_cols if c in market.columns]],
        on="company_id",
        how="left",
    )

    df = df.merge(
        pl[[c for c in pl_cols if c in pl.columns]],
        on="company_id",
        how="left",
    )

    return df


# ============================================================
# ANNUAL REPORT DATA
# ============================================================


@st.cache_data(ttl=600)
def get_report_companies():
    """Return report companies."""
    with _connect() as conn:
        return pd.read_sql_query(
            """
            SELECT DISTINCT
                c.id AS company_id,
                c.company_name
            FROM companies c
            INNER JOIN documents d
                ON c.id = d.company_id
            ORDER BY c.company_name
            """,
            conn,
        )
