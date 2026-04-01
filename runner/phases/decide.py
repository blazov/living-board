"""Phase 2: Decide -- pick ONE task to work on this cycle.

Uses the LLM to analyze the assembled context and decide what to do.
Handles goal decomposition (creating tasks) when a goal has none.
"""

from __future__ import annotations

import json
import logging
from typing import Any

from ..db import SupabaseClient
from ..models import AgentContext, Decision, Goal, Task
from ..providers.base import LLMProvider, LLMResponse, Message
from ..tools.registry import ToolRegistry

log = logging.getLogger(__name__)

_DECIDE_SYSTEM_PROMPT = """\
You are the decision-making module of the Living Board autonomous agent.

Your job: given the current board state, pick ONE action to take this cycle.

## Decision Rules (follow in order)

1. **Process comments first.** If there are unacknowledged user comments, they take priority. \
Return action="process_comments".

2. **Continue in-progress tasks.** If any task has status="in_progress", continue it. \
Return action="execute_task" with that task's ID.

3. **Pick next pending task.** Take the first pending task (by sort_order) in the highest-priority \
in_progress goal. Return action="execute_task" with that task's ID.

4. **Decompose a goal.** If a goal has status "in_progress" or "pending" but has NO tasks (or all \
tasks are done/blocked), decompose it into 3-8 concrete tasks. Return action="decompose_goal" \
with the goal's ID.

5. **Mark blocked tasks.** If a task has attempts >= max_attempts, it should be marked blocked. \
You can note this in your reasoning; the runner will handle it.

6. **Mark goals done.** If all tasks in a goal are done, return action="mark_goal_done" with the goal's ID.

7. **Nothing to do.** If there are no active goals or actionable tasks, return action="idle".

## Output Format

Respond with a JSON object (no markdown fences):
{
  "action": "execute_task" | "decompose_goal" | "mark_goal_done" | "process_comments" | "idle",
  "goal_id": "<uuid or null>",
  "task_id": "<uuid or null>",
  "reasoning": "<1-2 sentence explanation of your choice>"
}

If action is "decompose_goal", also include:
{
  "new_tasks": [
    {"title": "...", "description": "...", "sort_order": 10},
    {"title": "...", "description": "...", "sort_order": 20},
    ...
  ]
}

IMPORTANT: Return ONLY the JSON object. No other text.
"""


def _build_context_message(ctx: AgentContext) -> str:
    """Build a structured text summary of the current agent context."""
    parts: list[str] = []

    # Snapshot summary (if available)
    if ctx.snapshot:
        parts.append("## Current Snapshot")
        parts.append(ctx.snapshot.content)
        parts.append(f"Cycle: {ctx.snapshot.cycle_count}")
        if ctx.snapshot.current_focus:
            parts.append(f"Focus: {ctx.snapshot.current_focus}")
        if ctx.snapshot.open_blockers and ctx.snapshot.open_blockers != "[]":
            parts.append(f"Blockers: {ctx.snapshot.open_blockers}")
        parts.append("")

    # Goals
    parts.append("## Active Goals")
    if not ctx.goals:
        parts.append("(no active goals)")
    for g in ctx.goals:
        parts.append(
            f"- [{g.status}] P{g.priority} {g.title} (id={g.id})"
        )
        if g.description:
            parts.append(f"  Description: {g.description[:300]}")
        # List tasks for this goal
        goal_tasks = [t for t in ctx.tasks if t.goal_id == g.id]
        if goal_tasks:
            for t in goal_tasks:
                status_marker = {
                    "done": "[x]",
                    "in_progress": "[>]",
                    "blocked": "[!]",
                    "pending": "[ ]",
                }.get(t.status, "[ ]")
                task_line = (
                    f"  {status_marker} #{t.sort_order} {t.title} "
                    f"(id={t.id}, status={t.status}, attempts={t.attempts}/{t.max_attempts})"
                )
                parts.append(task_line)
                if t.status == "blocked" and t.blocked_reason:
                    parts.append(f"      Blocked: {t.blocked_reason}")
        else:
            parts.append("  (no tasks -- needs decomposition)")
    parts.append("")

    # Recent logs
    if ctx.recent_logs:
        parts.append("## Recent Execution Log")
        for log_entry in ctx.recent_logs:
            ts = log_entry.created_at.isoformat() if log_entry.created_at else "?"
            parts.append(f"- [{ts}] {log_entry.action}: {log_entry.summary}")
        parts.append("")

    # Learnings
    if ctx.learnings:
        parts.append("## Relevant Learnings")
        for l in ctx.learnings:
            parts.append(
                f"- [{l.category}, conf={l.confidence}] {l.content}"
            )
        parts.append("")

    # Comments
    if ctx.comments:
        parts.append("## Unacknowledged User Comments")
        for c in ctx.comments:
            parts.append(
                f"- [{c.comment_type}] on goal \"{c.goal_title}\": {c.content}"
            )
        parts.append("")

    # Memory results
    if ctx.memory_results:
        parts.append("## Vector Memory Recall")
        for m in ctx.memory_results:
            parts.append(
                f"- [score={m.get('score', '?')}, {m.get('category', '?')}] "
                f"{m.get('content', '')[:200]}"
            )
        parts.append("")

    return "\n".join(parts)


def _parse_decision(response: LLMResponse) -> Decision:
    """Parse the LLM response into a Decision object."""
    text = (response.content or "").strip()

    # Strip markdown code fences if present
    if text.startswith("```"):
        lines = text.split("\n")
        # Remove first and last lines (fences)
        lines = [l for l in lines if not l.strip().startswith("```")]
        text = "\n".join(lines).strip()

    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        log.warning("Failed to parse decision JSON, defaulting to idle: %s", text[:200])
        return Decision(
            action="idle",
            reasoning=f"Failed to parse LLM response: {text[:200]}",
        )

    return Decision(
        action=data.get("action", "idle"),
        goal_id=data.get("goal_id"),
        task_id=data.get("task_id"),
        reasoning=data.get("reasoning", ""),
        new_tasks=data.get("new_tasks", []),
    )


def _check_over_attempt_tasks(ctx: AgentContext, db: SupabaseClient) -> None:
    """Mark any tasks that have exceeded max_attempts as blocked."""
    for task in ctx.tasks:
        if task.status not in ("done", "blocked") and task.attempts >= task.max_attempts:
            log.info(
                "Marking task %s as blocked (attempts %d >= max %d)",
                task.id, task.attempts, task.max_attempts,
            )
            db.update_task(
                task.id,
                status="blocked",
                blocked_reason=f"Exceeded max attempts ({task.max_attempts})",
            )
            task.status = "blocked"
            task.blocked_reason = f"Exceeded max attempts ({task.max_attempts})"


def _check_completed_goals(ctx: AgentContext, db: SupabaseClient) -> list[str]:
    """Check if any goals have all tasks done and mark them complete.

    Returns list of goal IDs that were marked done.
    """
    completed: list[str] = []
    for goal in ctx.goals:
        goal_tasks = [t for t in ctx.tasks if t.goal_id == goal.id]
        if not goal_tasks:
            continue  # No tasks yet -- needs decomposition, not completion
        all_done = all(t.status in ("done", "blocked") for t in goal_tasks)
        any_done = any(t.status == "done" for t in goal_tasks)
        if all_done and any_done:
            log.info("All tasks for goal %s are done/blocked, marking goal done", goal.id)
            db.update_goal(goal.id, status="done")
            goal.status = "done"
            completed.append(goal.id)
    return completed


def decide(
    ctx: AgentContext,
    db: SupabaseClient,
    llm: LLMProvider,
    registry: ToolRegistry,
) -> Decision:
    """Execute Phase 2: Decide.

    Analyzes the context, handles mechanical checks (over-attempt tasks,
    completed goals), then asks the LLM to pick the next action.

    If decomposition is needed, uses the LLM with tool calling to
    generate and insert tasks.
    """
    # ── Pre-LLM mechanical checks ──
    _check_over_attempt_tasks(ctx, db)
    completed_goals = _check_completed_goals(ctx, db)

    if completed_goals:
        # Remove completed goals from context so LLM doesn't pick them
        ctx.goals = [g for g in ctx.goals if g.id not in completed_goals]

    # If there are no active goals left, we're idle
    if not ctx.goals:
        log.info("No active goals remaining, returning idle decision")
        return Decision(action="idle", reasoning="No active goals to work on.")

    # ── Comments take priority ──
    if ctx.comments:
        log.info("Unacknowledged comments found, prioritizing comment processing")
        return Decision(
            action="process_comments",
            reasoning=f"Found {len(ctx.comments)} unacknowledged user comment(s) to process.",
        )

    # ── Ask LLM to decide ──
    context_text = _build_context_message(ctx)
    messages = [
        Message(role="system", content=_DECIDE_SYSTEM_PROMPT),
        Message(role="user", content=context_text),
    ]

    log.info("Asking LLM to decide next action")
    response = llm.chat(messages, model_tier=2)
    decision = _parse_decision(response)
    log.info("LLM decision: action=%s, goal=%s, task=%s, reasoning=%s",
             decision.action, decision.goal_id, decision.task_id, decision.reasoning)

    # ── Handle decomposition: insert the tasks ──
    if decision.action == "decompose_goal" and decision.new_tasks:
        goal_id = decision.goal_id
        if not goal_id:
            log.warning("Decompose action but no goal_id provided")
            return Decision(action="idle", reasoning="Decompose requested but no goal_id.")

        log.info("Decomposing goal %s into %d tasks", goal_id, len(decision.new_tasks))
        result = registry.execute_by_name(
            "create_tasks",
            goal_id=goal_id,
            tasks=decision.new_tasks,
        )
        if result.success:
            log.info("Tasks created: %s", result.output)
            # Also mark the goal as in_progress if it was pending
            goal = next((g for g in ctx.goals if g.id == goal_id), None)
            if goal and goal.status == "pending":
                db.update_goal(goal_id, status="in_progress")

            # Log the decomposition
            db.insert_execution_log(
                action="decompose",
                summary=f"Decomposed goal into {len(decision.new_tasks)} tasks",
                goal_id=goal_id,
                details={
                    "task_count": len(decision.new_tasks),
                    "task_titles": [t.get("title", "") for t in decision.new_tasks],
                },
            )
        else:
            log.error("Failed to create tasks: %s", result.error)

    # ── If executing a task, mark it in_progress ──
    if decision.action == "execute_task" and decision.task_id:
        task = next((t for t in ctx.tasks if t.id == decision.task_id), None)
        if task and task.status == "pending":
            db.update_task(decision.task_id, status="in_progress")
        # Also ensure the parent goal is in_progress
        if decision.goal_id:
            goal = next((g for g in ctx.goals if g.id == decision.goal_id), None)
            if goal and goal.status == "pending":
                db.update_goal(decision.goal_id, status="in_progress")

    return decision
