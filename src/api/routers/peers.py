"""REST API endpoints for peer-group analysis."""

import sqlite3
from pathlib import Path

import pandas as pd
from fastapi import APIRouter, HTTPException

from src.analytics.peer import METRICS
from src.analytics.radar import RADAR_METRICS
from src.screener.engine import (
    load_screener_dataframe,
)


router = APIRouter()

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DB_PATH = PROJECT_ROOT / "db" / "nifty100.db"


def _connect():
    """Return SQLite connection with named-column rows."""

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _resolve_group(
    group_name: str,
    conn: sqlite3.Connection,
) -> str:
    """Resolve peer-group name case-insensitively."""

    cleaned = group_name.strip()

    if not cleaned:
        raise HTTPException(
            status_code=400,
            detail="group_name cannot be empty",
        )

    rows = conn.execute(
        """
        SELECT DISTINCT peer_group_name
        FROM peer_groups
        ORDER BY peer_group_name
        """
    ).fetchall()

    available = [
        row["peer_group_name"]
        for row in rows
    ]

    matched = next(
        (
            value
            for value in available
            if value.lower() == cleaned.lower()
        ),
        None,
    )

    if matched is None:
        raise HTTPException(
            status_code=404,
            detail={
                "message": (
                    f"Unknown peer group: {group_name}"
                ),
                "available_peer_groups": (
                    available
                ),
            },
        )

    return matched


def _score_lookup():
    """Return latest composite score by company."""

    df = load_screener_dataframe(DB_PATH)

    if df.empty:
        return {}

    return {
        str(row["company_id"]): (
            None
            if pd.isna(
                row.get(
                    "composite_quality_score"
                )
            )
            else float(
                row[
                    "composite_quality_score"
                ]
            )
        )
        for _, row in df.iterrows()
    }


@router.get("/peers/{group_name}")
def get_peer_group(
    group_name: str,
):
    """Return all companies and ten percentile metrics for a peer group."""

    with _connect() as conn:
        resolved_group = _resolve_group(
            group_name,
            conn,
        )

        members = conn.execute(
            """
            SELECT
                pg.company_id,
                c.company_name,
                pg.is_benchmark
            FROM peer_groups pg
            LEFT JOIN companies c
                ON c.id = pg.company_id
            WHERE pg.peer_group_name = ?
            ORDER BY
                pg.is_benchmark DESC,
                pg.company_id
            """,
            (resolved_group,),
        ).fetchall()

        percentile_rows = conn.execute(
            """
            SELECT
                company_id,
                metric,
                value,
                percentile_rank,
                year
            FROM peer_percentiles
            WHERE peer_group_name = ?
            ORDER BY
                company_id,
                metric
            """,
            (resolved_group,),
        ).fetchall()

    metric_map = {}

    for row in percentile_rows:
        company_id = row["company_id"]

        metric_map.setdefault(
            company_id,
            {},
        )

        metric_map[company_id][
            row["metric"]
        ] = {
            "value": row["value"],
            "percentile_rank": (
                row["percentile_rank"]
            ),
            "year": row["year"],
        }

    companies = []

    for member in members:
        company_id = member["company_id"]

        company_metrics = {}

        for metric_name in METRICS:
            company_metrics[
                metric_name
            ] = metric_map.get(
                company_id,
                {},
            ).get(
                metric_name,
                {
                    "value": None,
                    "percentile_rank": None,
                    "year": None,
                },
            )

        companies.append(
            {
                "company_id": company_id,
                "company_name": (
                    member["company_name"]
                ),
                "is_benchmark": bool(
                    member["is_benchmark"]
                ),
                "metrics": company_metrics,
            }
        )

    benchmark = next(
        (
            company
            for company in companies
            if company["is_benchmark"]
        ),
        None,
    )

    return {
        "peer_group_name": resolved_group,
        "company_count": len(companies),
        "metric_count": len(METRICS),
        "metrics": list(METRICS.keys()),
        "benchmark": (
            None
            if benchmark is None
            else {
                "company_id": (
                    benchmark["company_id"]
                ),
                "company_name": (
                    benchmark["company_name"]
                ),
            }
        ),
        "companies": companies,
    }


@router.get(
    "/companies/{ticker}/peers/compare"
)
def compare_company_to_peers(
    ticker: str,
):
    """Return eight-axis company, peer-average and benchmark comparison."""

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

        group_row = conn.execute(
            """
            SELECT
                peer_group_name
            FROM peer_groups
            WHERE UPPER(company_id) = ?
            ORDER BY peer_group_name
            LIMIT 1
            """,
            (ticker,),
        ).fetchone()

        if group_row is None:
            raise HTTPException(
                status_code=404,
                detail=(
                    f"No peer group found for "
                    f"{ticker}"
                ),
            )

        group_name = group_row[
            "peer_group_name"
        ]

        benchmark_row = conn.execute(
            """
            SELECT
                company_id
            FROM peer_groups
            WHERE peer_group_name = ?
              AND is_benchmark = 1
            LIMIT 1
            """,
            (group_name,),
        ).fetchone()

        if benchmark_row is None:
            raise HTTPException(
                status_code=404,
                detail=(
                    f"No benchmark configured for "
                    f"{group_name}"
                ),
            )

        benchmark_id = benchmark_row[
            "company_id"
        ]

        peer_rows = conn.execute(
            """
            SELECT
                pp.company_id,
                pp.metric,
                pp.percentile_rank
            FROM peer_percentiles pp
            WHERE pp.peer_group_name = ?
            """,
            (group_name,),
        ).fetchall()

        benchmark_company = conn.execute(
            """
            SELECT company_name
            FROM companies
            WHERE id = ?
            """,
            (benchmark_id,),
        ).fetchone()

    percentile_lookup = {}

    for row in peer_rows:
        percentile_lookup.setdefault(
            row["company_id"],
            {},
        )

        percentile_lookup[
            row["company_id"]
        ][row["metric"]] = (
            row["percentile_rank"]
        )

    scores = _score_lookup()

    radar_metric_names = [
        metric_name
        for metric_name, _
        in RADAR_METRICS
    ]

    labels = {
        metric_name: label
        for metric_name, label
        in RADAR_METRICS
    }

    axes = []

    company_ids = sorted(
        percentile_lookup.keys()
    )

    for metric_name in radar_metric_names:
        company_value = (
            percentile_lookup
            .get(ticker, {})
            .get(metric_name)
        )

        benchmark_value = (
            percentile_lookup
            .get(benchmark_id, {})
            .get(metric_name)
        )

        peer_values = [
            percentile_lookup[
                company_id
            ].get(metric_name)
            for company_id
            in company_ids
        ]

        peer_values = [
            value
            for value in peer_values
            if value is not None
        ]

        peer_average = (
            None
            if not peer_values
            else round(
                sum(peer_values)
                / len(peer_values),
                2,
            )
        )

        axes.append(
            {
                "metric": metric_name,
                "label": labels[
                    metric_name
                ],
                "company": company_value,
                "peer_average": (
                    peer_average
                ),
                "benchmark": (
                    benchmark_value
                ),
            }
        )

    group_scores = [
        scores.get(company_id)
        for company_id in company_ids
    ]

    group_scores = [
        value
        for value in group_scores
        if value is not None
    ]

    composite_peer_average = (
        None
        if not group_scores
        else round(
            sum(group_scores)
            / len(group_scores),
            2,
        )
    )

    axes.append(
        {
            "metric": (
                "composite_quality_score"
            ),
            "label": "Composite Score",
            "company": scores.get(ticker),
            "peer_average": (
                composite_peer_average
            ),
            "benchmark": scores.get(
                benchmark_id
            ),
        }
    )

    return {
        "company": {
            "company_id": ticker,
            "company_name": (
                company["company_name"]
            ),
        },
        "peer_group_name": group_name,
        "peer_company_count": len(
            company_ids
        ),
        "benchmark": {
            "company_id": benchmark_id,
            "company_name": (
                None
                if benchmark_company is None
                else benchmark_company[
                    "company_name"
                ]
            ),
        },
        "axis_count": len(axes),
        "axes": axes,
    }
