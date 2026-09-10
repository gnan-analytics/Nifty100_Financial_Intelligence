import sqlite3
from pathlib import Path

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse

router = APIRouter()

DB_PATH = Path("db/nifty100.db")


def _connect():
    """Return SQLite connection with dictionary-like rows."""

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _company_exists(
    conn: sqlite3.Connection,
    ticker: str,
) -> bool:
    """Return True when ticker exists."""

    row = conn.execute(
        """
        SELECT 1
        FROM companies
        WHERE UPPER(id) = ?
        LIMIT 1
        """,
        (ticker,),
    ).fetchone()

    return row is not None


def _latest_ratio_row(
    conn: sqlite3.Connection,
    ticker: str,
):
    """Return latest March annual ratio row, falling back to latest available."""

    row = conn.execute(
        """
        SELECT *
        FROM financial_ratios
        WHERE company_id = ?
          AND year LIKE '%-03'
        ORDER BY year DESC
        LIMIT 1
        """,
        (ticker,),
    ).fetchone()

    if row is not None:
        return row

    return conn.execute(
        """
        SELECT *
        FROM financial_ratios
        WHERE company_id = ?
        ORDER BY year DESC
        LIMIT 1
        """,
        (ticker,),
    ).fetchone()


def _history_query(
    table: str,
    ticker: str,
    from_year: str | None,
    to_year: str | None,
):
    """Return filtered historical rows for a company table."""

    query = f"""
        SELECT *
        FROM {table}
        WHERE company_id = ?
    """

    params = [ticker]

    if from_year:
        query += """
            AND year >= ?
        """
        params.append(from_year.strip())

    if to_year:
        query += """
            AND year <= ?
        """
        params.append(to_year.strip())

    query += """
        ORDER BY year
    """

    return query, params


@router.get("/companies")
def list_companies(
    sector: str | None = Query(default=None),
    market_cap_category: str | None = Query(default=None),
    search: str | None = Query(default=None),
):
    """Return all companies with optional filters."""

    query = """
        SELECT
            c.id,
            c.company_name AS name,
            s.broad_sector,
            s.sub_sector,
            s.market_cap_category,
            c.roe_percentage AS roe_pct,
            c.roce_percentage AS roce_pct
        FROM companies c
        LEFT JOIN sectors s
            ON c.id = s.company_id
        WHERE 1 = 1
    """

    params = []

    if sector:
        query += """
            AND LOWER(s.broad_sector) = LOWER(?)
        """
        params.append(sector.strip())

    if market_cap_category:
        query += """
            AND LOWER(s.market_cap_category) = LOWER(?)
        """
        params.append(market_cap_category.strip())

    if search:
        query += """
            AND (
                LOWER(c.id) LIKE LOWER(?)
                OR LOWER(c.company_name) LIKE LOWER(?)
            )
        """

        pattern = f"%{search.strip()}%"

        params.extend(
            [
                pattern,
                pattern,
            ]
        )

    query += """
        ORDER BY c.company_name
    """

    with _connect() as conn:

        rows = conn.execute(
            query,
            params,
        ).fetchall()

    return {
        "count": len(rows),
        "companies": [dict(row) for row in rows],
    }


@router.get("/companies/{ticker}")
def get_company(
    ticker: str,
):
    """Return full company profile with latest KPIs."""

    ticker = ticker.strip().upper()

    with _connect() as conn:

        company = conn.execute(
            """
            SELECT
                c.id,
                c.company_name,
                c.company_logo,
                c.about_company,
                c.website,
                c.nse_profile,
                c.bse_profile,
                c.face_value,
                c.book_value,
                c.roe_percentage,
                c.roce_percentage,
                s.broad_sector,
                s.sub_sector,
                s.index_weight_pct,
                s.market_cap_category
            FROM companies c
            LEFT JOIN sectors s
                ON c.id = s.company_id
            WHERE UPPER(c.id) = ?
            """,
            (ticker,),
        ).fetchone()

        if company is None:
            raise HTTPException(
                status_code=404,
                detail=(f"Company '{ticker}' " "not found"),
            )

        latest_ratio = _latest_ratio_row(
            conn,
            ticker,
        )

    return {
        "company": dict(company),
        "latest_kpis": (dict(latest_ratio) if latest_ratio else None),
    }


@router.get("/companies/{ticker}/pl")
def get_profit_and_loss(
    ticker: str,
    from_year: str | None = Query(default=None),
    to_year: str | None = Query(default=None),
):
    """Return company profit-and-loss history."""

    ticker = ticker.strip().upper()

    with _connect() as conn:

        if not _company_exists(
            conn,
            ticker,
        ):
            raise HTTPException(
                status_code=404,
                detail=(f"Company '{ticker}' " "not found"),
            )

        query, params = _history_query(
            "profitandloss",
            ticker,
            from_year,
            to_year,
        )

        rows = conn.execute(
            query,
            params,
        ).fetchall()

    return {
        "ticker": ticker,
        "count": len(rows),
        "data": [dict(row) for row in rows],
    }


@router.get("/companies/{ticker}/bs")
def get_balance_sheet(
    ticker: str,
    from_year: str | None = Query(default=None),
    to_year: str | None = Query(default=None),
):
    """Return company balance-sheet history."""

    ticker = ticker.strip().upper()

    with _connect() as conn:

        if not _company_exists(
            conn,
            ticker,
        ):
            raise HTTPException(
                status_code=404,
                detail=(f"Company '{ticker}' " "not found"),
            )

        query, params = _history_query(
            "balancesheet",
            ticker,
            from_year,
            to_year,
        )

        rows = conn.execute(
            query,
            params,
        ).fetchall()

    return {
        "ticker": ticker,
        "count": len(rows),
        "data": [dict(row) for row in rows],
    }


@router.get("/companies/{ticker}/cashflow")
def get_cashflow(
    ticker: str,
    from_year: str | None = Query(default=None),
    to_year: str | None = Query(default=None),
):
    """Return company cash-flow history."""

    ticker = ticker.strip().upper()

    with _connect() as conn:

        if not _company_exists(
            conn,
            ticker,
        ):
            raise HTTPException(
                status_code=404,
                detail=(f"Company '{ticker}' " "not found"),
            )

        query, params = _history_query(
            "cashflow",
            ticker,
            from_year,
            to_year,
        )

        rows = conn.execute(
            query,
            params,
        ).fetchall()

    return {
        "ticker": ticker,
        "count": len(rows),
        "data": [dict(row) for row in rows],
    }


@router.get("/companies/{ticker}/ratios")
def get_ratios(
    ticker: str,
    year: str | None = Query(default=None),
):
    """Return company financial-ratio history or one selected year."""

    ticker = ticker.strip().upper()

    with _connect() as conn:

        if not _company_exists(
            conn,
            ticker,
        ):
            raise HTTPException(
                status_code=404,
                detail=(f"Company '{ticker}' " "not found"),
            )

        query = """
            SELECT *
            FROM financial_ratios
            WHERE company_id = ?
        """

        params = [ticker]

        if year:
            query += """
                AND year = ?
            """

            params.append(year.strip())

        query += """
            ORDER BY year
        """

        rows = conn.execute(
            query,
            params,
        ).fetchall()

    return {
        "ticker": ticker,
        "count": len(rows),
        "data": [dict(row) for row in rows],
    }


@router.get("/companies/{ticker}/tearsheet")
def get_tearsheet(
    ticker: str,
):
    """Return the company's generated tearsheet PDF."""

    ticker = ticker.strip().upper()

    pdf_path = Path("reports/tearsheets") / f"{ticker}_tearsheet.pdf"

    if not pdf_path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Tearsheet for '{ticker}' not found",
        )

    return FileResponse(
        path=pdf_path,
        media_type="application/pdf",
        filename=f"{ticker}_tearsheet.pdf",
    )
