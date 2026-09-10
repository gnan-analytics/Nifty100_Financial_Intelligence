import pytest

from src.etl.normaliser import normalize_ticker, normalize_year


@pytest.mark.parametrize(
    "raw, expected",
    [
        ("TCS", "TCS"),
        (" tcs ", "TCS"),
        ("hdfcbank", "HDFCBANK"),
        (" INFY", "INFY"),
        ("reliance ", "RELIANCE"),
        ("  abb  ", "ABB"),
        ("ICICIBANK", "ICICIBANK"),
        ("axisbank", "AXISBANK"),
        ("SBIN", "SBIN"),
        ("lt", "LT"),
        ("", None),
        ("   ", None),
        (None, None),
    ],
)
def test_normalize_ticker(raw, expected):
    assert normalize_ticker(raw) == expected


@pytest.mark.parametrize(
    "raw, expected",
    [
        ("Mar-23", "2023-03"),
        ("Mar-24", "2024-03"),
        ("Mar-22", "2022-03"),
        ("Mar-2024", "2024-03"),
        ("Mar 2023", "2023-03"),
        ("March-2023", "2023-03"),
        ("FY23", "2023-03"),
        ("FY24", "2024-03"),
        ("Dec-22", "2022-12"),
        ("Dec-2024", "2024-12"),
        (2024, "2024-03"),
        (2023, "2023-03"),
        (2020, "2020-03"),
        (2015, "2015-03"),
        (2010, "2010-03"),
        ("2023-03", "2023-03"),
        (None, None),
        ("", None),
        ("   ", None),
    ],
)
def test_normalize_year(raw, expected):
    assert normalize_year(raw) == expected


@pytest.mark.parametrize(
    "raw",
    [
        "hello",
        "2023-25",
        "xyz",
        "ABC-24",
    ],
)
def test_normalize_year_invalid(raw):
    with pytest.raises(ValueError):
        normalize_year(raw)
