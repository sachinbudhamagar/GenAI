"""
tests/test_job_scorer.py — Unit tests for src.services.job_scorer
"""

import pytest
from src.services.job_scorer import compute_job_fit_scores


SAMPLE_RESUME = (
    "Experienced Python developer skilled in machine learning, NLP, and LangChain."
)

SAMPLE_JOBS = [
    {"Title": "ML Engineer", "Link": "http://a.com", "Snippet": "Python machine learning NLP"},
    {"Title": "Frontend Dev", "Link": "http://b.com", "Snippet": "React TypeScript CSS"},
    {"Title": "Data Scientist", "Link": "http://c.com", "Snippet": "Python data analysis sklearn"},
]


class TestComputeJobFitScores:
    def test_returns_two_lists(self):
        top, other = compute_job_fit_scores(SAMPLE_RESUME, SAMPLE_JOBS)
        assert isinstance(top, list)
        assert isinstance(other, list)

    def test_scores_present(self):
        top, _ = compute_job_fit_scores(SAMPLE_RESUME, SAMPLE_JOBS)
        for job in top:
            assert "Score" in job
            assert 0.0 <= job["Score"] <= 100.0

    def test_sorted_descending(self):
        top, _ = compute_job_fit_scores(SAMPLE_RESUME, SAMPLE_JOBS)
        scores = [j["Score"] for j in top]
        assert scores == sorted(scores, reverse=True)

    def test_empty_resume_raises(self):
        with pytest.raises(ValueError, match="empty"):
            compute_job_fit_scores("", SAMPLE_JOBS)

    def test_no_snippets_raises(self):
        jobs_no_snippet = [{"Title": "x", "Link": "http://x.com", "Snippet": ""}]
        with pytest.raises(ValueError, match="No job snippets"):
            compute_job_fit_scores(SAMPLE_RESUME, jobs_no_snippet)
