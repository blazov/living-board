# Fresh-Supabase Audit — schema.sql + setup.sh

**Date:** 2026-04-15
**Cycle:** 102
**Goal / Task:** 106eb0b9 / b296d977 (sort 30) — audit items **3** and **5**
**Method:** credential-free desk-check of `artifacts/living-board-template/schema.sql`, `setup.sh`,
and `artifacts/living-board-template/seed-data.sql`, assuming a brand-new Supabase project
(nothing pre-created, no env vars). Cross-referenced with `README.md` (manual-setup block) and
`CLAUDE.md` (cycle preamble + heartbeat).

## What was checked

- `artifacts/living-board-template/schema.sql` (185 lines)
- `setup.sh` (523 lines)
- `artifacts/living-board-template/seed-data.sql` (39 lines)
- `artifacts/living-board-template/CLAUDE.md.template` (spot-check vs. root `CLAUDE.md`)
- `artifacts/migrations/2026-04-14_goals_set_completed_at_trigger_and_backfill.sql`
- `artifacts/migrations/2026-04-14_scheduler_health_view.sql`
- `README.md` Manual-setup block (L98–L126)

## Friction points (file:line → issue → one-line fix)

### schema.sql

- **F-S1 — schema.sql:L6** — `gen_random_uuid()` is called without any `CREATE EXTENSION IF NOT EXISTS pgcrypto;` preamble. Supabase enables pgcrypto by default, so this silently works on the happy path. On a stripped Postgres (non-Supabase Postgres trial, `docker run postgres:16`) the whole file fails on the first table. **Fix:** prepend `CREATE EXTENSION IF NOT EXISTS pgcrypto;` — one line, zero cost on Supabase, unblocks portability.

- **F-S2 — schema.sql:L5, L20, L40, L53, L66, L79, L92** — Seven `CREATE TABLE` statements, none of them `CREATE TABLE IF NOT EXISTS`. Re-running `schema.sql` after a partial failure throws on the first table that made it through. **Fix:** add `IF NOT EXISTS` to every `CREATE TABLE`. Cheap and idempotent.

- **F-S3 — schema.sql:L99–L105** — Seven `CREATE INDEX` without `IF NOT EXISTS`. Same re-run hazard as F-S2, and *inconsistent* with the triggers at L141/L146 which already use `DROP TRIGGER IF EXISTS`. **Fix:** `CREATE INDEX IF NOT EXISTS` everywhere.

- **F-S4 — schema.sql:L108–L113 comment** — The `goals_set_completed_at` trigger comment claims it "[l]anded in the main project via artifacts/migrations/2026-04-14_...sql". That path is meaningless to a fresh user who pastes `schema.sql` into the SQL editor — the migration file isn't something they ran. It leaks internal provenance into template output. **Fix:** rephrase to describe *what the trigger does* without referencing the living-board repo's migration history. Or drop the provenance line.

- **F-S5 — schema.sql:L42** — `execution_log.trigger_run_id TEXT` column is defined but never populated by any query in `CLAUDE.md`. Fresh user reading the schema wonders what wires it up; the answer is "nothing currently." **Fix:** either (a) document what this column is reserved for in an inline comment, or (b) remove it until there's a writer.

- **F-S6 — schema.sql entire file** — No RLS policies, no `ALTER TABLE ... ENABLE ROW LEVEL SECURITY`. A fresh Supabase project using the anon key from `.env.local` will accept unauthenticated reads/writes on every row. The dashboard works, and so does anyone who finds the anon key. This is flagged in snapshot open-blockers via goal `5fd7408c`'s precursor 2e7109e5, but `schema.sql` ships zero guardrail and zero warning. **Fix (minimum):** a comment block at the bottom of `schema.sql` pointing users to a separate `rls-policies.sql` or warning them to run RLS setup before exposing the anon key.

- **F-S7 — schema.sql:L92–L96** — `agent_config` table exists but has no inserted defaults and no schema comment describing what keys the agent/runner expects. Fresh user is told "operational key-value settings" but gets no example. **Fix:** add a short COMMENT-ON-TABLE or a `-- Example keys:` block describing 2–3 real keys used in production.

- **F-S8 — schema.sql:L161–L184 scheduler_health view** — View works, but the `CLAUDE.md` heartbeat mechanism (cycle-start L2 at root) depends on `artifacts/scripts/scheduler-status.sh` which needs `SUPABASE_DB_URL`. For a fresh user running `setup.sh`, nothing prompts for or documents `SUPABASE_DB_URL`. They get `[scheduler] skipped: no SUPABASE_DB_URL` forever and the heartbeat monitoring never fires. Schema is fine; the *pairing* with setup is broken. **Fix:** extend `setup.sh` to also prompt for / write the DB connection string (see F-SH10).

### setup.sh

- **F-SH1 — setup.sh:L29–L33** — Root-detection only checks `CLAUDE.md` and `dashboard/` exist. Fine. But the script proceeds before checking that `artifacts/living-board-template/schema.sql` exists — a damaged clone would get past the gate and fail three steps later. **Fix:** add an explicit `[ -f artifacts/living-board-template/schema.sql ]` check.

- **F-SH2 — setup.sh:L136–L154 "auto-create via Claude Code MCP"** — The `DB_MODE=2` flow prints a multi-line `claude -p "..."` command for the user to paste into another terminal, then blocks on `read` for the URL and key. This is a *manual* step wearing an "auto" label — the user still copy-pastes credentials. Also: if the user chose DB_MODE=2 but has no `claude` binary, they're silently dropped back to DB_MODE=1 (L138) with only a `warn`, which is good, but the UX muddles the offer. **Fix:** rename option to `[2] Guided: prints a Claude Code command you run yourself` so the "auto" promise isn't oversold.

- **F-SH3 — setup.sh:L211–L220** — Post-schema re-check is only a REST HTTP status test against `/goals?select=id&limit=1`. A 200 back means the `goals` table exists; it does *not* verify the other 6 tables, the trigger, the view, or that pgcrypto is enabled. A partial schema apply passes this check. **Fix:** extend verification to `count(*)` on all 7 expected tables via a single `?select=...` probe against a catalog view, or make it a stronger SQL check with the service role key if available.

- **F-SH4 — setup.sh:L225–L233 seed-data prompt** — Interactive `read -p "[y/N]"`. A non-interactive CI / devcontainer / remote run hangs here. **Fix:** accept `SETUP_SEED=1` env var as an override; use `read -t 30` with a default.

- **F-SH5 — setup.sh:L247–L251 `.env.local` write** — Only writes `NEXT_PUBLIC_SUPABASE_URL`, `NEXT_PUBLIC_SUPABASE_ANON_KEY`, `AUTH_SECRET`. Nothing about `AGENTMAIL_API_KEY`, `DEVTO_API_KEY`, `SUPABASE_DB_URL`, `ANTHROPIC_API_KEY`. The first agent cycle then fails on silently missing credentials (snapshot open-blockers confirms this). **Fix:** emit a commented-out stanza in `.env.local` listing every credential the agent will reach for, with a one-line comment on where to get each. Non-blocking, high clarity.

- **F-SH6 — setup.sh:L275–L288 AgentMail** — Sets `{{AGENTMAIL_ADDRESS}}` in `CLAUDE.md` but never captures `AGENTMAIL_API_KEY`. The agent can then *refer to* the address but can't read or send mail. **Fix:** if the user supplies an address, also prompt for the API key and append to `.env.local`.

- **F-SH7 — setup.sh:L458–L461 `claude mcp add supabase`** — `|| true` at end swallows all errors. If the MCP registration fails (wrong flag grammar in a future `claude` CLI, auth required, hosted endpoint moved), the user walks away thinking Supabase MCP is configured and their next agent cycle blows up with "Supabase MCP not available." **Fix:** capture rc; on non-zero, print the manual JSON block instead of pretending success.

- **F-SH8 — setup.sh entire file** — Never installs the pre-commit hook. `CLAUDE.md:L17–L20` (root) says the hook is per-clone and every fresh clone must run `bash artifacts/scripts/install-pre-commit-hook.sh` once. Neither `setup.sh` nor the README manual-setup block does this. A fresh human user who later lets Claude commit on a detached HEAD loses work. **Fix:** add a `step "Installing pre-commit hook..." && bash artifacts/scripts/install-pre-commit-hook.sh` right after the prerequisite check. One line, maximum safety return.

- **F-SH9 — setup.sh:L511–L515** — Prints the `claude trigger create` command but never runs it, and never verifies a trigger exists. User may assume "Setup Complete!" means "it will run every hour." It will not. **Fix:** add an explicit note: "The trigger is not created automatically — paste the command above to schedule."

- **F-SH10 — setup.sh** — No step captures `SUPABASE_DB_URL` (direct psql connection string, distinct from the REST URL). Per `CLAUDE.md` root L25, the cycle-start heartbeat silently no-ops without it — *silently* degrading observability. **Fix:** add a step that prompts for the DB password (or pooler connection string) after validating the REST connection, builds the full `postgresql://...` URI, and writes it to a non-committed `.env` at repo root for the scheduler tooling to source.

### seed-data.sql

- **F-D1 — seed-data.sql:L6** — Hardcoded UUID `00000000-0000-0000-0000-000000000001`. Re-running seed-data.sql throws on PK conflict. **Fix:** `INSERT ... ON CONFLICT (id) DO NOTHING` — or better, omit the fixed id entirely and let `DEFAULT gen_random_uuid()` generate it.

- **F-D2 — seed-data.sql:L22** — Example task description points to `artifacts/content/` which exists in this repo but is not part of the stripped template directory. Minor, but a fresh clone of *just the template* will reference a non-existent path. **Fix:** drop the path hint from the seed, or ensure `artifacts/content/.gitkeep` ships in the template.

## Ordering / dependency check

- Tables → indexes → triggers → views: correct order in `schema.sql`. No forward-ref bugs found.
- `scheduler_health` view (L161) depends on `execution_log` (L40) — OK.
- `goals_set_completed_at` trigger function (L114) defined before triggers (L141/L146) reference it — OK.
- No foreign keys cross to tables that are created later.

## What was NOT audited (and why)

- **RLS / security policies** — only noted as F-S6; full RLS audit out of scope this cycle.
- **Dashboard migration / `supabase/migrations` directory** — none exists in-repo (confirmed via `find`); dashboard uses the same `schema.sql` + anon key at runtime, no separate migration graph.
- **Python runner schema expectations** — did not open `runner/` to confirm whether it adds tables; that is a separate audit surface (covered by task 590ea488, sort 40).
- **Live verification against a fresh Supabase project** — credential-free desk-check only. Would need Supabase MCP on a throwaway project to confirm F-S1/F-S3 re-run behaviour.

## Proposed follow-ups (for the synthesis memo, task 07af9171)

1. **Cheapest-fix candidate (task d1ae7725):** add `CREATE EXTENSION IF NOT EXISTS pgcrypto;` + `IF NOT EXISTS` clauses to `schema.sql` (F-S1, F-S2, F-S3). Three edits, fixes portability + idempotency in one commit.
2. **Follow-up task candidate:** extend `setup.sh` to install the pre-commit hook (F-SH8) — single line, protects fresh human users from the detached-HEAD hazard documented in `CLAUDE.md`.
3. **Follow-up goal candidate:** "RLS policies for the living-board schema" — ship `artifacts/living-board-template/rls-policies.sql` and wire `setup.sh` to apply it before emitting the dashboard password (addresses F-S6 and slots under goal `5fd7408c`'s anon-write precursor).
4. **Follow-up task candidate:** enrich `.env.local` scaffold with commented credential stanza (F-SH5) — zero-risk doc-in-code.

## Running tally of audit items

- **Item 3 (schema):** covered — F-S1 through F-S8, plus F-D1/F-D2 for seed.
- **Item 5 (setup.sh + extensions):** covered — F-SH1 through F-SH10, with F-S1 speaking directly to extensions.
- **Items 1, 2, 6:** already covered in `artifacts/research/audit-readme-claudemd-2026-04-15.md` (cycle 101).
- **Item 7:** covered by `artifacts/logs/2026-04-15-fresh-clone-smoke.log` (cycle 99).
- **Item 4:** remaining — credential surface vs. bootstrap-guide (task 590ea488).

Memo ready for synthesis (task 07af9171).
