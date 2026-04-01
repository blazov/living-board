"""Database tools -- SQL execution and higher-level Supabase helpers."""

from __future__ import annotations

import json
from typing import Any

from ..db import SupabaseClient
from .base import Tool, ToolResult


class ExecuteSqlTool(Tool):
    """Execute a raw SQL-style query via the Supabase PostgREST API.

    This tool translates a simplified query into the appropriate
    SupabaseClient method call.  For full SQL, the LLM should formulate
    the PostgREST path directly.
    """

    name = "execute_sql"
    description = (
        "Execute a query against the Supabase database. "
        "Provide a PostgREST-style path (e.g. 'goals?select=*&status=eq.pending') "
        "and an optional method (GET, POST, PATCH, DELETE) with an optional JSON body. "
        "Returns the JSON response."
    )
    parameters: dict[str, Any] = {
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": (
                    "PostgREST-style path, e.g. "
                    "'goals?select=*&status=eq.pending&order=priority.asc'"
                ),
            },
            "method": {
                "type": "string",
                "enum": ["GET", "POST", "PATCH", "DELETE"],
                "description": "HTTP method. Defaults to GET.",
            },
            "body": {
                "type": ["object", "array", "null"],
                "description": "JSON body for POST/PATCH requests.",
            },
        },
        "required": ["path"],
        "additionalProperties": False,
    }

    def __init__(self, db: SupabaseClient) -> None:
        self._db = db

    def execute(
        self,
        path: str,
        method: str = "GET",
        body: Any = None,
    ) -> ToolResult:
        try:
            result = self._db._request(path, method=method, data=body)
            output = json.dumps(result, indent=2, default=str) if result is not None else "OK (no content)"
            return ToolResult(success=True, output=output, data=result)
        except Exception as exc:
            return ToolResult(success=False, output="", error=str(exc))


class UpdateTaskTool(Tool):
    """Update a task's fields in Supabase."""

    name = "update_task"
    description = (
        "Update fields on a task. Commonly used to set status to 'done' or 'blocked', "
        "record result text, or increment attempts."
    )
    parameters: dict[str, Any] = {
        "type": "object",
        "properties": {
            "task_id": {
                "type": "string",
                "description": "UUID of the task to update.",
            },
            "status": {
                "type": "string",
                "enum": ["pending", "in_progress", "done", "blocked"],
                "description": "New status for the task.",
            },
            "result": {
                "type": "string",
                "description": "Summary of what was accomplished or why it's blocked.",
            },
            "blocked_reason": {
                "type": "string",
                "description": "Reason the task is blocked (if setting status to blocked).",
            },
            "increment_attempts": {
                "type": "boolean",
                "description": "If true, increment the attempts counter by 1.",
            },
        },
        "required": ["task_id"],
        "additionalProperties": False,
    }

    def __init__(self, db: SupabaseClient) -> None:
        self._db = db

    def execute(
        self,
        task_id: str,
        status: str | None = None,
        result: str | None = None,
        blocked_reason: str | None = None,
        increment_attempts: bool = False,
    ) -> ToolResult:
        fields: dict[str, Any] = {}
        if status is not None:
            fields["status"] = status
            if status == "done":
                import time
                fields["completed_at"] = time.strftime(
                    "%Y-%m-%dT%H:%M:%SZ", time.gmtime()
                )
        if result is not None:
            fields["result"] = result
        if blocked_reason is not None:
            fields["blocked_reason"] = blocked_reason

        if not fields and not increment_attempts:
            return ToolResult(
                success=False, output="", error="No fields to update."
            )

        try:
            if increment_attempts:
                # Read current attempts, then patch with incremented value
                rows = self._db._request(
                    f"tasks?select=attempts&id=eq.{task_id}"
                )
                current = rows[0]["attempts"] if rows else 0
                fields["attempts"] = current + 1

            self._db.update_task(task_id, **fields)
            return ToolResult(
                success=True,
                output=f"Task {task_id} updated: {json.dumps(fields, default=str)}",
            )
        except Exception as exc:
            return ToolResult(success=False, output="", error=str(exc))


class StoreLearningTool(Tool):
    """Store a learning in the Supabase learnings table."""

    name = "store_learning"
    description = (
        "Record a learning/insight in the database. "
        "Learnings are displayed on the dashboard and used to inform future cycles."
    )
    parameters: dict[str, Any] = {
        "type": "object",
        "properties": {
            "content": {
                "type": "string",
                "description": "The learning content -- a concrete, specific insight.",
            },
            "category": {
                "type": "string",
                "enum": [
                    "domain_knowledge",
                    "strategy",
                    "operational",
                    "meta",
                ],
                "description": "Category of the learning. Defaults to domain_knowledge.",
            },
            "confidence": {
                "type": "number",
                "minimum": 0.0,
                "maximum": 1.0,
                "description": "Confidence score from 0.0 to 1.0. Defaults to 0.8.",
            },
            "goal_id": {
                "type": ["string", "null"],
                "description": "UUID of the related goal, or null for global learnings.",
            },
            "task_id": {
                "type": ["string", "null"],
                "description": "UUID of the related task, if applicable.",
            },
        },
        "required": ["content"],
        "additionalProperties": False,
    }

    def __init__(self, db: SupabaseClient) -> None:
        self._db = db

    def execute(
        self,
        content: str,
        category: str = "domain_knowledge",
        confidence: float = 0.8,
        goal_id: str | None = None,
        task_id: str | None = None,
    ) -> ToolResult:
        try:
            self._db.insert_learning(
                content=content,
                category=category,
                confidence=confidence,
                goal_id=goal_id,
                task_id=task_id,
            )
            return ToolResult(
                success=True,
                output=f"Learning stored ({category}, confidence={confidence}): {content[:120]}",
            )
        except Exception as exc:
            return ToolResult(success=False, output="", error=str(exc))


class CreateTasksTool(Tool):
    """Batch-create tasks for a goal."""

    name = "create_tasks"
    description = (
        "Create one or more tasks for a goal. Used during goal decomposition. "
        "Each task needs a title, description, and sort_order."
    )
    parameters: dict[str, Any] = {
        "type": "object",
        "properties": {
            "goal_id": {
                "type": "string",
                "description": "UUID of the goal these tasks belong to.",
            },
            "tasks": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "title": {
                            "type": "string",
                            "description": "Short title for the task.",
                        },
                        "description": {
                            "type": "string",
                            "description": "Detailed description of what to do.",
                        },
                        "sort_order": {
                            "type": "integer",
                            "description": "Order within the goal (10, 20, 30...).",
                        },
                        "metadata": {
                            "type": "object",
                            "description": "Optional metadata (e.g. model preference).",
                        },
                    },
                    "required": ["title", "description", "sort_order"],
                    "additionalProperties": False,
                },
                "description": "List of tasks to create.",
            },
        },
        "required": ["goal_id", "tasks"],
        "additionalProperties": False,
    }

    def __init__(self, db: SupabaseClient) -> None:
        self._db = db

    def execute(
        self,
        goal_id: str,
        tasks: list[dict[str, Any]],
    ) -> ToolResult:
        rows = []
        for t in tasks:
            row: dict[str, Any] = {
                "goal_id": goal_id,
                "title": t["title"],
                "description": t.get("description", ""),
                "sort_order": t.get("sort_order", 10),
            }
            if "metadata" in t:
                row["metadata"] = t["metadata"]
            else:
                row["metadata"] = {"created_by": "agent"}
            rows.append(row)

        try:
            self._db.insert_tasks(rows)
            titles = [t["title"] for t in tasks]
            return ToolResult(
                success=True,
                output=f"Created {len(rows)} tasks for goal {goal_id}: {titles}",
                data=rows,
            )
        except Exception as exc:
            return ToolResult(success=False, output="", error=str(exc))


def create_database_tools(db: SupabaseClient) -> list[Tool]:
    """Create all database-related tools from a SupabaseClient."""
    return [
        ExecuteSqlTool(db),
        UpdateTaskTool(db),
        StoreLearningTool(db),
        CreateTasksTool(db),
    ]
