#!/usr/bin/env bash
# scheduler-status.sh
#
# Query the scheduler_health view and emit a one-line status summary.
#
# Goal  : 331b89e0 — Add scheduler heartbeat monitoring so silent dropouts
#                    surface within 6h
# Task  : 43481d43 — Write artifacts/scripts/scheduler-status.sh
#
# Usage:
#   scheduler-status.sh [--warn-threshold=<hours>]
#
#   --warn-threshold=N   Float/int hours. If hours_since_last > N, exit 3 after
#                        printing the summary. Default: 6. A NULL last_exec_at
#                        (empty log) is treated as always-warn → also exit 3.
#
# Output (stdout on success):
#   [scheduler] last_exec=<ISO-Z> age=<N.NNN>h gaps_24h=<N> entries_24h=<N>
#
# Output (empty log):
#   [scheduler] last_exec=NONE age=n/a gaps_24h=0 entries_24h=0
#
# Exit codes:
#   0   success — scheduler is healthy (or SUPABASE_DB_URL is unset → skipped)
#   1   psql command failed (network error, bad credentials, etc.)
#   2   usage error (bad flag / non-numeric threshold)
#   3   scheduler lag exceeds --warn-threshold (summary still printed to stdout)
#
# Dependencies:
#   psql (postgresql-client), SUPABASE_DB_URL env var
#
# Design notes:
#   - Zero side-effects: read-only query, no writes, no temp files.
#   - Fast: single SELECT against a pre-defined view; typically <200 ms.
#   - Idempotent: safe to run multiple times per cycle.
#   - Matches cycle-start.sh bash style: set -u, [scheduler] prefix, clear exits.

set -u

# ---------------------------------------------------------------------------
# Parse arguments
# ---------------------------------------------------------------------------
WARN_THRESHOLD=6

for arg in "$@"; do
  case "$arg" in
    --warn-threshold=*)
      raw_threshold="${arg#--warn-threshold=}"
      # Validate: must be a non-empty number (integer or decimal, positive).
      if ! printf '%s' "$raw_threshold" | grep -qE '^[0-9]+([.][0-9]+)?$'; then
        echo "[scheduler] ERROR: --warn-threshold value must be a positive number, got: '$raw_threshold'" >&2
        exit 2
      fi
      WARN_THRESHOLD="$raw_threshold"
      ;;
    *)
      echo "[scheduler] ERROR: unknown flag: '$arg'" >&2
      echo "[scheduler] Usage: scheduler-status.sh [--warn-threshold=<hours>]" >&2
      exit 2
      ;;
  esac
done

# ---------------------------------------------------------------------------
# Graceful skip when SUPABASE_DB_URL is unset or empty
# ---------------------------------------------------------------------------
if [ -z "${SUPABASE_DB_URL:-}" ]; then
  echo "[scheduler] skipped: no SUPABASE_DB_URL" >&2
  exit 0
fi

# ---------------------------------------------------------------------------
# Query scheduler_health view
# Pipe-delimited, tuples-only, unaligned — reliable for programmatic parsing.
# ---------------------------------------------------------------------------
QUERY="SELECT
  COALESCE(to_char(last_exec_at AT TIME ZONE 'UTC', 'YYYY-MM-DD\"T\"HH24:MI:SS\"Z\"'), 'NULL'),
  COALESCE(hours_since_last::text, 'NULL'),
  COALESCE(gap_24h_count::text, '0'),
  COALESCE(entries_24h::text, '0')
FROM scheduler_health;"

raw="$(psql "$SUPABASE_DB_URL" -tA -F'|' -c "$QUERY" 2>&1)"
psql_exit=$?

if [ $psql_exit -ne 0 ]; then
  echo "[scheduler] ERROR: psql failed (exit $psql_exit): $raw" >&2
  exit 1
fi

# Strip any trailing whitespace / blank lines from psql output
raw="$(printf '%s' "$raw" | tr -d '\r' | grep -v '^$' | head -1)"

if [ -z "$raw" ]; then
  echo "[scheduler] ERROR: psql returned no rows" >&2
  exit 1
fi

# Parse pipe-delimited fields
last_exec_raw="$(printf '%s' "$raw" | cut -d'|' -f1)"
age_raw="$(printf '%s' "$raw" | cut -d'|' -f2)"
gaps_raw="$(printf '%s' "$raw" | cut -d'|' -f3)"
entries_raw="$(printf '%s' "$raw" | cut -d'|' -f4)"

# ---------------------------------------------------------------------------
# Format and print the summary line
# ---------------------------------------------------------------------------
if [ "$last_exec_raw" = "NULL" ]; then
  # Empty log — anomalous, always warn.
  echo "[scheduler] last_exec=NONE age=n/a gaps_24h=${gaps_raw} entries_24h=${entries_raw}"
  exit 3
fi

# Round age to 3 decimal places for display (awk for portability).
age_display="$(printf '%s' "$age_raw" | awk '{printf "%.3f", $1}')h"

echo "[scheduler] last_exec=${last_exec_raw} age=${age_display} gaps_24h=${gaps_raw} entries_24h=${entries_raw}"

# ---------------------------------------------------------------------------
# Threshold check — exit 3 if lag exceeds the threshold
# ---------------------------------------------------------------------------
exceeds="$(printf '%s %s' "$age_raw" "$WARN_THRESHOLD" | awk '{print ($1 > $2) ? "yes" : "no"}')"
if [ "$exceeds" = "yes" ]; then
  exit 3
fi

exit 0
