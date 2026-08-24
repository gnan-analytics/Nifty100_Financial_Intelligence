-- =========================================================
-- NIFTY 100 FINANCIAL INTELLIGENCE PLATFORM
-- SPRINT 1 - EXPLORATORY QUERIES
-- =========================================================


-- 1. Total companies
SELECT COUNT(*) AS company_count
FROM companies;


-- 2. Row counts for major financial tables
SELECT
    'profitandloss' AS table_name,
    COUNT(*) AS row_count
FROM profitandloss

UNION ALL

SELECT
    'balancesheet',
    COUNT(*)
FROM balancesheet

UNION ALL

SELECT
    'cashflow',
    COUNT(*)
FROM cashflow

UNION ALL

SELECT
    'stock_prices',
    COUNT(*)
FROM stock_prices

UNION ALL

SELECT
    'financial_ratios',
    COUNT(*)
FROM financial_ratios;


-- 3. Foreign key integrity check
PRAGMA foreign_key_check;


-- 4. P&L year coverage per company
SELECT
    company_id,
    COUNT(DISTINCT year) AS years_available,
    MIN(year) AS earliest_year,
    MAX(year) AS latest_year
FROM profitandloss
GROUP BY company_id
ORDER BY years_available DESC;


-- 5. Balance Sheet year coverage per company
SELECT
    company_id,
    COUNT(DISTINCT year) AS years_available,
    MIN(year) AS earliest_year,
    MAX(year) AS latest_year
FROM balancesheet
GROUP BY company_id
ORDER BY years_available DESC;


-- 6. Cash Flow year coverage per company
SELECT
    company_id,
    COUNT(DISTINCT year) AS years_available,
    MIN(year) AS earliest_year,
    MAX(year) AS latest_year
FROM cashflow
GROUP BY company_id
ORDER BY years_available DESC;


-- 7. Companies with less than 5 years of P&L history
SELECT
    c.id AS company_id,
    c.company_name,
    COUNT(DISTINCT p.year) AS pnl_years
FROM companies c
LEFT JOIN profitandloss p
    ON c.id = p.company_id
GROUP BY
    c.id,
    c.company_name
HAVING COUNT(DISTINCT p.year) < 5
ORDER BY pnl_years ASC;


-- 8. Companies with less than 5 years of Balance Sheet history
SELECT
    c.id AS company_id,
    c.company_name,
    COUNT(DISTINCT b.year) AS bs_years
FROM companies c
LEFT JOIN balancesheet b
    ON c.id = b.company_id
GROUP BY
    c.id,
    c.company_name
HAVING COUNT(DISTINCT b.year) < 5
ORDER BY bs_years ASC;


-- 9. Companies with less than 5 years of Cash Flow history
SELECT
    c.id AS company_id,
    c.company_name,
    COUNT(DISTINCT cf.year) AS cashflow_years
FROM companies c
LEFT JOIN cashflow cf
    ON c.id = cf.company_id
GROUP BY
    c.id,
    c.company_name
HAVING COUNT(DISTINCT cf.year) < 5
ORDER BY cashflow_years ASC;


-- 10. Null check in key P&L fields
SELECT
    COUNT(*) AS total_rows,
    SUM(CASE WHEN sales IS NULL THEN 1 ELSE 0 END) AS null_sales,
    SUM(
        CASE
            WHEN operating_profit IS NULL THEN 1
            ELSE 0
        END
    ) AS null_operating_profit,
    SUM(
        CASE
            WHEN net_profit IS NULL THEN 1
            ELSE 0
        END
    ) AS null_net_profit,
    SUM(CASE WHEN eps IS NULL THEN 1 ELSE 0 END) AS null_eps
FROM profitandloss;


-- 11. Null check in Balance Sheet
SELECT
    COUNT(*) AS total_rows,
    SUM(
        CASE
            WHEN total_assets IS NULL THEN 1
            ELSE 0
        END
    ) AS null_total_assets,
    SUM(
        CASE
            WHEN total_liabilities IS NULL THEN 1
            ELSE 0
        END
    ) AS null_total_liabilities,
    SUM(
        CASE
            WHEN fixed_assets IS NULL THEN 1
            ELSE 0
        END
    ) AS null_fixed_assets
FROM balancesheet;


-- 12. Strict Balance Sheet equality check
SELECT
    COUNT(*) AS mismatched_rows
FROM balancesheet
WHERE total_assets <> total_liabilities;


-- 13. P&L duplicate company-year check
SELECT
    company_id,
    year,
    COUNT(*) AS duplicate_count
FROM profitandloss
GROUP BY
    company_id,
    year
HAVING COUNT(*) > 1;


-- 14. Balance Sheet duplicate company-year check
SELECT
    company_id,
    year,
    COUNT(*) AS duplicate_count
FROM balancesheet
GROUP BY
    company_id,
    year
HAVING COUNT(*) > 1;


-- 15. Cash Flow duplicate company-year check
SELECT
    company_id,
    year,
    COUNT(*) AS duplicate_count
FROM cashflow
GROUP BY
    company_id,
    year
HAVING COUNT(*) > 1;


-- 16. Sector distribution
SELECT
    broad_sector,
    COUNT(*) AS company_count
FROM sectors
GROUP BY broad_sector
ORDER BY company_count DESC;


-- 17. Latest P&L year available for every company
SELECT
    company_id,
    MAX(year) AS latest_year
FROM profitandloss
GROUP BY company_id
ORDER BY company_id;


-- 18. Companies with zero or negative sales
SELECT
    company_id,
    year,
    sales
FROM profitandloss
WHERE sales <= 0
ORDER BY company_id, year;


-- 19. Cash flow reconciliation check
SELECT
    company_id,
    year,
    net_cash_flow,
    operating_activity
        + investing_activity
        + financing_activity AS calculated_net_cash,
    ABS(
        net_cash_flow
        - (
            operating_activity
            + investing_activity
            + financing_activity
        )
    ) AS difference
FROM cashflow
WHERE ABS(
    net_cash_flow
    - (
        operating_activity
        + investing_activity
        + financing_activity
    )
) > 10
ORDER BY difference DESC;


-- 20. Overall time-series coverage summary
SELECT
    c.id AS company_id,
    c.company_name,

    COUNT(DISTINCT p.year) AS pnl_years,
    COUNT(DISTINCT b.year) AS bs_years,
    COUNT(DISTINCT cf.year) AS cf_years

FROM companies c

LEFT JOIN profitandloss p
    ON c.id = p.company_id

LEFT JOIN balancesheet b
    ON c.id = b.company_id

LEFT JOIN cashflow cf
    ON c.id = cf.company_id

GROUP BY
    c.id,
    c.company_name

ORDER BY
    pnl_years ASC,
    bs_years ASC,
    cf_years ASC;