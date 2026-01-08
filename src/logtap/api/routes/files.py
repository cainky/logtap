"""File listing endpoint for logtap."""

import os
from typing import Optional

from fastapi import APIRouter, Depends

from logtap.api.dependencies import get_settings, verify_api_key
from logtap.models.config import Settings
from logtap.models.responses import FileListResponse

router = APIRouter()


@router.get("", response_model=FileListResponse)
async def list_files(
    settings: Settings = Depends(get_settings),
    _api_key: Optional[str] = Depends(verify_api_key),
) -> FileListResponse:
    """
    List available log files in the configured log directory.

    Returns:
        List of log file names and the directory path.
    """
    log_dir = settings.get_log_directory()

    # Get list of files (not directories)
    try:
        files = [
            f for f in os.listdir(log_dir)
            if os.path.isfile(os.path.join(log_dir, f))
        ]
        files.sort()
    except OSError:
        files = []

    return FileListResponse(files=files, directory=log_dir)
