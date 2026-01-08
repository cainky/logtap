"""Unit tests for logtap.core.validation module."""

import pytest

from logtap.core.validation import is_filename_valid, is_search_term_valid, is_limit_valid


class TestIsFilenameValid:
    """Tests for is_filename_valid()."""

    def test_valid_filenames(self):
        """Test that valid filenames pass validation."""
        assert is_filename_valid("syslog") is True
        assert is_filename_valid("auth.log") is True
        assert is_filename_valid("nginx/access.log") is True
        assert is_filename_valid("app.log.1") is True

    def test_path_traversal_rejected(self):
        """Test that path traversal attempts are rejected."""
        assert is_filename_valid("../etc/passwd") is False
        assert is_filename_valid("foo/../bar") is False
        assert is_filename_valid("..") is False

    def test_absolute_paths_rejected(self):
        """Test that absolute paths are rejected."""
        assert is_filename_valid("/etc/passwd") is False
        assert is_filename_valid("/var/log/syslog") is False


class TestIsSearchTermValid:
    """Tests for is_search_term_valid()."""

    def test_valid_search_terms(self):
        """Test that valid search terms pass validation."""
        assert is_search_term_valid("") is True
        assert is_search_term_valid("error") is True
        assert is_search_term_valid("a" * 100) is True

    def test_long_search_term_rejected(self):
        """Test that search terms > 100 chars are rejected."""
        assert is_search_term_valid("a" * 101) is False
        assert is_search_term_valid("a" * 200) is False


class TestIsLimitValid:
    """Tests for is_limit_valid()."""

    def test_valid_limits(self):
        """Test that valid limits pass validation."""
        assert is_limit_valid(1) is True
        assert is_limit_valid(50) is True
        assert is_limit_valid(1000) is True

    def test_invalid_limits(self):
        """Test that invalid limits are rejected."""
        assert is_limit_valid(0) is False
        assert is_limit_valid(-1) is False
        assert is_limit_valid(1001) is False
        assert is_limit_valid(10000) is False
