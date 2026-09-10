from __future__ import annotations

import sqlite3
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DB_PATH = PROJECT_ROOT / "db" / "nifty100.db"
OUTPUT_PATH = PROJECT_ROOT / "output" / "pros_cons_generated.csv"

MIN_CONFIDENCE = 60.0


PRO_TEXT = {
    "PRO_01": "Consistently high return on equity above 20% demonstrates exceptional capital efficiency",
    "PRO_02": "Strong free cash flow generation over 5 years signals healthy business fundamentals",
    "PRO_03": "Debt-free balance sheet provides financial flexibility and eliminates interest burden",
    "PRO_04": "Revenue growing at above 15% CAGR over 5 years reflects strong business momentum",
    "PRO_05": "Operating profit margin above 25% indicates strong pricing power and cost discipline",
    "PRO_06": "Net profit compounding at above 20% over 5 years creates significant shareholder value",
    "PRO_07": "Very high interest coverage ratio reflects negligible financial stress from debt servicing",
    "PRO_08": "Consistent dividend yield above 2% backed by positive free cash flow",
    "PRO_09": "Earnings per share growing above 15% CAGR indicates strong earnings quality and compounding",
    "PRO_10": "Return on equity improving for 3 consecutive years shows strengthening business quality",
    "PRO_11": "Revenue growing slower than profits shows improving operating leverage and scale benefits",
    "PRO_12": "Growing asset base funded by internal accruals reflects self-sustaining growth",
}


CON_TEXT = {
    "CON_01": "Debt-to-equity ratio of {value:.2f} is elevated for a non-financial company and warrants monitoring",
    "CON_02": "Free cash flow negative for 3 consecutive years raises concern about cash generation quality",
    "CON_03": "Operating margins declining for 3 consecutive years suggest pricing or cost pressure",
    "CON_04": "Company reported a net loss in the most recent financial year",
    "CON_05": "Revenue contraction over 2 consecutive years indicates demand weakness or market share loss",
    "CON_06": "Interest coverage ratio below 1.5x indicates the company is at risk of not meeting its debt obligations",
    "CON_07": "Dividend payout ratio above 100% means the company is paying dividends from reserves, which is unsustainable",
    "CON_08": "Rising debt-to-equity ratio over 3 years suggests increasing financial leverage risk",
    "CON_09": "Earnings per share declining for 3 consecutive years reflects deteriorating profitability",
    "CON_10": "Return on capital employed below 10% suggests the business is not generating sufficient returns on invested capital",
    "CON_11": "Net debt exceeding 3 times EBITDA is a high leverage ratio and limits financial flexibility",
    "CON_12": "Revenue growing at below 5% over 5 years lags inflation and suggests limited business momentum",
}


def clamp_confidence(value: float) -> float:
    """Clamp confidence."""
    return round(float(np.clip(value, 61.0, 100.0)), 1)


def annual_rows(df: pd.DataFrame) -> pd.DataFrame:
    """
    Prefer March full-year observations for trend rules.
    """
    if df.empty:
        return df.copy()

    result = df.copy()
    result["year"] = result["year"].astype(str)

    march = result[result["year"].str.endswith("-03")].copy()

    if not march.empty:
        result = march

    result["_year_dt"] = pd.to_datetime(
        result["year"],
        format="%Y-%m",
        errors="coerce",
    )

    return result.sort_values("_year_dt")


def latest_annual(df: pd.DataFrame) -> pd.Series | None:
    """Return the latest annual financial row."""
    result = annual_rows(df)

    if result.empty:
        return None

    return result.iloc[-1]


def numeric_series(
    df: pd.DataFrame,
    column: str,
) -> pd.Series:
    """Return values as a numeric series."""
    result = annual_rows(df)

    if result.empty or column not in result.columns:
        return pd.Series(dtype=float)

    return pd.to_numeric(
        result[column],
        errors="coerce",
    ).dropna()


def last_n(
    df: pd.DataFrame,
    column: str,
    n: int,
) -> list[float]:
    """Handle last n."""
    values = numeric_series(df, column)

    if len(values) < n:
        return []

    return values.tail(n).astype(float).tolist()


def strictly_increasing(values: list[float]) -> bool:
    """Return whether values are strictly increasing."""
    return len(values) >= 2 and all(
        values[i] > values[i - 1] for i in range(1, len(values))
    )


def strictly_decreasing(values: list[float]) -> bool:
    """Return whether values are strictly decreasing."""
    return len(values) >= 2 and all(
        values[i] < values[i - 1] for i in range(1, len(values))
    )


def load_data() -> dict[str, pd.DataFrame]:
    """Load data."""
    if not DB_PATH.exists():
        raise FileNotFoundError(f"Database not found: {DB_PATH}")

    with sqlite3.connect(DB_PATH) as conn:
        data = {
            "companies": pd.read_sql_query(
                "SELECT * FROM companies",
                conn,
            ),
            "sectors": pd.read_sql_query(
                "SELECT * FROM sectors",
                conn,
            ),
            "ratios": pd.read_sql_query(
                "SELECT * FROM financial_ratios",
                conn,
            ),
            "pl": pd.read_sql_query(
                "SELECT * FROM profitandloss",
                conn,
            ),
            "bs": pd.read_sql_query(
                "SELECT * FROM balancesheet",
                conn,
            ),
            "cf": pd.read_sql_query(
                "SELECT * FROM cashflow",
                conn,
            ),
            "market": pd.read_sql_query(
                "SELECT * FROM market_cap",
                conn,
            ),
        }

    for key in [
        "sectors",
        "ratios",
        "pl",
        "bs",
        "cf",
        "market",
    ]:
        if "company_id" in data[key].columns:
            data[key]["company_id"] = (
                data[key]["company_id"].astype(str).str.strip().str.upper()
            )

    data["companies"]["id"] = (
        data["companies"]["id"].astype(str).str.strip().str.upper()
    )

    return data


def latest_market_row(df: pd.DataFrame) -> pd.Series | None:
    """Handle latest market row."""
    if df.empty:
        return None

    temp = df.copy()

    temp["_year_dt"] = pd.to_datetime(
        temp["year"],
        format="%Y-%m",
        errors="coerce",
    )

    temp = temp.sort_values("_year_dt")

    return temp.iloc[-1]


def add_signal(
    rows: list[dict],
    company_id: str,
    signal_type: str,
    rule_id: str,
    text: str,
    confidence: float,
) -> None:
    """Add signal."""
    confidence = clamp_confidence(confidence)

    if confidence <= MIN_CONFIDENCE:
        return

    rows.append(
        {
            "company_id": company_id,
            "type": signal_type,
            "rule_id": rule_id,
            "text": text,
            "confidence_pct": confidence,
        }
    )


def evaluate_company(
    ticker: str,
    data: dict[str, pd.DataFrame],
) -> list[dict]:
    """Evaluate company."""
    rows: list[dict] = []

    ratios = data["ratios"][data["ratios"]["company_id"] == ticker]

    pl = data["pl"][data["pl"]["company_id"] == ticker]

    bs = data["bs"][data["bs"]["company_id"] == ticker]

    data["cf"][data["cf"]["company_id"] == ticker]

    market = data["market"][data["market"]["company_id"] == ticker]

    sector_rows = data["sectors"][data["sectors"]["company_id"] == ticker]

    sector = ""

    if not sector_rows.empty:
        sector = str(
            sector_rows.iloc[-1].get(
                "broad_sector",
                "",
            )
        ).strip()

    is_financial = sector.lower() == "financials"

    latest_ratio = latest_annual(ratios)
    latest_pl = latest_annual(pl)

    latest_market = latest_market_row(market)

    # =========================================================
    # PRO 01 — ROE > 20 sustained for 3+ years
    # =========================================================
    roe3 = last_n(
        ratios,
        "return_on_equity_pct",
        3,
    )

    if len(roe3) == 3 and all(x > 20 for x in roe3):
        avg_roe = np.mean(roe3)

        add_signal(
            rows,
            ticker,
            "pro",
            "PRO_01",
            PRO_TEXT["PRO_01"],
            70 + min((avg_roe - 20) * 1.5, 30),
        )

    # =========================================================
    # PRO 02 — FCF positive for 5 consecutive years
    # =========================================================
    fcf5 = last_n(
        ratios,
        "free_cash_flow_cr",
        5,
    )

    if len(fcf5) == 5 and all(x > 0 for x in fcf5):
        add_signal(
            rows,
            ticker,
            "pro",
            "PRO_02",
            PRO_TEXT["PRO_02"],
            90,
        )

    # =========================================================
    # Latest ratio values
    # =========================================================
    if latest_ratio is not None:

        de = pd.to_numeric(
            pd.Series([latest_ratio.get("debt_to_equity")]),
            errors="coerce",
        ).iloc[0]

        pd.to_numeric(
            pd.Series([latest_ratio.get("return_on_equity_pct")]),
            errors="coerce",
        ).iloc[0]

        roce = pd.to_numeric(
            pd.Series([latest_ratio.get("return_on_capital_employed_pct")]),
            errors="coerce",
        ).iloc[0]

        opm = pd.to_numeric(
            pd.Series([latest_ratio.get("operating_profit_margin_pct")]),
            errors="coerce",
        ).iloc[0]

        icr = pd.to_numeric(
            pd.Series([latest_ratio.get("interest_coverage")]),
            errors="coerce",
        ).iloc[0]

        fcf = pd.to_numeric(
            pd.Series([latest_ratio.get("free_cash_flow_cr")]),
            errors="coerce",
        ).iloc[0]

        revenue_cagr5 = pd.to_numeric(
            pd.Series([latest_ratio.get("revenue_cagr_5yr")]),
            errors="coerce",
        ).iloc[0]

        pat_cagr5 = pd.to_numeric(
            pd.Series([latest_ratio.get("pat_cagr_5yr")]),
            errors="coerce",
        ).iloc[0]

        eps_cagr5 = pd.to_numeric(
            pd.Series([latest_ratio.get("eps_cagr_5yr")]),
            errors="coerce",
        ).iloc[0]

        net_debt = pd.to_numeric(
            pd.Series([latest_ratio.get("net_debt_cr")]),
            errors="coerce",
        ).iloc[0]

        # PRO 03
        if pd.notna(de) and abs(de) < 1e-9:
            add_signal(
                rows,
                ticker,
                "pro",
                "PRO_03",
                PRO_TEXT["PRO_03"],
                95,
            )

        # PRO 04
        if pd.notna(revenue_cagr5) and revenue_cagr5 > 15:
            add_signal(
                rows,
                ticker,
                "pro",
                "PRO_04",
                PRO_TEXT["PRO_04"],
                70
                + min(
                    (revenue_cagr5 - 15) * 2,
                    30,
                ),
            )

        # PRO 05
        if pd.notna(opm) and opm > 25:
            add_signal(
                rows,
                ticker,
                "pro",
                "PRO_05",
                PRO_TEXT["PRO_05"],
                70
                + min(
                    (opm - 25) * 1.5,
                    30,
                ),
            )

        # PRO 06
        if pd.notna(pat_cagr5) and pat_cagr5 > 20:
            add_signal(
                rows,
                ticker,
                "pro",
                "PRO_06",
                PRO_TEXT["PRO_06"],
                70
                + min(
                    (pat_cagr5 - 20) * 1.5,
                    30,
                ),
            )

        # PRO 07
        if (pd.notna(de) and abs(de) < 1e-9) or (pd.notna(icr) and icr > 10):
            confidence = (
                95
                if (pd.notna(de) and abs(de) < 1e-9)
                else (70 + min((icr - 10) * 1.0, 30))
            )

            add_signal(
                rows,
                ticker,
                "pro",
                "PRO_07",
                PRO_TEXT["PRO_07"],
                confidence,
            )

        # PRO 09
        if pd.notna(eps_cagr5) and eps_cagr5 > 15:
            add_signal(
                rows,
                ticker,
                "pro",
                "PRO_09",
                PRO_TEXT["PRO_09"],
                70
                + min(
                    (eps_cagr5 - 15) * 2,
                    30,
                ),
            )

        # PRO 11
        # Sprint text describes profits growing faster than revenue.
        if (
            pd.notna(revenue_cagr5)
            and pd.notna(pat_cagr5)
            and pat_cagr5 > revenue_cagr5
        ):
            spread = pat_cagr5 - revenue_cagr5

            add_signal(
                rows,
                ticker,
                "pro",
                "PRO_11",
                PRO_TEXT["PRO_11"],
                65 + min(spread * 3, 35),
            )

        # CON 01
        if not is_financial and pd.notna(de) and de > 2.0:
            add_signal(
                rows,
                ticker,
                "con",
                "CON_01",
                CON_TEXT["CON_01"].format(value=de),
                70
                + min(
                    (de - 2) * 10,
                    30,
                ),
            )

        # CON 06
        if pd.notna(icr) and icr < 1.5:
            add_signal(
                rows,
                ticker,
                "con",
                "CON_06",
                CON_TEXT["CON_06"],
                75
                + min(
                    (1.5 - icr) * 15,
                    25,
                ),
            )

        # CON 10
        if pd.notna(roce) and roce < 10:
            add_signal(
                rows,
                ticker,
                "con",
                "CON_10",
                CON_TEXT["CON_10"],
                65
                + min(
                    (10 - roce) * 3,
                    35,
                ),
            )

        # CON 12
        if pd.notna(revenue_cagr5) and revenue_cagr5 < 5:
            add_signal(
                rows,
                ticker,
                "con",
                "CON_12",
                CON_TEXT["CON_12"],
                70
                + min(
                    (5 - revenue_cagr5) * 3,
                    30,
                ),
            )

    # =========================================================
    # PRO 08 — Dividend yield >2 and FCF positive
    # =========================================================
    if latest_market is not None and latest_ratio is not None:
        div_yield = pd.to_numeric(
            pd.Series([latest_market.get("dividend_yield_pct")]),
            errors="coerce",
        ).iloc[0]

        if pd.notna(div_yield) and div_yield > 2 and pd.notna(fcf) and fcf > 0:
            add_signal(
                rows,
                ticker,
                "pro",
                "PRO_08",
                PRO_TEXT["PRO_08"],
                70
                + min(
                    (div_yield - 2) * 8,
                    30,
                ),
            )

    # =========================================================
    # PRO 10 — ROE improving 3 consecutive years
    # =========================================================
    roe_trend = last_n(
        ratios,
        "return_on_equity_pct",
        3,
    )

    if len(roe_trend) == 3 and strictly_increasing(roe_trend):
        improvement = roe_trend[-1] - roe_trend[0]

        add_signal(
            rows,
            ticker,
            "pro",
            "PRO_10",
            PRO_TEXT["PRO_10"],
            65
            + min(
                improvement * 4,
                35,
            ),
        )

    # =========================================================
    # PRO 12 — Assets growing while borrowings decline
    # =========================================================
    assets2 = last_n(
        bs,
        "total_assets",
        2,
    )

    debt2 = last_n(
        bs,
        "borrowings",
        2,
    )

    if (
        len(assets2) == 2
        and len(debt2) == 2
        and assets2[-1] > assets2[-2]
        and debt2[-1] < debt2[-2]
    ):
        add_signal(
            rows,
            ticker,
            "pro",
            "PRO_12",
            PRO_TEXT["PRO_12"],
            80,
        )

    # =========================================================
    # CON 02 — FCF negative 3 consecutive years
    # =========================================================
    fcf3 = last_n(
        ratios,
        "free_cash_flow_cr",
        3,
    )

    if len(fcf3) == 3 and all(x < 0 for x in fcf3):
        add_signal(
            rows,
            ticker,
            "con",
            "CON_02",
            CON_TEXT["CON_02"],
            90,
        )

    # =========================================================
    # CON 03 — OPM declining for 3 years
    # =========================================================
    opm3 = last_n(
        ratios,
        "operating_profit_margin_pct",
        3,
    )

    if len(opm3) == 3 and strictly_decreasing(opm3):
        decline = opm3[0] - opm3[-1]

        add_signal(
            rows,
            ticker,
            "con",
            "CON_03",
            CON_TEXT["CON_03"],
            65
            + min(
                decline * 4,
                35,
            ),
        )

    # =========================================================
    # CON 04 — Latest net profit negative
    # =========================================================
    if latest_pl is not None:
        net_profit = pd.to_numeric(
            pd.Series([latest_pl.get("net_profit")]),
            errors="coerce",
        ).iloc[0]

        dividend_payout = pd.to_numeric(
            pd.Series([latest_pl.get("dividend_payout")]),
            errors="coerce",
        ).iloc[0]

        if pd.notna(net_profit) and net_profit < 0:
            add_signal(
                rows,
                ticker,
                "con",
                "CON_04",
                CON_TEXT["CON_04"],
                95,
            )

        # CON 07
        if pd.notna(dividend_payout) and dividend_payout > 100:
            add_signal(
                rows,
                ticker,
                "con",
                "CON_07",
                CON_TEXT["CON_07"],
                80
                + min(
                    (dividend_payout - 100) / 5,
                    20,
                ),
            )

    # =========================================================
    # CON 05 — Revenue declining for 2+ consecutive years
    # =========================================================
    sales3 = last_n(
        pl,
        "sales",
        3,
    )

    if len(sales3) == 3 and sales3[-1] < sales3[-2] < sales3[-3]:
        decline_pct = (
            ((sales3[0] - sales3[-1]) / abs(sales3[0]) * 100) if sales3[0] != 0 else 0
        )

        add_signal(
            rows,
            ticker,
            "con",
            "CON_05",
            CON_TEXT["CON_05"],
            70
            + min(
                max(decline_pct, 0),
                30,
            ),
        )

    # =========================================================
    # CON 08 — D/E rising for 3 years
    # =========================================================
    de3 = last_n(
        ratios,
        "debt_to_equity",
        3,
    )

    if len(de3) == 3 and strictly_increasing(de3):
        rise = de3[-1] - de3[0]

        add_signal(
            rows,
            ticker,
            "con",
            "CON_08",
            CON_TEXT["CON_08"],
            65
            + min(
                rise * 15,
                35,
            ),
        )

    # =========================================================
    # CON 09 — EPS declining for 3 years
    # =========================================================
    eps3 = last_n(
        pl,
        "eps",
        3,
    )

    if len(eps3) == 3 and strictly_decreasing(eps3):
        add_signal(
            rows,
            ticker,
            "con",
            "CON_09",
            CON_TEXT["CON_09"],
            80,
        )

    # =========================================================
    # CON 11 — Net Debt > 3x EBITDA
    #
    # EBITDA estimated from:
    # enterprise_value / EV-EBITDA
    # =========================================================
    if latest_market is not None and latest_ratio is not None:
        ev = pd.to_numeric(
            pd.Series([latest_market.get("enterprise_value_crore")]),
            errors="coerce",
        ).iloc[0]

        ev_ebitda = pd.to_numeric(
            pd.Series([latest_market.get("ev_ebitda")]),
            errors="coerce",
        ).iloc[0]

        if (
            pd.notna(net_debt)
            and pd.notna(ev)
            and pd.notna(ev_ebitda)
            and ev > 0
            and ev_ebitda > 0
        ):
            estimated_ebitda = ev / ev_ebitda

            if estimated_ebitda > 0:
                net_debt_ebitda = net_debt / estimated_ebitda

                if net_debt_ebitda > 3:
                    add_signal(
                        rows,
                        ticker,
                        "con",
                        "CON_11",
                        CON_TEXT["CON_11"],
                        75
                        + min(
                            (net_debt_ebitda - 3) * 8,
                            25,
                        ),
                    )

    return rows


def generate() -> pd.DataFrame:
    """Handle generate."""
    data = load_data()

    tickers = sorted(data["companies"]["id"].dropna().unique().tolist())

    rows: list[dict] = []

    for ticker in tickers:
        rows.extend(
            evaluate_company(
                ticker,
                data,
            )
        )

    output = pd.DataFrame(
        rows,
        columns=[
            "company_id",
            "type",
            "rule_id",
            "text",
            "confidence_pct",
        ],
    )

    if not output.empty:
        output = (
            output.drop_duplicates(
                subset=[
                    "company_id",
                    "type",
                    "rule_id",
                ]
            )
            .sort_values(
                [
                    "company_id",
                    "type",
                    "confidence_pct",
                ],
                ascending=[
                    True,
                    True,
                    False,
                ],
            )
            .reset_index(drop=True)
        )

    return output


def validate_coverage(
    output: pd.DataFrame,
) -> tuple[list[str], list[str]]:
    """Validate coverage."""
    data = load_data()

    companies = set(data["companies"]["id"].dropna().astype(str).str.upper())

    pros = set(
        output.loc[
            output["type"] == "pro",
            "company_id",
        ]
    )

    cons = set(
        output.loc[
            output["type"] == "con",
            "company_id",
        ]
    )

    missing_pro = sorted(companies - pros)

    missing_con = sorted(companies - cons)

    return missing_pro, missing_con


def main() -> None:
    """Run the module entry point."""
    print("=" * 80)
    print("SPRINT 5 — DAY 30 AUTO PROS / CONS GENERATOR")
    print("=" * 80)

    output = generate()

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    output.to_csv(
        OUTPUT_PATH,
        index=False,
    )

    missing_pro, missing_con = validate_coverage(output)

    print(f"\nGenerated signals: {len(output)}")

    if not output.empty:
        print("\nTYPE COUNTS:")
        print(output["type"].value_counts().to_string())

        print("\nRULE COUNTS:")
        print(output["rule_id"].value_counts().sort_index().to_string())

        print(
            "\nCompanies with at least one PRO:",
            output.loc[
                output["type"] == "pro",
                "company_id",
            ].nunique(),
        )

        print(
            "Companies with at least one CON:",
            output.loc[
                output["type"] == "con",
                "company_id",
            ].nunique(),
        )

    print(f"\nCompanies missing PRO: " f"{len(missing_pro)}")
    print(", ".join(missing_pro) if missing_pro else "None")

    print(f"\nCompanies missing CON: " f"{len(missing_con)}")
    print(", ".join(missing_con) if missing_con else "None")

    print(f"\nOutput: {OUTPUT_PATH}")

    print("\nDAY 30 RULE ENGINE: PASS")


if __name__ == "__main__":
    main()
