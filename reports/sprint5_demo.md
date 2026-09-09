# Sprint 5 Demo - Intelligence, NLP & PDF Reports

## Sprint Goal
Build NLP-driven financial intelligence, cash flow intelligence, company tearsheets, sector reports, and a complete portfolio summary PDF.

## Completed Deliverables

### Day 29 - NLP Parser
- Parsed analysis.xlsx growth and ROE fields.
- Generated:
  - output/analysis_parsed.csv
  - output/parse_failures.csv
  - output/cagr_cross_validation.csv
- Parsed 65 metric values.
- 15 expected parsing failures were TTM / Last Year text formats.
- CAGR cross-validation identified one >5 percentage-point divergence:
  - INFY 3Y Revenue CAGR
- Day 29 validation passed.

### Day 30 - Pros / Cons Rule Engine
- Implemented all 24 specified rules:
  - 12 PRO rules
  - 12 CON rules
- Generated:
  - output/pros_cons_generated.csv
  - output/pros_cons_coverage_gaps.csv
- 506 signals generated:
  - 398 PRO
  - 108 CON
- Confidence threshold enforced above 60%.
- No duplicate company/type/rule signals.
- All 24 rules produced at least one signal.
- Dataset coverage:
  - Companies with at least one PRO: 89 / 92
  - Companies with at least one CON: 57 / 92
- Exact rule thresholds were preserved.
- Unsupported fallback statements were not fabricated.
- Rule 11 was implemented using PAT CAGR > Revenue CAGR to match the supplied operating-leverage explanation.

### Day 31 - Cash Flow Intelligence
- Extended existing cash flow analytics without overwriting prior Sprint 2 logic.
- Generated:
  - output/cashflow_intelligence.xlsx
  - output/distress_alerts.csv
- 92 company rows generated.
- CFO Quality:
  - High Quality: 62
  - Moderate: 12
  - Accrual Risk: 17
  - Data Unavailable: 1
- CapEx Profile:
  - Asset Light: 21
  - Moderate: 24
  - Capital Intensive: 46
  - Data Unavailable: 1
- Distress flags: 13
- Deleveraging flags: 26
- ATGL correctly marked Data Unavailable where source cash flow / balance data is missing.
- Day 31 validation passed.

### Day 32 - Capital Allocation Intelligence
- Validated 1,056 capital allocation rows.
- 91 companies have historical capital-allocation data.
- ATGL has no source allocation history.
- All 8 defined patterns appear historically.
- Latest reporting distribution contains 7 allocation patterns plus Data Unavailable.
- Generated:
  - output/capital_allocation_distribution.csv
  - output/pattern_changes.csv
- Historical pattern changes detected: 529
- Day 32 validation passed.

### Day 33 - Company Tearsheet Prototype
- Built src/reports/tearsheet.py using ReportLab.
- Two-page company tearsheet includes:
  - Navy company header
  - 6 KPI tiles
  - Revenue / Net Profit chart
  - ROE / ROCE chart
  - Balance-sheet funding chart
  - Cash-flow chart
  - Pros / Cons
  - Capital-allocation intelligence
- Prototype companies:
  - TCS
  - HDFCBANK
  - RELIANCE
  - SUNPHARMA
  - TATASTEEL
- All 5 PDFs:
  - exactly 2 pages
  - above 30 KB
  - visually inspected
  - no clipping or overflow
- Day 33 passed.

### Day 34 - Batch Company and Sector Reports
- Company master: 92
- Eligible company tearsheets with >=3 annual P&L years: 88
- Generated company tearsheets: 88
- Failures: 0
- Skipped due to insufficient annual source history:
  - AMBUJACEM
  - JIOFIN
  - NESTLEIND
  - SIEMENS
- Generated:
  - output/skipped_tearsheets.csv
- All 88 generated tearsheets:
  - exactly 2 pages
  - >=30 KB
- Sector source contains 10 broad sectors.
- Peer-group source contains exactly 11 reporting groups.
- Used the 11 peer groups as the Sprint 5 sector-report groups rather than fabricating an 11th broad sector.
- Generated 11 sector reports:
  - Automobiles
  - Consumer Finance
  - FMCG
  - IT Services
  - Life Insurance
  - Oil & Gas
  - Pharmaceuticals
  - Power & Utilities
  - Private Banks
  - Public Sector Banks
  - Steel
- Visual QA passed for representative sector reports.

### Day 35 - Portfolio Summary
- Generated:
  - reports/portfolio/portfolio_summary.pdf
  - output/portfolio_ratio_fallbacks.csv
- Companies included: 92
- Pages: 92
- One company per page.
- Companies ordered alphabetically by ticker.
- Six KPIs per company:
  - ROE
  - ROCE
  - Debt / Equity
  - Operating Margin
  - Revenue CAGR 5Y
  - PAT CAGR 5Y
- Trend logic:
  - > +2 percentage points = UP
  - < -2 percentage points = DOWN
  - within +/-2 percentage points = FLAT
- March annual ratio rows used wherever available.
- SIEMENS is the only fallback:
  - latest available period 2024-09
- Visual QA passed.

## Sprint 5 Source-Data Exceptions

### Pros / Cons Coverage
The source dataset does not naturally satisfy the exact 24-rule thresholds for at least one PRO and one CON for every company.

Actual coverage:
- PRO: 89 / 92
- CON: 57 / 92

No thresholds were weakened and no unsupported signals were invented.

### Company Tearsheet Coverage
The sprint specification requests 92 tearsheets but also requires companies with fewer than 3 annual years to be skipped.

Actual source coverage:
- 88 eligible
- 4 skipped

The four skipped companies are recorded in output/skipped_tearsheets.csv.

### Sector Report Count
The source contains:
- 10 broad sectors
- 11 peer groups

The required 11 reports were generated using the 11 source-defined peer groups.

## Sprint 5 Status
Sprint 5 implementation complete, subject to final regression tests and repository commit.
