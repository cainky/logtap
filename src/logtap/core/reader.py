"""
Core file reading functionality for logtap.

The tail() function is the heart of logtap - an efficient O(n) algorithm that reads
files from the end backwards in chunks, avoiding the need to load entire files into memory.
"""

from os import SEEK_END
from typing import IO, List, Optional, Tuple

import aiofiles


def tail(filename: str, lines_limit: int = 50, block_size: int = 1024) -> List[str]:
    """
    Reads a file in reverse and returns its last 'lines_limit' lines.

    This is an efficient algorithm that reads from the end of the file backwards
    in chunks, making it suitable for very large log files.

    Args:
        filename: The path to the file to be read.
        lines_limit: The maximum number of lines to be returned. Defaults to 50.
        block_size: The number of bytes to read at a time. Defaults to 1024.

    Returns:
        A list of the last 'lines_limit' lines in the file.
    """
    lines: List[str] = []
    with open(filename, "r", encoding="utf-8") as f:
        # Seek to the end of the file.
        f.seek(0, SEEK_END)
        # Get the current position in the file.
        block_end_byte = f.tell()

        # Continue reading blocks and adding lines until we have enough lines
        # or reach the start of the file.
        while len(lines) < lines_limit and block_end_byte > 0:
            # Read a block from the file, update the block_end_byte position,
            # and get the new lines.
            new_lines, block_end_byte = read_block(f, block_end_byte, block_size)
            lines.extend(new_lines)

        # Return the last 'lines_limit' lines
        return lines[-lines_limit:]


def read_block(file: IO, block_end_byte: int, block_size: int) -> Tuple[List[str], int]:
    """
    Reads a block from the end of a file and returns the lines in the block.

    Args:
        file: The file object to read from.
        block_end_byte: The current position in the file.
        block_size: The number of bytes to read at a time.

    Returns:
        A tuple containing the list of lines in the block,
        and the updated position in the file.
    """
    # Use min() to ensure we only step back as far as we can (start of file)
    stepback = min(block_size, block_end_byte)

    # Step back and read a block from the file
    file.seek(block_end_byte - stepback)
    block = file.read(stepback)
    block_end_byte -= stepback
    lines = block.split("\n")

    return lines, block_end_byte


async def tail_async(
    filename: str, lines_limit: int = 50, block_size: int = 1024
) -> List[str]:
    """
    Async version of tail() for use with FastAPI.

    Reads a file in reverse and returns its last 'lines_limit' lines.

    Args:
        filename: The path to the file to be read.
        lines_limit: The maximum number of lines to be returned. Defaults to 50.
        block_size: The number of bytes to read at a time. Defaults to 1024.

    Returns:
        A list of the last 'lines_limit' lines in the file.
    """
    lines: List[str] = []
    async with aiofiles.open(filename, "r", encoding="utf-8") as f:
        # Seek to the end of the file.
        await f.seek(0, SEEK_END)
        # Get the current position in the file.
        block_end_byte = await f.tell()

        # Continue reading blocks and adding lines until we have enough lines
        # or reach the start of the file.
        while len(lines) < lines_limit and block_end_byte > 0:
            # Read a block from the file
            stepback = min(block_size, block_end_byte)
            await f.seek(block_end_byte - stepback)
            block = await f.read(stepback)
            block_end_byte -= stepback
            new_lines = block.split("\n")
            lines.extend(new_lines)

        # Return the last 'lines_limit' lines
        return lines[-lines_limit:]


def get_file_lines(
    filepath: str,
    search_term: Optional[str] = None,
    num_lines_to_return: int = 50,
) -> List[str]:
    """
    Retrieves a specified number of lines from a file,
    optionally filtering for a search term.

    Args:
        filepath: Path to the file.
        search_term: Term to filter lines. If None or empty, no filtering is applied.
        num_lines_to_return: Number of lines to retrieve from the end of the file.

    Returns:
        List of lines from the file.
    """
    lines = tail(filepath, num_lines_to_return)

    if search_term:
        lines = [line for line in lines if search_term in line]

    return lines


async def get_file_lines_async(
    filepath: str,
    search_term: Optional[str] = None,
    num_lines_to_return: int = 50,
) -> List[str]:
    """
    Async version of get_file_lines() for use with FastAPI.

    Retrieves a specified number of lines from a file,
    optionally filtering for a search term.

    Args:
        filepath: Path to the file.
        search_term: Term to filter lines. If None or empty, no filtering is applied.
        num_lines_to_return: Number of lines to retrieve from the end of the file.

    Returns:
        List of lines from the file.
    """
    lines = await tail_async(filepath, num_lines_to_return)

    if search_term:
        lines = [line for line in lines if search_term in line]

    return lines
