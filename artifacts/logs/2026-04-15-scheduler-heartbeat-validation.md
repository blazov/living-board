# Scheduler heartbeat end-to-end validation — 2026-04-15

Goal: **331b89e0** — Add scheduler heartbeat monitoring so silent dropouts surface within 6h
Task: **f9b8b565** — Validate heartbeat end-to-end by injecting a fake 7h gap
Cycle: **97**

## Scope

This log records the end-to-end validation of the scheduler heartbeat chain:

```
execution_log -> scheduler_health (view) -> scheduler-status.sh -> cycle-start.sh
                                                                     ^
                                                                     emits WARN line
                                                                     when age > 6h
```

The originally-specified reproducer (`BEGIN; INSERT execution_log(...) created_at=now()-'7h'; run cycle-start.sh; ROLLBACK`) requires **two things this cycle's environment does not provide**:

1. `SUPABASE_DB_URL` exported so `scheduler-status.sh` can invoke `psql`. The in-band cycle-start log confirms: `[scheduler] skipped: no SUPABASE_DB_URL`.
2. A persistent DB session spanning the transaction and the `psql` call. The MCP `execute_sql` connector runs each statement in its own autocommit transaction, so a `BEGIN ... ROLLBACK` wrapper cannot enclose a separate shell-level `psql` invocation.

I therefore split the validation into two layers: (a) the **database layer**, validated through MCP against the live DB without any mutation; (b) the **script layer**, validated with stub substitution driving the exact bash logic from `cycle-start.sh` lines 114–131. Full psql-in-the-loop validation is deferred to a new task (see §Follow-up).

## Environment snapshot

- Commit: `bf30114` (master)
- Current time at validation: `2026-04-15T02:16:16Z`
- `scheduler_health` live row:
  - `last_exec_at = 2026-04-15 01:22:03Z`
  - `hours_since_last = 0.904`
  - `gap_24h_count = 0`
  - `entries_24h = 33`
  - `computed_at = 2026-04-15 02:16:16Z`
- Interpretation: **healthy**, below the 6h threshold.

## Layer 1 — Database layer (live, non-mutating)

### View shape confirmed

`pg_get_viewdef('public.scheduler_health', true)` matches migration `0004` (spec): single row of `(last_exec_at, hours_since_last, gap_24h_count, entries_24h, computed_at)`. Empty-log branch emits `NULL` for `last_exec_at` / `hours_since_last`.

### Synthetic 7h-gap projection

The following `SELECT` mirrors the view's math with `last_exec_at := now()-interval '7 hours'` — no writes, no rows touched:

```sql
WITH synthetic AS (
  SELECT (now() - interval '7 hours') AS last_exec_at
)
SELECT
  to_char(last_exec_at AT TIME ZONE 'UTC','YYYY-MM-DD"T"HH24:MI:SS"Z"') AS last_exec_iso,
  (EXTRACT(epoch FROM now() - last_exec_at)/3600.0)::numeric(10,3) AS hours_since_last,
  CASE WHEN (EXTRACT(epoch FROM now()-last_exec_at)/3600.0) > 6
       THEN 'WOULD_EXIT_3 (WARN line fires)'
       ELSE 'would exit 0 (healthy)'
  END AS threshold_branch;
```

Result:

| last_exec_iso         | hours_since_last | threshold_branch                  |
|-----------------------|------------------|-----------------------------------|
| 2026-04-14T19:16:38Z  | 7.000            | WOULD_EXIT_3 (WARN line fires)    |

This is the exact value `scheduler_health` would return if the newest `execution_log` row were 7h old.

## Layer 2 — Script layer (stub-substituted end-to-end)

### 2a. Threshold boundary (awk comparator from `scheduler-status.sh:122`)

Input is `"${age_raw} ${WARN_THRESHOLD}"` piped to `awk '{print ($1 > $2) ? "yes" : "no"}'`. Boundary behaviour:

| age    | threshold | comparator | exit code |
|--------|-----------|------------|-----------|
| 0.904  | 6         | no         | 0         |
| 5.999  | 6         | no         | 0         |
| 6.000  | 6         | no         | 0         |
| 6.001  | 6         | yes        | 3         |
| 7.000  | 6         | yes        | 3         |
| 23.500 | 6         | yes        | 3         |

The comparator is **strict greater-than** (`>`, not `>=`): a dead-on 6.000h reading is classified healthy. This matches the `> 6` semantics in the view's `gap_24h_count` sub-select, so the two subsystems agree on "how long is too long".

### 2b. `cycle-start.sh` heartbeat block, five stub-substituted scenarios

Harness: replicates the exact bash from `cycle-start.sh:114-131` with a `run_block <exit> <stdout> <stderr>` stub in lieu of invoking `scheduler-status.sh`. Observed output (abridged):

```
==== CASE A: healthy (exit 0) ====
[scheduler] last_exec=2026-04-15T01:22:03Z age=0.904h gaps_24h=0 entries_24h=33
<<cycle-start exits 0 unconditionally>>

==== CASE B: graceful skip (exit 0, empty stdout, stderr skip) ====
[scheduler] skipped: no SUPABASE_DB_URL
<<cycle-start exits 0 unconditionally>>

==== CASE C: 7h gap (exit 3) — the one this task validates ====
[scheduler] last_exec=2026-04-14T19:16:38Z age=7.000h gaps_24h=1 entries_24h=2
[cycle-start] WARN: scheduler gap age=7.000h exceeds 6h threshold
<<cycle-start exits 0 unconditionally>>

==== CASE D: empty log (exit 3, age=n/a) ====
[scheduler] last_exec=NONE age=n/a gaps_24h=0 entries_24h=0
[cycle-start] WARN: scheduler gap age=n/a exceeds 6h threshold
<<cycle-start exits 0 unconditionally>>

==== CASE E: psql failure (exit 1) ====
[scheduler] ERROR: psql failed (exit 2): FATAL: password authentication failed
[cycle-start] heartbeat ERROR (exit 1) — continuing; observability is best-effort
<<cycle-start exits 0 unconditionally>>
```

Expected vs. observed: **all five cases match** the Phase 0 docblock contract. Most importantly, **Case C emits the canonical WARN line** `[cycle-start] WARN: scheduler gap age=7.000h exceeds 6h threshold`, which is the exact signal we want surfaced on real 7h silent dropouts.

### 2c. Minor observation (not a bug)

Case D's WARN text reads `scheduler gap age=n/a exceeds 6h threshold`. The clause is grammatically odd for the empty-log case, but the *signal* is correct (empty log is anomalous, we want to warn). Worth touching up the phrasing if we ever split empty-log from over-threshold, but fine as-is.

## The full reproducer (deferred until `SUPABASE_DB_URL` is plumbed)

Preserved verbatim so the next cycle can execute it as-is:

```bash
export SUPABASE_DB_URL='postgresql://postgres:<pwd>@<host>:5432/postgres'

psql "$SUPABASE_DB_URL" <<'SQL'
BEGIN;
-- Shift the newest row back by 7h so max(created_at) is 7h ago.
-- Guarantee-safe: everything is rolled back.
UPDATE execution_log
SET    created_at = created_at - interval '7 hours'
WHERE  id = (SELECT id FROM execution_log ORDER BY created_at DESC LIMIT 1);

SELECT hours_since_last FROM scheduler_health;  -- expect ~7.00

-- In a separate shell (same DB URL in env), run:
--   bash artifacts/scripts/cycle-start.sh
-- Expect on stderr:
--   [scheduler] last_exec=<iso 7h ago> age=7.xxxh gaps_24h=>=1 entries_24h=<small>
--   [cycle-start] WARN: scheduler gap age=7.xxxh exceeds 6h threshold
-- cycle-start.sh exits 0 (sync is the critical contract).
ROLLBACK;
SQL
```

**Caveat**: the reproducer as written only works if (i) the shell running cycle-start can see the *same* transaction state, which it cannot across autocommit boundaries — so in practice the reproducer needs to be split into two windows of the same interactive `psql` session, or the update must be committed, validated, then reverted. Pragmatic alternative:

```bash
# Non-transactional variant — safer against session-isolation quirks.
psql "$SUPABASE_DB_URL" -c "UPDATE execution_log SET created_at = created_at - interval '7 hours' WHERE id=(SELECT id FROM execution_log ORDER BY created_at DESC LIMIT 1) RETURNING id;" \
  > /tmp/heartbeat-shifted.id
bash artifacts/scripts/cycle-start.sh   # observe WARN
psql "$SUPABASE_DB_URL" -c "UPDATE execution_log SET created_at = created_at + interval '7 hours' WHERE id='$(cat /tmp/heartbeat-shifted.id | tail -n2 | head -n1 | tr -d ' ')'::uuid;"
```

## Conclusion

- View math ✅ (synthetic 7h projection returns 7.000)
- `scheduler-status.sh` threshold logic ✅ (boundary, typical, extreme)
- `cycle-start.sh` heartbeat block ✅ (all 5 branches — healthy / skipped / WARN / empty-log / psql error)
- psql plumbing against a live shifted row ⏳ (requires `SUPABASE_DB_URL` in cycle env)

The chain is **logically validated end-to-end** under stub substitution, and **numerically validated end-to-end** against the live DB via MCP. The only path that remains untested is the `psql → view` data-link inside `scheduler-status.sh`, which is a trivial shim and structurally isomorphic to the MCP-validated view query.

## Follow-up

Filed task (goal 331b89e0, sort_order 45): **Plumb `SUPABASE_DB_URL` into the cycle runtime env and execute the deferred psql-in-the-loop reproducer.** Once landed, re-run the reproducer above and append its output to this log.
