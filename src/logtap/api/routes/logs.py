"""Log query endpoints for logtap."""

import os
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from logtap.api.dependencies import get_settings, verify_api_key
from logtap.core.reader import tail_async
from logtap.core.search import filter_lines
from logtap.core.validation import is_filename_valid, is_search_term_valid, is_limit_valid
from logtap.models.config import Settings
from logtap.models.responses import LogResponse

router = APIRouter()


# Error messages (matching original for backward compatibility)
ERROR_INVALID_FILENAME = 'Invalid filename: must not contain ".." or start with "/"'
ERROR_LONG_SEARCH_TERM = "Search term is too long: must be 100 characters or fewer"
ERROR_INVALID_LIMIT = "Invalid limit value: must be between 1 and 1000"


@router.get("", response_model=LogResponse)
async def get_logs(
    filename: str = Query(default="syslog", description="Name of the log file to read"),
    term: str = Query(default="", description="Substring to search for in log lines"),
    regex: Optional[str] = Query(default=None, description="Regex pattern to match log lines"),
    limit: int = Query(default=50, ge=1, le=1000, description="Number of lines to return (1-1000)"),
    case_sensitive: bool = Query(default=True, description="Whether search is case-sensitive"),
    settings: Settings = Depends(get_settings),
    _api_key: Optional[str] = Depends(verify_api_key),
) -> LogResponse:
    """
    Retrieve log entries from a specified log file.

    This endpoint reads the last N lines from a log file and optionally
    filters them by a search term or regex pattern.

    Args:
        filename: Name of the log file (relative to log directory).
        term: Substring to filter lines by.
        regex: Regex pattern to filter lines by (takes precedence over term).
        limit: Maximum number of lines to return.
        case_sensitive: Whether the search should be case-sensitive.

    Returns:
        JSON response with matching log lines.

    Raises:
        HTTPException: If validation fails or file is not found.
    """
    # Validate filename
    if not is_filename_valid(filename):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ERROR_INVALID_FILENAME,
        )

    # Additional filename validation (similar to werkzeug's secure_filename)
    # Block any filename with path separators
    if "/" in filename or "\\" in filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ERROR_INVALID_FILENAME,
        )

    # Validate search term
    if term and not is_search_term_valid(term):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ERROR_LONG_SEARCH_TERM,
        )

    # Validate limit (FastAPI's Query already handles ge/le, but keep for compatibility)
    if not is_limit_valid(limit):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ERROR_INVALID_LIMIT,
        )

    # Build file path
    log_dir = settings.get_log_directory()
    filepath = os.path.join(log_dir, filename)

    # Check file exists
    if not os.path.isfile(filepath):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"File not found: {filepath} does not exist",
        )

    # Read file lines
    lines = await tail_async(filepath, limit)

    # Apply filtering
    if regex:
        lines = filter_lines(lines, regex=regex, case_sensitive=case_sensitive)
    elif term:
        lines = filter_lines(lines, term=term, case_sensitive=case_sensitive)

    return LogResponse(
        lines=lines,
        count=len(lines),
        filename=filename,
    )
