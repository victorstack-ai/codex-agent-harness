# Codex Agent Harness

Inspired by the release of OpenAI GPT-5.3-Codex, this harness provides a structured environment for building and testing agent-style development workflows.

## Features

- **Tool Registry**: Easily register and invoke Python functions as tools.
- **Context Management**: Track conversation history and tool outputs over long task loops.
- **Terminal Simulator**: A sandboxed environment for testing terminal-based operations.
- **Interactive Supervision**: Built-in hooks for human-in-the-loop validation.

## Why

As models like GPT-5.3-Codex move toward "agent-style" autonomy, we need better local scaffolding to test their behavior, especially for complex software engineering tasks (SWE-Bench) and terminal interactions.

## Installation

```bash
pip install -e .
```

## Usage

```python
from codex_agent_harness.agent import Agent
from codex_agent_harness.tools import ToolRegistry

registry = ToolRegistry()

@registry.tool
def get_file_content(path: str) -> str:
    """Reads a file and returns its content."""
    # implementation ...
    return "content"

agent = Agent(registry=registry)
agent.run("Fix the bug in src/main.py")
```
