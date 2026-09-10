from pathlib import Path
import sqlite3
import sys

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.reports.tearsheet import (
    create_tearsheet,
    load_data,
)

DB_PATH = ROOT / "db" / "nifty100.db"
OUTPUT_DIR = ROOT / "reports" / "tearsheets"
SKIP_PATH = ROOT / "output" / "skipped_tearsheets.csv"

MIN_ANNUAL_YEARS = 3


def get_coverage():
    """Return coverage."""
    with sqlite3.connect(DB_PATH) as conn:
        companies = pd.read_sql_query(
            """
            SELECT
                id,
                company_name
            FROM companies
            ORDER BY id
            """,
            conn,
        )

        pnl = pd.read_sql_query(
            """
            SELECT
                company_id,
                year
            FROM profitandloss
            """,
            conn,
        )

    companies["id"] = companies["id"].astype(str).str.strip().str.upper()

    pnl["company_id"] = pnl["company_id"].astype(str).str.strip().str.upper()

    pnl["year"] = pnl["year"].astype(str).str.strip()

    annual = pnl[pnl["year"].str.endswith("-03")].copy()

    coverage = (
        annual.groupby("company_id")["year"]
        .nunique()
        .rename("annual_years")
        .reset_index()
    )

    result = companies.merge(
        coverage,
        left_on="id",
        right_on="company_id",
        how="left",
    )

    result["annual_years"] = result["annual_years"].fillna(0).astype(int)

    return result


def write_skipped(skipped):
    """Write skipped."""
    SKIP_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    output = skipped[
        [
            "id",
            "company_name",
            "annual_years",
        ]
    ].copy()

    output = output.rename(
        columns={
            "id": "company_id",
        }
    )

    output["reason"] = "Fewer than 3 annual P&L years"

    output.to_csv(
        SKIP_PATH,
        index=False,
    )


def main():
    """Run the module entry point."""
    print("=" * 90)
    print("SPRINT 5 - DAY 34 BATCH TEARSHEETS")
    print("=" * 90)

    coverage = get_coverage()

    eligible = coverage[coverage["annual_years"] >= MIN_ANNUAL_YEARS].copy()

    skipped = coverage[coverage["annual_years"] < MIN_ANNUAL_YEARS].copy()

    write_skipped(skipped)

    print(f"\nCompany master: {len(coverage)}")

    print(f"Eligible: {len(eligible)}")

    print(f"Skipped: {len(skipped)}")

    if not skipped.empty:
        print("\nSkipped companies:")

        for row in skipped.itertuples():
            print(f"  {row.id}: " f"{row.annual_years} annual years")

    data = load_data()

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    generated = []
    failed = []

    print("\nGenerating tearsheets...\n")

    total = len(eligible)

    for number, row in enumerate(
        eligible.itertuples(),
        start=1,
    ):
        ticker = row.id

        try:
            path = create_tearsheet(
                ticker,
                data,
            )

            size_kb = path.stat().st_size / 1024

            generated.append(
                {
                    "company_id": ticker,
                    "path": str(path),
                    "size_kb": size_kb,
                }
            )

            print(
                f"[{number:02d}/{total}] " f"[PASS] {ticker:<12} " f"{size_kb:>7.1f} KB"
            )

        except Exception as exc:
            failed.append(
                {
                    "company_id": ticker,
                    "error": str(exc),
                }
            )

            print(f"[{number:02d}/{total}] " f"[FAIL] {ticker}: {exc}")

    print("\n" + "=" * 90)
    print("BATCH SUMMARY")
    print("=" * 90)

    print(f"Eligible companies : {len(eligible)}")

    print(f"Generated PDFs     : {len(generated)}")

    print(f"Failed PDFs        : {len(failed)}")

    print(f"Skipped companies  : {len(skipped)}")

    assert len(generated) == len(
        eligible
    ), "Not every eligible company generated successfully"

    assert len(failed) == 0, f"Generation failures: {failed}"

    assert len(generated) + len(skipped) == len(coverage)

    print(f"\nSkip log: {SKIP_PATH}")

    print("\nDAY 34 BATCH TEARSHEETS: PASS")


if __name__ == "__main__":
    main()
