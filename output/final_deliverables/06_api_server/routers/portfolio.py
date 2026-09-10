"""REST API endpoint for portfolio-level KPI statistics."""

from pathlib import Path

import pandas as pd
from fastapi import APIRouter, HTTPException

router = APIRouter()

PROJECT_ROOT = Path(__file__).resolve().parents[3]
STATS_PATH = PROJECT_ROOT / "output" / "portfolio_stats.csv"


@router.get("/portfolio/stats")
def get_portfolio_stats():
    """Return P10-P90 statistics for the ten core portfolio KPIs."""

    if not STATS_PATH.exists():
        raise HTTPException(
            status_code=500,
            detail="portfolio_stats.csv not found",
        )

    df = pd.read_csv(STATS_PATH)

    expected_columns = [
        "kpi",
        "count",
        "p10",
        "p25",
        "p50",
        "p75",
        "p90",
        "mean",
        "std",
        "min",
        "max",
    ]

    missing = [column for column in expected_columns if column not in df.columns]

    if missing:
        raise HTTPException(
            status_code=500,
            detail={
                "message": "Invalid portfolio stats file",
                "missing_columns": missing,
            },
        )

    records = (
        df[expected_columns]
        .where(pd.notna(df[expected_columns]), None)
        .to_dict(orient="records")
    )

    for record in records:
        record["count"] = int(record["count"])

    return {
        "company_universe": 92,
        "kpi_count": len(records),
        "statistics": [
            "p10",
            "p25",
            "p50",
            "p75",
            "p90",
            "mean",
            "std",
            "min",
            "max",
        ],
        "kpis": records,
    }
