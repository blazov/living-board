#!/usr/bin/env python3
"""
Daily Activity Digest Generator for Living Board.

Queries Supabase for a given day's activity and renders a markdown digest.
Usage: python3 generate-digest.py [YYYY-MM-DD]
       Defaults to today (UTC) if no date provided.

Requires: SUPABASE_URL and SUPABASE_KEY environment variables,
          or uses defaults for the Living Board project.
"""

import sys
import os
import json
import requests
from datetime import datetime, timezone, timedelta

# Supabase config
SUPABASE_URL = os.environ.get("SUPABASE_URL", "https://ieekjkeayiclprdekxla.supabase.co")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImllZWtqa2VheWljbHByZGVreGxhIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzQ4MzAxODQsImV4cCI6MjA5MDQwNjE4NH0.dAcUXetSteRXcUytAnkd3CEp_z6fg2nqhC3lrWoNPl0")

HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=representation"
}

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs")


def query_supabase(endpoint, params=None):
    """Query Supabase REST API."""
    url = f"{SUPABASE_URL}/rest/v1/{endpoint}"
    resp = requests.get(url, headers=HEADERS, params=params or {})
    resp.raise_for_status()
    return resp.json()


def rpc(function_name, body=None):
    """Call a Supabase RPC function."""
    url = f"{SUPABASE_URL}/rest/v1/rpc/{function_name}"
    resp = requests.post(url, headers=HEADERS, json=body or {})
    resp.raise_for_status()
    return resp.json()


def get_execution_log(date_str):
    """Get all execution log entries for a given date (UTC)."""
    start = f"{date_str}T00:00:00+00:00"
    end_date = datetime.fromisoformat(start) + timedelta(days=1)
    end = end_date.isoformat()
    return query_supabase("execution_log", {
        "select": "id,goal_id,task_id,action,summary,details,created_at",
        "created_at": f"gte.{start}",
        "order": "created_at.asc",
        # Also filter by end date
    })


def get_goals():
    """Get all goals."""
    return query_supabase("goals", {
        "select": "id,title,status,priority",
        "order": "priority.asc"
    })


def get_tasks():
    """Get all tasks."""
    return query_supabase("tasks", {
        "select": "id,goal_id,title,status,sort_order,result,completed_at",
        "order": "sort_order.asc"
    })


def get_learnings(date_str):
    """Get learnings created on a given date."""
    start = f"{date_str}T00:00:00+00:00"
    return query_supabase("learnings", {
        "select": "id,goal_id,category,content,confidence,created_at",
        "created_at": f"gte.{start}",
        "order": "confidence.desc"
    })


def filter_by_date(entries, date_str):
    """Filter entries to only those matching the target date (UTC)."""
    return [e for e in entries if e.get("created_at", "").startswith(date_str)]


def build_digest(date_str):
    """Build the full digest markdown for a given date."""
    # Fetch data
    log_entries = filter_by_date(get_execution_log(date_str), date_str)
    goals = get_goals()
    tasks = get_tasks()
    learnings = filter_by_date(get_learnings(date_str), date_str)

    if not log_entries:
        return None  # No activity this day

    goals_map = {g["id"]: g for g in goals}
    tasks_map = {t["id"]: t for t in tasks}

    # Count metrics
    exec_count = len([e for e in log_entries if e["action"] == "execute"])
    reflect_count = len([e for e in log_entries if e["action"] == "reflect"])
    total_cycles = exec_count + reflect_count

    # Tasks completed today
    tasks_completed = [t for t in tasks if t.get("completed_at", "")
                       and t["completed_at"].startswith(date_str)]

    # Goals touched
    goal_ids_touched = set(e.get("goal_id") for e in log_entries if e.get("goal_id"))

    # Build markdown
    lines = []
    lines.append(f"# Living Board Daily Digest: {date_str}")
    lines.append("")

    # Summary
    lines.append("## Summary")
    lines.append("")
    lines.append(f"- **Cycles executed**: {total_cycles} ({exec_count} execution, {reflect_count} reflection)")
    lines.append(f"- **Tasks completed**: {len(tasks_completed)}")
    lines.append(f"- **Goals touched**: {len(goal_ids_touched)}")
    lines.append(f"- **Learnings extracted**: {len(learnings)}")
    lines.append("")

    # Activity Log grouped by goal
    lines.append("## Activity Log")
    lines.append("")

    # Group log entries by goal
    by_goal = {}
    no_goal = []
    for entry in log_entries:
        gid = entry.get("goal_id")
        if gid:
            by_goal.setdefault(gid, []).append(entry)
        else:
            no_goal.append(entry)

    for gid, entries in by_goal.items():
        goal = goals_map.get(gid, {})
        goal_title = goal.get("title", "Unknown Goal")
        goal_status = goal.get("status", "?")
        lines.append(f"### {goal_title} [{goal_status}]")
        lines.append("")
        for entry in entries:
            ts = entry["created_at"][:16].replace("T", " ")
            action = entry["action"]
            summary = entry.get("summary", "")
            lines.append(f"- **{ts} UTC** [{action}] {summary}")
        lines.append("")

    if no_goal:
        lines.append("### General / No Goal")
        lines.append("")
        for entry in no_goal:
            ts = entry["created_at"][:16].replace("T", " ")
            action = entry["action"]
            summary = entry.get("summary", "")
            lines.append(f"- **{ts} UTC** [{action}] {summary}")
        lines.append("")

    # Learnings
    if learnings:
        lines.append("## Learnings")
        lines.append("")
        by_category = {}
        for l in learnings:
            cat = l.get("category", "uncategorized")
            by_category.setdefault(cat, []).append(l)

        for cat, items in sorted(by_category.items()):
            lines.append(f"### {cat.replace('_', ' ').title()}")
            lines.append("")
            for item in items:
                conf = item.get("confidence", "?")
                lines.append(f"- [{conf}] {item['content']}")
            lines.append("")

    # Board State Snapshot
    lines.append("## Board State")
    lines.append("")
    status_counts = {}
    for g in goals:
        s = g["status"]
        status_counts[s] = status_counts.get(s, 0) + 1
    for status, count in sorted(status_counts.items()):
        lines.append(f"- **{status}**: {count} goals")
    lines.append("")

    # Active goals detail
    active = [g for g in goals if g["status"] in ("in_progress", "pending")]
    if active:
        lines.append("### Active Goals")
        lines.append("")
        for g in active:
            goal_tasks = [t for t in tasks if t.get("goal_id") == g["id"]]
            done_count = len([t for t in goal_tasks if t["status"] == "done"])
            total_count = len(goal_tasks)
            lines.append(f"- **[P{g['priority']}]** {g['title']} ({g['status']}) — {done_count}/{total_count} tasks done")
        lines.append("")

    # Footer
    lines.append("---")
    lines.append(f"*Generated automatically by Living Board agent on {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}*")
    lines.append("")

    return "\n".join(lines)


def main():
    if len(sys.argv) > 1:
        date_str = sys.argv[1]
    else:
        date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    print(f"Generating digest for {date_str}...")

    digest = build_digest(date_str)

    if digest is None:
        print(f"No activity found for {date_str}. Skipping.")
        sys.exit(0)

    # Ensure output directory exists
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    output_path = os.path.join(OUTPUT_DIR, f"digest-{date_str}.md")
    with open(output_path, "w") as f:
        f.write(digest)

    print(f"Digest written to {output_path}")
    print(f"  Lines: {len(digest.splitlines())}")
    print(f"  Size: {len(digest)} bytes")


if __name__ == "__main__":
    main()
