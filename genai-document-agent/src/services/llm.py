"""
services/llm.py — Lazy-initialised LLM singleton.

Usage::

    from src.services.llm import get_llm
    llm = get_llm()          # returns None when key is missing
    if llm is None:
        st.error("OpenAI API key missing")
"""

from __future__ import annotations

from langchain_openai import ChatOpenAI

from src.config import settings

_llm: ChatOpenAI | None = None
_initialised = False


def get_llm() -> ChatOpenAI | None:
    """Return the shared ChatOpenAI instance, or *None* if the key is absent."""
    global _llm, _initialised  # noqa: PLW0603
    if not _initialised:
        if settings.has_openai:
            import os
            os.environ.setdefault("OPENAI_API_KEY", settings.openai_api_key)
            _llm = ChatOpenAI(
                model=settings.llm_model,
                temperature=settings.llm_temperature,
            )
        _initialised = True
    return _llm
