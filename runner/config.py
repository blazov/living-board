"""Configuration loading from agent.toml + .env."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from pydantic import BaseModel, Field

try:
    import tomllib
except ImportError:
    import tomli as tomllib  # type: ignore[no-redef]


class ProviderModels(BaseModel):
    tier1: str = "claude-sonnet-4-20250514"
    tier2: str = "claude-sonnet-4-20250514"
    tier3: str = "claude-haiku-4-20250514"


class ProviderConfig(BaseModel):
    type: str = "anthropic"  # "anthropic" | "openai" | "ollama"
    models: ProviderModels = Field(default_factory=ProviderModels)
    base_url: str | None = None  # For Ollama or custom endpoints
    api_key: str | None = None  # Loaded from env


class SupabaseConfig(BaseModel):
    url: str = ""
    anon_key: str = ""
    project_id: str = ""


class MemoryConfig(BaseModel):
    qdrant_url: str = "http://localhost:6333"
    qdrant_collection: str = "living_board_memories"
    ollama_url: str = "http://localhost:11434"
    embed_model: str = "bge-m3"


class EmailConfig(BaseModel):
    enabled: bool = False
    address: str = ""
    api_key: str = ""


class SearchConfig(BaseModel):
    provider: str = "duckduckgo"  # "duckduckgo" | "tavily" | "brave"
    api_key: str = ""


class ExecutionConfig(BaseModel):
    max_tool_calls: int = 30
    shell_allowed: bool = True
    shell_timeout: int = 60
    file_sandbox: str = "artifacts"


class AgentConfig(BaseModel):
    name: str = "living-board"
    cycle_interval: str = "1h"
    artifacts_dir: str = "artifacts"
    system_prompt: str = "CLAUDE.md"
    provider: ProviderConfig = Field(default_factory=ProviderConfig)
    supabase: SupabaseConfig = Field(default_factory=SupabaseConfig)
    memory: MemoryConfig = Field(default_factory=MemoryConfig)
    email: EmailConfig = Field(default_factory=EmailConfig)
    search: SearchConfig = Field(default_factory=SearchConfig)
    execution: ExecutionConfig = Field(default_factory=ExecutionConfig)


def load_config(config_path: str = "agent.toml", env_path: str = ".env") -> AgentConfig:
    """Load config from TOML file and environment variables."""
    # Load .env
    env_file = Path(env_path)
    if env_file.exists():
        load_dotenv(env_file)

    # Also try dashboard/.env.local for Supabase keys
    dashboard_env = Path("dashboard/.env.local")
    if dashboard_env.exists():
        load_dotenv(dashboard_env, override=False)

    # Load TOML
    toml_file = Path(config_path)
    data: dict[str, Any] = {}
    if toml_file.exists():
        with open(toml_file, "rb") as f:
            data = tomllib.load(f)

    config = AgentConfig(**_flatten_toml(data))

    # Override from environment
    config.supabase.url = os.getenv("NEXT_PUBLIC_SUPABASE_URL", config.supabase.url)
    config.supabase.anon_key = os.getenv("NEXT_PUBLIC_SUPABASE_ANON_KEY", config.supabase.anon_key)

    # Extract project ID from URL
    if config.supabase.url and not config.supabase.project_id:
        try:
            host = config.supabase.url.split("//")[1].split(".")[0]
            config.supabase.project_id = host
        except (IndexError, AttributeError):
            pass

    # Provider API keys from env
    if config.provider.type == "anthropic":
        config.provider.api_key = os.getenv("ANTHROPIC_API_KEY", config.provider.api_key)
    elif config.provider.type == "openai":
        config.provider.api_key = os.getenv("OPENAI_API_KEY", config.provider.api_key)
    elif config.provider.type == "ollama":
        config.provider.base_url = config.provider.base_url or "http://localhost:11434"

    # Email
    config.email.api_key = os.getenv("AGENTMAIL_API_KEY", config.email.api_key)

    # Search
    config.search.api_key = os.getenv("TAVILY_API_KEY", "") or os.getenv("BRAVE_API_KEY", "")

    return config


def _flatten_toml(data: dict[str, Any]) -> dict[str, Any]:
    """Convert nested TOML to flat kwargs for AgentConfig."""
    result: dict[str, Any] = {}
    for key, value in data.items():
        if key == "agent":
            result.update(value)
        elif key in ("provider", "supabase", "memory", "email", "search", "execution"):
            result[key] = value
    return result
