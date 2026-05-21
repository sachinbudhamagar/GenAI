"""
ui/tab_resume_optimizer.py — "Resume & Cover Letter" tab.
"""

from __future__ import annotations

import streamlit as st

from src.services import (
    fetch_job_description_from_url,
    generate_resume_and_coverletter,
)
from src.utils import extract_pdf_text, generate_pdf_from_text


def render_resume_optimizer_tab() -> None:
    resume_file = st.file_uploader(
        "Upload your resume (PDF)",
        type=["pdf"],
        key="optimizer_resume",
    )
    job_url = st.text_input(
        "Job Posting URL",
        placeholder="https://www.linkedin.com/jobs/…",
        key="optimizer_url",
    )

    if not st.button("⚡ Generate Optimised Resume & Cover Letter"):
        return

    if not resume_file or not job_url.strip():
        st.warning("Please upload your resume and paste a valid job posting URL.")
        return

    # ── Step 1: Fetch job description ────────────────────────────────────────
    with st.spinner("Fetching job description…"):
        try:
            job_description = fetch_job_description_from_url(job_url.strip())
        except (ValueError, Exception) as exc:
            st.error(f"Could not fetch job description: {exc}")
            return

    # ── Step 2: Extract resume text ──────────────────────────────────────────
    try:
        resume_text = extract_pdf_text(resume_file)
    except RuntimeError as exc:
        st.error(str(exc))
        return

    if not resume_text:
        st.warning("Could not extract text from the resume PDF.")
        return

    # ── Step 3: Generate documents ───────────────────────────────────────────
    with st.spinner("Generating documents with AI…"):
        try:
            result = generate_resume_and_coverletter(resume_text, job_description)
        except EnvironmentError as exc:
            st.error(str(exc))
            return
        except Exception as exc:  # noqa: BLE001
            st.error(f"Generation failed: {exc}")
            return

    # ── Step 4: Show analysis metrics ────────────────────────────────────────
    col_match, col_keywords = st.columns(2)
    with col_match:
        st.metric("JD Match", result.jd_match)
    with col_keywords:
        missing = ", ".join(result.missing_keywords) or "None"
        st.markdown(f"**Missing Keywords:** {missing}")

    # ── Step 5: Expandable previews ──────────────────────────────────────────
    with st.expander("📄 View Optimised Resume"):
        st.text_area("Optimised Resume", result.optimized_resume, height=400)

    with st.expander("✉️ View Cover Letter"):
        st.text_area("Cover Letter", result.cover_letter, height=400)

    # ── Step 6: PDF downloads ────────────────────────────────────────────────
    resume_pdf = generate_pdf_from_text(result.optimized_resume, "optimized_resume.pdf")
    cover_pdf = generate_pdf_from_text(result.cover_letter, "cover_letter.pdf")

    col_dl1, col_dl2 = st.columns(2)
    with col_dl1:
        with open(resume_pdf, "rb") as f:
            st.download_button(
                "⬇️ Download Resume (PDF)",
                data=f,
                file_name="optimized_resume.pdf",
                mime="application/pdf",
                use_container_width=True,
            )
    with col_dl2:
        with open(cover_pdf, "rb") as f:
            st.download_button(
                "⬇️ Download Cover Letter (PDF)",
                data=f,
                file_name="cover_letter.pdf",
                mime="application/pdf",
                use_container_width=True,
            )
