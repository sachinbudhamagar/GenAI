"""
ui/main.py — Top-level Streamlit layout and tab routing.
"""

import streamlit as st

from .tab_job_search import render_job_search_tab
from .tab_resume_optimizer import render_resume_optimizer_tab


def render_app() -> None:
    """Configure the Streamlit page and render both tabs."""
    st.set_page_config(page_title="AI Job Agent", layout="centered")
    st.markdown(
        "<h1 style='text-align:center;'>🤖 AI Job Agent</h1>",
        unsafe_allow_html=True,
    )

    tab_search, tab_optimizer = st.tabs(["🔍 Job Search", "📄 Resume & Cover Letter"])

    with tab_search:
        render_job_search_tab()

    with tab_optimizer:
        render_resume_optimizer_tab()
