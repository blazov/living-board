"""Phase 1: Orient -- gather context from Supabase and memory.

This phase is pure Python (no LLM calls). It reads the current state
from Supabase, checks for comments, searches vector memory if available,
and determines whether reflection or email checks are needed.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from ..config import AgentConfig
from ..db import SupabaseClient
from ..models import AgentContext, Goal, Snapshot, Task
from ..tools.registry import ToolRegistry

log = logging.getLogger(__name__)

_STALE_THRESHOLD_HOURS = 2
_REFLECTION_INTERVAL_HOURS = 8
_EMAIL_CHECK_INTERVAL_HOURS = 8


def _parse_timestamp(ts: str | None) -> datetime | None:
    """Parse an ISO timestamp string into a timezone-aware datetime."""
    if not ts:
        return None
    try:
        # Handle various ISO formats from Supabase
        ts = ts.replace("Z", "+00:00")
        return datetime.fromisoformat(ts)
    except (ValueError, TypeError):
        return None


def _is_stale(created_at: datetime | None, threshold_hours: float) -> bool:
    """Check if a timestamp is older than threshold_hours from now."""
    if created_at is None:
        return True
    now = datetime.now(timezone.utc)
    if created_at.tzinfo is None:
        created_at = created_at.replace(tzinfo=timezone.utc)
    age_hours = (now - created_at).total_seconds() / 3600
    return age_hours > threshold_hours


def _search_memory(
    registry: ToolRegistry,
    query: str,
) -> list[dict[str, Any]]:
    """Search vector memory if the memory_search tool is available.

    Returns an empty list if the tool is not registered or the backend
    is unavailable -- memory is optional.
    """
    if not registry.has("memory_search"):
        log.info("memory_search tool not available, skipping vector recall")
        return []

    result = registry.execute_by_name("memory_search", query=query, limit=10)
    if result.success and result.data:
        log.info("Vector memory returned %d results", len(result.data))
        return result.data
    if not result.success:
        log.info("Vector memory search failed: %s", result.error)
    return []


def orient(
    db: SupabaseClient,
    config: AgentConfig,
    registry: ToolRegistry,
) -> AgentContext:
    """Execute Phase 1: Orient.

    Reads state from Supabase, checks staleness, loads comments,
    optionally searches vector memory, and flags whether reflection
    or email checks are needed.

    Returns a fully populated AgentContext.
    """
    ctx = AgentContext()

    # ── Step 1: Read snapshot ──
    log.info("Phase 1: Reading latest snapshot")
    snapshot = db.get_snapshot()
    snapshot_is_fresh = False

    if snapshot is not None:
        snapshot_ts = _parse_timestamp(
            snapshot.created_at.isoformat() if snapshot.created_at else None
        )
        snapshot_is_fresh = not _is_stale(snapshot_ts, _STALE_THRESHOLD_HOURS)

    if snapshot_is_fresh and snapshot is not None:
        log.info("Snapshot is fresh (cycle %d), using it for context", snapshot.cycle_count)
        ctx.snapshot = snapshot
    else:
        reason = "stale" if snapshot is not None else "missing"
        log.info("Snapshot is %s, falling back to full queries", reason)

    # ── Always load active goals (needed for decision-making) ──
    goals = db.get_active_goals()
    ctx.goals = goals
    log.info("Loaded %d active goals", len(goals))

    # ── If snapshot is stale/missing, load full context ──
    if not snapshot_is_fresh:
        # Load tasks for each goal
        all_tasks: list[Task] = []
        for goal in goals:
            goal_tasks = db.get_tasks_for_goal(goal.id)
            all_tasks.extend(goal_tasks)
        ctx.tasks = all_tasks
        log.info("Loaded %d tasks across all active goals", len(all_tasks))

        # Recent execution logs
        ctx.recent_logs = db.get_recent_logs(limit=5)
        log.info("Loaded %d recent execution logs", len(ctx.recent_logs))

        # Learnings for top-priority goal (and global learnings)
        top_goal_id = goals[0].id if goals else None
        ctx.learnings = db.get_learnings(goal_id=top_goal_id, limit=10)
        log.info("Loaded %d relevant learnings", len(ctx.learnings))
    else:
        # Even with a fresh snapshot, load tasks for the active goals
        # so the decide phase has task-level detail
        all_tasks = []
        for goal in goals:
            goal_tasks = db.get_tasks_for_goal(goal.id)
            all_tasks.extend(goal_tasks)
        ctx.tasks = all_tasks

        # Also load recent logs for awareness
        ctx.recent_logs = db.get_recent_logs(limit=5)

    # ── Step 2: Check for unacknowledged user comments ──
    comments = db.get_unacknowledged_comments()
    ctx.comments = comments
    if comments:
        log.info("Found %d unacknowledged user comments", len(comments))
    else:
        log.info("No unacknowledged comments")

    # ── Step 3: Sync Supabase learnings → Qdrant ──
    # Catches up any learnings created while Qdrant was unreachable
    # (e.g., overnight via remote trigger). Runs every cycle but is
    # a no-op when there's nothing new to sync.
    from ..tools.memory import sync_learnings
    synced = sync_learnings(db, config.memory)
    if synced > 0:
        log.info("Synced %d learnings from Supabase to Qdrant", synced)

    # ── Step 4: Semantic memory recall ──
    # Build a search query from the top-priority goal + its first pending task
    memory_query_parts: list[str] = []
    if goals:
        top_goal = goals[0]
        memory_query_parts.append(top_goal.title)
        if top_goal.description:
            memory_query_parts.append(top_goal.description[:200])
    # Add the first pending/in_progress task title
    pending_tasks = [t for t in ctx.tasks if t.status in ("pending", "in_progress")]
    if pending_tasks:
        memory_query_parts.append(pending_tasks[0].title)
        if pending_tasks[0].description:
            memory_query_parts.append(pending_tasks[0].description[:200])

    if memory_query_parts:
        memory_query = " ".join(memory_query_parts)
        ctx.memory_results = _search_memory(registry, memory_query)

    # ── Check if reflection is needed ──
    last_reflection = db.get_last_reflection_time()
    last_reflection_dt = _parse_timestamp(last_reflection)
    ctx.needs_reflection = _is_stale(last_reflection_dt, _REFLECTION_INTERVAL_HOURS)
    if ctx.needs_reflection:
        log.info("Reflection needed (last: %s)", last_reflection or "never")

    # ── Check if email check is needed ──
    if config.email.enabled:
        last_email = db.get_last_email_check_time()
        last_email_dt = _parse_timestamp(last_email)
        ctx.needs_email_check = _is_stale(last_email_dt, _EMAIL_CHECK_INTERVAL_HOURS)
        if ctx.needs_email_check:
            log.info("Email check needed (last: %s)", last_email or "never")
    else:
        ctx.needs_email_check = False

    log.info(
        "Orient complete: %d goals, %d tasks, %d comments, "
        "reflection=%s, email_check=%s",
        len(ctx.goals),
        len(ctx.tasks),
        len(ctx.comments),
        ctx.needs_reflection,
        ctx.needs_email_check,
    )
    return ctx
