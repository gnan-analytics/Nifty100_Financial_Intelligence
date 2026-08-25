**# Sprint 2 Retrospective — Financial Ratio Engine**



**## Sprint Goal**



**Build and validate a financial ratio engine capable of computing profitability,**

**leverage, efficiency, growth and cash-flow KPIs across all available company-year**

**records in the Nifty 100 dataset.**



**## Completed**



**- Implemented Net Profit Margin**

**- Implemented Operating Profit Margin**

**- Implemented OPM source cross-check**

**- Implemented ROE**

**- Implemented ROCE**

**- Implemented ROA**

**- Implemented Financials sector ROCE carve-out**



**- Implemented Debt-to-Equity**

**- Implemented high leverage flag**

**- Implemented Interest Coverage Ratio**

**- Implemented Debt Free ICR label**

**- Implemented ICR warning flag**

**- Implemented Net Debt**

**- Implemented Asset Turnover**



**- Implemented CAGR engine**

**- Revenue CAGR 3Y, 5Y and 10Y**

**- PAT CAGR 3Y, 5Y and 10Y**

**- EPS CAGR 3Y, 5Y and 10Y**



**## CAGR Edge Cases**



**Handled:**

**- NORMAL**

**- DECLINE\_TO\_LOSS**

**- TURNAROUND**

**- BOTH\_NEGATIVE**

**- ZERO\_BASE**

**- INSUFFICIENT**



**## Cash Flow KPIs**



**Implemented:**

**- Free Cash Flow**

**- CFO/PAT Ratio**

**- CFO Quality Score**

**- CapEx Intensity**

**- FCF Conversion Rate**

**- Capital Allocation Classifier**



**## Capital Allocation Patterns**



**Implemented:**

**- Reinvestor**

**- Shareholder Returns**

**- Liquidating Assets**

**- Distress Signal**

**- Growth Funded by Debt**

**- Cash Accumulator**

**- Pre-Revenue**

**- Mixed**



**## Database Population**



**financial\_ratios rows: 1155**



**Sprint requirement:**

**>= 1100 rows**



**Status:**

**PASS**



**All required KPI columns contain data.**

**No required KPI column is completely NULL.**



**## Automated Testing**



**Total tests passed:**



**86**



**Status:**



**PASS — 0 failures**



**## Screener Preview**



**Filter:**



**ROE > 15%**

**Debt-to-Equity < 1**



**Result count:**



**38 companies**



**Expected range:**



**15 to 50**



**Status:**



**PASS**



**## Ratio Edge Case Review**



**Companies reviewed:**



**92**



**ROE anomalies above 5 percentage points:**



**1**



**ROCE anomalies above 5 percentage points:**



**1**



**All anomalies were documented in:**



**output/ratio\_edge\_cases.log**



**Categories used:**



**- data source issue**

**- version difference**

**- formula discrepancy**



**Computed Ratio Engine values are used for analytics.**

**Source company-level ROE and ROCE values are retained for display and cross-check.**



**## Financials Carve-Out**



**Actual Financials companies in sectors table:**



**23**



**Sprint brief expected:**



**19**



**Resolution:**



**The SQLite sectors table is used as the operational source of truth.**

**The difference is documented as a dataset mapping/version discrepancy.**



**High Debt-to-Equity warnings are suppressed for Financials because structurally**

**high leverage is normal for banks, NBFCs, insurance companies and financial institutions.**



**ROCE for Financials is interpreted using sector-relative benchmarking rather than**

**a standard absolute threshold.**



**## Key Deliverables**



**- src/analytics/ratios.py**

**- src/analytics/cagr.py**

**- src/analytics/cashflow\_kpis.py**

**- src/analytics/populate\_financial\_ratios.py**

**- src/analytics/ratio\_edge\_cases.py**

**- output/capital\_allocation.csv**

**- output/ratio\_edge\_cases.log**

**- financial\_ratios SQLite table**

**- tests/kpi/**



**## Sprint 2 Definition of Done**



**financial\_ratios >= 1100 rows: PASS**



**14+ KPI columns populated: PASS**



**20+ KPI tests pass: PASS**



**Ratio edge cases documented: PASS**



**Capital allocation generated: PASS**



**Screener preview result within expected range: PASS**



**ROE/ROCE anomaly review complete: PASS**



**Sprint 2 Status:**



**COMPLETE**

