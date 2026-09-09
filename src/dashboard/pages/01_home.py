import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

from src.dashboard.utils.db import (
    get_dashboard_year,
)


st.title("🏠 Nifty 100 Analytics")

st.caption(
    "Market-wide financial intelligence dashboard"
)


# ------------------------------------------------------------
# Sidebar Year Selector
# ------------------------------------------------------------

selected_year = st.sidebar.selectbox(
    "Financial Year",
    options=list(range(2024, 2018, -1)),
    index=0,
    key="home_year",
)

df = get_dashboard_year(
    selected_year
)


# ------------------------------------------------------------
# Helpers
# ------------------------------------------------------------

def numeric_series(
    dataframe,
    column,
):
    if column not in dataframe.columns:
        return pd.Series(
            dtype=float
        )

    return pd.to_numeric(
        dataframe[column],
        errors="coerce",
    )


def metric_text(
    value,
    suffix="",
    decimals=1,
):
    if value is None:
        return "N/A"

    try:
        if pd.isna(value):
            return "N/A"

        return (
            f"{float(value):,.{decimals}f}"
            f"{suffix}"
        )
    except Exception:
        return "N/A"


roe = numeric_series(
    df,
    "return_on_equity_pct",
)

pe = numeric_series(
    df,
    "pe_ratio",
)

de = numeric_series(
    df,
    "debt_to_equity",
)

revenue_cagr = numeric_series(
    df,
    "revenue_cagr_5yr",
)


average_roe = (
    roe.mean()
    if not roe.empty
    else np.nan
)

median_pe = (
    pe.median()
    if not pe.empty
    else np.nan
)

median_de = (
    de.median()
    if not de.empty
    else np.nan
)

median_revenue_cagr = (
    revenue_cagr.median()
    if not revenue_cagr.empty
    else np.nan
)

debt_free_count = int(
    de.fillna(
        np.inf
    ).abs().le(
        0.000001
    ).sum()
)


# ------------------------------------------------------------
# KPI Tiles
# ------------------------------------------------------------

k1, k2, k3, k4, k5, k6 = st.columns(
    6
)

k1.metric(
    "Average ROE",
    metric_text(
        average_roe,
        "%",
    ),
)

k2.metric(
    "Median P/E",
    metric_text(
        median_pe,
        "x",
    ),
)

k3.metric(
    "Median D/E",
    metric_text(
        median_de,
        "x",
        2,
    ),
)

k4.metric(
    "Total Companies",
    f"{len(df):,}",
)

k5.metric(
    "Median Revenue CAGR 5Y",
    metric_text(
        median_revenue_cagr,
        "%",
    ),
)

k6.metric(
    "Debt-Free Companies",
    f"{debt_free_count:,}",
)


st.divider()


# ------------------------------------------------------------
# Sector Breakdown
# ------------------------------------------------------------

left, right = st.columns(
    [1.15, 1]
)

with left:
    st.subheader(
        "Sector Breakdown"
    )

    if (
        "broad_sector"
        in df.columns
    ):
        sector_counts = (
            df["broad_sector"]
            .fillna("Unknown")
            .value_counts()
            .rename_axis("Sector")
            .reset_index(
                name="Companies"
            )
        )

        fig = px.pie(
            sector_counts,
            names="Sector",
            values="Companies",
            hole=0.55,
            title=(
                f"Company Distribution — "
                f"{selected_year}"
            ),
        )

        fig.update_layout(
            height=500,
            margin=dict(
                l=20,
                r=20,
                t=60,
                b=20,
            ),
            legend=dict(
                orientation="h",
                yanchor="top",
                y=-0.1,
            ),
        )

        st.plotly_chart(
            fig,
            use_container_width=True,
        )
    else:
        st.info(
            "Sector data unavailable."
        )


# ------------------------------------------------------------
# Top Quality Companies
# ------------------------------------------------------------

with right:
    st.subheader(
        "Top 5 — Composite Quality"
    )

    if (
        "composite_quality_score"
        in df.columns
    ):
        quality = df.copy()

        quality[
            "composite_quality_score"
        ] = pd.to_numeric(
            quality[
                "composite_quality_score"
            ],
            errors="coerce",
        )

        quality = (
            quality
            .dropna(
                subset=[
                    "composite_quality_score"
                ]
            )
            .sort_values(
                "composite_quality_score",
                ascending=False,
            )
            .head(5)
        )

        show_cols = [
            "company_id",
            "company_name",
            "broad_sector",
            "composite_quality_score",
        ]

        show_cols = [
            col
            for col in show_cols
            if col in quality.columns
        ]

        if not quality.empty:
            display = quality[
                show_cols
            ].copy()

            display = display.rename(
                columns={
                    "company_id": "Ticker",
                    "company_name": "Company",
                    "broad_sector": "Sector",
                    "composite_quality_score":
                        "Quality Score",
                }
            )

            st.dataframe(
                display,
                hide_index=True,
                use_container_width=True,
            )
        else:
            st.info(
                "Composite quality scores "
                "are unavailable for this year."
            )
    else:
        st.info(
            "Composite quality scores "
            "are unavailable for this year."
        )


st.caption(
    "Metrics are calculated from available "
    f"financial data for calendar year {selected_year}."
)
