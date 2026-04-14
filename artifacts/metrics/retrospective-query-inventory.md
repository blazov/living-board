# Retrospective Query Inventory — 40-cycle Quantitative Baseline

Goal: `006ff1fd-7bef-467d-a3fd-d1d1c017d59f` — Quantitative 40-cycle retrospective.

This document lists every question the retrospective is trying to answer and the exact SQL query that produces the raw data for it. No interpretation here — this is the inventory. Task 2 of the goal executes these and snapshots the results as CSVs under `artifacts/metrics/retrospective-data/`.

Conventions:

- A **cycle** = one `execution_log` row whose `action` is one of `execute`, `reflect`, `decompose`, `check_email`, `noop` (or equivalent). We treat each `execution_log` row as one unit of agent activity, and group by `date_trunc('hour', created_at)` where per-cycle aggregation is needed.
- A **productive cycle** = a cycle where at least one task transitioned to `done` OR a goal was decomposed OR a reflection produced ≥1 new pending goal.
- A **credential blocker** = a task with `status='blocked'` whose `blocked_reason` matches `ILIKE '%key%' OR '%cookie%' OR '%credential%' OR '%token%' OR '%api%'`.

Queries reference columns confirmed against the live schema on 2026-04-14 (see cycle 73 schema probe).

---

## Section A — Volume & throughput

### A1. Total agent activity counts
**Question:** How much raw activity exists? Baseline row counts across all agent-owned tables.
```sql
SELECT 'goals' AS table, COUNT(*) AS n FROM goals
UNION ALL SELECT 'tasks', COUNT(*) FROM tasks
UNION ALL SELECT 'execution_log', COUNT(*) FROM execution_log
UNION ALL SELECT 'learnings', COUNT(*) FROM learnings
UNION ALL SELECT 'snapshots', COUNT(*) FROM snapshots
UNION ALL SELECT 'goal_comments', COUNT(*) FROM goal_comments;
```

### A2. Cycles per day
**Question:** What is the real cadence? The scheduler fires hourly, but outages and reflection cycles distort that.
```sql
SELECT date_trunc('day', created_at)::date AS day,
       COUNT(*) AS log_rows,
       COUNT(DISTINCT date_trunc('hour', created_at)) AS distinct_hours
FROM execution_log
GROUP BY 1
ORDER BY 1;
```

### A3. Cycles by action type
**Question:** What fraction of cycles are execute vs reflect vs decompose vs check_email vs other?
```sql
SELECT action, COUNT(*) AS n,
       ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 1) AS pct
FROM execution_log
GROUP BY action
ORDER BY n DESC;
```

### A4. Goals created per week, by creator
**Question:** Is goal creation mostly user-driven or agent-driven? Is the rate trending up or down?
```sql
SELECT date_trunc('week', created_at)::date AS week,
       COALESCE(created_by, 'unknown') AS creator,
       COUNT(*) AS goals_created
FROM goals
GROUP BY 1, 2
ORDER BY 1, 2;
```

---

## Section B — Completion & quality

### B1. Task completion rate (lifetime)
**Question:** Of every task the agent has ever touched, what fraction reached `done`?
```sql
SELECT status, COUNT(*) AS n,
       ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 1) AS pct
FROM tasks
GROUP BY status
ORDER BY n DESC;
```

### B2. Goal completion rate
**Question:** Of every goal, what fraction is `done` vs `in_progress` vs `pending` vs `blocked`/`abandoned`?
```sql
SELECT status, COUNT(*) AS n,
       ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 1) AS pct
FROM goals
GROUP BY status
ORDER BY n DESC;
```

### B3. Average task attempts before terminal state
**Question:** How hard does the agent grind on a task? High attempts on `done` = inefficient success; high attempts on `blocked` = wasted cycles.
```sql
SELECT status,
       ROUND(AVG(attempts)::numeric, 2) AS mean_attempts,
       PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY attempts) AS median_attempts,
       MAX(attempts) AS max_attempts
FROM tasks
WHERE status IN ('done','blocked','abandoned')
GROUP BY status
ORDER BY status;
```

### B4. Cycles from goal creation to goal closure
**Question:** How long does a closed goal take? This is the headline "cycles-to-goal-completion" metric.
```sql
SELECT g.id, g.title, g.created_at, g.completed_at,
       EXTRACT(EPOCH FROM (g.completed_at - g.created_at)) / 3600.0 AS hours_elapsed,
       (SELECT COUNT(*) FROM execution_log el
          WHERE el.goal_id = g.id
            AND el.created_at BETWEEN g.created_at AND g.completed_at) AS goal_scoped_log_rows
FROM goals g
WHERE g.status = 'done' AND g.completed_at IS NOT NULL
ORDER BY g.completed_at;
```

Aggregation:
```sql
WITH t AS (
  SELECT EXTRACT(EPOCH FROM (completed_at - created_at))/3600.0 AS hours
  FROM goals WHERE status='done' AND completed_at IS NOT NULL
)
SELECT COUNT(*) AS n_done_goals,
       ROUND(AVG(hours)::numeric, 1) AS mean_hours,
       PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY hours) AS median_hours,
       MIN(hours) AS min_hours, MAX(hours) AS max_hours
FROM t;
```

---

## Section C — Blockers

### C1. Blocked task taxonomy
**Question:** What actually blocks the agent? Extract the top reasons.
```sql
SELECT blocked_reason, COUNT(*) AS n
FROM tasks
WHERE status = 'blocked' AND blocked_reason IS NOT NULL
GROUP BY blocked_reason
ORDER BY n DESC
LIMIT 30;
```

### C2. Credential-blocked fraction
**Question:** How much of the blockage is "missing credential" specifically?
```sql
WITH b AS (
  SELECT COUNT(*) FILTER (
    WHERE blocked_reason ILIKE '%key%'
       OR blocked_reason ILIKE '%cookie%'
       OR blocked_reason ILIKE '%credential%'
       OR blocked_reason ILIKE '%token%'
       OR blocked_reason ILIKE '%api%'
  ) AS credential_blocked,
  COUNT(*) FILTER (WHERE status='blocked') AS total_blocked,
  COUNT(*) AS total_tasks
  FROM tasks
)
SELECT credential_blocked, total_blocked, total_tasks,
       ROUND(100.0 * credential_blocked / NULLIF(total_blocked,0), 1) AS pct_of_blocked,
       ROUND(100.0 * credential_blocked / NULLIF(total_tasks,0), 1) AS pct_of_all
FROM b;
```

### C3. Blocker-to-resolution ratio
**Question:** When a task is blocked, does it ever get unblocked? Are blocked tasks permanent parking or temporary holds?
```sql
SELECT status, COUNT(*) AS n
FROM tasks
WHERE id IN (
  SELECT task_id FROM execution_log WHERE summary ILIKE '%blocked%' OR details::text ILIKE '%blocked%'
)
GROUP BY status
ORDER BY n DESC;
```

Simpler proxy: ratio of currently-blocked to ever-reached-done.
```sql
SELECT
  COUNT(*) FILTER (WHERE status='blocked') AS currently_blocked,
  COUNT(*) FILTER (WHERE status='done') AS done,
  ROUND(1.0 * COUNT(*) FILTER (WHERE status='blocked')
        / NULLIF(COUNT(*) FILTER (WHERE status='done'),0), 3) AS blocked_to_done_ratio
FROM tasks;
```

---

## Section D — Reflection & meta-cycles

### D1. Reflection cadence
**Question:** How often does the agent reflect? CLAUDE.md says "every 8 hours" — is that what actually happens?
```sql
WITH r AS (
  SELECT created_at,
         LAG(created_at) OVER (ORDER BY created_at) AS prev_reflect
  FROM execution_log WHERE action='reflect'
)
SELECT COUNT(*) AS reflections,
       MIN(created_at) AS first, MAX(created_at) AS last,
       ROUND(AVG(EXTRACT(EPOCH FROM (created_at - prev_reflect))/3600.0)::numeric, 1) AS mean_hours_between,
       ROUND(PERCENTILE_CONT(0.5) WITHIN GROUP (
         ORDER BY EXTRACT(EPOCH FROM (created_at - prev_reflect))/3600.0)::numeric, 1) AS median_hours_between
FROM r WHERE prev_reflect IS NOT NULL;
```

### D2. Reflection productivity
**Question:** Do reflection cycles actually produce new goals?
```sql
SELECT el.id, el.created_at,
       (el.details->>'new_goals_proposed') AS proposed,
       (SELECT COUNT(*) FROM goals g
          WHERE g.created_at BETWEEN el.created_at - INTERVAL '10 minutes'
                                 AND el.created_at + INTERVAL '20 minutes'
            AND g.created_by='agent') AS goals_actually_created
FROM execution_log el
WHERE action='reflect'
ORDER BY el.created_at;
```

### D3. Email-check cadence
**Question:** Does email-check fire at the expected 8-hour interval?
```sql
WITH e AS (
  SELECT created_at,
         LAG(created_at) OVER (ORDER BY created_at) AS prev_check
  FROM execution_log WHERE action='check_email'
)
SELECT COUNT(*) AS checks,
       ROUND(AVG(EXTRACT(EPOCH FROM (created_at - prev_check))/3600.0)::numeric, 1) AS mean_hours_between
FROM e WHERE prev_check IS NOT NULL;
```

---

## Section E — Trend / temporal shape

### E1. Tasks completed per cycle, over time
**Question:** Is the agent getting more efficient, less, or flat?
```sql
SELECT date_trunc('day', completed_at)::date AS day,
       COUNT(*) AS tasks_done
FROM tasks
WHERE status='done' AND completed_at IS NOT NULL
GROUP BY 1
ORDER BY 1;
```

### E2. Learnings created per cycle, over time
**Question:** Is learning capture accelerating or flat?
```sql
SELECT date_trunc('day', created_at)::date AS day,
       COUNT(*) AS learnings_created,
       ROUND(AVG(confidence)::numeric, 2) AS mean_confidence
FROM learnings
GROUP BY 1
ORDER BY 1;
```

### E3. Active-goal count over time
**Question:** Is the board growing or converging?
```sql
-- For each snapshot (hourly-ish), how many goals were active?
SELECT created_at::date AS day,
       cycle_count,
       jsonb_array_length(active_goals) AS active_goal_count
FROM snapshots
ORDER BY created_at;
```

---

## Section F — Spot checks / data quality

### F1. Execution log rows with no task_id and no goal_id
**Question:** How many log rows are unattributed (orphan activity)?
```sql
SELECT COUNT(*) FILTER (WHERE goal_id IS NULL AND task_id IS NULL) AS orphan_rows,
       COUNT(*) AS total_rows
FROM execution_log;
```

### F2. Tasks stuck in_progress across multiple cycles
**Question:** Any zombies?
```sql
SELECT id, title, started_at,
       ROUND(EXTRACT(EPOCH FROM (now() - started_at))/3600.0, 1) AS hours_stuck
FROM tasks
WHERE status='in_progress'
ORDER BY started_at
LIMIT 20;
```

### F3. Learnings confidence distribution
**Question:** Are most learnings high-confidence or middling?
```sql
SELECT CASE
  WHEN confidence >= 0.9 THEN '0.9-1.0'
  WHEN confidence >= 0.7 THEN '0.7-0.9'
  WHEN confidence >= 0.5 THEN '0.5-0.7'
  WHEN confidence >= 0.3 THEN '0.3-0.5'
  ELSE '<0.3' END AS bucket,
  COUNT(*) AS n
FROM learnings
GROUP BY 1
ORDER BY 1 DESC;
```

---

## Out of scope (deliberately)

- Per-cycle duration / cost — `execution_log.duration_ms` is populated only when the trigger wrapper records it; coverage is incomplete and will bias any average. Noted for a future goal.
- mem0 / Qdrant metrics — mem0 is unavailable in remote-trigger cycles, so semantic-memory statistics cannot be derived from the Supabase side.
- Quality of individual artifacts — not quantifiable from database columns alone.

## How task 2 will use this file

Task 2 runs every query above against `ieekjkeayiclprdekxla`, writes one CSV per query under `artifacts/metrics/retrospective-data/` named `{section}-{id}.csv` (e.g. `A1-row-counts.csv`), and commits the data snapshots. Task 3 interprets them; task 4 writes the memo; task 5 promotes the most useful of these queries into a committed SQL library.
