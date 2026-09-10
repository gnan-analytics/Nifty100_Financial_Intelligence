import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src.dashboard.utils.db import (
    get_companies,
    get_company_trends,
)

st.title("📈 Trend Analysis")

st.caption(
    "Analyse up to three financial metrics " "across the latest 10 available periods"
)


companies = get_companies()


search = st.text_input(
    "Search company",
    placeholder="Ticker or company name",
)


filtered = companies.copy()

if search.strip():
    term = search.strip().lower()

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


filtered = filtered.copy()

filtered["label"] = (
    filtered["company_id"].astype(str) + " — " + filtered["company_name"].astype(str)
)


selected = st.selectbox(
    "Company",
    filtered["label"].tolist(),
)


ticker = selected.split(
    " — ",
    1,
)[0]


data = get_company_trends(ticker)


if data.empty:
    st.info("Financial trend data unavailable.")
    st.stop()


metric_map = {
    "Revenue": "sales",
    "Net Profit": "net_profit",
    "Operating Profit": "operating_profit",
    "OPM %": "opm_percentage",
    "EPS": "eps",
    "ROE %": "return_on_equity_pct",
    "ROCE %": "return_on_capital_employed_pct",
    "Net Profit Margin %": "net_profit_margin_pct",
    "Debt / Equity": "debt_to_equity",
    "Free Cash Flow": "free_cash_flow_cr",
    "Asset Turnover": "asset_turnover",
}


available = {
    label: column
    for label, column in metric_map.items()
    if column in data.columns
    and pd.to_numeric(
        data[column],
        errors="coerce",
    )
    .notna()
    .any()
}


default_metrics = list(available.keys())[:3]


selected_metrics = st.multiselect(
    "Metrics — select up to 3",
    list(available.keys()),
    default=default_metrics,
    max_selections=3,
)


if not selected_metrics:
    st.info("Select at least one metric.")
    st.stop()


chart_data = data.sort_values("year").tail(10).copy()


fig = go.Figure()


for label in selected_metrics:
    column = available[label]

    values = pd.to_numeric(
        chart_data[column],
        errors="coerce",
    )

    yoy = values.pct_change(fill_method=None) * 100

    annotation_text = []

    for value in yoy:
        if pd.isna(value):
            annotation_text.append("")
        else:
            annotation_text.append(f"{value:+.1f}%")

    fig.add_trace(
        go.Scatter(
            x=chart_data["year"],
            y=values,
            mode="lines+markers+text",
            text=annotation_text,
            textposition="top center",
            name=label,
            connectgaps=False,
        )
    )


fig.update_layout(
    height=620,
    hovermode="x unified",
    xaxis_title="Year",
    yaxis_title="Metric Value",
    margin=dict(
        l=20,
        r=20,
        t=50,
        b=20,
    ),
)


st.plotly_chart(
    fig,
    use_container_width=True,
)


if len(chart_data) < 10:
    st.info("Data available for only " f"{len(chart_data)} periods.")


st.caption("Labels above points show YoY percentage change.")
