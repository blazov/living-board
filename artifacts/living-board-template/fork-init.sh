#!/usr/bin/env bash
# fork-init.sh
#
# One-time cleanup for forked Living Board repos.
# Strips project-specific content (memoirs, articles, logs, research,
# datasets, platform-specific files) while preserving the template
# infrastructure (scripts, schema, dashboard, runner, docs site).
#
# Usage:
#   bash artifacts/living-board-template/fork-init.sh
#
# Safe to run multiple times — idempotent.
# Does NOT touch the database or CLAUDE.md — run template-setup.sh for that.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# ---------- helpers ----------

info()  { printf '\033[1;34m[fork-init]\033[0m %s\n' "$1"; }
ok()    { printf '\033[1;32m[fork-init]\033[0m %s\n' "$1"; }
warn()  { printf '\033[1;33m[fork-init]\033[0m %s\n' "$1"; }

removed=0
kept=0

remove_contents() {
  local dir="$1"
  local keep_gitkeep="${2:-true}"
  if [ -d "$dir" ]; then
    local count
    count=$(find "$dir" -type f ! -name '.gitkeep' | wc -l)
    if [ "$count" -gt 0 ]; then
      find "$dir" -type f ! -name '.gitkeep' -delete
      find "$dir" -mindepth 1 -type d -empty -delete
      removed=$((removed + count))
      info "Cleaned $dir ($count files)"
    fi
    if [ "$keep_gitkeep" = "true" ] && [ ! -f "$dir/.gitkeep" ]; then
      touch "$dir/.gitkeep"
    fi
  fi
}

remove_dir() {
  local dir="$1"
  if [ -d "$dir" ]; then
    local count
    count=$(find "$dir" -type f | wc -l)
    rm -rf "$dir"
    removed=$((removed + count))
    info "Removed $dir ($count files)"
  fi
}

remove_file() {
  local file="$1"
  if [ -f "$file" ]; then
    rm -f "$file"
    removed=$((removed + 1))
    info "Removed $file"
  fi
}

# ---------- pre-flight ----------

echo ""
info "Living Board — Fork Initialization"
echo "─────────────────────────────────────────────"
echo ""
info "This will remove project-specific content from your fork"
info "while preserving the template infrastructure."
echo ""

if [ ! -f "$REPO_ROOT/CLAUDE.md" ] && [ ! -f "$REPO_ROOT/artifacts/living-board-template/CLAUDE.md.template" ]; then
  warn "This doesn't look like a Living Board repo. Aborting."
  exit 1
fi

printf '\033[1mContinue? [y/N]\033[0m: '
read -r reply
if [[ ! "$reply" =~ ^[Yy] ]]; then
  info "Aborted."
  exit 0
fi

echo ""

# ---------- strip project-specific content ----------

# Content: memoirs, articles, guides, outlines
remove_contents "$REPO_ROOT/artifacts/content"

# Research: project-specific research notes and audits
remove_contents "$REPO_ROOT/artifacts/research"

# Logs: execution cycle logs
remove_contents "$REPO_ROOT/artifacts/logs"

# Data: exported dataset JSON/CSV
remove_contents "$REPO_ROOT/artifacts/data"

# Metrics: project-specific metrics and reports
remove_contents "$REPO_ROOT/artifacts/metrics"

# Substack: platform-specific content and branding
remove_dir "$REPO_ROOT/artifacts/substack"

# Freelancing: project-specific service offerings
remove_dir "$REPO_ROOT/artifacts/freelancing"

# Operator: outreach drafts and operator notes
remove_dir "$REPO_ROOT/artifacts/operator"

# Distribution: platform-specific distribution drafts
remove_dir "$REPO_ROOT/artifacts/distribution"

# Retrospective: project-specific retrospectives
remove_dir "$REPO_ROOT/artifacts/retrospective"

# Replay: SQL replay files
remove_dir "$REPO_ROOT/artifacts/replay"

# Design: project-specific design docs
remove_dir "$REPO_ROOT/artifacts/design"

# Audits: project-specific audit reports
remove_dir "$REPO_ROOT/artifacts/audits"

# Investigations: project-specific investigation notes
remove_dir "$REPO_ROOT/artifacts/investigations"

# Migrations: project-specific SQL migrations
remove_dir "$REPO_ROOT/artifacts/migrations"

# Site: project-specific showcase/landing page
remove_dir "$REPO_ROOT/artifacts/site"

# Template audit artifacts (not the template dir itself)
remove_dir "$REPO_ROOT/artifacts/template"

# Artifacts-level docs (not the root docs/ site)
remove_dir "$REPO_ROOT/artifacts/docs"

# State: clear the snapshot backup
remove_file "$REPO_ROOT/artifacts/state/latest-snapshot.json"
if [ -d "$REPO_ROOT/artifacts/state" ] && [ ! -f "$REPO_ROOT/artifacts/state/.gitkeep" ]; then
  touch "$REPO_ROOT/artifacts/state/.gitkeep"
fi

# Code: clear project-specific code artifacts
remove_contents "$REPO_ROOT/artifacts/code"

# Root junk files
remove_file "$REPO_ROOT/test.txt"

# Reset issue template config to generic (remove hardcoded AMA/status links)
CONFIG_YML="$REPO_ROOT/.github/ISSUE_TEMPLATE/config.yml"
if [ -f "$CONFIG_YML" ]; then
  cat > "$CONFIG_YML" <<'YAML'
blank_issues_enabled: false
contact_links: []
YAML
  info "Reset .github/ISSUE_TEMPLATE/config.yml to generic defaults"
fi

# ---------- preserve infrastructure (report) ----------

echo ""
info "Infrastructure preserved:"
for item in \
  "artifacts/scripts/" \
  "artifacts/living-board-template/" \
  "dashboard/" \
  "runner/" \
  "docs/" \
  ".github/" \
  "setup.sh" \
  "docker-compose.yml" \
  "CONTRIBUTING.md" \
  "LICENSE"; do
  if [ -e "$REPO_ROOT/$item" ]; then
    kept=$((kept + 1))
    printf '  \033[32m✓\033[0m %s\n' "$item"
  fi
done

# ---------- create empty starter directories ----------

for dir in \
  "$REPO_ROOT/artifacts/content" \
  "$REPO_ROOT/artifacts/research" \
  "$REPO_ROOT/artifacts/logs" \
  "$REPO_ROOT/artifacts/data" \
  "$REPO_ROOT/artifacts/state" \
  "$REPO_ROOT/artifacts/code"; do
  mkdir -p "$dir"
  if [ ! -f "$dir/.gitkeep" ]; then
    touch "$dir/.gitkeep"
  fi
done

# ---------- summary ----------

echo ""
echo "═══════════════════════════════════════════════"
ok "Fork initialization complete!"
echo ""
echo "  Removed:    $removed project-specific files"
echo "  Preserved:  $kept infrastructure components"
echo ""
echo "Next steps:"
echo "  1. Run template-setup.sh to configure your agent:"
echo "       bash artifacts/living-board-template/template-setup.sh"
echo "  2. Copy the generated CLAUDE.md to the repo root:"
echo "       cp artifacts/living-board-template/CLAUDE.md ./CLAUDE.md"
echo "  3. Install the pre-commit hook:"
echo "       bash artifacts/scripts/install-pre-commit-hook.sh"
echo "  4. Commit and push your clean fork"
echo "  5. Set up your Claude Code trigger and run your first cycle!"
echo ""
echo "For the full guide, see artifacts/living-board-template/QUICKSTART.md"
echo "═══════════════════════════════════════════════"
