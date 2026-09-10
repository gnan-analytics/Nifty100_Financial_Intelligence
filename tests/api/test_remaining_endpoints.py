"""Tests for remaining API endpoints and integration consistency."""

from src.screener.engine import run_screener


def test_peer_group_endpoint(client):
    response = client.get(
        "/api/v1/peers/IT%20Services"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["peer_group_name"] == "IT Services"
    assert data["company_count"] == 5
    assert data["metric_count"] == 10
    assert len(data["metrics"]) == 10
    assert len(data["companies"]) == 5


def test_unknown_peer_group_returns_404(client):
    response = client.get(
        "/api/v1/peers/UNKNOWN"
    )

    assert response.status_code == 404


def test_tcs_peer_compare(client):
    response = client.get(
        "/api/v1/companies/TCS/peers/compare"
    )

    assert response.status_code == 200

    data = response.json()

    assert (
        data["company"]["company_id"]
        == "TCS"
    )

    assert (
        data["peer_group_name"]
        == "IT Services"
    )

    assert data["axis_count"] == 8
    assert len(data["axes"]) == 8


def test_market_cap_tcs(client):
    response = client.get(
        "/api/v1/market-cap/TCS"
    )

    assert response.status_code == 200

    data = response.json()

    assert (
        data["company"]["company_id"]
        == "TCS"
    )

    assert data["count"] == 6
    assert len(data["history"]) == 6

    years = [
        row["year"]
        for row in data["history"]
    ]

    assert years[0] == "2019-03"
    assert years[-1] == "2024-03"


def test_market_cap_invalid_ticker(client):
    response = client.get(
        "/api/v1/market-cap/INVALIDXYZ"
    )

    assert response.status_code == 404


def test_portfolio_stats(client):
    response = client.get(
        "/api/v1/portfolio/stats"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["company_universe"] == 92
    assert data["kpi_count"] == 10

    assert len(data["statistics"]) == 9
    assert len(data["kpis"]) == 10

    expected_statistics = {
        "p10",
        "p25",
        "p50",
        "p75",
        "p90",
        "mean",
        "std",
        "min",
        "max",
    }

    assert (
        set(data["statistics"])
        == expected_statistics
    )


def test_tcs_documents(client):
    response = client.get(
        "/api/v1/companies/TCS/documents"
    )

    assert response.status_code == 200

    data = response.json()

    assert (
        data["company"]["company_id"]
        == "TCS"
    )

    assert data["document_count"] == 16
    assert data["valid_url_count"] == 14
    assert len(data["documents"]) == 16

    assert all(
        "year" in row
        and "annual_report" in row
        and "is_url_valid" in row
        for row in data["documents"]
    )


def test_invalid_documents_ticker(client):
    response = client.get(
        "/api/v1/companies/INVALIDXYZ/documents"
    )

    assert response.status_code == 404


def test_screener_api_matches_engine(client):
    api_filters = {
        "min_roe": 15,
        "max_de": 1,
        "min_fcf": 0,
        "min_rev_cagr_5yr": 10,
    }

    response = client.get(
        "/api/v1/screener",
        params=api_filters,
    )

    assert response.status_code == 200

    api_data = response.json()

    engine_filters = {
        "roe": 15,
        "debt_to_equity": 1,
        "free_cash_flow": 0,
        "revenue_cagr_5yr": 10,
    }

    engine_df = run_screener(
        engine_filters
    )

    engine_df = engine_df.sort_values(
        by=[
            "composite_quality_score",
            "company_id",
        ],
        ascending=[
            False,
            True,
        ],
    ).reset_index(
        drop=True
    )

    api_ids = [
        row["company_id"]
        for row in api_data["companies"]
    ]

    engine_ids = (
        engine_df["company_id"]
        .astype(str)
        .tolist()
    )

    assert api_ids == engine_ids
