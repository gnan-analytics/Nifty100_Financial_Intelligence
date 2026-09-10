import pytest

from src.screener.engine import (
    load_config,
    run_preset,
)


def test_six_presets_exist():
    config = load_config()

    expected = {
        "quality_compounder",
        "value_pick",
        "growth_accelerator",
        "dividend_champion",
        "debt_free_blue_chip",
        "turnaround_watch",
    }

    assert set(config["presets"].keys()) == expected


@pytest.mark.parametrize(
    "preset_name",
    [
        "quality_compounder",
        "value_pick",
        "growth_accelerator",
        "dividend_champion",
        "debt_free_blue_chip",
        "turnaround_watch",
    ],
)
def test_all_presets_run(preset_name):
    result = run_preset(preset_name)

    assert result is not None
    assert "company_id" in result.columns


def test_quality_compounder_conditions():
    df = run_preset("quality_compounder")

    assert len(df) > 0

    assert (df["return_on_equity_pct"] > 15).all()

    assert (df["free_cash_flow_cr"] > 0).all()

    assert (df["revenue_cagr_5yr"] > 10).all()

    non_financials = df[~df["is_financial"]]

    assert (non_financials["debt_to_equity"] < 1).all()


def test_value_pick_conditions():
    df = run_preset("value_pick")

    assert len(df) > 0

    assert (df["pe_ratio"] < 20).all()

    assert (df["pb_ratio"] < 3).all()

    assert (df["dividend_yield_pct"] > 1).all()

    non_financials = df[~df["is_financial"]]

    assert (non_financials["debt_to_equity"] < 2).all()


def test_growth_accelerator_conditions():
    df = run_preset("growth_accelerator")

    assert len(df) > 0

    assert (df["pat_cagr_5yr"] > 20).all()

    assert (df["revenue_cagr_5yr"] > 15).all()

    non_financials = df[~df["is_financial"]]

    assert (non_financials["debt_to_equity"] < 2).all()


def test_dividend_champion_conditions():
    df = run_preset("dividend_champion")

    assert len(df) > 0

    assert (df["dividend_yield_pct"] > 2).all()

    assert (df["dividend_payout_ratio_pct"] < 80).all()

    assert (df["free_cash_flow_cr"] > 0).all()


def test_debt_free_blue_chip_conditions():
    df = run_preset("debt_free_blue_chip")

    assert len(df) > 0

    assert (df["debt_to_equity"].abs() < 1e-9).all()

    assert (df["return_on_equity_pct"] > 12).all()

    assert (df["sales"] > 5000).all()


def test_turnaround_watch_conditions():
    df = run_preset("turnaround_watch")

    assert len(df) > 0

    assert (df["revenue_cagr_3yr"] > 10).all()

    assert (df["free_cash_flow_cr"] > 0).all()

    assert (df["de_declining_yoy"]).all()

    valid_years = df[df["previous_de_year"].notna()].copy()

    assert len(valid_years) == len(df)


def test_preset_counts_documented():
    """
    Sprint brief targets 5-50 companies per preset.

    The supplied dataset has two legitimate exceptions:
    Value Pick = 2
    Debt-Free Blue Chip = 2.

    Do not weaken the official business thresholds
    merely to force a 5-company minimum.
    """

    expected_ranges = {
        "quality_compounder": (5, 50),
        "growth_accelerator": (5, 50),
        "dividend_champion": (5, 50),
        "turnaround_watch": (5, 50),
    }

    for preset, (minimum, maximum) in expected_ranges.items():
        count = len(run_preset(preset))

        assert minimum <= count <= maximum

    assert len(run_preset("value_pick")) == 2

    assert len(run_preset("debt_free_blue_chip")) == 2
