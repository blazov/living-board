"""LLM provider implementations."""

from .base import LLMProvider, LLMResponse, Message, ToolCall, ToolSchema

__all__ = [
    "LLMProvider",
    "LLMResponse",
    "Message",
    "ToolCall",
    "ToolSchema",
    "create_provider",
]


def create_provider(config) -> LLMProvider:
    """Factory: instantiate the correct provider based on config.provider.type."""
    provider_type = config.provider.type

    if provider_type == "anthropic":
        from .anthropic_ import AnthropicProvider
        return AnthropicProvider(config)
    elif provider_type == "openai":
        from .openai_ import OpenAIProvider
        return OpenAIProvider(config)
    elif provider_type == "ollama":
        from .ollama import OllamaProvider
        return OllamaProvider(config)
    else:
        raise ValueError(f"Unknown provider type: {provider_type!r}. "
                         f"Expected 'anthropic', 'openai', or 'ollama'.")
