"""
Search and filtering functionality for logtap.

Provides substring, regex-based, and severity-based filtering of log lines.
"""

import re
from typing import List, Optional, Set

from logtap.core.parsers.base import LogLevel, ParsedLogEntry


def filter_lines(
    lines: List[str],
    term: Optional[str] = None,
    regex: Optional[str] = None,
    case_sensitive: bool = True,
) -> List[str]:
    """
    Filter lines by substring or regex pattern.

    Args:
        lines: List of log lines to filter.
        term: Substring to search for. If provided, only lines containing
              this term will be returned.
        regex: Regular expression pattern to match. If provided, only lines
               matching this pattern will be returned. Takes precedence over term.
        case_sensitive: Whether the search should be case-sensitive.
                       Defaults to True.

    Returns:
        Filtered list of lines matching the criteria.
    """
    if not term and not regex:
        return lines

    if regex:
        flags = 0 if case_sensitive else re.IGNORECASE
        try:
            pattern = re.compile(regex, flags)
            return [line for line in lines if pattern.search(line)]
        except re.error:
            # Invalid regex, return empty list
            return []

    if term:
        if case_sensitive:
            return [line for line in lines if term in line]
        return [line for line in lines if term.lower() in line.lower()]

    return lines


def filter_by_level(
    entries: List[ParsedLogEntry],
    min_level: Optional[LogLevel] = None,
    levels: Optional[List[LogLevel]] = None,
) -> List[ParsedLogEntry]:
    """
    Filter parsed log entries by severity level.

    Args:
        entries: List of ParsedLogEntry objects to filter.
        min_level: Minimum severity level to include. Entries at this level
                  or more severe will be included.
        levels: Specific levels to include. If provided, only entries with
               these exact levels will be returned.

    Returns:
        Filtered list of ParsedLogEntry objects.

    Example:
        # Get only ERROR and more severe
        filter_by_level(entries, min_level=LogLevel.ERROR)

        # Get only WARNING and ERROR
        filter_by_level(entries, levels=[LogLevel.WARNING, LogLevel.ERROR])
    """
    if not min_level and not levels:
        return entries

    if levels:
        level_set: Set[LogLevel] = set(levels)
        return [e for e in entries if e.level in level_set]

    if min_level:
        min_severity = min_level.severity
        return [
            e for e in entries
            if e.level is not None and e.level.severity <= min_severity
        ]

    return entries


def filter_entries(
    entries: List[ParsedLogEntry],
    term: Optional[str] = None,
    regex: Optional[str] = None,
    min_level: Optional[LogLevel] = None,
    levels: Optional[List[LogLevel]] = None,
    case_sensitive: bool = True,
) -> List[ParsedLogEntry]:
    """
    Filter parsed log entries by multiple criteria.

    Combines text search and level filtering.

    Args:
        entries: List of ParsedLogEntry objects to filter.
        term: Substring to search for in the message.
        regex: Regex pattern to match against the message.
        min_level: Minimum severity level to include.
        levels: Specific levels to include.
        case_sensitive: Whether text search is case-sensitive.

    Returns:
        Filtered list of ParsedLogEntry objects matching all criteria.
    """
    result = entries

    # Apply level filter first (usually more restrictive)
    if min_level or levels:
        result = filter_by_level(result, min_level=min_level, levels=levels)

    # Apply text filter
    if term or regex:
        if regex:
            flags = 0 if case_sensitive else re.IGNORECASE
            try:
                pattern = re.compile(regex, flags)
                result = [e for e in result if pattern.search(e.message)]
            except re.error:
                result = []
        elif term:
            if case_sensitive:
                result = [e for e in result if term in e.message]
            else:
                term_lower = term.lower()
                result = [e for e in result if term_lower in e.message.lower()]

    return result
