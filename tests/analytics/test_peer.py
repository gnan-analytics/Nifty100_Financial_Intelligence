import numpy as np
import pandas as pd

from src.analytics.peer import (
    METRICS,
    calculate_peer_percentiles,
    load_peer_groups,
    percent_rank_sql,
)


def test_metric_count():
    assert len(METRICS) == 10


def test_exactly_11_peer_groups():
    peers = load_peer_groups()

    assert (
        peers["peer_group_name"]
        .nunique()
        == 11
    )


def test_percent_rank_basic():
    series = pd.Series(
        [10, 20, 30, 40, 50]
    )

    result = percent_rank_sql(
        series
    )

    expected = [
        0.0,
        25.0,
        50.0,
        75.0,
        100.0,
    ]

    assert np.allclose(
        result.values,
        expected,
    )


def test_percent_rank_inverse():
    series = pd.Series(
        [1, 2, 3, 4, 5]
    )

    result = percent_rank_sql(
        series,
        inverse=True,
    )

    expected = [
        100.0,
        75.0,
        50.0,
        25.0,
        0.0,
    ]

    assert np.allclose(
        result.values,
        expected,
    )


def test_percent_rank_ties():
    series = pd.Series(
        [10, 10, 20, 30]
    )

    result = percent_rank_sql(
        series
    )

    assert result.iloc[0] == 0.0
    assert result.iloc[1] == 0.0
    assert result.iloc[2] > 0.0
    assert result.iloc[3] == 100.0


def test_peer_percentile_output():
    df = calculate_peer_percentiles()

    assert len(df) > 0

    required = {
        "company_id",
        "peer_group_name",
        "metric",
        "value",
        "percentile_rank",
        "year",
    }

    assert required.issubset(
        df.columns
    )


def test_all_11_groups_present():
    df = calculate_peer_percentiles()

    assert (
        df["peer_group_name"]
        .nunique()
        == 11
    )


def test_all_10_metrics_present():
    df = calculate_peer_percentiles()

    assert (
        df["metric"].nunique()
        == 10
    )


def test_no_duplicate_peer_metric():
    df = calculate_peer_percentiles()

    duplicates = df.duplicated(
        subset=[
            "company_id",
            "peer_group_name",
            "metric",
        ]
    )

    assert not duplicates.any()


def test_percentiles_in_valid_range():
    df = calculate_peer_percentiles()

    values = df[
        "percentile_rank"
    ].dropna()

    assert (
        values >= 0
    ).all()

    assert (
        values <= 100
    ).all()


def test_debt_to_equity_is_inverse():
    df = calculate_peer_percentiles()

    subset = df[
        (
            df["peer_group_name"]
            == "IT Services"
        )
        & (
            df["metric"]
            == "debt_to_equity"
        )
    ].dropna(
        subset=[
            "value",
            "percentile_rank",
        ]
    )

    if len(subset) >= 2:
        lowest_de = subset.sort_values(
            "value"
        ).iloc[0]

        highest_de = subset.sort_values(
            "value"
        ).iloc[-1]

        assert (
            lowest_de[
                "percentile_rank"
            ]
            >=
            highest_de[
                "percentile_rank"
            ]
        )


def test_it_services_highest_roe_gets_highest_percentile():
    df = calculate_peer_percentiles()

    subset = df[
        (
            df["peer_group_name"]
            == "IT Services"
        )
        & (
            df["metric"]
            == "roe"
        )
    ].dropna(
        subset=[
            "value",
            "percentile_rank",
        ]
    )

    assert len(subset) > 0

    highest_value = subset[
        "value"
    ].max()

    highest_percentile = subset.loc[
        subset["value"]
        == highest_value,
        "percentile_rank",
    ].iloc[0]

    assert highest_percentile == 100.0
