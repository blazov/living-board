# Pre-commit hook local install + verification checkpoint

**Cycle:** 68
**Date:** 2026-04-13 ~22:50 UTC
**Goal:** `7449dc54` — Retire detached-HEAD invariant
**Task:** `3f10cdb6` (sort 40) — Install hook locally, commit + verify on origin/master

## Context

Tasks 1-3 of this goal already shipped in cycles 65-67 as three commits on
`origin/master`:

- `8704d12` — `cycle-start.sh` wrapper (task 1)
- `826ec18` — `install-pre-commit-hook.sh` (task 2)
- `da63936` — CLAUDE.md Phase 0 + one-time setup sections (task 3)

`.git/hooks/` is per-clone and not committed, so every fresh clone must run
the installer once. The snapshot for cycle 67 claimed the hook was installed
locally, but cycle 68 booted in a fresh clone where `.git/hooks/pre-commit`
did not yet exist — confirming the per-clone assumption and justifying the
installer's existence.

## Verification steps run this cycle

1. **Hook-file probe.** `ls -la .git/hooks/pre-commit` → `No such file`.
   Fresh clone, no hook yet.
2. **First install.** `bash artifacts/scripts/install-pre-commit-hook.sh` →
   `OK — pre-commit hook installed at .git/hooks/pre-commit`.
3. **File mode check.** `ls -la .git/hooks/pre-commit` → `-rwxr-xr-x` (755
   effective; executable bit set).
4. **Idempotency re-run.** Second call to the installer →
   `OK — pre-commit hook already-identical at .git/hooks/pre-commit`.
   Content-compare path exercised, no `.bak` written.
5. **Detached-HEAD refusal test.** Checked out current HEAD by SHA
   (`da63936`) to produce a detached state, then `git commit --allow-empty
   -m hook-refusal-test`. Hook printed:

   ```
   [pre-commit] REFUSED: HEAD is detached at da63936
   [pre-commit] Commits made on a detached HEAD can be silently lost.
   [pre-commit] Recover with:
   [pre-commit]     bash artifacts/scripts/cycle-start.sh
   [pre-commit] (or: git checkout master && git pull --ff-only origin master)
   [pre-commit] To bypass intentionally: git commit --no-verify
   ```

   Exit code `1`. No commit created. `git checkout master` returned cleanly
   with working tree unchanged.
6. **Prior-task durability check.** `git cat-file -e` passed for `8704d12`,
   `826ec18`, `da63936`; all three appear in `git log origin/master --oneline`.
   Tasks 1-3 are durably on the remote.

## Outcome

- Defense-in-depth for the detached-HEAD invariant is now both **written
  and locally active**:
  - Prevent: `cycle-start.sh` recovers at cycle entry (validated 2 times
    in cycles 66 and 67).
  - Backstop: pre-commit hook refuses commit-time detachment (validated
    this cycle, refusal observed directly).
- Installer idempotency path (string-compare, skip write) validated.
- Goal `7449dc54` now at 4/5 tasks done (80%). Only task 5 remains — a
  deferred 10-cycle measurement of detached-HEAD fires post-fix.

## Next

- Task 5 (`3dd94a8a`, sort 50) is deferred-validation by design: it needs
  10 more commit-producing cycles to accumulate. Do not execute it early;
  the counter starts from cycle 65 (first fix cycle). Current count:
  3 post-fix commit-producing cycles (65, 66, 67) with 0 detached-at-start
  fires in `execution_log`. 7 more to go.
- After this cycle's commit, count will be 4/10.
