from pathlib import Path
import re
import sqlite3

import numpy as np
import pandas as pd

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
)


ROOT = Path(__file__).resolve().parents[2]
DB_PATH = ROOT / "db" / "nifty100.db"
OUTPUT_DIR = ROOT / "reports" / "sector"

NAVY = colors.HexColor("#0B1F3A")
LIGHT_BLUE = colors.HexColor("#EAF1F8")
LIGHT_GREY = colors.HexColor("#F4F6F8")
BORDER = colors.HexColor("#D8DEE6")


METRICS = [
    ("market_cap_crore", "Market Cap\nRs Cr"),
    ("pe_ratio", "P/E"),
    ("return_on_equity_pct", "ROE %"),
    ("return_on_capital_employed_pct", "ROCE %"),
    ("debt_to_equity", "D/E"),
    ("revenue_cagr_5yr", "Revenue\nCAGR 5Y %"),
    ("pat_cagr_5yr", "PAT\nCAGR 5Y %"),
    ("fcf_conversion_pct", "FCF\nConversion %"),
]


def annual_rows(df):
    if df.empty:
        return df.copy()

    out = df.copy()
    out["year"] = out["year"].astype(str)

    march = out[
        out["year"].str.endswith("-03")
    ].copy()

    if not march.empty:
        out = march

    return out.sort_values("year")


def latest_annual(df):
    out = annual_rows(df)

    if out.empty:
        return None

    return out.iloc[-1]


def safe_float(value):
    try:
        if pd.isna(value):
            return np.nan
        return float(value)
    except Exception:
        return np.nan


def fmt(value, decimals=1):
    value = safe_float(value)

    if np.isnan(value):
        return "-"

    return f"{value:,.{decimals}f}"


def safe_filename(name):
    value = re.sub(
        r"[^A-Za-z0-9]+",
        "_",
        str(name).strip(),
    )

    return value.strip("_").lower()


def load_data():
    with sqlite3.connect(DB_PATH) as conn:
        companies = pd.read_sql_query(
            """
            SELECT
                id,
                company_name
            FROM companies
            """,
            conn,
        )

        peers = pd.read_sql_query(
            """
            SELECT
                peer_group_name,
                company_id,
                is_benchmark
            FROM peer_groups
            """,
            conn,
        )

        ratios = pd.read_sql_query(
            """
            SELECT *
            FROM financial_ratios
            """,
            conn,
        )

        market = pd.read_sql_query(
            """
            SELECT *
            FROM market_cap
            """,
            conn,
        )

    for df, col in [
        (companies, "id"),
        (peers, "company_id"),
        (ratios, "company_id"),
        (market, "company_id"),
    ]:
        df[col] = (
            df[col]
            .astype(str)
            .str.strip()
            .str.upper()
        )

    return {
        "companies": companies,
        "peers": peers,
        "ratios": ratios,
        "market": market,
    }


def build_latest_company_table(data):
    companies = data["companies"]
    peers = data["peers"]
    ratios = data["ratios"]
    market = data["market"]

    rows = []

    for peer in peers.itertuples():
        ticker = peer.company_id

        company_rows = companies[
            companies["id"] == ticker
        ]

        company_name = (
            company_rows.iloc[0]["company_name"]
            if not company_rows.empty
            else ticker
        )

        ratio_row = latest_annual(
            ratios[
                ratios["company_id"] == ticker
            ]
        )

        market_row = latest_annual(
            market[
                market["company_id"] == ticker
            ]
        )

        record = {
            "peer_group_name": peer.peer_group_name,
            "company_id": ticker,
            "company_name": company_name,
            "is_benchmark": int(peer.is_benchmark),
        }

        for metric, _ in METRICS:
            if (
                metric
                in [
                    "market_cap_crore",
                    "pe_ratio",
                ]
            ):
                source = market_row
            else:
                source = ratio_row

            if (
                source is not None
                and metric in source.index
            ):
                record[metric] = safe_float(
                    source[metric]
                )
            else:
                record[metric] = np.nan

        rows.append(record)

    return pd.DataFrame(rows)


def styles():
    base = getSampleStyleSheet()

    return {
        "title": ParagraphStyle(
            "SectorTitle",
            parent=base["Heading1"],
            fontName="Helvetica-Bold",
            fontSize=18,
            leading=21,
            textColor=colors.white,
            alignment=TA_CENTER,
        ),
        "subtitle": ParagraphStyle(
            "Subtitle",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=8,
            leading=10,
            textColor=colors.white,
            alignment=TA_CENTER,
        ),
        "section": ParagraphStyle(
            "Section",
            parent=base["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=11,
            leading=13,
            textColor=NAVY,
            spaceAfter=5,
        ),
        "cell": ParagraphStyle(
            "Cell",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=7.2,
            leading=9,
            wordWrap="CJK",
        ),
        "cell_center": ParagraphStyle(
            "CellCenter",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=7.2,
            leading=9,
            alignment=TA_CENTER,
            wordWrap="CJK",
        ),
        "header": ParagraphStyle(
            "HeaderCell",
            parent=base["Normal"],
            fontName="Helvetica-Bold",
            fontSize=6.8,
            leading=8,
            alignment=TA_CENTER,
            textColor=colors.white,
            wordWrap="CJK",
        ),
        "median_label": ParagraphStyle(
            "MedianLabel",
            parent=base["Normal"],
            fontName="Helvetica-Bold",
            fontSize=7,
            leading=8,
            alignment=TA_CENTER,
            textColor=NAVY,
            wordWrap="CJK",
        ),
        "median_value": ParagraphStyle(
            "MedianValue",
            parent=base["Normal"],
            fontName="Helvetica-Bold",
            fontSize=9,
            leading=11,
            alignment=TA_CENTER,
            wordWrap="CJK",
        ),
    }


def header(group_name, company_count, s):
    table = Table(
        [
            [
                Paragraph(
                    f"{group_name}",
                    s["title"],
                )
            ],
            [
                Paragraph(
                    (
                        "Nifty 100 Financial Intelligence - "
                        f"Sector / Peer Group Report - "
                        f"{company_count} companies"
                    ),
                    s["subtitle"],
                )
            ],
        ],
        colWidths=[267 * mm],
    )

    table.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, -1),
                    NAVY,
                ),
                (
                    "LEFTPADDING",
                    (0, 0),
                    (-1, -1),
                    8,
                ),
                (
                    "RIGHTPADDING",
                    (0, 0),
                    (-1, -1),
                    8,
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    7,
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    7,
                ),
            ]
        )
    )

    return table


def median_summary(group, s):
    medians = []

    for metric, label in METRICS:
        value = group[metric].median(
            skipna=True
        )

        medians.append(
            [
                Paragraph(
                    label.replace("\n", "<br/>"),
                    s["median_label"],
                ),
                Paragraph(
                    fmt(value),
                    s["median_value"],
                ),
            ]
        )

    cells = []

    for label, value in medians:
        cells.append(
            Table(
                [[label], [value]],
                colWidths=[31.5 * mm],
            )
        )

    table = Table(
        [cells],
        colWidths=[33 * mm] * 8,
    )

    table.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, -1),
                    LIGHT_BLUE,
                ),
                (
                    "BOX",
                    (0, 0),
                    (-1, -1),
                    0.5,
                    BORDER,
                ),
                (
                    "INNERGRID",
                    (0, 0),
                    (-1, -1),
                    0.4,
                    BORDER,
                ),
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "MIDDLE",
                ),
                (
                    "LEFTPADDING",
                    (0, 0),
                    (-1, -1),
                    2,
                ),
                (
                    "RIGHTPADDING",
                    (0, 0),
                    (-1, -1),
                    2,
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    4,
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    4,
                ),
            ]
        )
    )

    return table


def company_table(group, s):
    headers = [
        "Ticker",
        "Company",
        "Benchmark",
    ] + [
        label.replace("\n", "<br/>")
        for _, label in METRICS
    ]

    data = [
        [
            Paragraph(
                item,
                s["header"],
            )
            for item in headers
        ]
    ]

    group = group.sort_values(
        "market_cap_crore",
        ascending=False,
        na_position="last",
    )

    for row in group.itertuples():
        values = [
            Paragraph(
                row.company_id,
                s["cell_center"],
            ),
            Paragraph(
                str(row.company_name),
                s["cell"],
            ),
            Paragraph(
                "Yes"
                if row.is_benchmark == 1
                else "",
                s["cell_center"],
            ),
        ]

        for metric, _ in METRICS:
            values.append(
                Paragraph(
                    fmt(
                        getattr(row, metric)
                    ),
                    s["cell_center"],
                )
            )

        data.append(values)

    widths = [
        19 * mm,
        48 * mm,
        18 * mm,
        27 * mm,
        18 * mm,
        20 * mm,
        20 * mm,
        18 * mm,
        26 * mm,
        25 * mm,
        28 * mm,
    ]

    table = Table(
        data,
        colWidths=widths,
        repeatRows=1,
    )

    commands = [
        (
            "BACKGROUND",
            (0, 0),
            (-1, 0),
            NAVY,
        ),
        (
            "GRID",
            (0, 0),
            (-1, -1),
            0.35,
            BORDER,
        ),
        (
            "VALIGN",
            (0, 0),
            (-1, -1),
            "MIDDLE",
        ),
        (
            "LEFTPADDING",
            (0, 0),
            (-1, -1),
            2,
        ),
        (
            "RIGHTPADDING",
            (0, 0),
            (-1, -1),
            2,
        ),
        (
            "TOPPADDING",
            (0, 0),
            (-1, -1),
            3,
        ),
        (
            "BOTTOMPADDING",
            (0, 0),
            (-1, -1),
            3,
        ),
    ]

    for i in range(1, len(data)):
        if i % 2 == 0:
            commands.append(
                (
                    "BACKGROUND",
                    (0, i),
                    (-1, i),
                    LIGHT_GREY,
                )
            )

    table.setStyle(
        TableStyle(commands)
    )

    return table


def footer(canvas, doc):
    canvas.saveState()

    canvas.setFont(
        "Helvetica",
        7,
    )

    canvas.setFillColor(
        colors.HexColor("#667085")
    )

    canvas.drawString(
        15 * mm,
        8 * mm,
        "Nifty 100 Financial Intelligence",
    )

    canvas.drawRightString(
        landscape(A4)[0] - 15 * mm,
        8 * mm,
        f"Page {doc.page}",
    )

    canvas.restoreState()


def create_sector_report(
    group_name,
    group,
):
    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    path = (
        OUTPUT_DIR
        / f"{safe_filename(group_name)}_report.pdf"
    )

    s = styles()

    doc = SimpleDocTemplate(
        str(path),
        pagesize=landscape(A4),
        leftMargin=15 * mm,
        rightMargin=15 * mm,
        topMargin=12 * mm,
        bottomMargin=14 * mm,
        title=f"{group_name} Sector Report",
        author="Nifty100 Financial Intelligence",
    )

    story = [
        header(
            group_name,
            len(group),
            s,
        ),
        Spacer(
            1,
            5 * mm,
        ),
        Paragraph(
            "Median KPI Summary",
            s["section"],
        ),
        median_summary(
            group,
            s,
        ),
        Spacer(
            1,
            6 * mm,
        ),
        Paragraph(
            "Company Comparison",
            s["section"],
        ),
        company_table(
            group,
            s,
        ),
    ]

    doc.build(
        story,
        onFirstPage=footer,
        onLaterPages=footer,
    )

    return path


def main():
    print("=" * 90)
    print("SPRINT 5 - DAY 34 SECTOR REPORTS")
    print("=" * 90)

    data = load_data()
    latest = build_latest_company_table(
        data
    )

    groups = sorted(
        latest[
            "peer_group_name"
        ].dropna().unique()
    )

    print(
        f"\nReporting groups: {len(groups)}"
    )

    assert len(groups) == 11, (
        f"Expected 11 reporting groups, got {len(groups)}"
    )

    generated = []

    for number, group_name in enumerate(
        groups,
        start=1,
    ):
        group = latest[
            latest["peer_group_name"]
            == group_name
        ].copy()

        path = create_sector_report(
            group_name,
            group,
        )

        size_kb = (
            path.stat().st_size
            / 1024
        )

        generated.append(path)

        print(
            f"[{number:02d}/11] "
            f"[PASS] "
            f"{group_name:<20} "
            f"{len(group):>2} companies | "
            f"{size_kb:>6.1f} KB"
        )

    assert len(generated) == 11

    print(
        f"\nGenerated sector reports: "
        f"{len(generated)}"
    )

    print(
        f"Output directory: "
        f"{OUTPUT_DIR}"
    )

    print(
        "\nDAY 34 SECTOR REPORT GENERATOR: PASS"
    )


if __name__ == "__main__":
    main()
