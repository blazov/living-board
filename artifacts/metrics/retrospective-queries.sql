-- Living Board — 40-cycle retrospective query set
-- Goal: 006ff1fd  Task: 73d99493 (sort_order 10)
-- Captured: 2026-04-14 (cycle 73), Supabase project ieekjkeayiclprdekxla
--
-- This file is a RUNBOOK. Each labeled query below is named so the raw output
-- in artifacts/metrics/retrospective-raw-<date>.md is traceable back to the
-- query that produced it. Re-run any section by copy-pasting the single query
-- block into execute_sql (Supabase MCP) or psql.
--
-- Organizing principle: measure what the agent actually does, not what it
-- claims to do. Every metric here is derived from the four behavioral tables:
-- goals, tasks, execution_log, learnings. Snapshots are used only to get an
-- authoritative cycle count.

----------------------------------------------------------------------
-- Section A — Overall scale & timespan
----------------------------------------------------------------------

-- A1: Row counts + operating window
SELECT
  (SELECT COUNT(*) FROM execution_log)               AS log_rows,
  (SELECT COUNT(*) FROM tasks)                       AS task_rows,
  (SELECT COUNT(*) FROM goals)                       AS goal_rows,
  (SELECT COUNT(*) FROM learnings)                   AS learning_rows,
  (SELECT COUNT(*) FROM snapshots)                   AS snapshot_rows,
  (SELECT MIN(created_at) FROM execution_log)        AS first_log,
  (SELECT MAX(created_at) FROM execution_log)        AS last_log;

-- A2: Cycle span (authoritative — snapshots are 1:1 with cycles)
SELECT MIN(cycle_count) min_cycle, MAX(cycle_count) max_cycle,
       COUNT(DISTINCT cycle_count) distinct_cycles,
       MIN(created_at) first_snap, MAX(created_at) last_snap
FROM snapshots;

----------------------------------------------------------------------
-- Section B — Task quality
----------------------------------------------------------------------

-- B1: Task status breakdown (primary task-quality number)
SELECT status, COUNT(*) n,
       ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 1) pct
FROM tasks GROUP BY status ORDER BY n DESC;

-- B2: Attempts histogram (retry rate)
SELECT attempts, COUNT(*) n FROM tasks GROUP BY attempts ORDER BY attempts;

-- B3: Multi-attempt done tasks (tasks that needed a retry to succeed)
SELECT id, title, attempts, status
FROM tasks WHERE attempts >= 2 ORDER BY attempts DESC, updated_at DESC;

-- B4: Task origin (agent vs user) + reopened flag
SELECT
  SUM(CASE WHEN (metadata->>'created_by')='agent' THEN 1 ELSE 0 END) agent_created,
  SUM(CASE WHEN (metadata->>'created_by')='user'  THEN 1 ELSE 0 END) user_created,
  SUM(CASE WHEN metadata->>'created_by' IS NULL    THEN 1 ELSE 0 END) origin_null,
  SUM(CASE WHEN attempts>=2 AND status='done'      THEN 1 ELSE 0 END) multi_attempt_done,
  SUM(CASE WHEN attempts>=1 AND status='done'      THEN 1 ELSE 0 END) any_attempt_done
FROM tasks;

----------------------------------------------------------------------
-- Section C — Goal flow & blockers
----------------------------------------------------------------------

-- C1: Goal status breakdown + created_by
SELECT status, created_by, COUNT(*) n
FROM goals GROUP BY status, created_by ORDER BY status, created_by;

-- C2: Completed goals — cycle cost (uses completed_at when set, else updated_at)
SELECT id, title, created_by,
       ROUND(EXTRACT(EPOCH FROM (COALESCE(completed_at, updated_at) - created_at))/3600::numeric, 1) hours,
       completed_at IS NOT NULL AS has_completed_at
FROM goals WHERE status='done' ORDER BY hours;

-- C3: Blocker free-text dump (tasks currently blocked)
SELECT id, title, blocked_reason FROM tasks WHERE status='blocked';

-- C4: Credential-blocked cycle share (coarse keyword match)
SELECT
  SUM(CASE WHEN action='check_email' AND summary ILIKE '%skipped%' THEN 1 ELSE 0 END) email_skipped,
  SUM(CASE WHEN action='check_email'                                THEN 1 ELSE 0 END) email_total,
  SUM(CASE WHEN summary ILIKE '%credential%'
             OR summary ILIKE '%no key%'
             OR summary ILIKE '%missing%'
             OR summary ILIKE '%devto_api_key%'
             OR summary ILIKE '%agentmail_api_key%'          THEN 1 ELSE 0 END) credential_mentions,
  COUNT(*) total_log_rows
FROM execution_log;

----------------------------------------------------------------------
-- Section D — Cycle productivity over time
----------------------------------------------------------------------

-- D1: execution_log action breakdown (global)
SELECT action, COUNT(*) n,
       ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 1) pct
FROM execution_log GROUP BY action ORDER BY n DESC;

-- D2: Weekly action trend (ISO week buckets)
SELECT TO_CHAR(date_trunc('week', created_at), 'IYYY-"W"IW') iso_week,
       COUNT(*) total,
       SUM(CASE WHEN action='execute'     THEN 1 ELSE 0 END) executes,
       SUM(CASE WHEN action='reflect'     THEN 1 ELSE 0 END) reflects,
       SUM(CASE WHEN action='check_email' THEN 1 ELSE 0 END) emails
FROM execution_log GROUP BY 1 ORDER BY 1;

----------------------------------------------------------------------
-- Section E — Learnings corpus shape
----------------------------------------------------------------------

-- E1: Learnings by category (corpus shape + mean confidence)
SELECT category, COUNT(*) n,
       ROUND(AVG(confidence)::numeric, 2) avg_conf,
       SUM(CASE WHEN confidence<0.5  THEN 1 ELSE 0 END) low_conf,
       SUM(CASE WHEN confidence>=0.8 THEN 1 ELSE 0 END) high_conf
FROM learnings GROUP BY category ORDER BY n DESC;

-- End of retrospective-queries.sql
