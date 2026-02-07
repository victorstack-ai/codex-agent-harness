from __future__ import annotations

from typing import Any, Dict, List, Optional, Protocol
from pydantic import BaseModel
from .registry import ToolRegistry

class Message(BaseModel):
    role: str
    content: str

class AgentState(BaseModel):
    history: List[Message] = []
    metadata: Dict[str, Any] = {}

class Supervisor(Protocol):
    def approve(self, action: str, params: Dict[str, Any]) -> bool:
        ...

class DefaultSupervisor:
    def approve(self, action: str, params: Dict[str, Any]) -> bool:
        return True

class Agent:
    def __init__(self, registry: ToolRegistry, supervisor: Optional[Supervisor] = None):
        self.registry = registry
        self.supervisor = supervisor or DefaultSupervisor()
        self.state = AgentState()

    def run(self, prompt: str, max_steps: int = 5):
        self.state.history.append(Message(role="user", content=prompt))
        
        for step in range(max_steps):
            # In a real scenario, we would call the LLM here.
            # For the harness, we simulate the 'next action' logic.
            action = self._decide_next_action()
            if action["type"] == "finish":
                break
            
            if action["type"] == "tool_call":
                tool_name = action["name"]
                params = action["params"]
                
                if self.supervisor.approve(tool_name, params):
                    try:
                        result = self.registry.call(tool_name, **params)
                        self.state.history.append(Message(
                            role="tool", 
                            content=f"Tool {tool_name} returned: {result}"
                        ))
                    except Exception as e:
                        self.state.history.append(Message(
                            role="error", 
                            content=f"Tool {tool_name} failed: {str(e)}"
                        ))
                else:
                    self.state.history.append(Message(
                        role="supervisor", 
                        content=f"Action {tool_name} rejected by supervisor."
                    ))
        
        return self.state.history[-1].content

    def _decide_next_action(self) -> Dict[str, Any]:
        # Simulation: if history is short, call a tool. Otherwise finish.
        if len(self.state.history) < 3:
            return {
                "type": "tool_call",
                "name": "list_files",
                "params": {"path": "."}
            }
        return {"type": "finish"}
