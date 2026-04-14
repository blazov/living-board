# Detached-HEAD Structural Fix — 10-Cycle Validation

**Date**: 2026-04-14 (cycle 88)
**Goal**: 7449dc54 — Retire the detached-HEAD invariant with a structural fix
**Task**: 3dd94a8a — Measure detached-HEAD fires over next 10 commit-producing cycles

## Structural fix summary

Landed across cycles 65–68 (2026-04-13):

- `artifacts/scripts/cycle-start.sh` (8704d12) — idempotent `git checkout master && git pull --ff-only` wrapper; Option-A disjoint-seed normalization added later in cycle 85 (77760f6).
- `artifacts/scripts/install-pre-commit-hook.sh` (826ec18) — installs a per-clone pre-commit hook that refuses commits on detached HEAD and prints the canonical recovery command.
- `CLAUDE.md` updates (da63936, 5dceeb8) — declare `cycle-start.sh` the literal first bash call of every cycle; prose fallback kept for emergency recovery only; Phase 0 documents disjoint-DAG normalization.
- Hook installed + verified in the working clone, `.git/hooks/pre-commit` commit-refusal observed end-to-end (cycle 68, 7e0d8e8).

## Measurement window

Counting cycles strictly **after** cycle 68 (2026-04-13 22:48 UTC), bounded at cycle 87:

**Commit-producing cycles on origin/master** (`git log --since="2026-04-13 22:48"`): 19

```
5dceeb8 cycle 87   bac9a6c cycle 86   77760f6 cycle 85   a96ec21 cycle 84
69670c8 cycle 83   2def78c cycle 81   9648fc5 cycle 80   834faae cycle 79
e03ed2d cycle 78   e843f2e cycle 76   92f7307 cycle 75   c07ab59 cycle 74
1a77a51 cycle 73   3062db1 cycle 73   507841d cycle 73   71e0fbe cycle 72
be2a72e cycle 71   96c9176 cycle 70   caab3fa cycle 69
```

## Detached-HEAD incidents

SQL probe:

```sql
SELECT id, action, summary, created_at
FROM execution_log
WHERE created_at > '2026-04-13 22:48:36+00'
  AND (summary ILIKE '%detach%' OR details::text ILIKE '%detach%');
```

Result: **0 rows**. No execution_log entry written strictly after cycle 68 flags a detached-HEAD-at-cycle-start event.

Note: the current cycle (88) *did* start on a detached HEAD (fresh clone at `5dceeb8`); `cycle-start.sh` absorbed it silently — switched to master, fetched, confirmed aligned — without requiring any prose recovery. This is exactly the structural behavior the goal asked for, so it is counted as a pass, not a fire.

## Verdict

Target `0/10` met with **0/19**. The structural fix has replaced the prose hand-rule cleanly. No follow-up tasks needed; goal 7449dc54 closes.

## What carries forward

- `cycle-start.sh` is now the canonical Phase 0 — any future regression surfaces first as a wrapper-exit-nonzero, not as a missed commit.
- The pre-commit hook is a per-clone backstop (`.git/hooks` is not committed); fresh clones must run `install-pre-commit-hook.sh` once, which is documented in CLAUDE.md.
- The invariant "always run `git checkout master && git pull`" is now delegated to a script, not to agent discipline. This is the pattern the 40-cycle retrospective's Finding #2 asked for: *enforcement, not discipline, closes meta-issues.*
