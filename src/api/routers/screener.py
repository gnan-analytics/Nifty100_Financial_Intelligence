"""REST API endpoints for the financial screener."""

import math

import pandas as pd
from fastapi import APIRouter, HTTPException, Query

from src.screener.engine import run_screener


router = APIRouter()


def _clean_records(df: pd.DataFrame) -> list[dict]:
    """Convert a DataFrame into JSON-safe records."""

    clean_df = df.astype(object).where(
        pd.notna(df),
        None,
    )

    records = clean_df.to_dict(
        orient="records",
    )

    for record in records:
        for key, value in record.items():
            if isinstance(value, float) and (
                math.isnan(value)
                or math.isinf(value)
            ):
                record[key] = None

    return records


@router.get("/screener")
def get_screener(
    min_roe: float | None = Query(
        default=None,
        description="Minimum return on equity percentage",
    ),
    max_de: float | None = Query(
        default=None,
        description="Maximum debt-to-equity ratio",
    ),
    min_fcf: float | None = Query(
        default=None,
        description="Minimum free cash flow in crore",
    ),
    sector: str | None = Query(
        default=None,
        description="Broad sector filter",
    ),
    min_rev_cagr_5yr: float | None = Query(
        default=None,
        description="Minimum 5-year revenue CAGR percentage",
    ),
    min_pat_cagr_5yr: float | None = Query(
        default=None,
        description="Minimum 5-year PAT CAGR percentage",
    ),
    max_pe: float | None = Query(
        default=None,
        description="Maximum P/E ratio",
    ),
):
    """Return ranked companies matching screener filters."""

    if max_de is not None and max_de < 0:
        raise HTTPException(
            status_code=400,
            detail="max_de cannot be negative",
        )

    if max_pe is not None and max_pe < 0:
        raise HTTPException(
            status_code=400,
            detail="max_pe cannot be negative",
        )

    filters = {}

    if min_roe is not None:
        filters["roe"] = min_roe

    if max_de is not None:
        filters["debt_to_equity"] = max_de

    if min_fcf is not None:
        filters["free_cash_flow"] = min_fcf

    if min_rev_cagr_5yr is not None:
        filters["revenue_cagr_5yr"] = (
            min_rev_cagr_5yr
        )

    if min_pat_cagr_5yr is not None:
        filters["pat_cagr_5yr"] = (
            min_pat_cagr_5yr
        )

    if max_pe is not None:
        filters["pe_ratio"] = max_pe

    try:
        result = run_screener(filters)
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    if sector is not None:
        sector = sector.strip()

        if not sector:
            raise HTTPException(
                status_code=400,
                detail="sector cannot be empty",
            )

        available_sectors = sorted(
            result["broad_sector"]
            .dropna()
            .astype(str)
            .unique()
            .tolist()
        )

        matched_sector = next(
            (
                value
                for value in available_sectors
                if value.lower() == sector.lower()
            ),
            None,
        )

        if matched_sector is None:
            raise HTTPException(
                status_code=400,
                detail={
                    "message": (
                        f"Unknown sector: {sector}"
                    ),
                    "available_sectors": (
                        available_sectors
                    ),
                },
            )

        result = result[
            result["broad_sector"]
            .astype(str)
            .str.lower()
            == matched_sector.lower()
        ].reset_index(drop=True)

    if "composite_quality_score" in result.columns:
        result = result.sort_values(
            by=[
                "composite_quality_score",
                "company_id",
            ],
            ascending=[
                False,
                True,
            ],
        ).reset_index(drop=True)

    records = _clean_records(result)

    for index, record in enumerate(
        records,
        start=1,
    ):
        record["rank"] = index

    return {
        "count": len(records),
        "filters": {
            "min_roe": min_roe,
            "max_de": max_de,
            "min_fcf": min_fcf,
            "sector": sector,
            "min_rev_cagr_5yr": (
                min_rev_cagr_5yr
            ),
            "min_pat_cagr_5yr": (
                min_pat_cagr_5yr
            ),
            "max_pe": max_pe,
        },
        "companies": records,
    }
