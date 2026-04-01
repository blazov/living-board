"""Email check cycle -- runs in addition to the normal task cycle.

Uses the email tools (list_emails, read_email, send_email) through
an LLM tool-use loop to triage and act on incoming messages.
Only runs if config.email.enabled is True.
"""

from __future__ import annotations

import json
import logging
import time
from typing import Any

from ..config import AgentConfig
from ..db import SupabaseClient
from ..models import AgentContext, CycleResult
from ..providers.base import LLMProvider, Message
from ..tools.registry import ToolRegistry

log = logging.getLogger(__name__)

_EMAIL_SYSTEM_PROMPT = """\
You are the Living Board autonomous agent checking your email inbox.

Your email address: {email_address}

## Instructions

1. **List recent messages** using the list_emails tool.
2. **Triage each new message:**
   - **Actionable** (verification emails, replies to outreach, collaboration requests): \
Read the full message with read_email and take action if possible. \
If action requires a full task cycle, note what needs to be done.
   - **Informational** (newsletters, notifications, tips): Skim subject lines. \
Only read if directly relevant to an active goal.
   - **Spam/irrelevant**: Ignore.
3. **Send replies or new emails** when appropriate using send_email.

## Active Goals for Context
{goals_context}

## Output

After processing emails, provide a summary of what you found and any actions taken.
"""


def check_email(
    ctx: AgentContext,
    db: SupabaseClient,
    llm: LLMProvider,
    config: AgentConfig,
    registry: ToolRegistry,
) -> CycleResult:
    """Execute an email check cycle.

    Uses an LLM tool-use loop with email tools to triage the inbox.
    This runs IN ADDITION to the normal task cycle (unlike reflection).
    """
    result = CycleResult(action="check_email", success=True)

    if not config.email.enabled:
        log.info("Email not enabled, skipping check")
        result.summary = "Email not enabled."
        return result

    # Check that email tools are registered
    if not registry.has("list_emails"):
        log.warning("Email tools not registered, skipping check")
        result.summary = "Email tools not available."
        result.success = False
        return result

    # Build goals context for the LLM
    goals_context_parts: list[str] = []
    for g in ctx.goals:
        goals_context_parts.append(f"- [{g.status}] {g.title}")
    goals_context = "\n".join(goals_context_parts) if goals_context_parts else "(no active goals)"

    system_prompt = _EMAIL_SYSTEM_PROMPT.format(
        email_address=config.email.address,
        goals_context=goals_context,
    )

    # Get the last email check time for context
    last_check = db.get_last_email_check_time()
    user_content = "Check the inbox for new messages."
    if last_check:
        user_content += f"\n\nLast email check was at: {last_check}. Focus on messages received since then."
    else:
        user_content += "\n\nThis is the first email check. Review the most recent messages."

    messages: list[Message] = [
        Message(role="system", content=system_prompt),
        Message(role="user", content=user_content),
    ]

    # Only include email-related tools + database tools for creating tasks
    tool_schemas = registry.get_schemas()

    # ── Tool-use loop ──
    max_tool_calls = 15  # Email checks should be quick
    tool_call_count = 0
    new_messages_found = 0
    actions_taken: list[str] = []
    emails_sent: list[str] = []

    while True:
        response = llm.chat(messages, tools=tool_schemas, model_tier=3)

        if not response.tool_calls:
            result.summary = response.content or "Email check completed."
            break

        if tool_call_count + len(response.tool_calls) > max_tool_calls:
            log.warning("Email check approaching max tool calls, stopping")
            result.summary = response.content or "Email check stopped (max tool calls)."
            break

        # Add assistant message to history
        messages.append(
            Message(
                role="assistant",
                content=response.content,
                tool_calls=response.tool_calls,
            )
        )

        for tc in response.tool_calls:
            tool_call_count += 1
            log.info("Email check tool call %d: %s", tool_call_count, tc.name)

            tool_result = registry.execute(tc)

            # Track what happened
            if tc.name == "list_emails" and tool_result.success and tool_result.data:
                new_messages_found = len(tool_result.data)
            if tc.name == "read_email" and tool_result.success:
                actions_taken.append(f"Read message: {tc.arguments.get('message_id', '?')[:20]}")
            if tc.name == "send_email" and tool_result.success:
                to = tc.arguments.get("to", [])
                subject = tc.arguments.get("subject", "reply")
                emails_sent.append(f"Sent to {to}: {subject}")

            messages.append(
                Message(
                    role="tool",
                    content=tool_result.to_content(),
                    tool_call_id=tc.id,
                    name=tc.name,
                )
            )

        if response.stop_reason == "end_turn":
            result.summary = response.content or "Email check completed."
            break

    # ── Log the email check ──
    try:
        db.insert_execution_log(
            action="check_email",
            summary=f"Email check: {result.summary[:200]}",
            details={
                "new_messages": new_messages_found,
                "actioned": actions_taken,
                "sent": emails_sent,
            },
        )
        log.info("Email check logged: %d messages, %d actions, %d sent",
                 new_messages_found, len(actions_taken), len(emails_sent))
    except Exception as exc:
        log.error("Failed to log email check: %s", exc)

    return result
