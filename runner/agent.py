"""Main agent loop — Orient → Decide → Execute → Record."""

from __future__ import annotations

import logging
import os
import time
from typing import Callable, Mapping, Optional

from .config import AgentConfig
from .db import SupabaseClient
from .models import CycleResult
from .phases import orient, decide, execute, record, reflect, check_email
from .providers import create_provider
from .tools import create_tool_registry

logger = logging.getLogger("living-board")


# Credentials the agent relies on. Presence/absence is logged once per process
# at the start of the first cycle so operators can immediately see what is
# wired up in the current environment without grepping through the cycle body.
# No secret values are ever emitted — only variable names.
CREDENTIAL_ENV_VARS: tuple[str, ...] = (
    "AGENTMAIL_API_KEY",
    "DEVTO_API_KEY",
    "SUPABASE_DB_URL",
    "AUTH_SECRET",
    "CLAUDE_API_KEY",
    "TRIGGER_ID",
    "SUBSTACK_COOKIE",
)

# Module-level guard: emit the banner exactly once per process, even if
# AgentRunner is re-instantiated (tests, supervisors, etc.).
_credentials_banner_emitted: bool = False


def emit_credentials_banner(
    env: Optional[Mapping[str, str]] = None,
    emit: Optional[Callable[[str], None]] = None,
    *,
    force: bool = False,
) -> Optional[str]:
    """Emit a one-line credentials presence/absence banner.

    Format: ``[credentials] present=A,B absent=C,D,E`` — variable names only.
    Idempotent per process: subsequent calls are no-ops and return ``None``
    unless ``force=True`` (used by tests). Returns the emitted line on the
    first call, ``None`` thereafter.
    """
    global _credentials_banner_emitted
    if _credentials_banner_emitted and not force:
        return None

    source = os.environ if env is None else env
    present = [name for name in CREDENTIAL_ENV_VARS if source.get(name)]
    absent = [name for name in CREDENTIAL_ENV_VARS if not source.get(name)]
    line = (
        f"[credentials] present={','.join(present) or '(none)'} "
        f"absent={','.join(absent) or '(none)'}"
    )

    if emit is None:
        logger.info(line)
    else:
        emit(line)

    _credentials_banner_emitted = True
    return line


class AgentRunner:
    """The main agent loop."""

    def __init__(self, config: AgentConfig):
        self.config = config
        self.provider = create_provider(config)
        self.db = SupabaseClient(config.supabase)
        self.registry = create_tool_registry(config, self.db)

    def run_cycle(self) -> CycleResult:
        """Execute one full agent cycle."""
        start = time.time()
        emit_credentials_banner()
        logger.info("Starting agent cycle...")

        # Phase 1: Orient (no LLM)
        logger.info("Phase 1: Orient")
        context = orient(self.db, self.config, self.registry)

        # Phase 1b: Reflection check
        if context.needs_reflection:
            logger.info("Reflection cycle triggered (>8 hours since last)")
            result = reflect(self.provider, self.db, self.config, self.registry)
            result.duration_ms = int((time.time() - start) * 1000)
            logger.info(f"Reflection complete: {result.summary}")
            return result

        # Phase 1c: Email check (additive — doesn't replace task cycle)
        if context.needs_email_check and self.config.email.enabled:
            logger.info("Email check triggered (>8 hours since last)")
            email_result = check_email(self.provider, self.db, self.config, self.registry)
            logger.info(f"Email check: {email_result.summary}")

        # Phase 2: Decide
        logger.info("Phase 2: Decide")
        decision = decide(self.provider, self.db, self.config, self.registry, context)

        if decision.action == "idle":
            logger.info("No actionable tasks found. Cycle complete.")
            return CycleResult(
                action="idle",
                summary="No actionable tasks found.",
                duration_ms=int((time.time() - start) * 1000),
            )

        if decision.action == "decompose_goal":
            logger.info(f"Decomposed goal {decision.goal_id} into tasks")
            return CycleResult(
                action="decompose_goal",
                goal_id=decision.goal_id,
                summary=f"Decomposed goal into {len(decision.new_tasks)} tasks",
                duration_ms=int((time.time() - start) * 1000),
            )

        # Phase 3: Execute
        logger.info(f"Phase 3: Execute task {decision.task_id}")
        execution = execute(
            self.provider, self.db, self.config, self.registry, context, decision
        )

        # Phase 4: Record
        logger.info("Phase 4: Record")
        result = record(
            self.provider, self.db, self.config, self.registry,
            context, decision, execution
        )
        result.duration_ms = int((time.time() - start) * 1000)

        logger.info(f"Cycle complete: {result.summary} ({result.duration_ms}ms)")
        return result
