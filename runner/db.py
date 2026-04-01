"""Supabase REST client — no MCP dependency."""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from typing import Any

from .config import SupabaseConfig
from .models import (
    ExecutionLog, Goal, GoalComment, Learning, Snapshot, Task,
)


class SupabaseClient:
    """Direct HTTP client for Supabase PostgREST API."""

    def __init__(self, config: SupabaseConfig):
        self.url = config.url.rstrip("/")
        self.key = config.anon_key
        self.headers = {
            "apikey": self.key,
            "Authorization": f"Bearer {self.key}",
            "Content-Type": "application/json",
            "Prefer": "return=representation",
        }

    def _request(
        self,
        path: str,
        method: str = "GET",
        data: Any = None,
        extra_headers: dict[str, str] | None = None,
    ) -> Any:
        url = f"{self.url}/rest/v1/{path}"
        body = json.dumps(data).encode() if data is not None else None
        headers = {**self.headers, **(extra_headers or {})}
        req = urllib.request.Request(url, data=body, headers=headers, method=method)
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                text = resp.read().decode()
                return json.loads(text) if text else None
        except urllib.error.HTTPError as e:
            err = e.read().decode() if e.fp else str(e)
            raise RuntimeError(f"Supabase HTTP {e.code}: {err}") from e

    # ── Reads ──

    def get_snapshot(self) -> Snapshot | None:
        rows = self._request(
            "snapshots?select=*&order=created_at.desc&limit=1"
        )
        if rows:
            return Snapshot(**rows[0])
        return None

    def get_active_goals(self) -> list[Goal]:
        rows = self._request(
            "goals?select=*&status=in.in_progress,pending&order=priority.asc,created_at.asc"
        )
        return [Goal(**r) for r in rows]

    def get_tasks_for_goal(self, goal_id: str) -> list[Task]:
        rows = self._request(
            f"tasks?select=*&goal_id=eq.{goal_id}&status=in.pending,in_progress&order=sort_order.asc"
        )
        return [Task(**r) for r in rows]

    def get_recent_logs(self, limit: int = 5) -> list[ExecutionLog]:
        rows = self._request(
            f"execution_log?select=*&order=created_at.desc&limit={limit}"
        )
        return [ExecutionLog(**r) for r in rows]

    def get_learnings(self, goal_id: str | None = None, limit: int = 10) -> list[Learning]:
        if goal_id:
            path = f"learnings?select=*&or=(goal_id.eq.{goal_id},goal_id.is.null)&order=confidence.desc&limit={limit}"
        else:
            path = f"learnings?select=*&order=confidence.desc&limit={limit}"
        rows = self._request(path)
        return [Learning(**r) for r in rows]

    def get_unacknowledged_comments(self) -> list[GoalComment]:
        rows = self._request(
            "goal_comments?select=*,goals(title)&acknowledged_at=is.null&order=created_at.asc"
        )
        comments = []
        for r in rows:
            if "goals" in r and r["goals"]:
                r["goal_title"] = r["goals"].get("title")
            r.pop("goals", None)
            comments.append(GoalComment(**r))
        return comments

    def get_last_reflection_time(self) -> str | None:
        rows = self._request(
            "execution_log?select=created_at&action=eq.reflect&order=created_at.desc&limit=1"
        )
        if rows:
            return rows[0]["created_at"]
        return None

    def get_last_email_check_time(self) -> str | None:
        rows = self._request(
            "execution_log?select=created_at&action=eq.check_email&order=created_at.desc&limit=1"
        )
        if rows:
            return rows[0]["created_at"]
        return None

    # ── Writes ──

    def update_task(self, task_id: str, **fields: Any) -> None:
        self._request(f"tasks?id=eq.{task_id}", method="PATCH", data=fields)

    def update_goal(self, goal_id: str, **fields: Any) -> None:
        self._request(f"goals?id=eq.{goal_id}", method="PATCH", data=fields)

    def insert_execution_log(
        self,
        action: str,
        summary: str,
        goal_id: str | None = None,
        task_id: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        data = {"action": action, "summary": summary}
        if goal_id:
            data["goal_id"] = goal_id
        if task_id:
            data["task_id"] = task_id
        if details:
            data["details"] = json.dumps(details)
        self._request("execution_log", method="POST", data=data)

    def insert_learning(
        self,
        content: str,
        category: str = "domain_knowledge",
        confidence: float = 0.8,
        goal_id: str | None = None,
        task_id: str | None = None,
    ) -> None:
        data = {"content": content, "category": category, "confidence": confidence}
        if goal_id:
            data["goal_id"] = goal_id
        if task_id:
            data["task_id"] = task_id
        self._request("learnings", method="POST", data=data)

    def insert_snapshot(
        self,
        content: str,
        active_goals: str = "[]",
        current_focus: str = "",
        recent_outcomes: str = "[]",
        open_blockers: str = "[]",
        key_learnings: str = "[]",
        cycle_count: int = 0,
    ) -> None:
        self._request("snapshots", method="POST", data={
            "content": content,
            "active_goals": active_goals,
            "current_focus": current_focus,
            "recent_outcomes": recent_outcomes,
            "open_blockers": open_blockers,
            "key_learnings": key_learnings,
            "cycle_count": cycle_count,
        })

    def acknowledge_comment(self, comment_id: str, response: str) -> None:
        self._request(
            f"goal_comments?id=eq.{comment_id}",
            method="PATCH",
            data={"acknowledged_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "agent_response": response},
        )

    def insert_tasks(self, tasks: list[dict[str, Any]]) -> None:
        self._request("tasks", method="POST", data=tasks)

    def check_connection(self) -> bool:
        """Test that the Supabase connection works."""
        try:
            self._request("goals?select=id&limit=1")
            return True
        except Exception:
            return False
