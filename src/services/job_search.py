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

    Raises:
        EnvironmentError: When the Serper key is absent.
        RuntimeError: When ALL query variations fail (carries the last error message).
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
    warnings: list[str] = []

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
        except requests.HTTPError as exc:
            # HTTP errors (401 bad key, 429 rate limit, etc.) are fatal for all
            # variations — raise immediately with a clear message.
            status = exc.response.status_code if exc.response is not None else "?"
            raise RuntimeError(
                f"Serper API returned HTTP {status}. "
                "Check your SERPER_API_KEY and account status."
            ) from exc
        except requests.RequestException as exc:
            # Network-level errors (timeout, DNS) — collect and continue.
            warnings.append(f"Search failed for '{variation}': {exc}")

    # If every single variation raised a network error and we got nothing, surface it.
    if not seen and warnings:
        raise RuntimeError(
            "All job search requests failed:\n" + "\n".join(warnings)
        )

    return list(seen.values())
