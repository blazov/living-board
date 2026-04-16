#!/bin/bash
# cycle-start.sh — Entry point for scheduled agent cycles.
# Runs the heartbeat check (if SUPABASE_DB_URL is set) then starts the agent.

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# ── Heartbeat check ──────────────────────────────────────
if [ -z "$SUPABASE_DB_URL" ]; then
  echo "[cycle-start] WARN: heartbeat skipped — SUPABASE_DB_URL unset; in-band scheduler observability disabled" >&2
else
  echo "[scheduler] heartbeat: recording cycle start"
  # If a heartbeat script exists, run it
  if [ -f "$SCRIPT_DIR/heartbeat.sh" ]; then
    bash "$SCRIPT_DIR/heartbeat.sh" || echo "[scheduler] heartbeat failed (non-fatal)" >&2
  fi
fi

# ── Start the agent cycle ────────────────────────────────
cd "$REPO_ROOT"
echo "[cycle-start] starting agent cycle"
