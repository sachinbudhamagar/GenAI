"""
utils/decorators.py — General-purpose decorators.
"""

from __future__ import annotations

import time
from functools import wraps
from typing import Callable

from src.config import settings


def retry_request(func: Callable) -> Callable:
    """Retry *func* up to ``settings.max_retry_attempts`` times on any exception,
    sleeping ``settings.retry_delay_seconds`` between attempts."""

    @wraps(func)
    def wrapper(*args, **kwargs):
        last_error: Exception | None = None
        for attempt in range(1, settings.max_retry_attempts + 1):
            try:
                return func(*args, **kwargs)
            except Exception as exc:  # noqa: BLE001
                last_error = exc
                if attempt < settings.max_retry_attempts:
                    time.sleep(settings.retry_delay_seconds)
        raise last_error  # type: ignore[misc]

    return wrapper
