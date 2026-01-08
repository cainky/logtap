"""Log format parsers for logtap."""

from logtap.core.parsers.base import LogParser, ParsedLogEntry, LogLevel
from logtap.core.parsers.syslog import SyslogParser
from logtap.core.parsers.json_parser import JsonLogParser
from logtap.core.parsers.nginx import NginxParser
from logtap.core.parsers.apache import ApacheParser
from logtap.core.parsers.auto import AutoParser, detect_format

__all__ = [
    "LogParser",
    "ParsedLogEntry",
    "LogLevel",
    "SyslogParser",
    "JsonLogParser",
    "NginxParser",
    "ApacheParser",
    "AutoParser",
    "detect_format",
]
