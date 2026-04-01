"""OpenAI LLM provider."""

from __future__ import annotations

import json
import logging
from typing import Any

import openai

from ..config import AgentConfig
from .base import LLMProvider, LLMResponse, Message, TokenUsage, ToolCall, ToolSchema

logger = logging.getLogger(__name__)


class OpenAIProvider(LLMProvider):
    """OpenAI API via the openai Python SDK."""

    def __init__(self, config: AgentConfig) -> None:
        if not config.provider.api_key:
            raise ValueError("OpenAI API key is required. Set OPENAI_API_KEY.")
        kwargs: dict[str, Any] = {"api_key": config.provider.api_key}
        if config.provider.base_url:
            kwargs["base_url"] = config.provider.base_url
        self.client = openai.OpenAI(**kwargs)
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
        logger.info("OpenAI chat: model=%s, messages=%d, tools=%d",
                     model, len(messages), len(tools) if tools else 0)

        api_messages = [self._convert_message(m) for m in messages]

        kwargs: dict[str, Any] = {
            "model": model,
            "messages": api_messages,
        }
        if tools:
            kwargs["tools"] = [self._convert_tool(t) for t in tools]

        response = self.client.chat.completions.create(**kwargs)
        return self._parse_response(response)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _convert_tool(tool: ToolSchema) -> dict[str, Any]:
        """Convert a ToolSchema to OpenAI's function calling format."""
        return {
            "type": "function",
            "function": {
                "name": tool.name,
                "description": tool.description,
                "parameters": tool.parameters,
            },
        }

    @staticmethod
    def _convert_message(msg: Message) -> dict[str, Any]:
        """Convert a Message to OpenAI's message format."""
        if msg.role == "tool":
            return {
                "role": "tool",
                "tool_call_id": msg.tool_call_id or "",
                "content": msg.content or "",
            }

        if msg.role == "assistant" and msg.tool_calls:
            result: dict[str, Any] = {
                "role": "assistant",
                "content": msg.content,
                "tool_calls": [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.name,
                            "arguments": json.dumps(tc.arguments),
                        },
                    }
                    for tc in msg.tool_calls
                ],
            }
            return result

        return {
            "role": msg.role,
            "content": msg.content or "",
        }

    @staticmethod
    def _parse_response(response: Any) -> LLMResponse:
        """Parse an OpenAI ChatCompletion response into an LLMResponse."""
        choice = response.choices[0]
        message = choice.message

        content_text = message.content
        tool_calls: list[ToolCall] = []

        if message.tool_calls:
            for tc in message.tool_calls:
                try:
                    arguments = json.loads(tc.function.arguments)
                except (json.JSONDecodeError, TypeError):
                    arguments = {}
                tool_calls.append(
                    ToolCall(
                        id=tc.id,
                        name=tc.function.name,
                        arguments=arguments,
                    )
                )

        # Map OpenAI finish_reason to our standard values.
        finish_reason_map = {
            "stop": "end_turn",
            "tool_calls": "tool_use",
            "length": "max_tokens",
            "content_filter": "end_turn",
        }
        stop_reason = finish_reason_map.get(choice.finish_reason or "stop", "end_turn")

        usage = TokenUsage()
        if response.usage:
            usage = TokenUsage(
                input_tokens=response.usage.prompt_tokens or 0,
                output_tokens=response.usage.completion_tokens or 0,
            )

        return LLMResponse(
            content=content_text,
            tool_calls=tool_calls,
            stop_reason=stop_reason,
            usage=usage,
            raw=response,
        )
