import math

import pandas as pd

# =========================================================
# CAGR FLAGS
# =========================================================

NORMAL = "NORMAL"
DECLINE_TO_LOSS = "DECLINE_TO_LOSS"
TURNAROUND = "TURNAROUND"
BOTH_NEGATIVE = "BOTH_NEGATIVE"
ZERO_BASE = "ZERO_BASE"
INSUFFICIENT = "INSUFFICIENT"


# =========================================================
# CORE CAGR CALCULATOR
# =========================================================


def calculate_cagr(
    start_value,
    end_value,
    years,
):
    """
    Calculate CAGR with Sprint 2 edge-case handling.

    Formula:
        ((end / start) ** (1 / years) - 1) * 100

    Returns:
        {
            "value": float | None,
            "flag": str
        }
    """

    if (
        start_value is None
        or end_value is None
        or pd.isna(start_value)
        or pd.isna(end_value)
        or years is None
    ):
        return {
            "value": None,
            "flag": INSUFFICIENT,
        }

    try:
        start_value = float(start_value)
        end_value = float(end_value)
        years = int(years)

    except (TypeError, ValueError):
        return {
            "value": None,
            "flag": INSUFFICIENT,
        }

    if years <= 0:
        return {
            "value": None,
            "flag": INSUFFICIENT,
        }

    if start_value == 0:
        return {
            "value": None,
            "flag": ZERO_BASE,
        }

    if start_value > 0 and end_value < 0:
        return {
            "value": None,
            "flag": DECLINE_TO_LOSS,
        }

    if start_value < 0 and end_value > 0:
        return {
            "value": None,
            "flag": TURNAROUND,
        }

    if start_value < 0 and end_value < 0:
        return {
            "value": None,
            "flag": BOTH_NEGATIVE,
        }

    if end_value == 0:
        return {
            "value": -100.0,
            "flag": NORMAL,
        }

    ratio = end_value / start_value

    cagr = (
        math.pow(
            ratio,
            1 / years,
        )
        - 1
    ) * 100

    return {
        "value": cagr,
        "flag": NORMAL,
    }


# =========================================================
# SERIES CAGR
# =========================================================


def calculate_series_cagr(
    values,
    window_years,
):
    """
    Calculate CAGR from an ordered series.

    A 5-year CAGR requires observations
    separated by 5 years, therefore at least
    6 annual observations are required.
    """

    if values is None:
        return {
            "value": None,
            "flag": INSUFFICIENT,
        }

    clean_values = list(values)

    required_observations = window_years + 1

    if len(clean_values) < required_observations:
        return {
            "value": None,
            "flag": INSUFFICIENT,
        }

    start_value = clean_values[-required_observations]

    end_value = clean_values[-1]

    return calculate_cagr(
        start_value=start_value,
        end_value=end_value,
        years=window_years,
    )


# =========================================================
# REVENUE CAGR
# =========================================================


def calculate_revenue_cagr(
    revenue_values,
    window_years,
):
    """Calculate revenue cagr."""
    return calculate_series_cagr(
        revenue_values,
        window_years,
    )


# =========================================================
# PAT CAGR
# =========================================================


def calculate_pat_cagr(
    pat_values,
    window_years,
):
    """Calculate pat cagr."""
    return calculate_series_cagr(
        pat_values,
        window_years,
    )


# =========================================================
# EPS CAGR
# =========================================================


def calculate_eps_cagr(
    eps_values,
    window_years,
):
    """Calculate eps cagr."""
    return calculate_series_cagr(
        eps_values,
        window_years,
    )


# =========================================================
# ALL GROWTH METRICS
# =========================================================


def calculate_growth_metrics(
    revenue_values,
    pat_values,
    eps_values,
):
    """
    Calculate 3Y, 5Y and 10Y CAGR for
    Revenue, PAT and EPS.
    """

    results = {}

    for years in (
        3,
        5,
        10,
    ):
        revenue = calculate_revenue_cagr(
            revenue_values,
            years,
        )

        pat = calculate_pat_cagr(
            pat_values,
            years,
        )

        eps = calculate_eps_cagr(
            eps_values,
            years,
        )

        results[f"revenue_cagr_{years}yr"] = revenue["value"]

        results[f"revenue_cagr_{years}yr_flag"] = revenue["flag"]

        results[f"pat_cagr_{years}yr"] = pat["value"]

        results[f"pat_cagr_{years}yr_flag"] = pat["flag"]

        results[f"eps_cagr_{years}yr"] = eps["value"]

        results[f"eps_cagr_{years}yr_flag"] = eps["flag"]

    return results
