"""Apache access log parser."""

import re
from datetime import datetime
from typing import Optional

from logtap.core.parsers.base import LogLevel, LogParser, ParsedLogEntry


class ApacheParser(LogParser):
    """
    Parser for Apache access log format.

    Common combined format:
    %h %l %u %t "%r" %>s %b "%{Referer}i" "%{User-Agent}i"

    Example:
    192.168.1.1 - frank [08/Jan/2024:10:23:45 -0500] "GET / HTTP/1.0" 200 1234
    """

    # Combined log format pattern (same as nginx essentially)
    PATTERN = re.compile(
        r"^(\S+)\s+"  # Remote host
        r"(\S+)\s+"  # Identity
        r"(\S+)\s+"  # Remote user
        r"\[([^\]]+)\]\s+"  # Time
        r'"([^"]*)"\s+'  # Request
        r"(\d{3})\s+"  # Status
        r"(\d+|-)\s*"  # Bytes
        r'(?:"([^"]*)"\s*)?'  # Referer
        r'(?:"([^"]*)")?'  # User agent
    )

    # Error log pattern
    ERROR_PATTERN = re.compile(
        r"^\[([^\]]+)\]\s+"  # Timestamp
        r"\[(\w+)\]\s+"  # Level
        r"(?:\[pid\s+(\d+)\]\s+)?"  # PID (optional)
        r"(?:\[client\s+([^\]]+)\]\s+)?"  # Client (optional)
        r"(.*)$"  # Message
    )

    @property
    def name(self) -> str:
        return "apache"

    def can_parse(self, line: str) -> bool:
        """Check if line matches apache format."""
        return bool(self.PATTERN.match(line) or self.ERROR_PATTERN.match(line))

    def parse(self, line: str) -> ParsedLogEntry:
        """Parse an apache log line."""
        # Try access log format first
        match = self.PATTERN.match(line)
        if match:
            return self._parse_access_log(line, match)

        # Try error log format
        match = self.ERROR_PATTERN.match(line)
        if match:
            return self._parse_error_log(line, match)

        return ParsedLogEntry(
            raw=line,
            message=line,
            level=self._detect_level_from_content(line),
        )

    def _parse_access_log(self, line: str, match: re.Match) -> ParsedLogEntry:
        """Parse apache access log line."""
        groups = match.groups()
        remote_host = groups[0]
        remote_user = groups[2] if groups[2] != "-" else None
        time_str = groups[3]
        request = groups[4]
        status = int(groups[5])
        bytes_sent = int(groups[6]) if groups[6] != "-" else 0
        referer = groups[7] if len(groups) > 7 and groups[7] != "-" else None
        user_agent = groups[8] if len(groups) > 8 else None

        timestamp = self._parse_apache_time(time_str)
        level = self._status_to_level(status)

        request_parts = request.split() if request else []
        method = request_parts[0] if len(request_parts) > 0 else None
        path = request_parts[1] if len(request_parts) > 1 else None

        return ParsedLogEntry(
            raw=line,
            message=f"{method} {path} -> {status}" if method and path else request,
            timestamp=timestamp,
            level=level,
            source=remote_host,
            metadata={
                "remote_host": remote_host,
                "remote_user": remote_user,
                "request": request,
                "method": method,
                "path": path,
                "status": status,
                "bytes_sent": bytes_sent,
                "referer": referer,
                "user_agent": user_agent,
                "log_type": "access",
            },
        )

    def _parse_error_log(self, line: str, match: re.Match) -> ParsedLogEntry:
        """Parse apache error log line."""
        groups = match.groups()
        time_str = groups[0]
        level_str = groups[1]
        pid = groups[2]
        client = groups[3]
        message = groups[4]

        timestamp = self._parse_error_time(time_str)
        level = LogLevel.from_string(level_str) or self._detect_level_from_content(message)

        return ParsedLogEntry(
            raw=line,
            message=message,
            timestamp=timestamp,
            level=level,
            source=client,
            metadata={
                "pid": pid,
                "client": client,
                "log_type": "error",
            },
        )

    def _parse_apache_time(self, time_str: str) -> Optional[datetime]:
        """Parse apache time format: 08/Jan/2024:10:23:45 -0500"""
        try:
            time_str = time_str.split()[0] if " " in time_str else time_str
            return datetime.strptime(time_str, "%d/%b/%Y:%H:%M:%S")
        except ValueError:
            return None

    def _parse_error_time(self, time_str: str) -> Optional[datetime]:
        """Parse apache error log time format."""
        formats = [
            "%a %b %d %H:%M:%S.%f %Y",
            "%a %b %d %H:%M:%S %Y",
            "%Y-%m-%d %H:%M:%S.%f",
            "%Y-%m-%d %H:%M:%S",
        ]
        for fmt in formats:
            try:
                return datetime.strptime(time_str, fmt)
            except ValueError:
                continue
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
