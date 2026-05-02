#!/usr/bin/env bash
# template-setup.sh
#
# Interactive setup for a Living Board agent instance.
# Substitutes placeholders in CLAUDE.md.template, runs schema.sql against
# Supabase, and optionally inserts seed data.
#
# Prerequisites:
#   - bash 4+
#   - psql (PostgreSQL client) — for running schema/seed SQL
#   - A Supabase project with a Postgres connection string
#
# Usage:
#   bash artifacts/living-board-template/template-setup.sh
#
# Idempotent: safe to re-run. schema.sql uses IF NOT EXISTS throughout.
# Re-running with different values overwrites CLAUDE.md.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TEMPLATE="$SCRIPT_DIR/CLAUDE.md.template"
SCHEMA="$SCRIPT_DIR/schema.sql"
SEED="$SCRIPT_DIR/seed-data.sql"

# ---------- helpers ----------

info()  { printf '\033[1;34m[setup]\033[0m %s\n' "$1"; }
ok()    { printf '\033[1;32m[setup]\033[0m %s\n' "$1"; }
warn()  { printf '\033[1;33m[setup]\033[0m %s\n' "$1"; }
err()   { printf '\033[1;31m[setup]\033[0m %s\n' "$1" >&2; }

ask() {
  local prompt="$1" default="${2:-}" value
  if [ -n "$default" ]; then
    printf '\033[1m%s\033[0m [%s]: ' "$prompt" "$default" >&2
  else
    printf '\033[1m%s\033[0m: ' "$prompt" >&2
  fi
  read -r value
  echo "${value:-$default}"
}

ask_yes_no() {
  local prompt="$1" default="${2:-y}" reply
  printf '\033[1m%s\033[0m [%s]: ' "$prompt" "$default"
  read -r reply
  reply="${reply:-$default}"
  [[ "$reply" =~ ^[Yy] ]]
}

# ---------- pre-flight ----------

if [ ! -f "$TEMPLATE" ]; then
  err "CLAUDE.md.template not found at $TEMPLATE"
  err "Run this script from the repo root: bash artifacts/living-board-template/template-setup.sh"
  exit 1
fi

if [ ! -f "$SCHEMA" ]; then
  err "schema.sql not found at $SCHEMA"
  exit 1
fi

if ! command -v psql &>/dev/null; then
  warn "psql not found — schema/seed SQL steps will be skipped."
  warn "Install postgresql-client and re-run, or run schema.sql manually in the Supabase SQL editor."
  HAS_PSQL=false
else
  HAS_PSQL=true
fi

# ---------- gather configuration ----------

echo ""
info "Living Board — Interactive Setup"
echo "─────────────────────────────────────────────"
echo ""

SUPABASE_PROJECT_ID="$(ask "Supabase project ID (from project settings)")"
if [ -z "$SUPABASE_PROJECT_ID" ]; then
  err "Supabase project ID is required."
  exit 1
fi

BRANCH_NAME="$(ask "Git branch name for the agent" "master")"

AGENTMAIL_ADDRESS="$(ask "AgentMail address (leave blank to skip email features)" "")"

DEFAULT_TOOLS='- **WebSearch / WebFetch**: Research, find information, check platforms
- **Bash**: Run scripts, process data, interact with APIs
- **Read / Write / Edit**: Work with files in the repo (artifacts/)
- **GitHub MCP**: Create issues, PRs, manage the repository'
echo ""
info "Available tools — a description of tools your agent can use."
info "Press Enter to accept the default, or type a custom list."
AVAILABLE_TOOLS="$(ask "Available tools" "$DEFAULT_TOOLS")"

echo ""

# ---------- generate CLAUDE.md ----------

info "Generating CLAUDE.md from template..."

OUTPUT="$SCRIPT_DIR/CLAUDE.md"

sed \
  -e "s|{{SUPABASE_PROJECT_ID}}|${SUPABASE_PROJECT_ID}|g" \
  -e "s|{{BRANCH_NAME}}|${BRANCH_NAME}|g" \
  -e "s|{{AGENTMAIL_ADDRESS}}|${AGENTMAIL_ADDRESS}|g" \
  "$TEMPLATE" > "$OUTPUT.tmp"

# AVAILABLE_TOOLS may be multi-line; sed can't handle that easily.
# Use awk for the multi-line replacement.
awk -v tools="$AVAILABLE_TOOLS" '{gsub(/\{\{AVAILABLE_TOOLS\}\}/, tools); print}' \
  "$OUTPUT.tmp" > "$OUTPUT"
rm -f "$OUTPUT.tmp"

ok "CLAUDE.md generated at $OUTPUT"

# If AGENTMAIL_ADDRESS is empty, note it in the output file
if [ -z "$AGENTMAIL_ADDRESS" ]; then
  warn "AgentMail address not set — Phase 1c (email) will be non-functional."
  warn "Edit CLAUDE.md later to add it, or re-run this script."
fi

# ---------- run schema.sql ----------

if [ "$HAS_PSQL" = true ]; then
  echo ""
  info "Database setup"
  echo ""
  info "You need your Supabase Postgres connection string."
  info "Find it in: Supabase Dashboard → Project Settings → Database → Connection string (URI)"
  info "Format: postgresql://postgres.[ref]:[password]@aws-0-[region].pooler.supabase.com:6543/postgres"
  echo ""
  DB_URL="$(ask "Supabase Postgres connection string (URI)" "")"

  if [ -n "$DB_URL" ]; then
    info "Running schema.sql..."
    if psql "$DB_URL" -f "$SCHEMA" 2>&1; then
      ok "Schema applied successfully."
    else
      err "Schema application failed. You can run schema.sql manually in the Supabase SQL editor."
    fi

    if [ -f "$SEED" ]; then
      echo ""
      if ask_yes_no "Insert example seed data? (creates a sample goal with tasks)" "y"; then
        info "Running seed-data.sql..."
        if psql "$DB_URL" -f "$SEED" 2>&1; then
          ok "Seed data inserted."
        else
          warn "Seed data insertion had errors (possibly already exists — safe to ignore)."
        fi
      else
        info "Skipping seed data."
      fi
    fi

    # Write DB_URL to .env.local for the dashboard if one exists
    DASHBOARD_ENV="$SCRIPT_DIR/../../dashboard/.env.local"
    if [ -d "$(dirname "$DASHBOARD_ENV")" ]; then
      if ask_yes_no "Write SUPABASE_DB_URL to dashboard/.env.local?" "y"; then
        if grep -q '^SUPABASE_DB_URL=' "$DASHBOARD_ENV" 2>/dev/null; then
          sed -i "s|^SUPABASE_DB_URL=.*|SUPABASE_DB_URL=$DB_URL|" "$DASHBOARD_ENV"
          ok "Updated SUPABASE_DB_URL in dashboard/.env.local"
        else
          echo "SUPABASE_DB_URL=$DB_URL" >> "$DASHBOARD_ENV"
          ok "Added SUPABASE_DB_URL to dashboard/.env.local"
        fi
      fi
    fi
  else
    warn "No connection string provided — skipping database setup."
    warn "Run schema.sql manually in the Supabase SQL editor."
  fi
else
  echo ""
  warn "psql not available — run these SQL files manually in the Supabase SQL editor:"
  warn "  1. $SCHEMA"
  warn "  2. $SEED (optional — example data)"
fi

# ---------- summary ----------

echo ""
echo "═══════════════════════════════════════════════"
ok "Setup complete!"
echo ""
echo "  CLAUDE.md:          $OUTPUT"
echo "  Supabase project:   $SUPABASE_PROJECT_ID"
echo "  Branch:             $BRANCH_NAME"
[ -n "$AGENTMAIL_ADDRESS" ] && echo "  AgentMail:          $AGENTMAIL_ADDRESS"
echo ""
echo "Next steps:"
echo "  1. Copy CLAUDE.md to your repo root:"
echo "       cp $OUTPUT ./CLAUDE.md"
echo "  2. Install the pre-commit hook:"
echo "       bash artifacts/scripts/install-pre-commit-hook.sh"
echo "  3. Set up your Claude Code trigger (scheduled or manual)"
echo "  4. Run your first cycle and watch the agent orient itself!"
echo ""
echo "For the full guide, see QUICKSTART.md"
echo "═══════════════════════════════════════════════"
