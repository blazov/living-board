"""System prompt builder — reads CLAUDE.md and adapts for the provider."""

from __future__ import annotations

from pathlib import Path

from .config import AgentConfig


def build_system_prompt(config: AgentConfig) -> str:
    """Load CLAUDE.md and prepend runner-specific context."""
    prompt_path = Path(config.system_prompt)
    if not prompt_path.exists():
        raise FileNotFoundError(
            f"System prompt file not found: {config.system_prompt}. "
            f"Make sure CLAUDE.md exists in the project root."
        )

    protocol = prompt_path.read_text()

    # Replace any remaining placeholders with config values
    if config.supabase.project_id:
        protocol = protocol.replace("{{SUPABASE_PROJECT_ID}}", config.supabase.project_id)
    if config.email.address:
        protocol = protocol.replace("{{AGENTMAIL_ADDRESS}}", config.email.address)

    # Prepend runner context
    header = (
        f"You are running via the Living Board Python runner.\n"
        f"LLM Provider: {config.provider.type}\n"
        f"Model tiers: tier1={config.provider.models.tier1}, "
        f"tier2={config.provider.models.tier2}, tier3={config.provider.models.tier3}\n"
        f"Memory system: Qdrant at {config.memory.qdrant_url}, "
        f"embeddings via {config.memory.embed_model} at {config.memory.ollama_url}\n"
        f"\n"
        f"You have access to tools via function calling. Use them to interact with "
        f"the database, search the web, read/write files, manage memory, and send email.\n"
        f"When you need to query or update the database, use the execute_sql, update_task, "
        f"store_learning, or create_tasks tools.\n"
        f"\n"
        f"---\n\n"
    )

    return header + protocol
