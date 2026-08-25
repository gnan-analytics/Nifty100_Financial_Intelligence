import pytest

from src.analytics.cagr import (
    calculate_cagr,
    calculate_series_cagr,
    calculate_growth_metrics,
    NORMAL,
    DECLINE_TO_LOSS,
    TURNAROUND,
    BOTH_NEGATIVE,
    ZERO_BASE,
    INSUFFICIENT,
)


def test_normal_cagr():
    result = calculate_cagr(
        start_value=100,
        end_value=121,
        years=2,
    )

    assert result["value"] == pytest.approx(
        10.0
    )

    assert result["flag"] == NORMAL


def test_decline_to_loss():
    result = calculate_cagr(
        start_value=100,
        end_value=-20,
        years=5,
    )

    assert result["value"] is None
    assert result["flag"] == DECLINE_TO_LOSS


def test_turnaround():
    result = calculate_cagr(
        start_value=-100,
        end_value=200,
        years=5,
    )

    assert result["value"] is None
    assert result["flag"] == TURNAROUND


def test_both_negative():
    result = calculate_cagr(
        start_value=-100,
        end_value=-50,
        years=5,
    )

    assert result["value"] is None
    assert result["flag"] == BOTH_NEGATIVE


def test_zero_base():
    result = calculate_cagr(
        start_value=0,
        end_value=100,
        years=5,
    )

    assert result["value"] is None
    assert result["flag"] == ZERO_BASE


def test_insufficient_data():
    result = calculate_series_cagr(
        values=[
            100,
            110,
            120,
        ],
        window_years=5,
    )

    assert result["value"] is None
    assert result["flag"] == INSUFFICIENT


def test_three_year_cagr():
    result = calculate_series_cagr(
        values=[
            100,
            110,
            120,
            133.1,
        ],
        window_years=3,
    )

    assert result["value"] == pytest.approx(
        10.0
    )

    assert result["flag"] == NORMAL


def test_five_year_cagr():
    result = calculate_series_cagr(
        values=[
            100,
            110,
            121,
            133.1,
            146.41,
            161.051,
        ],
        window_years=5,
    )

    assert result["value"] == pytest.approx(
        10.0
    )

    assert result["flag"] == NORMAL


def test_end_value_zero():
    result = calculate_cagr(
        start_value=100,
        end_value=0,
        years=5,
    )

    assert result["value"] == pytest.approx(
        -100.0
    )

    assert result["flag"] == NORMAL


def test_growth_metrics_columns():
    values = [
        100,
        110,
        121,
        133.1,
        146.41,
        161.051,
    ]

    result = calculate_growth_metrics(
        revenue_values=values,
        pat_values=values,
        eps_values=values,
    )

    assert "revenue_cagr_3yr" in result
    assert "revenue_cagr_5yr" in result
    assert "revenue_cagr_10yr" in result

    assert "pat_cagr_3yr" in result
    assert "pat_cagr_5yr" in result
    assert "pat_cagr_10yr" in result

    assert "eps_cagr_3yr" in result
    assert "eps_cagr_5yr" in result
    assert "eps_cagr_10yr" in result

    assert (
        result["revenue_cagr_10yr_flag"]
        == INSUFFICIENT
    )