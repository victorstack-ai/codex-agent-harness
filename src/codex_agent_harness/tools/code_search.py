"""CodeSearchTool -- search files for lines matching a regular expression.

Recursively walks a directory tree and returns matching lines annotated with
file paths and line numbers, similar to ``grep -rn``.
"""

from __future__ import annotations

import os
import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..registry import ToolRegistry

DEFAULT_MAX_RESULTS = 50


def code_search(
    pattern: str,
    directory: str = ".",
    file_glob: str = "*.py",
    max_results: int = DEFAULT_MAX_RESULTS,
) -> str:
    """Search for *pattern* across files under *directory*.

    Parameters
    ----------
    pattern:
        A Python-style regular expression to match against each line.
    directory:
        Root directory to search.  Defaults to the current directory.
    file_glob:
        A simple glob suffix used to filter filenames (e.g. ``*.py``).
        Only the file extension is checked.  Defaults to ``*.py``.
    max_results:
        Stop after collecting this many matches.  Defaults to 50.

    Returns
    -------
    str
        Newline-separated results in ``path:line_number: text`` format,
        or a message indicating no matches were found.
    """
    directory = os.path.expanduser(directory)
    regex = re.compile(pattern)

    # Derive the extension filter from file_glob (e.g. "*.py" -> ".py")
    ext = ""
    if file_glob.startswith("*"):
        ext = file_glob[1:]  # e.g. ".py"

    matches: list[str] = []
    for root, _dirs, files in os.walk(directory):
        # Skip hidden directories
        _dirs[:] = [d for d in _dirs if not d.startswith(".")]
        for fname in sorted(files):
            if ext and not fname.endswith(ext):
                continue
            filepath = os.path.join(root, fname)
            try:
                with open(filepath, "r", encoding="utf-8", errors="replace") as fh:
                    for lineno, line in enumerate(fh, start=1):
                        if regex.search(line):
                            matches.append(f"{filepath}:{lineno}: {line.rstrip()}")
                            if len(matches) >= max_results:
                                break
            except (OSError, PermissionError):
                continue
            if len(matches) >= max_results:
                break
        if len(matches) >= max_results:
            break

    if not matches:
        return f"No matches found for pattern '{pattern}' in {directory}"
    return "\n".join(matches)


def register(registry: ToolRegistry) -> None:
    """Register :func:`code_search` on *registry*."""
    registry.tool(code_search)
