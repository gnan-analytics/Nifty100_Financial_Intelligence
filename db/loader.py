from pathlib import Path
from datetime import datetime
import sqlite3
import time

import pandas as pd

from src.etl.loader import (
    load_core_datasets,
    load_supplementary_datasets,
    reject_invalid_year_rows,
    reject_orphan_company_ids,
)


# =========================================================
# PATHS
# =========================================================

DB_PATH = Path("db/nifty100.db")
SCHEMA_PATH = Path("db/schema.sql")
OUTPUT_DIR = Path("output")
AUDIT_PATH = OUTPUT_DIR / "load_audit.csv"


# =========================================================
# TABLE LOAD ORDER
# =========================================================

TABLE_ORDER = [
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
    "financial_ratios",
    "peer_groups",
]


# =========================================================
# DATABASE INITIALIZATION
# =========================================================

def create_database():
    """
    Create a fresh SQLite database from schema.sql.
    """

    if DB_PATH.exists():
        DB_PATH.unlink()

    DB_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    schema_sql = (
        SCHEMA_PATH
        .read_text(
            encoding="utf-8"
        )
    )

    with sqlite3.connect(
        DB_PATH
    ) as conn:

        conn.execute(
            "PRAGMA foreign_keys = ON;"
        )

        conn.executescript(
            schema_sql
        )

        conn.commit()

    print(
        f"Created database: {DB_PATH}"
    )


# =========================================================
# LOAD CLEAN DATASETS
# =========================================================

def prepare_datasets():
    """
    Load all source files and apply
    DQ-07 and DQ-03 cleanup.
    """

    print()
    print(
        "Loading source datasets"
    )
    print("-" * 60)

    core = (
        load_core_datasets()
    )

    supplementary = (
        load_supplementary_datasets()
    )

    datasets = {
        **core,
        **supplementary,
    }

    raw_counts = {
        name: len(df)
        for name, df
        in datasets.items()
    }

    print()
    print(
        "Applying DQ-07 cleanup"
    )
    print("-" * 60)

    (
        datasets,
        year_rejections,
    ) = reject_invalid_year_rows(
        datasets
    )

    print()
    print(
        "Applying DQ-03 cleanup"
    )
    print("-" * 60)

    (
        datasets,
        fk_rejections,
    ) = reject_orphan_company_ids(
        datasets
    )

    return (
        datasets,
        raw_counts,
        year_rejections,
        fk_rejections,
    )


# =========================================================
# COLUMN ALIGNMENT
# =========================================================

def get_table_columns(
    conn,
    table_name,
):
    """
    Return database column names
    for one SQLite table.
    """

    cursor = conn.execute(
        f"PRAGMA table_info({table_name})"
    )

    return [
        row[1]
        for row in cursor.fetchall()
    ]


def align_dataframe_to_table(
    conn,
    table_name,
    df,
):
    """
    Keep only columns present
    in the target SQLite table.

    Missing columns are created as None.
    """

    db_columns = get_table_columns(
        conn,
        table_name,
    )

    working = df.copy()

    for column in db_columns:

        if column not in working.columns:

            working[column] = None

    working = working[
        db_columns
    ]

    return working


# =========================================================
# INSERT TABLE
# =========================================================

def load_table(
    conn,
    table_name,
    df,
):
    """
    Load one pandas DataFrame
    into SQLite.
    """

    prepared_df = (
        align_dataframe_to_table(
            conn,
            table_name,
            df,
        )
    )

    prepared_df.to_sql(
        table_name,
        conn,
        if_exists="append",
        index=False,
    )

    return len(
        prepared_df
    )


# =========================================================
# REJECTION COUNTS
# =========================================================

def build_rejection_counts(
    year_rejections,
    fk_rejections,
):
    counts = {}

    for row in (
        year_rejections
        + fk_rejections
    ):

        table = row[
            "table"
        ]

        counts[table] = (
            counts.get(
                table,
                0,
            )
            + 1
        )

    return counts


# =========================================================
# FULL LOAD
# =========================================================

def run_full_load():

    start_total = time.time()

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    (
        datasets,
        raw_counts,
        year_rejections,
        fk_rejections,
    ) = prepare_datasets()

    create_database()

    rejection_counts = (
        build_rejection_counts(
            year_rejections,
            fk_rejections,
        )
    )

    audit_rows = []

    with sqlite3.connect(
        DB_PATH
    ) as conn:

        conn.execute(
            "PRAGMA foreign_keys = ON;"
        )

        for table_name in (
            TABLE_ORDER
        ):

            print()
            print(
                f"Loading table: "
                f"{table_name}"
            )

            table_start = (
                time.time()
            )

            df = datasets[
                table_name
            ]

            rows_loaded = load_table(
                conn,
                table_name,
                df,
            )

            runtime = (
                time.time()
                - table_start
            )

            rows_in = raw_counts.get(
                table_name,
                len(df),
            )

            rejected = (
                rejection_counts.get(
                    table_name,
                    0,
                )
            )

            audit_rows.append(
                {
                    "table": table_name,
                    "rows_in": rows_in,
                    "rows_out": rows_loaded,
                    "rejected": rejected,
                    "timestamp": (
                        datetime.now()
                        .isoformat(
                            timespec="seconds"
                        )
                    ),
                    "runtime_s": round(
                        runtime,
                        4,
                    ),
                }
            )

            print(
                f"Loaded {rows_loaded} rows"
            )

        conn.commit()

        # -------------------------------------------------
        # FK CHECK
        # -------------------------------------------------

        fk_errors = conn.execute(
            "PRAGMA foreign_key_check;"
        ).fetchall()

        print()
        print("=" * 60)
        print(
            "FOREIGN KEY CHECK"
        )
        print("=" * 60)

        if not fk_errors:

            print(
                "PASS: 0 FK violations"
            )

        else:

            print(
                f"FAIL: "
                f"{len(fk_errors)} "
                f"FK violations"
            )

            for row in (
                fk_errors[:20]
            ):

                print(row)

        # -------------------------------------------------
        # DB ROW COUNTS
        # -------------------------------------------------

        print()
        print("=" * 60)
        print(
            "DATABASE ROW COUNTS"
        )
        print("=" * 60)

        for table_name in (
            TABLE_ORDER
        ):

            count = conn.execute(
                f"SELECT COUNT(*) "
                f"FROM {table_name}"
            ).fetchone()[0]

            print(
                f"{table_name:<25} "
                f"{count}"
            )

    # =====================================================
    # SAVE LOAD AUDIT
    # =====================================================

    audit_df = pd.DataFrame(
        audit_rows
    )

    audit_df.to_csv(
        AUDIT_PATH,
        index=False,
    )

    total_runtime = (
        time.time()
        - start_total
    )

    print()
    print("=" * 60)
    print(
        "LOAD COMPLETE"
    )
    print("=" * 60)

    print(
        f"Database: {DB_PATH}"
    )

    print(
        f"Audit file: {AUDIT_PATH}"
    )

    print(
        f"DQ-07 rejected rows: "
        f"{len(year_rejections)}"
    )

    print(
        f"DQ-03 rejected rows: "
        f"{len(fk_rejections)}"
    )

    print(
        f"Total runtime: "
        f"{total_runtime:.2f}s"
    )


# =========================================================
# ENTRY POINT
# =========================================================

if __name__ == "__main__":
    run_full_load()