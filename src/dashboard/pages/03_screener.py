import pandas as pd
import streamlit as st

from src.dashboard.utils.db import get_screener_data
from src.screener.engine import run_preset

st.title("🔎 Nifty 100 Screener")

st.caption(
    "Screen Nifty 100 companies using custom thresholds "
    "or the exact Sprint 3 preset engine."
)

if "active_screener_preset" not in st.session_state:
    st.session_state.active_screener_preset = None

st.subheader("Quick Presets")

preset_map = {
    "Quality Compounder": "quality_compounder",
    "Value Pick": "value_pick",
    "Growth Accelerator": "growth_accelerator",
    "Dividend Champion": "dividend_champion",
    "Debt-Free Blue Chip": "debt_free_blue_chip",
    "Turnaround Watch": "turnaround_watch",
}

cols = st.columns(3)

for idx, (label, key) in enumerate(preset_map.items()):
    with cols[idx % 3]:
        if st.button(label, use_container_width=True, key=f"preset_{key}"):
            st.session_state.active_screener_preset = key

if st.button("Clear Preset / Use Custom Filters", use_container_width=True):
    st.session_state.active_screener_preset = None

active_preset = st.session_state.active_screener_preset

if active_preset:
    label = next(name for name, key in preset_map.items() if key == active_preset)

    st.info(f"Active preset: {label}")

    try:
        result = run_preset(active_preset)
    except Exception as exc:
        st.error(f"Preset execution failed: {exc}")
        st.stop()

else:
    data = get_screener_data().copy()

    if data.empty:
        st.warning("No screener data available.")
        st.stop()

    with st.sidebar:
        st.header("Screener Filters")

        roe_min = st.slider("ROE minimum (%)", -100.0, 100.0, -100.0, 1.0)
        de_max = st.slider("Debt / Equity maximum", 0.0, 20.0, 20.0, 0.1)
        fcf_min = st.slider("FCF minimum (₹ Cr)", -50000.0, 50000.0, -50000.0, 500.0)
        rev_cagr_min = st.slider(
            "Revenue CAGR 5Y minimum (%)", -100.0, 100.0, -100.0, 1.0
        )
        pat_cagr_min = st.slider("PAT CAGR 5Y minimum (%)", -100.0, 150.0, -100.0, 1.0)
        opm_min = st.slider("OPM minimum (%)", -100.0, 100.0, -100.0, 1.0)
        pe_max = st.slider("P/E maximum", 0.0, 500.0, 500.0, 5.0)
        pb_max = st.slider("P/B maximum", 0.0, 100.0, 100.0, 1.0)
        div_yield_min = st.slider("Dividend Yield minimum (%)", 0.0, 20.0, 0.0, 0.1)
        icr_min = st.slider("Interest Coverage minimum", -50.0, 100.0, -50.0, 1.0)

    result = data.copy()

    def apply_min(frame, column, threshold):
        """Apply min."""
        if column not in frame.columns:
            return frame

        values = pd.to_numeric(frame[column], errors="coerce")
        return frame[values.ge(threshold) | values.isna()]

    def apply_max(frame, column, threshold):
        """Apply max."""
        if column not in frame.columns:
            return frame

        values = pd.to_numeric(frame[column], errors="coerce")
        return frame[values.le(threshold) | values.isna()]

    result = apply_min(result, "return_on_equity_pct", roe_min)
    result = apply_min(result, "free_cash_flow_cr", fcf_min)
    result = apply_min(result, "revenue_cagr_5yr", rev_cagr_min)
    result = apply_min(result, "pat_cagr_5yr", pat_cagr_min)
    result = apply_min(result, "operating_profit_margin_pct", opm_min)
    result = apply_max(result, "pe_ratio", pe_max)
    result = apply_max(result, "pb_ratio", pb_max)
    result = apply_min(result, "dividend_yield_pct", div_yield_min)
    result = apply_min(result, "interest_coverage", icr_min)

    if "debt_to_equity" in result.columns and "sector" in result.columns:
        de = pd.to_numeric(result["debt_to_equity"], errors="coerce")

        is_financial = (
            result["sector"].fillna("").astype(str).str.lower().eq("financials")
        )

        result = result[is_financial | de.le(de_max) | de.isna()]

if result.empty:
    st.warning("No companies match the selected criteria.")
    st.metric("Matching Companies", 0)

    st.download_button(
        "Download CSV",
        data=result.to_csv(index=False).encode("utf-8"),
        file_name="nifty100_screener_results.csv",
        mime="text/csv",
    )
    st.stop()

if "composite_quality_score" in result.columns:
    result = result.sort_values(
        ["composite_quality_score", "company_id"],
        ascending=[False, True],
        na_position="last",
    )

st.metric("Matching Companies", len(result))

preferred_columns = [
    "company_id",
    "company_name",
    "sector",
    "return_on_equity_pct",
    "return_on_capital_employed_pct",
    "debt_to_equity",
    "free_cash_flow_cr",
    "revenue_cagr_5yr",
    "pat_cagr_5yr",
    "operating_profit_margin_pct",
    "pe_ratio",
    "pb_ratio",
    "dividend_yield_pct",
    "interest_coverage",
    "sales",
    "net_profit",
    "market_cap_crore",
    "composite_quality_score",
]

visible_columns = [col for col in preferred_columns if col in result.columns]

display = result[visible_columns].copy()

rename_map = {
    "company_id": "Ticker",
    "company_name": "Company",
    "sector": "Sector",
    "return_on_equity_pct": "ROE %",
    "return_on_capital_employed_pct": "ROCE %",
    "debt_to_equity": "D/E",
    "free_cash_flow_cr": "FCF ₹ Cr",
    "revenue_cagr_5yr": "Revenue CAGR 5Y %",
    "pat_cagr_5yr": "PAT CAGR 5Y %",
    "operating_profit_margin_pct": "OPM %",
    "pe_ratio": "P/E",
    "pb_ratio": "P/B",
    "dividend_yield_pct": "Dividend Yield %",
    "interest_coverage": "Interest Coverage",
    "sales": "Sales ₹ Cr",
    "net_profit": "Net Profit ₹ Cr",
    "market_cap_crore": "Market Cap ₹ Cr",
    "composite_quality_score": "Composite Score",
}

display = display.rename(columns=rename_map)

st.dataframe(
    display,
    use_container_width=True,
    hide_index=True,
)

st.download_button(
    "Download Results as CSV",
    data=result.to_csv(index=False).encode("utf-8"),
    file_name=(
        f"{active_preset}_screener.csv" if active_preset else "custom_screener.csv"
    ),
    mime="text/csv",
)
