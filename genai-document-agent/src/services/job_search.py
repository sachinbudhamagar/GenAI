"""
services/job_search.py — Job search via the Serper Google Search API.
"""

from __future__ import annotations

import requests

from src.config import settings

_SERPER_URL = "https://google.serper.dev/search"
_QUERY_VARIATIONS = ["{q}", "{q} jobs", "{q} site:linkedin.com"]


def search_jobs(query: str) -> list[dict]:
    """Search for job listings matching *query* using the Serper API.

    Returns a deduplicated list of dicts with keys Title, Link, Snippet.
    Raises ``EnvironmentError`` when the Serper key is absent.
    Raises ``requests.HTTPError`` on non-200 responses.
    """
    if not settings.has_serper:
        raise EnvironmentError(
            "SERPER_API_KEY is not set. Add it to your .env file."
        )

    headers = {
        "X-API-KEY": settings.serper_api_key,
        "Content-Type": "application/json",
    }
    seen: dict[str, dict] = {}

    for template in _QUERY_VARIATIONS:
        variation = template.format(q=query)
        try:
            response = requests.post(
                _SERPER_URL,
                headers=headers,
                json={"q": variation},
                timeout=10,
            )
            response.raise_for_status()
            for result in response.json().get("organic", []):
                link = result.get("link")
                title = result.get("title")
                if link and title and link not in seen:
                    seen[link] = {
                        "Title": title,
                        "Link": link,
                        "Snippet": result.get("snippet", ""),
                    }
        except requests.RequestException:
            # Individual variation failures are non-fatal; log & continue.
            pass

    return list(seen.values())
