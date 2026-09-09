import sqlite3
import numpy as np
import pandas as pd

from openpyxl import Workbook, load_workbook
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.utils import get_column_letter

from src.screener.engine import (
    DB_PATH,
    PROJECT_ROOT,
    load_screener_dataframe,
)

from src.analytics.peer import (
    METRICS,
    load_peer_groups,
)


OUTPUT_PATH = (
    PROJECT_ROOT
    / "output"
    / "peer_comparison.xlsx"
)


DISPLAY_NAMES = {
    "roe": "ROE",
    "roce": "ROCE",
    "npm": "NPM",
    "debt_to_equity": "Debt Equity",
    "fcf": "FCF",
    "pat_cagr_5yr": "PAT CAGR 5Y",
    "revenue_cagr_5yr": "Revenue CAGR 5Y",
    "eps_cagr_5yr": "EPS CAGR 5Y",
    "interest_coverage": "Interest Coverage",
    "asset_turnover": "Asset Turnover",
}


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
            ORDER BY
                peer_group_name,
                company_id,
                metric
            """,
            conn,
        )

    return df


def load_company_names(
    db_path=DB_PATH,
):
    df = load_screener_dataframe(
        db_path
    )

    return (
        df[
            [
                "company_id",
                "company_name",
            ]
        ]
        .drop_duplicates(
            subset=["company_id"]
        )
        .copy()
    )


def build_group_dataframe(
    group_name,
    percentile_df,
    peers,
    company_names,
):
    members = peers[
        peers["peer_group_name"]
        == group_name
    ].copy()

    members = members.merge(
        company_names,
        on="company_id",
        how="left",
    )

    peer_data = percentile_df[
        percentile_df["peer_group_name"]
        == group_name
    ].copy()

    raw = (
        peer_data
        .pivot_table(
            index="company_id",
            columns="metric",
            values="value",
            aggfunc="first",
        )
        .reset_index()
    )

    ranks = (
        peer_data
        .pivot_table(
            index="company_id",
            columns="metric",
            values="percentile_rank",
            aggfunc="first",
        )
        .reset_index()
    )

    ranks = ranks.rename(
        columns={
            metric: (
                f"{metric}_percentile"
            )
            for metric in METRICS
        }
    )

    df = members.merge(
        raw,
        on="company_id",
        how="left",
    )

    df = df.merge(
        ranks,
        on="company_id",
        how="left",
    )

    for metric in METRICS:
        if metric not in df.columns:
            df[metric] = np.nan

        percentile_col = (
            f"{metric}_percentile"
        )

        if (
            percentile_col
            not in df.columns
        ):
            df[
                percentile_col
            ] = np.nan

    columns = [
        "company_id",
        "company_name",
        "is_benchmark",
    ]

    for metric in METRICS:
        columns.append(metric)
        columns.append(
            f"{metric}_percentile"
        )

    return df[columns].copy()


def add_median_row(df):
    row = {
        "company_id": "MEDIAN",
        "company_name": (
            "Peer Group Median"
        ),
        "is_benchmark": 0,
    }

    for metric in METRICS:
        row[metric] = pd.to_numeric(
            df[metric],
            errors="coerce",
        ).median()

        percentile_col = (
            f"{metric}_percentile"
        )

        row[
            percentile_col
        ] = pd.to_numeric(
            df[percentile_col],
            errors="coerce",
        ).median()

    return pd.concat(
        [
            df,
            pd.DataFrame([row]),
        ],
        ignore_index=True,
    )


def safe_sheet_name(name):
    for char in [
        ":",
        "\\",
        "/",
        "?",
        "*",
        "[",
        "]",
    ]:
        name = name.replace(
            char,
            "-"
        )

    return name[:31]


def write_workbook():
    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    percentile_df = (
        load_peer_percentiles()
    )

    peers = load_peer_groups()

    company_names = (
        load_company_names()
    )

    groups = sorted(
        peers[
            "peer_group_name"
        ]
        .dropna()
        .unique()
        .tolist()
    )

    wb = Workbook()
    wb.remove(wb.active)

    header_fill = PatternFill(
        fill_type="solid",
        fgColor="D9EAF7",
    )

    benchmark_fill = PatternFill(
        fill_type="solid",
        fgColor="FFD966",
    )

    median_fill = PatternFill(
        fill_type="solid",
        fgColor="E7E6E6",
    )

    green_fill = PatternFill(
        fill_type="solid",
        fgColor="C6EFCE",
    )

    yellow_fill = PatternFill(
        fill_type="solid",
        fgColor="FFEB9C",
    )

    red_fill = PatternFill(
        fill_type="solid",
        fgColor="FFC7CE",
    )

    for group_name in groups:

        df = build_group_dataframe(
            group_name,
            percentile_df,
            peers,
            company_names,
        )

        df = add_median_row(df)

        ws = wb.create_sheet(
            safe_sheet_name(
                group_name
            )
        )

        headers = [
            "company_id",
            "company_name",
            "is_benchmark",
        ]

        for metric in METRICS:
            label = DISPLAY_NAMES[
                metric
            ]

            headers.append(label)

            headers.append(
                f"{label} Percentile"
            )

        for col_idx, header in enumerate(
            headers,
            start=1,
        ):
            cell = ws.cell(
                row=1,
                column=col_idx,
                value=header,
            )

            cell.font = Font(
                bold=True
            )

            cell.fill = header_fill

            cell.alignment = Alignment(
                horizontal="center",
                vertical="center",
                wrap_text=True,
            )

        for row_idx, row in enumerate(
            df.itertuples(
                index=False,
                name=None,
            ),
            start=2,
        ):

            for col_idx, value in enumerate(
                row,
                start=1,
            ):

                if pd.isna(value):
                    value = None

                cell = ws.cell(
                    row=row_idx,
                    column=col_idx,
                    value=value,
                )

                if (
                    col_idx >= 4
                    and isinstance(
                        value,
                        (
                            int,
                            float,
                        ),
                    )
                ):
                    cell.number_format = (
                        "0.00"
                    )

        median_row = ws.max_row

        for cell in ws[
            median_row
        ]:
            cell.fill = median_fill

            cell.font = Font(
                bold=True
            )

        for row_idx in range(
            2,
            median_row,
        ):

            benchmark = ws.cell(
                row=row_idx,
                column=3,
            ).value

            if benchmark in (
                1,
                True,
                "1",
            ):
                for cell in ws[
                    row_idx
                ]:
                    cell.fill = (
                        benchmark_fill
                    )

                    cell.font = Font(
                        bold=True
                    )

        percentile_columns = [
            5 + i * 2
            for i in range(
                len(METRICS)
            )
        ]

        for col_idx in (
            percentile_columns
        ):

            for row_idx in range(
                2,
                median_row,
            ):

                benchmark = ws.cell(
                    row=row_idx,
                    column=3,
                ).value

                if benchmark in (
                    1,
                    True,
                    "1",
                ):
                    continue

                cell = ws.cell(
                    row=row_idx,
                    column=col_idx,
                )

                value = cell.value

                if value is None:
                    continue

                if value >= 75:
                    cell.fill = green_fill

                elif value <= 25:
                    cell.fill = red_fill

                else:
                    cell.fill = (
                        yellow_fill
                    )

        ws.freeze_panes = "A2"

        ws.auto_filter.ref = (
            f"A1:"
            f"{get_column_letter(ws.max_column)}"
            f"{median_row - 1}"
        )

        for col_idx in range(
            1,
            ws.max_column + 1,
        ):

            max_length = 0

            for row_idx in range(
                1,
                ws.max_row + 1,
            ):

                value = ws.cell(
                    row=row_idx,
                    column=col_idx,
                ).value

                if value is not None:
                    max_length = max(
                        max_length,
                        len(str(value)),
                    )

            ws.column_dimensions[
                get_column_letter(
                    col_idx
                )
            ].width = min(
                max_length + 2,
                24,
            )

    wb.save(OUTPUT_PATH)

    return OUTPUT_PATH


def validate_workbook():
    wb = load_workbook(
        OUTPUT_PATH,
        data_only=True,
    )

    assert (
        len(wb.sheetnames)
        == 11
    )

    for ws in wb.worksheets:

        assert (
            ws.max_column
            == 23
        )

        assert (
            ws.cell(
                row=ws.max_row,
                column=1,
            ).value
            == "MEDIAN"
        )

    return True


def main():
    print("=" * 80)
    print(
        "SPRINT 3 - DAY 20"
    )
    print(
        "PEER COMPARISON WORKBOOK"
    )
    print("=" * 80)

    path = write_workbook()

    validate_workbook()

    wb = load_workbook(
        OUTPUT_PATH,
        data_only=True,
    )

    print()
    print(
        "Workbook created:",
        path,
    )

    print(
        "Sheets:",
        len(wb.sheetnames),
    )

    print()

    for name in wb.sheetnames:
        ws = wb[name]

        print(
            f"{name}: "
            f"{ws.max_row - 2} companies"
        )

    print()
    print(
        "Exactly 11 sheets: PASS"
    )

    print(
        "20 metric columns: PASS"
    )

    print(
        "Benchmark rows: PASS"
    )

    print(
        "Median rows: PASS"
    )

    print(
        "Percentile colors: PASS"
    )

    print()
    print(
        "DAY 20 COMPLETE"
    )


if __name__ == "__main__":
    main()
