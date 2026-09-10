import logging
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import pandas as pd
import requests

from src.etl.loader import (
    load_core_datasets,
    load_supplementary_datasets,
    reject_invalid_year_rows,
    reject_orphan_company_ids,
)

# =========================================================
# CONFIGURATION
# =========================================================

OUTPUT_DIR = Path("output")

FAILURE_FILE = OUTPUT_DIR / "validation_failures.csv"

DQ15_INFO_FILE = OUTPUT_DIR / "dq15_balance_info.csv"

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s | %(message)s",
)

logger = logging.getLogger(__name__)


# =========================================================
# FAILURE HELPER
# =========================================================


def make_failure(
    rule_id,
    table,
    severity,
    message,
    row_index=None,
    company_id=None,
    year=None,
    status=None,
    action=None,
):
    """Create failure."""
    if status is None:

        if severity == "CRITICAL":
            status = "OPEN_BLOCKER"

        elif severity == "INFO":
            status = "INFO"

        else:
            status = "OPEN_REVIEW"

    return {
        "rule_id": rule_id,
        "table": table,
        "severity": severity,
        "status": status,
        "message": message,
        "action": action,
        "row_index": row_index,
        "company_id": company_id,
        "year": year,
    }


# =========================================================
# DQ-01
# PRIMARY KEY UNIQUENESS
# =========================================================


def validate_pk_uniqueness(
    table_name,
    df,
    key_columns,
):
    """Validate pk uniqueness."""
    failures = []

    if not set(key_columns).issubset(df.columns):
        return failures

    duplicate_mask = df.duplicated(
        subset=key_columns,
        keep=False,
    )

    duplicates = df[duplicate_mask]

    for idx, row in duplicates.iterrows():

        failures.append(
            make_failure(
                rule_id="DQ-01",
                table=table_name,
                severity="CRITICAL",
                message=("Duplicate primary key: " f"{key_columns}"),
                row_index=idx,
                company_id=row.get(
                    "company_id",
                    row.get("id"),
                ),
                year=row.get("year"),
                action=("Deduplicate before " "database load"),
            )
        )

    return failures


# =========================================================
# DQ-02
# COMPANY-YEAR UNIQUENESS
# =========================================================


def validate_company_year_uniqueness(
    table_name,
    df,
):
    """Validate company year uniqueness."""
    failures = []

    required = {
        "company_id",
        "year",
    }

    if not required.issubset(df.columns):
        return failures

    duplicate_mask = df.duplicated(
        subset=[
            "company_id",
            "year",
        ],
        keep=False,
    )

    duplicates = df[duplicate_mask]

    for idx, row in duplicates.iterrows():

        failures.append(
            make_failure(
                rule_id="DQ-02",
                table=table_name,
                severity="CRITICAL",
                message=("Duplicate " "(company_id, year) pair"),
                row_index=idx,
                company_id=row.get("company_id"),
                year=row.get("year"),
                action=("Keep last occurrence " "and reject earlier duplicate"),
            )
        )

    return failures


# =========================================================
# DQ-03
# FOREIGN KEY INTEGRITY
# =========================================================


def validate_fk_integrity(
    table_name,
    df,
    valid_company_ids,
):
    """Validate fk integrity."""
    failures = []

    if "company_id" not in df.columns:
        return failures

    orphan_mask = ~df["company_id"].isin(valid_company_ids)

    orphan_rows = df[orphan_mask]

    for idx, row in orphan_rows.iterrows():

        failures.append(
            make_failure(
                rule_id="DQ-03",
                table=table_name,
                severity="CRITICAL",
                status="RESOLVED_REJECTED",
                message=("company_id does not exist " "in companies.id"),
                action=("Rejected before " "database load"),
                row_index=idx,
                company_id=row.get("company_id"),
                year=row.get("year"),
            )
        )

    return failures


# =========================================================
# DQ-04
# BALANCE SHEET BALANCE
# =========================================================


def validate_balance_sheet(
    df,
):
    """Validate balance sheet."""
    failures = []

    required = {
        "total_assets",
        "total_liabilities",
    }

    if not required.issubset(df.columns):
        return failures

    for idx, row in df.iterrows():

        assets = pd.to_numeric(
            row.get("total_assets"),
            errors="coerce",
        )

        liabilities = pd.to_numeric(
            row.get("total_liabilities"),
            errors="coerce",
        )

        if pd.isna(assets) or pd.isna(liabilities):
            continue

        if assets == 0:
            continue

        difference = abs(assets - liabilities) / abs(assets)

        if difference >= 0.01:

            failures.append(
                make_failure(
                    rule_id="DQ-04",
                    table="balancesheet",
                    severity="WARNING",
                    message=("Balance sheet mismatch: " f"{difference * 100:.2f}%"),
                    action=("Manual analyst review"),
                    row_index=idx,
                    company_id=row.get("company_id"),
                    year=row.get("year"),
                )
            )

    return failures


# =========================================================
# DQ-05
# OPM CROSS-CHECK
# =========================================================


def validate_opm(
    df,
):
    """Validate opm."""
    failures = []

    required = {
        "sales",
        "operating_profit",
        "opm_percentage",
    }

    if not required.issubset(df.columns):
        return failures

    for idx, row in df.iterrows():

        sales = pd.to_numeric(
            row.get("sales"),
            errors="coerce",
        )

        operating_profit = pd.to_numeric(
            row.get("operating_profit"),
            errors="coerce",
        )

        source_opm = pd.to_numeric(
            row.get("opm_percentage"),
            errors="coerce",
        )

        if pd.isna(sales) or pd.isna(operating_profit) or pd.isna(source_opm):
            continue

        if sales == 0:
            continue

        calculated_opm = operating_profit / sales * 100

        difference = abs(source_opm - calculated_opm)

        if difference >= 1.0:

            failures.append(
                make_failure(
                    rule_id="DQ-05",
                    table="profitandloss",
                    severity="WARNING",
                    message=(
                        f"OPM mismatch: "
                        f"source="
                        f"{source_opm:.2f}, "
                        f"calculated="
                        f"{calculated_opm:.2f}"
                    ),
                    action=(
                        "Keep source for display; " "use computed OPM " "in analytics"
                    ),
                    row_index=idx,
                    company_id=row.get("company_id"),
                    year=row.get("year"),
                )
            )

    return failures


# =========================================================
# BANK IDENTIFICATION
# =========================================================


def get_bank_tickers(
    companies,
    sectors,
):
    """Return bank tickers."""
    bank_tickers = set()

    if "company_id" in sectors.columns:

        text_columns = [col for col in sectors.columns if col != "company_id"]

        for _, row in sectors.iterrows():

            combined_text = " ".join(
                str(
                    row.get(
                        col,
                        "",
                    )
                )
                for col in text_columns
            ).lower()

            if "bank" in combined_text:

                ticker = row.get("company_id")

                if pd.notna(ticker):
                    bank_tickers.add(ticker)

    if {
        "id",
        "company_name",
    }.issubset(companies.columns):

        for _, row in companies.iterrows():

            company_name = str(
                row.get(
                    "company_name",
                    "",
                )
            ).lower()

            if "bank" in company_name:

                ticker = row.get("id")

                if pd.notna(ticker):
                    bank_tickers.add(ticker)

    return bank_tickers


# =========================================================
# DQ-06
# POSITIVE SALES
# =========================================================


def validate_positive_sales(
    df,
    bank_tickers,
):
    """Validate positive sales."""
    failures = []

    if "sales" not in df.columns:
        return failures

    for idx, row in df.iterrows():

        ticker = row.get("company_id")

        if ticker in bank_tickers:
            continue

        sales = pd.to_numeric(
            row.get("sales"),
            errors="coerce",
        )

        if pd.isna(sales):
            continue

        if sales <= 0:

            failures.append(
                make_failure(
                    rule_id="DQ-06",
                    table="profitandloss",
                    severity="WARNING",
                    message=("Non-positive sales: " f"{sales}"),
                    action=("Exclude row from " "sales CAGR calculation"),
                    row_index=idx,
                    company_id=ticker,
                    year=row.get("year"),
                )
            )

    return failures


# =========================================================
# DQ-07
# YEAR FORMAT
# =========================================================


def validate_year_format(
    table_name,
    df,
):
    """Validate year format."""
    failures = []

    if "year" not in df.columns:
        return failures

    pattern = re.compile(r"^\d{4}-\d{2}$")

    for idx, row in df.iterrows():

        value = row.get("year")

        if pd.isna(value):

            failures.append(
                make_failure(
                    rule_id="DQ-07",
                    table=table_name,
                    severity="CRITICAL",
                    status=("RESOLVED_REJECTED"),
                    message=("Year is null"),
                    action=("Rejected before " "database load"),
                    row_index=idx,
                    company_id=row.get("company_id"),
                    year=value,
                )
            )

            continue

        value = str(value).strip()

        if not pattern.fullmatch(value):

            failures.append(
                make_failure(
                    rule_id="DQ-07",
                    table=table_name,
                    severity="CRITICAL",
                    status=("RESOLVED_REJECTED"),
                    message=("Invalid year format: " f"{value}"),
                    action=("Rejected before " "database load"),
                    row_index=idx,
                    company_id=row.get("company_id"),
                    year=value,
                )
            )

            continue

        month = int(value.split("-")[1])

        if month < 1 or month > 12:

            failures.append(
                make_failure(
                    rule_id="DQ-07",
                    table=table_name,
                    severity="CRITICAL",
                    status=("RESOLVED_REJECTED"),
                    message=("Invalid month " f"in year: {value}"),
                    action=("Rejected before " "database load"),
                    row_index=idx,
                    company_id=row.get("company_id"),
                    year=value,
                )
            )

    return failures


# =========================================================
# DQ-08
# TICKER FORMAT
# =========================================================


def validate_ticker_format(
    table_name,
    df,
):
    """Validate ticker format."""
    failures = []

    column = None

    if table_name == "companies":

        if "id" in df.columns:
            column = "id"

    elif "company_id" in df.columns:

        column = "company_id"

    if column is None:
        return failures

    for idx, row in df.iterrows():

        ticker = row.get(column)

        if pd.isna(ticker):

            failures.append(
                make_failure(
                    rule_id="DQ-08",
                    table=table_name,
                    severity="CRITICAL",
                    message=("Ticker is null"),
                    action="Reject row",
                    row_index=idx,
                    company_id=ticker,
                    year=row.get("year"),
                )
            )

            continue

        ticker = str(ticker)

        valid_format = ticker == ticker.strip().upper()

        valid_length = 2 <= len(ticker) <= 12

        if not valid_format:

            failures.append(
                make_failure(
                    rule_id="DQ-08",
                    table=table_name,
                    severity="CRITICAL",
                    message=("Ticker not normalized: " f"{ticker}"),
                    action=("Strip whitespace " "and uppercase"),
                    row_index=idx,
                    company_id=ticker,
                    year=row.get("year"),
                )
            )

        elif not valid_length:

            failures.append(
                make_failure(
                    rule_id="DQ-08",
                    table=table_name,
                    severity="CRITICAL",
                    message=("Ticker length outside " f"2-12 chars: {ticker}"),
                    action="Reject row",
                    row_index=idx,
                    company_id=ticker,
                    year=row.get("year"),
                )
            )

    return failures


# =========================================================
# DQ-09
# NET CASH CHECK
# =========================================================


def validate_net_cash(
    df,
):
    """Validate net cash."""
    failures = []

    required = {
        "operating_activity",
        "investing_activity",
        "financing_activity",
        "net_cash_flow",
    }

    if not required.issubset(df.columns):
        return failures

    for idx, row in df.iterrows():

        cfo = pd.to_numeric(
            row.get("operating_activity"),
            errors="coerce",
        )

        cfi = pd.to_numeric(
            row.get("investing_activity"),
            errors="coerce",
        )

        cff = pd.to_numeric(
            row.get("financing_activity"),
            errors="coerce",
        )

        net_cash = pd.to_numeric(
            row.get("net_cash_flow"),
            errors="coerce",
        )

        values = [
            cfo,
            cfi,
            cff,
            net_cash,
        ]

        if any(pd.isna(value) for value in values):
            continue

        calculated = cfo + cfi + cff

        difference = abs(net_cash - calculated)

        if difference > 10:

            failures.append(
                make_failure(
                    rule_id="DQ-09",
                    table="cashflow",
                    severity="WARNING",
                    message=(
                        "Net cash mismatch: "
                        f"source={net_cash:.2f}, "
                        f"computed="
                        f"{calculated:.2f}, "
                        f"diff={difference:.2f}"
                    ),
                    action=("Use computed net cash " "for analytics"),
                    row_index=idx,
                    company_id=row.get("company_id"),
                    year=row.get("year"),
                )
            )

    return failures


# =========================================================
# DQ-10
# NON-NEGATIVE FIXED ASSETS
# =========================================================


def validate_fixed_assets(
    df,
):
    """Validate fixed assets."""
    failures = []

    if "fixed_assets" not in df.columns:
        return failures

    for idx, row in df.iterrows():

        value = pd.to_numeric(
            row.get("fixed_assets"),
            errors="coerce",
        )

        if pd.isna(value):
            continue

        if value < 0:

            failures.append(
                make_failure(
                    rule_id="DQ-10",
                    table="balancesheet",
                    severity="WARNING",
                    message=("Negative fixed assets: " f"{value}"),
                    action=("Coerce to 0 " "in cleaned analytics"),
                    row_index=idx,
                    company_id=row.get("company_id"),
                    year=row.get("year"),
                )
            )

    return failures


# =========================================================
# DQ-11
# TAX RATE RANGE
# =========================================================


def validate_tax_rate(
    df,
):
    """Validate tax rate."""
    failures = []

    if "tax_percentage" not in df.columns:
        return failures

    for idx, row in df.iterrows():

        tax = pd.to_numeric(
            row.get("tax_percentage"),
            errors="coerce",
        )

        if pd.isna(tax):
            continue

        if tax < 0 or tax > 60:

            failures.append(
                make_failure(
                    rule_id="DQ-11",
                    table="profitandloss",
                    severity="WARNING",
                    message=("Tax percentage outside " f"0-60 range: {tax}"),
                    action=("Manual analyst review"),
                    row_index=idx,
                    company_id=row.get("company_id"),
                    year=row.get("year"),
                )
            )

    return failures


# =========================================================
# DQ-12
# DIVIDEND PAYOUT CAP
# =========================================================


def validate_dividend_payout(
    df,
):
    """Validate dividend payout."""
    failures = []

    if "dividend_payout" not in df.columns:
        return failures

    for idx, row in df.iterrows():

        payout = pd.to_numeric(
            row.get("dividend_payout"),
            errors="coerce",
        )

        if pd.isna(payout):
            continue

        if payout > 200:

            failures.append(
                make_failure(
                    rule_id="DQ-12",
                    table="profitandloss",
                    severity="WARNING",
                    message=("Dividend payout " f"exceeds 200%: {payout}"),
                    action=("Manual analyst review"),
                    row_index=idx,
                    company_id=row.get("company_id"),
                    year=row.get("year"),
                )
            )

    return failures


# =========================================================
# DQ-13
# DOCUMENT URL VALIDITY
# =========================================================


def check_one_url(
    index,
    company_id,
    year,
    url,
):
    """Check one url."""
    if pd.isna(url):
        return make_failure(
            rule_id="DQ-13",
            table="documents",
            severity="WARNING",
            message=("Annual report URL is null"),
            action=("Mark report unavailable"),
            row_index=index,
            company_id=company_id,
            year=year,
        )

    url = str(url).strip()

    if not url.lower().startswith(
        (
            "http://",
            "https://",
        )
    ):
        return make_failure(
            rule_id="DQ-13",
            table="documents",
            severity="WARNING",
            message=("Invalid annual report " f"URL format: {url}"),
            action=("Mark report unavailable"),
            row_index=index,
            company_id=company_id,
            year=year,
        )

    try:

        response = requests.head(
            url,
            timeout=5,
            allow_redirects=True,
        )

        if response.status_code != 200:

            return make_failure(
                rule_id="DQ-13",
                table="documents",
                severity="WARNING",
                message=(
                    "Annual report URL " f"returned HTTP " f"{response.status_code}"
                ),
                action=("Keep row; mark report " "unavailable if needed"),
                row_index=index,
                company_id=company_id,
                year=year,
            )

    except requests.RequestException as exc:

        return make_failure(
            rule_id="DQ-13",
            table="documents",
            severity="WARNING",
            message=("Annual report URL " f"check failed: " f"{type(exc).__name__}"),
            action=("Keep row; manual URL review"),
            row_index=index,
            company_id=company_id,
            year=year,
        )

    return None


def validate_document_urls(
    df,
):
    """Validate document urls."""
    failures = []

    if "annual_report" not in df.columns:
        logger.warning("DQ-13 skipped: " "annual_report column missing")

        return failures

    logger.info(
        "Running DQ-13 URL checks " "on %s document rows",
        len(df),
    )

    tasks = []

    with ThreadPoolExecutor(max_workers=12) as executor:

        for idx, row in df.iterrows():

            future = executor.submit(
                check_one_url,
                idx,
                row.get("company_id"),
                row.get("year"),
                row.get("annual_report"),
            )

            tasks.append(future)

        for future in as_completed(tasks):

            result = future.result()

            if result is not None:
                failures.append(result)

    return failures


# =========================================================
# DQ-14
# EPS SIGN CONSISTENCY
# =========================================================


def validate_eps_sign(
    df,
):
    """Validate eps sign."""
    failures = []

    required = {
        "net_profit",
        "eps",
    }

    if not required.issubset(df.columns):
        return failures

    for idx, row in df.iterrows():

        net_profit = pd.to_numeric(
            row.get("net_profit"),
            errors="coerce",
        )

        eps = pd.to_numeric(
            row.get("eps"),
            errors="coerce",
        )

        if pd.isna(net_profit) or pd.isna(eps):
            continue

        if net_profit > 0 and eps <= 0:

            failures.append(
                make_failure(
                    rule_id="DQ-14",
                    table="profitandloss",
                    severity="WARNING",
                    message=(
                        "EPS sign mismatch: " f"net_profit={net_profit}, " f"eps={eps}"
                    ),
                    action=("Manual analyst review"),
                    row_index=idx,
                    company_id=row.get("company_id"),
                    year=row.get("year"),
                )
            )

    return failures


# =========================================================
# DQ-15
# STRICT BALANCE SHEET EQUALITY
# INFORMATIONAL ONLY
# =========================================================


def generate_dq15_balance_info(
    df,
):
    """Generate dq15 balance info."""
    info_rows = []

    required = {
        "total_assets",
        "total_liabilities",
    }

    if not required.issubset(df.columns):
        return pd.DataFrame()

    for idx, row in df.iterrows():

        assets = pd.to_numeric(
            row.get("total_assets"),
            errors="coerce",
        )

        liabilities = pd.to_numeric(
            row.get("total_liabilities"),
            errors="coerce",
        )

        if pd.isna(assets) or pd.isna(liabilities):
            continue

        strict_match = assets == liabilities

        info_rows.append(
            {
                "rule_id": "DQ-15",
                "table": "balancesheet",
                "severity": "INFO",
                "row_index": idx,
                "company_id": row.get("company_id"),
                "year": row.get("year"),
                "total_assets": assets,
                "total_liabilities": liabilities,
                "strict_match": strict_match,
                "difference": (assets - liabilities),
            }
        )

    result = pd.DataFrame(info_rows)

    return result


# =========================================================
# DQ-16
# COVERAGE CHECK
# =========================================================


def validate_coverage(
    companies,
    datasets,
):
    """Validate coverage."""
    failures = []

    required_tables = [
        "profitandloss",
        "balancesheet",
        "cashflow",
    ]

    company_ids = companies["id"].dropna().unique()

    for company_id in company_ids:

        for table_name in required_tables:

            df = datasets[table_name]

            company_rows = df[df["company_id"] == company_id]

            year_count = company_rows["year"].dropna().nunique()

            if year_count < 5:

                failures.append(
                    make_failure(
                        rule_id="DQ-16",
                        table=table_name,
                        severity="WARNING",
                        message=("Insufficient history: " f"{year_count} years"),
                        action=(
                            "Exclude from long-term "
                            "CAGR if coverage "
                            "is insufficient"
                        ),
                        company_id=company_id,
                        year=None,
                    )
                )

    return failures


# =========================================================
# SAVE VALIDATION FAILURES
# =========================================================


def save_failures(
    failures,
):
    """Save failures."""
    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    columns = [
        "rule_id",
        "table",
        "severity",
        "status",
        "message",
        "action",
        "row_index",
        "company_id",
        "year",
    ]

    result = pd.DataFrame(
        failures,
        columns=columns,
    )

    result.to_csv(
        FAILURE_FILE,
        index=False,
    )

    return result


# =========================================================
# MAIN VALIDATION PIPELINE
# =========================================================


def run_validation():
    """Run validation."""
    logger.info("Loading normalized datasets")

    core = load_core_datasets()

    supplementary = load_supplementary_datasets()

    datasets = {
        **core,
        **supplementary,
    }

    failures = []

    companies = datasets["companies"]

    valid_company_ids = set(companies["id"].dropna().tolist())

    # =====================================================
    # DQ-01
    # =====================================================

    failures.extend(
        validate_pk_uniqueness(
            "companies",
            companies,
            ["id"],
        )
    )

    # =====================================================
    # DQ-02
    # =====================================================

    for table_name in [
        "profitandloss",
        "balancesheet",
        "cashflow",
    ]:

        failures.extend(
            validate_company_year_uniqueness(
                table_name,
                datasets[table_name],
            )
        )

    # =====================================================
    # DQ-03
    # BEFORE FK CLEANUP
    # =====================================================

    for (
        table_name,
        df,
    ) in datasets.items():

        if table_name == "companies":
            continue

        failures.extend(
            validate_fk_integrity(
                table_name,
                df,
                valid_company_ids,
            )
        )

    # =====================================================
    # DQ-07
    # BEFORE INVALID YEAR CLEANUP
    # =====================================================

    for (
        table_name,
        df,
    ) in datasets.items():

        if "year" in df.columns:

            failures.extend(
                validate_year_format(
                    table_name,
                    df,
                )
            )

    # =====================================================
    # DQ-08
    # =====================================================

    for (
        table_name,
        df,
    ) in datasets.items():

        failures.extend(
            validate_ticker_format(
                table_name,
                df,
            )
        )

    # =====================================================
    # DQ-07 CLEANUP
    # =====================================================

    (
        datasets,
        year_rejections,
    ) = reject_invalid_year_rows(datasets)

    logger.info(
        "Rejected %s DQ-07 year rows",
        len(year_rejections),
    )

    # =====================================================
    # DQ-03 CLEANUP
    # =====================================================

    (
        cleaned_datasets,
        fk_rejections,
    ) = reject_orphan_company_ids(datasets)

    logger.info(
        "Rejected %s DQ-03 FK rows",
        len(fk_rejections),
    )

    # =====================================================
    # DQ-04
    # =====================================================

    failures.extend(validate_balance_sheet(cleaned_datasets["balancesheet"]))

    # =====================================================
    # DQ-05
    # =====================================================

    failures.extend(validate_opm(cleaned_datasets["profitandloss"]))

    # =====================================================
    # DQ-06
    # =====================================================

    bank_tickers = get_bank_tickers(
        cleaned_datasets["companies"],
        cleaned_datasets["sectors"],
    )

    failures.extend(
        validate_positive_sales(
            cleaned_datasets["profitandloss"],
            bank_tickers,
        )
    )

    # =====================================================
    # DQ-09
    # =====================================================

    failures.extend(validate_net_cash(cleaned_datasets["cashflow"]))

    # =====================================================
    # DQ-10
    # =====================================================

    failures.extend(validate_fixed_assets(cleaned_datasets["balancesheet"]))

    # =====================================================
    # DQ-11
    # =====================================================

    failures.extend(validate_tax_rate(cleaned_datasets["profitandloss"]))

    # =====================================================
    # DQ-12
    # =====================================================

    failures.extend(validate_dividend_payout(cleaned_datasets["profitandloss"]))

    # =====================================================
    # DQ-13
    # =====================================================

    failures.extend(validate_document_urls(cleaned_datasets["documents"]))

    # =====================================================
    # DQ-14
    # =====================================================

    failures.extend(validate_eps_sign(cleaned_datasets["profitandloss"]))

    # =====================================================
    # DQ-15
    # INFORMATIONAL REPORT
    # =====================================================

    dq15_info = generate_dq15_balance_info(cleaned_datasets["balancesheet"])

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    dq15_info.to_csv(
        DQ15_INFO_FILE,
        index=False,
    )

    # =====================================================
    # DQ-16
    # =====================================================

    failures.extend(
        validate_coverage(
            cleaned_datasets["companies"],
            cleaned_datasets,
        )
    )

    # =====================================================
    # SAVE FAILURE REPORT
    # =====================================================

    result = save_failures(failures)

    print()
    print("=" * 70)
    print("VALIDATION SUMMARY — DQ-01 TO DQ-16")
    print("=" * 70)

    print(f"Total violations logged: " f"{len(result)}")

    if not result.empty:

        print()
        print("Violations by rule:")

        print(result["rule_id"].value_counts().sort_index())

        print()
        print("Violations by severity:")

        print(result["severity"].value_counts())

        print()
        print("Violations by status:")

        print(result["status"].value_counts())

        unresolved_critical = result[
            (result["severity"] == "CRITICAL") & (result["status"] == "OPEN_BLOCKER")
        ]

        print()
        print("UNRESOLVED CRITICAL " "FAILURES: " f"{len(unresolved_critical)}")

    else:

        print("No violations found.")

    if not dq15_info.empty:

        strict_matches = dq15_info["strict_match"].sum()

        strict_mismatches = len(dq15_info) - strict_matches

        print()
        print("DQ-15 INFORMATIONAL:")

        print("Strict balance matches: " f"{strict_matches}")

        print("Strict balance mismatches: " f"{strict_mismatches}")

    print()
    print("Validation failures saved: " f"{FAILURE_FILE}")

    print("DQ-15 info saved: " f"{DQ15_INFO_FILE}")


# =========================================================
# ENTRY POINT
# =========================================================

if __name__ == "__main__":
    run_validation()
