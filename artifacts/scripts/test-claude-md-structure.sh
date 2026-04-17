#!/usr/bin/env bash
# test-claude-md-structure.sh
#
# Structural guard for CLAUDE.md.
#
# Goal ef48bb21, task sort_order=40.
#
# Follows the reference pattern from test-cycle-start-structure.sh.
# See artifacts/docs/structural-anchor-inventory.md §3 for the
# anchor rationale and invariant descriptions.
#
# EXIT CODES
#   0   all anchors present
#   1   one or more anchors missing
#   3   the file does not exist
#
# USAGE
#   bash artifacts/scripts/test-claude-md-structure.sh
#   bash artifacts/scripts/test-claude-md-structure.sh path/to/CLAUDE.md

set -u

repo_root="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
target="${1:-$repo_root/CLAUDE.md}"

if [ ! -f "$target" ]; then
  echo "[test-claude-md-structure] FAIL: target file does not exist: $target" >&2
  exit 3
fi

# ---------------------------------------------------------------------------
# Canonical anchors from structural-anchor-inventory.md §3.
# Format: "LABEL|ANCHOR" — grep -F match required.
# ---------------------------------------------------------------------------
ANCHORS=(
  "phase:0-heading|### Phase 0: Sync"
  "phase:1-heading|### Phase 1: Orient"
  "phase:1b-heading|### Phase 1b: Reflect"
  "phase:1c-heading|### Phase 1c: Check Email"
  "phase:1d-heading|### Phase 1d: Process User Comments"
  "phase:2-heading|### Phase 2: Decide"
  "phase:3-heading|### Phase 3: Execute"
  "phase:4-heading|### Phase 4: Record"
  "contract:literal-first-call|literal first bash call"
  "contract:cycle-start-ref|bash artifacts/scripts/cycle-start.sh"
  "orient:snapshot-query|SELECT content, active_goals"
  "section:goal-decomposition|## Goal Decomposition"
  "section:memory-system|## Memory System"
  "section:identity|## Identity"
  "tool:execute-sql|execute_sql"
)

missing=0
echo "[test-claude-md-structure] checking $target"
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

min_lines=300
actual_lines=$(wc -l < "$target")
if [ "$actual_lines" -lt "$min_lines" ]; then
  echo "  MISS  sanity:min-line-count  [expected >=$min_lines, got $actual_lines]" >&2
  missing=$((missing + 1))
else
  echo "  ok    sanity:min-line-count  [$actual_lines >= $min_lines]"
fi

if [ "$missing" -gt 0 ]; then
  echo "[test-claude-md-structure] FAIL: $missing anchor(s) missing — CLAUDE.md is structurally incomplete" >&2
  exit 1
fi

echo "[test-claude-md-structure] OK — all ${#ANCHORS[@]} anchors + sanity check present"
exit 0
