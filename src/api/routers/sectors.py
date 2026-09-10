"""REST API endpoints for sector summaries and sector companies."""

import sqlite3
from pathlib import Path

from fastapi import APIRouter, HTTPException


router = APIRouter()

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DB_PATH = PROJECT_ROOT / "db" / "nifty100.db"


SECTOR_ALIASES = {
    "it": "Information Technology",
    "information technology": "Information Technology",
    "financial": "Financials",
    "finance": "Financials",
    "consumer discretionary": "Consumer Discretionary",
    "consumer staples": "Consumer Staples",
    "communication services": "Communication Services",
    "healthcare": "Healthcare",
    "industrial": "Industrials",
    "industrials": "Industrials",
    "material": "Materials",
    "materials": "Materials",
    "energy": "Energy",
    "real estate": "Real Estate",
}


def _connect():
    """Return a SQLite connection with row access by column name."""

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _resolve_sector(
    sector: str,
    conn: sqlite3.Connection,
) -> str:
    """Resolve a sector name or supported alias."""

    cleaned = sector.strip()

    if not cleaned:
        raise HTTPException(
            status_code=400,
            detail="sector cannot be empty",
        )

    alias_match = SECTOR_ALIASES.get(
        cleaned.lower()
    )

    if alias_match is not None:
        cleaned = alias_match

    rows = conn.execute(
        """
        SELECT DISTINCT broad_sector
        FROM sectors
        WHERE broad_sector IS NOT NULL
        ORDER BY broad_sector
        """
    ).fetchall()

    available = [
        row["broad_sector"]
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
                    f"Unknown sector: {sector}"
                ),
                "available_sectors": available,
            },
        )

    return matched


@router.get("/sectors")
def list_sectors():
    """Return sector-level company counts and median financial metrics."""

    with _connect() as conn:
        rows = conn.execute(
            """
            WITH latest_ratios AS (
                SELECT *
                FROM (
                    SELECT
                        fr.*,
                        ROW_NUMBER() OVER (
                            PARTITION BY fr.company_id
                            ORDER BY
                                CASE
                                    WHEN substr(fr.year, 6, 2) = '03'
                                    THEN 0
                                    ELSE 1
                                END,
                                fr.year DESC
                        ) AS rn
                    FROM financial_ratios fr
                )
                WHERE rn = 1
            ),
            latest_market AS (
                SELECT *
                FROM (
                    SELECT
                        m.*,
                        ROW_NUMBER() OVER (
                            PARTITION BY m.company_id
                            ORDER BY m.year DESC
                        ) AS rn
                    FROM market_cap m
                )
                WHERE rn = 1
            )
            SELECT
                s.broad_sector,
                COUNT(DISTINCT s.company_id)
                    AS company_count
            FROM sectors s
            GROUP BY s.broad_sector
            ORDER BY s.broad_sector
            """
        ).fetchall()

        result = []

        for row in rows:
            sector = row["broad_sector"]

            roe_values = [
                r[0]
                for r in conn.execute(
                    """
                    WITH latest AS (
                        SELECT *
                        FROM (
                            SELECT
                                fr.*,
                                ROW_NUMBER() OVER (
                                    PARTITION BY fr.company_id
                                    ORDER BY
                                        CASE
                                            WHEN substr(fr.year, 6, 2) = '03'
                                            THEN 0
                                            ELSE 1
                                        END,
                                        fr.year DESC
                                ) AS rn
                            FROM financial_ratios fr
                        )
                        WHERE rn = 1
                    )
                    SELECT l.return_on_equity_pct
                    FROM latest l
                    JOIN sectors s
                        ON s.company_id = l.company_id
                    WHERE s.broad_sector = ?
                      AND l.return_on_equity_pct IS NOT NULL
                    ORDER BY l.return_on_equity_pct
                    """,
                    (sector,),
                ).fetchall()
            ]

            de_values = [
                r[0]
                for r in conn.execute(
                    """
                    WITH latest AS (
                        SELECT *
                        FROM (
                            SELECT
                                fr.*,
                                ROW_NUMBER() OVER (
                                    PARTITION BY fr.company_id
                                    ORDER BY
                                        CASE
                                            WHEN substr(fr.year, 6, 2) = '03'
                                            THEN 0
                                            ELSE 1
                                        END,
                                        fr.year DESC
                                ) AS rn
                            FROM financial_ratios fr
                        )
                        WHERE rn = 1
                    )
                    SELECT l.debt_to_equity
                    FROM latest l
                    JOIN sectors s
                        ON s.company_id = l.company_id
                    WHERE s.broad_sector = ?
                      AND l.debt_to_equity IS NOT NULL
                    ORDER BY l.debt_to_equity
                    """,
                    (sector,),
                ).fetchall()
            ]

            pe_values = [
                r[0]
                for r in conn.execute(
                    """
                    WITH latest AS (
                        SELECT *
                        FROM (
                            SELECT
                                m.*,
                                ROW_NUMBER() OVER (
                                    PARTITION BY m.company_id
                                    ORDER BY m.year DESC
                                ) AS rn
                            FROM market_cap m
                        )
                        WHERE rn = 1
                    )
                    SELECT l.pe_ratio
                    FROM latest l
                    JOIN sectors s
                        ON s.company_id = l.company_id
                    WHERE s.broad_sector = ?
                      AND l.pe_ratio IS NOT NULL
                    ORDER BY l.pe_ratio
                    """,
                    (sector,),
                ).fetchall()
            ]

            def median(values):
                """Return median of an already sorted list."""

                n = len(values)

                if n == 0:
                    return None

                middle = n // 2

                if n % 2 == 1:
                    return values[middle]

                return (
                    values[middle - 1]
                    + values[middle]
                ) / 2

            result.append(
                {
                    "sector": sector,
                    "company_count": row[
                        "company_count"
                    ],
                    "median_roe": median(
                        roe_values
                    ),
                    "median_pe": median(
                        pe_values
                    ),
                    "median_de": median(
                        de_values
                    ),
                }
            )

    return {
        "count": len(result),
        "sectors": result,
    }


@router.get("/sectors/{sector}/companies")
def sector_companies(
    sector: str,
):
    """Return all companies belonging to one broad sector."""

    with _connect() as conn:
        resolved_sector = _resolve_sector(
            sector,
            conn,
        )

        rows = conn.execute(
            """
            WITH latest_ratios AS (
                SELECT *
                FROM (
                    SELECT
                        fr.*,
                        ROW_NUMBER() OVER (
                            PARTITION BY fr.company_id
                            ORDER BY
                                CASE
                                    WHEN substr(fr.year, 6, 2) = '03'
                                    THEN 0
                                    ELSE 1
                                END,
                                fr.year DESC
                        ) AS rn
                    FROM financial_ratios fr
                )
                WHERE rn = 1
            )
            SELECT
                c.id AS company_id,
                c.company_name,
                s.broad_sector,
                s.sub_sector,
                s.market_cap_category,
                lr.return_on_equity_pct
                    AS roe_pct,
                lr.return_on_capital_employed_pct
                    AS roce_pct,
                lr.debt_to_equity,
                lr.revenue_cagr_5yr,
                lr.pat_cagr_5yr,
                lr.composite_quality_score
            FROM companies c
            JOIN sectors s
                ON s.company_id = c.id
            LEFT JOIN latest_ratios lr
                ON lr.company_id = c.id
            WHERE s.broad_sector = ?
            ORDER BY
                lr.composite_quality_score DESC,
                c.id
            """,
            (resolved_sector,),
        ).fetchall()

    companies = [
        dict(row)
        for row in rows
    ]

    return {
        "sector": resolved_sector,
        "count": len(companies),
        "companies": companies,
    }
