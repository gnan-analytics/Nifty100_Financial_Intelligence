import pandas as pd
import plotly.express as px
import streamlit as st

from src.dashboard.utils.db import (
    get_capital_allocation,
    get_companies,
)

st.title("💰 Capital Allocation Map")

st.caption(
    "Explore how Nifty 100 companies deploy capital "
    "using operating, investing and financing cash-flow patterns"
)


# ============================================================
# LOAD DATA
# ============================================================

capital = get_capital_allocation()
companies = get_companies()


if companies.empty:
    st.warning("Company universe unavailable.")
    st.stop()


required_columns = [
    "company_id",
    "year",
    "cfo_sign",
    "cfi_sign",
    "cff_sign",
    "pattern_label",
]


missing = [col for col in required_columns if col not in capital.columns]


if missing:
    st.error("Missing required columns: " + ", ".join(missing))
    st.stop()


# ============================================================
# PREPARE CAPITAL DATA
# ============================================================

capital = capital.copy()


capital["year_date"] = pd.to_datetime(
    capital["year"],
    format="%Y-%m",
    errors="coerce",
)


capital = capital.sort_values(
    [
        "company_id",
        "year_date",
    ]
)


# ============================================================
# LATEST AVAILABLE PATTERN
# ============================================================

latest_available = (
    capital.dropna(subset=["year_date"])
    .groupby(
        "company_id",
        as_index=False,
    )
    .tail(1)
    .copy()
)


# ============================================================
# BUILD COMPLETE 92-COMPANY UNIVERSE
# ============================================================

universe = companies[
    [
        "company_id",
        "company_name",
    ]
].copy()


latest = universe.merge(
    latest_available[
        [
            "company_id",
            "year",
            "year_date",
            "cfo_sign",
            "cfi_sign",
            "cff_sign",
            "pattern_label",
        ]
    ],
    on="company_id",
    how="left",
)


latest["pattern_label"] = latest["pattern_label"].fillna("Data Unavailable")


latest["year"] = latest["year"].fillna("N/A")


for column in [
    "cfo_sign",
    "cfi_sign",
    "cff_sign",
]:
    latest[column] = latest[column].fillna("N/A")


latest["Value"] = 1


# ============================================================
# COVERAGE
# ============================================================

classified_count = latest["pattern_label"].ne("Data Unavailable").sum()


unavailable_count = latest["pattern_label"].eq("Data Unavailable").sum()


# ============================================================
# SUMMARY KPIs
# ============================================================

k1, k2, k3, k4 = st.columns(4)


k1.metric(
    "Nifty 100 Companies",
    len(latest),
)


k2.metric(
    "Classified",
    classified_count,
)


k3.metric(
    "Data Unavailable",
    unavailable_count,
)


k4.metric(
    "Allocation Patterns",
    latest.loc[
        latest["pattern_label"] != "Data Unavailable",
        "pattern_label",
    ].nunique(),
)


if unavailable_count:
    unavailable_tickers = (
        latest.loc[
            latest["pattern_label"] == "Data Unavailable",
            "company_id",
        ]
        .astype(str)
        .tolist()
    )

    st.info(
        "Capital-allocation source data is unavailable for: "
        + ", ".join(unavailable_tickers)
        + ". No pattern has been inferred."
    )


st.divider()


# ============================================================
# PATTERN DISTRIBUTION
# ============================================================

st.subheader("Capital Allocation Distribution")


pattern_counts = (
    latest["pattern_label"]
    .value_counts()
    .rename_axis("Pattern")
    .reset_index(name="Companies")
)


bar = px.bar(
    pattern_counts,
    x="Pattern",
    y="Companies",
    text="Companies",
)


bar.update_layout(
    height=430,
    xaxis_title=("Capital Allocation Pattern"),
    yaxis_title="Companies",
    margin=dict(
        l=20,
        r=20,
        t=30,
        b=20,
    ),
)


st.plotly_chart(
    bar,
    use_container_width=True,
)


# ============================================================
# TREEMAP — ALL 92 COMPANIES
# ============================================================

st.subheader("Capital Allocation Map")


fig = px.treemap(
    latest,
    path=[
        "pattern_label",
        "company_name",
    ],
    values="Value",
    hover_data={
        "company_id": True,
        "year": True,
        "cfo_sign": True,
        "cfi_sign": True,
        "cff_sign": True,
        "Value": False,
    },
)


fig.update_layout(
    height=650,
    margin=dict(
        l=10,
        r=10,
        t=30,
        b=10,
    ),
)


st.plotly_chart(
    fig,
    use_container_width=True,
)


# ============================================================
# PATTERN EXPLORER
# ============================================================

st.subheader("Explore Allocation Pattern")


patterns = sorted(latest["pattern_label"].dropna().unique().tolist())


selected_pattern = st.selectbox(
    "Capital allocation pattern",
    patterns,
)


selected = latest[latest["pattern_label"] == selected_pattern].copy()


st.metric(
    "Companies in Pattern",
    len(selected),
)


display = selected[
    [
        "company_id",
        "company_name",
        "year",
        "cfo_sign",
        "cfi_sign",
        "cff_sign",
        "pattern_label",
    ]
].copy()


display = display.rename(
    columns={
        "company_id": "Ticker",
        "company_name": "Company",
        "year": "Period",
        "cfo_sign": "CFO",
        "cfi_sign": "CFI",
        "cff_sign": "CFF",
        "pattern_label": "Pattern",
    }
)


st.dataframe(
    display,
    hide_index=True,
    use_container_width=True,
)


# ============================================================
# COMPANY HISTORY
# ============================================================

st.divider()

st.subheader("Company Allocation History")


company_options = latest[
    [
        "company_id",
        "company_name",
    ]
].copy()


company_options = company_options.sort_values("company_name")


company_options["label"] = (
    company_options["company_id"].astype(str)
    + " — "
    + company_options["company_name"].astype(str)
)


selected_company_label = st.selectbox(
    "Company history",
    company_options["label"].tolist(),
)


selected_ticker = selected_company_label.split(
    " — ",
    1,
)[0]


history = capital[capital["company_id"] == selected_ticker].copy()


history = history.sort_values(
    "year_date",
    ascending=False,
)


if history.empty:
    st.warning(f"No capital-allocation history " f"is available for {selected_ticker}.")

else:
    history_display = history[
        [
            "year",
            "cfo_sign",
            "cfi_sign",
            "cff_sign",
            "pattern_label",
        ]
    ].copy()

    history_display = history_display.rename(
        columns={
            "year": "Period",
            "cfo_sign": "CFO",
            "cfi_sign": "CFI",
            "cff_sign": "CFF",
            "pattern_label": "Pattern",
        }
    )

    st.dataframe(
        history_display,
        hide_index=True,
        use_container_width=True,
    )


st.caption(
    "CFO = Cash Flow from Operations • "
    "CFI = Cash Flow from Investing • "
    "CFF = Cash Flow from Financing. "
    "Missing source data is displayed as "
    "Data Unavailable rather than inferred."
)
