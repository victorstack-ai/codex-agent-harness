"""FileReadTool -- read the contents of a file from the local filesystem.

Provides a safe, bounded file-read operation suitable for agent workflows.
A configurable ``max_bytes`` limit prevents the agent from accidentally
loading very large files into context.
"""

from __future__ import annotations

import os
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..registry import ToolRegistry

DEFAULT_MAX_BYTES = 100_000  # ~100 KB


def file_read(path: str, max_bytes: int = DEFAULT_MAX_BYTES) -> str:
    """Read and return the contents of the file at *path*.

    Parameters
    ----------
    path:
        Absolute or relative filesystem path to read.
    max_bytes:
        Maximum number of bytes to read.  Defaults to 100 000.

    Returns
    -------
    str
        The file contents (truncated to *max_bytes* if necessary).

    Raises
    ------
    FileNotFoundError
        If *path* does not exist.
    IsADirectoryError
        If *path* points to a directory.
    """
    path = os.path.expanduser(path)
    if not os.path.exists(path):
        raise FileNotFoundError(f"No such file: {path}")
    if os.path.isdir(path):
        raise IsADirectoryError(f"Is a directory: {path}")

    with open(path, "r", encoding="utf-8", errors="replace") as fh:
        return fh.read(max_bytes)


def register(registry: ToolRegistry) -> None:
    """Register :func:`file_read` on *registry*."""
    registry.tool(file_read)
