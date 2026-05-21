"""
config.py — Application-wide settings loaded from environment variables.

All other modules should import from here instead of calling os.getenv directly.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    openai_api_key: str = field(
        default_factory=lambda: (
            os.getenv("OPENAI_API_KEY") or os.getenv("OpenAI_API_Key") or ""
        )
    )
    serper_api_key: str = field(
        default_factory=lambda: (
            os.getenv("SERPER_API_KEY") or os.getenv("Serper_API_Key") or ""
        )
    )
    llm_model: str = field(default_factory=lambda: os.getenv("LLM_MODEL", "gpt-4o-mini"))
    llm_temperature: float = field(
        default_factory=lambda: float(os.getenv("LLM_TEMPERATURE", "0.3"))
    )
    max_retry_attempts: int = field(
        default_factory=lambda: int(os.getenv("MAX_RETRY_ATTEMPTS", "3"))
    )
    retry_delay_seconds: float = field(
        default_factory=lambda: float(os.getenv("RETRY_DELAY_SECONDS", "2.0"))
    )
    top_jobs_count: int = field(
        default_factory=lambda: int(os.getenv("TOP_JOBS_COUNT", "10"))
    )
    max_jobs_to_score: int = field(
        default_factory=lambda: int(os.getenv("MAX_JOBS_TO_SCORE", "30"))
    )

    @property
    def has_openai(self) -> bool:
        return bool(self.openai_api_key)

    @property
    def has_serper(self) -> bool:
        return bool(self.serper_api_key)


# Singleton — import this everywhere
settings = Settings()
