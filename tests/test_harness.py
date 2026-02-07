import pytest
from codex_agent_harness import Agent, ToolRegistry

def test_tool_registration():
    registry = ToolRegistry()
    
    @registry.tool
    def add(a: int, b: int) -> int:
        """Adds two numbers."""
        return a + b
    
    tools = registry.list_tools()
    assert len(tools) == 1
    assert tools[0]["name"] == "add"
    assert registry.call("add", a=1, b=2) == 3

def test_agent_loop_simulation():
    registry = ToolRegistry()
    
    @registry.tool
    def list_files(path: str):
        return ["file1.txt", "file2.txt"]
    
    agent = Agent(registry=registry)
    result = agent.run("What files are here?")
    
    # Check that tool was called
    history = agent.state.history
    assert any(m.role == "tool" for m in history)
    assert any("file1.txt" in m.content for m in history)

def test_supervisor_rejection():
    class RejectingSupervisor:
        def approve(self, action, params):
            return False
            
    registry = ToolRegistry()
    @registry.tool
    def delete_all():
        return "deleted"
        
    agent = Agent(registry=registry, supervisor=RejectingSupervisor())
    agent.run("Delete everything")
    
    history = agent.state.history
    assert any("rejected by supervisor" in m.content for m in history)
