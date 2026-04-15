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
#   3. Align local master to origin/master:
#        - already aligned  -> no-op
#        - strict ancestor  -> fast-forward
#        - disjoint/diverged -> hard reset to origin/master (safe: see below)
#
# Why the disjoint-reset path exists (goal 63d581f9, cycle 84):
#   Fresh clones seed local `master` to a stale open-source template tip
#   (root 8f1f1cc). The agent's real history lives on origin/master
#   (root 23c8e80). These are two disjoint DAGs that happen to share the
#   name `master`, so `git pull --ff-only` always fails with "Not possible
#   to fast-forward." Every agent-authored commit is pushed to origin
#   during its own cycle -- nothing of value ever lives only on local
#   master between cycles -- so resetting the stale seed is lossless.
#   Full writeup: artifacts/investigations/force-push-rootcause.md
#
# Safety: before any destructive reset we refuse if the working tree is
# dirty. `git checkout master` earlier in this script would already have
# failed on overwriting-dirty paths, but we re-check explicitly so no
# uncommitted work is ever silently discarded.
#
# Exit codes:
#   0   success -- HEAD is on master, equal to origin/master
#   1   git command failed (network, conflict, dirty tree, etc.)
#   2   not in a git repository

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

# Fetch origin/master explicitly; do not merge yet. We inspect refs first.
if ! git fetch origin master; then
  echo "[cycle-start] ERROR: git fetch origin master failed" >&2
  exit 1
fi

local_sha="$(git rev-parse master)"
remote_sha="$(git rev-parse origin/master)"

if [ "$local_sha" = "$remote_sha" ]; then
  echo "[cycle-start] already aligned with origin/master"
elif git merge-base --is-ancestor "$local_sha" "$remote_sha"; then
  # Normal fast-forward case: local master is strictly behind origin/master.
  echo "[cycle-start] fast-forwarding master from $local_sha to $remote_sha"
  if ! git merge --ff-only origin/master; then
    echo "[cycle-start] ERROR: fast-forward merge failed" >&2
    exit 1
  fi
else
  # Disjoint or diverged. Local master is the template seed or similar
  # non-agent state. The agent's canonical state is origin/master.
  # Refuse to destroy uncommitted work -- safety gate before reset --hard.
  if ! git diff --quiet || ! git diff --cached --quiet; then
    echo "[cycle-start] ERROR: local master ($local_sha) is not an ancestor of origin/master ($remote_sha), but the working tree is dirty." >&2
    echo "[cycle-start] HINT: inspect with 'git status' and either commit, stash, or discard before re-running." >&2
    exit 1
  fi
  echo "[cycle-start] local master ($local_sha) is not an ancestor of origin/master ($remote_sha) — resetting (disjoint-seed path)"
  if ! git reset --hard origin/master; then
    echo "[cycle-start] ERROR: git reset --hard origin/master failed" >&2
    exit 1
  fi
fi

final_ref="$(git symbolic-ref --short -q HEAD || echo "DETACHED")"
final_sha="$(git rev-parse --short HEAD 2>/dev/null || echo "?")"
echo "[cycle-start] OK — ref=$final_ref sha=$final_sha"

# ---------------------------------------------------------------------------
# Scheduler heartbeat check (goal 331b89e0, task d17cc5a2)
#
# Invoke scheduler-status.sh to surface silent-dropout warnings at cycle start.
# The script writes its one-line summary to stdout; we pass that through so it
# lands in the cycle-start log. Exit-code contract:
#   0   healthy (or SUPABASE_DB_URL unset → graceful skip)
#   1   psql failure           -> degrade, log [cycle-start] heartbeat ERROR
#   2   usage error (our bug)  -> degrade, log [cycle-start] heartbeat ERROR
#   3   gap > threshold        -> emit [cycle-start] WARN line to stderr
#
# Non-zero exits from the heartbeat NEVER fail cycle-start — the sync is the
# critical contract; the heartbeat is observability on top.
# ---------------------------------------------------------------------------
heartbeat_script="$repo_root/artifacts/scripts/scheduler-status.sh"
if [ -x "$heartbeat_script" ]; then
  # Single invocation: capture stdout; stderr streams directly to our stderr.
  heartbeat_summary="$("$heartbeat_script" --warn-threshold=6 2>&2)"
  heartbeat_exit=$?
  [ -n "$heartbeat_summary" ] && echo "$heartbeat_summary"
  case $heartbeat_exit in
    0) : ;;  # healthy or skipped (SUPABASE_DB_URL unset)
    3)
      # Parse `age=N.NNNh` from the summary for the WARN line.
      age_field="$(printf '%s' "$heartbeat_summary" | grep -oE 'age=[^ ]+' | head -1)"
      echo "[cycle-start] WARN: scheduler gap ${age_field:-unknown} exceeds 6h threshold" >&2
      ;;
    *)
      echo "[cycle-start] heartbeat ERROR (exit $heartbeat_exit) — continuing; observability is best-effort" >&2
      ;;
  esac
fi

exit 0
