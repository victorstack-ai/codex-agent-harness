# Codex Agent Harness

A Python scaffolding framework for building, testing, and supervising agent-style development workflows. Designed to provide a structured environment where tools can be registered, composed, and executed within a supervised agent loop -- ideal for prototyping AI-driven coding agents and evaluating tool-use patterns.

## Architecture

The harness is organized around three core components:

```
+-----------------+       +----------------+       +------------------+
|   Tool Registry |<----->|   Agent Loop   |<----->|   Supervisor     |
|  (registry.py)  |       |   (agent.py)   |       |  (human-in-the- |
|                 |       |                |       |   loop hooks)    |
+-----------------+       +----------------+       +------------------+
        ^
        |
+-------+--------+
|  Example Tools  |
| (tools/ module) |
+-----------------+
```

### Tool Registry

The `ToolRegistry` class provides a decorator-based interface for registering Python functions as tools. Each tool automatically captures its name, docstring, and parameter signature. Tools are stored in an internal dictionary and can be listed or invoked by name.

### Agent Loop

The `Agent` class drives the execution loop. It accepts a prompt, maintains a conversation history (`AgentState`), and iteratively decides which tool to call next. At each step, the agent consults the supervisor before executing a tool call, records the result (or any errors) in the history, and continues until a finish condition is met or the maximum number of steps is reached.

### Supervisor (Human-in-the-Loop)

Every tool call passes through a `Supervisor` before execution. The `Supervisor` protocol defines a single `approve(action, params) -> bool` method. The default supervisor auto-approves all actions, but you can implement custom supervisors to add confirmation prompts, policy checks, logging, or any gating logic you need.

## Installation

**Requirements:** Python 3.10+

```bash
# Clone the repository
git clone https://github.com/yourusername/codex-agent-harness.git
cd codex-agent-harness

# Create a virtual environment (recommended)
python -m venv .venv
source .venv/bin/activate

# Install in editable mode with dev dependencies
pip install -e ".[dev]"
```

Or install from requirements.txt:

```bash
pip install -r requirements.txt
```

## Usage

### Basic Example

```python
from codex_agent_harness import Agent, ToolRegistry

registry = ToolRegistry()

@registry.tool
def greet(name: str) -> str:
    """Returns a greeting for the given name."""
    return f"Hello, {name}!"

agent = Agent(registry=registry)
result = agent.run("Say hello to Alice")
print(result)
```

### Using the Built-in Example Tools

The `tools/` module provides three ready-to-use tools:

```python
from codex_agent_harness import ToolRegistry
from codex_agent_harness.tools import register_all_tools

registry = ToolRegistry()
register_all_tools(registry)

# Now the registry has: file_read, shell, code_search
print(registry.list_tools())
```

### Adding a Custom Supervisor

```python
from codex_agent_harness import Agent, ToolRegistry

class InteractiveSupervisor:
    """Asks the user for confirmation before each tool call."""

    DANGEROUS_TOOLS = {"shell", "delete_file"}

    def approve(self, action: str, params: dict) -> bool:
        if action in self.DANGEROUS_TOOLS:
            answer = input(f"Allow '{action}' with {params}? [y/N] ")
            return answer.strip().lower() == "y"
        return True

registry = ToolRegistry()

@registry.tool
def shell(command: str) -> str:
    """Runs a shell command."""
    import subprocess
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    return result.stdout

agent = Agent(registry=registry, supervisor=InteractiveSupervisor())
agent.run("List the current directory")
```

## How to Add Custom Tools

1. **Define a function** with type-annotated parameters and a docstring.
2. **Register it** using the `@registry.tool` decorator.

```python
@registry.tool
def my_tool(arg1: str, arg2: int) -> str:
    """Description of what this tool does."""
    return f"Processed {arg1} with {arg2}"
```

The registry automatically extracts the function name, docstring (used as the tool description), and parameter types. The tool is then available to the agent by name.

You can also create reusable tool modules. See `src/codex_agent_harness/tools/` for examples of how to package tools as registrable functions.

## Testing

Run the test suite with pytest:

```bash
pytest
```

Run with verbose output:

```bash
pytest -v
```

The test suite covers tool registration, tool execution, supervisor approval/rejection logic, error handling, and the agent loop lifecycle.

## Project Structure

```
codex-agent-harness/
  src/
    codex_agent_harness/
      __init__.py          # Package exports
      agent.py             # Agent loop and supervisor protocol
      registry.py          # Tool registry with decorator API
      tools/               # Built-in example tools
        __init__.py
        file_read.py       # FileReadTool - read file contents
        shell.py           # ShellTool - execute shell commands
        code_search.py     # CodeSearchTool - search code with regex
  tests/
    test_harness.py        # Comprehensive test suite
  pyproject.toml           # Build config and dependencies
  requirements.txt         # Pip requirements
  LICENSE                  # MIT License
  README.md
```

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
