import pandas as pd


# =========================================================
# FREE CASH FLOW
# =========================================================

def calculate_free_cash_flow(
    operating_activity,
    investing_activity,
):
    """
    Free Cash Flow

    Formula:
        operating_activity + investing_activity

    Negative values are allowed.
    """

    if pd.isna(operating_activity):
        return None

    if pd.isna(investing_activity):
        return None

    try:
        operating_activity = float(
            operating_activity
        )

        investing_activity = float(
            investing_activity
        )

    except (TypeError, ValueError):
        return None

    return (
        operating_activity
        + investing_activity
    )


# =========================================================
# CFO / PAT RATIO
# =========================================================

def calculate_cfo_pat_ratio(
    operating_activity,
    net_profit,
):
    """
    CFO / PAT ratio.

    Returns None if PAT = 0.
    """

    if pd.isna(operating_activity):
        return None

    if pd.isna(net_profit):
        return None

    try:
        operating_activity = float(
            operating_activity
        )

        net_profit = float(
            net_profit
        )

    except (TypeError, ValueError):
        return None

    if net_profit == 0:
        return None

    return (
        operating_activity
        / net_profit
    )


# =========================================================
# CFO QUALITY SCORE
# =========================================================

def calculate_cfo_quality_score(
    cfo_pat_ratios,
):
    """
    Average CFO/PAT ratio.

    Classification:
        > 1.0       = High Quality
        0.5 to 1.0  = Moderate
        < 0.5       = Accrual Risk

    Returns:
        {
            "average_ratio": float | None,
            "label": str | None
        }
    """

    if cfo_pat_ratios is None:
        return {
            "average_ratio": None,
            "label": None,
        }

    valid_values = []

    for value in cfo_pat_ratios:

        if value is None:
            continue

        if pd.isna(value):
            continue

        try:
            valid_values.append(
                float(value)
            )

        except (TypeError, ValueError):
            continue

    if not valid_values:
        return {
            "average_ratio": None,
            "label": None,
        }

    average_ratio = (
        sum(valid_values)
        / len(valid_values)
    )

    if average_ratio > 1.0:
        label = "High Quality"

    elif average_ratio >= 0.5:
        label = "Moderate"

    else:
        label = "Accrual Risk"

    return {
        "average_ratio": average_ratio,
        "label": label,
    }


# =========================================================
# CAPEX INTENSITY
# =========================================================

def calculate_capex_intensity(
    investing_activity,
    sales,
):
    """
    CapEx Intensity %

    Formula:
        abs(investing_activity) / sales * 100

    Classification:
        < 3%  = Asset Light
        3-8%  = Moderate
        > 8%  = Capital Intensive
    """

    if pd.isna(investing_activity):
        return {
            "value": None,
            "label": None,
        }

    if pd.isna(sales):
        return {
            "value": None,
            "label": None,
        }

    try:
        investing_activity = float(
            investing_activity
        )

        sales = float(
            sales
        )

    except (TypeError, ValueError):
        return {
            "value": None,
            "label": None,
        }

    if sales == 0:
        return {
            "value": None,
            "label": None,
        }

    value = (
        abs(investing_activity)
        / sales
        * 100
    )

    if value < 3:
        label = "Asset Light"

    elif value <= 8:
        label = "Moderate"

    else:
        label = "Capital Intensive"

    return {
        "value": value,
        "label": label,
    }


# =========================================================
# FCF CONVERSION
# =========================================================

def calculate_fcf_conversion(
    free_cash_flow,
    operating_profit,
):
    """
    FCF Conversion Rate %

    Formula:
        FCF / operating_profit * 100

    Returns None if operating_profit = 0.
    """

    if pd.isna(free_cash_flow):
        return None

    if pd.isna(operating_profit):
        return None

    try:
        free_cash_flow = float(
            free_cash_flow
        )

        operating_profit = float(
            operating_profit
        )

    except (TypeError, ValueError):
        return None

    if operating_profit == 0:
        return None

    return (
        free_cash_flow
        / operating_profit
        * 100
    )


# =========================================================
# SIGN HELPER
# =========================================================

def get_sign(value):
    """
    Return:
        + for positive
        - for negative
        0 for zero
    """

    if value is None:
        return None

    if pd.isna(value):
        return None

    try:
        value = float(value)

    except (TypeError, ValueError):
        return None

    if value > 0:
        return "+"

    if value < 0:
        return "-"

    return "0"


# =========================================================
# CAPITAL ALLOCATION CLASSIFIER
# =========================================================

def classify_capital_allocation(
    cfo,
    cfi,
    cff,
    cfo_pat_ratio=None,
):
    """
    Classify capital allocation pattern.

    Required Sprint patterns:

        (+,-,-) = Reinvestor
        (+,-,-) with high CFO/PAT
                = Shareholder Returns
        (+,+,-) = Liquidating Assets
        (-,+,+) = Distress Signal
        (-,-,+) = Growth Funded by Debt
        (+,+,+) = Cash Accumulator
        (-,-,-) = Pre-Revenue
        (+,-,+) = Mixed

    Zero-sign cases fall back to Mixed.
    """

    cfo_sign = get_sign(
        cfo
    )

    cfi_sign = get_sign(
        cfi
    )

    cff_sign = get_sign(
        cff
    )

    pattern = (
        cfo_sign,
        cfi_sign,
        cff_sign,
    )

    if pattern == (
        "+",
        "-",
        "-",
    ):
        if (
            cfo_pat_ratio is not None
            and not pd.isna(
                cfo_pat_ratio
            )
            and float(
                cfo_pat_ratio
            ) > 1.0
        ):
            label = "Shareholder Returns"

        else:
            label = "Reinvestor"

    elif pattern == (
        "+",
        "+",
        "-",
    ):
        label = "Liquidating Assets"

    elif pattern == (
        "-",
        "+",
        "+",
    ):
        label = "Distress Signal"

    elif pattern == (
        "-",
        "-",
        "+",
    ):
        label = "Growth Funded by Debt"

    elif pattern == (
        "+",
        "+",
        "+",
    ):
        label = "Cash Accumulator"

    elif pattern == (
        "-",
        "-",
        "-",
    ):
        label = "Pre-Revenue"

    elif pattern == (
        "+",
        "-",
        "+",
    ):
        label = "Mixed"

    else:
        label = "Mixed"

    return {
        "cfo_sign": cfo_sign,
        "cfi_sign": cfi_sign,
        "cff_sign": cff_sign,
        "pattern_label": label,
    }


# =========================================================
# FULL CASH FLOW KPI CALCULATION
# =========================================================

def calculate_cashflow_kpis(
    cashflow_row,
    pnl_row,
):
    """
    Calculate Day 11 cash flow KPIs
    for one company-year.
    """

    free_cash_flow = (
        calculate_free_cash_flow(
            cashflow_row.get(
                "operating_activity"
            ),
            cashflow_row.get(
                "investing_activity"
            ),
        )
    )

    cfo_pat_ratio = (
        calculate_cfo_pat_ratio(
            cashflow_row.get(
                "operating_activity"
            ),
            pnl_row.get(
                "net_profit"
            ),
        )
    )

    capex = (
        calculate_capex_intensity(
            cashflow_row.get(
                "investing_activity"
            ),
            pnl_row.get(
                "sales"
            ),
        )
    )

    fcf_conversion = (
        calculate_fcf_conversion(
            free_cash_flow,
            pnl_row.get(
                "operating_profit"
            ),
        )
    )

    allocation = (
        classify_capital_allocation(
            cfo=cashflow_row.get(
                "operating_activity"
            ),
            cfi=cashflow_row.get(
                "investing_activity"
            ),
            cff=cashflow_row.get(
                "financing_activity"
            ),
            cfo_pat_ratio=cfo_pat_ratio,
        )
    )

    return {
        "free_cash_flow_cr": (
            free_cash_flow
        ),
        "cfo_pat_ratio": (
            cfo_pat_ratio
        ),
        "capex_intensity_pct": (
            capex["value"]
        ),
        "capex_intensity_label": (
            capex["label"]
        ),
        "fcf_conversion_pct": (
            fcf_conversion
        ),
        "cfo_sign": (
            allocation["cfo_sign"]
        ),
        "cfi_sign": (
            allocation["cfi_sign"]
        ),
        "cff_sign": (
            allocation["cff_sign"]
        ),
        "pattern_label": (
            allocation["pattern_label"]
        ),
    }