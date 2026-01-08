"""Syslog format parser."""

import re
from datetime import datetime

from logtap.core.parsers.base import LogParser, ParsedLogEntry


class SyslogParser(LogParser):
    """
    Parser for standard syslog format.

    Handles formats like:
    - Jan  8 10:23:45 hostname process[pid]: message
    - Jan  8 10:23:45 hostname process: message
    """

    # Syslog pattern: Month Day HH:MM:SS hostname process[pid]: message
    PATTERN = re.compile(
        r"^(\w{3}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2})\s+"  # Timestamp
        r"(\S+)\s+"  # Hostname
        r"(\S+?)(?:\[(\d+)\])?:\s+"  # Process[PID]
        r"(.*)$"  # Message
    )

    # Alternative pattern without PID brackets
    PATTERN_ALT = re.compile(
        r"^(\w{3}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2})\s+" r"(\S+)\s+" r"(\S+):\s+" r"(.*)$"
    )

    @property
    def name(self) -> str:
        return "syslog"

    def can_parse(self, line: str) -> bool:
        """Check if line matches syslog format."""
        return bool(self.PATTERN.match(line) or self.PATTERN_ALT.match(line))

    def parse(self, line: str) -> ParsedLogEntry:
        """Parse a syslog line."""
        match = self.PATTERN.match(line)

        if match:
            timestamp_str, hostname, process, pid, message = match.groups()
        else:
            match = self.PATTERN_ALT.match(line)
            if match:
                timestamp_str, hostname, process, message = match.groups()
                pid = None
            else:
                # Can't parse, return basic entry
                return ParsedLogEntry(
                    raw=line,
                    message=line,
                    level=self._detect_level_from_content(line),
                )

        # Parse timestamp (assume current year)
        try:
            timestamp = datetime.strptime(timestamp_str, "%b %d %H:%M:%S")
            # Set to current year
            timestamp = timestamp.replace(year=datetime.now().year)
        except ValueError:
            timestamp = None

        # Detect level from message
        level = self._detect_level_from_content(message)

        return ParsedLogEntry(
            raw=line,
            message=message,
            timestamp=timestamp,
            level=level,
            source=f"{hostname}/{process}",
            metadata={
                "hostname": hostname,
                "process": process,
                "pid": pid,
            },
        )
