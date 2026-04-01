"""Phase 3: Execute -- run the chosen task via LLM tool-use loop.

Sends the task context and available tools to the LLM, then loops:
LLM returns tool calls -> execute them -> send results back -> repeat.
Stops when the LLM returns end_turn or max_tool_calls is reached.
"""

from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass, field
from typing import Any

from ..config import AgentConfig
from ..db import SupabaseClient
from ..models import AgentContext, Decision, Goal, Task
from ..providers.base import LLMProvider, LLMResponse, Message, ToolCall
from ..tools.base import ToolResult
from ..tools.registry import ToolRegistry

log = logging.getLogger(__name__)


@dataclass
class ExecutionResult:
    """Output of the execute phase."""
    summary: str = ""
    artifacts: list[str] = field(default_factory=list)
    learnings: list[str] = field(default_factory=list)
    success: bool = True
    tool_calls_made: int = 0
    error: str | None = None


_EXECUTE_SYSTEM_PROMPT = """\
You are the Living Board autonomous agent executing a task.

You have tools available to accomplish your work. Use them as needed.
Work concretely -- produce real artifacts and results, not just plans.

When you are DONE with the task, stop calling tools and provide a final summary \
of what you accomplished, including:
- What was done
- Any files/artifacts produced
- Any blockers encountered
- Any learnings or insights worth recording

Be specific and concrete in your summary.
"""


def _get_model_tier(
    task: Task | None,
    goal: Goal | None,
) -> int:
    """Determine the model tier from task/goal metadata.

    Task-level model overrides goal-level. Maps string model names
    to tier numbers: opus->1, sonnet->2, haiku->3.

    Returns 2 (sonnet) as the default for execution tasks.
    """
    model_map = {
        "opus": 1,
        "sonnet": 2,
        "haiku": 3,
    }

    # Check task metadata first
    if task and task.metadata.get("model"):
        model_name = task.metadata["model"].lower()
        if model_name in model_map:
            return model_map[model_name]

    # Fall back to goal metadata
    if goal and goal.metadata.get("model"):
        model_name = goal.metadata["model"].lower()
        if model_name in model_map:
            return model_map[model_name]

    # Default: tier 2 (sonnet) for execution tasks
    return 2


def _build_task_context(
    ctx: AgentContext,
    decision: Decision,
) -> str:
    """Build a focused context message for the task being executed."""
    parts: list[str] = []

    # Find the goal and task
    goal = next((g for g in ctx.goals if g.id == decision.goal_id), None)
    task = next((t for t in ctx.tasks if t.id == decision.task_id), None)

    if goal:
        parts.append(f"## Goal: {goal.title}")
        if goal.description:
            parts.append(goal.description)
        parts.append("")

    if task:
        parts.append(f"## Task: {task.title}")
        if task.description:
            parts.append(task.description)
        if task.result:
            parts.append(f"\nPrevious attempt result: {task.result}")
        if task.attempts > 0:
            parts.append(f"Attempt: {task.attempts + 1} of {task.max_attempts}")
        parts.append("")

    # Include relevant learnings
    if ctx.learnings:
        parts.append("## Relevant Learnings")
        for l in ctx.learnings[:5]:
            parts.append(f"- [{l.category}] {l.content}")
        parts.append("")

    # Include memory results
    if ctx.memory_results:
        parts.append("## Relevant Memories")
        for m in ctx.memory_results[:5]:
            parts.append(f"- {m.get('content', '')[:200]}")
        parts.append("")

    # Recent execution context
    if ctx.recent_logs:
        parts.append("## Recent Activity")
        for entry in ctx.recent_logs[:3]:
            parts.append(f"- {entry.action}: {entry.summary}")
        parts.append("")

    return "\n".join(parts)


def _build_comment_context(ctx: AgentContext) -> str:
    """Build context for processing user comments."""
    parts: list[str] = []

    parts.append("## User Comments to Process")
    parts.append("")
    parts.append("Process each comment below. For each comment:")
    parts.append("- direction_change: Adjust priorities, create/modify/delete tasks as needed")
    parts.append("- question: Provide a clear, specific answer")
    parts.append("- feedback: Extract learnings and adjust approach")
    parts.append("- note: Acknowledge and factor into work")
    parts.append("")

    for c in ctx.comments:
        parts.append(f"### Comment on goal \"{c.goal_title}\" (goal_id={c.goal_id})")
        parts.append(f"Type: {c.comment_type}")
        parts.append(f"Comment ID: {c.id}")
        parts.append(f"Content: {c.content}")
        parts.append("")

    parts.append(
        "After processing each comment, use the execute_sql tool to acknowledge it:\n"
        "PATCH goal_comments?id=eq.<comment_id> with "
        '{acknowledged_at: "<ISO timestamp>", agent_response: "<your response>"}'
    )

    # Include current goals/tasks for context
    if ctx.goals:
        parts.append("\n## Current Board State")
        for g in ctx.goals:
            parts.append(f"- [{g.status}] P{g.priority} {g.title} (id={g.id})")
            goal_tasks = [t for t in ctx.tasks if t.goal_id == g.id]
            for t in goal_tasks:
                parts.append(f"  - [{t.status}] {t.title} (id={t.id})")

    return "\n".join(parts)


def execute(
    ctx: AgentContext,
    decision: Decision,
    db: SupabaseClient,
    llm: LLMProvider,
    config: AgentConfig,
    registry: ToolRegistry,
) -> ExecutionResult:
    """Execute Phase 3: run the task through an LLM tool-use loop.

    Sends the task context + tool schemas to the LLM and loops until
    the LLM stops calling tools or max_tool_calls is reached.
    """
    result = ExecutionResult()
    max_tool_calls = config.execution.max_tool_calls

    # Determine what we're executing
    if decision.action == "process_comments":
        user_content = _build_comment_context(ctx)
        model_tier = 2  # sonnet for comment processing
    elif decision.action == "execute_task":
        goal = next((g for g in ctx.goals if g.id == decision.goal_id), None)
        task = next((t for t in ctx.tasks if t.id == decision.task_id), None)
        user_content = _build_task_context(ctx, decision)
        model_tier = _get_model_tier(task, goal)
    else:
        log.warning("Execute called with unexpected action: %s", decision.action)
        result.success = False
        result.error = f"Unexpected action for execution: {decision.action}"
        return result

    log.info(
        "Executing with model tier %d, max %d tool calls",
        model_tier, max_tool_calls,
    )

    # Build initial messages
    messages: list[Message] = [
        Message(role="system", content=_EXECUTE_SYSTEM_PROMPT),
        Message(role="user", content=user_content),
    ]

    # Get tool schemas
    tool_schemas = registry.get_schemas()

    # ── Tool-use loop ──
    tool_call_count = 0
    start_time = time.monotonic()

    while True:
        # Call the LLM
        response = llm.chat(messages, tools=tool_schemas, model_tier=model_tier)

        # If no tool calls, we're done
        if not response.tool_calls:
            result.summary = response.content or "Task completed (no summary provided)."
            break

        # If we've hit max tool calls, stop
        if tool_call_count + len(response.tool_calls) > max_tool_calls:
            log.warning(
                "Approaching max tool calls (%d/%d), forcing stop",
                tool_call_count, max_tool_calls,
            )
            result.summary = (
                response.content
                or f"Execution stopped: reached max tool calls ({max_tool_calls})."
            )
            result.success = False
            result.error = f"Max tool calls reached ({max_tool_calls})"
            break

        # Add the assistant message (with its tool calls) to history
        messages.append(
            Message(
                role="assistant",
                content=response.content,
                tool_calls=response.tool_calls,
            )
        )

        # Execute each tool call and add results to messages
        for tc in response.tool_calls:
            tool_call_count += 1
            log.info(
                "Tool call %d/%d: %s(%s)",
                tool_call_count,
                max_tool_calls,
                tc.name,
                _truncate_args(tc.arguments),
            )

            tool_result = registry.execute(tc)

            # Track artifacts from file writes
            if tc.name == "write_file" and tool_result.success:
                path = tc.arguments.get("path", "")
                if path:
                    result.artifacts.append(path)

            # Add tool result as a message
            messages.append(
                Message(
                    role="tool",
                    content=tool_result.to_content(),
                    tool_call_id=tc.id,
                    name=tc.name,
                )
            )

        # Check if the LLM indicated end_turn
        if response.stop_reason == "end_turn":
            result.summary = response.content or "Task completed."
            break

    # ── Finalize ──
    elapsed_ms = int((time.monotonic() - start_time) * 1000)
    result.tool_calls_made = tool_call_count

    log.info(
        "Execution complete: %d tool calls in %dms, success=%s",
        tool_call_count, elapsed_ms, result.success,
    )

    return result


def _truncate_args(args: dict[str, Any], max_len: int = 100) -> str:
    """Truncate tool call arguments for logging."""
    s = json.dumps(args, default=str)
    if len(s) > max_len:
        return s[:max_len] + "..."
    return s
