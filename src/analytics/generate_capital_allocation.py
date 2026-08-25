from pathlib import Path
import sqlite3

import pandas as pd

from src.analytics.cashflow_kpis import (
    calculate_cfo_pat_ratio,
    classify_capital_allocation,
)


DB_PATH = Path("db/nifty100.db")
OUTPUT_PATH = Path("output/capital_allocation.csv")


def load_data():
    """
    Load cash flow and P&L data from SQLite.
    """

    with sqlite3.connect(DB_PATH) as conn:

        query = """
        SELECT
            cf.company_id,
            cf.year,
            cf.operating_activity,
            cf.investing_activity,
            cf.financing_activity,
            p.net_profit
        FROM cashflow cf
        LEFT JOIN profitandloss p
            ON cf.company_id = p.company_id
           AND cf.year = p.year
        ORDER BY
            cf.company_id,
            cf.year
        """

        df = pd.read_sql_query(
            query,
            conn,
        )

    return df


def generate_capital_allocation():
    """
    Generate capital allocation pattern
    for every company-year in cashflow.
    """

    df = load_data()

    output_rows = []

    for _, row in df.iterrows():

        cfo_pat_ratio = (
            calculate_cfo_pat_ratio(
                operating_activity=row[
                    "operating_activity"
                ],
                net_profit=row[
                    "net_profit"
                ],
            )
        )

        allocation = (
            classify_capital_allocation(
                cfo=row[
                    "operating_activity"
                ],
                cfi=row[
                    "investing_activity"
                ],
                cff=row[
                    "financing_activity"
                ],
                cfo_pat_ratio=cfo_pat_ratio,
            )
        )

        output_rows.append(
            {
                "company_id": row[
                    "company_id"
                ],
                "year": row[
                    "year"
                ],
                "cfo_sign": allocation[
                    "cfo_sign"
                ],
                "cfi_sign": allocation[
                    "cfi_sign"
                ],
                "cff_sign": allocation[
                    "cff_sign"
                ],
                "pattern_label": allocation[
                    "pattern_label"
                ],
            }
        )

    output_df = pd.DataFrame(
        output_rows
    )

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    output_df.to_csv(
        OUTPUT_PATH,
        index=False,
    )

    print(
        f"Generated: {OUTPUT_PATH}"
    )

    print(
        f"Rows: {len(output_df)}"
    )

    print()
    print(
        "Pattern counts:"
    )

    print(
        output_df[
            "pattern_label"
        ]
        .value_counts()
    )


if __name__ == "__main__":
    generate_capital_allocation()