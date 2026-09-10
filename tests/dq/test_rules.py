"""Unit tests for Sprint 1 data-quality validation rules."""

import pandas as pd

from src.etl.validator import (
    generate_dq15_balance_info,
    validate_balance_sheet,
    validate_company_year_uniqueness,
    validate_coverage,
    validate_dividend_payout,
    validate_eps_sign,
    validate_fixed_assets,
    validate_fk_integrity,
    validate_net_cash,
    validate_opm,
    validate_pk_uniqueness,
    validate_positive_sales,
    validate_tax_rate,
    validate_ticker_format,
    validate_year_format,
)


def _assert_rule(failures, rule_id):
    """Assert that failures contain the expected DQ rule."""

    assert failures
    assert failures[0]["rule_id"] == rule_id


def test_dq01_duplicate_primary_key():
    df = pd.DataFrame(
        {
            "id": ["TCS", "TCS"],
        }
    )

    failures = validate_pk_uniqueness(
        "companies",
        df,
        ["id"],
    )

    _assert_rule(failures, "DQ-01")
    assert len(failures) == 2


def test_dq02_duplicate_company_year():
    df = pd.DataFrame(
        {
            "company_id": ["TCS", "TCS"],
            "year": ["2024-03", "2024-03"],
        }
    )

    failures = validate_company_year_uniqueness(
        "profitandloss",
        df,
    )

    _assert_rule(failures, "DQ-02")
    assert len(failures) == 2


def test_dq03_orphan_company():
    df = pd.DataFrame(
        {
            "company_id": ["TCS", "UNKNOWN"],
            "year": ["2024-03", "2024-03"],
        }
    )

    failures = validate_fk_integrity(
        "profitandloss",
        df,
        {"TCS"},
    )

    _assert_rule(failures, "DQ-03")
    assert len(failures) == 1
    assert failures[0]["company_id"] == "UNKNOWN"


def test_dq04_balance_sheet_mismatch():
    df = pd.DataFrame(
        {
            "company_id": ["TCS"],
            "year": ["2024-03"],
            "total_assets": [1000.0],
            "total_liabilities": [900.0],
        }
    )

    failures = validate_balance_sheet(
        df
    )

    _assert_rule(failures, "DQ-04")


def test_dq05_opm_mismatch():
    df = pd.DataFrame(
        {
            "company_id": ["TCS"],
            "year": ["2024-03"],
            "sales": [1000.0],
            "operating_profit": [200.0],
            "opm_percentage": [10.0],
        }
    )

    failures = validate_opm(
        df
    )

    _assert_rule(failures, "DQ-05")


def test_dq06_non_positive_sales():
    df = pd.DataFrame(
        {
            "company_id": ["TESTCO"],
            "year": ["2024-03"],
            "sales": [0.0],
        }
    )

    failures = validate_positive_sales(
        df,
        bank_tickers=set(),
    )

    _assert_rule(failures, "DQ-06")


def test_dq06_bank_is_excluded():
    df = pd.DataFrame(
        {
            "company_id": ["HDFCBANK"],
            "year": ["2024-03"],
            "sales": [0.0],
        }
    )

    failures = validate_positive_sales(
        df,
        bank_tickers={"HDFCBANK"},
    )

    assert failures == []


def test_dq07_invalid_year():
    df = pd.DataFrame(
        {
            "company_id": ["TCS"],
            "year": ["TTM"],
        }
    )

    failures = validate_year_format(
        "profitandloss",
        df,
    )

    _assert_rule(failures, "DQ-07")


def test_dq07_invalid_month():
    df = pd.DataFrame(
        {
            "company_id": ["TCS"],
            "year": ["2024-13"],
        }
    )

    failures = validate_year_format(
        "profitandloss",
        df,
    )

    _assert_rule(failures, "DQ-07")


def test_dq08_ticker_not_normalized():
    df = pd.DataFrame(
        {
            "company_id": [" tcs "],
            "year": ["2024-03"],
        }
    )

    failures = validate_ticker_format(
        "profitandloss",
        df,
    )

    _assert_rule(failures, "DQ-08")


def test_dq09_net_cash_mismatch():
    df = pd.DataFrame(
        {
            "company_id": ["TCS"],
            "year": ["2024-03"],
            "operating_activity": [100.0],
            "investing_activity": [-20.0],
            "financing_activity": [-10.0],
            "net_cash_flow": [100.0],
        }
    )

    failures = validate_net_cash(
        df
    )

    _assert_rule(failures, "DQ-09")


def test_dq10_negative_fixed_assets():
    df = pd.DataFrame(
        {
            "company_id": ["TCS"],
            "year": ["2024-03"],
            "fixed_assets": [-10.0],
        }
    )

    failures = validate_fixed_assets(
        df
    )

    _assert_rule(failures, "DQ-10")


def test_dq11_invalid_tax_rate():
    df = pd.DataFrame(
        {
            "company_id": ["TCS"],
            "year": ["2024-03"],
            "tax_percentage": [75.0],
        }
    )

    failures = validate_tax_rate(
        df
    )

    _assert_rule(failures, "DQ-11")


def test_dq12_excessive_dividend_payout():
    df = pd.DataFrame(
        {
            "company_id": ["TCS"],
            "year": ["2024-03"],
            "dividend_payout": [250.0],
        }
    )

    failures = validate_dividend_payout(
        df
    )

    _assert_rule(failures, "DQ-12")


def test_dq14_eps_sign_mismatch():
    df = pd.DataFrame(
        {
            "company_id": ["TCS"],
            "year": ["2024-03"],
            "net_profit": [100.0],
            "eps": [-2.0],
        }
    )

    failures = validate_eps_sign(
        df
    )

    _assert_rule(failures, "DQ-14")


def test_dq15_balance_information():
    df = pd.DataFrame(
        {
            "company_id": ["TCS"],
            "year": ["2024-03"],
            "total_assets": [1000.0],
            "total_liabilities": [1000.0],
        }
    )

    result = generate_dq15_balance_info(
        df
    )

    assert len(result) == 1
    assert result.iloc[0]["rule_id"] == "DQ-15"
    assert bool(
        result.iloc[0]["strict_match"]
    ) is True
    assert result.iloc[0]["difference"] == 0


def test_dq16_insufficient_history():
    companies = pd.DataFrame(
        {
            "id": ["TCS"],
        }
    )

    years = [
        "2022-03",
        "2023-03",
        "2024-03",
    ]

    datasets = {
        "profitandloss": pd.DataFrame(
            {
                "company_id": ["TCS"] * 3,
                "year": years,
            }
        ),
        "balancesheet": pd.DataFrame(
            {
                "company_id": ["TCS"] * 3,
                "year": years,
            }
        ),
        "cashflow": pd.DataFrame(
            {
                "company_id": ["TCS"] * 3,
                "year": years,
            }
        ),
    }

    failures = validate_coverage(
        companies,
        datasets,
    )

    assert len(failures) == 3
    assert all(
        failure["rule_id"] == "DQ-16"
        for failure in failures
    )


def test_clean_rows_produce_no_failures():
    pnl = pd.DataFrame(
        {
            "company_id": ["TCS"],
            "year": ["2024-03"],
            "sales": [1000.0],
            "operating_profit": [200.0],
            "opm_percentage": [20.0],
            "tax_percentage": [25.0],
            "dividend_payout": [50.0],
            "net_profit": [100.0],
            "eps": [10.0],
        }
    )

    assert validate_company_year_uniqueness(
        "profitandloss",
        pnl,
    ) == []

    assert validate_year_format(
        "profitandloss",
        pnl,
    ) == []

    assert validate_ticker_format(
        "profitandloss",
        pnl,
    ) == []

    assert validate_positive_sales(
        pnl,
        bank_tickers=set(),
    ) == []

    assert validate_opm(
        pnl
    ) == []

    assert validate_tax_rate(
        pnl
    ) == []

    assert validate_dividend_payout(
        pnl
    ) == []

    assert validate_eps_sign(
        pnl
    ) == []
