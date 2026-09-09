# Sprint 3 Retrospective

## Sprint

Sprint 3 — Screener & Peer Comparison Engine

## Completed

- Day 15: Config-driven screener engine
- Day 16: Six screener presets
- Day 17: Composite Quality Score
- Day 17: P10/P90 winsorization
- Day 17: Sector-relative scoring
- Day 17: screener_output.xlsx
- Day 18: Peer percentile engine
- Day 18: 11 peer groups
- Day 18: 10 peer metrics
- Day 18: peer_percentiles SQLite table
- Day 19: Radar chart generation
- Day 19: 56 peer radar charts
- Day 19: 36 standalone charts
- Day 19: 92 total charts
- Day 20: peer_comparison.xlsx
- Day 20: Exactly 11 peer sheets
- Day 20: Benchmark row highlighting
- Day 20: Median summary rows
- Day 20: Percentile conditional formatting
- Day 21: Final validation

## Screener Presets

- Quality Compounder: 22 companies
- Value Pick: 2 companies
- Growth Accelerator: 19 companies
- Dividend Champion: 30 companies
- Debt-Free Blue Chip: 2 companies
- Turnaround Watch: 31 companies

## Preset Dataset Exceptions

The Sprint brief targeted 5–50 companies per preset.

Two presets return fewer than 5 companies under the fixed official thresholds:

- Value Pick: 2
- Debt-Free Blue Chip: 2

The thresholds were not weakened to artificially satisfy the target range.

## Peer Engine

- Peer groups: 11
- Peer companies: 56
- Metrics per company: 10
- peer_percentiles rows: 560
- Percentile scale: 0–100
- Debt/Equity ranking: inverse
- SQL-style PERCENT_RANK semantics used

## Day 17 Scoring

Composite Quality Score uses:

- ROE: 15%
- ROCE: 10%
- Net Profit Margin: 10%
- FCF CAGR: 15%
- CFO/PAT: 10%
- Positive FCF: 5%
- Revenue CAGR: 10%
- PAT CAGR: 10%
- Debt/Equity: 10%
- Interest Coverage: 5%

Total weight: 100%

P10/P90 winsorization is applied before scaling continuous metrics.

## Data Quality Notes

Source-scale anomalies were observed in some companies such as BEL, HAL and INDIGO.

The ROE and ROCE formulas are mathematically consistent with the database inputs, so raw source values were preserved.

Winsorization is used to prevent extreme source values from dominating the quality score.

The sectors dataset contains 23 Financials companies, although the Sprint brief referenced 19. The sectors table is treated as the operational source of truth.

## Outputs

- output/screener_output.xlsx
- output/peer_comparison.xlsx
- reports/radar_charts/
- db/nifty100.db peer_percentiles table

## Sprint 3 Status

COMPLETE
