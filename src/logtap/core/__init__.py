"""Core business logic for logtap."""

from logtap.core.reader import tail, tail_async, get_file_lines, get_file_lines_async
from logtap.core.validation import is_filename_valid, is_search_term_valid, is_limit_valid
from logtap.core.search import filter_lines

__all__ = [
    "tail",
    "tail_async",
    "get_file_lines",
    "get_file_lines_async",
    "is_filename_valid",
    "is_search_term_valid",
    "is_limit_valid",
    "filter_lines",
]
