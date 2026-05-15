#!/usr/bin/env bash
set -euo pipefail

# Main entrypoint for the Living Board GitHub Action.
# This script is called by the composite action steps but can also
# be invoked standalone for local testing.
#
# Usage: ./action/entrypoint.sh
#
# Required env vars:
#   ANTHROPIC_API_KEY, SUPABASE_PROJECT_ID, SUPABASE_SERVICE_KEY
# Optional env vars:
#   MODEL (default: sonnet), MAX_TURNS (default: 200),
#   BRANCH (default: master), WORKING_DIR (default: .)

MODEL="${MODEL:-sonnet}"
MAX_TURNS="${MAX_TURNS:-200}"
BRANCH="${BRANCH:-master}"
WORKING_DIR="${WORKING_DIR:-.}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "=== Living Board Agent Cycle ==="
echo "Model: ${MODEL} | Max turns: ${MAX_TURNS} | Branch: ${BRANCH}"

# Step 1: Configure MCP
echo "--- Configuring MCP ---"
bash "${SCRIPT_DIR}/configure-mcp.sh"

# Step 2: Run the agent cycle
echo "--- Running agent cycle ---"
cd "${WORKING_DIR}"
claude --model "${MODEL}" \
  --max-turns "${MAX_TURNS}" \
  --print \
  "Execute your full agent cycle as defined in CLAUDE.md. Orient (read goals/tasks from Supabase), Decide (pick the highest priority incomplete task), Execute (do the work), Record (update Supabase with results, log entry, and learnings). Be concrete and produce real results."

# Step 3: Commit artifacts
echo "--- Committing artifacts ---"
cd "${WORKING_DIR}"
bash "${SCRIPT_DIR}/commit-artifacts.sh"

echo "=== Cycle complete ==="
