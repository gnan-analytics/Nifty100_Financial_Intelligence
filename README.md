# Nifty 100 Financial Intelligence Platform

A full-stack financial analytics platform for the Nifty 100 universe built with Python, SQLite, Pandas, Streamlit, FastAPI, scikit-learn, Plotly, ReportLab, and automated testing.

## Project Status

- Sprint 1 - Data Foundation: Complete
- Sprint 2 - Financial Ratio Engine: Complete
- Sprint 3 - Screener and Peer Comparison: Complete
- Sprint 4 - Dashboard and Valuation: Complete
- Sprint 5 - Intelligence, NLP and PDF Reporting: Complete
- Sprint 6 - Clustering, API, QA and Final Delivery: In Progress

## Platform Coverage

- 92 companies
- 12 SQLite tables
- 1,155 financial ratio records
- 10 broad sectors
- 11 peer groups
- 5 KMeans company archetypes
- 16 FastAPI endpoints
- 8 Streamlit dashboard screens
- 168 automated tests

## Dashboard

Run:

    python -m streamlit run src\dashboard\app.py

Open `http://localhost:8501`.

## FastAPI

Run:

    python -m uvicorn src.api.main:app --host 127.0.0.1 --port 8000 --reload

Documentation:

- Swagger: `http://127.0.0.1:8000/docs`
- ReDoc: `http://127.0.0.1:8000/redoc`
- Health: `http://127.0.0.1:8000/api/v1/health`

API exports are available in `docs/`.

## Screener

Validated preset counts:

- Quality Compounder: 22
- Value Pick: 2
- Growth Accelerator: 19
- Dividend Champion: 30
- Debt-Free Blue Chip: 2
- Turnaround Watch: 31

## Clustering

Run:

    python -m src.analytics.clustering

Five company archetypes are generated using ROE, Debt-to-Equity, Revenue CAGR 5Y, FCF CAGR 5Y, and Operating Profit Margin.

Outputs include:

- `output/cluster_labels.csv`
- `output/cluster_imputation_audit.csv`
- `reports/elbow_plot.png`
- `reports/correlation_heatmap.png`
- `output/outlier_report.csv`
- `output/portfolio_stats.csv`

## Financial Intelligence and Reports

The platform includes rule-based PRO/CON signals, cash-flow intelligence, capital-allocation analysis, company tear sheets, peer-group reports, and a portfolio summary.

Missing financial intelligence is reported as unavailable rather than fabricated.

## Testing

Run:

    pytest -q

Current verified result:

    168 passed

## Code Quality

Run:

    python -m black --check src tests
    python -m ruff check src tests

Current status:

- Black: clean
- Ruff: clean
- Pytest: 168 passed

## Performance

Sprint 6 performance testing confirms screener requests complete within the 10-second target and company-profile requests within the 3-second target.

See `output/perf_notes.md`.

## Source-Truth Policy

The project preserves source truth. Known constraints include 10 broad sectors versus 11 peer groups, source-level ROE/ROCE outliers, incomplete PRO/CON coverage for some companies, and insufficient history for some tear sheets.

## Disclaimer

This project is for educational, analytical, and portfolio-development purposes only. It is not investment advice.

## Sprint 6 Final Release

Sprint 6 is complete with the clustering, statistical profiling, FastAPI
service, API test suite, performance validation, Analyst Guide, final
deliverable archive, and Day 45 acceptance package.

Final release metrics:

- 92 Nifty 100 companies
- 1,155 financial-ratio rows
- 5 KMeans company archetypes
- 16 `/api/v1` endpoints
- 8 Streamlit dashboard screens
- 11 peer groups
- 88 eligible company tearsheets
- 11 peer-group reports
- 168 automated tests passing
- Black and Ruff checks passing
- 18-page Analyst Guide
- 23-item final deliverable archive
- Day 45 acceptance: 17 PASS, 3 documented exceptions, 0 REVIEW

### Documented Acceptance Exceptions

**AC05 - Revenue CAGR cross-validation**

The independent validation identified a maximum divergence of 10.2165
percentage points. The material case is INFY 3-year compounded sales
growth: source value 5.0% versus independently calculated 15.2165%.
The source value and calculation evidence are retained without manipulation.

**AC16 - PRO / CON coverage**

The deterministic 24-signal framework produces PRO coverage for 89 of
92 companies and CON coverage for 57 of 92 companies. Signals are not
fabricated for companies that do not satisfy the defined rules.

**AC17 - Company tearsheet coverage**

88 of 92 companies meet the established annual-history eligibility rule
and have generated tearsheets. All 88 generated tearsheets are at least
30 KB. Four companies with insufficient annual history are intentionally
excluded rather than generating unsupported reports.

The detailed evidence and team-lead sign-off section are available in
`docs/acceptance_checklist.pdf`.
