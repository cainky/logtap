"""Response models for logtap API."""

from typing import List, Optional

from pydantic import BaseModel, Field


class LogResponse(BaseModel):
    """Response model for log queries."""

    lines: List[str] = Field(description="Log lines matching the query")
    count: int = Field(description="Number of lines returned")
    filename: str = Field(description="Name of the log file queried")

    model_config = {
        "json_schema_extra": {
            "example": {
                "lines": [
                    "Jan  8 10:23:45 server sshd[1234]: Accepted publickey",
                    "Jan  8 10:23:46 server systemd[1]: Started session",
                ],
                "count": 2,
                "filename": "syslog",
            }
        }
    }


class ErrorResponse(BaseModel):
    """Response model for errors."""

    error: str = Field(description="Error message")
    detail: Optional[str] = Field(default=None, description="Additional error details")

    model_config = {
        "json_schema_extra": {
            "example": {
                "error": "File not found",
                "detail": "/var/log/nonexistent does not exist",
            }
        }
    }


class FileListResponse(BaseModel):
    """Response model for listing available log files."""

    files: List[str] = Field(description="List of available log files")
    directory: str = Field(description="Log directory path")

    model_config = {
        "json_schema_extra": {
            "example": {
                "files": ["syslog", "auth.log", "kern.log", "dpkg.log"],
                "directory": "/var/log",
            }
        }
    }


class HealthResponse(BaseModel):
    """Response model for health check."""

    status: str = Field(default="healthy", description="Service status")
    version: str = Field(description="logtap version")
