# Cycle-start heartbeat integration — 2026-04-15

Task: `d17cc5a2` (goal `331b89e0` — scheduler heartbeat monitoring)
Cycle: 96

## What changed

1. `artifacts/scripts/cycle-start.sh` — appended a heartbeat block after the
   existing sync logic. It invokes `scheduler-status.sh --warn-threshold=6`,
   prints its one-line summary, and branches on exit code.
2. `CLAUDE.md` — Phase 0 docblock now documents the heartbeat line so future
   cycles know the signal is already in the preamble and do not need to
   query `scheduler_health` themselves in Phase 1.

## Exit-code wiring (cycle-start always exits 0 on sync success)

| scheduler-status exit | cycle-start action                                              |
|-----------------------|-----------------------------------------------------------------|
| 0 (healthy or SUPABASE_DB_URL unset) | prints summary (or skip note), continues     |
| 1 (psql failure)      | prints `[cycle-start] heartbeat ERROR (exit 1) — continuing…`   |
| 2 (usage error)       | prints `[cycle-start] heartbeat ERROR (exit 2) — continuing…`   |
| 3 (gap > threshold)   | prints `[cycle-start] WARN: scheduler gap age=<N>h exceeds 6h threshold` to stderr |

In every case cycle-start still exits 0 (the sync contract is what matters).

## Validation

Exercised all four branches by substituting a stub `scheduler-status.sh` that
exits with a fixed code and a known summary, then running `cycle-start.sh`.

### Branch: no SUPABASE_DB_URL (real script, graceful skip)

```
[cycle-start] OK — ref=master sha=9b56e3e
[scheduler] skipped: no SUPABASE_DB_URL
EXIT=0
```

### Branch: exit=3 (WARN)

Stub: `echo "[scheduler] last_exec=2026-04-14T18:00:00Z age=7.250h gaps_24h=1 entries_24h=3"; exit 3`

```
[cycle-start] OK — ref=master sha=9b56e3e
[scheduler] last_exec=2026-04-14T18:00:00Z age=7.250h gaps_24h=1 entries_24h=3
[cycle-start] WARN: scheduler gap age=7.250h exceeds 6h threshold
raw_exit=0
```

### Branch: exit=1 (psql error)

Stub: `echo "[scheduler] ERROR: psql failed ..." >&2; exit 1`

```
[cycle-start] OK — ref=master sha=9b56e3e
[scheduler] ERROR: psql failed (exit 2): could not connect
[cycle-start] heartbeat ERROR (exit 1) — continuing; observability is best-effort
raw_exit=0
```

### Branch: exit=0 (healthy)

```
[cycle-start] OK — ref=master sha=9b56e3e
[scheduler] last_exec=2026-04-15T00:25:43Z age=0.862h gaps_24h=0 entries_24h=34
raw_exit=0
```

Also: `bash -n artifacts/scripts/cycle-start.sh` → OK.

## Follow-up

Task `f9b8b565` — end-to-end validation with a real 7h gap injected into
`execution_log` via `BEGIN; INSERT … created_at=now()-'7h'::interval …; ROLLBACK;`
while `SUPABASE_DB_URL` is set. Deferred to next cycle (needs the DB URL in
this environment, not configured here).

Task `fb266a37` — passive-monitor 10 cycles on origin/master for false
positives. Accumulates naturally over the next ~10h of wall-clock.
