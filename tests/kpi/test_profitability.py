import pytest

from src.analytics.ratios import (
    calculate_net_profit_margin,
    calculate_operating_profit_margin,
    calculate_roa,
    calculate_roce,
    calculate_roe,
    cross_check_opm,
    evaluate_roce_benchmark,
)

# =========================================================
# TEST 1 — NET PROFIT MARGIN NORMAL CASE
# =========================================================


def test_net_profit_margin_normal():
    result = calculate_net_profit_margin(
        net_profit=200,
        sales=1000,
    )

    assert result == pytest.approx(20.0)


# =========================================================
# TEST 2 — ZERO SALES
# =========================================================


def test_net_profit_margin_zero_sales():
    result = calculate_net_profit_margin(
        net_profit=200,
        sales=0,
    )

    assert result is None


# =========================================================
# TEST 3 — OPERATING PROFIT MARGIN
# =========================================================


def test_operating_profit_margin_normal():
    result = calculate_operating_profit_margin(
        operating_profit=250,
        sales=1000,
    )

    assert result == pytest.approx(25.0)


# =========================================================
# TEST 4 — OPM CROSS-CHECK MISMATCH
# =========================================================


def test_opm_cross_check_mismatch():
    result = cross_check_opm(
        operating_profit=300,
        sales=1000,
        source_opm_percentage=20,
        company_id="TEST",
        year="2024-03",
    )

    assert result["computed_opm"] == pytest.approx(30.0)
    assert result["difference"] == pytest.approx(10.0)
    assert result["mismatch"] is True


# =========================================================
# TEST 5 — ROE NORMAL CASE
# =========================================================


def test_roe_normal():
    result = calculate_roe(
        net_profit=200,
        equity_capital=200,
        reserves=800,
    )

    assert result == pytest.approx(20.0)


# =========================================================
# TEST 6 — NEGATIVE EQUITY
# =========================================================


def test_roe_negative_equity():
    result = calculate_roe(
        net_profit=100,
        equity_capital=100,
        reserves=-200,
    )

    assert result is None


# =========================================================
# TEST 7 — ROCE NORMAL CASE
# =========================================================


def test_roce_normal():
    result = calculate_roce(
        ebit=200,
        equity_capital=100,
        reserves=600,
        borrowings=300,
    )

    assert result == pytest.approx(20.0)


# =========================================================
# TEST 8 — ROA ZERO ASSETS
# =========================================================


def test_roa_zero_assets():
    result = calculate_roa(
        net_profit=200,
        total_assets=0,
    )

    assert result is None


# =========================================================
# TEST 9 — FINANCIALS SECTOR ROCE BENCHMARK
# =========================================================


def test_financial_roce_sector_benchmark():
    result = evaluate_roce_benchmark(
        roce=14,
        broad_sector="Financials",
        sector_median_roce=12,
    )

    assert result["benchmark_type"] == "SECTOR_RELATIVE"
    assert result["benchmark_value"] == pytest.approx(12.0)
    assert result["above_benchmark"] is True
