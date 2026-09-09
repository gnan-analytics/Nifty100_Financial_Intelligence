from pathlib import Path
import sqlite3
import pandas as pd

from src.screener.engine import (
    DB_PATH,
    PROJECT_ROOT,
    run_preset,
)


def check_quality_compounder():
    df = run_preset(
        "quality_compounder"
    )

    cols = [
        "company_id",
        "company_name",
        "broad_sector",
        "return_on_equity_pct",
        "debt_to_equity",
        "free_cash_flow_cr",
        "revenue_cagr_5yr",
        "composite_quality_score",
    ]

    cols = [
        c for c in cols
        if c in df.columns
    ]

    df = df.sort_values(
        "composite_quality_score",
        ascending=False,
    )

    print()
    print("=" * 90)
    print("QUALITY COMPOUNDER - TOP 5")
    print("=" * 90)

    print(
        df[cols]
        .head(5)
        .to_string(
            index=False
        )
    )

    return len(df)


def check_it_services():
    with sqlite3.connect(
        DB_PATH
    ) as conn:
        df = pd.read_sql_query(
            """
            SELECT
                company_id,
                metric,
                value,
                percentile_rank
            FROM peer_percentiles
            WHERE peer_group_name = 'IT Services'
              AND metric = 'roe'
            ORDER BY
                percentile_rank DESC,
                value DESC
            """,
            conn,
        )

    print()
    print("=" * 90)
    print("IT SERVICES - ROE PEER RANK")
    print("=" * 90)

    print(
        df.to_string(
            index=False
        )
    )

    highest = df.dropna(
        subset=[
            "value",
            "percentile_rank",
        ]
    ).iloc[0]

    assert (
        highest[
            "percentile_rank"
        ]
        == 100.0
    )

    print()
    print(
        "Highest ROE company:",
        highest["company_id"],
    )

    print(
        "Highest percentile:",
        highest[
            "percentile_rank"
        ],
    )

    print(
        "IT Services ROE check: PASS"
    )


def check_outputs():
    outputs = {
        "Screener workbook":
            PROJECT_ROOT
            / "output"
            / "screener_output.xlsx",

        "Peer workbook":
            PROJECT_ROOT
            / "output"
            / "peer_comparison.xlsx",

        "Radar directory":
            PROJECT_ROOT
            / "reports"
            / "radar_charts",
    }

    print()
    print("=" * 90)
    print("OUTPUT VALIDATION")
    print("=" * 90)

    for name, path in (
        outputs.items()
    ):
        exists = path.exists()

        print(
            f"{name}: "
            f"{'PASS' if exists else 'FAIL'}"
        )

        assert exists

    radar_dir = outputs[
        "Radar directory"
    ]

    radar_count = len(
        list(
            radar_dir.glob(
                "*.png"
            )
        )
    )

    print(
        "Radar chart count:",
        radar_count,
    )

    assert radar_count == 92


def check_peer_table():
    with sqlite3.connect(
        DB_PATH
    ) as conn:
        result = conn.execute(
            """
            SELECT
                COUNT(*),
                COUNT(
                    DISTINCT peer_group_name
                ),
                COUNT(
                    DISTINCT metric
                )
            FROM peer_percentiles
            """
        ).fetchone()

    rows, groups, metrics = result

    print()
    print("=" * 90)
    print("PEER TABLE VALIDATION")
    print("=" * 90)

    print(
        "Rows:",
        rows,
    )

    print(
        "Peer groups:",
        groups,
    )

    print(
        "Metrics:",
        metrics,
    )

    assert rows == 560
    assert groups == 11
    assert metrics == 10

    print(
        "Peer percentile table: PASS"
    )


def main():
    print("=" * 90)
    print("SPRINT 3 - DAY 21")
    print("FINAL VALIDATION")
    print("=" * 90)

    quality_count = (
        check_quality_compounder()
    )

    print()
    print(
        "Quality Compounder count:",
        quality_count,
    )

    assert (
        5
        <= quality_count
        <= 50
    )

    check_it_services()

    check_peer_table()

    check_outputs()

    print()
    print("=" * 90)
    print(
        "DAY 21 VALIDATION COMPLETE"
    )
    print("=" * 90)


if __name__ == "__main__":
    main()
