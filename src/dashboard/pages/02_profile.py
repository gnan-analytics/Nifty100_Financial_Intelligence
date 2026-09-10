import html
import re

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

from src.dashboard.utils.db import (
    get_bs,
    get_cf,
    get_companies,
    get_company,
    get_pl,
    get_pros_cons,
    get_ratios,
    get_sector_for_company,
)

st.title("🏢 Company Profile")

st.caption("Company fundamentals, profitability " "and historical trends")


# ------------------------------------------------------------
# Helpers
# ------------------------------------------------------------


def clean_number(
    value,
):
    """Handle clean number."""
    try:
        if value is None:
            return None

        value = float(value)

        if np.isnan(value):
            return None

        return value

    except Exception:
        return None


def format_metric(
    value,
    suffix="",
    decimals=1,
):
    """Format metric."""
    value = clean_number(value)

    if value is None:
        return "N/A"

    return f"{value:,.{decimals}f}" f"{suffix}"


def latest_non_null(
    dataframe,
    column,
):
    """Handle latest non null."""
    if dataframe.empty or column not in dataframe.columns:
        return None

    values = pd.to_numeric(
        dataframe[column],
        errors="coerce",
    ).dropna()

    if values.empty:
        return None

    return values.iloc[-1]


def split_items(
    value,
):
    """Split items."""
    if value is None:
        return []

    if isinstance(
        value,
        float,
    ) and pd.isna(value):
        return []

    text = str(value).strip()

    if not text:
        return []

    parts = re.split(
        r"[\n;•]+",
        text,
    )

    return [part.strip(" -\t") for part in parts if part.strip(" -\t")]


# ------------------------------------------------------------
# Search + Autocomplete
# ------------------------------------------------------------

companies = get_companies()

search_text = st.text_input(
    "Search company name or ticker",
    placeholder=("Example: TCS, Infosys, Reliance..."),
)

filtered = companies.copy()

if search_text.strip():
    term = search_text.strip().lower()

    filtered = filtered[
        filtered["company_id"]
        .astype(str)
        .str.lower()
        .str.contains(
            term,
            regex=False,
        )
        | filtered["company_name"]
        .astype(str)
        .str.lower()
        .str.contains(
            term,
            regex=False,
        )
    ]

if filtered.empty:
    st.warning("Ticker not found — please try another")
    st.stop()


options = filtered[
    [
        "company_id",
        "company_name",
    ]
].copy()

options["label"] = (
    options["company_id"].astype(str) + " — " + options["company_name"].astype(str)
)

selected_label = st.selectbox(
    "Select company",
    options["label"].tolist(),
)

selected_row = options[options["label"] == selected_label].iloc[0]

ticker = selected_row["company_id"]


# ------------------------------------------------------------
# Load Company Data
# ------------------------------------------------------------

company = get_company(ticker)

sector = get_sector_for_company(ticker)

ratios = get_ratios(ticker)

pl = get_pl(ticker)

bs = get_bs(ticker)

cf = get_cf(ticker)

pros_cons = get_pros_cons(ticker)


if company.empty:
    st.warning("Ticker not found — please try another")
    st.stop()


company_row = company.iloc[0]


# ------------------------------------------------------------
# Company Card
# ------------------------------------------------------------

company_name = company_row.get(
    "company_name",
    ticker,
)

about = company_row.get(
    "about_company",
    "",
)

if about is None or pd.isna(about):
    about = "Company description unavailable."


broad_sector = "N/A"
sub_sector = "N/A"

if not sector.empty:
    sector_row = sector.iloc[0]

    broad_sector = sector_row.get(
        "broad_sector",
        "N/A",
    )

    sub_sector = sector_row.get(
        "sub_sector",
        "N/A",
    )


st.subheader(f"{company_name} ({ticker})")

c1, c2, c3 = st.columns([1, 1, 1])

c1.markdown(f"**Sector**  \n{broad_sector}")

c2.markdown(f"**Sub-sector**  \n{sub_sector}")

c3.markdown(f"**NSE Ticker**  \n{ticker}")

st.markdown(str(about))

st.divider()


# ------------------------------------------------------------
# Latest KPI Tiles
# ------------------------------------------------------------

roe = latest_non_null(
    ratios,
    "return_on_equity_pct",
)

roce = latest_non_null(
    ratios,
    "return_on_capital_employed_pct",
)

npm = latest_non_null(
    ratios,
    "net_profit_margin_pct",
)

de = latest_non_null(
    ratios,
    "debt_to_equity",
)

revenue_cagr = latest_non_null(
    ratios,
    "revenue_cagr_5yr",
)

fcf = latest_non_null(
    ratios,
    "free_cash_flow_cr",
)


m1, m2, m3, m4, m5, m6 = st.columns(6)

m1.metric(
    "ROE",
    format_metric(
        roe,
        "%",
    ),
)

m2.metric(
    "ROCE",
    format_metric(
        roce,
        "%",
    ),
)

m3.metric(
    "Net Profit Margin",
    format_metric(
        npm,
        "%",
    ),
)

m4.metric(
    "Debt / Equity",
    format_metric(
        de,
        "x",
        2,
    ),
)

m5.metric(
    "Revenue CAGR 5Y",
    format_metric(
        revenue_cagr,
        "%",
    ),
)

m6.metric(
    "Free Cash Flow",
    ("N/A" if clean_number(fcf) is None else f"₹{fcf:,.0f} Cr"),
)


# ------------------------------------------------------------
# Revenue + Net Profit Chart
# ------------------------------------------------------------

st.subheader("Revenue & Net Profit — 10 Year Trend")

if not pl.empty:
    pl_chart = pl.copy()

    pl_chart["year_sort"] = pd.to_datetime(
        pl_chart["year"].astype(str) + "-01",
        errors="coerce",
    )

    pl_chart = pl_chart.sort_values("year_sort").tail(10)

    fig = go.Figure()

    fig.add_trace(
        go.Bar(
            x=pl_chart["year"],
            y=pl_chart["sales"],
            name="Revenue",
        )
    )

    fig.add_trace(
        go.Bar(
            x=pl_chart["year"],
            y=pl_chart["net_profit"],
            name="Net Profit",
        )
    )

    fig.update_layout(
        barmode="group",
        height=480,
        xaxis_title="Year",
        yaxis_title="₹ Crore",
        margin=dict(
            l=20,
            r=20,
            t=40,
            b=20,
        ),
    )

    st.plotly_chart(
        fig,
        use_container_width=True,
    )

    if len(pl_chart) < 10:
        st.caption("Data available for only " f"{len(pl_chart)} periods.")
else:
    st.info("Revenue and profit history unavailable.")


# ------------------------------------------------------------
# ROE + ROCE Dual Axis Chart
# ------------------------------------------------------------

st.subheader("ROE & ROCE — 10 Year Trend")

if not ratios.empty:
    ratio_chart = ratios.copy()

    ratio_chart["year_sort"] = pd.to_datetime(
        ratio_chart["year"].astype(str) + "-01",
        errors="coerce",
    )

    ratio_chart = ratio_chart.sort_values("year_sort").tail(10)

    fig2 = make_subplots(specs=[[{"secondary_y": True}]])

    fig2.add_trace(
        go.Scatter(
            x=ratio_chart["year"],
            y=ratio_chart["return_on_equity_pct"],
            mode="lines+markers",
            name="ROE",
        ),
        secondary_y=False,
    )

    fig2.add_trace(
        go.Scatter(
            x=ratio_chart["year"],
            y=ratio_chart["return_on_capital_employed_pct"],
            mode="lines+markers",
            name="ROCE",
        ),
        secondary_y=True,
    )

    fig2.update_yaxes(
        title_text="ROE (%)",
        secondary_y=False,
    )

    fig2.update_yaxes(
        title_text="ROCE (%)",
        secondary_y=True,
    )

    fig2.update_layout(
        height=480,
        xaxis_title="Year",
        margin=dict(
            l=20,
            r=20,
            t=40,
            b=20,
        ),
    )

    st.plotly_chart(
        fig2,
        use_container_width=True,
    )

    if len(ratio_chart) < 10:
        st.caption("Data available for only " f"{len(ratio_chart)} periods.")
else:
    st.info("ROE and ROCE history unavailable.")


# ------------------------------------------------------------
# Pros and Cons
# ------------------------------------------------------------

st.subheader("Pros & Cons")

pros = []
cons = []

if not pros_cons.empty:
    for _, row in pros_cons.iterrows():
        pros.extend(split_items(row.get("pros")))

        cons.extend(split_items(row.get("cons")))


pros_col, cons_col = st.columns(2)

with pros_col:
    st.markdown("### ✅ Pros")

    if pros:
        for item in pros:
            safe = html.escape(item)

            st.markdown(
                f"""
                <div style="
                    padding:10px 12px;
                    margin-bottom:8px;
                    border-radius:8px;
                    background:rgba(34,197,94,0.10);
                    border:1px solid rgba(34,197,94,0.35);
                ">
                    ✅ {safe}
                </div>
                """,
                unsafe_allow_html=True,
            )
    else:
        st.caption("No pros available.")


with cons_col:
    st.markdown("### ❌ Cons")

    if cons:
        for item in cons:
            safe = html.escape(item)

            st.markdown(
                f"""
                <div style="
                    padding:10px 12px;
                    margin-bottom:8px;
                    border-radius:8px;
                    background:rgba(239,68,68,0.10);
                    border:1px solid rgba(239,68,68,0.35);
                ">
                    ❌ {safe}
                </div>
                """,
                unsafe_allow_html=True,
            )
    else:
        st.caption("No cons available.")
