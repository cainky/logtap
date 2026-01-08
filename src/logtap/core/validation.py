"""
Input validation functions for logtap.

These functions validate user input to prevent security issues
like path traversal attacks and DoS via overly large inputs.
"""


def is_filename_valid(filename: str) -> bool:
    """
    Validates a filename for path traversal and absolute paths.

    The filename is considered valid if it does not contain any ".."
    (used for path traversal) and does not start with "/" (indicating an absolute path).

    Args:
        filename: The filename to be checked.

    Returns:
        True if filename is valid, False otherwise.
    """
    return ".." not in filename and not filename.startswith("/")


def is_search_term_valid(search_term: str) -> bool:
    """
    Validates a search term based on its length.

    The search term is considered valid if its length is less than or equal to 100.

    Args:
        search_term: The search term to be checked.

    Returns:
        True if search term is valid, False otherwise.
    """
    return len(search_term) <= 100


def is_limit_valid(limit: int) -> bool:
    """
    Validates a limit for the number of lines to return.

    The limit is considered valid if it's within the range 1 to 1000, inclusive.

    Args:
        limit: The limit to be checked.

    Returns:
        True if limit is valid, False otherwise.
    """
    return 1 <= limit <= 1000
