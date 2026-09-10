import re
from pathlib import Path

import pandas as pd

from src.etl.normaliser import normalize_ticker, normalize_year

# =========================================================
# PATHS
# =========================================================

CORE_DIR = Path("data/raw/core")
SUPPLEMENTARY_DIR = Path("data/raw/supplementary")


CORE_FILES = [
    "companies.xlsx",
    "profitandloss.xlsx",
    "balancesheet.xlsx",
    "cashflow.xlsx",
    "analysis.xlsx",
    "documents.xlsx",
    "prosandcons.xlsx",
]


SUPPLEMENTARY_FILES = [
    "sectors.xlsx",
    "stock_prices.xlsx",
    "market_cap.xlsx",
    "financial_ratios.xlsx",
    "peer_groups.xlsx",
]


# =========================================================
# COLUMN CLEANING
# =========================================================


def clean_column_names(df):
    """
    Convert Excel column names to lowercase snake_case.
    """

    df.columns = [
        str(column).strip().lower().replace(" ", "_") for column in df.columns
    ]

    return df


# =========================================================
# EXCEL LOADER
# =========================================================


def load_excel_file(path, header):
    """
    Load a single Excel file.
    """

    df = pd.read_excel(
        path,
        header=header,
    )

    return clean_column_names(df)


# =========================================================
# COMPANY / TICKER NORMALIZATION
# =========================================================


def normalize_company_id(df):
    """
    Normalize company identifiers.
    """

    if "company_id" in df.columns:

        df["company_id"] = df["company_id"].apply(normalize_ticker)

    if "id" in df.columns and "company_name" in df.columns:

        df["id"] = df["id"].apply(normalize_ticker)

    return df


# =========================================================
# YEAR NORMALIZATION
# =========================================================


def normalize_year_column(df):
    """
    Normalize supported year formats to YYYY-MM.

    Invalid values are preserved so DQ-07
    can detect them later.
    """

    if "year" not in df.columns:
        return df

    normalized_values = []

    for value in df["year"]:

        try:

            normalized_values.append(normalize_year(value))

        except ValueError:

            normalized_values.append(value)

    df["year"] = normalized_values

    return df


# =========================================================
# DQ-02 DEDUPLICATION
# =========================================================


def deduplicate_company_year(
    df,
    table_name,
):
    """
    Remove duplicate (company_id, year) rows.

    Keep LAST occurrence.
    """

    required = {
        "company_id",
        "year",
    }

    if not required.issubset(df.columns):
        return df

    duplicate_mask = df.duplicated(
        subset=[
            "company_id",
            "year",
        ],
        keep=False,
    )

    duplicate_count = int(duplicate_mask.sum())

    if duplicate_count > 0:

        print(f"Deduplicating {table_name}: " f"{duplicate_count} duplicate rows found")

        original_count = len(df)

        df = df.drop_duplicates(
            subset=[
                "company_id",
                "year",
            ],
            keep="last",
        ).reset_index(drop=True)

        removed_count = original_count - len(df)

        print(
            f"Removed {removed_count} rows "
            f"from {table_name}; "
            f"kept last occurrence"
        )

    return df


# =========================================================
# DQ-07 INVALID YEAR CLEANUP
# =========================================================


def reject_invalid_year_rows(
    datasets,
):
    """
    Reject rows where year is not valid YYYY-MM.
    """

    pattern = re.compile(r"^\d{4}-\d{2}$")

    rejected_rows = []

    for table_name, df in datasets.items():

        if "year" not in df.columns:
            continue

        invalid_indexes = []

        for index, row in df.iterrows():

            value = row.get("year")

            valid = False

            if pd.notna(value):

                value_text = str(value).strip()

                if pattern.fullmatch(value_text):

                    month = int(value_text.split("-")[1])

                    if 1 <= month <= 12:
                        valid = True

            if not valid:

                invalid_indexes.append(index)

                rejected_rows.append(
                    {
                        "rule_id": "DQ-07",
                        "table": table_name,
                        "severity": "CRITICAL",
                        "status": "RESOLVED_REJECTED",
                        "row_index": index,
                        "company_id": row.get("company_id"),
                        "year": value,
                        "message": ("Invalid year format"),
                        "action": ("Rejected before " "database load"),
                    }
                )

        if invalid_indexes:

            print(
                f"DQ-07 {table_name}: "
                f"rejecting "
                f"{len(invalid_indexes)} "
                f"invalid year rows"
            )

            datasets[table_name] = df.drop(index=invalid_indexes).reset_index(drop=True)

    return (
        datasets,
        rejected_rows,
    )


# =========================================================
# DQ-03 FK CLEANUP
# =========================================================


def reject_orphan_company_ids(
    datasets,
):
    """
    Reject rows where company_id is not
    present in companies.id.
    """

    companies = datasets["companies"]

    valid_company_ids = set(companies["id"].dropna().tolist())

    rejected_rows = []

    for table_name, df in datasets.items():

        if table_name == "companies":
            continue

        if "company_id" not in df.columns:
            continue

        orphan_mask = ~df["company_id"].isin(valid_company_ids)

        orphan_rows = df[orphan_mask]

        if len(orphan_rows) == 0:
            continue

        print(
            f"DQ-03 {table_name}: "
            f"rejecting "
            f"{len(orphan_rows)} "
            f"orphan FK rows"
        )

        for index, row in orphan_rows.iterrows():

            rejected_rows.append(
                {
                    "rule_id": "DQ-03",
                    "table": table_name,
                    "severity": "CRITICAL",
                    "status": "RESOLVED_REJECTED",
                    "row_index": index,
                    "company_id": row.get("company_id"),
                    "year": row.get("year"),
                    "message": ("company_id not found " "in companies.id"),
                    "action": ("Rejected before " "database load"),
                }
            )

        datasets[table_name] = df[~orphan_mask].reset_index(drop=True)

    return (
        datasets,
        rejected_rows,
    )


# =========================================================
# LOAD CORE DATASETS
# =========================================================


def load_core_datasets():
    """
    Load all 7 core datasets.
    """

    datasets = {}

    for filename in CORE_FILES:

        path = CORE_DIR / filename

        if not path.exists():

            raise FileNotFoundError(f"Missing file: {path}")

        # Core files use header=1
        df = load_excel_file(
            path,
            header=1,
        )

        df = normalize_company_id(df)

        if "year" in df.columns:

            df = normalize_year_column(df)

        # Composite key datasets
        if filename in [
            "profitandloss.xlsx",
            "balancesheet.xlsx",
            "cashflow.xlsx",
        ]:

            df = deduplicate_company_year(
                df,
                path.stem,
            )

        datasets[path.stem] = df

        print(
            f"Loaded {filename:<25} " f"rows={len(df):<6} " f"columns={len(df.columns)}"
        )

    return datasets


# =========================================================
# LOAD SUPPLEMENTARY DATASETS
# =========================================================


def load_supplementary_datasets():
    """
    Load all 5 supplementary datasets.
    """

    datasets = {}

    for filename in SUPPLEMENTARY_FILES:

        path = SUPPLEMENTARY_DIR / filename

        if not path.exists():

            raise FileNotFoundError(f"Missing file: {path}")

        # Supplementary files use header=0
        df = load_excel_file(
            path,
            header=0,
        )

        df = normalize_company_id(df)

        if "year" in df.columns:

            df = normalize_year_column(df)

        # These also use company_id + year
        # as their composite key
        if filename in [
            "market_cap.xlsx",
            "financial_ratios.xlsx",
        ]:

            df = deduplicate_company_year(
                df,
                path.stem,
            )

        datasets[path.stem] = df

        print(
            f"Loaded {filename:<25} " f"rows={len(df):<6} " f"columns={len(df.columns)}"
        )

    return datasets


# =========================================================
# LOAD ALL DATASETS
# =========================================================


def load_all_datasets():
    """
    Load, normalize, deduplicate,
    reject invalid years and reject FK orphans.
    """

    print()
    print("Loading core datasets")
    print("-" * 60)

    core = load_core_datasets()

    print()
    print("Loading supplementary datasets")
    print("-" * 60)

    supplementary = load_supplementary_datasets()

    datasets = {
        **core,
        **supplementary,
    }

    print()
    print("Running DQ-07 year cleanup")
    print("-" * 60)

    (
        datasets,
        year_rejections,
    ) = reject_invalid_year_rows(datasets)

    print()
    print("Running DQ-03 FK cleanup")
    print("-" * 60)

    (
        datasets,
        fk_rejections,
    ) = reject_orphan_company_ids(datasets)

    print()
    print("Load summary")
    print("-" * 60)

    for name, df in datasets.items():

        print(f"{name:<25} " f"{df.shape}")

    print()

    print(f"Total datasets loaded: " f"{len(datasets)}")

    print(f"DQ-07 rejected rows: " f"{len(year_rejections)}")

    print(f"DQ-03 rejected rows: " f"{len(fk_rejections)}")

    return datasets


# =========================================================
# ENTRY POINT
# =========================================================

if __name__ == "__main__":
    load_all_datasets()
