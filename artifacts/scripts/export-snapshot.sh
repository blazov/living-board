#!/usr/bin/env bash
# export-snapshot.sh
#
# Export current board state to local JSON files for offline resilience.
# Writes two files:
#   artifacts/state/latest-snapshot.json   (overwritten each cycle)
#   artifacts/state/snapshot-<ISO>.json    (timestamped historical copy)
#
# Usage: bash artifacts/scripts/export-snapshot.sh
#
# Requires: psql, jq, SUPABASE_DB_URL env var (or dashboard/.env.local)
#
# Exit codes:
#   0   success
#   1   query or write failure
#   2   missing dependencies

set -u

repo_root="$(git rev-parse --show-toplevel 2>/dev/null)"
if [ -z "$repo_root" ]; then
  echo "[export-snapshot] ERROR: not inside a git repository" >&2
  exit 2
fi

for cmd in psql jq; do
  if ! command -v "$cmd" >/dev/null 2>&1; then
    echo "[export-snapshot] ERROR: $cmd not found" >&2
    exit 2
  fi
done

# Source SUPABASE_DB_URL from dashboard/.env.local if not already set
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
  echo "[export-snapshot] skipped: no SUPABASE_DB_URL" >&2
  exit 0
fi

STATE_DIR="$repo_root/artifacts/state"
mkdir -p "$STATE_DIR"

QUERY="
SELECT json_build_object(
  'exported_at', now(),
  'snapshot', (
    SELECT json_build_object(
      'content', s.content,
      'active_goals', s.active_goals,
      'current_focus', s.current_focus,
      'recent_outcomes', s.recent_outcomes,
      'open_blockers', s.open_blockers,
      'key_learnings', s.key_learnings,
      'cycle_count', s.cycle_count,
      'created_at', s.created_at
    )
    FROM snapshots s ORDER BY s.created_at DESC LIMIT 1
  ),
  'goals', (
    SELECT COALESCE(json_agg(json_build_object(
      'id', g.id, 'title', g.title, 'status', g.status,
      'priority', g.priority, 'description', g.description
    ) ORDER BY g.priority ASC, g.created_at ASC), '[]'::json)
    FROM goals g WHERE g.status IN ('in_progress', 'pending')
  ),
  'tasks', (
    SELECT COALESCE(json_agg(json_build_object(
      'id', t.id, 'goal_id', t.goal_id, 'title', t.title,
      'status', t.status, 'sort_order', t.sort_order,
      'result', t.result, 'blocked_reason', t.blocked_reason
    ) ORDER BY t.sort_order ASC), '[]'::json)
    FROM tasks t
    JOIN goals g ON g.id = t.goal_id
    WHERE g.status IN ('in_progress', 'pending')
      AND t.status IN ('pending', 'in_progress', 'blocked')
  ),
  'recent_log', (
    SELECT COALESCE(json_agg(json_build_object(
      'action', el.action, 'summary', el.summary, 'created_at', el.created_at
    ) ORDER BY el.created_at DESC), '[]'::json)
    FROM (SELECT action, summary, created_at FROM execution_log ORDER BY created_at DESC LIMIT 5) el
  )
) AS state;
"

raw="$(psql "$SUPABASE_DB_URL" -tA -c "$QUERY" 2>&1)"
psql_exit=$?

if [ $psql_exit -ne 0 ]; then
  echo "[export-snapshot] ERROR: psql failed (exit $psql_exit): $raw" >&2
  exit 1
fi

if [ -z "$raw" ] || ! echo "$raw" | jq . >/dev/null 2>&1; then
  echo "[export-snapshot] ERROR: invalid JSON from query" >&2
  exit 1
fi

formatted="$(echo "$raw" | jq .)"

# Write latest (overwritten each cycle)
echo "$formatted" > "$STATE_DIR/latest-snapshot.json"

# Write timestamped copy
ts="$(echo "$formatted" | jq -r '.exported_at' | sed 's/[:]/-/g; s/[+].*//; s/T/_T/')"
if [ -n "$ts" ] && [ "$ts" != "null" ]; then
  echo "$formatted" > "$STATE_DIR/snapshot-${ts}.json"
  echo "[export-snapshot] OK — wrote latest-snapshot.json + snapshot-${ts}.json"
else
  echo "[export-snapshot] OK — wrote latest-snapshot.json (timestamp parse failed, no historical copy)"
fi

exit 0
