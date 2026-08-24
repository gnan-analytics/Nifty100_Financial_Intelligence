from pathlib import Path

from src.etl.loader import (
    CORE_DIR,
    SUPPLEMENTARY_DIR,
    CORE_FILES,
    SUPPLEMENTARY_FILES,
    load_core_datasets,
    load_supplementary_datasets,
)


# =========================================================
# FILE EXISTENCE TESTS
# =========================================================

def test_core_files_exist():
    for filename in CORE_FILES:
        assert (CORE_DIR / filename).exists()


def test_supplementary_files_exist():
    for filename in SUPPLEMENTARY_FILES:
        assert (SUPPLEMENTARY_DIR / filename).exists()


# =========================================================
# FILE COUNT TESTS
# =========================================================

def test_core_file_count():
    files = list(
        Path(CORE_DIR).glob("*.xlsx")
    )

    assert len(files) == 7


def test_supplementary_file_count():
    files = list(
        Path(SUPPLEMENTARY_DIR).glob("*.xlsx")
    )

    assert len(files) == 5


# =========================================================
# CORE DATASET LOAD TEST
# =========================================================

def test_load_core_datasets():
    datasets = load_core_datasets()

    assert len(datasets) == 7

    assert "companies" in datasets
    assert "profitandloss" in datasets
    assert "balancesheet" in datasets
    assert "cashflow" in datasets
    assert "analysis" in datasets
    assert "documents" in datasets
    assert "prosandcons" in datasets


# =========================================================
# SUPPLEMENTARY DATASET LOAD TEST
# =========================================================

def test_load_supplementary_datasets():
    datasets = (
        load_supplementary_datasets()
    )

    assert len(datasets) == 5

    assert "sectors" in datasets
    assert "stock_prices" in datasets
    assert "market_cap" in datasets
    assert "financial_ratios" in datasets
    assert "peer_groups" in datasets


# =========================================================
# CORE ROW COUNT TESTS
# AFTER DQ-02 DEDUPLICATION
# =========================================================

def test_companies_row_count():
    datasets = load_core_datasets()

    assert (
        len(datasets["companies"])
        == 92
    )


def test_profitandloss_row_count():
    datasets = load_core_datasets()

    assert (
        len(
            datasets[
                "profitandloss"
            ]
        )
        == 1263
    )


def test_balancesheet_row_count():
    datasets = load_core_datasets()

    assert (
        len(
            datasets[
                "balancesheet"
            ]
        )
        == 1225
    )


def test_cashflow_row_count():
    datasets = load_core_datasets()

    assert (
        len(
            datasets[
                "cashflow"
            ]
        )
        == 1152
    )


# =========================================================
# SUPPLEMENTARY ROW COUNT TESTS
# =========================================================

def test_stock_prices_row_count():
    datasets = (
        load_supplementary_datasets()
    )

    assert (
        len(
            datasets[
                "stock_prices"
            ]
        )
        == 5520
    )