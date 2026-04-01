"""Reflection cycle -- replaces Phases 2-3 when reflection is needed.

Follows CLAUDE.md Phase 1b:
- Read the full board (all goals, recent learnings, last 10 logs)
- Ask LLM to think about new goals, validate learnings, consolidate memories
- Insert proposed goals as pending
- Log the reflection
"""

from __future__ import annotations

import json
import logging
import time
from typing import Any

from ..db import SupabaseClient
from ..models import AgentContext, CycleResult
from ..providers.base import LLMProvider, Message
from ..tools.registry import ToolRegistry

log = logging.getLogger(__name__)

_REFLECT_SYSTEM_PROMPT = """\
You are the Living Board autonomous agent in a **reflection cycle**.

This is not an execution cycle -- you are stepping back to think strategically.

## Your Tasks

1. **Review the full board.** Look at all goals (active, pending, done, blocked), \
recent learnings, and execution history.

2. **Think about new goals.** Consider:
   - What goals would amplify or unblock existing ones?
   - What's missing from the current strategy? What blind spots exist?
   - What interests, curiosities, or creative ideas feel worth exploring?
   - What did you learn recently that opens up a new direction?
   - What would you work on if you had no obligations?

3. **Propose 0-2 new goals.** Only propose goals that are genuinely worth pursuing. \
Don't propose goals just because you can.

4. **Validate learnings.** Check if recent task outcomes confirm or contradict stored learnings.

5. **Identify patterns.** Look for cross-goal patterns and meta-learnings.

## Output Format

Respond with a JSON object (no markdown fences):
{
  "reflection_summary": "1-2 sentence summary of what you reflected on",
  "new_goals": [
    {
      "title": "Goal title",
      "description": "Clear description explaining reasoning -- why this goal, why now",
      "priority": 5
    }
  ],
  "meta_learnings": [
    {
      "content": "Cross-goal insight or pattern",
      "category": "meta",
      "confidence": 0.7
    }
  ],
  "learnings_to_validate": [
    {
      "content": "Learning content that was confirmed or contradicted",
      "confirmed": true,
      "reasoning": "Why this was confirmed/contradicted"
    }
  ],
  "strategic_notes": "Any broader strategic observations"
}

IMPORTANT: Return ONLY the JSON object. No other text.
"""


def _build_reflection_context(
    ctx: AgentContext,
    all_goals: list[dict[str, Any]],
    all_learnings: list[dict[str, Any]],
    recent_logs: list[dict[str, Any]],
) -> str:
    """Build a comprehensive context for the reflection."""
    parts: list[str] = []

    # All goals (not just active)
    parts.append("## All Goals")
    for g in all_goals:
        status = g.get("status", "?")
        title = g.get("title", "?")
        priority = g.get("priority", "?")
        created_by = g.get("created_by", "user")
        parts.append(f"- [{status}] P{priority} {title} (created_by={created_by}, id={g.get('id', '?')})")
        if g.get("description"):
            parts.append(f"  {g['description'][:300]}")
    parts.append("")

    # Recent execution logs (last 10)
    parts.append("## Recent Execution Log (last 10)")
    for entry in recent_logs:
        ts = entry.get("created_at", "?")
        action = entry.get("action", "?")
        summary = entry.get("summary", "?")
        parts.append(f"- [{ts}] {action}: {summary}")
    parts.append("")

    # All learnings
    parts.append("## Stored Learnings")
    if not all_learnings:
        parts.append("(no learnings stored yet)")
    for l in all_learnings:
        cat = l.get("category", "?")
        content = l.get("content", "?")
        conf = l.get("confidence", "?")
        parts.append(f"- [{cat}, conf={conf}] {content}")
    parts.append("")

    # Memory results from orient phase
    if ctx.memory_results:
        parts.append("## Vector Memory (semantic search results)")
        for m in ctx.memory_results:
            parts.append(
                f"- [score={m.get('score', '?')}, {m.get('category', '?')}] "
                f"{m.get('content', '')[:200]}"
            )
        parts.append("")

    return "\n".join(parts)


def _parse_reflection(content: str) -> dict[str, Any]:
    """Parse the LLM's reflection response."""
    text = content.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        lines = [l for l in lines if not l.strip().startswith("```")]
        text = "\n".join(lines).strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        log.warning("Failed to parse reflection JSON: %s", text[:200])
        return {
            "reflection_summary": text[:200],
            "new_goals": [],
            "meta_learnings": [],
            "learnings_to_validate": [],
            "strategic_notes": "",
        }


def reflect(
    ctx: AgentContext,
    db: SupabaseClient,
    llm: LLMProvider,
    registry: ToolRegistry,
) -> CycleResult:
    """Execute a reflection cycle.

    Reads the full board, asks the LLM to reflect strategically,
    proposes new goals, validates learnings, and logs the reflection.
    This replaces Phases 2-3 for this cycle.
    """
    result = CycleResult(action="reflect", success=True)

    # ── Load full board state ──
    log.info("Reflection: loading full board state")

    # All goals (not just active -- include done and blocked)
    try:
        all_goals_raw = db._request(
            "goals?select=*&order=priority.asc,created_at.asc"
        )
    except Exception as exc:
        log.error("Failed to load all goals: %s", exc)
        all_goals_raw = []

    # All learnings
    try:
        all_learnings_raw = db._request(
            "learnings?select=*&order=confidence.desc&limit=30"
        )
    except Exception as exc:
        log.error("Failed to load learnings: %s", exc)
        all_learnings_raw = []

    # Last 10 execution logs
    try:
        recent_logs_raw = db._request(
            "execution_log?select=*&order=created_at.desc&limit=10"
        )
    except Exception as exc:
        log.error("Failed to load execution logs: %s", exc)
        recent_logs_raw = []

    # ── Ask LLM to reflect ──
    context_text = _build_reflection_context(
        ctx, all_goals_raw, all_learnings_raw, recent_logs_raw,
    )
    messages = [
        Message(role="system", content=_REFLECT_SYSTEM_PROMPT),
        Message(role="user", content=context_text),
    ]

    log.info("Asking LLM to reflect")
    response = llm.chat(messages, model_tier=1)  # Use tier 1 (opus) for reflection
    reflection = _parse_reflection(response.content or "{}")

    reflection_summary = reflection.get("reflection_summary", "Reflection completed.")
    new_goals = reflection.get("new_goals", [])
    meta_learnings = reflection.get("meta_learnings", [])
    strategic_notes = reflection.get("strategic_notes", "")

    result.summary = reflection_summary

    # ── Insert proposed goals ──
    goals_inserted: list[str] = []
    for goal_data in new_goals:
        title = goal_data.get("title", "")
        description = goal_data.get("description", "")
        priority = goal_data.get("priority", 5)

        if not title:
            continue

        try:
            db._request("goals", method="POST", data={
                "title": title,
                "description": description,
                "status": "pending",
                "priority": priority,
                "created_by": "agent",
                "metadata": json.dumps({
                    "proposed_during": "reflection",
                    "proposed_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                }),
            })
            goals_inserted.append(title)
            log.info("Proposed new goal: %s", title)
        except Exception as exc:
            log.error("Failed to insert goal '%s': %s", title, exc)

    # ── Store meta-learnings (dual-write) ──
    learnings_stored = 0
    for learning in meta_learnings:
        content = learning.get("content", "")
        category = learning.get("category", "meta")
        confidence = learning.get("confidence", 0.7)

        if not content:
            continue

        # Supabase
        try:
            db.insert_learning(
                content=content,
                category=category,
                confidence=confidence,
                goal_id=None,  # meta-learnings are global
            )
        except Exception as exc:
            log.error("Failed to store meta-learning in Supabase: %s", exc)

        # Qdrant
        if registry.has("memory_store"):
            mem_result = registry.execute_by_name(
                "memory_store",
                text=content,
                category=category,
                confidence=confidence,
            )
            if not mem_result.success:
                log.info("Memory store unavailable: %s", mem_result.error)

        learnings_stored += 1

    result.learnings = [l.get("content", "") for l in meta_learnings if l.get("content")]

    # ── Validate existing learnings ──
    validations = reflection.get("learnings_to_validate", [])
    validated_count = 0
    for v in validations:
        # We note the validation but since we don't have point IDs from
        # Supabase learnings, we log it rather than updating confidence
        log.info(
            "Learning validation: confirmed=%s, content='%s', reason='%s'",
            v.get("confirmed"), v.get("content", "")[:100], v.get("reasoning", ""),
        )
        validated_count += 1

    # ── Log the reflection ──
    try:
        db.insert_execution_log(
            action="reflect",
            summary=f"Reflection cycle: {reflection_summary}",
            details={
                "new_goals_proposed": goals_inserted,
                "reasoning": strategic_notes,
                "memories_consolidated": 0,  # Placeholder for future consolidation
                "learnings_validated": validated_count,
                "meta_learnings_stored": learnings_stored,
            },
        )
        log.info("Reflection logged")
    except Exception as exc:
        log.error("Failed to log reflection: %s", exc)

    # ── Regenerate snapshot ──
    try:
        _regenerate_snapshot_after_reflection(db, reflection_summary)
    except Exception as exc:
        log.error("Failed to regenerate snapshot: %s", exc)

    log.info(
        "Reflection complete: %d new goals proposed, %d meta-learnings, %d validations",
        len(goals_inserted), learnings_stored, validated_count,
    )

    return result


def _regenerate_snapshot_after_reflection(
    db: SupabaseClient,
    reflection_summary: str,
) -> None:
    """Regenerate the snapshot after a reflection cycle."""
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

    recent_logs = db.get_recent_logs(limit=3)
    recent_outcomes: list[dict[str, Any]] = []
    for entry in recent_logs:
        recent_outcomes.append({
            "summary": entry.summary,
            "timestamp": entry.created_at.isoformat() if entry.created_at else "",
            "success": entry.action != "blocked",
        })

    db_learnings = db.get_learnings(limit=5)
    key_learnings: list[dict[str, Any]] = []
    for l in db_learnings:
        key_learnings.append({
            "content": l.content,
            "confidence": l.confidence,
            "category": l.category,
        })

    current_snapshot = db.get_snapshot()
    cycle_count = (current_snapshot.cycle_count + 1) if current_snapshot else 1

    content = f"Completed reflection cycle. {reflection_summary}"

    # Determine next focus from highest-priority active goal
    next_focus = ""
    if active_goals:
        next_focus = f"Continue working on: {active_goals[0].title}"

    db.insert_snapshot(
        content=content,
        active_goals=json.dumps(active_goals_json),
        current_focus=next_focus,
        recent_outcomes=json.dumps(recent_outcomes),
        open_blockers="[]",
        key_learnings=json.dumps(key_learnings),
        cycle_count=cycle_count,
    )
    log.info("Snapshot regenerated after reflection (cycle %d)", cycle_count)
