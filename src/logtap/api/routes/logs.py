"""Log query endpoints for logtap."""

import asyncio
import os
from typing import Optional

import aiofiles
from fastapi import APIRouter, Depends, HTTPException, Query, WebSocket, WebSocketDisconnect, status
from starlette.responses import StreamingResponse

from logtap.api.dependencies import get_settings, verify_api_key
from logtap.core.reader import tail_async
from logtap.core.search import filter_lines
from logtap.core.validation import is_filename_valid, is_limit_valid, is_search_term_valid
from logtap.models.config import Settings
from logtap.models.responses import LogResponse

router = APIRouter()


# Error messages (matching original for backward compatibility)
ERROR_INVALID_FILENAME = 'Invalid filename: must not contain ".." or start with "/"'
ERROR_LONG_SEARCH_TERM = "Search term is too long: must be 100 characters or fewer"
ERROR_INVALID_LIMIT = "Invalid limit value: must be between 1 and 1000"


def validate_filename(filename: str) -> None:
    """Validate filename and raise HTTPException if invalid."""
    if not is_filename_valid(filename):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ERROR_INVALID_FILENAME,
        )
    # Block any filename with path separators
    if "/" in filename or "\\" in filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ERROR_INVALID_FILENAME,
        )


def get_filepath(filename: str, settings: Settings) -> str:
    """Get full filepath and validate it exists."""
    log_dir = settings.get_log_directory()
    filepath = os.path.join(log_dir, filename)
    if not os.path.isfile(filepath):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"File not found: {filepath} does not exist",
        )
    return filepath


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
    """
    validate_filename(filename)

    if term and not is_search_term_valid(term):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ERROR_LONG_SEARCH_TERM,
        )

    if not is_limit_valid(limit):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ERROR_INVALID_LIMIT,
        )

    filepath = get_filepath(filename, settings)
    lines = await tail_async(filepath, limit)

    if regex:
        lines = filter_lines(lines, regex=regex, case_sensitive=case_sensitive)
    elif term:
        lines = filter_lines(lines, term=term, case_sensitive=case_sensitive)

    return LogResponse(lines=lines, count=len(lines), filename=filename)


@router.get("/multi")
async def get_logs_multi(
    filenames: str = Query(..., description="Comma-separated list of log file names"),
    term: str = Query(default="", description="Substring to search for"),
    regex: Optional[str] = Query(default=None, description="Regex pattern to match"),
    limit: int = Query(default=50, ge=1, le=1000, description="Lines per file"),
    case_sensitive: bool = Query(default=True, description="Case-sensitive search"),
    settings: Settings = Depends(get_settings),
    _api_key: Optional[str] = Depends(verify_api_key),
) -> dict:
    """
    Query multiple log files simultaneously.

    Returns results grouped by filename.
    """
    file_list = [f.strip() for f in filenames.split(",") if f.strip()]

    if not file_list:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No filenames provided",
        )

    if len(file_list) > 10:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Maximum 10 files per request",
        )

    results = {}
    log_dir = settings.get_log_directory()

    for filename in file_list:
        try:
            validate_filename(filename)
            filepath = os.path.join(log_dir, filename)

            if not os.path.isfile(filepath):
                results[filename] = {"error": "File not found", "lines": []}
                continue

            lines = await tail_async(filepath, limit)

            if regex:
                lines = filter_lines(lines, regex=regex, case_sensitive=case_sensitive)
            elif term:
                lines = filter_lines(lines, term=term, case_sensitive=case_sensitive)

            results[filename] = {"lines": lines, "count": len(lines)}

        except HTTPException as e:
            results[filename] = {"error": e.detail, "lines": []}

    return {"results": results, "files_queried": len(file_list)}


@router.websocket("/stream")
async def stream_logs(
    websocket: WebSocket,
    filename: str = Query(default="syslog"),
):
    """
    Stream log file changes in real-time via WebSocket.

    Connect to this endpoint to receive new log lines as they are written.
    Similar to `tail -f`.
    """
    await websocket.accept()

    # Get settings (can't use Depends in WebSocket easily)
    settings = get_settings()

    try:
        validate_filename(filename)
    except HTTPException as e:
        await websocket.send_json({"error": e.detail})
        await websocket.close()
        return

    log_dir = settings.get_log_directory()
    filepath = os.path.join(log_dir, filename)

    if not os.path.isfile(filepath):
        await websocket.send_json({"error": f"File not found: {filename}"})
        await websocket.close()
        return

    try:
        async with aiofiles.open(filepath, mode="r", encoding="utf-8") as f:
            # Seek to end of file
            await f.seek(0, 2)

            while True:
                line = await f.readline()
                if line:
                    await websocket.send_text(line.rstrip("\n"))
                else:
                    # No new content, wait a bit
                    await asyncio.sleep(0.1)

                # Check if client is still connected
                try:
                    # Non-blocking receive to check connection
                    await asyncio.wait_for(websocket.receive_text(), timeout=0.01)
                except asyncio.TimeoutError:
                    # No message, continue streaming
                    pass

    except WebSocketDisconnect:
        pass
    except Exception as e:
        try:
            await websocket.send_json({"error": str(e)})
        except Exception:
            # Connection already closed, ignore
            pass


@router.get("/sse")
async def stream_logs_sse(
    filename: str = Query(default="syslog", description="Log file to stream"),
    settings: Settings = Depends(get_settings),
    _api_key: Optional[str] = Depends(verify_api_key),
):
    """
    Stream log file changes via Server-Sent Events (SSE).

    Alternative to WebSocket for simpler clients.
    """
    validate_filename(filename)
    filepath = get_filepath(filename, settings)

    async def event_generator():
        async with aiofiles.open(filepath, mode="r", encoding="utf-8") as f:
            # Seek to end
            await f.seek(0, 2)

            while True:
                line = await f.readline()
                if line:
                    # SSE format: data: <content>\n\n
                    yield f"data: {line.rstrip()}\n\n"
                else:
                    # Send heartbeat to keep connection alive
                    yield ": heartbeat\n\n"
                    await asyncio.sleep(1)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )
