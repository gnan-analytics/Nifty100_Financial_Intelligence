# Nifty 100 Financial Intelligence Platform



A financial analytics platform for the Nifty 100 universe built with Python, SQLite, Pandas, Streamlit, Plotly, and automated testing.



## Project Status



- Sprint 1 - Data Foundation: Complete

- Sprint 2 - Financial Ratio Engine: Complete

- Sprint 3 - Screener & Peer Comparison: Complete

- Sprint 4 - Dashboard & Valuation Module: Complete



## Dashboard



The Streamlit dashboard contains eight screens:



1. Home

2. Company Profile

3. Screener

4. Peer Comparison

5. Trend Analysis

6. Sector Analysis

7. Capital Allocation

8. Annual Reports



## Run the Dashboard



Activate the virtual environment:



.\\.venv\\Scripts\\Activate.ps1



Start Streamlit:



python -m streamlit run src\\dashboard\\app.py



Open:



http://localhost:8501



## Screener



Preset strategies:



- Quality Compounder

- Value Pick

- Growth Accelerator

- Dividend Champion

- Debt-Free Blue Chip

- Turnaround Watch



Current preset counts:



- Quality Compounder: 22

- Value Pick: 2

- Growth Accelerator: 19

- Dividend Champion: 30

- Debt-Free Blue Chip: 2

- Turnaround Watch: 31



## Valuation Module



Run:



python -m src.analytics.valuation



Outputs:



- output/valuation\_summary.xlsx

- output/valuation\_flags.csv



## Peer Analytics



- 11 peer groups

- 56 peer memberships

- 10 ranking metrics

- 560 percentile records



## Capital Allocation



The source covers 91 companies.



ATGL has no source classification and is shown as:



Data Unavailable



## Testing



Run all tests:



python -m pytest -q



Run dashboard QA:



python -m src.dashboard.day27\_qa



Compile source:



python -m compileall -q src



## Disclaimer



This project is for educational financial analytics purposes and is not financial advice.



