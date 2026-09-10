"""Tests for screener and sector API endpoints."""


def test_screener_returns_200(client):
    response = client.get("/api/v1/screener")

    assert response.status_code == 200

    data = response.json()

    assert "count" in data
    assert "companies" in data


def test_screener_quality_filter(client):
    response = client.get(
        "/api/v1/screener",
        params={
            "min_roe": 15,
            "max_de": 1,
            "min_fcf": 0,
            "min_rev_cagr_5yr": 10,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["count"] == 22
    assert len(data["companies"]) == 22


def test_screener_rank_order(client):
    response = client.get("/api/v1/screener")

    data = response.json()

    ranks = [row["rank"] for row in data["companies"]]

    assert ranks == list(
        range(
            1,
            len(ranks) + 1,
        )
    )


def test_screener_invalid_max_de(client):
    response = client.get(
        "/api/v1/screener",
        params={
            "max_de": -1,
        },
    )

    assert response.status_code == 400


def test_screener_invalid_max_pe(client):
    response = client.get(
        "/api/v1/screener",
        params={
            "max_pe": -1,
        },
    )

    assert response.status_code == 400


def test_sectors_returns_200(client):
    response = client.get("/api/v1/sectors")

    assert response.status_code == 200


def test_sectors_count_matches_source(client):
    response = client.get("/api/v1/sectors")

    data = response.json()

    assert data["count"] == 10
    assert len(data["sectors"]) == 10


def test_sector_company_total_is_92(client):
    response = client.get("/api/v1/sectors")

    data = response.json()

    total = sum(row["company_count"] for row in data["sectors"])

    assert total == 92


def test_it_sector_alias(client):
    response = client.get("/api/v1/sectors/IT/companies")

    assert response.status_code == 200

    data = response.json()

    assert data["sector"] == "Information Technology"

    assert data["count"] == 5


def test_financials_sector(client):
    response = client.get("/api/v1/sectors/Financials/companies")

    assert response.status_code == 200

    data = response.json()

    assert data["count"] == 23


def test_unknown_sector_returns_404(client):
    response = client.get("/api/v1/sectors/UNKNOWNSECTOR/companies")

    assert response.status_code == 404
