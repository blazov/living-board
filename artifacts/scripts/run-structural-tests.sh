#!/usr/bin/env bash
# run-structural-tests.sh
#
# Entry point that runs every structural-invariant test script and
# reports a pass/fail summary.  Designed for CI, pre-commit hooks,
# or manual runs.
#
# EXIT CODES
#   0   all suites passed
#   1   one or more suites failed
#
# USAGE
#   bash artifacts/scripts/run-structural-tests.sh           # run all
#   bash artifacts/scripts/run-structural-tests.sh --quiet   # summary only

set -u

repo_root="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
quiet=false
[[ "${1:-}" == "--quiet" ]] && quiet=true

# ---- Test suites (add new scripts here) ----
SUITES=(
  "artifacts/scripts/test-cycle-start-structure.sh"
  "artifacts/scripts/test-agent-structure.sh"
  "artifacts/scripts/test-scheduler-status-structure.sh"
  "artifacts/scripts/test-claude-md-structure.sh"
  "artifacts/scripts/test-schema-structure.sh"
)

passed=0
failed=0
failed_names=()

echo "========================================"
echo " Structural-Invariant Test Runner"
echo "========================================"
echo ""

for suite in "${SUITES[@]}"; do
  script="$repo_root/$suite"
  name="$(basename "$suite" .sh)"

  if [ ! -f "$script" ]; then
    echo "SKIP  $name  (file not found: $suite)"
    failed=$((failed + 1))
    failed_names+=("$name [missing]")
    continue
  fi

  if $quiet; then
    output=$(bash "$script" 2>&1)
    rc=$?
  else
    echo "---- $name ----"
    bash "$script"
    rc=$?
    echo ""
  fi

  if [ $rc -eq 0 ]; then
    passed=$((passed + 1))
    $quiet && echo "PASS  $name"
  else
    failed=$((failed + 1))
    failed_names+=("$name [exit $rc]")
    $quiet && echo "FAIL  $name  (exit $rc)"
    $quiet && echo "$output" | grep -E "MISS|FAIL" | head -5
  fi
done

total=$((passed + failed))

echo "========================================"
echo " Results: $passed/$total passed"
echo "========================================"

if [ $failed -gt 0 ]; then
  echo ""
  echo "Failed suites:"
  for f in "${failed_names[@]}"; do
    echo "  - $f"
  done
  echo ""
  exit 1
fi

echo "All structural-invariant tests passed."
exit 0
