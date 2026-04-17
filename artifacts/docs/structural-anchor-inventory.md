# Structural Anchor Inventory

Audit of canonical anchor strings for each critical-path file.
Each anchor guards a structural invariant — if a rewrite drops it, the test fails loudly.

Reference implementation: `artifacts/scripts/test-cycle-start-structure.sh` (cycle 119).

---

## 1. runner/agent.py (141 lines)

| # | Label | Anchor string | Invariant guarded |
|---|-------|--------------|-------------------|
| 1 | imports:phase-orient | `from .phases import orient` | Phase module wiring |
| 2 | imports:phase-reflect | `reflect, check_email` | Reflection + email phases imported |
| 3 | credential-banner:env-vars | `CREDENTIAL_ENV_VARS` | Credential enumeration exists |
| 4 | credential-banner:emit-fn | `def emit_credentials_banner` | Banner function defined |
| 5 | credential-banner:call | `emit_credentials_banner()` | Banner is actually called in cycle |
| 6 | phase:orient | `Phase 1: Orient` | Orient phase ordering |
| 7 | phase:decide | `Phase 2: Decide` | Decide phase ordering |
| 8 | phase:execute | `Phase 3: Execute` | Execute phase ordering |
| 9 | phase:record | `Phase 4: Record` | Record phase ordering |
| 10 | reflection:gate | `needs_reflection` | Reflection gate check wired |
| 11 | email:gate | `needs_email_check` | Email check gate wired |
| 12 | decide:idle | `action == "idle"` | Idle path exists |
| 13 | decide:decompose | `action == "decompose_goal"` | Decompose path exists |
| 14 | class:runner | `class AgentRunner` | Main runner class exists |

Min line count floor: 100

---

## 2. artifacts/scripts/scheduler-status.sh (127 lines)

| # | Label | Anchor string | Invariant guarded |
|---|-------|--------------|-------------------|
| 1 | args:warn-threshold | `--warn-threshold=` | Threshold argument parsing |
| 2 | env:db-url-check | `SUPABASE_DB_URL` | Graceful skip when unset |
| 3 | query:view-ref | `scheduler_health` | Queries the correct view |
| 4 | query:hours-since | `hours_since_last` | Age calculation in query |
| 5 | query:gap-count | `gap_24h_count` | Gap detection in query |
| 6 | query:entries | `entries_24h` | Entry count in query |
| 7 | exec:psql | `psql "$SUPABASE_DB_URL"` | psql invocation with correct var |
| 8 | output:prefix | `[scheduler]` | Canonical output prefix |
| 9 | output:last-exec | `last_exec=` | Output format includes timestamp |
| 10 | output:age | `age=` | Output format includes age |
| 11 | exit:threshold-check | `exit 3` | Exit code 3 for threshold exceeded |
| 12 | skip:no-db-url | `skipped: no SUPABASE_DB_URL` | Skip message when env unset |

Min line count floor: 80

---

## 3. CLAUDE.md (407 lines)

| # | Label | Anchor string | Invariant guarded |
|---|-------|--------------|-------------------|
| 1 | phase:0-heading | `### Phase 0: Sync` | Phase 0 section exists |
| 2 | phase:1-heading | `### Phase 1: Orient` | Phase 1 section exists |
| 3 | phase:1b-heading | `### Phase 1b: Reflect` | Phase 1b section exists |
| 4 | phase:1c-heading | `### Phase 1c: Check Email` | Phase 1c section exists |
| 5 | phase:1d-heading | `### Phase 1d: Process User Comments` | Phase 1d section exists |
| 6 | phase:2-heading | `### Phase 2: Decide` | Phase 2 section exists |
| 7 | phase:3-heading | `### Phase 3: Execute` | Phase 3 section exists |
| 8 | phase:4-heading | `### Phase 4: Record` | Phase 4 section exists |
| 9 | contract:literal-first-call | `literal first bash call` | Phase 0 contract language |
| 10 | contract:cycle-start-ref | `bash artifacts/scripts/cycle-start.sh` | Cycle-start invocation |
| 11 | orient:snapshot-query | `SELECT content, active_goals` | Snapshot query present |
| 12 | section:goal-decomposition | `## Goal Decomposition` | Decomposition section exists |
| 13 | section:memory-system | `## Memory System` | Memory section exists |
| 14 | section:identity | `## Identity` | Identity section exists |
| 15 | tool:execute-sql | `execute_sql` | Supabase tool reference |

Min line count floor: 300

---

## 4. artifacts/living-board-template/schema.sql (191 lines)

| # | Label | Anchor string | Invariant guarded |
|---|-------|--------------|-------------------|
| 1 | table:goals | `CREATE TABLE IF NOT EXISTS goals` | Goals table definition |
| 2 | table:tasks | `CREATE TABLE IF NOT EXISTS tasks` | Tasks table definition |
| 3 | table:execution-log | `CREATE TABLE IF NOT EXISTS execution_log` | Execution log table |
| 4 | table:learnings | `CREATE TABLE IF NOT EXISTS learnings` | Learnings table |
| 5 | table:snapshots | `CREATE TABLE IF NOT EXISTS snapshots` | Snapshots table |
| 6 | table:goal-comments | `CREATE TABLE IF NOT EXISTS goal_comments` | Goal comments table |
| 7 | table:agent-config | `CREATE TABLE IF NOT EXISTS agent_config` | Agent config table |
| 8 | ext:pgcrypto | `CREATE EXTENSION IF NOT EXISTS pgcrypto` | UUID generation extension |
| 9 | trigger:completed-at-fn | `goals_set_completed_at()` | Completed_at trigger function |
| 10 | trigger:completed-at-ins | `goals_set_completed_at_ins` | Insert trigger name |
| 11 | trigger:completed-at-upd | `goals_set_completed_at_upd` | Update trigger name |
| 12 | view:scheduler-health | `CREATE OR REPLACE VIEW public.scheduler_health` | Scheduler health view |
| 13 | fk:tasks-goals | `goal_id UUID NOT NULL REFERENCES goals(id)` | Tasks→goals foreign key |
| 14 | index:goals-status | `idx_goals_status` | Performance index on goals |

Min line count floor: 120

---

## Notes

- runner/phases/__init__.py (21 lines) is covered indirectly by the agent.py test anchors 1-2 (the import line). A dedicated test for a 21-line re-export file would be low-value.
- Individual phase files (orient.py, decide.py, etc.) are not included in this initial round. They are large (175-382 lines each) but their internal structure is less prone to silent-rewrite regression than the orchestration surfaces above. Can be added in a follow-up goal if needed.
- Anchor strings are chosen to be unique enough that a stub file cannot satisfy them accidentally, but generic enough to survive minor refactors (e.g., `Phase 1: Orient` vs `# Phase 1 — Orient`).
