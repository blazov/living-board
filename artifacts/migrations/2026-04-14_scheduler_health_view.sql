-- Migration: scheduler_health_view
-- Applied: 2026-04-14 (cycle 94) via Supabase MCP apply_migration
-- Goal:    331b89e0-9570-40d9-86e0-bb9fea7762c1 (scheduler heartbeat monitoring)
-- Task:    2dd04e42-7055-4829-9d83-0279da6956c9
--
-- Why: The 40-cycle retrospective discovered a 6-day scheduler dropout
-- (W2, Apr 1-9) that produced zero agent-side signal because detection
-- requires being awake. This view surfaces, in one row, the observables
-- needed for an in-band, agent-visible heartbeat check: the last
-- execution_log timestamp, the age of that timestamp in hours, and the
-- count of >6h gaps observed in the last 24h window.
--
-- Shape (intentionally single-row for cheap SELECT from bash/dashboard):
--   last_exec_at       timestamptz  | created_at of most recent execution_log row
--   hours_since_last   numeric(10,3)| (now() - last_exec_at) in hours
--   gap_24h_count      int          | consecutive-pair gaps >6h within last 24h
--   entries_24h        int          | rows inserted in last 24h (sanity counter)
--   computed_at        timestamptz  | server now() at query time
--
-- Verification (run after apply):
--   SELECT * FROM scheduler_health;
--   -- hours_since_last should be small (<2) during active agent work,
--   -- gap_24h_count should be 0 under normal scheduler operation.
--
-- Cycle-94 validation vs hand-check:
--   hand: last_exec_at=2026-04-14 22:19:13.150353+00, hours_since_last≈1.013,
--         gap_24h_count=0, entries_24h=34
--   view: last_exec_at=2026-04-14 22:19:13.150353+00, hours_since_last=1.022
--         (drift from elapsed time between queries), gap_24h_count=0,
--         entries_24h=34 — match.

CREATE OR REPLACE VIEW public.scheduler_health AS
WITH last AS (
  SELECT MAX(created_at) AS last_exec_at FROM public.execution_log
),
pairs_24h AS (
  SELECT created_at,
         LAG(created_at) OVER (ORDER BY created_at) AS prev_ts
  FROM public.execution_log
  WHERE created_at > now() - interval '24 hours'
)
SELECT
  last.last_exec_at,
  CASE
    WHEN last.last_exec_at IS NULL THEN NULL
    ELSE EXTRACT(EPOCH FROM (now() - last.last_exec_at)) / 3600.0
  END::numeric(10,3) AS hours_since_last,
  (SELECT count(*)::int
     FROM pairs_24h
     WHERE prev_ts IS NOT NULL
       AND EXTRACT(EPOCH FROM (created_at - prev_ts)) / 3600.0 > 6) AS gap_24h_count,
  (SELECT count(*)::int FROM public.execution_log
     WHERE created_at > now() - interval '24 hours') AS entries_24h,
  now() AS computed_at
FROM last;
