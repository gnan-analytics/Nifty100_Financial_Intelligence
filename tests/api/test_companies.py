"""Tests for health and company API endpoints."""


def test_health_returns_200(client):
    response = client.get("/api/v1/health")

    assert response.status_code == 200


def test_health_status_ok(client):
    data = client.get("/api/v1/health").json()

    assert data["status"] == "ok"
    assert data["version"] == "1.0.0"


def test_health_reports_92_companies(client):
    data = client.get("/api/v1/health").json()

    assert data["db_row_counts"]["companies"] == 92


def test_companies_returns_92(client):
    response = client.get("/api/v1/companies")

    assert response.status_code == 200

    data = response.json()

    assert data["count"] == 92
    assert len(data["companies"]) == 92


def test_company_tcs_profile(client):
    response = client.get("/api/v1/companies/TCS")

    assert response.status_code == 200

    data = response.json()

    assert data["company"]["id"] == "TCS"
    assert data["company"]["company_name"]
    assert data["latest_kpis"] is not None


def test_company_lowercase_ticker(client):
    response = client.get("/api/v1/companies/tcs")

    assert response.status_code == 200
    assert response.json()["company"]["id"] == "TCS"


def test_invalid_company_returns_404(client):
    response = client.get("/api/v1/companies/INVALIDXYZ")

    assert response.status_code == 404


def test_company_search(client):
    response = client.get(
        "/api/v1/companies",
        params={
            "search": "TCS",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["count"] >= 1

    tickers = [company["id"] for company in data["companies"]]

    assert "TCS" in tickers


def test_company_financials_filter(client):
    response = client.get(
        "/api/v1/companies",
        params={
            "sector": "Financials",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["count"] == 23

    assert all(company["broad_sector"] == "Financials" for company in data["companies"])


def test_tcs_profit_loss_history(client):
    response = client.get("/api/v1/companies/TCS/pl")

    assert response.status_code == 200

    data = response.json()

    assert data["ticker"] == "TCS"
    assert data["count"] >= 10

    assert all(row["company_id"] == "TCS" for row in data["data"])


def test_tcs_ratio_history(client):
    response = client.get("/api/v1/companies/TCS/ratios")

    assert response.status_code == 200

    data = response.json()

    assert data["ticker"] == "TCS"
    assert data["count"] >= 10

    assert all(row["company_id"] == "TCS" for row in data["data"])


def test_tcs_tearsheet_pdf(client):
    response = client.get("/api/v1/companies/TCS/tearsheet")

    assert response.status_code == 200

    assert response.headers["content-type"] == "application/pdf"

    assert response.content.startswith(b"%PDF")
