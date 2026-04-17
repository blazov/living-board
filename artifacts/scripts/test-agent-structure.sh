#!/usr/bin/env bash
# test-agent-structure.sh
#
# Structural guard for runner/agent.py.
#
# Goal ef48bb21, task sort_order=20.
#
# Follows the reference pattern from test-cycle-start-structure.sh.
# See artifacts/docs/structural-anchor-inventory.md §1 for the
# anchor rationale and invariant descriptions.
#
# EXIT CODES
#   0   all anchors present, syntax ok
#   1   one or more anchors missing
#   2   python syntax error
#   3   the file does not exist
#
# USAGE
#   bash artifacts/scripts/test-agent-structure.sh
#   bash artifacts/scripts/test-agent-structure.sh path/to/agent.py

set -u

repo_root="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
target="${1:-$repo_root/runner/agent.py}"

if [ ! -f "$target" ]; then
  echo "[test-agent-structure] FAIL: target file does not exist: $target" >&2
  exit 3
fi

if ! python3 -m py_compile "$target" 2>/tmp/agent-py-syntax-err; then
  echo "[test-agent-structure] FAIL: python syntax error in $target" >&2
  sed 's/^/  /' /tmp/agent-py-syntax-err >&2 || true
  exit 2
fi

# ---------------------------------------------------------------------------
# Canonical anchors from structural-anchor-inventory.md §1.
# Format: "LABEL|ANCHOR" — grep -F match required.
# ---------------------------------------------------------------------------
ANCHORS=(
  "imports:phase-orient|from .phases import orient"
  "imports:phase-reflect|reflect, check_email"
  "credential-banner:env-vars|CREDENTIAL_ENV_VARS"
  "credential-banner:emit-fn|def emit_credentials_banner"
  "credential-banner:call|emit_credentials_banner()"
  "phase:orient|Phase 1: Orient"
  "phase:decide|Phase 2: Decide"
  "phase:execute|Phase 3: Execute"
  "phase:record|Phase 4: Record"
  "reflection:gate|needs_reflection"
  "email:gate|needs_email_check"
  "decide:idle|action == \"idle\""
  "decide:decompose|action == \"decompose_goal\""
  "class:runner|class AgentRunner"
)

missing=0
echo "[test-agent-structure] checking $target"
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

min_lines=100
actual_lines=$(wc -l < "$target")
if [ "$actual_lines" -lt "$min_lines" ]; then
  echo "  MISS  sanity:min-line-count  [expected >=$min_lines, got $actual_lines]" >&2
  missing=$((missing + 1))
else
  echo "  ok    sanity:min-line-count  [$actual_lines >= $min_lines]"
fi

if [ "$missing" -gt 0 ]; then
  echo "[test-agent-structure] FAIL: $missing anchor(s) missing — runner/agent.py is structurally incomplete" >&2
  exit 1
fi

echo "[test-agent-structure] OK — all ${#ANCHORS[@]} anchors + sanity check present"
exit 0
