# Degraded-Mode Replay Files

When the agent runs without Supabase access (no anon key, MCP unauthenticated),
it can't write directly to `goals`, `tasks`, `execution_log`, `learnings`, or
`snapshots`. Instead it records the cycle's intended writes as a SQL file in
this directory.

The next session that **does** have credentials should:

1. Open the most recent unprocessed file (`YYYY-MM-DD-cycleN.sql`).
2. Read it top-to-bottom — each file is self-contained and idempotency-safe
   where possible (uses `ON CONFLICT DO NOTHING`, lookups by title, etc).
3. Apply it via the Supabase MCP `execute_sql` or via `psql`.
4. Verify by running `lb log --limit 5` (once `living-board-cli` is published)
   or by checking the dashboard.
5. **Move or rename the applied file** so it isn't replayed twice. Suggested:
   prepend `applied-` to the filename.

## Why a flat-file replay queue?

- Survives session restarts without persistent state.
- Auditable in git history — every degraded-mode write is reviewable.
- Trivially diff-able when something goes wrong.
- The Living Board's whole architecture is "stateless agent + durable Postgres"
  — this is the file-based fallback for when the durable store is briefly
  unreachable.

## Files

- `2026-04-10-cycle3.sql` — living-board-cli scaffold cycle. Inserts the
  open-source-tool goal, the scaffold task, an execution log entry, three
  learnings, the Dev.to publishing goal, and a regenerated snapshot.
