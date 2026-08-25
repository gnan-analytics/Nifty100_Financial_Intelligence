import pytest

from src.analytics.cashflow_kpis import (
    calculate_free_cash_flow,
    calculate_cfo_pat_ratio,
    calculate_cfo_quality_score,
    calculate_capex_intensity,
    calculate_fcf_conversion,
    classify_capital_allocation,
)


def test_free_cash_flow():
    result = calculate_free_cash_flow(
        operating_activity=1000,
        investing_activity=-400,
    )

    assert result == pytest.approx(
        600.0
    )


def test_negative_free_cash_flow_allowed():
    result = calculate_free_cash_flow(
        operating_activity=300,
        investing_activity=-500,
    )

    assert result == pytest.approx(
        -200.0
    )


def test_cfo_pat_ratio_zero_pat():
    result = calculate_cfo_pat_ratio(
        operating_activity=500,
        net_profit=0,
    )

    assert result is None


def test_cfo_quality_high():
    result = calculate_cfo_quality_score(
        [
            1.2,
            1.1,
            1.3,
            1.0,
            1.4,
        ]
    )

    assert result[
        "average_ratio"
    ] == pytest.approx(
        1.2
    )

    assert result[
        "label"
    ] == "High Quality"


def test_capex_intensity_asset_light():
    result = calculate_capex_intensity(
        investing_activity=-20,
        sales=1000,
    )

    assert result[
        "value"
    ] == pytest.approx(
        2.0
    )

    assert result[
        "label"
    ] == "Asset Light"


def test_capex_intensity_capital_intensive():
    result = calculate_capex_intensity(
        investing_activity=-100,
        sales=1000,
    )

    assert result[
        "value"
    ] == pytest.approx(
        10.0
    )

    assert result[
        "label"
    ] == "Capital Intensive"


def test_fcf_conversion_zero_operating_profit():
    result = calculate_fcf_conversion(
        free_cash_flow=500,
        operating_profit=0,
    )

    assert result is None


def test_reinvestor_pattern():
    result = classify_capital_allocation(
        cfo=100,
        cfi=-50,
        cff=-20,
        cfo_pat_ratio=0.8,
    )

    assert result[
        "pattern_label"
    ] == "Reinvestor"


def test_shareholder_returns_pattern():
    result = classify_capital_allocation(
        cfo=100,
        cfi=-50,
        cff=-20,
        cfo_pat_ratio=1.2,
    )

    assert result[
        "pattern_label"
    ] == "Shareholder Returns"


def test_growth_funded_by_debt_pattern():
    result = classify_capital_allocation(
        cfo=-100,
        cfi=-50,
        cff=200,
    )

    assert result[
        "pattern_label"
    ] == "Growth Funded by Debt"
