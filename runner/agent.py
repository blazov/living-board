"""Main agent loop — Orient → Decide → Execute → Record."""

from __future__ import annotations

import logging
import time

from .config import AgentConfig
from .db import SupabaseClient
from .models import CycleResult
from .phases import orient, decide, execute, record, reflect, check_email
from .providers import create_provider
from .tools import create_tool_registry

logger = logging.getLogger("living-board")


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
