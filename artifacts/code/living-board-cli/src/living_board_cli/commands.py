"""CLI command implementations.

Each command is a pure function: (client, args) -> None. The CLI module owns
argparse wiring; commands own formatting and the exact queries.
"""

from __future__ import annotations

import argparse
import json
from typing import Any

from .client import Client, LivingBoardError
from .render import render_kv, render_table, short_id, short_ts


# ── helpers ───────────────────────────────────────────────────────


def _status_filter(statuses: list[str] | None) -> dict[str, str]:
    if not statuses:
        return {}
    return {"status": f"in.({','.join(statuses)})"}


def _priority_label(value: Any) -> str:
    try:
        n = int(value)
    except (TypeError, ValueError):
        return "?"
    return f"P{n}"


def _print(text: str) -> None:
    # Indirection so tests can capture output.
    print(text)


# ── commands ──────────────────────────────────────────────────────


def cmd_goals(client: Client, args: argparse.Namespace) -> None:
    statuses = args.status or ["in_progress", "pending"]
    filters = _status_filter(statuses)
    rows = client.query(
        "goals",
        select="id,title,status,priority,created_by,created_at",
        filters=filters,
        order="priority.asc,created_at.asc",
        limit=args.limit,
    )
    if args.json:
        _print(json.dumps(rows, indent=2, default=str))
        return
    headers = ["ID", "PRIO", "STATUS", "BY", "TITLE", "CREATED"]
    table_rows = [
        [
            short_id(r.get("id")),
            _priority_label(r.get("priority")),
            r.get("status", ""),
            r.get("created_by", ""),
            r.get("title", ""),
            short_ts(r.get("created_at")),
        ]
        for r in rows
    ]
    _print(render_table(headers, table_rows))
    _print(f"\n{len(rows)} goal(s) — statuses: {', '.join(statuses)}")


def cmd_tasks(client: Client, args: argparse.Namespace) -> None:
    filters: dict[str, str] = {}
    if args.goal:
        filters["goal_id"] = f"eq.{args.goal}"
    statuses = args.status or ["in_progress", "pending"]
    filters.update(_status_filter(statuses))
    rows = client.query(
        "tasks",
        select="id,goal_id,title,status,sort_order,attempts,max_attempts,created_at",
        filters=filters,
        order="sort_order.asc,created_at.asc",
        limit=args.limit,
    )
    if args.json:
        _print(json.dumps(rows, indent=2, default=str))
        return
    headers = ["ID", "GOAL", "#", "STATUS", "ATT", "TITLE", "CREATED"]
    table_rows = [
        [
            short_id(r.get("id")),
            short_id(r.get("goal_id")),
            r.get("sort_order", ""),
            r.get("status", ""),
            f"{r.get('attempts', 0)}/{r.get('max_attempts', 0)}",
            r.get("title", ""),
            short_ts(r.get("created_at")),
        ]
        for r in rows
    ]
    _print(render_table(headers, table_rows))
    _print(f"\n{len(rows)} task(s)")


def cmd_log(client: Client, args: argparse.Namespace) -> None:
    rows = client.query(
        "execution_log",
        select="id,action,summary,goal_id,task_id,created_at",
        order="created_at.desc",
        limit=args.limit,
    )
    if args.json:
        _print(json.dumps(rows, indent=2, default=str))
        return
    headers = ["WHEN", "ACTION", "GOAL", "SUMMARY"]
    table_rows = [
        [
            short_ts(r.get("created_at")),
            r.get("action", ""),
            short_id(r.get("goal_id")),
            r.get("summary", ""),
        ]
        for r in rows
    ]
    _print(render_table(headers, table_rows))
    _print(f"\n{len(rows)} log entries")


def cmd_learnings(client: Client, args: argparse.Namespace) -> None:
    filters: dict[str, str] = {}
    if args.goal:
        filters["goal_id"] = f"eq.{args.goal}"
    if args.category:
        filters["category"] = f"eq.{args.category}"
    rows = client.query(
        "learnings",
        select="id,category,content,confidence,goal_id,created_at",
        filters=filters,
        order="confidence.desc,created_at.desc",
        limit=args.limit,
    )
    if args.json:
        _print(json.dumps(rows, indent=2, default=str))
        return
    headers = ["CONF", "CATEGORY", "GOAL", "CONTENT", "CREATED"]
    table_rows = [
        [
            f"{float(r.get('confidence') or 0):.2f}",
            r.get("category", ""),
            short_id(r.get("goal_id")),
            r.get("content", ""),
            short_ts(r.get("created_at")),
        ]
        for r in rows
    ]
    _print(render_table(headers, table_rows))
    _print(f"\n{len(rows)} learning(s)")


def cmd_snapshot(client: Client, args: argparse.Namespace) -> None:
    rows = client.query(
        "snapshots",
        select="content,current_focus,cycle_count,created_at",
        order="created_at.desc",
        limit=1,
    )
    if not rows:
        _print("(no snapshots yet)")
        return
    row = rows[0]
    if args.json:
        _print(json.dumps(row, indent=2, default=str))
        return
    _print(
        render_kv(
            [
                ("cycle", row.get("cycle_count")),
                ("created", short_ts(row.get("created_at"))),
                ("focus", row.get("current_focus") or "(none)"),
                ("content", row.get("content") or "(empty)"),
            ]
        )
    )


def cmd_stats(client: Client, args: argparse.Namespace) -> None:
    goals = client.query("goals", select="status")
    tasks = client.query("tasks", select="status")
    logs = client.query("execution_log", select="action", order="created_at.desc", limit=500)
    learnings = client.query("learnings", select="id")

    def counts(rows: list[dict[str, Any]], key: str) -> dict[str, int]:
        out: dict[str, int] = {}
        for r in rows:
            out[r.get(key) or "?"] = out.get(r.get(key) or "?", 0) + 1
        return out

    goal_counts = counts(goals, "status")
    task_counts = counts(tasks, "status")
    log_counts = counts(logs, "action")

    def fmt_counts(d: dict[str, int]) -> str:
        return ", ".join(f"{k}={v}" for k, v in sorted(d.items())) or "(none)"

    if args.json:
        _print(
            json.dumps(
                {
                    "goals": goal_counts,
                    "tasks": task_counts,
                    "recent_actions": log_counts,
                    "learnings_total": len(learnings),
                },
                indent=2,
            )
        )
        return

    _print(
        render_kv(
            [
                ("goals", fmt_counts(goal_counts)),
                ("tasks", fmt_counts(task_counts)),
                ("recent actions (last 500)", fmt_counts(log_counts)),
                ("learnings (total)", len(learnings)),
            ]
        )
    )


def cmd_comment(client: Client, args: argparse.Namespace) -> None:
    try:
        client.insert(
            "goal_comments",
            {
                "goal_id": args.goal,
                "author": "user",
                "comment_type": args.type,
                "content": args.content,
            },
        )
    except LivingBoardError as exc:
        _print(f"error: {exc}")
        raise SystemExit(1)
    _print(f"comment added to goal {short_id(args.goal)}: [{args.type}] {args.content}")


def cmd_check(client: Client, args: argparse.Namespace) -> None:
    try:
        client.check()
    except LivingBoardError as exc:
        _print(f"NOT OK: {exc}")
        raise SystemExit(1)
    _print("OK — Supabase reachable and goals table queryable")
