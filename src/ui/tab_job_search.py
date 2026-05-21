"""
ui/tab_job_search.py — "Job Search" tab: upload resume, search, rank results.
"""

from __future__ import annotations

import html

import streamlit as st

from src.services import compute_job_fit_scores, search_jobs
from src.utils import extract_pdf_text


def render_job_search_tab() -> None:
    resume_file = st.file_uploader(
        "Upload your resume (PDF)",
        type=["pdf"],
        key="search_resume",
    )
    query = st.text_input(
        "Search jobs",
        placeholder="e.g. AI engineer in Nepal",
        key="search_query",
    )

    _, col_btn, _ = st.columns([1, 2, 1])
    with col_btn:
        search_clicked = st.button("🔎 Search Jobs", use_container_width=True)

    if not search_clicked:
        return

    if not query.strip() or not resume_file:
        st.warning("Please enter a search query and upload your resume.")
        return

    with st.spinner("Extracting resume and searching jobs…"):
        try:
            resume_text = extract_pdf_text(resume_file)
        except RuntimeError as exc:
            st.error(str(exc))
            return

        if not resume_text:
            st.warning("Could not extract text from the resume PDF.")
            return

        try:
            jobs = search_jobs(query)
        except (EnvironmentError, RuntimeError) as exc:
            st.error(str(exc))
            return

    if not jobs:
        st.error("No jobs found for that query.")
        return

    try:
        top_jobs, other_jobs = compute_job_fit_scores(resume_text, jobs)
    except ValueError as exc:
        st.warning(str(exc))
        return

    _render_job_list("🏆 Top Matching Jobs", top_jobs, show_score=True)

    if other_jobs:
        with st.expander("📋 Other Opportunities"):
            _render_job_list("", other_jobs, show_score=False)


# ── private helpers ───────────────────────────────────────────────────────────

def _render_job_list(
    header: str,
    jobs: list[dict],
    *,
    show_score: bool,
) -> None:
    if header:
        st.subheader(header)
    for idx, job in enumerate(jobs, start=1):
        title = html.escape(job.get("Title", "Untitled"))
        link = html.escape(job.get("Link", "#"), quote=True)
        snippet = html.escape(job.get("Snippet", ""))
        score_html = (
            f"<p><strong>Match:</strong> {job['Score']}%</p>" if show_score else ""
        )
        st.markdown(
            f"""
            <div style="border:1px solid #ddd; padding:10px; border-radius:8px;
                        margin-bottom:10px; box-shadow:0 1px 3px rgba(0,0,0,.06);">
              <h4>{idx}. <a href="{link}" target="_blank"
                            rel="noopener noreferrer"
                            style="text-decoration:none;">{title}</a></h4>
              {score_html}
              <p style="color:#555;">{snippet}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
