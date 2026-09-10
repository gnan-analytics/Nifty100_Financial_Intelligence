import runpy
import sys
from pathlib import Path

import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[2]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(
        0,
        str(PROJECT_ROOT),
    )


st.set_page_config(
    page_title="Nifty 100 Analytics",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)


PAGES = {
    "Home": "01_home.py",
    "Company Profile": "02_profile.py",
    "Screener": "03_screener.py",
    "Peer Comparison": "04_peers.py",
    "Trend Analysis": "05_trends.py",
    "Sector Analysis": "06_sectors.py",
    "Capital Allocation": "07_capital.py",
    "Annual Reports": "08_reports.py",
}


st.sidebar.title("Nifty 100 Analytics")

st.sidebar.caption("Financial Intelligence Platform")

selected_page = st.sidebar.radio(
    "Navigation",
    list(PAGES.keys()),
)

st.sidebar.divider()

st.sidebar.caption("Sprint 4 Dashboard")


page_path = Path(__file__).parent / "pages" / PAGES[selected_page]

runpy.run_path(
    str(page_path),
    run_name="__main__",
)
