#!/usr/bin/env bash
# install-pre-commit-hook.sh
#
# Installs a git pre-commit hook that refuses commits when HEAD is detached.
# Part of goal 7449dc54 (retire the detached-HEAD-at-cycle-start invariant):
# complements artifacts/scripts/cycle-start.sh. Where cycle-start.sh prevents
# detached HEAD at the *start* of a cycle, this hook is a defense-in-depth
# backstop that refuses the *commit itself* if somehow HEAD is still detached.
#
# .git/hooks is per-clone and not tracked by git, so this installer must be
# run once per clone. It is idempotent and safe to re-run — subsequent runs
# will report whether the hook was already present, overwritten, or created
# fresh, and whether the contents changed.
#
# Exit codes:
#   0   success — hook installed (or already identical)
#   1   filesystem error (cannot write hook, permissions, etc.)
#   2   not in a git repository
#
# Usage (run once per clone):
#   bash artifacts/scripts/install-pre-commit-hook.sh
#
# To uninstall: rm .git/hooks/pre-commit
#
# To bypass intentionally (should be rare): git commit --no-verify

set -u

repo_root="$(git rev-parse --show-toplevel 2>/dev/null)"
if [ -z "$repo_root" ]; then
  echo "[install-hook] ERROR: not inside a git repository" >&2
  exit 2
fi
cd "$repo_root" || { echo "[install-hook] ERROR: cannot cd to $repo_root" >&2; exit 1; }

hooks_dir="$(git rev-parse --git-path hooks 2>/dev/null)"
if [ -z "$hooks_dir" ]; then
  echo "[install-hook] ERROR: could not resolve .git/hooks path" >&2
  exit 1
fi
mkdir -p "$hooks_dir" || { echo "[install-hook] ERROR: mkdir -p $hooks_dir failed" >&2; exit 1; }

hook_path="$hooks_dir/pre-commit"

# The hook body. Kept minimal and self-contained so it has no runtime
# dependencies on the repo's script directory. If HEAD is detached, refuse
# the commit and print the canonical recovery command.
read -r -d '' hook_body <<'HOOK' || true
#!/usr/bin/env bash
# pre-commit hook — refuse commits on detached HEAD.
# Installed by artifacts/scripts/install-pre-commit-hook.sh (goal 7449dc54).
# To bypass intentionally: git commit --no-verify
set -u

ref="$(git symbolic-ref --short -q HEAD || true)"
if [ -z "$ref" ]; then
  sha="$(git rev-parse --short HEAD 2>/dev/null || echo '?')"
  echo "[pre-commit] REFUSED: HEAD is detached at $sha" >&2
  echo "[pre-commit] Commits made on a detached HEAD can be silently lost." >&2
  echo "[pre-commit] Recover with:" >&2
  echo "[pre-commit]     bash artifacts/scripts/cycle-start.sh" >&2
  echo "[pre-commit] (or: git checkout master && git pull --ff-only origin master)" >&2
  echo "[pre-commit] To bypass intentionally: git commit --no-verify" >&2
  exit 1
fi

exit 0
HOOK

# Decide action: fresh install, no-op, or overwrite.
action="installed"
if [ -e "$hook_path" ]; then
  existing="$(cat "$hook_path" 2>/dev/null || echo "")"
  if [ "$existing" = "$hook_body" ]; then
    action="already-identical"
  else
    action="overwritten"
    # Back up the previous hook so nothing is silently clobbered.
    backup_path="$hook_path.bak.$(date -u +%Y%m%dT%H%M%SZ)"
    if ! cp "$hook_path" "$backup_path"; then
      echo "[install-hook] ERROR: failed to back up existing hook to $backup_path" >&2
      exit 1
    fi
    echo "[install-hook] backed up existing hook to $backup_path"
  fi
fi

if [ "$action" != "already-identical" ]; then
  if ! printf '%s\n' "$hook_body" > "$hook_path"; then
    echo "[install-hook] ERROR: failed to write $hook_path" >&2
    exit 1
  fi
fi

if ! chmod +x "$hook_path"; then
  echo "[install-hook] ERROR: failed to chmod +x $hook_path" >&2
  exit 1
fi

echo "[install-hook] OK — pre-commit hook $action at $hook_path"
echo "[install-hook] Test it with: git commit --allow-empty -m test   (on master vs detached)"
exit 0
