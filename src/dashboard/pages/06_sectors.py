import pandas as pd
import plotly.express as px
import streamlit as st

from src.dashboard.utils.db import (
    get_sector_dashboard,
)

st.title("🧩 Sector Analysis")

st.caption("Compare companies and sector-level fundamentals")


df = get_sector_dashboard()


sectors = sorted(df["broad_sector"].dropna().astype(str).unique().tolist())


if not sectors:
    st.warning("Sector data unavailable.")
    st.stop()


selected_sector = st.selectbox(
    "Sector",
    sectors,
)


sector_df = df[df["broad_sector"] == selected_sector].copy()


for column in [
    "sales",
    "return_on_equity_pct",
    "market_cap_crore",
]:
    if column in sector_df.columns:
        sector_df[column] = pd.to_numeric(
            sector_df[column],
            errors="coerce",
        )


st.subheader(f"{selected_sector} — Company Map")


bubble = sector_df.dropna(
    subset=[
        "sales",
        "return_on_equity_pct",
        "market_cap_crore",
    ]
).copy()


if not bubble.empty:
    bubble["bubble_size"] = bubble["market_cap_crore"].clip(lower=1)

    fig = px.scatter(
        bubble,
        x="sales",
        y="return_on_equity_pct",
        size="bubble_size",
        color="sub_sector",
        hover_name="company_name",
        hover_data={
            "company_id": True,
            "sales": ":,.0f",
            "return_on_equity_pct": ":.2f",
            "market_cap_crore": ":,.0f",
            "bubble_size": False,
        },
        labels={
            "sales": "Revenue (₹ Cr)",
            "return_on_equity_pct": "ROE (%)",
            "sub_sector": "Sub-sector",
        },
        size_max=65,
    )

    fig.update_layout(
        height=600,
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
else:
    st.info("Insufficient data for bubble chart.")


# ------------------------------------------------------------
# Sector Median KPI Chart
# ------------------------------------------------------------

st.subheader("Sector Median KPIs")


median_metrics = {
    "ROE %": "return_on_equity_pct",
    "ROCE %": "return_on_capital_employed_pct",
    "Net Profit Margin %": "net_profit_margin_pct",
    "Debt / Equity": "debt_to_equity",
    "Revenue CAGR 5Y %": "revenue_cagr_5yr",
    "PAT CAGR 5Y %": "pat_cagr_5yr",
    "P/E": "pe_ratio",
    "P/B": "pb_ratio",
}


rows = []


for label, column in median_metrics.items():
    if column not in sector_df.columns:
        continue

    values = pd.to_numeric(
        sector_df[column],
        errors="coerce",
    ).dropna()

    if values.empty:
        continue

    rows.append(
        {
            "Metric": label,
            "Median": values.median(),
        }
    )


median_df = pd.DataFrame(rows)


if not median_df.empty:
    bar = px.bar(
        median_df,
        x="Metric",
        y="Median",
        text_auto=".2f",
    )

    bar.update_layout(
        height=450,
        xaxis_title="",
        yaxis_title="Sector Median",
        margin=dict(
            l=20,
            r=20,
            t=40,
            b=20,
        ),
    )

    st.plotly_chart(
        bar,
        use_container_width=True,
    )
else:
    st.info("Sector median data unavailable.")


st.dataframe(
    sector_df[
        [
            c
            for c in [
                "company_id",
                "company_name",
                "sub_sector",
                "sales",
                "return_on_equity_pct",
                "market_cap_crore",
            ]
            if c in sector_df.columns
        ]
    ],
    hide_index=True,
    use_container_width=True,
)
