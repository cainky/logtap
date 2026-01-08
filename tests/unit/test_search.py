"""Unit tests for logtap.core.search module."""

import pytest

from logtap.core.search import filter_lines


class TestFilterLines:
    """Tests for filter_lines()."""

    def test_no_filter(self):
        """Test that lines pass through when no filter is applied."""
        lines = ["line 1", "line 2", "line 3"]
        result = filter_lines(lines)
        assert result == lines

    def test_substring_filter(self):
        """Test substring filtering."""
        lines = ["error: failed", "info: ok", "error: timeout"]
        result = filter_lines(lines, term="error")
        assert result == ["error: failed", "error: timeout"]

    def test_substring_filter_case_sensitive(self):
        """Test case-sensitive substring filtering."""
        lines = ["Error: failed", "error: timeout", "ERROR: critical"]
        result = filter_lines(lines, term="error", case_sensitive=True)
        assert result == ["error: timeout"]

    def test_substring_filter_case_insensitive(self):
        """Test case-insensitive substring filtering."""
        lines = ["Error: failed", "error: timeout", "ERROR: critical"]
        result = filter_lines(lines, term="error", case_sensitive=False)
        assert result == ["Error: failed", "error: timeout", "ERROR: critical"]

    def test_regex_filter(self):
        """Test regex filtering."""
        lines = ["error: connection failed", "info: connected", "error: timeout"]
        result = filter_lines(lines, regex=r"error:.*failed")
        assert result == ["error: connection failed"]

    def test_regex_filter_case_insensitive(self):
        """Test case-insensitive regex filtering."""
        lines = ["ERROR: failed", "error: timeout"]
        result = filter_lines(lines, regex=r"error:", case_sensitive=False)
        assert result == ["ERROR: failed", "error: timeout"]

    def test_invalid_regex_returns_empty(self):
        """Test that invalid regex returns empty list."""
        lines = ["line 1", "line 2"]
        result = filter_lines(lines, regex=r"[invalid")
        assert result == []

    def test_regex_takes_precedence_over_term(self):
        """Test that regex takes precedence when both are provided."""
        lines = ["error: failed", "error: timeout", "warning: slow"]
        # If regex is provided, term should be ignored
        result = filter_lines(lines, term="warning", regex=r"error:")
        assert result == ["error: failed", "error: timeout"]

    def test_empty_lines_preserved(self):
        """Test that empty lines are preserved in results."""
        lines = ["error", "", "error again"]
        result = filter_lines(lines, term="error")
        assert result == ["error", "error again"]

    def test_no_matches(self):
        """Test that no matches returns empty list."""
        lines = ["line 1", "line 2"]
        result = filter_lines(lines, term="nonexistent")
        assert result == []
