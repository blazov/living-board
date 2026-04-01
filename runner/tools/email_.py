"""Email tools -- send/receive via AgentMail SDK."""

from __future__ import annotations

import json
import logging
import os
from typing import Any

from ..config import EmailConfig
from .base import Tool, ToolResult

log = logging.getLogger(__name__)


def _get_client(config: EmailConfig) -> Any:
    """Lazily import and instantiate the AgentMail client."""
    # Set the API key in the environment where the SDK expects it
    os.environ["AGENTMAIL_API_KEY"] = config.api_key
    from agentmail import AgentMail  # type: ignore[import-untyped]
    return AgentMail()


class SendEmailTool(Tool):
    """Send an email via AgentMail."""

    name = "send_email"
    description = (
        "Send an email from the agent's AgentMail address. "
        "Can be used for outreach, follow-ups, and responses."
    )
    parameters: dict[str, Any] = {
        "type": "object",
        "properties": {
            "to": {
                "type": "array",
                "items": {"type": "string"},
                "description": "List of recipient email addresses.",
            },
            "subject": {
                "type": "string",
                "description": "Email subject line.",
            },
            "text": {
                "type": "string",
                "description": "Plain text email body.",
            },
            "reply_to_message_id": {
                "type": ["string", "null"],
                "description": (
                    "If this is a reply, the message_id of the message being replied to. "
                    "If provided, 'to' and 'subject' are optional (derived from original)."
                ),
            },
        },
        "required": ["text"],
        "additionalProperties": False,
    }

    def __init__(self, config: EmailConfig) -> None:
        self._config = config

    def execute(
        self,
        text: str,
        to: list[str] | None = None,
        subject: str | None = None,
        reply_to_message_id: str | None = None,
    ) -> ToolResult:
        try:
            client = _get_client(self._config)
            address = self._config.address

            if reply_to_message_id:
                # Reply to an existing message
                client.inboxes.messages.reply(
                    address,
                    reply_to_message_id,
                    text=text,
                )
                return ToolResult(
                    success=True,
                    output=f"Reply sent to message {reply_to_message_id}",
                )
            else:
                if not to:
                    return ToolResult(
                        success=False,
                        output="",
                        error="'to' is required when not replying to an existing message.",
                    )
                if not subject:
                    return ToolResult(
                        success=False,
                        output="",
                        error="'subject' is required when not replying to an existing message.",
                    )

                client.inboxes.messages.send(
                    address,
                    to=to,
                    subject=subject,
                    text=text,
                )
                return ToolResult(
                    success=True,
                    output=f"Email sent to {', '.join(to)} with subject: {subject}",
                )

        except ImportError:
            return ToolResult(
                success=False,
                output="",
                error="agentmail package not installed. Install with: pip install agentmail",
            )
        except Exception as exc:
            return ToolResult(success=False, output="", error=str(exc))


class ListEmailsTool(Tool):
    """List recent emails in the AgentMail inbox."""

    name = "list_emails"
    description = (
        "List recent emails in the agent's inbox. "
        "Returns message IDs, senders, subjects, and timestamps."
    )
    parameters: dict[str, Any] = {
        "type": "object",
        "properties": {
            "limit": {
                "type": "integer",
                "minimum": 1,
                "maximum": 50,
                "description": "Maximum number of messages to return. Defaults to 20.",
            },
        },
        "required": [],
        "additionalProperties": False,
    }

    def __init__(self, config: EmailConfig) -> None:
        self._config = config

    def execute(self, limit: int = 20) -> ToolResult:
        try:
            client = _get_client(self._config)
            result = client.inboxes.messages.list(
                self._config.address, limit=limit
            )

            messages = []
            for m in result.messages:
                messages.append({
                    "message_id": m.message_id,
                    "from": str(m.from_) if m.from_ else None,
                    "subject": m.subject,
                    "date": str(m.date) if hasattr(m, "date") else None,
                })

            output = json.dumps(messages, indent=2, default=str)
            return ToolResult(success=True, output=output, data=messages)

        except ImportError:
            return ToolResult(
                success=False,
                output="",
                error="agentmail package not installed. Install with: pip install agentmail",
            )
        except Exception as exc:
            return ToolResult(success=False, output="", error=str(exc))


class ReadEmailTool(Tool):
    """Read a specific email message by ID."""

    name = "read_email"
    description = (
        "Read the full contents of a specific email message by its message_id. "
        "Returns the sender, subject, and body text."
    )
    parameters: dict[str, Any] = {
        "type": "object",
        "properties": {
            "message_id": {
                "type": "string",
                "description": "The message_id of the email to read.",
            },
        },
        "required": ["message_id"],
        "additionalProperties": False,
    }

    def __init__(self, config: EmailConfig) -> None:
        self._config = config

    def execute(self, message_id: str) -> ToolResult:
        try:
            client = _get_client(self._config)
            msg = client.inboxes.messages.get(
                self._config.address, message_id
            )

            body = msg.text or msg.extracted_text or msg.html or "(no body)"

            data = {
                "message_id": msg.message_id,
                "from": str(msg.from_) if msg.from_ else None,
                "subject": msg.subject,
                "body": body,
            }

            output = json.dumps(data, indent=2, default=str)
            return ToolResult(success=True, output=output, data=data)

        except ImportError:
            return ToolResult(
                success=False,
                output="",
                error="agentmail package not installed. Install with: pip install agentmail",
            )
        except Exception as exc:
            return ToolResult(success=False, output="", error=str(exc))


def create_email_tools(config: EmailConfig) -> list[Tool]:
    """Create email tools if email is enabled.

    Returns an empty list if email is disabled or not configured.
    """
    if not config.enabled or not config.api_key or not config.address:
        log.info("Email tools not registered (disabled or missing config)")
        return []

    return [
        SendEmailTool(config),
        ListEmailsTool(config),
        ReadEmailTool(config),
    ]
