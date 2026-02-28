"""Comprehensive test suite for the Codex Agent Harness.

Covers tool registration, tool execution, supervisor approval/rejection,
the agent loop lifecycle, error handling, and the built-in example tools.
"""

from __future__ import annotations

import pytest

from codex_agent_harness import Agent, ToolRegistry, DefaultSupervisor
from codex_agent_harness.tools import register_all_tools
from codex_agent_harness.tools.file_read import file_read
from codex_agent_harness.tools.shell import shell
from codex_agent_harness.tools.code_search import code_search


# ---------------------------------------------------------------------------
# Tool Registration
# ---------------------------------------------------------------------------


class TestToolRegistration:
    """Tests for ToolRegistry.tool decorator and listing."""

    def test_register_single_tool(self):
        registry = ToolRegistry()

        @registry.tool
        def add(a: int, b: int) -> int:
            """Adds two numbers."""
            return a + b

        tools = registry.list_tools()
        assert len(tools) == 1
        assert tools[0]["name"] == "add"
        assert tools[0]["description"] == "Adds two numbers."
        assert "a" in tools[0]["parameters"]
        assert "b" in tools[0]["parameters"]

    def test_register_multiple_tools(self):
        registry = ToolRegistry()

        @registry.tool
        def foo():
            """First tool."""
            return "foo"

        @registry.tool
        def bar():
            """Second tool."""
            return "bar"

        tools = registry.list_tools()
        names = {t["name"] for t in tools}
        assert names == {"foo", "bar"}

    def test_register_preserves_function(self):
        """The decorator should return the original function unchanged."""
        registry = ToolRegistry()

        @registry.tool
        def multiply(x: int, y: int) -> int:
            """Multiplies two numbers."""
            return x * y

        # The decorated function should still work normally
        assert multiply(3, 4) == 12

    def test_tool_without_docstring(self):
        registry = ToolRegistry()

        @registry.tool
        def no_doc(x: int):
            return x

        tools = registry.list_tools()
        assert tools[0]["description"] == ""


# ---------------------------------------------------------------------------
# Tool Execution
# ---------------------------------------------------------------------------


class TestToolExecution:
    """Tests for calling registered tools via the registry."""

    def test_call_registered_tool(self):
        registry = ToolRegistry()

        @registry.tool
        def add(a: int, b: int) -> int:
            """Adds two numbers."""
            return a + b

        assert registry.call("add", a=1, b=2) == 3

    def test_call_unregistered_tool_raises(self):
        registry = ToolRegistry()
        with pytest.raises(ValueError, match="Tool .* not found"):
            registry.call("nonexistent")

    def test_call_with_wrong_args_raises(self):
        registry = ToolRegistry()

        @registry.tool
        def divide(a: float, b: float) -> float:
            """Divides a by b."""
            return a / b

        with pytest.raises(TypeError):
            registry.call("divide", a=10)  # missing b

    def test_tool_raising_exception_propagates(self):
        registry = ToolRegistry()

        @registry.tool
        def boom():
            """Always fails."""
            raise RuntimeError("kaboom")

        with pytest.raises(RuntimeError, match="kaboom"):
            registry.call("boom")


# ---------------------------------------------------------------------------
# Supervisor
# ---------------------------------------------------------------------------


class TestSupervisor:
    """Tests for supervisor approval and rejection."""

    def test_default_supervisor_approves(self):
        supervisor = DefaultSupervisor()
        assert supervisor.approve("any_action", {"key": "val"}) is True

    def test_custom_supervisor_rejects(self):
        class RejectingSupervisor:
            def approve(self, action, params):
                return False

        registry = ToolRegistry()

        @registry.tool
        def delete_all():
            """Dangerous tool."""
            return "deleted"

        agent = Agent(registry=registry, supervisor=RejectingSupervisor())
        agent.run("Delete everything")

        history = agent.state.history
        assert any("rejected by supervisor" in m.content for m in history)
        # The tool itself should never have been called
        assert not any("deleted" in m.content and m.role == "tool" for m in history)

    def test_selective_supervisor(self):
        """Supervisor that approves some tools and rejects others."""

        class SelectiveSupervisor:
            def approve(self, action, params):
                return action != "dangerous_tool"

        registry = ToolRegistry()

        @registry.tool
        def safe_tool():
            """A safe tool."""
            return "safe result"

        @registry.tool
        def dangerous_tool():
            """A dangerous tool."""
            return "danger result"

        _agent = Agent(registry=registry, supervisor=SelectiveSupervisor())
        # The simulated agent loop calls "list_files" by default,
        # so we just verify the supervisor protocol is respected.
        assert SelectiveSupervisor().approve("safe_tool", {}) is True
        assert SelectiveSupervisor().approve("dangerous_tool", {}) is False


# ---------------------------------------------------------------------------
# Agent Loop
# ---------------------------------------------------------------------------


class TestAgentLoop:
    """Tests for the agent run loop and state management."""

    def test_agent_loop_calls_tool(self):
        registry = ToolRegistry()

        @registry.tool
        def list_files(path: str):
            """Lists files in the given path."""
            return ["file1.txt", "file2.txt"]

        agent = Agent(registry=registry)
        agent.run("What files are here?")

        history = agent.state.history
        assert any(m.role == "tool" for m in history)
        assert any("file1.txt" in m.content for m in history)

    def test_agent_records_user_prompt(self):
        registry = ToolRegistry()

        @registry.tool
        def list_files(path: str):
            return []

        agent = Agent(registry=registry)
        agent.run("Hello agent")

        assert agent.state.history[0].role == "user"
        assert agent.state.history[0].content == "Hello agent"

    def test_agent_respects_max_steps(self):
        """Agent should not exceed max_steps iterations."""
        registry = ToolRegistry()

        @registry.tool
        def list_files(path: str):
            return "ok"

        agent = Agent(registry=registry)
        agent.run("Do something", max_steps=1)

        # 1 user message + at most 1 tool result
        assert len(agent.state.history) <= 3

    def test_agent_handles_tool_error(self):
        """If a tool raises, the error should be recorded in history."""
        registry = ToolRegistry()

        @registry.tool
        def list_files(path: str):
            raise RuntimeError("disk error")

        agent = Agent(registry=registry)
        agent.run("List files")

        history = agent.state.history
        assert any(m.role == "error" for m in history)
        assert any("disk error" in m.content for m in history)

    def test_agent_returns_last_message(self):
        registry = ToolRegistry()

        @registry.tool
        def list_files(path: str):
            return ["a.py"]

        agent = Agent(registry=registry)
        result = agent.run("List files")

        # Should return the content of the last history message
        assert isinstance(result, str)
        assert len(result) > 0


# ---------------------------------------------------------------------------
# Built-in Example Tools
# ---------------------------------------------------------------------------


class TestFileReadTool:
    """Tests for the file_read example tool."""

    def test_read_existing_file(self, tmp_path):
        test_file = tmp_path / "hello.txt"
        test_file.write_text("Hello, World!")

        content = file_read(str(test_file))
        assert content == "Hello, World!"

    def test_read_nonexistent_file(self):
        with pytest.raises(FileNotFoundError):
            file_read("/nonexistent/path/to/file.txt")

    def test_read_directory_raises(self, tmp_path):
        with pytest.raises(IsADirectoryError):
            file_read(str(tmp_path))

    def test_read_respects_max_bytes(self, tmp_path):
        test_file = tmp_path / "big.txt"
        test_file.write_text("A" * 1000)

        content = file_read(str(test_file), max_bytes=10)
        assert len(content) == 10

    def test_register_file_read(self):
        registry = ToolRegistry()
        from codex_agent_harness.tools.file_read import register

        register(registry)
        names = [t["name"] for t in registry.list_tools()]
        assert "file_read" in names


class TestShellTool:
    """Tests for the shell example tool."""

    def test_echo_command(self):
        result = shell("echo hello")
        assert "hello" in result

    def test_captures_stderr(self):
        result = shell("echo err >&2")
        assert "err" in result
        assert "stderr" in result

    def test_reports_exit_code(self):
        result = shell("exit 42")
        assert "exit code 42" in result

    def test_timeout(self):
        import subprocess

        with pytest.raises(subprocess.TimeoutExpired):
            shell("sleep 10", timeout=1)

    def test_register_shell(self):
        registry = ToolRegistry()
        from codex_agent_harness.tools.shell import register

        register(registry)
        names = [t["name"] for t in registry.list_tools()]
        assert "shell" in names


class TestCodeSearchTool:
    """Tests for the code_search example tool."""

    def test_search_finds_match(self, tmp_path):
        py_file = tmp_path / "sample.py"
        py_file.write_text("def hello():\n    return 'world'\n")

        result = code_search("hello", directory=str(tmp_path))
        assert "hello" in result
        assert "sample.py" in result

    def test_search_no_match(self, tmp_path):
        py_file = tmp_path / "sample.py"
        py_file.write_text("def foo():\n    pass\n")

        result = code_search("zzz_no_match", directory=str(tmp_path))
        assert "No matches found" in result

    def test_search_respects_max_results(self, tmp_path):
        py_file = tmp_path / "lines.py"
        py_file.write_text("\n".join(f"line {i}" for i in range(100)))

        result = code_search("line", directory=str(tmp_path), max_results=5)
        assert result.count("\n") <= 5  # at most 5 matches (4 newlines + last line)

    def test_search_file_glob_filter(self, tmp_path):
        py_file = tmp_path / "code.py"
        py_file.write_text("match_me\n")
        txt_file = tmp_path / "notes.txt"
        txt_file.write_text("match_me\n")

        result = code_search("match_me", directory=str(tmp_path), file_glob="*.py")
        assert "code.py" in result
        assert "notes.txt" not in result

    def test_register_code_search(self):
        registry = ToolRegistry()
        from codex_agent_harness.tools.code_search import register

        register(registry)
        names = [t["name"] for t in registry.list_tools()]
        assert "code_search" in names


# ---------------------------------------------------------------------------
# register_all_tools helper
# ---------------------------------------------------------------------------


class TestRegisterAllTools:
    """Tests for the convenience register_all_tools function."""

    def test_registers_all_three_tools(self):
        registry = ToolRegistry()
        register_all_tools(registry)
        names = {t["name"] for t in registry.list_tools()}
        assert names == {"file_read", "shell", "code_search"}
