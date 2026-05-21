"""
services/job_scorer.py — TF-IDF cosine-similarity job-fit scoring.
"""

from __future__ import annotations

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from src.config import settings


def compute_job_fit_scores(
    resume_text: str,
    jobs: list[dict],
) -> tuple[list[dict], list[dict]]:
    """Score *jobs* against *resume_text* using TF-IDF cosine similarity.

    Args:
        resume_text: Full plaintext of the candidate's resume.
        jobs: List of job dicts with at least Title, Link, Snippet keys.

    Returns:
        A ``(top_jobs, other_jobs)`` tuple where *top_jobs* contains the
        ``settings.top_jobs_count`` highest-scoring jobs (descending) and
        *other_jobs* holds the remainder. Each dict gains a ``Score`` key
        (float, 0-100 rounded to 2 dp).

    Raises:
        ValueError: When *resume_text* is empty or no job snippet is available.
    """
    if not resume_text.strip():
        raise ValueError("Resume text is empty — cannot compute job fit scores.")

    candidates = [j for j in jobs[: settings.max_jobs_to_score] if j.get("Snippet", "").strip()]
    if not candidates:
        raise ValueError("No job snippets available for similarity scoring.")

    snippets = [j["Snippet"] for j in candidates]
    vectorizer = TfidfVectorizer(stop_words="english")
    tfidf_matrix = vectorizer.fit_transform([resume_text] + snippets)
    similarities = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:]).flatten()

    scored = [
        {**job, "Score": round(float(score) * 100, 2)}
        for job, score in zip(candidates, similarities)
    ]
    scored.sort(key=lambda x: x["Score"], reverse=True)

    top_n = settings.top_jobs_count
    return scored[:top_n], scored[top_n:]
