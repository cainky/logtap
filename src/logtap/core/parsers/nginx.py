"""Nginx access log parser."""

import re
from datetime import datetime
from typing import Optional

from logtap.core.parsers.base import LogLevel, LogParser, ParsedLogEntry


class NginxParser(LogParser):
    """
    Parser for Nginx access log format (combined log format).

    Example:
    192.168.1.1 - - [08/Jan/2024:10:23:45 +0000] "GET /api HTTP/1.1" 200 45
    """

    # Combined log format pattern
    PATTERN = re.compile(
        r"^(\S+)\s+"  # Remote address
        r"(\S+)\s+"  # Identity (usually -)
        r"(\S+)\s+"  # Remote user (usually -)
        r"\[([^\]]+)\]\s+"  # Time
        r'"([^"]*)"\s+'  # Request
        r"(\d{3})\s+"  # Status
        r"(\d+|-)\s*"  # Bytes
        r'(?:"([^"]*)"\s*)?'  # Referer (optional)
        r'(?:"([^"]*)")?'  # User agent (optional)
    )

    @property
    def name(self) -> str:
        return "nginx"

    def can_parse(self, line: str) -> bool:
        """Check if line matches nginx format."""
        return bool(self.PATTERN.match(line))

    def parse(self, line: str) -> ParsedLogEntry:
        """Parse an nginx access log line."""
        match = self.PATTERN.match(line)

        if not match:
            return ParsedLogEntry(
                raw=line,
                message=line,
                level=self._detect_level_from_content(line),
            )

        groups = match.groups()
        remote_addr = groups[0]
        remote_user = groups[2] if groups[2] != "-" else None
        time_str = groups[3]
        request = groups[4]
        status = int(groups[5])
        bytes_sent = int(groups[6]) if groups[6] != "-" else 0
        referer = groups[7] if len(groups) > 7 and groups[7] != "-" else None
        user_agent = groups[8] if len(groups) > 8 else None

        # Parse timestamp
        timestamp = self._parse_nginx_time(time_str)

        # Determine level based on status code
        level = self._status_to_level(status)

        # Parse request method and path
        request_parts = request.split() if request else []
        method = request_parts[0] if len(request_parts) > 0 else None
        path = request_parts[1] if len(request_parts) > 1 else None

        return ParsedLogEntry(
            raw=line,
            message=f"{method} {path} -> {status}" if method and path else request,
            timestamp=timestamp,
            level=level,
            source=remote_addr,
            metadata={
                "remote_addr": remote_addr,
                "remote_user": remote_user,
                "request": request,
                "method": method,
                "path": path,
                "status": status,
                "bytes_sent": bytes_sent,
                "referer": referer,
                "user_agent": user_agent,
            },
        )

    def _parse_nginx_time(self, time_str: str) -> Optional[datetime]:
        """Parse nginx time format: 08/Jan/2024:10:23:45 +0000"""
        try:
            # Remove timezone for simpler parsing
            time_str = time_str.split()[0] if " " in time_str else time_str
            return datetime.strptime(time_str, "%d/%b/%Y:%H:%M:%S")
        except ValueError:
            return None

    def _status_to_level(self, status: int) -> LogLevel:
        """Convert HTTP status code to log level."""
        if status >= 500:
            return LogLevel.ERROR
        elif status >= 400:
            return LogLevel.WARNING
        elif status >= 300:
            return LogLevel.NOTICE
        else:
            return LogLevel.INFO
