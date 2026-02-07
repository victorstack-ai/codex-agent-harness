from __future__ import annotations

import inspect
from typing import Any, Callable, Dict, List, Optional
from pydantic import BaseModel, Field

class Tool(BaseModel):
    name: str
    description: str
    func: Callable
    parameters: Dict[str, Any]

class ToolRegistry:
    def __init__(self):
        self._tools: Dict[str, Tool] = {}

    def tool(self, func: Callable):
        name = func.__name__
        description = func.__doc__ or ""
        # Basic parameter extraction for simulation
        sig = inspect.signature(func)
        parameters = {
            k: v.annotation.__name__ if hasattr(v.annotation, "__name__") else str(v.annotation)
            for k, v in sig.parameters.items()
        }
        
        self._tools[name] = Tool(
            name=name,
            description=description,
            func=func,
            parameters=parameters
        )
        return func

    def list_tools(self) -> List[Dict[str, Any]]:
        return [
            {
                "name": t.name,
                "description": t.description,
                "parameters": t.parameters
            }
            for t in self._tools.values()
        ]

    def call(self, name: str, **kwargs) -> Any:
        if name not in self._tools:
            raise ValueError(f"Tool {name} not found")
        return self._tools[name].func(**kwargs)
