#!/usr/bin/env bash
# test-scheduler-status-structure.sh
#
# Structural guard for artifacts/scripts/scheduler-status.sh.
#
# Goal ef48bb21, task sort_order=30.
#
# Follows the reference pattern from test-agent-structure.sh.
# See artifacts/docs/structural-anchor-inventory.md §2 for the
# anchor rationale and invariant descriptions.
#
# EXIT CODES
#   0   all anchors present, syntax ok
#   1   one or more anchors missing
#   2   bash syntax error
#   3   the file does not exist
#
# USAGE
#   bash artifacts/scripts/test-scheduler-status-structure.sh
#   bash artifacts/scripts/test-scheduler-status-structure.sh path/to/scheduler-status.sh

set -u

repo_root="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
target="${1:-$repo_root/artifacts/scripts/scheduler-status.sh}"

if [ ! -f "$target" ]; then
  echo "[test-scheduler-status-structure] FAIL: target file does not exist: $target" >&2
  exit 3
fi

if ! bash -n "$target" 2>/tmp/scheduler-status-syntax-err; then
  echo "[test-scheduler-status-structure] FAIL: bash syntax error in $target" >&2
  sed 's/^/  /' /tmp/scheduler-status-syntax-err >&2 || true
  exit 2
fi

# ---------------------------------------------------------------------------
# Canonical anchors from structural-anchor-inventory.md §2.
# Format: "LABEL|ANCHOR" — grep -F match required.
# ---------------------------------------------------------------------------
ANCHORS=(
  "args:warn-threshold|--warn-threshold="
  "env:db-url-check|SUPABASE_DB_URL"
  "query:view-ref|scheduler_health"
  "query:hours-since|hours_since_last"
  "query:gap-count|gap_24h_count"
  "query:entries|entries_24h"
  "exec:psql|psql \"\$SUPABASE_DB_URL\""
  "output:prefix|[scheduler]"
  "output:last-exec|last_exec="
  "output:age|age="
  "exit:threshold-check|exit 3"
  "skip:no-db-url|skipped: no SUPABASE_DB_URL"
)

missing=0
echo "[test-scheduler-status-structure] checking $target"
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

min_lines=80
actual_lines=$(wc -l < "$target")
if [ "$actual_lines" -lt "$min_lines" ]; then
  echo "  MISS  sanity:min-line-count  [expected >=$min_lines, got $actual_lines]" >&2
  missing=$((missing + 1))
else
  echo "  ok    sanity:min-line-count  [$actual_lines >= $min_lines]"
fi

if [ "$missing" -gt 0 ]; then
  echo "[test-scheduler-status-structure] FAIL: $missing anchor(s) missing — scheduler-status.sh is structurally incomplete" >&2
  exit 1
fi

echo "[test-scheduler-status-structure] OK — all ${#ANCHORS[@]} anchors + sanity check present"
exit 0
