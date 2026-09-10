"""REST API endpoint for company annual-report documents."""

import sqlite3
from pathlib import Path
from urllib.parse import urlparse

from fastapi import APIRouter, HTTPException


router = APIRouter()

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DB_PATH = PROJECT_ROOT / "db" / "nifty100.db"


def _connect():
    """Return SQLite connection with named-column rows."""

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _is_valid_url(value: str | None) -> bool:
    """Return True when a stored document value looks like a valid HTTP URL."""

    if value is None:
        return False

    cleaned = str(value).strip()

    if not cleaned:
        return False

    if cleaned.lower() in {
        "null",
        "none",
        "nan",
        "na",
        "n/a",
    }:
        return False

    parsed = urlparse(cleaned)

    return (
        parsed.scheme in {"http", "https"}
        and bool(parsed.netloc)
    )


@router.get(
    "/companies/{ticker}/documents"
)
def get_company_documents(
    ticker: str,
):
    """Return annual-report links for a company."""

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
                annual_report
            FROM documents
            WHERE UPPER(company_id) = ?
            ORDER BY year
            """,
            (ticker,),
        ).fetchall()

    documents = []

    for row in rows:
        raw_url = row["annual_report"]

        valid = _is_valid_url(
            raw_url
        )

        documents.append(
            {
                "year": row["year"],
                "annual_report": (
                    raw_url
                    if valid
                    else None
                ),
                "is_url_valid": valid,
            }
        )

    valid_count = sum(
        1
        for document in documents
        if document["is_url_valid"]
    )

    return {
        "company": {
            "company_id": ticker,
            "company_name": (
                company["company_name"]
            ),
        },
        "document_count": len(documents),
        "valid_url_count": valid_count,
        "documents": documents,
    }
