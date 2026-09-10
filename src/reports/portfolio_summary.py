from pathlib import Path
import sqlite3
import math

import numpy as np
import pandas as pd

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
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
OUTPUT_DIR = ROOT / "reports" / "portfolio"
OUTPUT_PATH = OUTPUT_DIR / "portfolio_summary.pdf"
FALLBACK_LOG = ROOT / "output" / "portfolio_ratio_fallbacks.csv"

NAVY = colors.HexColor("#0B1F3A")
GREEN = colors.HexColor("#18794E")
RED = colors.HexColor("#B42318")
GREY = colors.HexColor("#667085")
LIGHT_BLUE = colors.HexColor("#EEF4FB")
LIGHT_GREY = colors.HexColor("#F6F8FA")
BORDER = colors.HexColor("#D0D5DD")


KPI_DEFS = [
    (
        "return_on_equity_pct",
        "ROE",
        "%",
    ),
    (
        "return_on_capital_employed_pct",
        "ROCE",
        "%",
    ),
    (
        "debt_to_equity",
        "Debt / Equity",
        "x",
    ),
    (
        "operating_profit_margin_pct",
        "Operating Margin",
        "%",
    ),
    (
        "revenue_cagr_5yr",
        "Revenue CAGR 5Y",
        "%",
    ),
    (
        "pat_cagr_5yr",
        "PAT CAGR 5Y",
        "%",
    ),
]


def normalize_id(series):
    """Normalize id."""
    return series.astype(str).str.strip().str.upper()


def safe_float(value):
    """Convert a value to float safely."""
    try:
        if pd.isna(value):
            return np.nan
        return float(value)
    except Exception:
        return np.nan


def fmt_value(value, suffix):
    """Format value."""
    value = safe_float(value)

    if np.isnan(value):
        return "N/A"

    if suffix == "%":
        return f"{value:.1f}%"

    if suffix == "x":
        return f"{value:.2f}x"

    return f"{value:.1f}"


def trend_symbol(current, previous):
    """Handle trend symbol."""
    current = safe_float(current)
    previous = safe_float(previous)

    if np.isnan(current) or np.isnan(previous):
        return "N/A", "Unavailable"

    change = current - previous

    if change > 2:
        return "UP", "Improving"

    if change < -2:
        return "DOWN", "Declining"

    return "FLAT", "Stable"


def trend_display(symbol):
    """Handle trend display."""
    if symbol == "UP":
        return "UP", GREEN

    if symbol == "DOWN":
        return "DOWN", RED

    if symbol == "FLAT":
        return "FLAT", GREY

    return "N/A", GREY


def load_data():
    """Load data."""
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

        sectors = pd.read_sql_query(
            """
            SELECT
                company_id,
                broad_sector
            FROM sectors
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

    companies["id"] = normalize_id(companies["id"])

    sectors["company_id"] = normalize_id(sectors["company_id"])

    ratios["company_id"] = normalize_id(ratios["company_id"])

    ratios["year"] = ratios["year"].astype(str).str.strip()

    return companies, sectors, ratios


def select_ratio_rows(ratios, ticker):
    """Select ratio rows."""
    rows = ratios[ratios["company_id"] == ticker].copy()

    if rows.empty:
        return None, None, "NO_RATIO_DATA"

    rows = rows.sort_values("year")

    annual = rows[rows["year"].str.endswith("-03")].copy()

    if not annual.empty:
        current = annual.iloc[-1]

        previous = annual.iloc[-2] if len(annual) >= 2 else None

        return current, previous, "MARCH_ANNUAL"

    current = rows.iloc[-1]

    previous = rows.iloc[-2] if len(rows) >= 2 else None

    return current, previous, "LATEST_AVAILABLE_FALLBACK"


def build_styles():
    """Build styles."""
    base = getSampleStyleSheet()

    return {
        "title": ParagraphStyle(
            "Title",
            parent=base["Heading1"],
            fontName="Helvetica-Bold",
            fontSize=22,
            leading=26,
            textColor=colors.white,
            alignment=TA_CENTER,
        ),
        "subtitle": ParagraphStyle(
            "Subtitle",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=9,
            leading=11,
            textColor=colors.white,
            alignment=TA_CENTER,
        ),
        "section": ParagraphStyle(
            "Section",
            parent=base["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=12,
            leading=14,
            textColor=NAVY,
        ),
        "label": ParagraphStyle(
            "Label",
            parent=base["Normal"],
            fontName="Helvetica-Bold",
            fontSize=8,
            leading=10,
            textColor=GREY,
            alignment=TA_CENTER,
        ),
        "value": ParagraphStyle(
            "Value",
            parent=base["Normal"],
            fontName="Helvetica-Bold",
            fontSize=14,
            leading=16,
            textColor=NAVY,
            alignment=TA_CENTER,
        ),
        "small": ParagraphStyle(
            "Small",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=8,
            leading=10,
            textColor=GREY,
        ),
        "body": ParagraphStyle(
            "Body",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=9,
            leading=12,
            textColor=colors.HexColor("#344054"),
        ),
    }


def header(ticker, company_name, sector, period, source_mode, s):
    """Handle header."""
    mode_text = (
        "Annual March data"
        if source_mode == "MARCH_ANNUAL"
        else "Latest available data"
    )

    table = Table(
        [
            [
                Paragraph(
                    ticker,
                    s["title"],
                )
            ],
            [
                Paragraph(
                    company_name,
                    s["subtitle"],
                )
            ],
            [
                Paragraph(
                    f"{sector} | Period: {period} | {mode_text}",
                    s["subtitle"],
                )
            ],
        ],
        colWidths=[180 * mm],
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
                    5,
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    5,
                ),
            ]
        )
    )

    return table


def kpi_card(label, value, trend_text, trend_color, s):
    """Handle kpi card."""
    trend_style = ParagraphStyle(
        f"Trend_{label}",
        parent=s["small"],
        alignment=TA_CENTER,
        textColor=trend_color,
        fontName="Helvetica-Bold",
    )

    table = Table(
        [
            [
                Paragraph(
                    label,
                    s["label"],
                )
            ],
            [
                Paragraph(
                    value,
                    s["value"],
                )
            ],
            [
                Paragraph(
                    trend_text,
                    trend_style,
                )
            ],
        ],
        colWidths=[55 * mm],
        rowHeights=[
            10 * mm,
            13 * mm,
            9 * mm,
        ],
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
                    0.6,
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
                    4,
                ),
                (
                    "RIGHTPADDING",
                    (0, 0),
                    (-1, -1),
                    4,
                ),
            ]
        )
    )

    return table


def build_kpi_grid(current, previous, s):
    """Build kpi grid."""
    cards = []

    for metric, label, suffix in KPI_DEFS:
        current_value = (
            current[metric]
            if current is not None and metric in current.index
            else np.nan
        )

        previous_value = (
            previous[metric]
            if previous is not None and metric in previous.index
            else np.nan
        )

        symbol, description = trend_symbol(
            current_value,
            previous_value,
        )

        display_symbol, trend_color = trend_display(symbol)

        if display_symbol == "N/A":
            trend_text = "Trend: N/A"
        else:
            trend_text = f"{display_symbol} - {description}"

        cards.append(
            kpi_card(
                label,
                fmt_value(
                    current_value,
                    suffix,
                ),
                trend_text,
                trend_color,
                s,
            )
        )

    rows = [
        cards[0:3],
        cards[3:6],
    ]

    table = Table(
        rows,
        colWidths=[
            58 * mm,
            58 * mm,
            58 * mm,
        ],
        rowHeights=[
            35 * mm,
            35 * mm,
        ],
    )

    table.setStyle(
        TableStyle(
            [
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
                    2,
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    2,
                ),
            ]
        )
    )

    return table


def footer(canvas, doc):
    """Handle footer."""
    canvas.saveState()

    canvas.setFont(
        "Helvetica",
        7,
    )

    canvas.setFillColor(GREY)

    canvas.drawString(
        15 * mm,
        8 * mm,
        "Nifty 100 Financial Intelligence - Portfolio Summary",
    )

    canvas.drawRightString(
        A4[0] - 15 * mm,
        8 * mm,
        f"Page {doc.page}",
    )

    canvas.restoreState()


def main():
    """Run the module entry point."""
    companies, sectors, ratios = load_data()

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    s = build_styles()

    doc = SimpleDocTemplate(
        str(OUTPUT_PATH),
        pagesize=A4,
        leftMargin=15 * mm,
        rightMargin=15 * mm,
        topMargin=12 * mm,
        bottomMargin=14 * mm,
        title="Nifty 100 Portfolio Summary",
        author="Nifty100 Financial Intelligence",
    )

    story = []
    fallback_rows = []

    companies = companies.sort_values("id").reset_index(drop=True)

    print("=" * 90)
    print("SPRINT 5 - DAY 35 PORTFOLIO SUMMARY")
    print("=" * 90)

    for index, company in companies.iterrows():
        ticker = company["id"]
        company_name = company["company_name"]

        sector_rows = sectors[sectors["company_id"] == ticker]

        sector = (
            sector_rows.iloc[0]["broad_sector"] if not sector_rows.empty else "Unknown"
        )

        current, previous, source_mode = select_ratio_rows(
            ratios,
            ticker,
        )

        period = current["year"] if current is not None else "N/A"

        if source_mode != "MARCH_ANNUAL":
            fallback_rows.append(
                {
                    "company_id": ticker,
                    "company_name": company_name,
                    "source_mode": source_mode,
                    "selected_period": period,
                }
            )

        story.append(
            header(
                ticker,
                company_name,
                sector,
                period,
                source_mode,
                s,
            )
        )

        story.append(
            Spacer(
                1,
                10 * mm,
            )
        )

        story.append(
            Paragraph(
                "Key Financial Indicators",
                s["section"],
            )
        )

        story.append(
            Spacer(
                1,
                4 * mm,
            )
        )

        story.append(
            build_kpi_grid(
                current,
                previous,
                s,
            )
        )

        story.append(
            Spacer(
                1,
                10 * mm,
            )
        )

        story.append(
            Paragraph(
                "Trend Logic",
                s["section"],
            )
        )

        story.append(
            Spacer(
                1,
                3 * mm,
            )
        )

        story.append(
            Paragraph(
                (
                    "Trend classification compares the latest selected period "
                    "with the previous comparable period. A change above "
                    "+2 percentage points is classified as UP, below "
                    "-2 percentage points as DOWN, and values within "
                    "plus or minus 2 percentage points as FLAT. "
                    "Missing current or prior values are shown as N/A."
                ),
                s["body"],
            )
        )

        if source_mode == "LATEST_AVAILABLE_FALLBACK":
            story.append(
                Spacer(
                    1,
                    8 * mm,
                )
            )

            story.append(
                Paragraph(
                    "Data Note",
                    s["section"],
                )
            )

            story.append(
                Spacer(
                    1,
                    3 * mm,
                )
            )

            story.append(
                Paragraph(
                    (
                        "This company has no March annual ratio record in the "
                        "source dataset. The latest available ratio period is "
                        f"used instead: {period}."
                    ),
                    s["body"],
                )
            )

        if index < len(companies) - 1:
            story.append(PageBreak())

        print(
            f"[{index + 1:02d}/92] " f"{ticker:<12} " f"{period:<8} " f"{source_mode}"
        )

    doc.build(
        story,
        onFirstPage=footer,
        onLaterPages=footer,
    )

    fallback_df = pd.DataFrame(
        fallback_rows,
        columns=[
            "company_id",
            "company_name",
            "source_mode",
            "selected_period",
        ],
    )

    fallback_df.to_csv(
        FALLBACK_LOG,
        index=False,
    )

    size_mb = OUTPUT_PATH.stat().st_size / 1024 / 1024

    print("\n" + "=" * 90)
    print("PORTFOLIO SUMMARY")
    print("=" * 90)

    print(f"Companies included : {len(companies)}")

    print(f"Fallback companies : {len(fallback_df)}")

    print(f"Output PDF         : {OUTPUT_PATH}")

    print(f"PDF size           : {size_mb:.2f} MB")

    print(f"Fallback log       : {FALLBACK_LOG}")

    print("\nDAY 35 PORTFOLIO GENERATOR: PASS")


if __name__ == "__main__":
    main()
