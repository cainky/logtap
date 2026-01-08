"""
Search and filtering functionality for logtap.

Provides substring and regex-based filtering of log lines.
"""

import re
from typing import List, Optional


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
