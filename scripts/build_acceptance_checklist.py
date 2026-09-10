from datetime import date
from pathlib import Path

import pandas as pd
from pypdf import PdfReader
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    KeepTogether,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

ROOT = Path.cwd()
AUDIT = ROOT / "output" / "acceptance_audit.csv"
OUT = ROOT / "docs" / "acceptance_checklist.pdf"

df = pd.read_csv(AUDIT)

styles = getSampleStyleSheet()

title_style = ParagraphStyle(
    "TitleCustom",
    parent=styles["Title"],
    fontSize=19,
    leading=23,
    alignment=TA_CENTER,
    spaceAfter=10,
)

subtitle_style = ParagraphStyle(
    "Subtitle",
    parent=styles["Normal"],
    fontSize=10,
    leading=14,
    alignment=TA_CENTER,
    spaceAfter=14,
)

heading = ParagraphStyle(
    "HeadingCustom",
    parent=styles["Heading2"],
    fontSize=13,
    leading=17,
    spaceBefore=8,
    spaceAfter=8,
)

body = ParagraphStyle(
    "BodyCustom",
    parent=styles["BodyText"],
    fontSize=9,
    leading=13,
    spaceAfter=6,
)

small = ParagraphStyle(
    "SmallCustom",
    parent=styles["BodyText"],
    fontSize=7.7,
    leading=10,
)

status_style = ParagraphStyle(
    "StatusCustom",
    parent=styles["BodyText"],
    fontSize=11,
    leading=15,
    alignment=TA_CENTER,
    spaceAfter=10,
)

doc = SimpleDocTemplate(
    str(OUT),
    pagesize=A4,
    rightMargin=15 * mm,
    leftMargin=15 * mm,
    topMargin=15 * mm,
    bottomMargin=15 * mm,
)

story = []

story.append(
    Paragraph(
        "Nifty 100 Financial Intelligence Platform",
        title_style,
    )
)

story.append(
    Paragraph(
        "Sprint 6 - Day 45 Final Acceptance Checklist",
        subtitle_style,
    )
)

pass_count = int((df["Status"] == "PASS").sum())
fail_count = int((df["Status"] == "FAIL").sum())
review_count = int((df["Status"] == "REVIEW").sum())

story.append(
    Paragraph(
        f"<b>Acceptance Result:</b> "
        f"{pass_count} PASS / {fail_count} FAIL / "
        f"{review_count} REVIEW out of {len(df)} gates",
        status_style,
    )
)

story.append(
    Paragraph(
        "Final disposition: CONDITIONAL ACCEPTANCE WITH DOCUMENTED "
        "SOURCE-DATA / ELIGIBILITY EXCEPTIONS. "
        "No source values, signals, financial calculations, or report "
        "eligibility rules were fabricated or weakened to force an "
        "acceptance gate to pass.",
        body,
    )
)

story.append(Spacer(1, 4 * mm))

story.append(Paragraph("1. Acceptance Gate Summary", heading))

summary_data = [
    [
        Paragraph("<b>Gate</b>", small),
        Paragraph("<b>Status</b>", small),
        Paragraph("<b>Acceptance Requirement</b>", small),
    ]
]

for row in df.itertuples():
    summary_data.append(
        [
            Paragraph(str(row.AC), small),
            Paragraph(str(row.Status), small),
            Paragraph(str(row.Gate), small),
        ]
    )

table = Table(
    summary_data,
    colWidths=[18 * mm, 22 * mm, 135 * mm],
    repeatRows=1,
)

table.setStyle(
    TableStyle(
        [
            ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
            ("GRID", (0, 0), (-1, -1), 0.35, colors.grey),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 4),
            ("RIGHTPADDING", (0, 0), (-1, -1), 4),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]
    )
)

story.append(table)

story.append(PageBreak())

story.append(Paragraph("2. Detailed Acceptance Evidence", heading))

for row in df.itertuples():
    block = [
        Paragraph(
            f"<b>{row.AC} - {row.Status}</b>",
            body,
        ),
        Paragraph(
            f"<b>Requirement:</b> {row.Gate}",
            body,
        ),
        Paragraph(
            f"<b>Evidence:</b> {row.Evidence}",
            small,
        ),
        Spacer(1, 3 * mm),
    ]

    story.append(KeepTogether(block))

story.append(PageBreak())

story.append(Paragraph("3. Documented Exceptions", heading))

story.append(
    Paragraph(
        "<b>AC05 - Revenue CAGR cross-validation within 0.1%</b>",
        body,
    )
)

story.append(
    Paragraph(
        "Status: FAIL. The independent cross-validation identified a "
        "maximum absolute divergence of 10.2165 percentage points. "
        "The material outlier is INFY 3-year compounded sales growth: "
        "the source value is 5.0%, while the independently calculated "
        "value is 15.2165%. The discrepancy is retained as an auditable "
        "source/calculation exception rather than modifying the ratio "
        "engine or source value solely to satisfy the acceptance gate.",
        body,
    )
)

story.append(
    Paragraph(
        "<b>AC16 - All 92 companies must have at least one PRO and " "one CON</b>",
        body,
    )
)

story.append(
    Paragraph(
        "Status: FAIL. Deterministic signal generation produced PRO "
        "coverage for 89 of 92 companies and CON coverage for 57 of "
        "92 companies. The defined signal rules and thresholds were "
        "preserved. Missing signals were not fabricated for companies "
        "that did not satisfy a qualifying condition.",
        body,
    )
)

story.append(
    Paragraph(
        "<b>AC17 - All 92 tearsheets must exist and be at least " "30 KB</b>",
        body,
    )
)

story.append(
    Paragraph(
        "Status: FAIL. 88 of 92 companies satisfy the established "
        "financial-history eligibility requirement and have generated "
        "tearsheets. All 88 generated tearsheets are at least 30 KB. "
        "Four companies were intentionally skipped because they have "
        "insufficient annual financial history under the reporting "
        "eligibility rule. Empty or unsupported reports were not "
        "generated merely to reach a count of 92.",
        body,
    )
)

story.append(Spacer(1, 5 * mm))

story.append(Paragraph("4. Quality and Release Evidence", heading))

quality_data = [
    ["Metric", "Final Result"],
    ["Companies loaded", "92"],
    ["Financial ratio rows", "1,155"],
    ["Long-history coverage", "84/92 (91.30%)"],
    ["Foreign-key violations", "0"],
    ["Automated tests", "168 passed"],
    ["API health", "HTTP 200"],
    ["TCS ratio history", "13 rows"],
    ["Quality screener", "22 companies"],
    ["Peer groups", "11"],
    ["Cluster assignments", "92/92"],
    ["Generated tearsheets", "88/92 eligible"],
    ["Valid tearsheets >=30 KB", "88/88"],
    ["Analyst Guide", "18 pages"],
    ["Acceptance gates", "17 PASS / 3 FAIL / 0 REVIEW"],
]

quality_table = Table(
    quality_data,
    colWidths=[75 * mm, 95 * mm],
)

quality_table.setStyle(
    TableStyle(
        [
            ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
            ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ]
    )
)

story.append(quality_table)

story.append(Spacer(1, 8 * mm))

story.append(Paragraph("5. Final Deliverable Archive", heading))

story.append(
    Paragraph(
        "The final archive contains 23 top-level deliverables under "
        "output/final_deliverables/. This includes the API source, "
        "OpenAPI specification, Postman collection, clustering and "
        "statistical outputs, screener and valuation workbooks, "
        "financial intelligence outputs, 88 company tearsheets, "
        "11 sector reports, portfolio summary, pytest report, "
        "performance notes, and Analyst Guide.",
        body,
    )
)

story.append(Spacer(1, 8 * mm))

story.append(Paragraph("6. Team Lead Sign-off", heading))

story.append(
    Paragraph(
        "I have reviewed the acceptance evidence and documented "
        "exceptions for the Nifty 100 Financial Intelligence Platform.",
        body,
    )
)

signoff_data = [
    ["Team Lead Name", ""],
    ["Signature", ""],
    ["Date", ""],
    ["Decision", "Accept / Accept with Exceptions / Reject"],
]

signoff = Table(
    signoff_data,
    colWidths=[50 * mm, 120 * mm],
    rowHeights=[12 * mm, 18 * mm, 12 * mm, 12 * mm],
)

signoff.setStyle(
    TableStyle(
        [
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ]
    )
)

story.append(signoff)

story.append(Spacer(1, 8 * mm))

story.append(
    Paragraph(
        f"Checklist generated: {date.today().isoformat()}",
        small,
    )
)

story.append(
    Paragraph(
        "The signature fields are intentionally blank and must be "
        "completed by the authorized team lead.",
        small,
    )
)

doc.build(story)

print(f"Created: {OUT}")
print(f"Size: {OUT.stat().st_size:,} bytes")


reader = PdfReader(str(OUT))

print(f"Pages: {len(reader.pages)}")
print("Acceptance gates represented:", len(df))
print(f"Summary: {pass_count} PASS / " f"{fail_count} FAIL / {review_count} REVIEW")

print()
print("FINAL ACCEPTANCE CHECKLIST: CREATED")
