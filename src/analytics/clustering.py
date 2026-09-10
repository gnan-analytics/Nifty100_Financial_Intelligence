import sqlite3
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

DB_PATH = Path("db/nifty100.db")
CASHFLOW_PATH = Path("output/cashflow_intelligence.xlsx")
OUTPUT_PATH = Path("output/cluster_labels.csv")
ELBOW_PATH = Path("reports/elbow_plot.png")

FEATURES = [
    "return_on_equity_pct",
    "debt_to_equity",
    "revenue_cagr_5yr",
    "fcf_cagr_5yr",
    "operating_profit_margin_pct",
]


def load_clustering_data() -> pd.DataFrame:
    """Load latest company-level financial features for clustering."""

    with sqlite3.connect(DB_PATH) as conn:
        companies = pd.read_sql_query(
            """
            SELECT id, company_name
            FROM companies
            """,
            conn,
        )

        sectors = pd.read_sql_query(
            """
            SELECT company_id, broad_sector
            FROM sectors
            """,
            conn,
        )

        ratios = pd.read_sql_query(
            """
            SELECT
                company_id,
                year,
                return_on_equity_pct,
                debt_to_equity,
                revenue_cagr_5yr,
                operating_profit_margin_pct
            FROM financial_ratios
            """,
            conn,
        )

    cashflow = pd.read_excel(CASHFLOW_PATH)

    companies["id"] = companies["id"].astype(str).str.strip().str.upper()

    sectors["company_id"] = sectors["company_id"].astype(str).str.strip().str.upper()

    ratios["company_id"] = ratios["company_id"].astype(str).str.strip().str.upper()

    cashflow["company_id"] = cashflow["company_id"].astype(str).str.strip().str.upper()

    ratios["year"] = ratios["year"].astype(str).str.strip()

    annual = ratios[ratios["year"].str.endswith("-03")].copy()

    annual = (
        annual.sort_values(["company_id", "year"])
        .groupby(
            "company_id",
            as_index=False,
        )
        .tail(1)
    )

    missing_ids = set(companies["id"]) - set(annual["company_id"])

    fallback_rows = []

    for ticker in sorted(missing_ids):
        rows = ratios[ratios["company_id"] == ticker].sort_values("year")

        if not rows.empty:
            fallback_rows.append(rows.iloc[-1])

    if fallback_rows:
        fallback_df = pd.DataFrame(fallback_rows)

        annual = pd.concat(
            [
                annual,
                fallback_df,
            ],
            ignore_index=True,
        )

    frame = (
        companies.merge(
            sectors,
            left_on="id",
            right_on="company_id",
            how="left",
        )
        .drop(
            columns=["company_id"],
            errors="ignore",
        )
        .rename(columns={"id": "company_id"})
        .merge(
            annual,
            on="company_id",
            how="left",
        )
        .merge(
            cashflow[
                [
                    "company_id",
                    "fcf_cagr_5yr",
                ]
            ],
            on="company_id",
            how="left",
        )
    )

    return frame


def impute_features(
    frame: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Impute missing values using sector medians with global fallback."""

    result = frame.copy()

    audit_rows = []

    for feature in FEATURES:
        sector_median = result.groupby("broad_sector")[feature].transform("median")

        missing_before = result[feature].isna()

        sector_fill_mask = missing_before & sector_median.notna()

        result.loc[
            sector_fill_mask,
            feature,
        ] = sector_median[sector_fill_mask]

        for idx in result[sector_fill_mask].index:
            audit_rows.append(
                {
                    "company_id": result.loc[
                        idx,
                        "company_id",
                    ],
                    "feature": feature,
                    "method": "SECTOR_MEDIAN",
                    "value": result.loc[
                        idx,
                        feature,
                    ],
                }
            )

        remaining_mask = result[feature].isna()

        if remaining_mask.any():
            global_median = frame[feature].median()

            if pd.isna(global_median):
                raise ValueError(f"No usable values exist for " f"{feature}")

            result.loc[
                remaining_mask,
                feature,
            ] = global_median

            for idx in result[remaining_mask].index:
                audit_rows.append(
                    {
                        "company_id": result.loc[
                            idx,
                            "company_id",
                        ],
                        "feature": feature,
                        "method": "GLOBAL_MEDIAN_FALLBACK",
                        "value": global_median,
                    }
                )

    audit = pd.DataFrame(audit_rows)

    return result, audit


def generate_elbow_plot(
    scaled_features: np.ndarray,
) -> None:
    """Generate KMeans inertia plot for k values 2 through 10."""

    inertias = []

    ks = range(2, 11)

    for k in ks:
        model = KMeans(
            n_clusters=k,
            random_state=42,
            n_init=10,
        )

        model.fit(scaled_features)

        inertias.append(model.inertia_)

    ELBOW_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    plt.figure(figsize=(8, 5))

    plt.plot(
        list(ks),
        inertias,
        marker="o",
    )

    plt.xlabel("Number of Clusters (k)")

    plt.ylabel("Inertia")

    plt.title("KMeans Elbow Plot")

    plt.xticks(list(ks))

    plt.tight_layout()

    plt.savefig(
        ELBOW_PATH,
        dpi=160,
    )

    plt.close()


def run_clustering() -> pd.DataFrame:
    """Run the complete five-cluster KMeans pipeline."""

    frame = load_clustering_data()

    if len(frame) != 92:
        raise ValueError(f"Expected 92 companies, got " f"{len(frame)}")

    prepared, audit = impute_features(frame)

    remaining_missing = prepared[FEATURES].isna().sum().sum()

    if remaining_missing != 0:
        raise ValueError("Missing clustering features remain " "after imputation.")

    scaler = StandardScaler()

    scaled = scaler.fit_transform(prepared[FEATURES])

    generate_elbow_plot(scaled)

    model = KMeans(
        n_clusters=5,
        random_state=42,
        n_init=10,
    )

    cluster_ids = model.fit_predict(scaled)

    distances = model.transform(scaled)

    prepared["cluster_id"] = cluster_ids

    prepared["distance_from_centroid"] = [
        distances[i, cluster_ids[i]] for i in range(len(cluster_ids))
    ]

    prepared["cluster_name"] = prepared["cluster_id"].map(
        {
            0: "Core Balanced Companies",
            1: "High Margin / Mixed Quality",
            2: "ROE Outliers",
            3: "FCF Growth Outliers",
            4: "Leveraged Financial Growth",
        }
    )

    output = prepared[
        [
            "company_id",
            "cluster_id",
            "cluster_name",
            "distance_from_centroid",
        ]
    ].copy()

    output = output.sort_values(
        [
            "cluster_id",
            "distance_from_centroid",
        ]
    )

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    output.to_csv(
        OUTPUT_PATH,
        index=False,
    )

    audit_path = Path("output/cluster_imputation_audit.csv")

    audit.to_csv(
        audit_path,
        index=False,
    )

    print("=" * 90)
    print("SPRINT 6 - DAY 36 KMEANS CLUSTERING")
    print("=" * 90)

    print(f"\nCompanies clustered: " f"{len(output)}")

    print(f"Clusters assigned: " f"{output['cluster_id'].nunique()}")

    print("\nCluster distribution:")

    print(output["cluster_id"].value_counts().sort_index().to_string())

    print("\nImputation methods:")

    if audit.empty:
        print("No imputation required.")
    else:
        print(audit["method"].value_counts().to_string())

    global_fallbacks = audit[audit["method"] == "GLOBAL_MEDIAN_FALLBACK"]

    print("\nGlobal median fallbacks:")

    if global_fallbacks.empty:
        print("None")
    else:
        print(
            global_fallbacks[
                [
                    "company_id",
                    "feature",
                    "value",
                ]
            ].to_string(index=False)
        )

    print(f"\nSaved: {OUTPUT_PATH}")

    print(f"Saved: {ELBOW_PATH}")

    print(f"Saved: {audit_path}")

    print("\nDAY 36 KMEANS CLUSTERING: PASS")

    return output


if __name__ == "__main__":
    run_clustering()
