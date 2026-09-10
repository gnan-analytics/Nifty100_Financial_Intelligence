"""REST API endpoints for historical valuation and market-cap data."""

import sqlite3
from pathlib import Path

from fastapi import APIRouter, HTTPException


router = APIRouter()

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DB_PATH = PROJECT_ROOT / "db" / "nifty100.db"


def _connect():
    """Return SQLite connection with named-column rows."""

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


@router.get("/market-cap/{ticker}")
def get_market_cap_history(
    ticker: str,
):
    """Return 2019-2024 historical market-cap and valuation multiples."""

    ticker = ticker.strip().upper()

    if not ticker:
        raise HTTPException(
            status_code=400,
            detail="ticker cannot be empty",
        )

    with _connect() as conn:
        company = conn.execute(
            """
            SELECT
                id,
                company_name
            FROM companies
            WHERE UPPER(id) = ?
            """,
            (ticker,),
        ).fetchone()

        if company is None:
            raise HTTPException(
                status_code=404,
                detail=(
                    f"Unknown company ticker: "
                    f"{ticker}"
                ),
            )

        rows = conn.execute(
            """
            SELECT
                year,
                market_cap_crore,
                enterprise_value_crore,
                pe_ratio,
                pb_ratio,
                ev_ebitda,
                dividend_yield_pct
            FROM market_cap
            WHERE UPPER(company_id) = ?
              AND CAST(substr(year, 1, 4) AS INTEGER)
                  BETWEEN 2019 AND 2024
            ORDER BY year
            """,
            (ticker,),
        ).fetchall()

    history = [
        dict(row)
        for row in rows
    ]

    return {
        "company": {
            "company_id": ticker,
            "company_name": (
                company["company_name"]
            ),
        },
        "period": {
            "from_year": "2019-03",
            "to_year": "2024-03",
        },
        "count": len(history),
        "history": history,
    }
