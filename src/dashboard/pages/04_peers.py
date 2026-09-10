import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src.dashboard.utils.db import (
    get_peer_dashboard,
    get_peer_groups,
    get_peer_percentiles,
)

st.title("🎯 Peer Comparison")

st.caption(
    "Compare a company against its peer group "
    "using percentile-based financial metrics"
)


# ------------------------------------------------------------
# Peer Group
# ------------------------------------------------------------

groups = get_peer_groups()

if groups.empty:
    st.warning("Peer group data unavailable.")
    st.stop()


group_name = st.selectbox(
    "Peer Group",
    groups["peer_group_name"].tolist(),
)


peer_df = get_peer_dashboard(group_name)


if peer_df.empty:
    st.warning("No companies found in this peer group.")
    st.stop()


# ------------------------------------------------------------
# Company Selector
# ------------------------------------------------------------

peer_df["label"] = (
    peer_df["company_id"].astype(str) + " — " + peer_df["company_name"].astype(str)
)


selected_label = st.selectbox(
    "Company",
    peer_df["label"].tolist(),
)


selected_company = peer_df.loc[
    peer_df["label"] == selected_label,
    "company_id",
].iloc[0]


# ------------------------------------------------------------
# Percentiles
# ------------------------------------------------------------

percentiles = get_peer_percentiles(group_name)


metric_aliases = {
    "roe": "ROE",
    "roce": "ROCE",
    "npm": "NPM",
    "debt_to_equity": "D/E",
    "fcf": "FCF",
    "pat_cagr_5yr": "PAT CAGR 5Y",
    "revenue_cagr_5yr": "Revenue CAGR 5Y",
}


def metric_column(
    df,
):
    """Handle metric column."""
    for candidate in [
        "metric",
        "metric_name",
    ]:
        if candidate in df.columns:
            return candidate

    return None


def percentile_column(
    df,
):
    """Handle percentile column."""
    for candidate in [
        "percentile",
        "percentile_rank",
        "percentile_score",
    ]:
        if candidate in df.columns:
            return candidate

    return None


metric_col = metric_column(percentiles)

pct_col = percentile_column(percentiles)


radar_metrics = [
    "roe",
    "roce",
    "npm",
    "debt_to_equity",
    "fcf",
    "pat_cagr_5yr",
    "revenue_cagr_5yr",
]


company_values = []
peer_values = []
labels = []


if not percentiles.empty and metric_col and pct_col:
    for metric in radar_metrics:
        metric_rows = percentiles[percentiles[metric_col] == metric].copy()

        selected_rows = metric_rows[metric_rows["company_id"] == selected_company]

        if selected_rows.empty:
            continue

        company_pct = pd.to_numeric(
            selected_rows[pct_col],
            errors="coerce",
        ).iloc[0]

        peer_avg = pd.to_numeric(
            metric_rows[pct_col],
            errors="coerce",
        ).mean()

        if pd.isna(company_pct):
            continue

        labels.append(
            metric_aliases.get(
                metric,
                metric,
            )
        )

        company_values.append(float(company_pct))

        peer_values.append(float(peer_avg) if not pd.isna(peer_avg) else 0.0)


# Composite score percentile calculated locally
if "composite_quality_score" in peer_df.columns:
    comp = pd.to_numeric(
        peer_df["composite_quality_score"],
        errors="coerce",
    )

    valid = comp.dropna()

    selected_score = pd.to_numeric(
        peer_df.loc[
            peer_df["company_id"] == selected_company,
            "composite_quality_score",
        ],
        errors="coerce",
    )

    if (
        not valid.empty
        and not selected_score.empty
        and not pd.isna(selected_score.iloc[0])
    ):
        score = float(selected_score.iloc[0])

        rank = valid.rank(method="min")

        selected_index = peer_df.index[peer_df["company_id"] == selected_company][0]

        if selected_index in rank.index:
            if len(valid) > 1:
                pct = (rank.loc[selected_index] - 1) / (len(valid) - 1) * 100
            else:
                pct = 100.0

            labels.append("Composite Score")

            company_values.append(float(pct))

            peer_values.append(50.0)


# ------------------------------------------------------------
# Radar Chart
# ------------------------------------------------------------

st.subheader("Company vs Peer Group Average")


if len(labels) >= 3:
    radar_labels = labels + [labels[0]]

    company_closed = company_values + [company_values[0]]

    peer_closed = peer_values + [peer_values[0]]

    fig = go.Figure()

    fig.add_trace(
        go.Scatterpolar(
            r=company_closed,
            theta=radar_labels,
            fill="toself",
            name=selected_company,
        )
    )

    fig.add_trace(
        go.Scatterpolar(
            r=peer_closed,
            theta=radar_labels,
            mode="lines",
            name="Peer Average",
        )
    )

    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 100],
            )
        ),
        showlegend=True,
        height=600,
        margin=dict(
            l=40,
            r=40,
            t=60,
            b=40,
        ),
    )

    st.plotly_chart(
        fig,
        use_container_width=True,
    )
else:
    st.info("Insufficient percentile data " "for radar chart.")


# ------------------------------------------------------------
# Side-by-Side Peer Table
# ------------------------------------------------------------

st.subheader("Peer Group KPI Table")


table_columns = [
    "company_id",
    "company_name",
    "is_benchmark",
    "return_on_equity_pct",
    "return_on_capital_employed_pct",
    "net_profit_margin_pct",
    "debt_to_equity",
    "free_cash_flow_cr",
    "pat_cagr_5yr",
    "revenue_cagr_5yr",
    "composite_quality_score",
]


table_columns = [col for col in table_columns if col in peer_df.columns]


table = peer_df[table_columns].copy()


table = table.rename(
    columns={
        "company_id": "Ticker",
        "company_name": "Company",
        "is_benchmark": "Benchmark",
        "return_on_equity_pct": "ROE %",
        "return_on_capital_employed_pct": "ROCE %",
        "net_profit_margin_pct": "NPM %",
        "debt_to_equity": "D/E",
        "free_cash_flow_cr": "FCF ₹ Cr",
        "pat_cagr_5yr": "PAT CAGR 5Y %",
        "revenue_cagr_5yr": "Revenue CAGR 5Y %",
        "composite_quality_score": "Composite Score",
    }
)


if "Benchmark" in table.columns:
    table["Benchmark"] = table["Benchmark"].apply(
        lambda x: "⭐ Yes" if int(x) == 1 else ""
    )


def highlight_benchmark(
    row,
):
    """Highlight benchmark."""
    if (
        row.get(
            "Benchmark",
            "",
        )
        == "⭐ Yes"
    ):
        return ["background-color: rgba(255,193,7,0.22);" for _ in row]

    return ["" for _ in row]


styled = table.style.apply(
    highlight_benchmark,
    axis=1,
)


st.dataframe(
    styled,
    hide_index=True,
    use_container_width=True,
    height=500,
)
