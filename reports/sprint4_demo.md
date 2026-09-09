**# Sprint 4 Demo Guide**



**## Start Dashboard**



**Run:**



**python -m streamlit run src\\dashboard\\app.py**



**Open:**



**http://localhost:8501**



**## Demo Flow**



**### 1. Home**



**Show:**



**- Year selector**

**- Six KPIs**

**- Sector distribution**

**- Top composite score companies**



**### 2. Company Profile**



**Search for TCS.**



**Show:**



**- Company information**

**- ROE**

**- ROCE**

**- NPM**

**- D/E**

**- Revenue CAGR**

**- FCF**

**- Revenue and profit history**



**### 3. Screener**



**Show:**



**- Quality Compounder preset**

**- Custom filters**

**- CSV download**



**### 4. Peer Comparison**



**Select a peer group.**



**Show:**



**- Radar chart**

**- Peer average**

**- Percentile table**

**- Benchmark company**



**### 5. Trend Analysis**



**Select a company and up to three metrics.**



**Show:**



**- Historical trend**

**- YoY changes**



**### 6. Sector Analysis**



**Show:**



**- Sector selector**

**- Revenue vs ROE bubble chart**

**- Market-cap sizing**



**### 7. Capital Allocation**



**Show:**



**- Pattern distribution**

**- Treemap**

**- Company history**

**- ATGL Data Unavailable handling**



**### 8. Annual Reports**



**Show:**



**- Company search**

**- Available report years**

**- Working PDF link**

**- Unavailable / 404 handling**



**## Valuation**



**Run:**



**python -m src.analytics.valuation**



**Show:**



**- output/valuation\_summary.xlsx**

**- output/valuation\_flags.csv**



**## QA**



**Run:**



**python -m src.dashboard.day27\_qa**



**Then:**



**python -m pytest -q**



**Expected:**



**DAY 27 DASHBOARD QA: PASS**



**118 passed**

