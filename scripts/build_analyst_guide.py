from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = PROJECT_ROOT / "docs"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT_FILE = OUTPUT_DIR / "analyst_guide.pdf"

PAGE_WIDTH, PAGE_HEIGHT = A4

styles = getSampleStyleSheet()

title_style = ParagraphStyle(
    "GuideTitle",
    parent=styles["Title"],
    fontName="Helvetica-Bold",
    fontSize=24,
    leading=30,
    alignment=TA_CENTER,
    spaceAfter=18,
)

subtitle_style = ParagraphStyle(
    "GuideSubtitle",
    parent=styles["Normal"],
    fontName="Helvetica",
    fontSize=12,
    leading=18,
    alignment=TA_CENTER,
    textColor=colors.HexColor("#444444"),
)

heading_style = ParagraphStyle(
    "SectionHeading",
    parent=styles["Heading1"],
    fontName="Helvetica-Bold",
    fontSize=18,
    leading=22,
    spaceAfter=12,
)

subheading_style = ParagraphStyle(
    "SubHeading",
    parent=styles["Heading2"],
    fontName="Helvetica-Bold",
    fontSize=12,
    leading=16,
    spaceBefore=8,
    spaceAfter=6,
)

body_style = ParagraphStyle(
    "Body",
    parent=styles["BodyText"],
    fontName="Helvetica",
    fontSize=10,
    leading=15,
    spaceAfter=8,
)

small_style = ParagraphStyle(
    "Small",
    parent=body_style,
    fontSize=8.5,
    leading=12,
)


def add_page_number(canvas, doc):
    """Add page number and footer text to each page."""
    canvas.saveState()

    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(colors.HexColor("#666666"))

    canvas.drawString(
        18 * mm,
        10 * mm,
        "Nifty 100 Financial Intelligence Platform",
    )

    canvas.drawRightString(
        PAGE_WIDTH - 18 * mm,
        10 * mm,
        f"Page {doc.page}",
    )

    canvas.restoreState()


def section_title(story, title, subtitle=None):
    """Add a section heading and optional subtitle."""
    story.append(Paragraph(title, heading_style))

    if subtitle:
        story.append(Paragraph(subtitle, body_style))

    story.append(Spacer(1, 6))


def bullet(story, text):
    """Add a formatted bullet paragraph."""
    story.append(
        Paragraph(
            f"- {text}",
            body_style,
        )
    )


def add_key_value_table(story, rows):
    """Add a simple two-column key-value table."""
    data = [
        [
            Paragraph(str(key), small_style),
            Paragraph(str(value), small_style),
        ]
        for key, value in rows
    ]

    table = Table(
        data,
        colWidths=[55 * mm, 115 * mm],
        repeatRows=0,
    )

    table.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#BBBBBB")),
                ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#F2F2F2")),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )

    story.append(table)
    story.append(Spacer(1, 10))


def build_guide():
    """Build the analyst guide PDF."""
    doc = SimpleDocTemplate(
        str(OUTPUT_FILE),
        pagesize=A4,
        rightMargin=18 * mm,
        leftMargin=18 * mm,
        topMargin=18 * mm,
        bottomMargin=18 * mm,
        title="Nifty 100 Financial Intelligence Analyst Guide",
        author="Nifty 100 Financial Intelligence Platform",
    )

    story = []

    story.append(Spacer(1, 35 * mm))
    story.append(
        Paragraph(
            "Nifty 100 Financial Intelligence Platform",
            title_style,
        )
    )
    story.append(
        Paragraph(
            "Analyst Guide",
            title_style,
        )
    )
    story.append(
        Paragraph(
            "A practical guide to the data foundation, analytics engine, "
            "dashboard, API, clustering, financial intelligence, reporting, "
            "testing, and source-truth principles of the platform.",
            subtitle_style,
        )
    )
    story.append(Spacer(1, 20 * mm))

    add_key_value_table(
        story,
        [
            ("Universe", "Nifty 100 source dataset"),
            ("Companies", "92"),
            ("Database", "SQLite"),
            ("Dashboard", "Streamlit"),
            ("API", "FastAPI"),
            ("Automated tests", "168 passing"),
            ("Company archetypes", "5 KMeans clusters"),
            ("Primary objective", "Financial analytics and research automation"),
        ],
    )

    story.append(PageBreak())

    section_title(
        story,
        "1. Platform Overview",
        "The platform combines data engineering, financial analytics, "
        "screening, peer comparison, valuation, clustering, NLP-style "
        "financial signals, dashboards, APIs, and automated reporting.",
    )

    bullet(story, "92 companies are represented in the source company universe.")
    bullet(story, "Financial data is normalized and stored in SQLite.")
    bullet(
        story, "Financial ratios and growth metrics are calculated programmatically."
    )
    bullet(story, "A multi-factor screener supports both presets and custom filters.")
    bullet(story, "Peer analytics provide percentile-based relative comparison.")
    bullet(story, "A Streamlit dashboard provides interactive analyst workflows.")
    bullet(story, "A FastAPI service exposes the platform programmatically.")
    bullet(story, "KMeans clustering groups companies into five financial archetypes.")
    bullet(story, "Automated PDF reports summarize company and portfolio intelligence.")

    story.append(Spacer(1, 8))
    story.append(
        Paragraph(
            "The project follows a source-truth-first design. Missing, unusual, "
            "or incomplete source information is documented rather than fabricated "
            "or adjusted only to satisfy expected outcomes.",
            body_style,
        )
    )

    story.append(PageBreak())
    section_title(
        story,
        "2. Data Foundation",
        "Sprint 1 established the data model, ETL workflow, normalization rules, "
        "SQLite database, and data-quality framework used by the rest of the platform.",
    )

    bullet(story, "Raw data is organized into core and supplementary source folders.")
    bullet(story, "Company identifiers are normalized to ticker-based keys.")
    bullet(story, "Year values are normalized into consistent reporting periods.")
    bullet(story, "Duplicate financial rows are removed using deterministic rules.")
    bullet(story, "Invalid or orphan records are rejected before database loading.")
    bullet(story, "The SQLite database contains 12 analytical tables.")
    bullet(story, "Foreign-key integrity is validated after loading.")
    bullet(story, "A multi-rule data-quality engine records validation failures.")

    add_key_value_table(
        story,
        [
            ("Companies", "92"),
            ("Profit and Loss rows", "1,070"),
            ("Balance Sheet rows", "1,140"),
            ("Cash Flow rows", "1,056"),
            ("Stock price rows", "5,520"),
            ("Market-cap rows", "552"),
            ("Peer-group rows", "56"),
            ("Foreign-key violations", "0"),
        ],
    )

    story.append(
        Paragraph(
            "Data-quality checks are treated as part of the analytical pipeline, not "
            "as a separate afterthought. Critical issues are resolved before downstream "
            "analytics are considered reliable.",
            body_style,
        )
    )

    story.append(PageBreak())

    section_title(
        story,
        "3. Financial Ratio Engine",
        "Sprint 2 created the reusable KPI layer that powers screening, peer analysis, "
        "valuation, clustering, dashboard views, and API responses.",
    )

    bullet(story, "Profitability metrics include ROE, ROCE, ROA, NPM, and OPM.")
    bullet(
        story,
        "Leverage and efficiency metrics include Debt-to-Equity and related ratios.",
    )
    bullet(story, "Revenue, PAT, and EPS CAGR calculations handle multiple edge cases.")
    bullet(
        story, "Financial-sector companies are handled separately where appropriate."
    )
    bullet(story, "Cash-flow conversion and growth metrics support quality analysis.")
    bullet(story, "Computed ratios are persisted for reuse across the platform.")

    add_key_value_table(
        story,
        [
            ("Financial ratio rows", "1,155"),
            ("Primary use", "Screening and company analysis"),
            ("Growth handling", "CAGR with edge-case flags"),
            ("Sector-aware logic", "Yes"),
            ("Downstream reuse", "Dashboard, API, peers, valuation, clustering"),
        ],
    )

    story.append(
        Paragraph(
            "The ratio engine preserves unusual source-derived values rather than "
            "silently replacing them. This is important because some source ROE and "
            "ROCE observations are extreme and materially affect statistical analysis.",
            body_style,
        )
    )

    story.append(PageBreak())

    section_title(
        story,
        "4. Screener and Peer Comparison",
        "Sprint 3 added preset screening strategies, custom filtering, composite "
        "scores, peer-group analytics, and percentile-based comparison.",
    )

    bullet(story, "The screener supports both preset strategies and custom filters.")
    bullet(
        story,
        "Preset logic is kept exact instead of being weakened to increase counts.",
    )
    bullet(story, "Company rankings combine multiple financial dimensions.")
    bullet(
        story,
        "Peer groups allow like-for-like comparison within comparable businesses.",
    )
    bullet(story, "Percentile ranks provide relative positioning across peer metrics.")
    bullet(story, "Radar-chart data is generated for visual peer comparison.")

    add_key_value_table(
        story,
        [
            ("Quality Compounder", "22 companies"),
            ("Value Pick", "2 companies"),
            ("Growth Accelerator", "19 companies"),
            ("Dividend Champion", "30 companies"),
            ("Debt-Free Blue Chip", "2 companies"),
            ("Turnaround Watch", "31 companies"),
            ("Peer groups", "11"),
            ("Peer percentile rows", "560"),
        ],
    )

    story.append(
        Paragraph(
            "The screener is intended as an analytical narrowing tool rather than "
            "a recommendation engine. A low count in a strict preset is considered "
            "valid when it reflects the actual rule set.",
            body_style,
        )
    )

    story.append(PageBreak())

    section_title(
        story,
        "5. Dashboard and Valuation",
        "Sprint 4 delivered the interactive analyst dashboard and valuation workflow.",
    )

    bullet(story, "The Streamlit dashboard contains eight analyst-facing screens.")
    bullet(story, "Database access is cached to improve dashboard responsiveness.")
    bullet(
        story, "Company profiles combine fundamentals, ratios, valuation, and reports."
    )
    bullet(story, "The screener can be used interactively from the dashboard.")
    bullet(story, "Peer comparison and sector analysis are available visually.")
    bullet(story, "Capital-allocation data is integrated where source coverage exists.")
    bullet(
        story,
        "The valuation engine combines market-cap, earnings, and cash-flow metrics.",
    )

    add_key_value_table(
        story,
        [
            ("Day 22", "Streamlit foundation and cached DB layer - DONE"),
            ("Day 23", "Home and Company Profile - DONE"),
            ("Day 24", "Screener and Peer Comparison - DONE"),
            ("Day 25", "Trends, Sectors, Capital Allocation and Reports - DONE"),
            ("Day 26", "Valuation Module - DONE"),
            ("Day 27", "Dashboard QA - DONE"),
            ("Day 28", "Documentation and final release - DONE"),
            ("Sprint 4 Status", "COMPLETE"),
        ],
    )

    story.append(
        Paragraph(
            "The valuation module exports reusable analytical outputs and is also "
            "consumed by dashboard and reporting workflows.",
            body_style,
        )
    )

    story.append(PageBreak())
    section_title(
        story,
        "6. Financial Intelligence and Automated Reporting",
        "Sprint 5 expanded the platform from traditional financial analytics into "
        "rule-based intelligence, cash-flow analysis, capital-allocation analysis, "
        "and automated PDF reporting.",
    )

    bullet(
        story,
        "Financial text and analysis data are parsed into structured information.",
    )
    bullet(story, "A 24-rule engine generates evidence-based PRO and CON signals.")
    bullet(story, "Signal confidence is based on the underlying financial conditions.")
    bullet(
        story, "Cash-flow intelligence evaluates FCF quality, conversion, and growth."
    )
    bullet(
        story, "Distress and deleveraging indicators provide additional risk context."
    )
    bullet(
        story, "Capital-allocation patterns are analyzed from available source history."
    )
    bullet(
        story, "Company tear sheets are generated automatically with charts and KPIs."
    )
    bullet(story, "Peer-group reports and a portfolio summary provide broader context.")

    add_key_value_table(
        story,
        [
            ("Signal rules", "24"),
            ("Generated PRO signals", "398"),
            ("Generated CON signals", "108"),
            ("Total signals", "506"),
            ("Companies with PRO coverage", "89"),
            ("Companies with CON coverage", "57"),
            ("Eligible company tear sheets", "88"),
            ("Peer-group reports", "11"),
        ],
    )

    story.append(
        Paragraph(
            "Coverage is deliberately not forced to 100 percent. A company receives "
            "a PRO or CON only when the relevant rule is satisfied. Likewise, companies "
            "with insufficient annual history are not given fabricated tear sheets.",
            body_style,
        )
    )

    story.append(PageBreak())

    section_title(
        story,
        "7. Clustering and Statistical Intelligence",
        "Sprint 6 introduces unsupervised learning and portfolio-level statistical "
        "analysis to identify financial archetypes, relationships, and outliers.",
    )

    bullet(story, "Five financial features are standardized before clustering.")
    bullet(story, "Missing observations use sector-median imputation where possible.")
    bullet(
        story,
        "A portfolio median is used only when the sector itself has no usable value.",
    )
    bullet(story, "KMeans uses five clusters with random_state=42 for reproducibility.")
    bullet(
        story, "Elbow analysis evaluates candidate cluster counts from 2 through 10."
    )
    bullet(story, "A 10-KPI correlation matrix supports relationship analysis.")
    bullet(story, "Sector-relative z-scores identify extreme observations.")
    bullet(story, "Portfolio statistics provide distribution and percentile context.")

    add_key_value_table(
        story,
        [
            ("Core Balanced Companies", "58"),
            ("High Margin / Mixed Quality", "16"),
            ("ROE Outliers", "2"),
            ("FCF Growth Outliers", "2"),
            ("Leveraged Financial Growth", "14"),
            ("Total clustered companies", "92"),
        ],
    )

    story.append(
        Paragraph(
            "Cluster names are descriptive labels derived from cluster profiles. "
            "They are analytical archetypes, not investment ratings.",
            body_style,
        )
    )

    story.append(PageBreak())
    section_title(
        story,
        "8. FastAPI Service",
        "Sprint 6 exposes the analytical platform through a versioned FastAPI "
        "service for programmatic access and integration.",
    )

    bullet(story, "The API uses the /api/v1 prefix.")
    bullet(story, "A health endpoint reports service status and database counts.")
    bullet(story, "Company endpoints expose profiles and financial statements.")
    bullet(story, "Ratio history can be retrieved by company and reporting period.")
    bullet(story, "The screener is accessible through query parameters.")
    bullet(story, "Sector and peer-group endpoints support comparative analysis.")
    bullet(story, "Market-cap and portfolio-statistics endpoints are available.")
    bullet(story, "Company documents and tear sheets are accessible through the API.")
    bullet(story, "OpenAPI and Postman specifications are exported in docs.")

    add_key_value_table(
        story,
        [
            ("API framework", "FastAPI"),
            ("Version prefix", "/api/v1"),
            ("API endpoints", "16"),
            ("Local port", "8000"),
            ("Interactive docs", "/docs"),
            ("Alternative docs", "/redoc"),
            ("Health endpoint", "/api/v1/health"),
            ("OpenAPI export", "docs/openapi.json"),
        ],
    )

    story.append(
        Paragraph(
            "The API reuses the analytical engines used elsewhere in the "
            "platform. This helps prevent calculation differences between "
            "the dashboard, API, and underlying analytics.",
            body_style,
        )
    )

    story.append(PageBreak())

    section_title(
        story,
        "9. Testing, QA and Performance",
        "Automated testing and performance validation protect the data "
        "pipeline, analytics, API behavior, and integration workflows.",
    )

    bullet(story, "ETL tests validate normalization and loading behavior.")
    bullet(story, "KPI tests verify financial calculations and edge cases.")
    bullet(story, "Data-quality tests cover the validation framework.")
    bullet(
        story, "API tests cover companies, screening, sectors, peers, and documents."
    )
    bullet(story, "Integration tests compare API screening with the core engine.")
    bullet(story, "An HTML pytest report provides test-run evidence.")
    bullet(story, "Concurrent screener calls are tested for performance.")
    bullet(story, "Company-profile endpoints are tested for response time.")
    bullet(story, "Streamlit and FastAPI are verified to operate simultaneously.")

    add_key_value_table(
        story,
        [
            ("Automated tests", "168"),
            ("Current failures", "0"),
            ("API tests", "32"),
            ("Black", "PASS"),
            ("Ruff", "PASS"),
            ("Screener target", "Less than 10 seconds"),
            ("Company profile target", "Less than 3 seconds"),
            ("HTML report", "reports/pytest_report.html"),
        ],
    )

    story.append(
        Paragraph(
            "The verified project regression suite currently completes with "
            "168 passing tests and zero failures.",
            body_style,
        )
    )

    story.append(PageBreak())

    section_title(
        story,
        "10. Analyst Workflow",
        "The platform is designed to support a repeatable research workflow "
        "from universe selection through company-level investigation.",
    )

    story.append(Paragraph("Step 1 - Screen the universe", subheading_style))
    story.append(
        Paragraph(
            "Start with a preset strategy or custom screener conditions to "
            "reduce the company universe to candidates matching the required "
            "financial characteristics.",
            body_style,
        )
    )

    story.append(Paragraph("Step 2 - Review company fundamentals", subheading_style))
    story.append(
        Paragraph(
            "Inspect historical profit and loss, balance-sheet, cash-flow, "
            "ratio, growth, and market-cap information.",
            body_style,
        )
    )

    story.append(Paragraph("Step 3 - Compare peers", subheading_style))
    story.append(
        Paragraph(
            "Use peer percentiles and radar-style comparisons to understand "
            "whether a company is strong or weak relative to comparable businesses.",
            body_style,
        )
    )

    story.append(Paragraph("Step 4 - Evaluate valuation", subheading_style))
    story.append(
        Paragraph(
            "Review valuation metrics together with profitability, growth, "
            "cash-flow quality, and historical context rather than treating "
            "valuation as a standalone decision.",
            body_style,
        )
    )

    story.append(Paragraph("Step 5 - Review intelligence signals", subheading_style))
    story.append(
        Paragraph(
            "Use PRO and CON signals as evidence summaries. A missing signal "
            "does not imply a positive or negative conclusion.",
            body_style,
        )
    )

    story.append(Paragraph("Step 6 - Inspect statistical context", subheading_style))
    story.append(
        Paragraph(
            "Review company clusters, portfolio percentiles, correlations, "
            "and outliers to understand broader positioning.",
            body_style,
        )
    )

    story.append(Paragraph("Step 7 - Review source documents", subheading_style))
    story.append(
        Paragraph(
            "Where important decisions depend on a number or narrative, "
            "analysts should review the available source documents and "
            "independently verify material information.",
            body_style,
        )
    )

    story.append(PageBreak())

    section_title(
        story,
        "11. Source-Truth Principles and Known Constraints",
        "The platform deliberately distinguishes between a software defect "
        "and a limitation inherited from the source data.",
    )

    bullet(
        story,
        "The source company universe contains 92 usable company records.",
    )
    bullet(
        story,
        "The broad sector taxonomy contains 10 sectors while peer analytics "
        "contain 11 peer groups.",
    )
    bullet(
        story,
        "Some source-derived ROE and ROCE observations are unusually large.",
    )
    bullet(
        story,
        "Extreme observations are retained when they are traceable to source data.",
    )
    bullet(
        story,
        "PRO and CON signals are not fabricated to force full company coverage.",
    )
    bullet(
        story,
        "Current rule-based coverage includes 89 companies with at least one "
        "PRO and 57 with at least one CON.",
    )
    bullet(
        story,
        "Only 88 companies currently meet the annual-history requirement for "
        "full company tear-sheet generation.",
    )
    bullet(
        story,
        "AMBUJACEM, JIOFIN, NESTLEIND, and SIEMENS are skipped by the batch "
        "tear-sheet process when they do not satisfy the required annual history.",
    )
    bullet(
        story,
        "ATGL has unavailable source information for parts of the "
        "capital-allocation and cash-flow intelligence workflow.",
    )
    bullet(
        story,
        "Missing values are reported transparently rather than replaced with "
        "invented financial conclusions.",
    )

    story.append(Spacer(1, 8))

    story.append(
        Paragraph(
            "These constraints are important when interpreting acceptance "
            "criteria. The project prioritizes reproducibility and source truth "
            "over manipulating data merely to obtain a desired checklist result.",
            body_style,
        )
    )

    story.append(PageBreak())

    section_title(
        story,
        "12. Operating Guide and Conclusion",
        "The platform can be operated locally as an analytics application, "
        "dashboard, API service, and reporting system.",
    )

    story.append(Paragraph("Run the dashboard", subheading_style))
    story.append(
        Paragraph(
            "python -m streamlit run src/dashboard/app.py",
            body_style,
        )
    )

    story.append(Paragraph("Run the API", subheading_style))
    story.append(
        Paragraph(
            "python -m uvicorn src.api.main:app --host 127.0.0.1 "
            "--port 8000 --reload",
            body_style,
        )
    )

    story.append(Paragraph("Run clustering", subheading_style))
    story.append(
        Paragraph(
            "python -m src.analytics.clustering",
            body_style,
        )
    )

    story.append(Paragraph("Run valuation", subheading_style))
    story.append(
        Paragraph(
            "python -m src.analytics.valuation",
            body_style,
        )
    )

    story.append(Paragraph("Run automated tests", subheading_style))
    story.append(
        Paragraph(
            "pytest -q",
            body_style,
        )
    )

    story.append(Paragraph("Run code-quality checks", subheading_style))
    story.append(
        Paragraph(
            "python -m black --check src tests",
            body_style,
        )
    )
    story.append(
        Paragraph(
            "python -m ruff check src tests",
            body_style,
        )
    )

    story.append(Spacer(1, 10))

    add_key_value_table(
        story,
        [
            ("Company universe", "92"),
            ("Financial ratio records", "1,155"),
            ("Broad sectors", "10"),
            ("Peer groups", "11"),
            ("KMeans clusters", "5"),
            ("FastAPI endpoints", "16"),
            ("Dashboard screens", "8"),
            ("Automated tests", "168 passing"),
        ],
    )

    story.append(
        Paragraph(
            "The Nifty 100 Financial Intelligence Platform demonstrates an "
            "end-to-end financial analytics workflow combining data engineering, "
            "financial modelling, statistical analysis, machine learning, "
            "interactive visualization, APIs, automated testing, and reporting.",
            body_style,
        )
    )

    story.append(
        Paragraph(
            "The system is intended for educational, analytical, and "
            "portfolio-development purposes. It does not provide investment advice.",
            body_style,
        )
    )

    add_required_usage_sections(story, styles)

    doc.build(
        story,
        onFirstPage=add_page_number,
        onLaterPages=add_page_number,
    )

    print(f"Analyst Guide created: {OUTPUT_FILE}")


# === DAY 44 REQUIRED USER GUIDE SECTIONS ===


def add_required_usage_sections(story, styles):
    """Add the Day 44 required analyst guide usage sections."""
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_LEFT
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import PageBreak, Paragraph, Spacer, Table, TableStyle

    body = styles["BodyText"]
    heading1 = styles["Heading1"]
    heading2 = styles["Heading2"]

    code_style = ParagraphStyle(
        "Day44GuideCode",
        parent=body,
        fontName="Courier",
        fontSize=8,
        leading=10,
        leftIndent=10,
        rightIndent=10,
        spaceBefore=6,
        spaceAfter=8,
        alignment=TA_LEFT,
    )

    def add_table(rows, widths):
        """Add a consistently formatted guide table."""
        table = Table(rows, colWidths=widths, repeatRows=1)
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                    ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 8),
                    ("LEADING", (0, 0), (-1, -1), 10),
                    ("LEFTPADDING", (0, 0), (-1, -1), 5),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                    ("TOPPADDING", (0, 0), (-1, -1), 5),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ]
            )
        )
        story.append(table)

    story.append(PageBreak())
    story.append(Paragraph("13. Streamlit Screener - How to Use It", heading1))
    story.append(
        Paragraph(
            "Start the dashboard from the project root with "
            "<b>streamlit run src/dashboard/app.py</b>. "
            "Open the local Streamlit URL shown in the terminal and navigate "
            "to the Screener screen.",
            body,
        )
    )

    screener_steps = [
        ["Step", "Action"],
        ["1", "Open the Screener page from the dashboard navigation."],
        ["2", "Choose a built-in preset or configure custom filters."],
        [
            "3",
            "Set filters such as minimum ROE, maximum debt-to-equity, "
            "minimum revenue CAGR, minimum PAT CAGR, sector, FCF and P/E.",
        ],
        ["4", "Run the screener to generate the ranked company list."],
        ["5", "Review metrics and composite ranking."],
        ["6", "Export the filtered result when CSV download is required."],
        [
            "7",
            "Cross-check shortlisted companies using Profile, Peers, "
            "Trends and Reports.",
        ],
    ]

    add_table(screener_steps, [0.55 * inch, 6.5 * inch])

    story.append(Spacer(1, 10))
    story.append(
        Paragraph(
            "Built-in presets use their defined financial rules without "
            "weakening thresholds merely to increase the number of results.",
            body,
        )
    )

    story.append(PageBreak())
    story.append(Paragraph("14. Dashboard Navigation - All 8 Screens", heading1))

    screens = [
        (
            "1. Home",
            "Provides the portfolio-level landing view with headline KPIs, "
            "coverage information and high-level financial summaries.",
        ),
        (
            "2. Company Profile",
            "Displays one company's financial history, key ratios, latest "
            "metrics, business information and supporting analysis.",
        ),
        (
            "3. Screener",
            "Filters and ranks companies using financial rules, presets "
            "and custom thresholds.",
        ),
        (
            "4. Peers",
            "Compares companies within peer groups using percentile metrics, "
            "benchmarking and radar-style relative analysis.",
        ),
        (
            "5. Trends",
            "Shows historical financial and ratio trends to identify growth, "
            "deterioration, consistency and cyclicality.",
        ),
        (
            "6. Sectors",
            "Summarizes broad-sector performance and enables sector-level "
            "comparison of companies.",
        ),
        (
            "7. Capital",
            "Focuses on capital allocation, cash-flow intelligence, leverage "
            "changes and related financial-quality signals.",
        ),
        (
            "8. Reports",
            "Provides access to company tearsheets, sector reports and "
            "portfolio-level reports.",
        ),
    ]

    for title, description in screens:
        story.append(Paragraph(title, heading2))
        story.append(Paragraph(description, body))
        story.append(Spacer(1, 6))

    story.append(
        Paragraph(
            "A typical workflow begins on Home, moves to Screener for discovery, "
            "uses Company Profile and Trends for historical analysis, Peers and "
            "Sectors for relative comparison, Capital for cash-flow analysis, "
            "and Reports for final review.",
            body,
        )
    )

    story.append(PageBreak())
    story.append(Paragraph("15. Generating PDF Tearsheets", heading1))

    story.append(
        Paragraph(
            "Company tearsheets are generated from the SQLite financial "
            "database, calculated ratios and intelligence outputs. Run the "
            "commands from the project root while the virtual environment "
            "is active.",
            body,
        )
    )

    story.append(Paragraph("Single-company reporting module", heading2))
    story.append(
        Paragraph(
            "python -m src.reports.tearsheet",
            code_style,
        )
    )

    story.append(Paragraph("Batch tearsheet generation", heading2))
    story.append(
        Paragraph(
            "python -m src.reports.batch_tearsheets",
            code_style,
        )
    )

    story.append(
        Paragraph(
            "Generated company PDFs are stored under "
            "<b>reports/tearsheets/</b>. Companies without enough annual "
            "financial history may be skipped according to the reporting "
            "eligibility rules.",
            body,
        )
    )

    story.append(
        Paragraph(
            "The platform preserves source-data limitations rather than "
            "fabricating missing financial history.",
            body,
        )
    )

    story.append(PageBreak())
    story.append(Paragraph("16. FastAPI Usage and Example curl Commands", heading1))

    story.append(
        Paragraph(
            "Start the REST API server from the project root:",
            body,
        )
    )

    story.append(
        Paragraph(
            "python -m uvicorn src.api.main:app " "--host 127.0.0.1 --port 8000",
            code_style,
        )
    )

    story.append(
        Paragraph(
            "Interactive OpenAPI documentation is available at "
            "<b>http://127.0.0.1:8000/docs</b> while the server is running.",
            body,
        )
    )

    curl_examples = [
        (
            "Health check",
            'curl "http://127.0.0.1:8000/api/v1/health"',
        ),
        (
            "List companies",
            'curl "http://127.0.0.1:8000/api/v1/companies"',
        ),
        (
            "TCS company profile",
            'curl "http://127.0.0.1:8000/api/v1/companies/TCS"',
        ),
        (
            "TCS ratios",
            'curl "http://127.0.0.1:8000/api/v1/companies/TCS/ratios"',
        ),
        (
            "Screener example",
            'curl "http://127.0.0.1:8000/api/v1/screener?' 'min_roe=15&max_de=1"',
        ),
        (
            "Sector summary",
            'curl "http://127.0.0.1:8000/api/v1/sectors"',
        ),
        (
            "Portfolio statistics",
            'curl "http://127.0.0.1:8000/api/v1/portfolio/stats"',
        ),
        (
            "TCS documents",
            'curl "http://127.0.0.1:8000/api/v1/companies/TCS/documents"',
        ),
    ]

    for title, command in curl_examples:
        story.append(Paragraph(title, heading2))
        story.append(Paragraph(command, code_style))

    story.append(PageBreak())
    story.append(Paragraph("17. Troubleshooting Common Issues", heading1))

    troubleshooting = [
        ["Issue", "Recommended action"],
        [
            "ModuleNotFoundError: src",
            "Run commands from the project root and ensure the virtual "
            "environment is active.",
        ],
        [
            "API port 8000 already in use",
            "Stop the existing API process or start uvicorn on another port.",
        ],
        [
            "Streamlit port 8501 already in use",
            "Stop the earlier Streamlit process or use another available port.",
        ],
        [
            "Database or table not found",
            "Confirm db/nifty100.db exists and ETL completed successfully.",
        ],
        [
            "Screener returns fewer companies than expected",
            "Review active filters. Exact presets may legitimately return "
            "small result sets.",
        ],
        [
            "Missing ratios or CAGR values",
            "Check source-history coverage and required calculation inputs.",
        ],
        [
            "Tearsheet not generated",
            "Verify sufficient annual financial history and reporting inputs.",
        ],
        [
            "PDF rendering problem",
            "Regenerate and visually inspect for clipping, overflow or broken charts.",
        ],
        [
            "Tests modify generated Excel outputs",
            "Restore unintended tracked workbook changes with git restore.",
        ],
        [
            "Ruff or Black reports issues",
            "Run Black, then Ruff, then rerun the full pytest suite.",
        ],
        [
            "Unexpected source counts",
            "Verify source data before changing code. Document source/spec "
            "mismatches instead of fabricating records.",
        ],
    ]

    add_table(troubleshooting, [2.0 * inch, 5.05 * inch])

    story.append(Spacer(1, 10))
    story.append(
        Paragraph(
            "<b>Disclaimer:</b> This platform is an analytical and educational "
            "tool. Outputs should be verified against source financial statements "
            "and should not be treated as investment advice.",
            body,
        )
    )


# === END DAY 44 REQUIRED USER GUIDE SECTIONS ===


if __name__ == "__main__":
    build_guide()
