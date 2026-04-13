#!/usr/bin/env bash
# cycle-start.sh
#
# Idempotent cycle-start wrapper for the Living Board agent.
#
# Goal 7449dc54 (cycle 65): retire the detached-HEAD-at-cycle-start invariant
# with a structural fix. This script is the canonical mechanism. Per CLAUDE.md,
# it MUST be the first bash call of every cycle.
#
# What it does:
#   1. Detect whether HEAD is detached (or already on master).
#   2. Switch to master (idempotent).
#   3. Fast-forward master from origin/master.
#
# Exit codes:
#   0   success — HEAD is on master, up to date with origin/master
#   1   git command failed (network, conflict, dirty tree)
#   2   not in a git repository
#
# Usage:
#   bash artifacts/scripts/cycle-start.sh
#
# This script is safe to re-run. If already on master and up to date, it
# is a no-op except for printing status.

set -u

# Move to repo root so the script works from any cwd.
repo_root="$(git rev-parse --show-toplevel 2>/dev/null)"
if [ -z "$repo_root" ]; then
  echo "[cycle-start] ERROR: not inside a git repository" >&2
  exit 2
fi
cd "$repo_root" || { echo "[cycle-start] ERROR: cannot cd to $repo_root" >&2; exit 1; }

current_ref="$(git symbolic-ref --short -q HEAD || echo "DETACHED")"
current_sha="$(git rev-parse --short HEAD 2>/dev/null || echo "?")"
echo "[cycle-start] starting at: ref=$current_ref sha=$current_sha"

if [ "$current_ref" = "DETACHED" ]; then
  echo "[cycle-start] HEAD was detached at $current_sha — switching to master"
fi

# Idempotent checkout. If already on master, this is a no-op.
if ! git checkout master; then
  echo "[cycle-start] ERROR: git checkout master failed" >&2
  exit 1
fi

if ! git pull --ff-only origin master; then
  echo "[cycle-start] ERROR: git pull --ff-only origin master failed" >&2
  echo "[cycle-start] HINT: there may be local commits not on origin, or a network error." >&2
  exit 1
fi

final_ref="$(git symbolic-ref --short -q HEAD || echo "DETACHED")"
final_sha="$(git rev-parse --short HEAD 2>/dev/null || echo "?")"
echo "[cycle-start] OK — ref=$final_ref sha=$final_sha"
exit 0
