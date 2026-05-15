#!/usr/bin/env bash
set -euo pipefail

# Commits and pushes artifact changes produced by the agent cycle.
# Expected env vars: BRANCH, WORKING_DIR

BRANCH="${BRANCH:-master}"
WORKING_DIR="${WORKING_DIR:-.}"

cd "${WORKING_DIR}"

git config user.name "living-board-agent"
git config user.email "agent@living-board.dev"

if [ -n "$(git status --porcelain artifacts/ 2>/dev/null)" ]; then
  git add artifacts/

  CYCLE="?"
  if [ -f artifacts/state/latest-snapshot.json ]; then
    CYCLE=$(python3 -c "import json; print(json.load(open('artifacts/state/latest-snapshot.json')).get('snapshot',{}).get('cycle_count','?'))" 2>/dev/null || echo "?")
  fi

  git commit -m "Agent cycle ${CYCLE} artifacts"
  git push origin "${BRANCH}"

  echo "artifacts_changed=true" >> "$GITHUB_OUTPUT"
  echo "Committed and pushed artifact changes (cycle ${CYCLE})"
else
  echo "artifacts_changed=false" >> "$GITHUB_OUTPUT"
  echo "No artifact changes to commit"
fi
