#!/usr/bin/env bash
# test-fork-flow.sh
#
# Validates the fork flow without destructive side effects.
# Tests: file existence, template substitution, schema SQL syntax,
#        seed-data consistency, fork-init target coverage.
#
# Usage: bash artifacts/scripts/test-fork-flow.sh
# Exit: 0 if all checks pass, 1 if any fail.

set -u

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
TEMPLATE_DIR="$REPO_ROOT/artifacts/living-board-template"

pass=0
fail=0
warn=0

ok()   { pass=$((pass + 1)); printf '  \033[32m✓\033[0m %s\n' "$1"; }
fail() { fail=$((fail + 1)); printf '  \033[31m✗\033[0m %s\n' "$1"; }
skip() { warn=$((warn + 1)); printf '  \033[33m⊘\033[0m %s\n' "$1"; }

# ── 1. Required files exist ──────────────────────────────────────────

echo ""
echo "1. Required template files"
echo "──────────────────────────"

for f in fork-init.sh template-setup.sh schema.sql seed-data.sql \
         CLAUDE.md.template CLAUDE.md.minimal QUICKSTART.md README.md; do
  if [ -f "$TEMPLATE_DIR/$f" ]; then
    ok "$f exists"
  else
    fail "$f MISSING"
  fi
done

for f in fork-init.sh template-setup.sh; do
  if [ -x "$TEMPLATE_DIR/$f" ]; then
    ok "$f is executable"
  else
    fail "$f is NOT executable"
  fi
done

# ── 2. Template substitution ─────────────────────────────────────────

echo ""
echo "2. Template substitution (CLAUDE.md.template)"
echo "──────────────────────────────────────────────"

TMPDIR_TEST="$(mktemp -d)"
trap 'rm -rf "$TMPDIR_TEST"' EXIT

sed \
  -e 's|{{SUPABASE_PROJECT_ID}}|test-proj-xyz|g' \
  -e 's|{{BRANCH_NAME}}|main|g' \
  -e 's|{{AGENTMAIL_ADDRESS}}|me@agent.test|g' \
  "$TEMPLATE_DIR/CLAUDE.md.template" > "$TMPDIR_TEST/step1.md"

TOOLS="- WebSearch\n- Bash\n- Read/Write/Edit"
awk -v tools="$TOOLS" '{gsub(/\{\{AVAILABLE_TOOLS\}\}/, tools); print}' \
  "$TMPDIR_TEST/step1.md" > "$TMPDIR_TEST/claude-full.md"

remaining=$(grep -c '{{' "$TMPDIR_TEST/claude-full.md" 2>/dev/null || true)
remaining=${remaining:-0}
if [ "$remaining" -eq 0 ]; then
  ok "All placeholders substituted (full template)"
else
  fail "$remaining placeholder(s) remain in generated CLAUDE.md"
  grep -n '{{' "$TMPDIR_TEST/claude-full.md"
fi

if grep -q 'test-proj-xyz' "$TMPDIR_TEST/claude-full.md"; then
  ok "SUPABASE_PROJECT_ID substituted correctly"
else
  fail "SUPABASE_PROJECT_ID not found in output"
fi

if grep -q 'cycle-start.sh main' "$TMPDIR_TEST/claude-full.md"; then
  ok "BRANCH_NAME substituted correctly"
else
  fail "BRANCH_NAME not found in output"
fi

# Minimal template
sed \
  -e 's|{{SUPABASE_PROJECT_ID}}|test-proj-xyz|g' \
  -e 's|{{BRANCH_NAME}}|main|g' \
  -e 's|{{AGENTMAIL_ADDRESS}}|me@agent.test|g' \
  "$TEMPLATE_DIR/CLAUDE.md.minimal" > "$TMPDIR_TEST/claude-min.md"

TOOLS_LINE="- Default tools"
awk -v tools="$TOOLS_LINE" '{gsub(/\{\{AVAILABLE_TOOLS\}\}/, tools); print}' \
  "$TMPDIR_TEST/claude-min.md" > "$TMPDIR_TEST/claude-min-final.md"

remaining_min=$(grep -c '{{' "$TMPDIR_TEST/claude-min-final.md" 2>/dev/null || true)
remaining_min=${remaining_min:-0}
if [ "$remaining_min" -eq 0 ]; then
  ok "All placeholders substituted (minimal template)"
else
  fail "$remaining_min placeholder(s) remain in minimal CLAUDE.md"
fi

# Empty AGENTMAIL_ADDRESS
sed \
  -e 's|{{SUPABASE_PROJECT_ID}}|test-proj-xyz|g' \
  -e 's|{{BRANCH_NAME}}|main|g' \
  -e 's|{{AGENTMAIL_ADDRESS}}||g' \
  "$TEMPLATE_DIR/CLAUDE.md.template" > "$TMPDIR_TEST/empty-agent.md"

remaining_empty=$(grep -c '{{AVAILABLE_TOOLS}}' "$TMPDIR_TEST/empty-agent.md" 2>/dev/null || echo 0)
if [ "$remaining_empty" -le 1 ]; then
  ok "Empty AGENTMAIL_ADDRESS produces valid output"
else
  fail "Empty AGENTMAIL_ADDRESS left extra placeholders"
fi

# ── 3. Schema SQL structure ──────────────────────────────────────────

echo ""
echo "3. Schema SQL structure"
echo "───────────────────────"

tables_if=$(grep -c 'CREATE TABLE IF NOT EXISTS' "$TEMPLATE_DIR/schema.sql")
tables_total=$(grep -c 'CREATE TABLE' "$TEMPLATE_DIR/schema.sql")

if [ "$tables_if" -eq "$tables_total" ]; then
  ok "All $tables_total CREATE TABLE use IF NOT EXISTS"
else
  fail "$tables_if/$tables_total tables use IF NOT EXISTS"
fi

indexes_if=$(grep -c 'CREATE INDEX IF NOT EXISTS' "$TEMPLATE_DIR/schema.sql")
indexes_total=$(grep -c 'CREATE INDEX' "$TEMPLATE_DIR/schema.sql")

if [ "$indexes_if" -eq "$indexes_total" ]; then
  ok "All $indexes_total CREATE INDEX use IF NOT EXISTS"
else
  fail "$indexes_if/$indexes_total indexes use IF NOT EXISTS"
fi

if grep -q 'CREATE EXTENSION IF NOT EXISTS pgcrypto' "$TEMPLATE_DIR/schema.sql"; then
  ok "pgcrypto extension loaded for gen_random_uuid()"
else
  fail "pgcrypto extension not loaded"
fi

expected_tables="goals tasks execution_log learnings snapshots goal_comments agent_config"
for tbl in $expected_tables; do
  if grep -q "CREATE TABLE IF NOT EXISTS $tbl" "$TEMPLATE_DIR/schema.sql"; then
    ok "Table '$tbl' defined"
  else
    fail "Table '$tbl' MISSING from schema"
  fi
done

if grep -q 'CREATE OR REPLACE VIEW.*scheduler_health' "$TEMPLATE_DIR/schema.sql"; then
  ok "scheduler_health view defined"
else
  fail "scheduler_health view MISSING"
fi

if grep -q 'goals_set_completed_at' "$TEMPLATE_DIR/schema.sql"; then
  ok "goals_set_completed_at trigger defined"
else
  fail "goals_set_completed_at trigger MISSING"
fi

# ── 4. Seed data consistency ─────────────────────────────────────────

echo ""
echo "4. Seed data consistency"
echo "────────────────────────"

seed_inserts=$(grep -c '^INSERT INTO' "$TEMPLATE_DIR/seed-data.sql")
seed_conflicts=$(grep -c '^ON CONFLICT DO NOTHING' "$TEMPLATE_DIR/seed-data.sql")

if [ "$seed_inserts" -eq "$seed_conflicts" ]; then
  ok "All $seed_inserts INSERT statements have ON CONFLICT DO NOTHING"
else
  fail "$seed_conflicts/$seed_inserts inserts have ON CONFLICT"
fi

goal_uuid="00000000-0000-0000-0000-000000000001"
goal_refs=$(grep -c "$goal_uuid" "$TEMPLATE_DIR/seed-data.sql")
if [ "$goal_refs" -ge 3 ]; then
  ok "Seed goal UUID referenced in goals, tasks, and learnings ($goal_refs refs)"
else
  fail "Goal UUID not consistently referenced ($goal_refs refs, expected ≥3)"
fi

for tbl in goals tasks learnings; do
  if grep -q "INSERT INTO $tbl" "$TEMPLATE_DIR/seed-data.sql"; then
    ok "Seed data for '$tbl'"
  else
    skip "No seed data for '$tbl'"
  fi
done

# ── 5. fork-init.sh coverage ─────────────────────────────────────────

echo ""
echo "5. fork-init.sh target coverage"
echo "────────────────────────────────"

clean_dirs="artifacts/content artifacts/research artifacts/logs artifacts/data artifacts/metrics artifacts/code"
remove_dirs="artifacts/substack artifacts/freelancing artifacts/operator artifacts/distribution artifacts/retrospective artifacts/replay artifacts/design artifacts/audits artifacts/investigations artifacts/template artifacts/docs"

total_clean=0
for dir in $clean_dirs; do
  full="$REPO_ROOT/$dir"
  if [ -d "$full" ]; then
    count=$(find "$full" -type f ! -name '.gitkeep' 2>/dev/null | wc -l)
    total_clean=$((total_clean + count))
  fi
done

total_remove=0
for dir in $remove_dirs; do
  full="$REPO_ROOT/$dir"
  if [ -d "$full" ]; then
    count=$(find "$full" -type f 2>/dev/null | wc -l)
    total_remove=$((total_remove + count))
  fi
done

echo "  Would clean: $total_clean files from content dirs"
echo "  Would remove: $total_remove files from project dirs"
ok "fork-init targets $(($total_clean + $total_remove)) total project-specific files"

infra_dirs="artifacts/scripts artifacts/living-board-template dashboard runner docs .github"
for dir in $infra_dirs; do
  # Use word-boundary matching: "docs" should not match "artifacts/docs"
  if grep -qE "remove_(contents|dir|file).*\"\\\$REPO_ROOT/$dir\"" "$TEMPLATE_DIR/fork-init.sh" 2>/dev/null; then
    fail "fork-init.sh would DELETE infrastructure dir: $dir"
  else
    ok "Infrastructure preserved: $dir"
  fi
done

# ── 6. cycle-start.sh branch argument ────────────────────────────────

echo ""
echo "6. cycle-start.sh branch argument"
echo "──────────────────────────────────"

cs="$REPO_ROOT/artifacts/scripts/cycle-start.sh"
if [ -f "$cs" ]; then
  if grep -q 'BRANCH="${1:-master}"' "$cs" || grep -q 'BRANCH="${1:-' "$cs"; then
    ok "cycle-start.sh accepts branch argument (\$1)"
  else
    fail "cycle-start.sh does NOT accept branch argument"
  fi

  if grep -q 'git checkout "$BRANCH"' "$cs"; then
    ok "cycle-start.sh uses \$BRANCH for checkout"
  else
    fail "cycle-start.sh does not use \$BRANCH for checkout"
  fi

  if grep -q 'git fetch origin "$BRANCH"' "$cs"; then
    ok "cycle-start.sh uses \$BRANCH for fetch"
  else
    fail "cycle-start.sh does not use \$BRANCH for fetch"
  fi
else
  fail "cycle-start.sh not found"
fi

# ── 7. CLAUDE.md.minimal critical sections ───────────────────────────

echo ""
echo "7. CLAUDE.md.minimal critical sections"
echo "───────────────────────────────────────"

min="$TEMPLATE_DIR/CLAUDE.md.minimal"
for section in "Supabase Project" "Phase 0" "Phase 1" "Phase 2" "Phase 3" "Phase 4" "Goal Decomposition" "Rules"; do
  if grep -q "$section" "$min"; then
    ok "Minimal has section: $section"
  else
    fail "Minimal MISSING section: $section"
  fi
done

# ── Summary ──────────────────────────────────────────────────────────

echo ""
echo "═══════════════════════════════════════════════"
printf "Results: \033[32m%d passed\033[0m, \033[31m%d failed\033[0m, \033[33m%d skipped\033[0m\n" "$pass" "$fail" "$warn"
echo "═══════════════════════════════════════════════"

if [ "$fail" -gt 0 ]; then
  exit 1
fi
exit 0
