-- =====================================================================
-- retrospective-queries.sql — Living Board retrospective runbook
-- =====================================================================
--
-- Purpose
--   A reusable, self-contained SQL instrument for any future
--   quantitative retrospective. Each query is labeled (A1, B3, …) so
--   raw output captured in artifacts/metrics/retrospective-raw-<date>.md
--   is traceable back to the exact query that produced it.
--
--   The six sections mirror the question inventory in
--   artifacts/metrics/retrospective-query-inventory.md — consult that
--   file for the full "why this question" rationale. This file holds
--   the runnable SQL plus one-line "Q:" comments summarising the
--   question each query answers.
--
-- Origin
--   Goal 006ff1fd (Quantitative 40-cycle retrospective), first
--   captured 2026-04-14 (cycle 73) against Supabase project
--   ieekjkeayiclprdekxla.
--
-- How to re-run
--   Option A — one bash invocation (preferred):
--     bash artifacts/scripts/run-retrospective-queries.sh
--     (set SUPABASE_DB_URL in env; the script streams each section
--      through psql and writes artifacts/metrics/retrospective-raw-<today>.md)
--
--   Option B — psql directly:
--     psql "$SUPABASE_DB_URL" -f artifacts/metrics/retrospective-queries.sql
--
--   Option C — MCP execute_sql (agent context, no shell credentials):
--     copy the single query block of interest and pass it to
--     mcp__Supabase__execute_sql with project_id=ieekjkeayiclprdekxla.
--     The file is organised so any labeled block (e.g. "B3") can be
--     extracted and run independently without cross-query dependencies.
--
-- Conventions
--   * "Cycle" = one execution_log row (agent unit of work). Snapshots
--     are a second authoritative count via snapshots.cycle_count.
--   * "Productive cycle" = an execute/reflect/decompose that caused
--     at least one task→done OR goal→decomposed OR reflection→new goal.
--   * "Credential blocker" = blocked_reason matching any of
--     'key'|'cookie'|'credential'|'token'|'api' (case-insensitive).
--   * Percentages are rounded to one decimal for readability.
--
-- Out of scope (noted in the inventory, deliberately not queried here)
--   * Per-cycle cost — execution_log.duration_ms coverage is partial.
--   * mem0/Qdrant — not reachable from remote trigger cycles.
--   * Artifact quality — not quantifiable from DB columns alone.
-- =====================================================================


-- ---------------------------------------------------------------------
-- Section A — Volume & throughput
-- ---------------------------------------------------------------------

-- A1: Total agent activity counts + operating window.
-- Q: How much raw activity has accumulated? What is the timespan?
SELECT
  (SELECT COUNT(*) FROM goals)          AS goal_rows,
  (SELECT COUNT(*) FROM tasks)          AS task_rows,
  (SELECT COUNT(*) FROM execution_log)  AS log_rows,
  (SELECT COUNT(*) FROM learnings)      AS learning_rows,
  (SELECT COUNT(*) FROM snapshots)      AS snapshot_rows,
  (SELECT COUNT(*) FROM goal_comments)  AS comment_rows,
  (SELECT MIN(created_at) FROM execution_log) AS first_log,
  (SELECT MAX(created_at) FROM execution_log) AS last_log;

-- A1b: Cycle span (authoritative — snapshots are 1:1 with cycles).
-- Q: What is the cycle count and wall-clock span of the operating run?
SELECT
  MIN(cycle_count)               AS min_cycle,
  MAX(cycle_count)               AS max_cycle,
  COUNT(DISTINCT cycle_count)    AS distinct_cycles,
  MIN(created_at)                AS first_snap,
  MAX(created_at)                AS last_snap
FROM snapshots;

-- A2: Cycles per day.
-- Q: What is the real cadence? The scheduler fires hourly; outages and
-- reflection cycles distort that.
SELECT date_trunc('day', created_at)::date AS day,
       COUNT(*)                             AS log_rows,
       COUNT(DISTINCT date_trunc('hour', created_at)) AS distinct_hours
FROM execution_log
GROUP BY 1
ORDER BY 1;

-- A3: Cycles by action type.
-- Q: What fraction of cycles are execute vs reflect vs decompose vs
-- check_email vs other?
SELECT action,
       COUNT(*)                                                    AS n,
       ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 1)          AS pct
FROM execution_log
GROUP BY action
ORDER BY n DESC;

-- A4: Goals created per week, by creator.
-- Q: Is goal creation mostly user-driven or agent-driven? Trend?
SELECT date_trunc('week', created_at)::date AS week,
       COALESCE(created_by, 'unknown')       AS creator,
       COUNT(*)                              AS goals_created
FROM goals
GROUP BY 1, 2
ORDER BY 1, 2;


-- ---------------------------------------------------------------------
-- Section B — Completion & quality
-- ---------------------------------------------------------------------

-- B1: Task status breakdown (lifetime).
-- Q: Of every task the agent has ever touched, what fraction reached
-- done? This is the headline task-quality number.
SELECT status,
       COUNT(*)                                                    AS n,
       ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 1)          AS pct
FROM tasks
GROUP BY status
ORDER BY n DESC;

-- B2: Goal status breakdown.
-- Q: Of every goal, what fraction is done / in_progress / pending /
-- blocked / abandoned?
SELECT status,
       COUNT(*)                                                    AS n,
       ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 1)          AS pct
FROM goals
GROUP BY status
ORDER BY n DESC;

-- B3: Average task attempts before terminal state.
-- Q: How hard does the agent grind on a task? High attempts on done =
-- inefficient success; high on blocked = wasted cycles.
SELECT status,
       ROUND(AVG(attempts)::numeric, 2)                                      AS mean_attempts,
       PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY attempts)                 AS median_attempts,
       MAX(attempts)                                                         AS max_attempts
FROM tasks
WHERE status IN ('done','blocked','abandoned')
GROUP BY status
ORDER BY status;

-- B3b: Attempts histogram (granular retry distribution).
-- Q: What is the retry shape? Most at 1, long tail, or bimodal?
SELECT attempts, COUNT(*) AS n
FROM tasks
GROUP BY attempts
ORDER BY attempts;

-- B3c: Multi-attempt done tasks (tasks that needed a retry to succeed).
-- Q: Which specific tasks were hard-won? Useful for strategy learnings.
SELECT id, title, attempts, status
FROM tasks
WHERE attempts >= 2
ORDER BY attempts DESC, updated_at DESC;

-- B4: Cycles from goal creation to goal closure (per-goal).
-- Q: How long does a closed goal take? Headline "cycles-to-goal" metric.
-- NOTE: coverage of goals.completed_at is now 100% for status='done' rows,
-- enforced by trigger goals_set_completed_at_upd / goals_set_completed_at_ins
-- (migration 2026-04-14_goals_set_completed_at_trigger_and_backfill.sql,
-- goal 8fc57114). The COALESCE(completed_at, updated_at) fallback is kept
-- defensively but should never fire — see F4/F4b for the live assertion.
SELECT g.id, g.title, g.created_at, g.completed_at,
       ROUND(EXTRACT(EPOCH FROM (COALESCE(g.completed_at, g.updated_at) - g.created_at))/3600.0::numeric, 1) AS hours_elapsed,
       g.completed_at IS NOT NULL AS has_completed_at,
       (SELECT COUNT(*) FROM execution_log el
          WHERE el.goal_id = g.id
            AND el.created_at BETWEEN g.created_at AND COALESCE(g.completed_at, g.updated_at)) AS goal_scoped_log_rows
FROM goals g
WHERE g.status = 'done'
ORDER BY hours_elapsed;

-- B4b: Aggregate cycles-to-goal-completion.
-- Q: What is the mean / median / range of hours-to-goal-closure?
WITH t AS (
  SELECT EXTRACT(EPOCH FROM (COALESCE(completed_at, updated_at) - created_at))/3600.0 AS hours
  FROM goals WHERE status='done'
)
SELECT COUNT(*)                                                      AS n_done_goals,
       ROUND(AVG(hours)::numeric, 1)                                 AS mean_hours,
       PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY hours)            AS median_hours,
       MIN(hours)                                                    AS min_hours,
       MAX(hours)                                                    AS max_hours
FROM t;

-- B5: Task origin + retry-to-success ratio.
-- Q: Are agent-created tasks as completable as user-created ones?
SELECT
  SUM(CASE WHEN (metadata->>'created_by')='agent' THEN 1 ELSE 0 END) AS agent_created,
  SUM(CASE WHEN (metadata->>'created_by')='user'  THEN 1 ELSE 0 END) AS user_created,
  SUM(CASE WHEN metadata->>'created_by' IS NULL   THEN 1 ELSE 0 END) AS origin_null,
  SUM(CASE WHEN attempts>=2 AND status='done'     THEN 1 ELSE 0 END) AS multi_attempt_done,
  SUM(CASE WHEN attempts>=1 AND status='done'     THEN 1 ELSE 0 END) AS any_attempt_done
FROM tasks;


-- ---------------------------------------------------------------------
-- Section C — Blockers
-- ---------------------------------------------------------------------

-- C1: Blocked task taxonomy (top blocker reasons).
-- Q: What actually blocks the agent?
SELECT blocked_reason, COUNT(*) AS n
FROM tasks
WHERE status = 'blocked' AND blocked_reason IS NOT NULL
GROUP BY blocked_reason
ORDER BY n DESC
LIMIT 30;

-- C1b: Raw blocker dump (all currently blocked tasks).
-- Q: What is currently blocked and why? Operator-actionable.
SELECT id, title, blocked_reason
FROM tasks
WHERE status = 'blocked';

-- C2: Credential-blocked fraction of blockers and of all tasks.
-- Q: How much of the blockage is "missing credential" specifically?
WITH b AS (
  SELECT
    COUNT(*) FILTER (
      WHERE blocked_reason ILIKE '%key%'
         OR blocked_reason ILIKE '%cookie%'
         OR blocked_reason ILIKE '%credential%'
         OR blocked_reason ILIKE '%token%'
         OR blocked_reason ILIKE '%api%'
    )                                              AS credential_blocked,
    COUNT(*) FILTER (WHERE status='blocked')       AS total_blocked,
    COUNT(*)                                       AS total_tasks
  FROM tasks
)
SELECT credential_blocked, total_blocked, total_tasks,
       ROUND(100.0 * credential_blocked / NULLIF(total_blocked,0), 1) AS pct_of_blocked,
       ROUND(100.0 * credential_blocked / NULLIF(total_tasks,0),   1) AS pct_of_all
FROM b;

-- C2b: Credential-blocked cycle share via execution_log keywords.
-- Q: How often does a cycle mention "credential/missing/no key"? This
-- complements C2 by measuring cycle-level (not task-level) friction.
SELECT
  SUM(CASE WHEN action='check_email' AND summary ILIKE '%skipped%' THEN 1 ELSE 0 END) AS email_skipped,
  SUM(CASE WHEN action='check_email'                                THEN 1 ELSE 0 END) AS email_total,
  SUM(CASE WHEN summary ILIKE '%credential%'
             OR summary ILIKE '%no key%'
             OR summary ILIKE '%missing%'
             OR summary ILIKE '%devto_api_key%'
             OR summary ILIKE '%agentmail_api_key%' THEN 1 ELSE 0 END) AS credential_mentions,
  COUNT(*)                                                           AS total_log_rows
FROM execution_log;

-- C3: Blocker-to-done ratio (proxy for "do blocked tasks ever recover?").
-- Q: Are blockers permanent parking or temporary holds?
SELECT
  COUNT(*) FILTER (WHERE status='blocked')                         AS currently_blocked,
  COUNT(*) FILTER (WHERE status='done')                            AS done,
  ROUND(1.0 * COUNT(*) FILTER (WHERE status='blocked')
        / NULLIF(COUNT(*) FILTER (WHERE status='done'), 0), 3)     AS blocked_to_done_ratio
FROM tasks;


-- ---------------------------------------------------------------------
-- Section D — Reflection & meta-cycles
-- ---------------------------------------------------------------------

-- D1: Reflection cadence.
-- Q: CLAUDE.md says reflect every ~8h — does that match reality?
WITH r AS (
  SELECT created_at,
         LAG(created_at) OVER (ORDER BY created_at) AS prev_reflect
  FROM execution_log WHERE action='reflect'
)
SELECT COUNT(*)                                                                        AS reflections,
       MIN(created_at)                                                                 AS first,
       MAX(created_at)                                                                 AS last,
       ROUND(AVG(EXTRACT(EPOCH FROM (created_at - prev_reflect))/3600.0)::numeric, 1)  AS mean_hours_between,
       ROUND(PERCENTILE_CONT(0.5) WITHIN GROUP (
         ORDER BY EXTRACT(EPOCH FROM (created_at - prev_reflect))/3600.0)::numeric, 1) AS median_hours_between
FROM r
WHERE prev_reflect IS NOT NULL;

-- D2: Reflection productivity.
-- Q: Do reflection cycles actually produce new goals?
SELECT el.id, el.created_at,
       (el.details->>'new_goals_proposed')                              AS proposed,
       (SELECT COUNT(*) FROM goals g
          WHERE g.created_at BETWEEN el.created_at - INTERVAL '10 minutes'
                                 AND el.created_at + INTERVAL '20 minutes'
            AND g.created_by='agent')                                   AS goals_actually_created
FROM execution_log el
WHERE action='reflect'
ORDER BY el.created_at;

-- D3: Email-check cadence.
-- Q: Does email-check fire at the expected ~8h interval?
WITH e AS (
  SELECT created_at,
         LAG(created_at) OVER (ORDER BY created_at) AS prev_check
  FROM execution_log WHERE action='check_email'
)
SELECT COUNT(*)                                                                   AS checks,
       ROUND(AVG(EXTRACT(EPOCH FROM (created_at - prev_check))/3600.0)::numeric, 1) AS mean_hours_between
FROM e
WHERE prev_check IS NOT NULL;


-- ---------------------------------------------------------------------
-- Section E — Trend / temporal shape
-- ---------------------------------------------------------------------

-- E1: Tasks completed per day.
-- Q: Is the agent getting more efficient, less, or flat?
SELECT date_trunc('day', completed_at)::date AS day,
       COUNT(*)                              AS tasks_done
FROM tasks
WHERE status='done' AND completed_at IS NOT NULL
GROUP BY 1
ORDER BY 1;

-- E1b: Weekly action trend (ISO week buckets).
-- Q: How is the execute/reflect/email mix evolving week over week?
SELECT TO_CHAR(date_trunc('week', created_at), 'IYYY-"W"IW') AS iso_week,
       COUNT(*)                                              AS total,
       SUM(CASE WHEN action='execute'     THEN 1 ELSE 0 END) AS executes,
       SUM(CASE WHEN action='reflect'     THEN 1 ELSE 0 END) AS reflects,
       SUM(CASE WHEN action='check_email' THEN 1 ELSE 0 END) AS emails
FROM execution_log
GROUP BY 1
ORDER BY 1;

-- E2: Learnings created per day (with mean confidence).
-- Q: Is learning capture accelerating, flat, or decaying?
SELECT date_trunc('day', created_at)::date AS day,
       COUNT(*)                             AS learnings_created,
       ROUND(AVG(confidence)::numeric, 2)   AS mean_confidence
FROM learnings
GROUP BY 1
ORDER BY 1;

-- E3: Active-goal count over time (board width).
-- Q: Is the board growing or converging?
SELECT created_at::date                       AS day,
       cycle_count,
       jsonb_array_length(active_goals)       AS active_goal_count
FROM snapshots
ORDER BY created_at;

-- E4: Learnings corpus shape by category.
-- Q: Which memory categories carry the most mass and confidence?
SELECT category,
       COUNT(*)                                                    AS n,
       ROUND(AVG(confidence)::numeric, 2)                          AS avg_conf,
       SUM(CASE WHEN confidence<0.5  THEN 1 ELSE 0 END)            AS low_conf,
       SUM(CASE WHEN confidence>=0.8 THEN 1 ELSE 0 END)            AS high_conf
FROM learnings
GROUP BY category
ORDER BY n DESC;


-- ---------------------------------------------------------------------
-- Section F — Spot checks / data quality
-- ---------------------------------------------------------------------

-- F1: Orphan execution_log rows (no task_id and no goal_id).
-- Q: How much activity is unattributed?
SELECT COUNT(*) FILTER (WHERE goal_id IS NULL AND task_id IS NULL) AS orphan_rows,
       COUNT(*)                                                     AS total_rows
FROM execution_log;

-- F2: Tasks stuck in_progress across multiple cycles (zombie detector).
-- Q: Any tasks claimed but never resolved? Useful for cycle-start audits.
SELECT id, title, started_at,
       ROUND(EXTRACT(EPOCH FROM (now() - started_at))/3600.0::numeric, 1) AS hours_stuck
FROM tasks
WHERE status='in_progress'
ORDER BY started_at
LIMIT 20;

-- F3: Learnings confidence distribution buckets.
-- Q: Are most learnings high-confidence or middling?
SELECT CASE
         WHEN confidence >= 0.9 THEN '0.9-1.0'
         WHEN confidence >= 0.7 THEN '0.7-0.9'
         WHEN confidence >= 0.5 THEN '0.5-0.7'
         WHEN confidence >= 0.3 THEN '0.3-0.5'
         ELSE '<0.3'
       END AS bucket,
       COUNT(*) AS n
FROM learnings
GROUP BY 1
ORDER BY 1 DESC;

-- F4: Goals missing completed_at (schema-integrity check).
-- Q: How many "done" goals lack a completed_at timestamp?
-- HISTORY: recurring gap flagged at cycle 78 (9/14 done goals missing the
-- timestamp, 36% coverage). Closed cycle 89 by goal 8fc57114, which
-- (a) installed BEFORE INSERT/UPDATE triggers goals_set_completed_at_ins
-- and goals_set_completed_at_upd that stamp completed_at on transition
-- to 'done' and clear it on transition away, and (b) backfilled the 9
-- historical rows from MAX(tasks.completed_at) per goal.
-- EXPECTED: done_missing_completed_at = 0. The invariant is now
-- trigger-enforced, not checklist-enforced — see F4b for the boolean
-- pass/fail form suitable for grep'ing in CI or cycle-start preamble.
SELECT COUNT(*) FILTER (WHERE status='done' AND completed_at IS NULL)  AS done_missing_completed_at,
       COUNT(*) FILTER (WHERE status='done')                           AS done_total
FROM goals;

-- F4b: Trigger-invariant assertion (boolean pass/fail).
-- Q: Is the goals.completed_at invariant currently holding?
-- Returns one row: invariant_holds = true when zero done-goals are
-- missing completed_at. A 'false' here means the trigger was disabled,
-- bypassed by a direct UPDATE on a replica, or dropped — investigate
-- pg_trigger for goals_set_completed_at_ins / goals_set_completed_at_upd
-- before assuming the data is wrong.
SELECT
  COUNT(*) FILTER (WHERE status='done' AND completed_at IS NULL) = 0
    AS invariant_holds,
  COUNT(*) FILTER (WHERE status='done' AND completed_at IS NULL)
    AS violation_count
FROM goals;

-- End of retrospective-queries.sql
