"""
web/views.py — Django views replacing the Streamlit UI.

All heavy logic lives in src/services and src/utils — views just
wire HTTP requests/responses to those services.
"""

from __future__ import annotations

import io
import os
import sys

# Ensure the project root is on sys.path so `src.*` imports resolve
# regardless of how Django is launched.
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from django.http import HttpRequest, HttpResponse, JsonResponse, FileResponse
from django.shortcuts import render
from django.views.decorators.http import require_http_methods

from src.services.job_search import search_jobs
from src.services.job_scorer import compute_job_fit_scores
from src.services.job_scraper import fetch_job_description_from_url
from src.services.resume_generator import generate_resume_and_coverletter
from src.utils.pdf import extract_pdf_text, generate_pdf_from_text


# ── Index ─────────────────────────────────────────────────────────────────────

def index(request: HttpRequest) -> HttpResponse:
    return render(request, "web/index.html")


# ── Job Search ────────────────────────────────────────────────────────────────

@require_http_methods(["GET", "POST"])
def job_search(request: HttpRequest) -> HttpResponse:
    context: dict = {"tab": "search"}

    if request.method != "POST":
        return render(request, "web/job_search.html", context)

    query      = request.POST.get("query", "").strip()
    resume_file = request.FILES.get("resume")

    # ── Validation ────────────────────────────────────────────────────────────
    errors = []
    if not query:
        errors.append("Please enter a job search query.")
    if not resume_file:
        errors.append("Please upload your resume PDF.")
    if errors:
        context["errors"] = errors
        return render(request, "web/job_search.html", context)

    # ── Extract resume text ───────────────────────────────────────────────────
    try:
        resume_text = extract_pdf_text(resume_file)
    except RuntimeError as exc:
        context["errors"] = [str(exc)]
        return render(request, "web/job_search.html", context)

    if not resume_text:
        context["errors"] = ["Could not extract text from the uploaded PDF."]
        return render(request, "web/job_search.html", context)

    # ── Search ────────────────────────────────────────────────────────────────
    try:
        jobs = search_jobs(query)
    except (EnvironmentError, RuntimeError) as exc:
        context["errors"] = [str(exc)]
        return render(request, "web/job_search.html", context)

    if not jobs:
        context["errors"] = ["No jobs found for that query. Try a different search."]
        return render(request, "web/job_search.html", context)

    # ── Score ─────────────────────────────────────────────────────────────────
    try:
        top_jobs, other_jobs = compute_job_fit_scores(resume_text, jobs)
    except ValueError as exc:
        context["errors"] = [str(exc)]
        return render(request, "web/job_search.html", context)

    context.update({
        "query":      query,
        "top_jobs":   top_jobs,
        "other_jobs": other_jobs,
    })
    return render(request, "web/job_search.html", context)


# ── Resume Optimizer ──────────────────────────────────────────────────────────

@require_http_methods(["GET", "POST"])
def resume_optimizer(request: HttpRequest) -> HttpResponse:
    context: dict = {"tab": "optimizer"}

    if request.method != "POST":
        return render(request, "web/resume_optimizer.html", context)

    job_url     = request.POST.get("job_url", "").strip()
    resume_file = request.FILES.get("resume")

    # ── Validation ────────────────────────────────────────────────────────────
    errors = []
    if not job_url:
        errors.append("Please enter a job posting URL.")
    if not resume_file:
        errors.append("Please upload your resume PDF.")
    if errors:
        context["errors"] = errors
        return render(request, "web/resume_optimizer.html", context)

    # ── Fetch job description ─────────────────────────────────────────────────
    try:
        job_description = fetch_job_description_from_url(job_url)
    except (ValueError, Exception) as exc:
        context["errors"] = [f"Could not fetch job description: {exc}"]
        return render(request, "web/resume_optimizer.html", context)

    # ── Extract resume ────────────────────────────────────────────────────────
    try:
        resume_text = extract_pdf_text(resume_file)
    except RuntimeError as exc:
        context["errors"] = [str(exc)]
        return render(request, "web/resume_optimizer.html", context)

    if not resume_text:
        context["errors"] = ["Could not extract text from the uploaded PDF."]
        return render(request, "web/resume_optimizer.html", context)

    # ── Generate ──────────────────────────────────────────────────────────────
    try:
        result = generate_resume_and_coverletter(resume_text, job_description)
    except (EnvironmentError, Exception) as exc:
        context["errors"] = [f"Generation failed: {exc}"]
        return render(request, "web/resume_optimizer.html", context)

    # ── Store PDFs in session-safe temp files ─────────────────────────────────
    resume_pdf_path  = generate_pdf_from_text(result.optimized_resume, "optimized_resume.pdf")
    cover_pdf_path   = generate_pdf_from_text(result.cover_letter,     "cover_letter.pdf")

    # Store paths in session for the download view
    request.session["resume_pdf_path"] = resume_pdf_path
    request.session["cover_pdf_path"]  = cover_pdf_path

    context.update({
        "jd_match":         result.jd_match,
        "missing_keywords": result.missing_keywords,
        "optimized_resume": result.optimized_resume,
        "cover_letter":     result.cover_letter,
        "show_results":     True,
        "job_url":          job_url,
    })
    return render(request, "web/resume_optimizer.html", context)


# ── PDF Download ──────────────────────────────────────────────────────────────

def download_pdf(request: HttpRequest, kind: str) -> HttpResponse:
    """Serve resume or cover letter PDF from the temp path stored in session."""
    key_map = {
        "resume":  ("resume_pdf_path",  "optimized_resume.pdf"),
        "cover":   ("cover_pdf_path",   "cover_letter.pdf"),
    }
    if kind not in key_map:
        return HttpResponse("Not found", status=404)

    session_key, filename = key_map[kind]
    path = request.session.get(session_key)

    if not path or not os.path.exists(path):
        return HttpResponse("File not found — please regenerate.", status=404)

    response = FileResponse(
        open(path, "rb"),
        content_type="application/pdf",
        as_attachment=True,
        filename=filename,
    )
    return response
