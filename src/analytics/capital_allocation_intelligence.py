from pathlib import Path
import sqlite3

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]

DB_PATH = ROOT / "db" / "nifty100.db"

CAPITAL_PATH = (
    ROOT
    / "output"
    / "capital_allocation.csv"
)

INTEL_PATH = (
    ROOT
    / "output"
    / "cashflow_intelligence.xlsx"
)

DISTRIBUTION_PATH = (
    ROOT
    / "output"
    / "capital_allocation_distribution.csv"
)

CHANGES_PATH = (
    ROOT
    / "output"
    / "pattern_changes.csv"
)


EXPECTED_PATTERNS = [
    "Reinvestor",
    "Shareholder Returns",
    "Liquidating Assets",
    "Distress Signal",
    "Growth Funded by Debt",
    "Cash Accumulator",
    "Pre-Revenue",
    "Mixed",
]


def prepare_year(df):
    x = df.copy()

    x["year"] = x["year"].astype(str)

    x["_date"] = pd.to_datetime(
        x["year"],
        format="%Y-%m",
        errors="coerce",
    )

    return (
        x
        .dropna(subset=["_date"])
        .sort_values(
            [
                "company_id",
                "_date",
            ]
        )
    )


def load_company_master():
    with sqlite3.connect(DB_PATH) as conn:

        companies = pd.read_sql_query(
            """
            SELECT
                c.id AS company_id,
                c.company_name,
                s.broad_sector AS sector
            FROM companies c
            LEFT JOIN sectors s
                ON s.company_id = c.id
            ORDER BY c.id
            """,
            conn,
        )

    companies["company_id"] = (
        companies["company_id"]
        .astype(str)
        .str.strip()
        .str.upper()
    )

    return companies


def build_latest_distribution(
    companies,
    allocation,
):
    latest = (
        prepare_year(allocation)
        .groupby(
            "company_id",
            as_index=False,
        )
        .tail(1)
        [
            [
                "company_id",
                "year",
                "pattern_label",
            ]
        ]
    )

    latest = companies.merge(
        latest,
        on="company_id",
        how="left",
    )

    latest["pattern_label"] = (
        latest["pattern_label"]
        .fillna("Data Unavailable")
    )

    latest["year"] = (
        latest["year"]
        .fillna("Data Unavailable")
    )

    category_order = (
        EXPECTED_PATTERNS
        + ["Data Unavailable"]
    )

    counts = (
        latest["pattern_label"]
        .value_counts()
        .reindex(
            category_order,
            fill_value=0,
        )
    )

    distribution = (
        counts
        .rename_axis(
            "pattern_label"
        )
        .reset_index(
            name="company_count"
        )
    )

    distribution["pct_of_92"] = (
        distribution[
            "company_count"
        ]
        / len(companies)
        * 100
    ).round(2)

    distribution = distribution[
        distribution[
            "company_count"
        ] > 0
    ].reset_index(drop=True)

    return latest, distribution


def build_pattern_changes(allocation):
    x = prepare_year(
        allocation
    )

    rows = []

    for company_id, group in x.groupby(
        "company_id"
    ):

        group = (
            group
            .sort_values("_date")
            .reset_index(drop=True)
        )

        previous = None

        for _, row in group.iterrows():

            current = row[
                "pattern_label"
            ]

            if previous is not None:

                if (
                    current
                    != previous[
                        "pattern_label"
                    ]
                ):

                    rows.append(
                        {
                            "company_id": (
                                company_id
                            ),
                            "from_year": (
                                previous[
                                    "year"
                                ]
                            ),
                            "to_year": (
                                row[
                                    "year"
                                ]
                            ),
                            "from_pattern": (
                                previous[
                                    "pattern_label"
                                ]
                            ),
                            "to_pattern": (
                                current
                            ),
                        }
                    )

            previous = row

    return pd.DataFrame(
        rows,
        columns=[
            "company_id",
            "from_year",
            "to_year",
            "from_pattern",
            "to_pattern",
        ],
    )


def validate_intelligence_labels(
    latest,
):
    intel = pd.read_excel(
        INTEL_PATH
    )

    intel["company_id"] = (
        intel["company_id"]
        .astype(str)
        .str.strip()
        .str.upper()
    )

    check = intel[
        [
            "company_id",
            "capital_allocation_label",
        ]
    ].merge(
        latest[
            [
                "company_id",
                "pattern_label",
            ]
        ],
        on="company_id",
        how="left",
    )

    mismatches = check[
        check[
            "capital_allocation_label"
        ]
        != check[
            "pattern_label"
        ]
    ]

    return mismatches


def main():
    companies = (
        load_company_master()
    )

    allocation = pd.read_csv(
        CAPITAL_PATH
    )

    allocation["company_id"] = (
        allocation[
            "company_id"
        ]
        .astype(str)
        .str.strip()
        .str.upper()
    )

    latest, distribution = (
        build_latest_distribution(
            companies,
            allocation,
        )
    )

    changes = (
        build_pattern_changes(
            allocation
        )
    )

    mismatches = (
        validate_intelligence_labels(
            latest
        )
    )

    distribution.to_csv(
        DISTRIBUTION_PATH,
        index=False,
    )

    changes.to_csv(
        CHANGES_PATH,
        index=False,
    )

    print("=" * 90)
    print(
        "SPRINT 5 - DAY 32 CAPITAL ALLOCATION INTELLIGENCE"
    )
    print("=" * 90)

    print(
        "\nCapital allocation rows:",
        len(allocation),
    )

    print(
        "Companies with history:",
        allocation[
            "company_id"
        ].nunique(),
    )

    print(
        "Company master:",
        len(companies),
    )

    missing = sorted(
        set(
            companies[
                "company_id"
            ]
        )
        - set(
            allocation[
                "company_id"
            ]
        )
    )

    print(
        "\nCompanies without allocation history:",
        missing,
    )

    observed = sorted(
        allocation[
            "pattern_label"
        ]
        .dropna()
        .unique()
        .tolist()
    )

    print(
        "\nObserved historical patterns:",
        len(observed),
    )

    for pattern in observed:
        print(
            f"  {pattern}"
        )

    print(
        "\nLATEST DISTRIBUTION:"
    )

    print(
        distribution.to_string(
            index=False
        )
    )

    print(
        "\nLatest reporting categories:",
        len(distribution),
    )

    print(
        "Historical pattern changes:",
        len(changes),
    )

    print(
        "Companies with >=1 change:",
        changes[
            "company_id"
        ].nunique()
        if not changes.empty
        else 0,
    )

    print(
        "Cashflow intelligence mismatches:",
        len(mismatches),
    )

    assert len(companies) == 92
    assert (
        allocation[
            "company_id"
        ].nunique()
        == 91
    )

    assert missing == ["ATGL"]

    assert set(observed) == set(EXPECTED_PATTERNS)

    assert (
        latest[
            "pattern_label"
        ]
        .eq(
            "Data Unavailable"
        )
        .sum()
        == 1
    )

    assert len(mismatches) == 0

    print(
        f"\nCreated: {DISTRIBUTION_PATH}"
    )

    print(
        f"Created: {CHANGES_PATH}"
    )

    print(
        "\nDAY 32 GENERATOR: PASS"
    )


if __name__ == "__main__":
    main()
