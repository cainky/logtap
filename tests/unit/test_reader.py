"""Unit tests for logtap.core.reader module."""

import tempfile
import os
from pathlib import Path

import pytest

from logtap.core.reader import tail, read_block, get_file_lines


class TestTail:
    """Tests for the tail() function."""

    def test_tail_basic(self, tmp_path: Path):
        """Test basic tail functionality."""
        log_file = tmp_path / "test.log"
        lines = ["line 1", "line 2", "line 3"]
        log_file.write_text("\n".join(lines))

        result = tail(str(log_file), lines_limit=3)
        assert result == lines

    def test_tail_limit(self, tmp_path: Path):
        """Test that tail respects the lines limit."""
        log_file = tmp_path / "test.log"
        lines = [f"log {i}" for i in range(10)]
        log_file.write_text("\n".join(lines))

        result = tail(str(log_file), lines_limit=5)
        # Should return last 5 lines
        assert result == ["log 5", "log 6", "log 7", "log 8", "log 9"]

    def test_tail_large_file(self, tmp_path: Path):
        """Test tail with a large file (1M lines)."""
        log_file = tmp_path / "large.log"
        lines = ["test log line"] * 10**6
        log_file.write_text("\n".join(lines))

        result = tail(str(log_file), lines_limit=10)
        assert len(result) == 10
        assert all(line == "test log line" for line in result)

    def test_tail_empty_file(self, tmp_path: Path):
        """Test tail with an empty file."""
        log_file = tmp_path / "empty.log"
        log_file.write_text("")

        result = tail(str(log_file), lines_limit=10)
        # Empty file returns empty list (no lines to read)
        assert result == []

    def test_tail_utf8(self, tmp_path: Path):
        """Test tail with UTF-8 content."""
        log_file = tmp_path / "utf8.log"
        lines = ["test log containing non-ASCII character: ö", "日本語テスト", "emoji: 🚀"]
        log_file.write_text("\n".join(lines), encoding="utf-8")

        result = tail(str(log_file), lines_limit=3)
        assert result == lines

    def test_tail_preserves_empty_lines(self, tmp_path: Path):
        """Test that tail preserves empty lines."""
        log_file = tmp_path / "test.log"
        lines = ["line 1", "", "line 3"]
        log_file.write_text("\n".join(lines))

        result = tail(str(log_file), lines_limit=3)
        assert result == lines


class TestGetFileLines:
    """Tests for the get_file_lines() function."""

    def test_get_file_lines_no_filter(self, tmp_path: Path):
        """Test get_file_lines without search term."""
        log_file = tmp_path / "test.log"
        lines = ["line 1", "line 2", "line 3"]
        log_file.write_text("\n".join(lines))

        result = get_file_lines(str(log_file), num_lines_to_return=3)
        assert result == lines

    def test_get_file_lines_with_filter(self, tmp_path: Path):
        """Test get_file_lines with search term."""
        log_file = tmp_path / "test.log"
        lines = ["error: something failed", "info: all good", "error: another failure"]
        log_file.write_text("\n".join(lines))

        result = get_file_lines(str(log_file), search_term="error", num_lines_to_return=10)
        assert result == ["error: something failed", "error: another failure"]

    def test_get_file_lines_no_matches(self, tmp_path: Path):
        """Test get_file_lines when search term matches nothing."""
        log_file = tmp_path / "test.log"
        lines = ["line 1", "line 2", "line 3"]
        log_file.write_text("\n".join(lines))

        result = get_file_lines(str(log_file), search_term="nonexistent", num_lines_to_return=10)
        assert result == []

    def test_get_file_lines_utf8_search(self, tmp_path: Path):
        """Test get_file_lines with UTF-8 search term."""
        log_file = tmp_path / "test.log"
        lines = ["test log containing non-ASCII character: ö"]
        log_file.write_text("\n".join(lines), encoding="utf-8")

        result = get_file_lines(str(log_file), search_term="ö", num_lines_to_return=10)
        assert result == lines
