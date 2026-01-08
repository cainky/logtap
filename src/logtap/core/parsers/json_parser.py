"""JSON log format parser."""

import json
from datetime import datetime
from typing import Any, Dict, Optional

from logtap.core.parsers.base import LogLevel, LogParser, ParsedLogEntry


class JsonLogParser(LogParser):
    """
    Parser for JSON-formatted log lines.

    Handles common JSON log formats with fields like:
    - message, msg, log
    - level, severity, loglevel
    - timestamp, time, @timestamp, ts
    - source, logger, name
    """

    # Common field names for each attribute
    MESSAGE_FIELDS = ["message", "msg", "log", "text", "body"]
    LEVEL_FIELDS = ["level", "severity", "loglevel", "log_level", "lvl"]
    TIMESTAMP_FIELDS = ["timestamp", "time", "@timestamp", "ts", "datetime", "date"]
    SOURCE_FIELDS = ["source", "logger", "name", "service", "app", "application"]

    @property
    def name(self) -> str:
        return "json"

    def can_parse(self, line: str) -> bool:
        """Check if line is valid JSON."""
        line = line.strip()
        if not line.startswith("{"):
            return False
        try:
            json.loads(line)
            return True
        except (json.JSONDecodeError, ValueError):
            return False

    def parse(self, line: str) -> ParsedLogEntry:
        """Parse a JSON log line."""
        try:
            data = json.loads(line.strip())
        except (json.JSONDecodeError, ValueError):
            return ParsedLogEntry(
                raw=line,
                message=line,
                level=self._detect_level_from_content(line),
            )

        # Extract message
        message = self._get_field(data, self.MESSAGE_FIELDS, line)

        # Extract level
        level_str = self._get_field(data, self.LEVEL_FIELDS)
        level = None
        if level_str:
            level = LogLevel.from_string(str(level_str))
        if not level:
            level = self._detect_level_from_content(message)

        # Extract timestamp
        timestamp_str = self._get_field(data, self.TIMESTAMP_FIELDS)
        timestamp = self._parse_timestamp(timestamp_str) if timestamp_str else None

        # Extract source
        source = self._get_field(data, self.SOURCE_FIELDS)

        return ParsedLogEntry(
            raw=line,
            message=message,
            timestamp=timestamp,
            level=level,
            source=source,
            metadata=data,
        )

    def _get_field(self, data: Dict[str, Any], field_names: list, default: Any = None) -> Any:
        """Get first matching field from data."""
        for field in field_names:
            if field in data:
                return data[field]
            # Check case-insensitive
            for key in data:
                if key.lower() == field.lower():
                    return data[key]
        return default

    def _parse_timestamp(self, value: Any) -> Optional[datetime]:
        """Parse timestamp from various formats."""
        if isinstance(value, datetime):
            return value

        if isinstance(value, (int, float)):
            # Unix timestamp
            try:
                return datetime.fromtimestamp(value)
            except (ValueError, OSError):
                pass

        if isinstance(value, str):
            # Try common formats
            formats = [
                "%Y-%m-%dT%H:%M:%S.%fZ",
                "%Y-%m-%dT%H:%M:%SZ",
                "%Y-%m-%dT%H:%M:%S.%f",
                "%Y-%m-%dT%H:%M:%S",
                "%Y-%m-%d %H:%M:%S.%f",
                "%Y-%m-%d %H:%M:%S",
            ]
            for fmt in formats:
                try:
                    return datetime.strptime(value, fmt)
                except ValueError:
                    continue

        return None
