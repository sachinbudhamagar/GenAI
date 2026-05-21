"""
tests/test_utils_text.py — Unit tests for src.utils.text
"""

import pytest
from src.utils.text import clean_markdown, is_valid_url


class TestCleanMarkdown:
    def test_removes_bold(self):
        assert clean_markdown("**hello** world") == "hello world"

    def test_no_markdown(self):
        assert clean_markdown("plain text") == "plain text"

    def test_multiple_bold(self):
        assert clean_markdown("**a** and **b**") == "a and b"


class TestIsValidUrl:
    @pytest.mark.parametrize(
        "url",
        [
            "https://example.com",
            "http://jobs.example.co.uk/listings?id=1",
            "https://www.linkedin.com/jobs/view/123",
        ],
    )
    def test_valid_urls(self, url: str):
        assert is_valid_url(url) is True

    @pytest.mark.parametrize(
        "url",
        [
            "not-a-url",
            "ftp://old.protocol.com",
            "",
            "javascript:alert(1)",
        ],
    )
    def test_invalid_urls(self, url: str):
        assert is_valid_url(url) is False
