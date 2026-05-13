#!/usr/bin/env python3
"""Convert JSON dataset exports to CSV and compute summary statistics."""

import csv
import json
import os
from collections import Counter
from datetime import datetime, timezone

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")

TABLES = ["goals", "tasks", "execution_log", "learnings", "snapshots"]


def load_json(name):
    with open(os.path.join(DATA_DIR, f"{name}.json")) as f:
        return json.load(f)


def write_csv(name, rows):
    if not rows:
        return
    path = os.path.join(DATA_DIR, f"{name}.csv")
    keys = list(rows[0].keys())
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=keys)
        w.writeheader()
        for row in rows:
            flat = {}
            for k, v in row.items():
                if isinstance(v, (dict, list)):
                    flat[k] = json.dumps(v)
                else:
                    flat[k] = v
            w.writerow(flat)
    print(f"  {path} ({len(rows)} rows)")


def parse_ts(ts_str):
    if not ts_str:
        return None
    ts_str = ts_str.strip()
    # Normalize short timezone offsets like +00 to +00:00
    if len(ts_str) >= 3 and ts_str[-3] in ('+', '-') and ts_str[-2:].isdigit():
        ts_str += ":00"
    for fmt in [
        "%Y-%m-%dT%H:%M:%S.%f%z",
        "%Y-%m-%dT%H:%M:%S%z",
        "%Y-%m-%d %H:%M:%S.%f%z",
        "%Y-%m-%d %H:%M:%S%z",
        "%Y-%m-%dT%H:%M:%S.%f",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d %H:%M:%S.%f",
        "%Y-%m-%d %H:%M:%S",
    ]:
        try:
            return datetime.strptime(ts_str, fmt)
        except ValueError:
            continue
    return None


def compute_stats(goals, tasks, log, learnings, snapshots):
    stats = {}

    total_rows = len(goals) + len(tasks) + len(log) + len(learnings) + len(snapshots)
    all_timestamps = []
    for t in ["goals", "tasks", "execution_log", "learnings", "snapshots"]:
        data = {"goals": goals, "tasks": tasks, "execution_log": log,
                "learnings": learnings, "snapshots": snapshots}[t]
        for r in data:
            ts = parse_ts(r.get("created_at", ""))
            if ts:
                all_timestamps.append(ts)
    all_timestamps.sort()
    stats["dataset_overview"] = {
        "total_rows": total_rows,
        "tables": {t: len({"goals": goals, "tasks": tasks, "execution_log": log,
                           "learnings": learnings, "snapshots": snapshots}[t]) for t in TABLES},
        "date_range_start": all_timestamps[0].isoformat() if all_timestamps else None,
        "date_range_end": all_timestamps[-1].isoformat() if all_timestamps else None,
        "span_days": (all_timestamps[-1] - all_timestamps[0]).days if len(all_timestamps) >= 2 else 0,
    }

    goal_statuses = Counter(g["status"] for g in goals)
    goal_creators = Counter()
    for g in goals:
        md = g.get("metadata") or {}
        if isinstance(md, str):
            try:
                md = json.loads(md)
            except (json.JSONDecodeError, TypeError):
                md = {}
        goal_creators[md.get("created_by", "unknown")] += 1

    stats["goals"] = {
        "total": len(goals),
        "by_status": dict(goal_statuses),
        "by_creator": dict(goal_creators),
        "completion_rate": round(goal_statuses.get("done", 0) / max(len(goals), 1), 3),
    }

    task_statuses = Counter(t["status"] for t in tasks)
    completed_tasks = [t for t in tasks if t["status"] == "done"]
    blocked_tasks = [t for t in tasks if t["status"] == "blocked"]
    attempt_counts = [t.get("attempts", 0) or 0 for t in tasks]

    stats["tasks"] = {
        "total": len(tasks),
        "by_status": dict(task_statuses),
        "completion_rate": round(task_statuses.get("done", 0) / max(len(tasks), 1), 3),
        "blocked_rate": round(len(blocked_tasks) / max(len(tasks), 1), 3),
        "avg_attempts": round(sum(attempt_counts) / max(len(attempt_counts), 1), 2),
        "max_attempts_seen": max(attempt_counts) if attempt_counts else 0,
        "single_attempt_success_rate": round(
            sum(1 for t in completed_tasks if (t.get("attempts", 0) or 0) <= 1) / max(len(completed_tasks), 1), 3
        ),
    }

    action_counts = Counter(e["action"] for e in log)
    exec_timestamps = []
    for e in log:
        ts = parse_ts(e.get("created_at", ""))
        if ts:
            exec_timestamps.append(ts)
    exec_timestamps.sort()

    cycles_by_date = Counter()
    for ts in exec_timestamps:
        cycles_by_date[ts.strftime("%Y-%m-%d")] += 1

    daily_counts = list(cycles_by_date.values()) if cycles_by_date else [0]
    stats["execution"] = {
        "total_log_entries": len(log),
        "by_action": dict(action_counts),
        "cycles_per_day_avg": round(sum(daily_counts) / max(len(daily_counts), 1), 1),
        "cycles_per_day_max": max(daily_counts),
        "cycles_per_day_min": min(daily_counts),
        "active_days": len(cycles_by_date),
        "daily_breakdown": dict(sorted(cycles_by_date.items())),
    }

    if len(exec_timestamps) >= 2:
        gaps_hours = []
        for i in range(1, len(exec_timestamps)):
            diff = exec_timestamps[i] - exec_timestamps[i - 1]
            gaps_hours.append(diff.total_seconds() / 3600)
        stats["execution"]["inter_cycle_gap_hours"] = {
            "median": round(sorted(gaps_hours)[len(gaps_hours) // 2], 2),
            "mean": round(sum(gaps_hours) / len(gaps_hours), 2),
            "min": round(min(gaps_hours), 2),
            "max": round(max(gaps_hours), 2),
        }

    hour_dist = Counter()
    for ts in exec_timestamps:
        hour_dist[ts.hour] += 1
    stats["execution"]["hour_of_day_distribution"] = {
        str(h): hour_dist.get(h, 0) for h in range(24)
    }

    learning_cats = Counter(l["category"] for l in learnings)
    confidences = [l.get("confidence", 0) or 0 for l in learnings]
    goal_specific = sum(1 for l in learnings if l.get("goal_id"))
    global_learnings = sum(1 for l in learnings if not l.get("goal_id"))

    stats["learnings"] = {
        "total": len(learnings),
        "by_category": dict(learning_cats),
        "confidence_avg": round(sum(confidences) / max(len(confidences), 1), 3),
        "confidence_max": max(confidences) if confidences else 0,
        "confidence_min": min(confidences) if confidences else 0,
        "goal_specific": goal_specific,
        "global": global_learnings,
    }

    cycle_numbers = [s.get("cycle_count", 0) or 0 for s in snapshots]
    stats["snapshots"] = {
        "total": len(snapshots),
        "cycle_count_range": [min(cycle_numbers) if cycle_numbers else 0,
                              max(cycle_numbers) if cycle_numbers else 0],
    }

    goals_with_tasks = set(t["goal_id"] for t in tasks if t.get("goal_id"))
    goals_with_learnings = set(l["goal_id"] for l in learnings if l.get("goal_id"))
    tasks_per_goal = Counter(t["goal_id"] for t in tasks if t.get("goal_id"))
    learnings_per_goal = Counter(l["goal_id"] for l in learnings if l.get("goal_id"))

    stats["cross_table"] = {
        "goals_with_tasks": len(goals_with_tasks),
        "goals_without_tasks": len(goals) - len(goals_with_tasks),
        "goals_with_learnings": len(goals_with_learnings),
        "avg_tasks_per_goal": round(sum(tasks_per_goal.values()) / max(len(tasks_per_goal), 1), 1),
        "avg_learnings_per_goal": round(sum(learnings_per_goal.values()) / max(len(learnings_per_goal), 1), 1),
    }

    return stats


def main():
    print("Loading JSON datasets...")
    data = {t: load_json(t) for t in TABLES}

    print("\nConverting to CSV:")
    for t in TABLES:
        write_csv(t, data[t])

    print("\nComputing summary statistics...")
    stats = compute_stats(
        data["goals"], data["tasks"], data["execution_log"],
        data["learnings"], data["snapshots"]
    )

    stats_path = os.path.join(DATA_DIR, "summary-statistics.json")
    with open(stats_path, "w") as f:
        json.dump(stats, f, indent=2)
    print(f"\nSaved: {stats_path}")

    print("\n=== Key Metrics ===")
    overview = stats["dataset_overview"]
    print(f"Total rows: {overview['total_rows']}")
    print(f"Date range: {overview['date_range_start'][:10]} to {overview['date_range_end'][:10]} ({overview['span_days']} days)")
    print(f"Goals: {stats['goals']['total']} ({stats['goals']['completion_rate']*100:.1f}% completion rate)")
    print(f"Tasks: {stats['tasks']['total']} ({stats['tasks']['completion_rate']*100:.1f}% done, {stats['tasks']['blocked_rate']*100:.1f}% blocked)")
    print(f"Execution log: {stats['execution']['total_log_entries']} entries")
    print(f"Cycles/day: avg {stats['execution']['cycles_per_day_avg']}, max {stats['execution']['cycles_per_day_max']}")
    print(f"Learnings: {stats['learnings']['total']} ({stats['learnings']['confidence_avg']:.2f} avg confidence)")
    if "inter_cycle_gap_hours" in stats["execution"]:
        gap = stats["execution"]["inter_cycle_gap_hours"]
        print(f"Inter-cycle gap: median {gap['median']}h, mean {gap['mean']}h")


if __name__ == "__main__":
    main()
