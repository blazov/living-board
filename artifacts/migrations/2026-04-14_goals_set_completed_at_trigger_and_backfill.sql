-- Migration: goals_set_completed_at_trigger_and_backfill
-- Applied: 2026-04-14 (cycle 83) via Supabase MCP apply_migration
-- Goal:    8fc57114-0593-4a7f-9dba-385c41ecfecb
-- Task:    9c6fe2da-48e8-418a-a8ec-b779556d1d93
--
-- Why: goals.completed_at coverage was 5/14 (~36%) on 'done' goals.  Past
-- cycles tried to fix this with CLAUDE.md checklist nudges and a
-- high-confidence learning (684897f5).  Both failed — the gap kept
-- recurring.  This migration moves the invariant into the schema so it
-- cannot be forgotten.
--
-- Behaviour:
--   * BEFORE INSERT — if status='done' and completed_at is NULL, stamp now()
--   * BEFORE UPDATE — transitioning into 'done' stamps completed_at;
--                     transitioning out of 'done' clears it;
--                     a row that's already 'done' but lost completed_at
--                     self-heals to OLD.completed_at or now()
--   * Backfill — for all 'done' goals with NULL completed_at, set to:
--                MAX(tasks.completed_at) for that goal,
--                else goals.updated_at, else goals.created_at, else now()
--
-- Verification (run after apply):
--   SELECT count(*) FROM goals WHERE status='done' AND completed_at IS NULL;
--   -- expected: 0

CREATE OR REPLACE FUNCTION public.goals_set_completed_at()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
  IF TG_OP = 'INSERT' THEN
    IF NEW.status = 'done' AND NEW.completed_at IS NULL THEN
      NEW.completed_at := now();
    END IF;
    RETURN NEW;
  END IF;

  -- UPDATE
  IF NEW.status = 'done' AND COALESCE(OLD.status, '') <> 'done' THEN
    IF NEW.completed_at IS NULL THEN
      NEW.completed_at := now();
    END IF;
  ELSIF NEW.status <> 'done' AND OLD.status = 'done' THEN
    NEW.completed_at := NULL;
  ELSIF NEW.status = 'done' AND OLD.status = 'done' AND NEW.completed_at IS NULL THEN
    NEW.completed_at := COALESCE(OLD.completed_at, now());
  END IF;

  RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS goals_set_completed_at_ins ON public.goals;
CREATE TRIGGER goals_set_completed_at_ins
BEFORE INSERT ON public.goals
FOR EACH ROW EXECUTE FUNCTION public.goals_set_completed_at();

DROP TRIGGER IF EXISTS goals_set_completed_at_upd ON public.goals;
CREATE TRIGGER goals_set_completed_at_upd
BEFORE UPDATE OF status, completed_at ON public.goals
FOR EACH ROW EXECUTE FUNCTION public.goals_set_completed_at();

WITH src AS (
  SELECT g.id,
         COALESCE(
           (SELECT MAX(t.completed_at) FROM public.tasks t
              WHERE t.goal_id = g.id AND t.completed_at IS NOT NULL),
           g.updated_at,
           g.created_at,
           now()
         ) AS chosen
  FROM public.goals g
  WHERE g.status = 'done' AND g.completed_at IS NULL
)
UPDATE public.goals g
SET completed_at = src.chosen
FROM src
WHERE g.id = src.id;
