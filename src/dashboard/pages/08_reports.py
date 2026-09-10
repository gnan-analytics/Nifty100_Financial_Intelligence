import requests
import streamlit as st

from src.dashboard.utils.db import (
    get_documents,
    get_report_companies,
)

st.title("📚 Annual Reports")

st.caption("Browse available company annual reports")


@st.cache_data(
    ttl=3600,
    show_spinner=False,
)
def check_report_url(url):
    """Check report url."""
    if not isinstance(url, str):
        return "not_found"

    url = url.strip()

    if not url.startswith(("http://", "https://")):
        return "not_found"

    headers = {"User-Agent": "Mozilla/5.0 Nifty100-Financial-Intelligence"}

    try:
        response = requests.head(
            url,
            allow_redirects=True,
            timeout=4,
            headers=headers,
        )

        if response.status_code == 404:
            return "not_found"

        if response.status_code in {403, 405}:
            response = requests.get(
                url,
                allow_redirects=True,
                timeout=5,
                headers=headers,
                stream=True,
            )

        if response.status_code == 404:
            return "not_found"

        if 200 <= response.status_code < 400:
            return "available"

        return "unknown"

    except requests.RequestException:
        return "unknown"


companies = get_report_companies()

search = st.text_input(
    "Search company",
    placeholder="Ticker or company name",
)

filtered = companies.copy()

if search.strip():
    term = search.strip().lower()

    filtered = filtered[
        filtered["company_id"].astype(str).str.lower().str.contains(term, regex=False)
        | filtered["company_name"]
        .astype(str)
        .str.lower()
        .str.contains(term, regex=False)
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

ticker = selected.split(" — ", 1)[0]

documents = get_documents(ticker)

st.subheader(f"Available Reports — {ticker}")

if documents.empty:
    st.info("No annual reports available.")
    st.stop()

documents = documents.copy()

documents["annual_report"] = documents["annual_report"].fillna("").astype(str)

for _, row in documents.iterrows():
    year = row.get("year", "Unknown Year")

    url = row.get(
        "annual_report",
        "",
    ).strip()

    col1, col2 = st.columns([1, 3])

    with col1:
        st.markdown(f"### {year}")

    with col2:
        if not url.startswith(("http://", "https://")):
            st.error("Report unavailable")
            continue

        status = check_report_url(url)

        if status == "not_found":
            st.error("Report unavailable (404)")

        elif status == "available":
            st.link_button(
                "Open BSE PDF",
                url,
                use_container_width=False,
            )

        else:
            st.warning(
                "Availability could not be verified. "
                "You can still try the stored report link."
            )

            st.link_button(
                "Try Report Link",
                url,
                use_container_width=False,
            )

st.caption(
    "Report URLs come from the project documents dataset. "
    "Availability checks are cached for one hour."
)
