"""Ollama (local) LLM provider via HTTP API."""

from __future__ import annotations

import json
import logging
import re
import uuid
from typing import Any

import httpx

from ..config import AgentConfig
from .base import LLMProvider, LLMResponse, Message, TokenUsage, ToolCall, ToolSchema

logger = logging.getLogger(__name__)


class OllamaProvider(LLMProvider):
    """Local Ollama instance via its HTTP chat API."""

    def __init__(self, config: AgentConfig) -> None:
        self.base_url = (config.provider.base_url or "http://localhost:11434").rstrip("/")
        self.models = config.provider.models
        self.client = httpx.Client(base_url=self.base_url, timeout=300)

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
        logger.info("Ollama chat: model=%s, messages=%d, tools=%d",
                     model, len(messages), len(tools) if tools else 0)

        api_messages = [self._convert_message(m) for m in messages]

        payload: dict[str, Any] = {
            "model": model,
            "messages": api_messages,
            "stream": False,
        }
        if tools:
            payload["tools"] = [self._convert_tool(t) for t in tools]

        resp = self.client.post("/api/chat", json=payload)
        resp.raise_for_status()
        data = resp.json()

        result = self._parse_response(data)

        # Fallback: if we sent tools but got no tool_calls in the response,
        # try to extract a JSON tool call from the text content.
        if tools and not result.tool_calls and result.content:
            fallback_calls = self._extract_tool_calls_from_text(result.content, tools)
            if fallback_calls:
                logger.info("Ollama: extracted %d tool call(s) from text fallback",
                            len(fallback_calls))
                result.tool_calls = fallback_calls
                result.stop_reason = "tool_use"

        return result

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _convert_tool(tool: ToolSchema) -> dict[str, Any]:
        """Convert a ToolSchema to Ollama's tool format (OpenAI-compatible)."""
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
        """Convert a Message to Ollama's chat message format."""
        if msg.role == "tool":
            return {
                "role": "tool",
                "content": msg.content or "",
            }

        if msg.role == "assistant" and msg.tool_calls:
            result: dict[str, Any] = {
                "role": "assistant",
                "content": msg.content or "",
                "tool_calls": [
                    {
                        "function": {
                            "name": tc.name,
                            "arguments": tc.arguments,
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
    def _parse_response(data: dict[str, Any]) -> LLMResponse:
        """Parse an Ollama /api/chat response into an LLMResponse."""
        message = data.get("message", {})
        content_text = message.get("content") or None
        tool_calls: list[ToolCall] = []

        for tc in message.get("tool_calls", []):
            func = tc.get("function", {})
            name = func.get("name", "")
            arguments = func.get("arguments", {})
            if isinstance(arguments, str):
                try:
                    arguments = json.loads(arguments)
                except (json.JSONDecodeError, TypeError):
                    arguments = {}
            tool_calls.append(
                ToolCall(
                    id=f"ollama_{uuid.uuid4().hex[:12]}",
                    name=name,
                    arguments=arguments,
                )
            )

        # Determine stop reason.
        done_reason = data.get("done_reason", "")
        if tool_calls:
            stop_reason = "tool_use"
        elif done_reason == "length":
            stop_reason = "max_tokens"
        else:
            stop_reason = "end_turn"

        # Token usage from Ollama's response fields.
        usage = TokenUsage(
            input_tokens=data.get("prompt_eval_count", 0) or 0,
            output_tokens=data.get("eval_count", 0) or 0,
        )

        return LLMResponse(
            content=content_text,
            tool_calls=tool_calls,
            stop_reason=stop_reason,
            usage=usage,
            raw=data,
        )

    @staticmethod
    def _extract_tool_calls_from_text(
        text: str, tools: list[ToolSchema]
    ) -> list[ToolCall]:
        """Fallback: parse tool calls from model text when native tool_use is unsupported.

        Looks for JSON blocks like:
            {"name": "tool_name", "arguments": {...}}
        or fenced code blocks containing such JSON.
        """
        tool_names = {t.name for t in tools}
        results: list[ToolCall] = []

        # Try to find JSON in fenced code blocks first.
        fenced = re.findall(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
        # Also try bare JSON objects.
        bare = re.findall(r"\{[^{}]*\"name\"\s*:\s*\"[^\"]+\"[^{}]*\}", text)

        candidates = fenced + bare
        for candidate in candidates:
            try:
                obj = json.loads(candidate)
            except (json.JSONDecodeError, TypeError):
                continue

            name = obj.get("name", "")
            arguments = obj.get("arguments") or obj.get("parameters") or {}
            if isinstance(arguments, str):
                try:
                    arguments = json.loads(arguments)
                except (json.JSONDecodeError, TypeError):
                    arguments = {}

            if name in tool_names and isinstance(arguments, dict):
                results.append(
                    ToolCall(
                        id=f"ollama_fb_{uuid.uuid4().hex[:12]}",
                        name=name,
                        arguments=arguments,
                    )
                )

        return results
