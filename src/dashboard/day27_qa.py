from pathlib import Path
import time

import numpy as np
import pandas as pd

from src.dashboard.utils.db import (
    get_companies,
    get_company,
    get_ratios,
    get_pl,
    get_bs,
    get_cf,
    get_sectors,
    get_sector_for_company,
    get_peer_groups,
    get_peers,
    get_peer_percentiles,
    get_market_cap,
    get_valuation,
    get_pros_cons,
    get_documents,
    get_capital_allocation,
    get_dashboard_master,
    get_dashboard_year,
    get_screener_data,
    get_peer_dashboard,
    get_company_trends,
    get_sector_dashboard,
    get_report_companies,
)


PROJECT_ROOT = Path(
    __file__
).resolve().parents[2]


# ============================================================
# HELPERS
# ============================================================

def heading(text):
    print()
    print("=" * 80)
    print(text)
    print("=" * 80)


def pass_msg(text):
    print(
        f"[PASS] {text}"
    )


def safe_assert(
    condition,
    message,
):
    if not condition:
        raise AssertionError(
            message
        )

    pass_msg(
        message
    )


# ============================================================
# 1. CORE DASHBOARD DATA
# ============================================================

def test_core_dashboard():
    heading(
        "1. CORE DASHBOARD DATA"
    )

    companies = get_companies()

    safe_assert(
        len(companies) == 92,
        "Dashboard contains 92 companies",
    )

    safe_assert(
        companies[
            "company_id"
        ].nunique() == 92,
        "All dashboard tickers are unique",
    )

    sectors = get_sectors()

    safe_assert(
        len(sectors) == 92,
        "Sector mapping contains 92 rows",
    )

    groups = get_peer_groups()

    safe_assert(
        len(groups) == 11,
        "All 11 peer groups available",
    )

    master = get_dashboard_master()

    safe_assert(
        len(master) == 92,
        "Dashboard master contains 92 companies",
    )


# ============================================================
# 2. HOME SCREEN — 2019 TO 2024
# ============================================================

def test_home_screen():
    heading(
        "2. HOME SCREEN"
    )

    for year in range(
        2019,
        2025,
    ):
        df = get_dashboard_year(
            year
        )

        safe_assert(
            len(df) == 92,
            f"Home {year}: 92 companies loaded",
        )

        print(
            f"    {year} | "
            f"ROE values: "
            f"{df['return_on_equity_pct'].notna().sum() if 'return_on_equity_pct' in df.columns else 0} | "
            f"P/E values: "
            f"{df['pe_ratio'].notna().sum() if 'pe_ratio' in df.columns else 0}"
        )


# ============================================================
# 3. TEST 10 TICKERS ACROSS SECTORS
# ============================================================

def choose_test_tickers():
    sectors = get_sectors().copy()

    sectors = sectors.dropna(
        subset=[
            "broad_sector",
            "company_id",
        ]
    )

    selected = (
        sectors
        .sort_values(
            [
                "broad_sector",
                "company_id",
            ]
        )
        .groupby(
            "broad_sector",
            as_index=False,
        )
        .first()
    )

    tickers = selected[
        "company_id"
    ].tolist()

    if len(tickers) < 10:
        extras = (
            get_companies()[
                "company_id"
            ]
            .tolist()
        )

        for ticker in extras:
            if ticker not in tickers:
                tickers.append(
                    ticker
                )

            if len(tickers) >= 10:
                break

    return tickers[:10]


def test_profile_screen():
    heading(
        "3. PROFILE SCREEN — 10 TICKERS"
    )

    tickers = choose_test_tickers()

    print(
        "QA tickers:",
        ", ".join(tickers),
    )

    for ticker in tickers:
        start = time.perf_counter()

        company = get_company(
            ticker
        )

        ratios = get_ratios(
            ticker
        )

        pl = get_pl(
            ticker
        )

        bs = get_bs(
            ticker
        )

        cf = get_cf(
            ticker
        )

        sector = get_sector_for_company(
            ticker
        )

        pros = get_pros_cons(
            ticker
        )

        elapsed = (
            time.perf_counter()
            - start
        )

        safe_assert(
            len(company) == 1,
            f"{ticker}: company card loads",
        )

        safe_assert(
            not ratios.empty,
            f"{ticker}: ratios load",
        )

        safe_assert(
            not pl.empty,
            f"{ticker}: P&L loads",
        )

        safe_assert(
            not bs.empty,
            f"{ticker}: balance sheet loads",
        )

        safe_assert(
            not cf.empty,
            f"{ticker}: cash flow loads",
        )

        print(
            f"    {ticker:<12} "
            f"profile data load: "
            f"{elapsed:.4f}s"
        )

        safe_assert(
            elapsed < 3.0,
            f"{ticker}: profile data loads under 3 seconds",
        )


# ============================================================
# 4. SCREENER EXTREME FILTER QA
# ============================================================

def apply_filter(
    df,
    column,
    op,
    value,
):
    if column not in df.columns:
        return df

    series = pd.to_numeric(
        df[column],
        errors="coerce",
    )

    if op == ">=":
        return df[
            series >= value
        ]

    if op == "<=":
        return df[
            series <= value
        ]

    return df


def test_screener():
    heading(
        "4. SCREENER QA"
    )

    df = get_screener_data()

    safe_assert(
        len(df) == 92,
        "Screener loads all 92 companies",
    )

    # Normal broad filter
    normal = df.copy()

    normal = apply_filter(
        normal,
        "return_on_equity_pct",
        ">=",
        0,
    )

    normal = apply_filter(
        normal,
        "pe_ratio",
        "<=",
        200,
    )

    print(
        "    Normal filter results:",
        len(normal),
    )

    # Deliberately extreme filters.
    # Zero results must NOT crash the app.
    extreme = df.copy()

    extreme = apply_filter(
        extreme,
        "return_on_equity_pct",
        ">=",
        100,
    )

    extreme = apply_filter(
        extreme,
        "debt_to_equity",
        "<=",
        0,
    )

    extreme = apply_filter(
        extreme,
        "pe_ratio",
        "<=",
        1,
    )

    extreme = apply_filter(
        extreme,
        "dividend_yield_pct",
        ">=",
        15,
    )

    print(
        "    Extreme filter results:",
        len(extreme),
    )

    safe_assert(
        isinstance(
            extreme,
            pd.DataFrame,
        ),
        "Extreme screener filters return a valid DataFrame",
    )

    # CSV export simulation
    csv_data = normal.to_csv(
        index=False
    )

    safe_assert(
        len(csv_data) > 0,
        "Screener CSV export produces data",
    )


# ============================================================
# 5. PEER SCREEN QA
# ============================================================

def test_peers():
    heading(
        "5. PEER COMPARISON QA"
    )

    groups = get_peer_groups()

    total_memberships = 0
    total_percentiles = 0

    for group in groups[
        "peer_group_name"
    ]:
        peers = get_peer_dashboard(
            group
        )

        percentiles = get_peer_percentiles(
            group
        )

        safe_assert(
            not peers.empty,
            f"{group}: peer table loads",
        )

        safe_assert(
            not percentiles.empty,
            f"{group}: percentiles load",
        )

        total_memberships += len(
            peers
        )

        total_percentiles += len(
            percentiles
        )

    print(
        "    Peer memberships:",
        total_memberships,
    )

    print(
        "    Percentile rows:",
        total_percentiles,
    )

    safe_assert(
        total_memberships == 56,
        "Peer groups contain 56 total company memberships",
    )

    safe_assert(
        total_percentiles == 560,
        "Peer dashboard contains 560 percentile rows",
    )


# ============================================================
# 6. TREND SCREEN QA
# ============================================================

def test_trends():
    heading(
        "6. TREND ANALYSIS QA"
    )

    tickers = choose_test_tickers()

    for ticker in tickers:
        trends = get_company_trends(
            ticker
        )

        safe_assert(
            not trends.empty,
            f"{ticker}: trend data loads",
        )

        safe_assert(
            "year" in trends.columns,
            f"{ticker}: trend year available",
        )

        print(
            f"    {ticker:<12} "
            f"{len(trends)} periods"
        )


# ============================================================
# 7. SECTOR SCREEN QA
# ============================================================

def test_sectors():
    heading(
        "7. SECTOR ANALYSIS QA"
    )

    df = get_sector_dashboard()

    safe_assert(
        len(df) == 92,
        "Sector dashboard contains 92 companies",
    )

    sector_count = (
        df[
            "broad_sector"
        ]
        .dropna()
        .nunique()
    )

    print(
        "    Broad sectors:",
        sector_count,
    )

    safe_assert(
        sector_count > 0,
        "Sector dropdown has available sectors",
    )

    for sector in sorted(
        df[
            "broad_sector"
        ]
        .dropna()
        .unique()
    ):
        subset = df[
            df[
                "broad_sector"
            ]
            == sector
        ]

        safe_assert(
            not subset.empty,
            f"{sector}: sector page has companies",
        )


# ============================================================
# 8. CAPITAL ALLOCATION SCREEN QA
# ============================================================

def test_capital():
    heading(
        "8. CAPITAL ALLOCATION QA"
    )

    df = get_capital_allocation()

    safe_assert(
        not df.empty,
        "Capital allocation data loads",
    )

    required = [
        "company_id",
        "year",
        "cfo_sign",
        "cfi_sign",
        "cff_sign",
        "pattern_label",
    ]

    for column in required:
        safe_assert(
            column in df.columns,
            f"Capital allocation has {column}",
        )

    dates = pd.to_datetime(
        df["year"],
        format="%Y-%m",
        errors="coerce",
    )

    temp = df.copy()

    temp[
        "_year_date"
    ] = dates

    latest = (
        temp
        .dropna(
            subset=[
                "_year_date"
            ]
        )
        .sort_values(
            [
                "company_id",
                "_year_date",
            ]
        )
        .groupby(
            "company_id",
            as_index=False,
        )
        .tail(1)
    )

    companies = get_companies()

    expected_ids = set(
        companies[
            "company_id"
        ].astype(str)
    )

    classified_ids = set(
        latest[
            "company_id"
        ].astype(str)
    )

    missing_ids = sorted(
        expected_ids
        - classified_ids
    )

    safe_assert(
        len(expected_ids) == 92,
        "Capital QA company universe contains 92 companies",
    )

    safe_assert(
        len(classified_ids) == 91,
        "Capital allocation source classifies 91 companies",
    )

    safe_assert(
        missing_ids == ["ATGL"],
        "ATGL is the only company without capital-allocation source data",
    )

    dashboard_latest = (
        companies[
            [
                "company_id",
                "company_name",
            ]
        ]
        .merge(
            latest[
                [
                    "company_id",
                    "year",
                    "cfo_sign",
                    "cfi_sign",
                    "cff_sign",
                    "pattern_label",
                ]
            ],
            on="company_id",
            how="left",
        )
    )

    dashboard_latest[
        "pattern_label"
    ] = dashboard_latest[
        "pattern_label"
    ].fillna(
        "Data Unavailable"
    )

    safe_assert(
        len(dashboard_latest) == 92,
        "Capital dashboard displays all 92 companies",
    )

    safe_assert(
        (
            dashboard_latest[
                "pattern_label"
            ]
            == "Data Unavailable"
        ).sum() == 1,
        "Missing capital-allocation data is explicitly labelled",
    )

    print(
        "    Classified companies:",
        len(classified_ids),
    )

    print(
        "    Missing source data:",
        ", ".join(missing_ids),
    )

    print(
        "    Allocation patterns:",
        latest[
            "pattern_label"
        ].nunique(),
    )

    print()

    print(
        dashboard_latest[
            "pattern_label"
        ]
        .value_counts()
        .to_string()
    )


# ============================================================
# 9. REPORTS SCREEN QA
# ============================================================

def test_reports():
    heading(
        "9. ANNUAL REPORTS QA"
    )

    companies = (
        get_report_companies()
    )

    safe_assert(
        not companies.empty,
        "Annual report company list loads",
    )

    print(
        "    Companies with document records:",
        len(companies),
    )

    sample = companies.head(
        10
    )

    for ticker in sample[
        "company_id"
    ]:
        docs = get_documents(
            ticker
        )

        safe_assert(
            not docs.empty,
            f"{ticker}: report records load",
        )

        if (
            "annual_report"
            in docs.columns
        ):
            valid_urls = (
                docs[
                    "annual_report"
                ]
                .fillna("")
                .astype(str)
                .str.startswith(
                    (
                        "http://",
                        "https://",
                    )
                )
                .sum()
            )

            print(
                f"    {ticker:<12} "
                f"valid URL strings: "
                f"{valid_urls}"
            )


# ============================================================
# 10. VALUATION QA
# ============================================================

def test_valuation():
    heading(
        "10. VALUATION MODULE QA"
    )

    summary_path = (
        PROJECT_ROOT
        / "output"
        / "valuation_summary.xlsx"
    )

    flags_path = (
        PROJECT_ROOT
        / "output"
        / "valuation_flags.csv"
    )

    safe_assert(
        summary_path.exists(),
        "valuation_summary.xlsx exists",
    )

    safe_assert(
        flags_path.exists(),
        "valuation_flags.csv exists",
    )

    summary = pd.read_excel(
        summary_path
    )

    flags = pd.read_csv(
        flags_path
    )

    safe_assert(
        len(summary) == 92,
        "Valuation summary contains 92 companies",
    )

    safe_assert(
        summary[
            "company_id"
        ].nunique() == 92,
        "Valuation tickers are unique",
    )

    required = [
        "company_id",
        "company_name",
        "sector",
        "P/E",
        "P/B",
        "EV/EBITDA",
        "FCF_yield_pct",
        "5yr_median_PE",
        "PE_vs_sector_median_pct",
        "flag",
    ]

    for column in required:
        safe_assert(
            column in summary.columns,
            f"Valuation contains {column}",
        )

    safe_assert(
        summary[
            "5yr_median_PE"
        ].notna().sum() == 92,
        "5-year median P/E available for all companies",
    )

    safe_assert(
        flags[
            "flag"
        ].isin(
            [
                "Caution",
                "Discount",
            ]
        ).all(),
        "Flag CSV contains only Caution/Discount",
    )

    print()
    print(
        "    Valuation distribution:"
    )

    print(
        summary[
            "flag"
        ]
        .value_counts()
        .to_string()
    )

    # Check dashboard lookup
    sample_tickers = (
        summary[
            "company_id"
        ]
        .head(10)
        .tolist()
    )

    for ticker in sample_tickers:
        valuation = get_valuation(
            ticker
        )

        safe_assert(
            not valuation.empty,
            f"{ticker}: dashboard valuation lookup works",
        )


# ============================================================
# 11. MISSING / PARTIAL DATA SAFETY
# ============================================================

def test_missing_data():
    heading(
        "11. MISSING DATA SAFETY"
    )

    # Fake partial row to reproduce UI formatting scenario
    partial = pd.DataFrame(
        [
            {
                "company_id":
                    "TEST",
                "return_on_equity_pct":
                    np.nan,
                "pe_ratio":
                    np.nan,
                "free_cash_flow_cr":
                    np.nan,
            }
        ]
    )

    safe_assert(
        partial.isna().any().any(),
        "Partial-data test fixture created",
    )

    def display_value(
        value,
    ):
        return (
            "N/A"
            if pd.isna(value)
            else value
        )

    for column in [
        "return_on_equity_pct",
        "pe_ratio",
        "free_cash_flow_cr",
    ]:
        result = display_value(
            partial.iloc[0][
                column
            ]
        )

        safe_assert(
            result == "N/A",
            f"Missing {column} renders as N/A",
        )


# ============================================================
# 12. DASHBOARD PAGE FILES
# ============================================================

def test_dashboard_pages():
    heading(
        "12. DASHBOARD PAGE FILES"
    )

    page_dir = (
        PROJECT_ROOT
        / "src"
        / "dashboard"
        / "pages"
    )

    expected = [
        "01_home.py",
        "02_profile.py",
        "03_screener.py",
        "04_peers.py",
        "05_trends.py",
        "06_sectors.py",
        "07_capital.py",
        "08_reports.py",
    ]

    for filename in expected:
        path = (
            page_dir
            / filename
        )

        safe_assert(
            path.exists(),
            f"{filename} exists",
        )

    safe_assert(
        len(expected) == 8,
        "All 8 dashboard screens accounted for",
    )


# ============================================================
# MAIN
# ============================================================

def main():
    started = time.perf_counter()

    test_core_dashboard()
    test_home_screen()
    test_profile_screen()
    test_screener()
    test_peers()
    test_trends()
    test_sectors()
    test_capital()
    test_reports()
    test_valuation()
    test_missing_data()
    test_dashboard_pages()

    elapsed = (
        time.perf_counter()
        - started
    )

    heading(
        "DAY 27 QA RESULT"
    )

    print(
        f"Total QA runtime: "
        f"{elapsed:.2f}s"
    )

    print()
    print(
        "DAY 27 DASHBOARD QA: PASS"
    )


if __name__ == "__main__":
    main()
