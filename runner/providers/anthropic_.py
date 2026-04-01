"""Anthropic (Claude) LLM provider."""

from __future__ import annotations

import json
import logging
from typing import Any

import anthropic

from ..config import AgentConfig
from .base import LLMProvider, LLMResponse, Message, TokenUsage, ToolCall, ToolSchema

logger = logging.getLogger(__name__)


class AnthropicProvider(LLMProvider):
    """Claude API via the anthropic Python SDK."""

    def __init__(self, config: AgentConfig) -> None:
        if not config.provider.api_key:
            raise ValueError("Anthropic API key is required. Set ANTHROPIC_API_KEY.")
        self.client = anthropic.Anthropic(api_key=config.provider.api_key)
        self.models = config.provider.models

    def get_model_name(self, tier: int) -> str:
        if tier == 1:
            return self.models.tier1
        elif tier == 2:
            return self.models.tier2
        elif tier == 3:
            return self.models.tier3
        raise ValueError(f"Invalid tier: {tier}. Must be 1, 2, or 3.")

    def chat(
        self,
        messages: list[Message],
        tools: list[ToolSchema] | None = None,
        model_tier: int = 1,
    ) -> LLMResponse:
        model = self.get_model_name(model_tier)
        logger.info("Anthropic chat: model=%s, messages=%d, tools=%d",
                     model, len(messages), len(tools) if tools else 0)

        # Separate system message from conversation messages.
        system_text: str | None = None
        conversation: list[dict[str, Any]] = []

        for msg in messages:
            if msg.role == "system":
                system_text = msg.content
            elif msg.role == "assistant":
                conversation.append(self._build_assistant_message(msg))
            elif msg.role == "tool":
                conversation.append(self._build_tool_result_message(msg))
            else:
                # user
                conversation.append({"role": "user", "content": msg.content or ""})

        # Build API kwargs.
        kwargs: dict[str, Any] = {
            "model": model,
            "max_tokens": 4096,
            "messages": conversation,
        }
        if system_text:
            kwargs["system"] = system_text
        if tools:
            kwargs["tools"] = [self._convert_tool(t) for t in tools]

        response = self.client.messages.create(**kwargs)
        return self._parse_response(response)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _convert_tool(tool: ToolSchema) -> dict[str, Any]:
        """Convert a ToolSchema to Anthropic's tool_use format."""
        return {
            "name": tool.name,
            "description": tool.description,
            "input_schema": tool.parameters,
        }

    @staticmethod
    def _build_assistant_message(msg: Message) -> dict[str, Any]:
        """Build an assistant message, including any tool_use blocks."""
        content: list[dict[str, Any]] = []
        if msg.content:
            content.append({"type": "text", "text": msg.content})
        for tc in msg.tool_calls:
            content.append({
                "type": "tool_use",
                "id": tc.id,
                "name": tc.name,
                "input": tc.arguments,
            })
        # If there is only plain text and no tool calls, use a simple string.
        if len(content) == 1 and content[0]["type"] == "text":
            return {"role": "assistant", "content": content[0]["text"]}
        return {"role": "assistant", "content": content}

    @staticmethod
    def _build_tool_result_message(msg: Message) -> dict[str, Any]:
        """Build a tool result message for Anthropic's format."""
        return {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "tool_use_id": msg.tool_call_id,
                    "content": msg.content or "",
                }
            ],
        }

    @staticmethod
    def _parse_response(response: Any) -> LLMResponse:
        """Parse an Anthropic Messages API response into an LLMResponse."""
        content_text: str | None = None
        tool_calls: list[ToolCall] = []

        for block in response.content:
            if block.type == "text":
                content_text = block.text
            elif block.type == "tool_use":
                tool_calls.append(
                    ToolCall(
                        id=block.id,
                        name=block.name,
                        arguments=block.input if isinstance(block.input, dict) else {},
                    )
                )

        # Map Anthropic stop_reason to our standard values.
        stop_reason_map = {
            "end_turn": "end_turn",
            "tool_use": "tool_use",
            "max_tokens": "max_tokens",
            "stop_sequence": "end_turn",
        }
        stop_reason = stop_reason_map.get(response.stop_reason, "end_turn")

        usage = TokenUsage(
            input_tokens=getattr(response.usage, "input_tokens", 0),
            output_tokens=getattr(response.usage, "output_tokens", 0),
        )

        return LLMResponse(
            content=content_text,
            tool_calls=tool_calls,
            stop_reason=stop_reason,
            usage=usage,
            raw=response,
        )
