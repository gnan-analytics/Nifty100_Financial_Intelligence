from pathlib import Path
import sqlite3

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from src.screener.engine import (
    DB_PATH,
    PROJECT_ROOT,
    load_screener_dataframe,
)
from src.analytics.peer import (
    load_peer_groups,
)


RADAR_DIR = PROJECT_ROOT / "reports" / "radar_charts"


RADAR_METRICS = [
    ("roe", "ROE"),
    ("roce", "ROCE"),
    ("npm", "NPM"),
    ("debt_to_equity", "D/E"),
    ("fcf", "FCF"),
    ("pat_cagr_5yr", "PAT CAGR 5Y"),
    ("revenue_cagr_5yr", "Revenue CAGR 5Y"),
]


def load_peer_percentiles(
    db_path=DB_PATH,
):
    with sqlite3.connect(db_path) as conn:
        df = pd.read_sql_query(
            """
            SELECT
                company_id,
                peer_group_name,
                metric,
                value,
                percentile_rank,
                year
            FROM peer_percentiles
            """,
            conn,
        )

    return df


def load_company_scores(
    db_path=DB_PATH,
):
    df = load_screener_dataframe(
        db_path
    )

    cols = [
        "company_id",
        "company_name",
        "broad_sector",
        "composite_quality_score",
    ]

    return df[cols].copy()


def build_group_radar_data(
    group_name,
    percentile_df,
    score_df,
):
    group = percentile_df[
        percentile_df["peer_group_name"]
        == group_name
    ].copy()

    companies = sorted(
        group["company_id"]
        .dropna()
        .unique()
        .tolist()
    )

    rows = []

    for company_id in companies:
        row = {
            "company_id": company_id
        }

        company_metrics = group[
            group["company_id"]
            == company_id
        ]

        for metric_name, _ in RADAR_METRICS:
            metric_row = company_metrics[
                company_metrics["metric"]
                == metric_name
            ]

            if metric_row.empty:
                row[metric_name] = np.nan
            else:
                row[metric_name] = (
                    metric_row[
                        "percentile_rank"
                    ].iloc[0]
                )

        score_row = score_df[
            score_df["company_id"]
            == company_id
        ]

        if score_row.empty:
            row[
                "composite_quality_score"
            ] = np.nan
        else:
            row[
                "composite_quality_score"
            ] = (
                score_row[
                    "composite_quality_score"
                ].iloc[0]
            )

        rows.append(row)

    return pd.DataFrame(rows)


def prepare_radar_values(
    row,
):
    labels = [
        label
        for _, label
        in RADAR_METRICS
    ] + [
        "Composite Score"
    ]

    values = [
        row.get(
            metric,
            np.nan,
        )
        for metric, _
        in RADAR_METRICS
    ]

    values.append(
        row.get(
            "composite_quality_score",
            np.nan,
        )
    )

    values = [
        0.0
        if pd.isna(v)
        else float(v)
        for v in values
    ]

    return labels, values


def create_radar_chart(
    company_id,
    group_name,
    group_df,
    output_dir=RADAR_DIR,
):
    output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    company_row = group_df[
        group_df["company_id"]
        == company_id
    ]

    if company_row.empty:
        return None

    company_row = (
        company_row.iloc[0]
        .to_dict()
    )

    peer_avg = (
        group_df
        .drop(
            columns=["company_id"]
        )
        .mean(
            numeric_only=True
        )
        .to_dict()
    )

    labels, company_values = (
        prepare_radar_values(
            company_row
        )
    )

    _, peer_values = (
        prepare_radar_values(
            peer_avg
        )
    )

    count = len(labels)

    angles = np.linspace(
        0,
        2 * np.pi,
        count,
        endpoint=False,
    ).tolist()

    angles += angles[:1]

    company_values += (
        company_values[:1]
    )

    peer_values += (
        peer_values[:1]
    )

    fig = plt.figure(
        figsize=(9, 9)
    )

    ax = fig.add_subplot(
        111,
        polar=True,
    )

    ax.plot(
        angles,
        company_values,
        linewidth=2,
        label=company_id,
    )

    ax.fill(
        angles,
        company_values,
        alpha=0.25,
    )

    ax.plot(
        angles,
        peer_values,
        linewidth=2,
        linestyle="--",
        label="Peer Average",
    )

    ax.set_xticks(
        angles[:-1]
    )

    ax.set_xticklabels(
        labels,
        fontsize=9,
    )

    ax.set_ylim(
        0,
        100,
    )

    ax.set_yticks(
        [20, 40, 60, 80, 100]
    )

    ax.set_yticklabels(
        ["20", "40", "60", "80", "100"]
    )

    ax.set_title(
        f"{company_id}\n{group_name}",
        pad=25,
        fontsize=14,
        fontweight="bold",
    )

    ax.legend(
        loc="upper right",
        bbox_to_anchor=(
            1.30,
            1.15,
        ),
    )

    safe_group = (
        group_name
        .replace("/", "-")
        .replace("\\", "-")
        .replace(" ", "_")
    )

    filename = (
        f"{safe_group}_{company_id}_radar.png"
    )

    output_path = (
        output_dir / filename
    )

    plt.tight_layout()
    plt.savefig(
        output_path,
        dpi=150,
        bbox_inches="tight",
    )
    plt.close(fig)

    return output_path


def create_standalone_chart(
    company_id,
    score_df,
    output_dir=RADAR_DIR,
):
    output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    row = score_df[
        score_df["company_id"]
        == company_id
    ]

    if row.empty:
        return None

    company_score = row[
        "composite_quality_score"
    ].iloc[0]

    nifty_avg = score_df[
        "composite_quality_score"
    ].mean()

    if pd.isna(company_score):
        company_score = 0.0

    if pd.isna(nifty_avg):
        nifty_avg = 0.0

    fig = plt.figure(
        figsize=(7, 5)
    )

    ax = fig.add_subplot(111)

    ax.bar(
        [
            company_id,
            "Nifty100 Avg",
        ],
        [
            company_score,
            nifty_avg,
        ],
    )

    ax.set_ylim(
        0,
        100,
    )

    ax.set_ylabel(
        "Composite Quality Score"
    )

    ax.set_title(
        f"{company_id} vs Nifty100 Average"
    )

    for idx, value in enumerate(
        [
            company_score,
            nifty_avg,
        ]
    ):
        ax.text(
            idx,
            value + 2,
            f"{value:.1f}",
            ha="center",
        )

    output_path = (
        output_dir
        / f"Standalone_{company_id}.png"
    )

    plt.tight_layout()
    plt.savefig(
        output_path,
        dpi=150,
        bbox_inches="tight",
    )
    plt.close(fig)

    return output_path


def generate_all_radar_charts(
    db_path=DB_PATH,
):
    RADAR_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    percentile_df = (
        load_peer_percentiles(
            db_path
        )
    )

    score_df = (
        load_company_scores(
            db_path
        )
    )

    peer_groups = (
        load_peer_groups(
            db_path
        )
    )

    created = []

    for group_name in sorted(
        peer_groups[
            "peer_group_name"
        ].unique()
    ):
        group_df = (
            build_group_radar_data(
                group_name,
                percentile_df,
                score_df,
            )
        )

        for company_id in (
            group_df[
                "company_id"
            ].tolist()
        ):
            path = create_radar_chart(
                company_id,
                group_name,
                group_df,
            )

            if path is not None:
                created.append(path)

    peer_company_ids = set(
        peer_groups[
            "company_id"
        ].tolist()
    )

    all_company_ids = set(
        score_df[
            "company_id"
        ].tolist()
    )

    no_peer_ids = sorted(
        all_company_ids
        - peer_company_ids
    )

    standalone_created = []

    for company_id in no_peer_ids:
        path = create_standalone_chart(
            company_id,
            score_df,
        )

        if path is not None:
            standalone_created.append(
                path
            )

    return (
        created,
        standalone_created,
    )


def main():
    print("=" * 90)
    print("SPRINT 3 — DAY 19")
    print("RADAR CHART GENERATION")
    print("=" * 90)

    peer_charts, standalone = (
        generate_all_radar_charts()
    )

    print()
    print(
        "Peer radar charts:",
        len(peer_charts),
    )

    print(
        "Standalone charts:",
        len(standalone),
    )

    print(
        "Total charts:",
        len(peer_charts)
        + len(standalone),
    )

    print()
    print(
        "Output directory:",
        RADAR_DIR,
    )

    print()
    print("DAY 19 COMPLETE")


if __name__ == "__main__":
    main()
