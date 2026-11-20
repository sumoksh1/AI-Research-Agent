from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Callable, Iterable

from google.genai import types

if TYPE_CHECKING:
    from agent.features.memory.store import MemoryStore


@dataclass(frozen=True)
class ToolContext:
    """Runtime dependencies handed to every tool handler."""

    memory_store: MemoryStore


@dataclass(frozen=True)
class Tool:
    """A tool's Gemini declaration and its handler, kept together.

    Handlers are called as handler(ctx, **args).
    """

    declaration: types.FunctionDeclaration
    handler: Callable[..., Any]

    @property
    def name(self) -> str:
        return self.declaration.name


class ToolRegistry:

    def __init__(self, tools: Iterable[Tool]):

        self._tools = {}

        for tool in tools:

            if tool.name in self._tools:
                raise ValueError(f"Duplicate tool name: {tool.name}")

            self._tools[tool.name] = tool

    def gemini_tools(self) -> list[types.Tool]:

        return [
            types.Tool(
                function_declarations=[t.declaration for t in self._tools.values()]
            )
        ]

    def execute(self, name: str, args: dict, ctx: ToolContext) -> Any:

        if name not in self._tools:

            raise ValueError(f"Unknown tool: {name}")

        return self._tools[name].handler(ctx, **(args or {}))
