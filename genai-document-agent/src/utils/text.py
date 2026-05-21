"""
utils/text.py — Pure text-manipulation helpers (no I/O, no Streamlit).
"""

from __future__ import annotations

import re


def clean_markdown(text: str) -> str:
    """Strip common Markdown bold markers from *text*."""
    return re.sub(r"\*\*(.*?)\*\*", r"\1", text)


def is_valid_url(url: str) -> bool:
    """Return True when *url* looks like a well-formed http/https URL."""
    pattern = r"^https?://[^\s/$.?#].[^\s]*$"
    return bool(re.match(pattern, url.strip(), re.IGNORECASE))
