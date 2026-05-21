"""
services/job_scraper.py — Scrape a job description from a public URL.
"""

from __future__ import annotations

import requests
from bs4 import BeautifulSoup

from src.utils.decorators import retry_request
from src.utils.text import is_valid_url

_HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; GenAI-Document-Agent/1.0)"}

_CSS_SELECTORS = [
    "div.job-description",
    "div.description",
    "section.job-desc",
    "div#job-description",
    "div.jd-content",
    "article",
    "div[class*=job]",
    "div[class*=description]",
]


@retry_request
def fetch_job_description_from_url(url: str) -> str:
    """Fetch and return the job description text from *url*.

    Raises:
        ValueError: When *url* is not a valid http/https URL.
        requests.HTTPError: On non-200 HTTP responses (after retries).
        RuntimeError: When the page cannot be parsed.
    """
    if not is_valid_url(url):
        raise ValueError(f"Invalid URL: '{url}'. Must start with http:// or https://.")

    response = requests.get(url, headers=_HEADERS, timeout=10)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    for selector in _CSS_SELECTORS:
        element = soup.select_one(selector)
        if element and element.get_text(strip=True):
            return element.get_text(separator="\n", strip=True)

    # Fallback: all visible text
    return "\n".join(soup.stripped_strings)
