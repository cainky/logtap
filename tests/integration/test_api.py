"""Integration tests for logtap API endpoints.

These tests cover the same cases as the original test_app.py from UnixLogMonitor,
migrated to pytest and FastAPI.
"""

from http import HTTPStatus

import pytest


class TestLogsEndpoint:
    """Tests for GET /logs endpoint."""

    def test_invalid_filename_absolute_path(self, client):
        """Test that absolute paths are rejected."""
        response = client.get("/logs", params={"filename": "/invalid"})
        assert response.status_code == HTTPStatus.BAD_REQUEST

    def test_invalid_filename_path_traversal(self, client):
        """Test that path traversal is rejected."""
        response = client.get("/logs", params={"filename": "../etc/passwd"})
        assert response.status_code == HTTPStatus.BAD_REQUEST

    def test_file_not_found(self, client):
        """Test that missing files return 404."""
        response = client.get("/logs", params={"filename": "nonexistent"})
        assert response.status_code == HTTPStatus.NOT_FOUND

    def test_valid_request(self, client, log_file):
        """Test valid request returns log lines."""
        filename = log_file(["test log"])
        response = client.get(
            "/logs",
            params={"filename": filename, "term": "test", "limit": 1}
        )
        assert response.status_code == HTTPStatus.OK
        data = response.json()
        assert data["lines"] == ["test log"]

    def test_no_matching_lines(self, client, log_file):
        """Test that non-matching search returns empty list."""
        filename = log_file(["test log"])
        response = client.get(
            "/logs",
            params={"filename": filename, "term": "no match"}
        )
        assert response.status_code == HTTPStatus.OK
        data = response.json()
        assert data["lines"] == []

    def test_lines_limit(self, client, log_file):
        """Test that limit parameter is respected."""
        lines = [f"log {i}" for i in range(10)]
        filename = log_file(lines)
        response = client.get(
            "/logs",
            params={"filename": filename, "limit": 5}
        )
        assert response.status_code == HTTPStatus.OK
        data = response.json()
        # Should return last 5 lines
        assert data["lines"] == ["log 5", "log 6", "log 7", "log 8", "log 9"]

    def test_large_files(self, client, log_file):
        """Test handling of large files (1M lines)."""
        lines = ["test log line"] * 10**6
        filename = log_file(lines)
        response = client.get(
            "/logs",
            params={"filename": filename, "limit": 10}
        )
        assert response.status_code == HTTPStatus.OK
        data = response.json()
        assert data["lines"] == ["test log line"] * 10

    def test_default_parameters(self, client, log_file):
        """Test that default parameters work."""
        filename = log_file(["test log"])
        response = client.get("/logs", params={"filename": filename})
        assert response.status_code == HTTPStatus.OK
        data = response.json()
        assert data["lines"] == ["test log"]

    def test_long_search_term(self, client):
        """Test that search terms > 100 chars are rejected."""
        long_term = "a" * 101
        response = client.get("/logs", params={"term": long_term})
        assert response.status_code == HTTPStatus.BAD_REQUEST

    def test_invalid_limit_zero(self, client):
        """Test that limit=0 is rejected."""
        response = client.get("/logs", params={"limit": 0})
        assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY  # FastAPI validation

    def test_invalid_limit_too_high(self, client):
        """Test that limit>1000 is rejected."""
        response = client.get("/logs", params={"limit": 1001})
        assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY  # FastAPI validation

    def test_non_ascii_characters(self, client, log_file):
        """Test UTF-8 content and search."""
        lines = ["test log containing non-ASCII character: ö"]
        filename = log_file(lines)
        response = client.get(
            "/logs",
            params={"filename": filename, "term": "ö"}
        )
        assert response.status_code == HTTPStatus.OK
        data = response.json()
        assert data["lines"] == lines

    def test_multi_line_with_empty(self, client, log_file):
        """Test that empty lines are preserved."""
        lines = ["test log line 1", "", "test log line 2"]
        filename = log_file(lines)
        response = client.get(
            "/logs",
            params={"filename": filename, "limit": 3}
        )
        assert response.status_code == HTTPStatus.OK
        data = response.json()
        assert data["lines"] == lines

    def test_regex_search(self, client, log_file):
        """Test regex search functionality."""
        lines = ["error: connection failed", "info: connected", "error: timeout"]
        filename = log_file(lines)
        response = client.get(
            "/logs",
            params={"filename": filename, "regex": r"error:.*"}
        )
        assert response.status_code == HTTPStatus.OK
        data = response.json()
        assert data["lines"] == ["error: connection failed", "error: timeout"]

    def test_case_insensitive_search(self, client, log_file):
        """Test case-insensitive search."""
        lines = ["Error: failed", "error: timeout", "ERROR: critical"]
        filename = log_file(lines)
        response = client.get(
            "/logs",
            params={"filename": filename, "term": "error", "case_sensitive": False}
        )
        assert response.status_code == HTTPStatus.OK
        data = response.json()
        assert len(data["lines"]) == 3


class TestFilesEndpoint:
    """Tests for GET /files endpoint."""

    def test_list_files(self, client, log_file):
        """Test listing available log files."""
        # Create a test file
        filename = log_file(["test"], filename="testfile.log")
        response = client.get("/files")
        assert response.status_code == HTTPStatus.OK
        data = response.json()
        assert "testfile.log" in data["files"]


class TestHealthEndpoint:
    """Tests for GET /health endpoint."""

    def test_health_check(self, client):
        """Test health endpoint returns healthy status."""
        response = client.get("/health")
        assert response.status_code == HTTPStatus.OK
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data
