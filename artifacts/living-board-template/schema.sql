-- Living Board: Autonomous Agent Schema
-- Run this in your Supabase SQL editor to set up the database.

-- Goals: high-level objectives the agent works toward
CREATE TABLE goals (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  title TEXT NOT NULL,
  description TEXT,
  status TEXT NOT NULL DEFAULT 'pending',  -- pending, in_progress, done, blocked
  priority INTEGER NOT NULL DEFAULT 5,      -- 1 = highest, 10 = lowest
  parent_goal_id UUID REFERENCES goals(id),
  created_by TEXT DEFAULT 'user',           -- 'user' or 'agent'
  metadata JSONB DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now(),
  completed_at TIMESTAMPTZ
);

-- Tasks: concrete steps within a goal
CREATE TABLE tasks (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  goal_id UUID NOT NULL REFERENCES goals(id),
  title TEXT NOT NULL,
  description TEXT,
  status TEXT NOT NULL DEFAULT 'pending',   -- pending, in_progress, done, blocked
  sort_order INTEGER NOT NULL DEFAULT 0,
  attempts INTEGER DEFAULT 0,
  max_attempts INTEGER DEFAULT 3,
  result TEXT,
  blocked_reason TEXT,
  depends_on UUID[] DEFAULT '{}',
  metadata JSONB DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now(),
  started_at TIMESTAMPTZ,
  completed_at TIMESTAMPTZ
);

-- Execution Log: audit trail of every agent cycle
CREATE TABLE execution_log (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  trigger_run_id TEXT,                      -- links to scheduled trigger run
  goal_id UUID REFERENCES goals(id),
  task_id UUID REFERENCES tasks(id),
  action TEXT NOT NULL,                     -- 'execute', 'reflect', 'decompose'
  summary TEXT NOT NULL,
  details JSONB DEFAULT '{}'::jsonb,
  duration_ms INTEGER,
  created_at TIMESTAMPTZ DEFAULT now()
);

-- Learnings: accumulated knowledge across cycles
CREATE TABLE learnings (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  goal_id UUID REFERENCES goals(id),       -- NULL = global learning
  task_id UUID REFERENCES tasks(id),
  category TEXT NOT NULL,                   -- 'domain_knowledge', 'strategy', 'operational', 'market_intelligence'
  content TEXT NOT NULL,
  confidence REAL DEFAULT 0.5,             -- 0.0 to 1.0
  times_validated INTEGER DEFAULT 0,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

-- Snapshots: compressed state for fast agent context loading
CREATE TABLE snapshots (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  content TEXT NOT NULL,                  -- natural language summary of current state
  active_goals JSONB DEFAULT '[]'::jsonb, -- [{id, title, status, progress_pct}]
  current_focus TEXT,                     -- what the agent should work on next
  recent_outcomes JSONB DEFAULT '[]'::jsonb,  -- [{summary, timestamp, success}]
  open_blockers JSONB DEFAULT '[]'::jsonb,    -- [{goal_id, description}]
  key_learnings JSONB DEFAULT '[]'::jsonb,    -- [{content, confidence, category}]
  cycle_count INTEGER DEFAULT 0,
  created_at TIMESTAMPTZ DEFAULT now()
);

-- Goal Comments: human-agent collaboration thread per goal
CREATE TABLE goal_comments (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  goal_id UUID NOT NULL REFERENCES goals(id),
  author TEXT NOT NULL DEFAULT 'user',     -- 'user' or 'agent'
  comment_type TEXT NOT NULL DEFAULT 'note', -- 'question', 'direction_change', 'feedback', 'note'
  content TEXT NOT NULL,
  acknowledged_at TIMESTAMPTZ,             -- when the agent processed this comment
  agent_response TEXT,                     -- the agent's reply
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

-- Agent Config: operational key-value settings
CREATE TABLE agent_config (
  key TEXT PRIMARY KEY,
  value JSONB NOT NULL,
  updated_at TIMESTAMPTZ DEFAULT now()
);

-- Performance indexes
CREATE INDEX idx_goals_status ON goals (status) WHERE status IN ('pending', 'in_progress');
CREATE INDEX idx_tasks_goal_status ON tasks (goal_id, status, sort_order);
CREATE INDEX idx_tasks_status ON tasks (status) WHERE status IN ('pending', 'in_progress');
CREATE INDEX idx_execution_log_created ON execution_log (created_at DESC);
CREATE INDEX idx_learnings_category ON learnings (category);
CREATE INDEX idx_goal_comments_goal ON goal_comments (goal_id, created_at DESC);
CREATE INDEX idx_snapshots_created ON snapshots (created_at DESC);

-- Invariant triggers
--
-- goals.completed_at is stamped automatically whenever a goal transitions to
-- 'done' and cleared when it transitions out of 'done'.  This makes the
-- invariant structural — the agent cannot forget to set it, and retrospective
-- queries on completed_at are trustworthy.  Landed in the main project via
-- artifacts/migrations/2026-04-14_goals_set_completed_at_trigger_and_backfill.sql.
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

-- Observability views
--
-- scheduler_health: single-row summary of agent heartbeat state — the
-- last execution_log timestamp, its age in hours, a 24h window entry
-- count, and a count of consecutive-pair gaps >6h within that window.
-- This exists because scheduler dropouts produce zero agent-side signal
-- (detection requires being awake); Phase 0 of the agent cycle SELECTs
-- from this view to make silent dropouts visible on the next wake.
-- Landed in the main project via
-- artifacts/migrations/2026-04-14_scheduler_health_view.sql.
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
