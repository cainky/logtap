"""Base classes for log parsers."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class LogLevel(str, Enum):
    """Standard log severity levels."""

    EMERGENCY = "EMERGENCY"  # System is unusable
    ALERT = "ALERT"  # Action must be taken immediately
    CRITICAL = "CRITICAL"  # Critical conditions
    ERROR = "ERROR"  # Error conditions
    WARNING = "WARNING"  # Warning conditions
    NOTICE = "NOTICE"  # Normal but significant
    INFO = "INFO"  # Informational
    DEBUG = "DEBUG"  # Debug-level messages

    @classmethod
    def from_string(cls, level: str) -> Optional["LogLevel"]:
        """Parse a log level from string."""
        level_map = {
            # Standard names
            "emergency": cls.EMERGENCY,
            "emerg": cls.EMERGENCY,
            "alert": cls.ALERT,
            "critical": cls.CRITICAL,
            "crit": cls.CRITICAL,
            "error": cls.ERROR,
            "err": cls.ERROR,
            "warning": cls.WARNING,
            "warn": cls.WARNING,
            "notice": cls.NOTICE,
            "info": cls.INFO,
            "information": cls.INFO,
            "informational": cls.INFO,
            "debug": cls.DEBUG,
            # Numeric syslog levels
            "0": cls.EMERGENCY,
            "1": cls.ALERT,
            "2": cls.CRITICAL,
            "3": cls.ERROR,
            "4": cls.WARNING,
            "5": cls.NOTICE,
            "6": cls.INFO,
            "7": cls.DEBUG,
        }
        return level_map.get(level.lower())

    @property
    def severity(self) -> int:
        """Get numeric severity (0=most severe, 7=least severe)."""
        severity_map = {
            LogLevel.EMERGENCY: 0,
            LogLevel.ALERT: 1,
            LogLevel.CRITICAL: 2,
            LogLevel.ERROR: 3,
            LogLevel.WARNING: 4,
            LogLevel.NOTICE: 5,
            LogLevel.INFO: 6,
            LogLevel.DEBUG: 7,
        }
        return severity_map[self]


@dataclass
class ParsedLogEntry:
    """A parsed log entry with structured fields."""

    raw: str  # Original log line
    message: str  # Main message content
    timestamp: Optional[datetime] = None
    level: Optional[LogLevel] = None
    source: Optional[str] = None  # hostname, process, etc.
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "raw": self.raw,
            "message": self.message,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "level": self.level.value if self.level else None,
            "source": self.source,
            "metadata": self.metadata,
        }


class LogParser(ABC):
    """Abstract base class for log parsers."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Name of this parser format."""
        pass

    @abstractmethod
    def can_parse(self, line: str) -> bool:
        """
        Check if this parser can handle the given line.

        Args:
            line: A log line to check.

        Returns:
            True if this parser can parse the line.
        """
        pass

    @abstractmethod
    def parse(self, line: str) -> ParsedLogEntry:
        """
        Parse a log line into structured format.

        Args:
            line: The log line to parse.

        Returns:
            A ParsedLogEntry with extracted fields.
        """
        pass

    def parse_many(self, lines: List[str]) -> List[ParsedLogEntry]:
        """
        Parse multiple log lines.

        Args:
            lines: List of log lines to parse.

        Returns:
            List of ParsedLogEntry objects.
        """
        return [self.parse(line) for line in lines]

    def _detect_level_from_content(self, content: str) -> Optional[LogLevel]:
        """
        Detect log level from message content.

        Common patterns like "ERROR:", "[error]", etc.
        """
        content_lower = content.lower()

        # Check for explicit level indicators
        level_patterns = [
            (["emergency", "emerg"], LogLevel.EMERGENCY),
            (["alert"], LogLevel.ALERT),
            (["critical", "crit", "fatal"], LogLevel.CRITICAL),
            (["error", "err", "fail", "failed"], LogLevel.ERROR),
            (["warning", "warn"], LogLevel.WARNING),
            (["notice"], LogLevel.NOTICE),
            (["info"], LogLevel.INFO),
            (["debug", "trace"], LogLevel.DEBUG),
        ]

        for patterns, level in level_patterns:
            for pattern in patterns:
                if pattern in content_lower:
                    return level

        return None
