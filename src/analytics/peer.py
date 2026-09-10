import sqlite3

import numpy as np
import pandas as pd

from src.screener.engine import (
    DB_PATH,
    load_screener_dataframe,
)

# ============================================================
# CONFIG
# ============================================================

METRICS = {
    "roe": {
        "column": "return_on_equity_pct",
        "inverse": False,
    },
    "roce": {
        "column": "return_on_capital_employed_pct",
        "inverse": False,
    },
    "npm": {
        "column": "net_profit_margin_pct",
        "inverse": False,
    },
    "debt_to_equity": {
        "column": "debt_to_equity",
        "inverse": True,
    },
    "fcf": {
        "column": "free_cash_flow_cr",
        "inverse": False,
    },
    "pat_cagr_5yr": {
        "column": "pat_cagr_5yr",
        "inverse": False,
    },
    "revenue_cagr_5yr": {
        "column": "revenue_cagr_5yr",
        "inverse": False,
    },
    "eps_cagr_5yr": {
        "column": "eps_cagr_5yr",
        "inverse": False,
    },
    "interest_coverage": {
        "column": "interest_coverage_effective",
        "inverse": False,
    },
    "asset_turnover": {
        "column": "asset_turnover",
        "inverse": False,
    },
}


# ============================================================
# PEER GROUP LOAD
# ============================================================


def load_peer_groups(
    db_path=DB_PATH,
):
    """Load peer groups."""
    with sqlite3.connect(db_path) as conn:
        df = pd.read_sql_query(
            """
            SELECT
                id,
                peer_group_name,
                company_id,
                is_benchmark
            FROM peer_groups
            ORDER BY
                peer_group_name,
                is_benchmark DESC,
                company_id
            """,
            conn,
        )

    return df


# ============================================================
# SQL PERCENT_RANK IMPLEMENTATION
# ============================================================


def percent_rank_sql(
    series,
    inverse=False,
):
    """
    SQL-style PERCENT_RANK:

        (RANK - 1) / (N - 1)

    Ties use RANK(method='min').

    Returns percentile on 0-100 scale.
    """

    numeric = pd.to_numeric(
        series,
        errors="coerce",
    )

    result = pd.Series(
        np.nan,
        index=series.index,
        dtype=float,
    )

    valid = numeric.dropna()

    n = len(valid)

    if n == 0:
        return result

    if n == 1:
        result.loc[valid.index] = 100.0
        return result

    ascending = not inverse

    ranks = valid.rank(
        method="min",
        ascending=ascending,
    )

    percentiles = (ranks - 1) / (n - 1) * 100

    result.loc[valid.index] = percentiles

    return result.round(2)


# ============================================================
# PREPARE LATEST METRICS
# ============================================================


def load_latest_peer_metrics(
    db_path=DB_PATH,
):
    """Load latest peer metrics."""
    df = load_screener_dataframe(db_path)

    columns = [
        "company_id",
        "company_name",
        "broad_sector",
        "year",
        "return_on_equity_pct",
        "return_on_capital_employed_pct",
        "net_profit_margin_pct",
        "debt_to_equity",
        "free_cash_flow_cr",
        "pat_cagr_5yr",
        "revenue_cagr_5yr",
        "eps_cagr_5yr",
        "interest_coverage_effective",
        "asset_turnover",
        "composite_quality_score",
    ]

    columns = [col for col in columns if col in df.columns]

    return df[columns].copy()


# ============================================================
# PEER PERCENTILES
# ============================================================


def calculate_peer_percentiles(
    db_path=DB_PATH,
):
    """Calculate peer percentiles."""
    peers = load_peer_groups(db_path)

    metrics_df = load_latest_peer_metrics(db_path)

    peer_data = peers.merge(
        metrics_df,
        on="company_id",
        how="left",
    )

    rows = []

    for peer_group_name, group in peer_data.groupby("peer_group_name"):
        group = group.copy()

        for metric_name, config in METRICS.items():
            column = config["column"]
            inverse = config["inverse"]

            values = group[column].copy()

            # Debt-free companies should receive
            # maximum ICR percentile.
            if metric_name == "interest_coverage":
                finite = values.replace(
                    [np.inf, -np.inf],
                    np.nan,
                )

                max_finite = finite.max()

                if pd.isna(max_finite):
                    max_finite = 1.0

                values = values.replace(
                    np.inf,
                    max_finite + 1,
                )

            percentiles = percent_rank_sql(
                values,
                inverse=inverse,
            )

            for index in group.index:
                value = values.loc[index]

                if pd.isna(value):
                    percentile = np.nan
                else:
                    percentile = percentiles.loc[index]

                rows.append(
                    {
                        "company_id": group.loc[
                            index,
                            "company_id",
                        ],
                        "peer_group_name": (peer_group_name),
                        "metric": metric_name,
                        "value": (None if pd.isna(value) else float(value)),
                        "percentile_rank": (
                            None if pd.isna(percentile) else float(percentile)
                        ),
                        "year": group.loc[
                            index,
                            "year",
                        ],
                    }
                )

    return pd.DataFrame(rows)


# ============================================================
# DATABASE TABLE
# ============================================================


def create_peer_percentiles_table(
    conn,
):
    """Create peer percentiles table."""
    conn.execute("""
        CREATE TABLE IF NOT EXISTS peer_percentiles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company_id TEXT NOT NULL,
            peer_group_name TEXT NOT NULL,
            metric TEXT NOT NULL,
            value REAL,
            percentile_rank REAL,
            year TEXT,
            UNIQUE (
                company_id,
                peer_group_name,
                metric,
                year
            )
        )
        """)

    conn.execute("""
        CREATE INDEX IF NOT EXISTS
        idx_peer_percentiles_company
        ON peer_percentiles(company_id)
        """)

    conn.execute("""
        CREATE INDEX IF NOT EXISTS
        idx_peer_percentiles_group
        ON peer_percentiles(peer_group_name)
        """)


def populate_peer_percentiles(
    df,
    db_path=DB_PATH,
):
    """Populate peer percentiles."""
    with sqlite3.connect(db_path) as conn:
        create_peer_percentiles_table(conn)

        conn.execute("""
            DELETE FROM peer_percentiles
            """)

        records = []

        for _, row in df.iterrows():
            records.append(
                (
                    row["company_id"],
                    row["peer_group_name"],
                    row["metric"],
                    row["value"],
                    row["percentile_rank"],
                    row["year"],
                )
            )

        conn.executemany(
            """
            INSERT INTO peer_percentiles (
                company_id,
                peer_group_name,
                metric,
                value,
                percentile_rank,
                year
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            records,
        )

        conn.commit()


# ============================================================
# VALIDATION
# ============================================================


def validate_peer_percentiles(
    df,
    db_path=DB_PATH,
):
    """Validate peer percentiles."""
    peers = load_peer_groups(db_path)

    expected_groups = peers["peer_group_name"].dropna().nunique()

    actual_groups = df["peer_group_name"].dropna().nunique()

    expected_rows = len(peers) * len(METRICS)

    duplicate_count = df.duplicated(
        subset=[
            "company_id",
            "peer_group_name",
            "metric",
        ]
    ).sum()

    invalid_percentiles = df[
        df["percentile_rank"].notna()
        & ((df["percentile_rank"] < 0) | (df["percentile_rank"] > 100))
    ]

    return {
        "expected_groups": (expected_groups),
        "actual_groups": (actual_groups),
        "expected_rows": (expected_rows),
        "actual_rows": len(df),
        "duplicates": int(duplicate_count),
        "invalid_percentiles": (len(invalid_percentiles)),
    }


# ============================================================
# PREVIEW
# ============================================================


def preview_group(
    df,
    group_name,
):
    """Preview group."""
    print()
    print("=" * 90)
    print(group_name)
    print("=" * 90)

    subset = df[df["peer_group_name"] == group_name]

    pivot = subset.pivot_table(
        index="company_id",
        columns="metric",
        values="percentile_rank",
        aggfunc="first",
    )

    print(pivot.round(2).to_string())


# ============================================================
# MAIN
# ============================================================


def main():
    """Run the module entry point."""
    print("=" * 90)
    print("SPRINT 3 — DAY 18")
    print("PEER PERCENTILE ENGINE")
    print("=" * 90)

    df = calculate_peer_percentiles()

    populate_peer_percentiles(df)

    validation = validate_peer_percentiles(df)

    print()
    print(
        "Peer groups:",
        validation["actual_groups"],
    )

    print(
        "Expected groups:",
        validation["expected_groups"],
    )

    print(
        "Rows:",
        validation["actual_rows"],
    )

    print(
        "Expected rows:",
        validation["expected_rows"],
    )

    print(
        "Duplicates:",
        validation["duplicates"],
    )

    print(
        "Invalid percentiles:",
        validation["invalid_percentiles"],
    )

    print()
    print(
        "Metric count:",
        len(METRICS),
    )

    print(
        "Metrics:",
        ", ".join(METRICS.keys()),
    )

    preview_group(
        df,
        "IT Services",
    )

    print()
    print("=" * 90)
    print("DAY 18 COMPLETE")
    print("=" * 90)


if __name__ == "__main__":
    main()
