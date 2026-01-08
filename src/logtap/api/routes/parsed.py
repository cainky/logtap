"""Parsed log endpoints for logtap - with format detection and severity filtering."""

import os
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from logtap.api.dependencies import get_settings, verify_api_key
from logtap.core.parsers import AutoParser, LogLevel
from logtap.core.reader import tail_async
from logtap.core.search import filter_entries
from logtap.models.config import Settings

router = APIRouter()


@router.get("")
async def get_parsed_logs(
    filename: str = Query(default="syslog", description="Name of the log file to read"),
    term: str = Query(default="", description="Substring to search for"),
    regex: Optional[str] = Query(default=None, description="Regex pattern to match"),
    limit: int = Query(default=50, ge=1, le=1000, description="Number of lines"),
    level: Optional[str] = Query(
        default=None,
        description="Minimum severity level (DEBUG, INFO, WARNING, ERROR, CRITICAL)",
    ),
    levels: Optional[str] = Query(
        default=None,
        description="Comma-separated list of specific levels to include",
    ),
    case_sensitive: bool = Query(default=True),
    settings: Settings = Depends(get_settings),
    _api_key: Optional[str] = Depends(verify_api_key),
) -> dict:
    """
    Retrieve and parse log entries with format auto-detection.

    Returns structured log data with extracted fields like timestamp,
    severity level, source, and message. Supports filtering by severity.

    Supported formats: syslog, JSON, nginx, apache (auto-detected).
    """
    # Validate filename
    if ".." in filename or filename.startswith("/") or "/" in filename or "\\" in filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Invalid filename: must not contain ".." or start with "/"',
        )

    # Build file path
    log_dir = settings.get_log_directory()
    filepath = os.path.join(log_dir, filename)

    if not os.path.isfile(filepath):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"File not found: {filepath} does not exist",
        )

    # Read file lines
    lines = await tail_async(filepath, limit)

    # Parse lines
    parser = AutoParser()
    entries = parser.parse_many(lines)

    # Parse level filter
    min_level = None
    if level:
        min_level = LogLevel.from_string(level)
        if not min_level:
            valid = "DEBUG, INFO, NOTICE, WARNING, ERROR, CRITICAL, ALERT, EMERGENCY"
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid level: {level}. Valid levels: {valid}",
            )

    # Parse levels filter
    level_list = None
    if levels:
        level_list = []
        for lvl in levels.split(","):
            parsed = LogLevel.from_string(lvl.strip())
            if parsed:
                level_list.append(parsed)

    # Apply filters
    filtered = filter_entries(
        entries,
        term=term if term else None,
        regex=regex,
        min_level=min_level,
        levels=level_list,
        case_sensitive=case_sensitive,
    )

    return {
        "entries": [e.to_dict() for e in filtered],
        "count": len(filtered),
        "filename": filename,
        "format": parser.name,
    }
