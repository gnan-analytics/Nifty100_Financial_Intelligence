import logging

import pandas as pd

logger = logging.getLogger(__name__)


# =========================================================
# GENERIC SAFE DIVISION
# =========================================================


def safe_divide(
    numerator,
    denominator,
):
    """Divide values safely."""
    if pd.isna(numerator):
        return None

    if pd.isna(denominator):
        return None

    try:
        numerator = float(numerator)
        denominator = float(denominator)

    except (TypeError, ValueError):
        return None

    if denominator == 0:
        return None

    return numerator / denominator


# =========================================================
# DAY 08 — PROFITABILITY RATIOS
# =========================================================


def calculate_net_profit_margin(
    net_profit,
    sales,
):
    """Calculate net profit margin."""
    result = safe_divide(
        net_profit,
        sales,
    )

    if result is None:
        return None

    return result * 100


def calculate_operating_profit_margin(
    operating_profit,
    sales,
):
    """Calculate operating profit margin."""
    result = safe_divide(
        operating_profit,
        sales,
    )

    if result is None:
        return None

    return result * 100


def cross_check_opm(
    operating_profit,
    sales,
    source_opm_percentage,
    company_id=None,
    year=None,
    tolerance=1.0,
):
    """Handle cross check opm."""
    computed_opm = calculate_operating_profit_margin(
        operating_profit,
        sales,
    )

    if computed_opm is None:
        return {
            "computed_opm": None,
            "source_opm": source_opm_percentage,
            "difference": None,
            "mismatch": False,
        }

    if pd.isna(source_opm_percentage):
        return {
            "computed_opm": computed_opm,
            "source_opm": None,
            "difference": None,
            "mismatch": False,
        }

    try:
        source_opm = float(source_opm_percentage)

    except (TypeError, ValueError):
        return {
            "computed_opm": computed_opm,
            "source_opm": None,
            "difference": None,
            "mismatch": False,
        }

    difference = abs(computed_opm - source_opm)

    mismatch = difference > tolerance

    if mismatch:
        logger.warning(
            "OPM mismatch | company=%s | year=%s | "
            "source=%.2f | computed=%.2f | difference=%.2f",
            company_id,
            year,
            source_opm,
            computed_opm,
            difference,
        )

    return {
        "computed_opm": computed_opm,
        "source_opm": source_opm,
        "difference": difference,
        "mismatch": mismatch,
    }


def calculate_roe(
    net_profit,
    equity_capital,
    reserves,
):
    """Calculate roe."""
    values = [
        net_profit,
        equity_capital,
        reserves,
    ]

    if any(pd.isna(value) for value in values):
        return None

    try:
        net_profit = float(net_profit)

        equity_capital = float(equity_capital)

        reserves = float(reserves)

    except (TypeError, ValueError):
        return None

    total_equity = equity_capital + reserves

    if total_equity <= 0:
        return None

    return net_profit / total_equity * 100


def calculate_roce(
    ebit,
    equity_capital,
    reserves,
    borrowings,
):
    """Calculate roce."""
    values = [
        ebit,
        equity_capital,
        reserves,
        borrowings,
    ]

    if any(pd.isna(value) for value in values):
        return None

    try:
        ebit = float(ebit)

        equity_capital = float(equity_capital)

        reserves = float(reserves)

        borrowings = float(borrowings)

    except (TypeError, ValueError):
        return None

    capital_employed = equity_capital + reserves + borrowings

    if capital_employed <= 0:
        return None

    return ebit / capital_employed * 100


def calculate_roa(
    net_profit,
    total_assets,
):
    """Calculate roa."""
    result = safe_divide(
        net_profit,
        total_assets,
    )

    if result is None:
        return None

    return result * 100


def is_financial_sector(
    broad_sector,
):
    """Return whether financial sector."""
    if broad_sector is None:
        return False

    if pd.isna(broad_sector):
        return False

    return str(broad_sector).strip().lower() == "financials"


def evaluate_roce_benchmark(
    roce,
    broad_sector,
    sector_median_roce=None,
):
    """Evaluate roce benchmark."""
    if roce is None:
        return {
            "roce": None,
            "benchmark_type": None,
            "benchmark_value": None,
            "above_benchmark": None,
        }

    if is_financial_sector(broad_sector):
        if sector_median_roce is None or pd.isna(sector_median_roce):
            return {
                "roce": roce,
                "benchmark_type": "SECTOR_RELATIVE",
                "benchmark_value": None,
                "above_benchmark": None,
            }

        benchmark = float(sector_median_roce)

        return {
            "roce": roce,
            "benchmark_type": "SECTOR_RELATIVE",
            "benchmark_value": benchmark,
            "above_benchmark": (roce > benchmark),
        }

    return {
        "roce": roce,
        "benchmark_type": "STANDARD",
        "benchmark_value": None,
        "above_benchmark": None,
    }


# =========================================================
# DAY 09 — LEVERAGE & EFFICIENCY RATIOS
# =========================================================


def calculate_debt_to_equity(
    borrowings,
    equity_capital,
    reserves,
):
    """
    Debt-to-Equity

    Formula:
        borrowings /
        (equity_capital + reserves)

    Rules:
        - borrowings = 0 -> return 0
        - total equity <= 0 -> return None
    """

    values = [
        borrowings,
        equity_capital,
        reserves,
    ]

    if any(pd.isna(value) for value in values):
        return None

    try:
        borrowings = float(borrowings)

        equity_capital = float(equity_capital)

        reserves = float(reserves)

    except (TypeError, ValueError):
        return None

    if borrowings == 0:
        return 0.0

    total_equity = equity_capital + reserves

    if total_equity <= 0:
        return None

    return borrowings / total_equity


def calculate_high_leverage_flag(
    debt_to_equity,
    broad_sector,
    threshold=5.0,
):
    """
    High leverage flag.

    Financials are excluded from the flag.
    """

    if debt_to_equity is None:
        return False

    if is_financial_sector(broad_sector):
        return False

    return debt_to_equity > threshold


def calculate_interest_coverage(
    operating_profit,
    other_income,
    interest,
):
    """
    Interest Coverage Ratio

    Formula:
        (operating_profit + other_income)
        / interest

    Returns None if interest = 0.
    """

    values = [
        operating_profit,
        other_income,
        interest,
    ]

    if any(pd.isna(value) for value in values):
        return None

    try:
        operating_profit = float(operating_profit)

        other_income = float(other_income)

        interest = float(interest)

    except (TypeError, ValueError):
        return None

    if interest == 0:
        return None

    return (operating_profit + other_income) / interest


def get_icr_label(
    interest_coverage,
    interest,
):
    """
    Display label for Interest Coverage.

    If interest = 0, company is treated
    as Debt Free.
    """

    if pd.isna(interest):
        return None

    try:
        interest = float(interest)

    except (TypeError, ValueError):
        return None

    if interest == 0:
        return "Debt Free"

    if interest_coverage is None:
        return None

    return f"{interest_coverage:.2f}"


def calculate_icr_warning_flag(
    interest_coverage,
    threshold=1.5,
):
    """
    Flag companies at risk of not
    covering interest payments.
    """

    if interest_coverage is None:
        return False

    return interest_coverage < threshold


def calculate_net_debt(
    borrowings,
    investments,
):
    """
    Net Debt

    Formula:
        borrowings - investments

    investments are used as a liquid
    asset proxy.
    """

    if pd.isna(borrowings):
        return None

    if pd.isna(investments):
        return None

    try:
        borrowings = float(borrowings)

        investments = float(investments)

    except (TypeError, ValueError):
        return None

    return borrowings - investments


def calculate_asset_turnover(
    sales,
    total_assets,
):
    """
    Asset Turnover

    Formula:
        sales / total_assets

    Returns None if total_assets = 0.
    """

    return safe_divide(
        sales,
        total_assets,
    )


# =========================================================
# FULL PROFITABILITY CALCULATION
# =========================================================


def calculate_profitability_ratios(
    pnl_row,
    bs_row,
    broad_sector=None,
    sector_median_roce=None,
):
    """Calculate profitability ratios."""
    npm = calculate_net_profit_margin(
        pnl_row.get("net_profit"),
        pnl_row.get("sales"),
    )

    opm_check = cross_check_opm(
        operating_profit=pnl_row.get("operating_profit"),
        sales=pnl_row.get("sales"),
        source_opm_percentage=pnl_row.get("opm_percentage"),
        company_id=pnl_row.get("company_id"),
        year=pnl_row.get("year"),
    )

    roe = calculate_roe(
        net_profit=pnl_row.get("net_profit"),
        equity_capital=bs_row.get("equity_capital"),
        reserves=bs_row.get("reserves"),
    )

    roce = calculate_roce(
        ebit=pnl_row.get("operating_profit"),
        equity_capital=bs_row.get("equity_capital"),
        reserves=bs_row.get("reserves"),
        borrowings=bs_row.get("borrowings"),
    )

    roa = calculate_roa(
        net_profit=pnl_row.get("net_profit"),
        total_assets=bs_row.get("total_assets"),
    )

    roce_benchmark = evaluate_roce_benchmark(
        roce=roce,
        broad_sector=broad_sector,
        sector_median_roce=sector_median_roce,
    )

    return {
        "net_profit_margin_pct": npm,
        "operating_profit_margin_pct": (opm_check["computed_opm"]),
        "opm_source_pct": (opm_check["source_opm"]),
        "opm_difference_pct": (opm_check["difference"]),
        "opm_mismatch_flag": (opm_check["mismatch"]),
        "return_on_equity_pct": roe,
        "return_on_capital_employed_pct": roce,
        "return_on_assets_pct": roa,
        "roce_benchmark_type": (roce_benchmark["benchmark_type"]),
        "roce_benchmark_value": (roce_benchmark["benchmark_value"]),
        "roce_above_benchmark": (roce_benchmark["above_benchmark"]),
    }


# =========================================================
# FULL LEVERAGE / EFFICIENCY CALCULATION
# =========================================================


def calculate_leverage_efficiency_ratios(
    pnl_row,
    bs_row,
    broad_sector=None,
):
    """Calculate leverage efficiency ratios."""
    debt_to_equity = calculate_debt_to_equity(
        borrowings=bs_row.get("borrowings"),
        equity_capital=bs_row.get("equity_capital"),
        reserves=bs_row.get("reserves"),
    )

    high_leverage_flag = calculate_high_leverage_flag(
        debt_to_equity,
        broad_sector,
    )

    interest_coverage = calculate_interest_coverage(
        operating_profit=pnl_row.get("operating_profit"),
        other_income=pnl_row.get("other_income"),
        interest=pnl_row.get("interest"),
    )

    icr_label = get_icr_label(
        interest_coverage,
        pnl_row.get("interest"),
    )

    icr_warning_flag = calculate_icr_warning_flag(interest_coverage)

    net_debt = calculate_net_debt(
        borrowings=bs_row.get("borrowings"),
        investments=bs_row.get("investments"),
    )

    asset_turnover = calculate_asset_turnover(
        sales=pnl_row.get("sales"),
        total_assets=bs_row.get("total_assets"),
    )

    return {
        "debt_to_equity": debt_to_equity,
        "high_leverage_flag": high_leverage_flag,
        "interest_coverage": interest_coverage,
        "icr_label": icr_label,
        "icr_warning_flag": icr_warning_flag,
        "net_debt": net_debt,
        "asset_turnover": asset_turnover,
    }
