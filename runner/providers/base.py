"""Abstract base class for LLM providers."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class Message:
    role: str  # "system", "user", "assistant", "tool"
    content: str | None = None
    tool_calls: list[ToolCall] = field(default_factory=list)
    tool_call_id: str | None = None  # For tool result messages
    name: str | None = None  # Tool name for tool results


@dataclass
class ToolSchema:
    """Provider-agnostic tool definition."""
    name: str
    description: str
    parameters: dict[str, Any]  # JSON Schema


@dataclass
class ToolCall:
    """A tool invocation from the LLM."""
    id: str
    name: str
    arguments: dict[str, Any]


@dataclass
class TokenUsage:
    input_tokens: int = 0
    output_tokens: int = 0


@dataclass
class LLMResponse:
    content: str | None = None
    tool_calls: list[ToolCall] = field(default_factory=list)
    stop_reason: str = "end_turn"  # "end_turn", "tool_use", "max_tokens"
    usage: TokenUsage = field(default_factory=TokenUsage)
    raw: Any = None


class LLMProvider(ABC):
    """Abstract interface for any LLM provider."""

    @abstractmethod
    def chat(
        self,
        messages: list[Message],
        tools: list[ToolSchema] | None = None,
        model_tier: int = 1,
    ) -> LLMResponse:
        """Send messages to the LLM, optionally with tool schemas."""
        ...

    @abstractmethod
    def get_model_name(self, tier: int) -> str:
        """Get the provider-specific model name for a tier (1=complex, 2=standard, 3=simple)."""
        ...
