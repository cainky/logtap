"""Auto-detection and parsing of log formats."""

from typing import List, Optional, Type

from logtap.core.parsers.apache import ApacheParser
from logtap.core.parsers.base import LogParser, ParsedLogEntry
from logtap.core.parsers.json_parser import JsonLogParser
from logtap.core.parsers.nginx import NginxParser
from logtap.core.parsers.syslog import SyslogParser

# Parser priority order (more specific formats first)
PARSERS: List[Type[LogParser]] = [
    JsonLogParser,  # JSON is very specific
    NginxParser,  # Nginx before Apache (almost identical)
    ApacheParser,
    SyslogParser,  # Syslog is more generic, try last
]


def detect_format(lines: List[str], sample_size: int = 10) -> Optional[LogParser]:
    """
    Detect the log format by sampling lines.

    Args:
        lines: List of log lines to analyze.
        sample_size: Number of lines to sample for detection.

    Returns:
        A LogParser instance that can handle the format, or None.
    """
    if not lines:
        return None

    # Sample lines from the input
    sample = lines[:sample_size]

    # Try each parser and count successes
    parser_scores = {}

    for parser_cls in PARSERS:
        parser = parser_cls()
        matches = sum(1 for line in sample if line.strip() and parser.can_parse(line))
        if matches > 0:
            parser_scores[parser_cls] = matches / len([line for line in sample if line.strip()])

    if not parser_scores:
        return None

    # Return parser with highest match rate
    best_parser_cls = max(parser_scores, key=parser_scores.get)
    return best_parser_cls()


class AutoParser(LogParser):
    """
    Parser that auto-detects the log format.

    On first parse, it samples lines to detect the format,
    then uses the appropriate parser for subsequent lines.
    """

    def __init__(self):
        self._detected_parser: Optional[LogParser] = None
        self._parsers = [cls() for cls in PARSERS]

    @property
    def name(self) -> str:
        if self._detected_parser:
            return f"auto:{self._detected_parser.name}"
        return "auto"

    def can_parse(self, line: str) -> bool:
        """Auto parser can attempt to parse any line."""
        return True

    def parse(self, line: str) -> ParsedLogEntry:
        """Parse a line, auto-detecting format if needed."""
        line = line.strip()

        if not line:
            return ParsedLogEntry(raw=line, message=line)

        # If we've detected a format, use it
        if self._detected_parser and self._detected_parser.can_parse(line):
            return self._detected_parser.parse(line)

        # Try each parser in order
        for parser in self._parsers:
            if parser.can_parse(line):
                self._detected_parser = parser
                return parser.parse(line)

        # Fallback: return unparsed entry
        return ParsedLogEntry(
            raw=line,
            message=line,
            level=self._detect_level_from_content(line),
        )

    def parse_many(self, lines: List[str]) -> List[ParsedLogEntry]:
        """
        Parse multiple lines with format detection.

        Uses the first few lines to detect format, then applies
        consistently to all lines.
        """
        if not lines:
            return []

        # Detect format from sample
        self._detected_parser = detect_format(lines)

        # Parse all lines
        return [self.parse(line) for line in lines]

    def reset(self):
        """Reset format detection."""
        self._detected_parser = None
