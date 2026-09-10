import sqlite3
import time
from pathlib import Path

from fastapi import APIRouter

router = APIRouter()

DB_PATH = Path("db/nifty100.db")

START_TIME = time.time()

TABLES = [
    "companies",
    "profitandloss",
    "balancesheet",
    "cashflow",
    "analysis",
    "documents",
    "prosandcons",
    "sectors",
    "stock_prices",
    "market_cap",
]


@router.get("/health")
def health_check():
    """Return API health, uptime, version, and database row counts."""

    row_counts = {}

    with sqlite3.connect(DB_PATH) as conn:

        for table in TABLES:

            count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]

            row_counts[table] = count

    return {
        "status": "ok",
        "version": "1.0.0",
        "uptime_seconds": round(
            time.time() - START_TIME,
            2,
        ),
        "db_row_counts": row_counts,
    }
