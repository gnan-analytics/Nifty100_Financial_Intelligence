from io import BytesIO
from pathlib import Path
import sqlite3
import sys

import matplotlib.pyplot as plt
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
    Image,
    PageBreak,
    KeepTogether,
)

ROOT = Path(__file__).resolve().parents[2]
DB_PATH = ROOT / "db" / "nifty100.db"
PROS_CONS_PATH = ROOT / "output" / "pros_cons_generated.csv"
CASHFLOW_INTEL_PATH = ROOT / "output" / "cashflow_intelligence.xlsx"
OUTPUT_DIR = ROOT / "reports" / "tearsheets"

TEST_TICKERS = [
    "TCS",
    "HDFCBANK",
    "RELIANCE",
    "SUNPHARMA",
    "TATASTEEL",
]

NAVY = colors.HexColor("#102A43")
LIGHT_NAVY = colors.HexColor("#D9EAF7")
LIGHT_GREY = colors.HexColor("#F3F4F6")
MID_GREY = colors.HexColor("#6B7280")
DARK = colors.HexColor("#111827")
GREEN_BG = colors.HexColor("#E8F5E9")
GREEN_TEXT = colors.HexColor("#176B32")
RED_BG = colors.HexColor("#FDECEC")
RED_TEXT = colors.HexColor("#A61B1B")
WHITE = colors.white


def safe_float(value):
    if value is None or pd.isna(value):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def annual_rows(df):
    if df.empty:
        return df.copy()

    x = df.copy()
    x["year"] = x["year"].astype(str).str.strip()

    x["_date"] = pd.to_datetime(
        x["year"],
        format="%Y-%m",
        errors="coerce",
    )

    x = x.dropna(subset=["_date"])

    march = x[x["year"].str.endswith("-03")].copy()

    if not march.empty:
        x = march

    return x.sort_values("_date")


def latest_annual(df):
    x = annual_rows(df)

    if x.empty:
        return None

    return x.iloc[-1]


def fmt_num(value, decimals=1, suffix=""):
    value = safe_float(value)

    if value is None:
        return "N/A"

    return f"{value:,.{decimals}f}{suffix}"


def fmt_cr(value):
    value = safe_float(value)

    if value is None:
        return "N/A"

    return f"Rs {value:,.0f} Cr"


def load_data():
    with sqlite3.connect(DB_PATH) as conn:
        companies = pd.read_sql_query(
            "SELECT * FROM companies", conn
        )
        sectors = pd.read_sql_query(
            "SELECT * FROM sectors", conn
        )
        ratios = pd.read_sql_query(
            "SELECT * FROM financial_ratios", conn
        )
        pnl = pd.read_sql_query(
            "SELECT * FROM profitandloss", conn
        )
        balance = pd.read_sql_query(
            "SELECT * FROM balancesheet", conn
        )
        cashflow = pd.read_sql_query(
            "SELECT * FROM cashflow", conn
        )
        market = pd.read_sql_query(
            "SELECT * FROM market_cap", conn
        )

    pros_cons = pd.read_csv(PROS_CONS_PATH)
    cashflow_intel = pd.read_excel(CASHFLOW_INTEL_PATH)

    frames = [
        sectors,
        ratios,
        pnl,
        balance,
        cashflow,
        market,
        pros_cons,
        cashflow_intel,
    ]

    for df in frames:
        if "company_id" in df.columns:
            df["company_id"] = (
                df["company_id"]
                .astype(str)
                .str.strip()
                .str.upper()
            )

    companies["id"] = (
        companies["id"]
        .astype(str)
        .str.strip()
        .str.upper()
    )

    return {
        "companies": companies,
        "sectors": sectors,
        "ratios": ratios,
        "pnl": pnl,
        "balance": balance,
        "cashflow": cashflow,
        "market": market,
        "pros_cons": pros_cons,
        "cashflow_intel": cashflow_intel,
    }


print("DAY 33 TEARSHEET FOUNDATION LOADED")


def fig_to_image(
    fig,
    width=170 * mm,
    height=58 * mm,
):
    buffer = BytesIO()

    fig.savefig(
        buffer,
        format="png",
        dpi=150,
        bbox_inches="tight",
    )

    plt.close(fig)

    buffer.seek(0)

    img = Image(
        buffer,
        width=width,
        height=height,
    )

    img._buffer_ref = buffer

    return img


def revenue_profit_chart(pnl):
    x = annual_rows(pnl).tail(10)

    fig, ax = plt.subplots(
        figsize=(8.5, 3.0)
    )

    if x.empty:
        ax.text(
            0.5,
            0.5,
            "No annual P&L data available",
            ha="center",
            va="center",
        )

        ax.axis("off")

        return fig_to_image(fig)

    years = (
        x["year"]
        .astype(str)
        .str[:4]
        .tolist()
    )

    revenue = pd.to_numeric(
        x["sales"],
        errors="coerce",
    ).fillna(0)

    profit = pd.to_numeric(
        x["net_profit"],
        errors="coerce",
    ).fillna(0)

    positions = np.arange(len(x))
    width = 0.38

    ax.bar(
        positions - width / 2,
        revenue,
        width,
        label="Revenue",
    )

    ax.bar(
        positions + width / 2,
        profit,
        width,
        label="Net Profit",
    )

    ax.set_xticks(positions)

    ax.set_xticklabels(
        years,
        rotation=45,
        ha="right",
    )

    ax.set_ylabel("Rs Crore")
    ax.set_title("10-Year Revenue and Net Profit")

    ax.legend(
        loc="upper left",
        fontsize=8,
    )

    ax.grid(
        axis="y",
        alpha=0.2,
    )

    fig.tight_layout()

    return fig_to_image(fig)


def roe_roce_chart(ratios):
    x = annual_rows(ratios).tail(10)

    fig, ax1 = plt.subplots(
        figsize=(8.5, 3.0)
    )

    if x.empty:
        ax1.text(
            0.5,
            0.5,
            "No annual ratio history available",
            ha="center",
            va="center",
        )

        ax1.axis("off")

        return fig_to_image(fig)

    years = (
        x["year"]
        .astype(str)
        .str[:4]
        .tolist()
    )

    roe = pd.to_numeric(
        x["return_on_equity_pct"],
        errors="coerce",
    )

    roce = pd.to_numeric(
        x["return_on_capital_employed_pct"],
        errors="coerce",
    )

    positions = np.arange(len(x))

    ax1.plot(
        positions,
        roe,
        marker="o",
        linewidth=2,
        label="ROE",
    )

    ax1.set_ylabel("ROE %")
    ax1.set_xticks(positions)

    ax1.set_xticklabels(
        years,
        rotation=45,
        ha="right",
    )

    ax2 = ax1.twinx()

    ax2.plot(
        positions,
        roce,
        marker="s",
        linewidth=2,
        linestyle="--",
        label="ROCE",
    )

    ax2.set_ylabel("ROCE %")
    ax1.set_title("ROE vs ROCE Trend")

    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()

    ax1.legend(
        lines1 + lines2,
        labels1 + labels2,
        loc="upper left",
        fontsize=8,
    )

    ax1.grid(alpha=0.2)

    fig.tight_layout()

    return fig_to_image(fig)


def balance_sheet_chart(balance):
    x = annual_rows(balance).tail(5)

    fig, ax = plt.subplots(
        figsize=(8.5, 2.8)
    )

    if x.empty:
        ax.text(
            0.5,
            0.5,
            "No balance sheet data available",
            ha="center",
            va="center",
        )

        ax.axis("off")

        return fig_to_image(
            fig,
            height=52 * mm,
        )

    years = (
        x["year"]
        .astype(str)
        .str[:4]
        .tolist()
    )

    equity_capital = pd.to_numeric(
        x["equity_capital"],
        errors="coerce",
    ).fillna(0)

    reserves = pd.to_numeric(
        x["reserves"],
        errors="coerce",
    ).fillna(0)

    equity = equity_capital + reserves

    borrowings = pd.to_numeric(
        x["borrowings"],
        errors="coerce",
    ).fillna(0)

    other_liabilities = pd.to_numeric(
        x["other_liabilities"],
        errors="coerce",
    ).fillna(0)

    ax.bar(
        years,
        equity,
        label="Equity + Reserves",
    )

    ax.bar(
        years,
        borrowings,
        bottom=equity,
        label="Borrowings",
    )

    ax.bar(
        years,
        other_liabilities,
        bottom=equity + borrowings,
        label="Other Liabilities",
    )

    ax.set_title("Balance Sheet Funding Mix")
    ax.set_ylabel("Rs Crore")

    ax.legend(
        fontsize=7,
        loc="upper left",
    )

    ax.grid(
        axis="y",
        alpha=0.2,
    )

    fig.tight_layout()

    return fig_to_image(
        fig,
        height=52 * mm,
    )


def cashflow_waterfall(cashflow):
    row = latest_annual(cashflow)

    fig, ax = plt.subplots(
        figsize=(8.5, 2.5)
    )

    if row is None:
        ax.text(
            0.5,
            0.5,
            "No annual cash flow data available",
            ha="center",
            va="center",
        )

        ax.axis("off")

        return fig_to_image(
            fig,
            height=45 * mm,
        )

    cfo = safe_float(
        row.get("operating_activity")
    ) or 0

    cfi = safe_float(
        row.get("investing_activity")
    ) or 0

    cff = safe_float(
        row.get("financing_activity")
    ) or 0

    total = safe_float(
        row.get("net_cash_flow")
    )

    if total is None:
        total = cfo + cfi + cff

    labels = [
        "CFO",
        "CFI",
        "CFF",
        "Net CF",
    ]

    values = [
        cfo,
        cfi,
        cff,
        total,
    ]

    ax.bar(
        range(4),
        values,
    )

    ax.axhline(
        0,
        linewidth=0.8,
    )

    ax.set_xticks(range(4))
    ax.set_xticklabels(labels)

    ax.set_ylabel("Rs Crore")
    ax.set_title(f"Cash Flow - {row['year']}")

    ax.grid(
        axis="y",
        alpha=0.2,
    )

    fig.tight_layout()

    return fig_to_image(
        fig,
        height=45 * mm,
    )


print("DAY 33 CHART HELPERS LOADED")


def build_styles():
    styles = getSampleStyleSheet()

    return {
        "section": ParagraphStyle(
            "Section",
            parent=styles["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=11,
            leading=13,
            textColor=NAVY,
            spaceBefore=3,
            spaceAfter=4,
        ),

        "small": ParagraphStyle(
            "Small",
            parent=styles["BodyText"],
            fontSize=7.5,
            leading=9,
            textColor=DARK,
        ),

        "signal": ParagraphStyle(
            "Signal",
            parent=styles["BodyText"],
            fontSize=7.5,
            leading=9,
            textColor=DARK,
            wordWrap="CJK",
        ),

        "center_small": ParagraphStyle(
            "CenterSmall",
            parent=styles["BodyText"],
            fontSize=7.5,
            leading=9,
            alignment=TA_CENTER,
            wordWrap="CJK",
        ),

        "tile_value": ParagraphStyle(
            "TileValue",
            parent=styles["BodyText"],
            fontName="Helvetica-Bold",
            fontSize=10,
            leading=12,
            alignment=TA_CENTER,
            textColor=NAVY,
            wordWrap="CJK",
        ),

        "tile_label": ParagraphStyle(
            "TileLabel",
            parent=styles["BodyText"],
            fontSize=6.5,
            leading=8,
            alignment=TA_CENTER,
            textColor=MID_GREY,
            wordWrap="CJK",
        ),
    }


def header_table(
    ticker,
    company_name,
    sector,
    report_year,
):
    title_style = ParagraphStyle(
        "HeaderTitle",
        fontName="Helvetica",
        fontSize=15,
        leading=18,
        textColor=WHITE,
        wordWrap="CJK",
    )

    meta_style = ParagraphStyle(
        "HeaderMeta",
        fontName="Helvetica",
        fontSize=8,
        leading=11,
        textColor=WHITE,
        wordWrap="CJK",
    )

    title = Paragraph(
        f"<b>{company_name}</b><br/>"
        f"<font size='9'>{ticker} | {sector}</font>",
        title_style,
    )

    meta = Paragraph(
        "<b>NIFTY100 FINANCIAL INTELLIGENCE</b><br/>"
        f"Annual data through {report_year}",
        meta_style,
    )

    table = Table(
        [[title, meta]],
        colWidths=[
            105 * mm,
            70 * mm,
        ],
        rowHeights=[
            23 * mm,
        ],
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
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "MIDDLE",
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
            ]
        )
    )

    return table


def kpi_tile(
    label,
    value,
    styles,
):
    return Table(
        [
            [
                Paragraph(
                    value,
                    styles["tile_value"],
                )
            ],
            [
                Paragraph(
                    label,
                    styles["tile_label"],
                )
            ],
        ],
        colWidths=[
            28.5 * mm,
        ],
    )


def kpi_table(
    ratio_row,
    market_row,
    styles,
):
    market_cap = (
        market_row.get("market_cap_crore")
        if market_row is not None
        else None
    )

    pe = (
        market_row.get("pe_ratio")
        if market_row is not None
        else None
    )

    roe = (
        ratio_row.get("return_on_equity_pct")
        if ratio_row is not None
        else None
    )

    debt_equity = (
        ratio_row.get("debt_to_equity")
        if ratio_row is not None
        else None
    )

    revenue_cagr = (
        ratio_row.get("revenue_cagr_5yr")
        if ratio_row is not None
        else None
    )

    pat_cagr = (
        ratio_row.get("pat_cagr_5yr")
        if ratio_row is not None
        else None
    )

    tiles = [
        kpi_tile(
            "Market Cap",
            fmt_cr(market_cap),
            styles,
        ),
        kpi_tile(
            "P/E",
            fmt_num(pe, 1, "x"),
            styles,
        ),
        kpi_tile(
            "ROE",
            fmt_num(roe, 1, "%"),
            styles,
        ),
        kpi_tile(
            "Debt / Equity",
            fmt_num(
                debt_equity,
                2,
                "x",
            ),
            styles,
        ),
        kpi_tile(
            "Revenue CAGR 5Y",
            fmt_num(
                revenue_cagr,
                1,
                "%",
            ),
            styles,
        ),
        kpi_tile(
            "PAT CAGR 5Y",
            fmt_num(
                pat_cagr,
                1,
                "%",
            ),
            styles,
        ),
    ]

    table = Table(
        [tiles],
        colWidths=[
            29 * mm,
        ] * 6,
    )

    table.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, -1),
                    LIGHT_GREY,
                ),
                (
                    "BOX",
                    (0, 0),
                    (-1, -1),
                    0.4,
                    colors.HexColor("#D1D5DB"),
                ),
                (
                    "INNERGRID",
                    (0, 0),
                    (-1, -1),
                    0.25,
                    colors.HexColor("#D1D5DB"),
                ),
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "MIDDLE",
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


def signal_table(
    title,
    signals,
    styles,
    positive=True,
):
    if positive:
        bg = GREEN_BG
        text_color = GREEN_TEXT
    else:
        bg = RED_BG
        text_color = RED_TEXT

    title_style = ParagraphStyle(
        f"{title}Title",
        parent=styles["section"],
        textColor=text_color,
        wordWrap="CJK",
    )

    rows = [
        [
            Paragraph(
                f"<b>{title}</b>",
                title_style,
            )
        ]
    ]

    if signals.empty:
        rows.append(
            [
                Paragraph(
                    "No qualifying signal under the defined rule set.",
                    styles["signal"],
                )
            ]
        )
    else:
        for _, row in signals.head(4).iterrows():
            confidence = safe_float(
                row.get("confidence_pct")
            )

            confidence_text = (
                f"{confidence:.0f}%"
                if confidence is not None
                else "N/A"
            )

            text = (
                f"<b>{row['rule_id']}</b> "
                f"({confidence_text}) - "
                f"{row['text']}"
            )

            rows.append(
                [
                    Paragraph(
                        text,
                        styles["signal"],
                    )
                ]
            )

    table = Table(
        rows,
        colWidths=[
            84 * mm,
        ],
    )

    table.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, -1),
                    bg,
                ),
                (
                    "BOX",
                    (0, 0),
                    (-1, -1),
                    0.5,
                    text_color,
                ),
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "TOP",
                ),
                (
                    "LEFTPADDING",
                    (0, 0),
                    (-1, -1),
                    5,
                ),
                (
                    "RIGHTPADDING",
                    (0, 0),
                    (-1, -1),
                    5,
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
        )
    )

    return table


def allocation_badge(
    intel_row,
    styles,
):
    if intel_row is None:
        label = "Data Unavailable"
        quality = "Data Unavailable"
        capex = "Data Unavailable"
        deleveraging = False
        distress = False

    else:
        label = intel_row.get(
            "capital_allocation_label",
            "Data Unavailable",
        )

        quality = intel_row.get(
            "cfo_quality_label",
            "Data Unavailable",
        )

        capex = intel_row.get(
            "capex_label",
            "Data Unavailable",
        )

        deleveraging = bool(
            intel_row.get(
                "deleveraging_flag",
                False,
            )
        )

        distress = bool(
            intel_row.get(
                "distress_flag",
                False,
            )
        )

    table = Table(
        [
            [
                Paragraph(
                    "<b>Capital Allocation</b>",
                    styles["center_small"],
                ),
                Paragraph(
                    "<b>CFO Quality</b>",
                    styles["center_small"],
                ),
                Paragraph(
                    "<b>CapEx Profile</b>",
                    styles["center_small"],
                ),
            ],
            [
                Paragraph(
                    str(label),
                    styles["center_small"],
                ),
                Paragraph(
                    str(quality),
                    styles["center_small"],
                ),
                Paragraph(
                    str(capex),
                    styles["center_small"],
                ),
            ],
            [
                Paragraph(
                    f"Deleveraging: {'Yes' if deleveraging else 'No'}",
                    styles["center_small"],
                ),
                Paragraph(
                    f"Distress: {'Yes' if distress else 'No'}",
                    styles["center_small"],
                ),
                Paragraph(
                    "",
                    styles["center_small"],
                ),
            ],
        ],
        colWidths=[
            58 * mm,
            58 * mm,
            58 * mm,
        ],
    )

    table.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, 0),
                    NAVY,
                ),
                (
                    "TEXTCOLOR",
                    (0, 0),
                    (-1, 0),
                    WHITE,
                ),
                (
                    "BACKGROUND",
                    (0, 1),
                    (-1, -1),
                    LIGHT_NAVY,
                ),
                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.4,
                    colors.HexColor("#B6C8DA"),
                ),
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "MIDDLE",
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
        )
    )

    return table


def footer(canvas, doc):
    canvas.saveState()

    canvas.setFont(
        "Helvetica",
        7,
    )

    canvas.setFillColor(
        MID_GREY
    )

    canvas.drawString(
        18 * mm,
        8 * mm,
        "Nifty100 Financial Intelligence Platform",
    )

    canvas.drawRightString(
        192 * mm,
        8 * mm,
        f"Page {doc.page}",
    )

    canvas.restoreState()


print("DAY 33 PDF COMPONENTS LOADED")


def create_tearsheet(
    ticker,
    data,
):
    ticker = ticker.upper()

    company_rows = data["companies"][
        data["companies"]["id"] == ticker
    ]

    if company_rows.empty:
        raise ValueError(
            f"Unknown company: {ticker}"
        )

    company = company_rows.iloc[0]

    sector_rows = data["sectors"][
        data["sectors"]["company_id"] == ticker
    ]

    if not sector_rows.empty and "broad_sector" in sector_rows.columns:
        sector = sector_rows.iloc[0]["broad_sector"]
    else:
        sector = "Unknown"

    ratio_df = data["ratios"][
        data["ratios"]["company_id"] == ticker
    ]

    pnl_df = data["pnl"][
        data["pnl"]["company_id"] == ticker
    ]

    balance_df = data["balance"][
        data["balance"]["company_id"] == ticker
    ]

    cashflow_df = data["cashflow"][
        data["cashflow"]["company_id"] == ticker
    ]

    market_df = data["market"][
        data["market"]["company_id"] == ticker
    ]

    ratio_row = latest_annual(
        ratio_df
    )

    market_row = latest_annual(
        market_df
    )

    report_year = (
        ratio_row["year"]
        if ratio_row is not None
        else "N/A"
    )

    pros = data["pros_cons"][
        (
            data["pros_cons"]["company_id"]
            == ticker
        )
        &
        (
            data["pros_cons"]["type"]
            == "pro"
        )
    ].copy()

    cons = data["pros_cons"][
        (
            data["pros_cons"]["company_id"]
            == ticker
        )
        &
        (
            data["pros_cons"]["type"]
            == "con"
        )
    ].copy()

    if not pros.empty:
        pros = pros.sort_values(
            "confidence_pct",
            ascending=False,
        )

    if not cons.empty:
        cons = cons.sort_values(
            "confidence_pct",
            ascending=False,
        )

    intel_rows = data["cashflow_intel"][
        data["cashflow_intel"]["company_id"]
        == ticker
    ]

    intel_row = (
        intel_rows.iloc[0]
        if not intel_rows.empty
        else None
    )

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    output_path = (
        OUTPUT_DIR
        / f"{ticker}_tearsheet.pdf"
    )

    styles = build_styles()

    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=A4,
        rightMargin=15 * mm,
        leftMargin=15 * mm,
        topMargin=12 * mm,
        bottomMargin=15 * mm,
        title=f"{ticker} Financial Tearsheet",
        author="Nifty100 Financial Intelligence",
    )

    story = []

    # PAGE 1

    story.append(
        header_table(
            ticker=ticker,
            company_name=company["company_name"],
            sector=sector,
            report_year=report_year,
        )
    )

    story.append(
        Spacer(
            1,
            4 * mm,
        )
    )

    story.append(
        kpi_table(
            ratio_row,
            market_row,
            styles,
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
            "Financial Performance",
            styles["section"],
        )
    )

    story.append(
        revenue_profit_chart(
            pnl_df
        )
    )

    story.append(
        Spacer(
            1,
            2 * mm,
        )
    )

    story.append(
        Paragraph(
            "Return Ratios",
            styles["section"],
        )
    )

    story.append(
        roe_roce_chart(
            ratio_df
        )
    )

    # PAGE 2

    story.append(
        PageBreak()
    )

    story.append(
        header_table(
            ticker=ticker,
            company_name=company["company_name"],
            sector=sector,
            report_year=report_year,
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
            "Balance Sheet Structure",
            styles["section"],
        )
    )

    story.append(
        balance_sheet_chart(
            balance_df
        )
    )

    story.append(
        Spacer(
            1,
            1 * mm,
        )
    )

    story.append(
        Paragraph(
            "Cash Flow",
            styles["section"],
        )
    )

    story.append(
        cashflow_waterfall(
            cashflow_df
        )
    )

    story.append(
        Spacer(
            1,
            2 * mm,
        )
    )

    story.append(
        allocation_badge(
            intel_row,
            styles,
        )
    )

    story.append(
        Spacer(
            1,
            3 * mm,
        )
    )

    pro_table = signal_table(
        "Key Pros",
        pros,
        styles,
        positive=True,
    )

    con_table = signal_table(
        "Key Cons",
        cons,
        styles,
        positive=False,
    )

    signals = Table(
        [
            [
                pro_table,
                con_table,
            ]
        ],
        colWidths=[
            87 * mm,
            87 * mm,
        ],
    )

    signals.setStyle(
        TableStyle(
            [
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "TOP",
                ),
                (
                    "LEFTPADDING",
                    (0, 0),
                    (-1, -1),
                    0,
                ),
                (
                    "RIGHTPADDING",
                    (0, 0),
                    (-1, -1),
                    3,
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    0,
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    0,
                ),
            ]
        )
    )

    story.append(
        KeepTogether(
            signals
        )
    )

    doc.build(
        story,
        onFirstPage=footer,
        onLaterPages=footer,
    )

    return output_path


def main():
    data = load_data()

    tickers = (
        [
            item.strip().upper()
            for item in sys.argv[1:]
            if item.strip()
        ]
        or TEST_TICKERS
    )

    print(
        "=" * 90
    )

    print(
        "SPRINT 5 - DAY 33 TEARSHEET PROTOTYPE"
    )

    print(
        "=" * 90
    )

    generated = []

    for ticker in tickers:
        try:
            path = create_tearsheet(
                ticker,
                data,
            )

            size_kb = (
                path.stat().st_size
                / 1024
            )

            generated.append(
                (
                    ticker,
                    path,
                    size_kb,
                )
            )

            print(
                f"[PASS] {ticker}: "
                f"{size_kb:.1f} KB"
            )

        except Exception as exc:
            print(
                f"[FAIL] {ticker}: {exc}"
            )
            raise

    print(
        f"\nGenerated: {len(generated)}"
    )

    print(
        f"Output directory: {OUTPUT_DIR}"
    )

    print(
        "\nDAY 33 PDF GENERATOR: PASS"
    )


if __name__ == "__main__":
    main()
