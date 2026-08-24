import re
import pandas as pd


def normalize_ticker(value):
    """
    Normalize company ticker values.
    """
    if value is None:
        return None

    if pd.isna(value):
        return None

    ticker = str(value).strip().upper()

    if ticker == "":
        return None

    return ticker


def normalize_year(value):
    """
    Normalize supported year labels to YYYY-MM.

    Examples:
        Mar-23       -> 2023-03
        Mar 2023     -> 2023-03
        March-2023   -> 2023-03
        Dec 2022     -> 2022-12
        Sep 2024     -> 2024-09
        FY23         -> 2023-03
        2023         -> 2023-03
        2023.0       -> 2023-03

    Unsupported period labels such as TTM remain invalid
    and are handled by DQ-07.
    """
    if value is None or pd.isna(value):
        return None

    # -----------------------------------------
    # Integer / float year values
    # -----------------------------------------

    if isinstance(value, (int, float)):
        numeric_value = float(value)

        # Only accept whole-number years.
        if numeric_value.is_integer():
            year = int(numeric_value)

            if 1900 <= year <= 2100:
                return f"{year}-03"

        raise ValueError(
            f"Unsupported numeric year format: {value}"
        )

    value = str(value).strip()

    if not value:
        return None

    # -----------------------------------------
    # Already normalized YYYY-MM
    # -----------------------------------------

    match = re.fullmatch(
        r"(\d{4})-(\d{2})",
        value,
    )

    if match:
        year = int(match.group(1))
        month = int(match.group(2))

        if 1 <= month <= 12:
            return f"{year}-{month:02d}"

        raise ValueError(
            f"Invalid month in year format: {value}"
        )

    # -----------------------------------------
    # Numeric string year
    # -----------------------------------------

    match = re.fullmatch(
        r"\d{4}",
        value,
    )

    if match:
        year = int(value)

        if 1900 <= year <= 2100:
            return f"{year}-03"

    # Numeric string generated from Excel float:
    # 2023.0
    match = re.fullmatch(
        r"(\d{4})\.0",
        value,
    )

    if match:
        year = int(match.group(1))
        return f"{year}-03"

    # -----------------------------------------
    # FY23 / FY2023
    # -----------------------------------------

    match = re.fullmatch(
        r"(?i)FY\s*(\d{2}|\d{4})",
        value,
    )

    if match:
        year = int(match.group(1))

        if year < 100:
            year += 2000

        return f"{year}-03"

    # -----------------------------------------
    # Month-year formats
    # -----------------------------------------

    month_map = {
        "jan": 1,
        "january": 1,
        "feb": 2,
        "february": 2,
        "mar": 3,
        "march": 3,
        "apr": 4,
        "april": 4,
        "may": 5,
        "jun": 6,
        "june": 6,
        "jul": 7,
        "july": 7,
        "aug": 8,
        "august": 8,
        "sep": 9,
        "sept": 9,
        "september": 9,
        "oct": 10,
        "october": 10,
        "nov": 11,
        "november": 11,
        "dec": 12,
        "december": 12,
    }

    match = re.fullmatch(
        r"(?i)([A-Za-z]+)[\s\-]*(\d{2}|\d{4})",
        value,
    )

    if match:
        month_text = match.group(1).lower()
        year = int(match.group(2))

        if month_text not in month_map:
            raise ValueError(
                f"Unsupported month: {month_text}"
            )

        if year < 100:
            year += 2000

        month = month_map[month_text]

        return f"{year}-{month:02d}"

    # -----------------------------------------
    # Unsupported period
    # -----------------------------------------

    raise ValueError(
        f"Unsupported year format: {value}"
    )