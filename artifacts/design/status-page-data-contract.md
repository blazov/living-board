# Status Page Data Contract

Goal: 5fd7408c — Live public status page
Task: 73b3e480 — Audit Supabase RLS + pick safe anon-readable columns
Cycle: 80 (2026-04-14)

## Current RLS / policy state (public schema)

| Table             | RLS enabled | anon SELECT | anon INSERT | anon UPDATE | anon DELETE |
|-------------------|-------------|-------------|-------------|-------------|-------------|
| goals             | yes         | allow (qual=true) | allow | allow | allow |
| tasks             | yes         | allow       | allow       | allow       | allow       |
| execution_log     | yes         | allow       | allow       | —           | allow       |
| learnings         | yes         | allow       | allow       | allow       | allow       |
| snapshots         | **no**      | implicit (GRANT) | implicit | implicit | implicit |
| goal_comments     | **no**      | implicit    | implicit    | implicit    | implicit    |
| agent_config      | yes         | — (no policy) | — | — | — |
| metrics_snapshots | yes         | — (no policy) | — | — | — |
| page_views        | yes         | insert-only per comment | insert-only | — | — |

Source: `pg_policies` + `pg_class.relrowsecurity` snapshot taken 2026-04-14 09:17 UTC.

## Security finding (must address before the status page goes public)

The public status page will embed the Supabase publishable anon key in client-side
JS. That key is already exposed anywhere the anon SDK is used (dashboard, page_views
beacon), so exposure itself is not new. **What is new**: a public
`docs/status.html` gives anonymous readers a one-click JS console from which to
run INSERT/UPDATE/DELETE against `goals`, `tasks`, `execution_log`, `learnings`,
`snapshots`, and `goal_comments`. That is a write-vandalism surface.

Mitigation (pre-publish, required):

1. Drop the `Allow public delete`, `Allow public insert`, and `Allow public update`
   policies on `goals`, `tasks`, `execution_log`, `learnings`. Keep only
   `Allow public read`. The agent writes via Supabase MCP (service role) and the
   operator dashboard writes via authenticated key, so anon-write is unused.
2. Enable RLS on `snapshots` and `goal_comments` and add `SELECT ... TO anon USING (true)`
   (public-read) policies. Do **not** add anon write policies.
3. Keep `page_views` as-is (insert-only anon already documented).
4. Leave `agent_config` and `metrics_snapshots` without anon policies → effectively invisible to the status page. Good.

Defer the RLS migration to its own task (new task 5fd7408c-05: "Lock down
anon write access before publishing") — we'll add it before the implementation task.

## Columns safe to expose on the status page

Anything tagged **expose** goes into the public view. **redact** means drop on the client.

### goals
- expose: `id`, `title`, `description`, `status`, `priority`, `created_at`, `completed_at`, `created_by`
- expose with filter: `metadata` — strip any key ending in `_key`, `_token`, `_secret`, `_password`; also drop `metadata.reasoning` if it reveals unshipped strategy. Safer default: don't render `metadata` at all on v1.
- redact: `parent_goal_id` (leak internal graph — optional render as "has parent" boolean)

### tasks
- expose: `id`, `goal_id`, `title`, `description`, `status`, `sort_order`, `attempts`, `max_attempts`, `blocked_reason`, `result`, `created_at`, `completed_at`
- redact from metadata: any key holding credentials or internal URLs. v1: drop metadata.

### execution_log
- expose: `id`, `goal_id`, `task_id`, `action`, `summary`, `created_at`, `duration_ms`
- redact: `details` — frequently contains file paths, internal IDs, payloads. v1: drop.
- redact: `trigger_run_id` (internal scheduler id)

### learnings
- expose: `id`, `category`, `content`, `confidence`, `times_validated`, `created_at`
- expose link: `goal_id` (to group by goal)

### snapshots (most-recent-1 only)
- expose: `content`, `cycle_count`, `current_focus`, `created_at`
- expose: `active_goals` (already a public projection)
- redact: `open_blockers` (may name credentials and operator-side gaps — fine to show
  at summary level, but v1 omit to avoid leaking vendor names and token names)
- redact: `recent_outcomes` jsonb (might contain file paths); OK to include if we map
  to `{summary, timestamp, success}` only — which matches its defined shape. Include.
- expose: `key_learnings` (already a public projection of top-5 learnings)

### goal_comments
- **do not expose on v1.** User feedback is semi-private; leaking it breaks the trust
  that the comment stream is an operator/agent channel. Revisit later.

## REST endpoint shapes (PostgREST)

Base: `https://ieekjkeayiclprdekxla.supabase.co/rest/v1`

Required headers: `apikey: <anon>` and `Authorization: Bearer <anon>`.

1. Active goals:
   `GET /goals?status=in.(in_progress,pending)&select=id,title,description,status,priority,created_at,created_by&order=priority.asc,created_at.asc`
2. Tasks for a goal:
   `GET /tasks?goal_id=eq.<id>&select=id,title,status,sort_order,attempts,max_attempts,blocked_reason,completed_at&order=sort_order.asc`
3. Recent execution log:
   `GET /execution_log?select=action,summary,created_at,duration_ms,goal_id&order=created_at.desc&limit=20`
4. Recent learnings:
   `GET /learnings?select=category,content,confidence,times_validated,created_at,goal_id&order=created_at.desc&limit=10`
5. Latest snapshot:
   `GET /snapshots?select=content,cycle_count,current_focus,active_goals,recent_outcomes,key_learnings,created_at&order=created_at.desc&limit=1`

All five are covered by existing `Allow public read` policies on RLS-enabled tables,
except snapshots, which reads via default GRANTs (RLS off). After the mitigation
migration, snapshots will have an explicit `SELECT TO anon` policy.

## Publishable anon key

Obtain via `mcp__Supabase__get_publishable_keys`. Commit the key into `docs/status.html`
— publishable anon keys are designed for public embedding.

## Output of this task

This document. Next task (design — b5474fad) consumes it. The implementation task
(6f4a5aab) consumes both. Before 6f4a5aab runs, a new "lock-down anon writes"
task must be inserted and executed; filing that now as task 5fd7408c-25
(sort_order 25, between design and implement).
