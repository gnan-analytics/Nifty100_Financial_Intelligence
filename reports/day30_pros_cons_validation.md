# Day 30 ? Auto Pros/Cons Validation

## Rule Engine

- Defined rules: 24 (12 PRO + 12 CON)
- Rules producing signals: 24/24
- Generated signals: 506
- PRO signals: 398
- CON signals: 108
- Minimum confidence: 65.1%
- Maximum confidence: 100.0%
- Signals with confidence <= 60%: 0

## Coverage

- Companies represented: 92
- Companies with >=1 PRO: 89/92
- Companies with >=1 CON: 57/92

### Companies without a qualifying PRO

BHEL, GODREJCP, JINDALSTEL

### Companies without a qualifying CON

ABB, ADANIPORTS, ADANIPOWER, AMBUJACEM, APOLLOHOSP, ATGL, BEL, BOSCHLTD, BPCL, BRITANNIA, DMART, DRREDDY, HAVELLS, HDFCLIFE, HINDALCO, ICICIPRULI, IOC, ITC, JSWSTEEL, LICI, M&M, MARUTI, MOTHERSON, NESTLEIND, ONGC, PIDILITIND, PNB, SHREECEM, SIEMENS, SUNPHARMA, TATAMOTORS, TATAPOWER, TCS, TORNTPHARM, TRENT

## Rule Counts

- CON_01: 4
- CON_02: 6
- CON_03: 19
- CON_04: 2
- CON_05: 1
- CON_06: 7
- CON_07: 1
- CON_08: 19
- CON_09: 4
- CON_10: 21
- CON_11: 17
- CON_12: 7
- PRO_01: 20
- PRO_02: 30
- PRO_03: 3
- PRO_04: 31
- PRO_05: 46
- PRO_06: 36
- PRO_07: 50
- PRO_08: 33
- PRO_09: 39
- PRO_10: 31
- PRO_11: 59
- PRO_12: 20

## Validation Note

All 24 specified financial rules are implemented and produce signals.
The dataset does not naturally produce at least one qualifying PRO and one qualifying CON for every company under the specified thresholds.
Thresholds were not weakened and unsupported financial statements were not fabricated solely to force 92/92 coverage.
