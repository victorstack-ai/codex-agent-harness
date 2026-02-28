"""Built-in example tools for the Codex Agent Harness.

This module provides three ready-to-use tools that demonstrate the tool
registration pattern and cover common agent operations: reading files,
executing shell commands, and searching code with regular expressions.

Use ``register_all_tools(registry)`` to register every built-in tool at once,
or import individual registration helpers for finer control.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from .file_read import register as register_file_read
from .shell import register as register_shell
from .code_search import register as register_code_search

if TYPE_CHECKING:
    from ..registry import ToolRegistry

__all__ = [
    "register_all_tools",
    "register_file_read",
    "register_shell",
    "register_code_search",
]


def register_all_tools(registry: ToolRegistry) -> None:
    """Register every built-in tool on *registry*."""
    register_file_read(registry)
    register_shell(registry)
    register_code_search(registry)
