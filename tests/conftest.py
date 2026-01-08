"""Pytest configuration and fixtures for logtap tests."""

import os
import tempfile
from pathlib import Path
from typing import Generator

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def test_log_dir(tmp_path: Path) -> Path:
    """Create a temporary log directory for testing."""
    log_dir = tmp_path / "log"
    log_dir.mkdir()
    return log_dir


@pytest.fixture
def app(test_log_dir: Path, monkeypatch):
    """Create a FastAPI test app with test configuration."""
    # Set environment variables before importing the app
    monkeypatch.setenv("LOGTAP_LOG_DIRECTORY", str(test_log_dir))
    monkeypatch.setenv("LOGTAP_TESTING", "true")

    # Clear the settings cache
    from logtap.api.dependencies import get_settings
    get_settings.cache_clear()

    # Import and create app
    from logtap.api.app import create_app
    return create_app()


@pytest.fixture
def client(app) -> TestClient:
    """Create a test client for the FastAPI app."""
    return TestClient(app)


@pytest.fixture
def log_file(test_log_dir: Path):
    """Factory fixture for creating test log files."""
    created_files = []

    def _create_log_file(lines: list[str], filename: str = None) -> str:
        """
        Create a log file with the given lines.

        Args:
            lines: List of log lines to write.
            filename: Optional filename. If not provided, a unique name is generated.

        Returns:
            The filename (not full path) of the created file.
        """
        if filename is None:
            fd, path = tempfile.mkstemp(dir=test_log_dir)
            os.close(fd)
            filename = Path(path).name
        else:
            path = test_log_dir / filename

        with open(path, "w", encoding="utf-8") as f:
            for index, line in enumerate(lines):
                # Don't add newline after last line (matches original test behavior)
                if index == len(lines) - 1:
                    f.write(line)
                else:
                    f.write(f"{line}\n")

        created_files.append(path)
        return filename

    yield _create_log_file

    # Cleanup (though tmp_path should handle this)
    for path in created_files:
        try:
            os.unlink(path)
        except OSError:
            pass
