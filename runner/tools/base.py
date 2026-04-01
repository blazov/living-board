"""Abstract base class for tools and the ToolResult type."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from ..providers.base import ToolSchema


@dataclass
class ToolResult:
    """Result returned from executing a tool."""

    success: bool
    output: str
    data: Any = None
    error: str | None = None

    def to_content(self) -> str:
        """Format for inclusion in an LLM message."""
        if self.success:
            return self.output
        return f"Error: {self.error or self.output}"


class Tool(ABC):
    """Abstract base class that every tool must implement."""

    name: str
    description: str
    parameters: dict[str, Any]  # JSON Schema for the tool's parameters

    @abstractmethod
    def execute(self, **kwargs: Any) -> ToolResult:
        """Execute the tool with the given keyword arguments.

        Returns a ToolResult with the outcome.
        """
        ...

    def to_schema(self) -> ToolSchema:
        """Convert this tool to a provider-agnostic ToolSchema."""
        return ToolSchema(
            name=self.name,
            description=self.description,
            parameters=self.parameters,
        )
