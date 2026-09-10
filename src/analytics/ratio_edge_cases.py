import sqlite3
from pathlib import Path

import pandas as pd

DB_PATH = Path("db/nifty100.db")
OUTPUT_PATH = Path("output/ratio_edge_cases.log")


def load_latest_ratio_rows(conn):
    """
    Load the latest available ratio row
    for each company.
    """

    query = """
    SELECT
        r.company_id,
        r.year,
        r.return_on_equity_pct,
        r.return_on_capital_employed_pct,
        r.debt_to_equity,
        c.company_name,
        c.roe_percentage AS source_roe_percentage,
        c.roce_percentage AS source_roce_percentage,
        s.broad_sector
    FROM financial_ratios r

    JOIN companies c
        ON r.company_id = c.id

    LEFT JOIN sectors s
        ON r.company_id = s.company_id

    JOIN (
        SELECT
            company_id,
            MAX(year) AS latest_year
        FROM financial_ratios
        GROUP BY company_id
    ) latest
        ON r.company_id = latest.company_id
       AND r.year = latest.latest_year

    ORDER BY r.company_id
    """

    return pd.read_sql_query(
        query,
        conn,
    )


def is_financial_sector(
    broad_sector,
):
    """Return whether financial sector."""
    if pd.isna(broad_sector):
        return False

    return str(broad_sector).strip().lower() == "financials"


def classify_difference(
    metric,
    source_value,
    computed_value,
    broad_sector,
):
    """
    Categorise the anomaly as:
        - data source issue
        - version difference
        - formula discrepancy
    """

    if (
        source_value is None
        or computed_value is None
        or pd.isna(source_value)
        or pd.isna(computed_value)
    ):
        return "data source issue"

    difference = abs(float(source_value) - float(computed_value))

    if metric == "ROCE" and is_financial_sector(broad_sector):
        return "formula discrepancy"

    if difference > 20:
        return "data source issue"

    return "version difference"


def analyze_edge_cases():
    """
    Compare latest computed ROE and ROCE
    with source values from companies table.

    Log:
        - ROE difference > 5 percentage points
        - ROCE difference > 5 percentage points
        - Financials sector carve-out notes
        - D/E suppression notes for Financials
    """

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with sqlite3.connect(DB_PATH) as conn:

        df = load_latest_ratio_rows(conn)

    log_lines = []

    log_lines.append("=" * 80)

    log_lines.append("NIFTY 100 FINANCIAL INTELLIGENCE PLATFORM")

    log_lines.append("SPRINT 2 — RATIO EDGE CASE LOG")

    log_lines.append("=" * 80)

    log_lines.append("")

    roe_anomaly_count = 0
    roce_anomaly_count = 0
    financial_count = 0

    for _, row in df.iterrows():

        company_id = row["company_id"]

        company_name = row["company_name"]

        year = row["year"]

        broad_sector = row["broad_sector"]

        computed_roe = row["return_on_equity_pct"]

        computed_roce = row["return_on_capital_employed_pct"]

        source_roe = row["source_roe_percentage"]

        source_roce = row["source_roce_percentage"]

        debt_to_equity = row["debt_to_equity"]

        # =================================================
        # FINANCIALS CARVE-OUT
        # =================================================

        if is_financial_sector(broad_sector):
            financial_count += 1

            log_lines.append(
                f"[FINANCIALS CARVE-OUT] "
                f"{company_id} | "
                f"{company_name} | "
                f"{year}"
            )

            log_lines.append(f"  Broad Sector: " f"{broad_sector}")

            log_lines.append(f"  Debt-to-Equity: " f"{debt_to_equity}")

            log_lines.append("  Decision: Standard high " "D/E warning suppressed.")

            log_lines.append("  ROCE benchmark: " "sector-relative.")

            log_lines.append("")

        # =================================================
        # ROE CROSS-CHECK
        # =================================================

        if pd.notna(computed_roe) and pd.notna(source_roe):

            roe_difference = abs(float(computed_roe) - float(source_roe))

            if roe_difference > 5:

                roe_anomaly_count += 1

                category = classify_difference(
                    metric="ROE",
                    source_value=source_roe,
                    computed_value=computed_roe,
                    broad_sector=broad_sector,
                )

                log_lines.append(
                    f"[ROE ANOMALY] " f"{company_id} | " f"{company_name} | " f"{year}"
                )

                log_lines.append(f"  Source ROE: " f"{float(source_roe):.2f}%")

                log_lines.append(f"  Computed ROE: " f"{float(computed_roe):.2f}%")

                log_lines.append(f"  Difference: " f"{roe_difference:.2f} pp")

                log_lines.append(f"  Category: " f"{category}")

                log_lines.append(
                    "  Decision: Ratio-engine "
                    "ROE used for analytics; "
                    "source retained for display."
                )

                log_lines.append("")

        # =================================================
        # ROCE CROSS-CHECK
        # =================================================

        if pd.notna(computed_roce) and pd.notna(source_roce):

            roce_difference = abs(float(computed_roce) - float(source_roce))

            if roce_difference > 5:

                roce_anomaly_count += 1

                category = classify_difference(
                    metric="ROCE",
                    source_value=source_roce,
                    computed_value=computed_roce,
                    broad_sector=broad_sector,
                )

                log_lines.append(
                    f"[ROCE ANOMALY] " f"{company_id} | " f"{company_name} | " f"{year}"
                )

                log_lines.append(f"  Source ROCE: " f"{float(source_roce):.2f}%")

                log_lines.append(f"  Computed ROCE: " f"{float(computed_roce):.2f}%")

                log_lines.append(f"  Difference: " f"{roce_difference:.2f} pp")

                log_lines.append(f"  Category: " f"{category}")

                if is_financial_sector(broad_sector):

                    log_lines.append(
                        "  Decision: Standard "
                        "absolute ROCE threshold "
                        "not used for Financials."
                    )

                else:

                    log_lines.append(
                        "  Decision: Review source " "version and formula inputs."
                    )

                log_lines.append("")

    # =====================================================
    # SUMMARY
    # =====================================================

    log_lines.append("=" * 80)

    log_lines.append("SUMMARY")

    log_lines.append("=" * 80)

    log_lines.append(f"Companies reviewed: " f"{len(df)}")

    log_lines.append(f"Financials carve-out rows: " f"{financial_count}")

    log_lines.append(f"ROE anomalies > 5pp: " f"{roe_anomaly_count}")

    log_lines.append(f"ROCE anomalies > 5pp: " f"{roce_anomaly_count}")

    log_lines.append("")

    log_lines.append("Allowed anomaly categories:")

    log_lines.append("- data source issue")

    log_lines.append("- version difference")

    log_lines.append("- formula discrepancy")

    log_lines.append("")

    log_lines.append("Analytics policy:")

    log_lines.append("Computed Ratio Engine values " "are used for analytics.")

    log_lines.append(
        "Source company-level ROE/ROCE "
        "values are retained for display "
        "and cross-check only."
    )

    OUTPUT_PATH.write_text(
        "\n".join(log_lines),
        encoding="utf-8",
    )

    print(f"Generated: {OUTPUT_PATH}")

    print(f"Companies reviewed: {len(df)}")

    print(f"Financials carve-outs: " f"{financial_count}")

    print(f"ROE anomalies: " f"{roe_anomaly_count}")

    print(f"ROCE anomalies: " f"{roce_anomaly_count}")


if __name__ == "__main__":
    analyze_edge_cases()
