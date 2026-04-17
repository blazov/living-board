#!/usr/bin/env bash
# test-schema-structure.sh
#
# Structural guard for artifacts/living-board-template/schema.sql.
#
# Goal ef48bb21, task sort_order=50.
#
# Follows the reference pattern from test-cycle-start-structure.sh.
# See artifacts/docs/structural-anchor-inventory.md §4 for the
# anchor rationale and invariant descriptions.
#
# EXIT CODES
#   0   all anchors present
#   1   one or more anchors missing
#   3   the file does not exist
#
# USAGE
#   bash artifacts/scripts/test-schema-structure.sh
#   bash artifacts/scripts/test-schema-structure.sh path/to/schema.sql

set -u

repo_root="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
target="${1:-$repo_root/artifacts/living-board-template/schema.sql}"

if [ ! -f "$target" ]; then
  echo "[test-schema-structure] FAIL: target file does not exist: $target" >&2
  exit 3
fi

# ---------------------------------------------------------------------------
# Canonical anchors from structural-anchor-inventory.md §4.
# Format: "LABEL|ANCHOR" — grep -F match required.
# ---------------------------------------------------------------------------
ANCHORS=(
  "table:goals|CREATE TABLE IF NOT EXISTS goals"
  "table:tasks|CREATE TABLE IF NOT EXISTS tasks"
  "table:execution-log|CREATE TABLE IF NOT EXISTS execution_log"
  "table:learnings|CREATE TABLE IF NOT EXISTS learnings"
  "table:snapshots|CREATE TABLE IF NOT EXISTS snapshots"
  "table:goal-comments|CREATE TABLE IF NOT EXISTS goal_comments"
  "table:agent-config|CREATE TABLE IF NOT EXISTS agent_config"
  "ext:pgcrypto|CREATE EXTENSION IF NOT EXISTS pgcrypto"
  "trigger:completed-at-fn|goals_set_completed_at()"
  "trigger:completed-at-ins|goals_set_completed_at_ins"
  "trigger:completed-at-upd|goals_set_completed_at_upd"
  "view:scheduler-health|CREATE OR REPLACE VIEW public.scheduler_health"
  "fk:tasks-goals|goal_id UUID NOT NULL REFERENCES goals(id)"
  "index:goals-status|idx_goals_status"
)

missing=0
echo "[test-schema-structure] checking $target"
for entry in "${ANCHORS[@]}"; do
  label="${entry%%|*}"
  anchor="${entry#*|}"
  if grep -F -q -- "$anchor" "$target"; then
    echo "  ok    $label  [anchor: $anchor]"
  else
    echo "  MISS  $label  [anchor: $anchor]" >&2
    missing=$((missing + 1))
  fi
done

min_lines=120
actual_lines=$(wc -l < "$target")
if [ "$actual_lines" -lt "$min_lines" ]; then
  echo "  MISS  sanity:min-line-count  [expected >=$min_lines, got $actual_lines]" >&2
  missing=$((missing + 1))
else
  echo "  ok    sanity:min-line-count  [$actual_lines >= $min_lines]"
fi

if [ "$missing" -gt 0 ]; then
  echo "[test-schema-structure] FAIL: $missing anchor(s) missing — schema.sql is structurally incomplete" >&2
  exit 1
fi

echo "[test-schema-structure] OK — all ${#ANCHORS[@]} anchors + sanity check present"
exit 0
