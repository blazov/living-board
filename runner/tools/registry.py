"""Tool registry -- holds tools, converts to schemas, dispatches calls."""

from __future__ import annotations

import logging
from typing import Any

from ..providers.base import ToolCall, ToolSchema
from .base import Tool, ToolResult

log = logging.getLogger(__name__)


class ToolRegistry:
    """Central registry for all available tools.

    Holds Tool instances, exposes them as ToolSchema lists for LLM providers,
    and dispatches ToolCall executions by name.
    """

    def __init__(self) -> None:
        self._tools: dict[str, Tool] = {}

    # ── Registration ──

    def register(self, tool: Tool) -> None:
        """Register a single tool."""
        if tool.name in self._tools:
            log.warning("Overwriting already-registered tool: %s", tool.name)
        self._tools[tool.name] = tool

    def register_all(self, tools: list[Tool]) -> None:
        """Register a list of tools."""
        for tool in tools:
            self.register(tool)

    # ── Query ──

    def get_schemas(self) -> list[ToolSchema]:
        """Return ToolSchema list suitable for any LLM provider."""
        return [tool.to_schema() for tool in self._tools.values()]

    def has(self, name: str) -> bool:
        return name in self._tools

    @property
    def names(self) -> list[str]:
        return list(self._tools.keys())

    def __len__(self) -> int:
        return len(self._tools)

    # ── Execution ──

    def execute(self, call: ToolCall) -> ToolResult:
        """Execute a ToolCall by looking up the tool and invoking it."""
        tool = self._tools.get(call.name)
        if tool is None:
            return ToolResult(
                success=False,
                output="",
                error=f"Unknown tool: {call.name}",
            )
        try:
            return tool.execute(**call.arguments)
        except Exception as exc:
            log.exception("Tool %s raised an exception", call.name)
            return ToolResult(
                success=False,
                output="",
                error=f"{type(exc).__name__}: {exc}",
            )

    def execute_by_name(self, name: str, **kwargs: Any) -> ToolResult:
        """Convenience method: execute a tool by name with keyword args."""
        tool = self._tools.get(name)
        if tool is None:
            return ToolResult(
                success=False,
                output="",
                error=f"Unknown tool: {name}",
            )
        try:
            return tool.execute(**kwargs)
        except Exception as exc:
            log.exception("Tool %s raised an exception", name)
            return ToolResult(
                success=False,
                output="",
                error=f"{type(exc).__name__}: {exc}",
            )
