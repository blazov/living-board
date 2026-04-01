"""CLI for the Living Board agent runner."""

from __future__ import annotations

import logging
import sys
import time

import click

from .agent import AgentRunner
from .config import load_config


def setup_logging(verbose: bool = False) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


@click.group()
def cli():
    """Living Board Agent Runner — run the agent with any LLM."""
    pass


@cli.command()
@click.option("--config", "-c", default="agent.toml", help="Config file path")
@click.option("--env", "-e", default=".env", help="Env file path")
@click.option("--task-id", default=None, help="Force a specific task ID")
@click.option("--dry-run", is_flag=True, help="Orient + Decide only, no Execute")
@click.option("--verbose", "-v", is_flag=True, help="Verbose logging")
def run(config: str, env: str, task_id: str | None, dry_run: bool, verbose: bool):
    """Execute one agent cycle."""
    setup_logging(verbose)
    logger = logging.getLogger("living-board")

    try:
        cfg = load_config(config, env)
    except Exception as e:
        click.echo(f"Error loading config: {e}", err=True)
        sys.exit(1)

    if not cfg.supabase.url or not cfg.supabase.anon_key:
        click.echo("Error: Supabase URL and anon key are required.", err=True)
        click.echo("Set them in agent.toml, .env, or dashboard/.env.local", err=True)
        sys.exit(1)

    if not cfg.provider.api_key and cfg.provider.type != "ollama":
        click.echo(
            f"Error: API key required for provider '{cfg.provider.type}'.", err=True
        )
        sys.exit(1)

    runner = AgentRunner(cfg)

    # Verify Supabase connection
    if not runner.db.check_connection():
        click.echo("Error: Cannot connect to Supabase. Check URL and anon key.", err=True)
        sys.exit(1)

    if dry_run:
        from .phases import orient, decide
        context = orient(runner.db, cfg, runner.registry)
        click.echo(f"Active goals: {len(context.goals)}")
        click.echo(f"Pending tasks: {len(context.tasks)}")
        click.echo(f"Unread comments: {len(context.comments)}")
        click.echo(f"Needs reflection: {context.needs_reflection}")
        click.echo(f"Needs email check: {context.needs_email_check}")

        decision = decide(runner.provider, runner.db, cfg, runner.registry, context)
        click.echo(f"Decision: {decision.action} (goal={decision.goal_id}, task={decision.task_id})")
        click.echo(f"Reasoning: {decision.reasoning}")
        return

    result = runner.run_cycle()
    click.echo(f"\n{'='*50}")
    click.echo(f"Action: {result.action}")
    click.echo(f"Summary: {result.summary}")
    if result.learnings:
        click.echo(f"Learnings: {len(result.learnings)}")
    click.echo(f"Duration: {result.duration_ms}ms")
    click.echo(f"Success: {result.success}")


@cli.command()
@click.option("--config", "-c", default="agent.toml", help="Config file path")
@click.option("--env", "-e", default=".env", help="Env file path")
@click.option("--interval", default=3600, help="Seconds between cycles (default: 3600)")
@click.option("--verbose", "-v", is_flag=True, help="Verbose logging")
def daemon(config: str, env: str, interval: int, verbose: bool):
    """Run the agent in a continuous loop."""
    setup_logging(verbose)
    logger = logging.getLogger("living-board")

    cfg = load_config(config, env)
    runner = AgentRunner(cfg)

    if not runner.db.check_connection():
        click.echo("Error: Cannot connect to Supabase.", err=True)
        sys.exit(1)

    click.echo(f"Living Board daemon started (interval: {interval}s)")
    click.echo(f"Provider: {cfg.provider.type}")
    click.echo(f"Press Ctrl+C to stop.\n")

    while True:
        try:
            result = runner.run_cycle()
            logger.info(f"Cycle done: {result.action} — {result.summary}")
        except KeyboardInterrupt:
            click.echo("\nStopping daemon...")
            break
        except Exception:
            logger.exception("Cycle failed")

        try:
            time.sleep(interval)
        except KeyboardInterrupt:
            click.echo("\nStopping daemon...")
            break


@cli.command()
@click.option("--config", "-c", default="agent.toml", help="Config file path")
@click.option("--env", "-e", default=".env", help="Env file path")
def status(config: str, env: str):
    """Check agent status and connectivity."""
    cfg = load_config(config, env)

    click.echo("Living Board Status")
    click.echo("=" * 40)

    # Provider
    click.echo(f"Provider: {cfg.provider.type}")
    click.echo(f"  Tier 1: {cfg.provider.models.tier1}")
    click.echo(f"  Tier 2: {cfg.provider.models.tier2}")
    click.echo(f"  Tier 3: {cfg.provider.models.tier3}")
    has_key = bool(cfg.provider.api_key) or cfg.provider.type == "ollama"
    click.echo(f"  API key: {'✓' if has_key else '✗ missing'}")

    # Supabase
    from .db import SupabaseClient
    db = SupabaseClient(cfg.supabase)
    connected = db.check_connection()
    click.echo(f"\nSupabase: {'✓ connected' if connected else '✗ cannot connect'}")
    click.echo(f"  URL: {cfg.supabase.url}")

    # Memory
    import urllib.request
    import urllib.error
    try:
        urllib.request.urlopen(f"{cfg.memory.qdrant_url}/healthz", timeout=3)
        click.echo(f"\nQdrant: ✓ running at {cfg.memory.qdrant_url}")
    except Exception:
        click.echo(f"\nQdrant: ✗ not reachable at {cfg.memory.qdrant_url}")

    try:
        urllib.request.urlopen(f"{cfg.memory.ollama_url}/api/tags", timeout=3)
        click.echo(f"Ollama: ✓ running at {cfg.memory.ollama_url}")
    except Exception:
        click.echo(f"Ollama: ✗ not reachable at {cfg.memory.ollama_url}")

    # Email
    if cfg.email.enabled:
        click.echo(f"\nEmail: {cfg.email.address}")
    else:
        click.echo(f"\nEmail: disabled")
