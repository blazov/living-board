#!/usr/bin/env bash
# refresh-operator-actions.sh
#
# Refresh artifacts/state/operator-actions.json from current Supabase state.
# Queries all blocked tasks, cross-references against the existing action queue,
# removes resolved actions, updates task counts, flags new unclassified blockers,
# and recalculates priority scores.
#
# Usage: bash artifacts/scripts/refresh-operator-actions.sh
#
# Requires: psql, jq, python3, SUPABASE_DB_URL env var (or dashboard/.env.local)
#
# Exit codes:
#   0   success (operator-actions.json updated)
#   1   query or processing failure
#   2   missing dependencies

set -u

repo_root="$(git rev-parse --show-toplevel 2>/dev/null)"
if [ -z "$repo_root" ]; then
  echo "[refresh-actions] ERROR: not inside a git repository" >&2
  exit 2
fi

for cmd in psql jq python3; do
  if ! command -v "$cmd" >/dev/null 2>&1; then
    echo "[refresh-actions] ERROR: $cmd not found" >&2
    exit 2
  fi
done

if [ -z "${SUPABASE_DB_URL:-}" ] && [ -f "$repo_root/dashboard/.env.local" ]; then
  db_url_line="$(grep -E '^[[:space:]]*SUPABASE_DB_URL=' "$repo_root/dashboard/.env.local" | head -1 || true)"
  if [ -n "$db_url_line" ]; then
    db_url_value="${db_url_line#*=}"
    db_url_value="${db_url_value%\"}"
    db_url_value="${db_url_value#\"}"
    db_url_value="${db_url_value%\'}"
    db_url_value="${db_url_value#\'}"
    [ -n "$db_url_value" ] && export SUPABASE_DB_URL="$db_url_value"
  fi
fi

if [ -z "${SUPABASE_DB_URL:-}" ]; then
  echo "[refresh-actions] skipped: no SUPABASE_DB_URL" >&2
  exit 0
fi

STATE_DIR="$repo_root/artifacts/state"
ACTIONS_FILE="$STATE_DIR/operator-actions.json"

if [ ! -f "$ACTIONS_FILE" ]; then
  echo "[refresh-actions] ERROR: $ACTIONS_FILE not found — run initial audit first" >&2
  exit 1
fi

QUERY="
SELECT json_build_object(
  'blocked_tasks', (
    SELECT COALESCE(json_agg(json_build_object(
      'task_id', t.id,
      'task_title', t.title,
      'blocked_reason', t.blocked_reason,
      'goal_id', t.goal_id,
      'goal_title', g.title,
      'goal_priority', g.priority,
      'goal_status', g.status
    )), '[]'::json)
    FROM tasks t
    JOIN goals g ON g.id = t.goal_id
    WHERE t.status = 'blocked'
  ),
  'goal_priorities', (
    SELECT COALESCE(json_agg(json_build_object(
      'id', g.id,
      'title', g.title,
      'priority', g.priority,
      'status', g.status
    )), '[]'::json)
    FROM goals g
    WHERE g.status IN ('in_progress', 'pending')
  ),
  'cycle_count', (
    SELECT COALESCE(MAX(cycle_count), 0) FROM snapshots
  ),
  'queried_at', now()
) AS data;
"

echo "[refresh-actions] querying Supabase for blocked tasks..."
raw="$(psql "$SUPABASE_DB_URL" -tA -c "$QUERY" 2>&1)"
psql_exit=$?

if [ $psql_exit -ne 0 ]; then
  echo "[refresh-actions] ERROR: psql failed (exit $psql_exit): $raw" >&2
  exit 1
fi

if [ -z "$raw" ] || ! echo "$raw" | jq . >/dev/null 2>&1; then
  echo "[refresh-actions] ERROR: invalid JSON from query" >&2
  exit 1
fi

existing="$(cat "$ACTIONS_FILE")"

updated="$(python3 - "$raw" "$existing" <<'PYEOF'
import json
import sys
from datetime import datetime, timezone

db_data = json.loads(sys.argv[1])
existing = json.loads(sys.argv[2])

blocked_tasks = db_data["blocked_tasks"]
goal_priorities = {g["id"]: g for g in db_data["goal_priorities"]}
cycle_count = db_data["cycle_count"]
queried_at = db_data["queried_at"]

blocked_by_goal = {}
for t in blocked_tasks:
    gid = t["goal_id"]
    if gid not in blocked_by_goal:
        blocked_by_goal[gid] = []
    blocked_by_goal[gid].append(t)

refreshed_actions = []
removed_actions = []

for action in existing["actions"]:
    still_relevant = False
    updated_goals = []

    for gu in action.get("goals_unblocked", []):
        gid = gu["goal_id"]
        goal_blocked = blocked_by_goal.get(gid, [])

        if goal_blocked:
            updated_goals.append({
                "goal_id": gid,
                "goal_title": goal_blocked[0]["goal_title"],
                "tasks_unblocked": len(goal_blocked)
            })
            still_relevant = True
        else:
            gp = goal_priorities.get(gid)
            if gp and gp["status"] in ("in_progress", "pending"):
                updated_goals.append({
                    "goal_id": gid,
                    "goal_title": gp["title"],
                    "tasks_unblocked": 0
                })

    if still_relevant:
        total_unblocked = sum(g["tasks_unblocked"] for g in updated_goals)
        max_goal_priority = 10
        for gu in updated_goals:
            gp = goal_priorities.get(gu["goal_id"])
            if gp:
                max_goal_priority = min(max_goal_priority, gp["priority"])

        priority_score = round(
            (10 - max_goal_priority) * 0.4
            + total_unblocked * 1.0
            + max(0, (10 - action["effort_minutes"])) * 0.1,
            1
        )

        action["goals_unblocked"] = updated_goals
        action["priority_score"] = priority_score
        refreshed_actions.append(action)
    else:
        removed_actions.append(action["action"])

refreshed_actions.sort(key=lambda a: -a["priority_score"])
for i, a in enumerate(refreshed_actions, 1):
    a["id"] = i

action_lookup = {a["action"]: a["id"] for a in refreshed_actions}

refreshed_bundles = []
for bundle in existing.get("bundles", []):
    new_ids = []
    for old_id in bundle["action_ids"]:
        old_action = next((a for a in existing["actions"] if a["id"] == old_id), None)
        if old_action and old_action["action"] in action_lookup:
            new_ids.append(action_lookup[old_action["action"]])

    if len(new_ids) >= 2:
        matched = [a for a in refreshed_actions if a["id"] in new_ids]
        total_effort = sum(a["effort_minutes"] for a in matched)
        total_tasks = sum(
            sum(g["tasks_unblocked"] for g in a["goals_unblocked"])
            for a in matched
        )
        refreshed_bundles.append({
            "name": bundle["name"],
            "action_ids": new_ids,
            "total_effort_minutes": total_effort,
            "tasks_unblocked": total_tasks,
            "description": bundle["description"]
        })

matched_goal_ids = set()
for a in refreshed_actions:
    for gu in a.get("goals_unblocked", []):
        matched_goal_ids.add(gu["goal_id"])

unclassified = []
for gid, tasks in blocked_by_goal.items():
    if gid not in matched_goal_ids:
        for t in tasks:
            unclassified.append({
                "task_id": t["task_id"],
                "task_title": t["task_title"],
                "blocked_reason": t["blocked_reason"],
                "goal_id": gid,
                "goal_title": t["goal_title"]
            })

total_blocked = len(blocked_tasks)
total_actions = len(refreshed_actions)

summary_parts = [
    f"{total_actions} actions tracked across {len(blocked_by_goal)} goals",
    f"({total_blocked} blocked tasks total)"
]
if removed_actions:
    summary_parts.append(f"Removed {len(removed_actions)} resolved: {', '.join(removed_actions[:3])}")
if unclassified:
    summary_parts.append(f"{len(unclassified)} unclassified blocked tasks need audit")

result = {
    "generated_at": queried_at if isinstance(queried_at, str) else datetime.now(timezone.utc).isoformat(),
    "cycle": cycle_count,
    "summary": ". ".join(summary_parts) + ".",
    "actions": refreshed_actions,
    "bundles": refreshed_bundles
}

if unclassified:
    result["unclassified_blockers"] = unclassified

if removed_actions:
    result["removed_since_last"] = removed_actions

print(json.dumps(result, indent=2))
PYEOF
)"
py_exit=$?

if [ $py_exit -ne 0 ]; then
  echo "[refresh-actions] ERROR: Python processing failed" >&2
  exit 1
fi

if [ -z "$updated" ] || ! echo "$updated" | jq . >/dev/null 2>&1; then
  echo "[refresh-actions] ERROR: invalid JSON output from reconciliation" >&2
  exit 1
fi

echo "$updated" | jq . > "$ACTIONS_FILE"

action_count="$(echo "$updated" | jq '.actions | length')"
removed_count="$(echo "$updated" | jq '.removed_since_last // [] | length')"
unclassified_count="$(echo "$updated" | jq '.unclassified_blockers // [] | length')"
echo "[refresh-actions] OK — $action_count actions, $removed_count removed, $unclassified_count unclassified"

exit 0
