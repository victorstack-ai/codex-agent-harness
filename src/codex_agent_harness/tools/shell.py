"""ShellTool -- execute a shell command and capture its output.

Wraps ``subprocess.run`` with a configurable timeout so agents can interact
with the local environment without risking runaway processes.
"""

from __future__ import annotations

import subprocess
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..registry import ToolRegistry

DEFAULT_TIMEOUT = 30  # seconds


def shell(command: str, timeout: int = DEFAULT_TIMEOUT) -> str:
    """Run *command* in a subprocess and return its combined output.

    Parameters
    ----------
    command:
        The shell command string to execute.
    timeout:
        Maximum wall-clock seconds the command may run.  Defaults to 30.

    Returns
    -------
    str
        A string containing stdout and stderr separated by a header line.

    Raises
    ------
    subprocess.TimeoutExpired
        If the command exceeds *timeout* seconds.
    """
    result = subprocess.run(
        command,
        shell=True,
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    parts: list[str] = []
    if result.stdout:
        parts.append(result.stdout)
    if result.stderr:
        parts.append(f"--- stderr ---\n{result.stderr}")
    if result.returncode != 0:
        parts.append(f"[exit code {result.returncode}]")
    return "\n".join(parts) if parts else "(no output)"


def register(registry: ToolRegistry) -> None:
    """Register :func:`shell` on *registry*."""
    registry.tool(shell)
