"""Tools framework for the Living Board runner.

Exports the base types, registry, and a factory function to create
a fully-populated ToolRegistry from an AgentConfig + SupabaseClient.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from .base import Tool, ToolResult
from .registry import ToolRegistry

if TYPE_CHECKING:
    from ..config import AgentConfig
    from ..db import SupabaseClient


def create_tool_registry(config: AgentConfig, db: SupabaseClient) -> ToolRegistry:
    """Build a ToolRegistry with all tools enabled by the given config.

    This is the primary entry point. It inspects the config to decide
    which tool sets to register (e.g. email tools only if email is enabled).
    """
    from .database import create_database_tools
    from .email_ import create_email_tools
    from .files import create_file_tools
    from .memory import create_memory_tools
    from .search import WebSearchTool
    from .shell import ShellTool
    from .web import WebFetchTool

    registry = ToolRegistry()

    # Database tools (always available)
    registry.register_all(create_database_tools(db))

    # Memory tools (may be unavailable if Qdrant/Ollama not running)
    registry.register_all(create_memory_tools(config.memory))

    # Web search
    registry.register(WebSearchTool())

    # Web fetch
    registry.register(WebFetchTool())

    # File tools (sandboxed)
    registry.register_all(create_file_tools(config.execution.file_sandbox))

    # Shell tool
    registry.register(
        ShellTool(
            allowed=config.execution.shell_allowed,
            default_timeout=config.execution.shell_timeout,
        )
    )

    # Email tools (only if enabled)
    registry.register_all(create_email_tools(config.email))

    return registry


__all__ = [
    "Tool",
    "ToolResult",
    "ToolRegistry",
    "create_tool_registry",
]
