"""Phase 4: Record -- persist results back to Supabase and update state.

Asks the LLM for a summary and learnings extraction, then:
- Updates the task status/result
- Inserts an execution log entry
- Dual-writes learnings to Supabase AND Qdrant (via memory tool)
- Regenerates the snapshot
- Updates goal status if all tasks are done
"""

from __future__ import annotations

import json
import logging
import time
from typing import Any

from ..db import SupabaseClient
from ..models import AgentContext, CycleResult, Decision, Goal, Task
from ..providers.base import LLMProvider, Message
from ..tools.registry import ToolRegistry

log = logging.getLogger(__name__)

_RECORD_SYSTEM_PROMPT = """\
You are the recording module of the Living Board autonomous agent.

Given the execution summary below, extract:
1. A concise 1-2 sentence summary of what was accomplished.
2. Any learnings or insights worth recording for future cycles.
3. What the agent should focus on next cycle.
4. Any blockers that remain.

Respond with a JSON object (no markdown fences):
{
  "summary": "1-2 sentence summary of what happened",
  "learnings": [
    {"content": "...", "category": "domain_knowledge|strategy|operational|meta", "confidence": 0.8}
  ],
  "next_focus": "what to work on next",
  "blockers": ["any remaining blockers"],
  "task_status": "done|blocked",
  "task_result": "detailed result text for the task record"
}

If the execution failed or was blocked, set task_status to "blocked" and explain in task_result.
IMPORTANT: Return ONLY the JSON object. No other text.
"""


def _build_record_context(
    ctx: AgentContext,
    decision: Decision,
    execution_summary: str,
    execution_artifacts: list[str],
    execution_success: bool,
) -> str:
    """Build context for the LLM to extract structured results."""
    parts: list[str] = []

    goal = next((g for g in ctx.goals if g.id == decision.goal_id), None)
    task = next((t for t in ctx.tasks if t.id == decision.task_id), None)

    if goal:
        parts.append(f"Goal: {goal.title}")
    if task:
        parts.append(f"Task: {task.title}")

    parts.append(f"\nExecution success: {execution_success}")
    parts.append(f"\nExecution summary:\n{execution_summary}")

    if execution_artifacts:
        parts.append(f"\nArtifacts produced: {execution_artifacts}")

    return "\n".join(parts)


def _parse_record_response(content: str) -> dict[str, Any]:
    """Parse the LLM response into structured record data."""
    text = content.strip()

    # Strip markdown fences if present
    if text.startswith("```"):
        lines = text.split("\n")
        lines = [l for l in lines if not l.strip().startswith("```")]
        text = "\n".join(lines).strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        log.warning("Failed to parse record JSON: %s", text[:200])
        return {
            "summary": text[:200],
            "learnings": [],
            "next_focus": "",
            "blockers": [],
            "task_status": "done",
            "task_result": text[:500],
        }


def _store_learnings(
    learnings: list[dict[str, Any]],
    goal_id: str | None,
    task_id: str | None,
    db: SupabaseClient,
    registry: ToolRegistry,
) -> int:
    """Dual-write learnings to Supabase and Qdrant.

    Returns the count of learnings stored.
    """
    count = 0
    for learning in learnings:
        content = learning.get("content", "")
        category = learning.get("category", "domain_knowledge")
        confidence = learning.get("confidence", 0.8)

        if not content:
            continue

        # Supabase (always)
        try:
            db.insert_learning(
                content=content,
                category=category,
                confidence=confidence,
                goal_id=goal_id,
                task_id=task_id,
            )
        except Exception as exc:
            log.error("Failed to store learning in Supabase: %s", exc)

        # Qdrant (if available)
        if registry.has("memory_store"):
            result = registry.execute_by_name(
                "memory_store",
                text=content,
                category=category,
                confidence=confidence,
                goal_id=goal_id,
                task_id=task_id,
            )
            if not result.success:
                log.info("Memory store unavailable: %s", result.error)

        count += 1

    return count


def _build_snapshot(
    ctx: AgentContext,
    summary: str,
    next_focus: str,
    blockers: list[str],
    learnings_stored: list[dict[str, Any]],
    db: SupabaseClient,
) -> None:
    """Regenerate the snapshot for the next cycle."""
    # Refresh active goals from DB for accurate snapshot
    active_goals = db.get_active_goals()
    active_goals_json: list[dict[str, Any]] = []
    for g in active_goals:
        tasks = db.get_tasks_for_goal(g.id)
        total = len(tasks)
        done = sum(1 for t in tasks if t.status == "done")
        pct = int((done / total) * 100) if total > 0 else 0
        active_goals_json.append({
            "id": g.id,
            "title": g.title,
            "status": g.status,
            "progress_pct": pct,
        })

    # Build recent outcomes from the last 3 logs
    recent_logs = db.get_recent_logs(limit=3)
    recent_outcomes: list[dict[str, Any]] = []
    for entry in recent_logs:
        recent_outcomes.append({
            "summary": entry.summary,
            "timestamp": entry.created_at.isoformat() if entry.created_at else "",
            "success": entry.action != "blocked",
        })

    # Build blockers list
    blockers_json: list[dict[str, Any]] = []
    for b in blockers:
        blockers_json.append({"description": b})

    # Top learnings
    key_learnings: list[dict[str, Any]] = []
    for l in learnings_stored[:5]:
        key_learnings.append({
            "content": l.get("content", ""),
            "confidence": l.get("confidence", 0.8),
            "category": l.get("category", "domain_knowledge"),
        })
    # Also pull recent from DB if we don't have enough
    if len(key_learnings) < 5:
        db_learnings = db.get_learnings(limit=5)
        for l in db_learnings:
            if len(key_learnings) >= 5:
                break
            if l.content not in [k["content"] for k in key_learnings]:
                key_learnings.append({
                    "content": l.content,
                    "confidence": l.confidence,
                    "category": l.category,
                })

    # Get current cycle count
    current_snapshot = db.get_snapshot()
    cycle_count = (current_snapshot.cycle_count + 1) if current_snapshot else 1

    # Build the natural language content
    content = summary
    if next_focus:
        content += f"\n\nNext focus: {next_focus}"

    db.insert_snapshot(
        content=content,
        active_goals=json.dumps(active_goals_json),
        current_focus=next_focus,
        recent_outcomes=json.dumps(recent_outcomes),
        open_blockers=json.dumps(blockers_json),
        key_learnings=json.dumps(key_learnings),
        cycle_count=cycle_count,
    )
    log.info("Snapshot regenerated (cycle %d)", cycle_count)


def record(
    ctx: AgentContext,
    decision: Decision,
    execution_summary: str,
    execution_artifacts: list[str],
    execution_success: bool,
    db: SupabaseClient,
    llm: LLMProvider,
    registry: ToolRegistry,
) -> CycleResult:
    """Execute Phase 4: Record.

    Persists execution results to Supabase, extracts learnings,
    and regenerates the snapshot.
    """
    cycle_result = CycleResult(
        action=decision.action,
        goal_id=decision.goal_id,
        task_id=decision.task_id,
        success=execution_success,
    )

    # ── Ask LLM to extract structured results ──
    record_context = _build_record_context(
        ctx, decision, execution_summary, execution_artifacts, execution_success,
    )
    messages = [
        Message(role="system", content=_RECORD_SYSTEM_PROMPT),
        Message(role="user", content=record_context),
    ]

    response = llm.chat(messages, model_tier=3)  # Use haiku for extraction
    record_data = _parse_record_response(response.content or "{}")

    structured_summary = record_data.get("summary", execution_summary)
    task_status = record_data.get("task_status", "done" if execution_success else "blocked")
    task_result = record_data.get("task_result", execution_summary)
    next_focus = record_data.get("next_focus", "")
    blockers = record_data.get("blockers", [])
    raw_learnings = record_data.get("learnings", [])

    cycle_result.summary = structured_summary
    cycle_result.learnings = [l.get("content", "") for l in raw_learnings if l.get("content")]

    # ── 1. Update the task ──
    if decision.task_id:
        try:
            update_fields: dict[str, Any] = {
                "status": task_status,
                "result": task_result[:2000],  # Truncate long results
            }
            if task_status == "done":
                update_fields["completed_at"] = time.strftime(
                    "%Y-%m-%dT%H:%M:%SZ", time.gmtime()
                )
            # Increment attempts
            task = next((t for t in ctx.tasks if t.id == decision.task_id), None)
            if task:
                update_fields["attempts"] = task.attempts + 1

            db.update_task(decision.task_id, **update_fields)
            log.info("Task %s updated: status=%s", decision.task_id, task_status)
        except Exception as exc:
            log.error("Failed to update task %s: %s", decision.task_id, exc)

    # ── 2. Check if goal is now complete ──
    if decision.goal_id:
        try:
            goal_tasks = db.get_tasks_for_goal(decision.goal_id)
            # Re-check: get_tasks_for_goal only returns pending/in_progress,
            # so if it returns empty, all tasks are done or blocked
            if not goal_tasks:
                log.info("All tasks for goal %s appear complete, marking done", decision.goal_id)
                db.update_goal(decision.goal_id, status="done")
        except Exception as exc:
            log.error("Failed to check goal completion: %s", exc)

    # ── 3. Insert execution log ──
    try:
        db.insert_execution_log(
            action="execute",
            summary=structured_summary,
            goal_id=decision.goal_id,
            task_id=decision.task_id,
            details={
                "artifacts": execution_artifacts,
                "outcome": "success" if execution_success else "failure",
                "tool_calls": execution_summary[:500] if execution_summary else "",
            },
        )
        log.info("Execution log inserted")
    except Exception as exc:
        log.error("Failed to insert execution log: %s", exc)

    # ── 4. Store learnings (dual-write) ──
    if raw_learnings:
        stored = _store_learnings(
            raw_learnings,
            goal_id=decision.goal_id,
            task_id=decision.task_id,
            db=db,
            registry=registry,
        )
        log.info("Stored %d learnings", stored)

    # ── 5. Regenerate snapshot ──
    try:
        _build_snapshot(
            ctx=ctx,
            summary=structured_summary,
            next_focus=next_focus,
            blockers=blockers,
            learnings_stored=raw_learnings,
            db=db,
        )
    except Exception as exc:
        log.error("Failed to regenerate snapshot: %s", exc)

    return cycle_result
