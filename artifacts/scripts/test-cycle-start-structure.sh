#!/usr/bin/env bash
# test-cycle-start-structure.sh
#
# Structural guard for artifacts/scripts/cycle-start.sh.
#
# Goal 6f3e5575 (loud-failure-mode refit), task sort_order=60.
#
# WHY THIS EXISTS
# ---------------
# In cycle 116 a commit landed claiming to "rebuild three loud-failure
# surfaces" (40fc743). It also silently deleted 135 lines from
# cycle-start.sh: the entire git-sync block (checkout master / fetch /
# is-ancestor / hard-reset) and the canonical "[cycle-start] WARN:
# scheduler gap ..." surface, preserving only the single behavior the
# cycle-117 per-surface validator happened to spot-check. Cycle 117
# then declared the goal closed — transient state had convinced a
# behavioral validator that a gutted script was fine.
#
# The lesson (key_learning "validator-blindness pattern", 0.85):
# per-surface behavioral tests pass even when the surrounding
# implementation has been gutted, as long as the one tested behavior
# is preserved. The fix is a STRUCTURAL assertion at the text level,
# i.e. anchor-greps on the file itself. This script is that assertion.
#
# HOW IT WORKS
# ------------
# For each canonical anchor string that must appear in cycle-start.sh
# (one per invariant surface of the script), we grep. Missing anchor =
# non-zero exit with a loud per-miss log line naming the anchor and
# the invariant it guards. A future diff that replaces the file with
# a stub cannot pass this test without putting all the anchors back.
#
# This test is CHEAP (grep + bash -n), offline, and requires no
# credentials. It is meant to be wired into the validation pass for
# any future loud-failure or cycle-start work.
#
# EXIT CODES
#   0   all anchors present, syntax ok
#   1   one or more anchors missing, or the script is missing/empty
#   2   bash -n syntax error
#   3   the file does not exist
#
# USAGE
#   bash artifacts/scripts/test-cycle-start-structure.sh
#   bash artifacts/scripts/test-cycle-start-structure.sh path/to/cycle-start.sh  # override target
#
# To add a new invariant surface to cycle-start.sh in the future: add
# its canonical anchor to the ANCHORS array below with a short label
# explaining what the anchor guards.

set -u

repo_root="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
target="${1:-$repo_root/artifacts/scripts/cycle-start.sh}"

if [ ! -f "$target" ]; then
  echo "[test-cycle-start-structure] FAIL: target file does not exist: $target" >&2
  exit 3
fi

if ! bash -n "$target" 2>/tmp/cycle-start-syntax-err; then
  echo "[test-cycle-start-structure] FAIL: bash -n syntax error in $target" >&2
  sed 's/^/  /' /tmp/cycle-start-syntax-err >&2 || true
  exit 2
fi

# ---------------------------------------------------------------------------
# Canonical anchors. Each entry is "LABEL|ANCHOR". The anchor is a
# fixed string (grep -F) that must appear at least once in the target.
# Labels are human names for the surface being guarded so a miss produces
# a diagnosable log line.
#
# Keep anchors SHORT and UNIQUE — something generic like "echo" or "git"
# would be a trivially-satisfied stub-bait. Prefer strings that only
# exist because a specific surface is wired up.
# ---------------------------------------------------------------------------
ANCHORS=(
  "sync:branch-default|BRANCH=\"\${1:-master}\""
  "sync:checkout-branch|git checkout \"\$BRANCH\""
  "sync:fetch-origin|git fetch origin \"\$BRANCH\""
  "sync:ancestor-check|is-ancestor"
  "sync:disjoint-reset|git reset --hard \"origin/\$BRANCH\""
  "heartbeat:invokes-scheduler-status|scheduler-status.sh"
  "heartbeat:warn-threshold-arg|--warn-threshold=6"
  "heartbeat:gap-warn-surface|WARN: scheduler gap"
  "heartbeat:supabase-db-url-unset-warn|WARN: heartbeat skipped"
  "heartbeat:ok-summary-line|[cycle-start] OK"
  "safety:dirty-tree-gate|git diff --cached --quiet"
)

missing=0
echo "[test-cycle-start-structure] checking $target"
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

# Belt-and-braces: also assert a minimum line count. A heavily stubbed
# but anchor-preserving file would still fail this. 100 lines is well
# below the current ~160-line file; adjust upward if the file grows.
min_lines=100
actual_lines=$(wc -l < "$target")
if [ "$actual_lines" -lt "$min_lines" ]; then
  echo "  MISS  sanity:min-line-count  [expected >=$min_lines, got $actual_lines]" >&2
  missing=$((missing + 1))
else
  echo "  ok    sanity:min-line-count  [$actual_lines >= $min_lines]"
fi

if [ "$missing" -gt 0 ]; then
  echo "[test-cycle-start-structure] FAIL: $missing anchor(s) missing — cycle-start.sh is structurally incomplete" >&2
  echo "[test-cycle-start-structure] This is the structural guard that blocks the cycle-116 silent-regression class." >&2
  exit 1
fi

echo "[test-cycle-start-structure] OK — all ${#ANCHORS[@]} anchors + sanity check present"
exit 0
