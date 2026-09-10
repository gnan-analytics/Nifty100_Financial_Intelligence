import pytest

from src.analytics.ratios import (
    calculate_asset_turnover,
    calculate_debt_to_equity,
    calculate_high_leverage_flag,
    calculate_icr_warning_flag,
    calculate_interest_coverage,
    calculate_net_debt,
    get_icr_label,
)


def test_debt_to_equity_normal():
    result = calculate_debt_to_equity(
        borrowings=500,
        equity_capital=100,
        reserves=900,
    )

    assert result == pytest.approx(0.5)


def test_debt_to_equity_debt_free():
    result = calculate_debt_to_equity(
        borrowings=0,
        equity_capital=100,
        reserves=900,
    )

    assert result == pytest.approx(0.0)


def test_high_debt_to_equity_flag():
    result = calculate_high_leverage_flag(
        debt_to_equity=6.0,
        broad_sector="Industrials",
    )

    assert result is True


def test_financial_sector_suppresses_high_leverage_flag():
    result = calculate_high_leverage_flag(
        debt_to_equity=8.0,
        broad_sector="Financials",
    )

    assert result is False


def test_interest_coverage_normal():
    result = calculate_interest_coverage(
        operating_profit=1000,
        other_income=100,
        interest=100,
    )

    assert result == pytest.approx(11.0)


def test_interest_coverage_zero_interest():
    result = calculate_interest_coverage(
        operating_profit=1000,
        other_income=100,
        interest=0,
    )

    assert result is None


def test_icr_label_debt_free():
    result = get_icr_label(
        interest_coverage=None,
        interest=0,
    )

    assert result == "Debt Free"


def test_icr_warning_flag():
    result = calculate_icr_warning_flag(
        interest_coverage=1.2,
    )

    assert result is True


def test_net_debt():
    result = calculate_net_debt(
        borrowings=1000,
        investments=300,
    )

    assert result == pytest.approx(700.0)


def test_asset_turnover_zero_assets():
    result = calculate_asset_turnover(
        sales=1000,
        total_assets=0,
    )

    assert result is None
