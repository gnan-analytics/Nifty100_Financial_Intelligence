# Sprint 5 Retrospective

## What Went Well
- Existing Sprint 2 analytics modules were extended instead of being overwritten.
- NLP parsing and rule generation preserved exact source thresholds.
- All 24 pros/cons rules were implemented and exercised.
- Cash flow intelligence covers all 92 company master records.
- Missing source data was represented explicitly rather than fabricated.
- ReportLab tearsheets were tested incrementally before full batch generation.
- PDF page counts, file sizes, rendering, and visual layout were validated.
- All 88 eligible company tearsheets generated without failures.
- The 11-report sector requirement was resolved using source-defined peer groups.
- Portfolio summary includes all 92 companies and documents the SIEMENS fallback.

## Challenges
- Day 30 strict 92/92 PRO and CON coverage conflicts with the actual source data and supplied thresholds.
- ATGL lacks cash flow / balance-sheet history required for some intelligence metrics.
- Four companies have fewer than 3 March annual P&L years.
- The source has 10 broad sectors while the sprint brief asks for 11 sector reports.
- SIEMENS uses September fiscal-year data instead of March annual rows.
- PowerShell source-file encoding required explicit UTF-8 handling.

## Decisions
- Preserve exact rule thresholds rather than weaken them for artificial coverage.
- Do not fabricate missing financial history.
- Use explicit Data Unavailable labels where source data is absent.
- Use 11 source-defined peer groups for the 11 report requirement.
- Use 2024-09 as the documented SIEMENS portfolio fallback.
- Keep company tearsheet generation restricted to companies with at least 3 annual P&L years.

## Technical Debt / Follow-Up
- Consider formal product-owner approval for fallback PRO / CON messaging if 92/92 coverage is mandatory.
- Clarify whether future sector reports should use broad sectors or peer groups.
- Consider adding automated visual-layout regression checks for PDFs.
- Verify all runtime dependencies are declared in project requirements before deployment.
- Consider adding true cumulative cash-flow waterfall rendering if stricter waterfall semantics are required.

## Sprint 5 Outcome
The intelligence and reporting layer is operational with source-data exceptions documented explicitly and without synthetic financial signals or history.
