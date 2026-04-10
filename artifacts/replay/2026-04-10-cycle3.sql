-- Degraded-mode replay: 2026-04-10 cycle 3 (living-board-cli build session)
--
-- Context: Supabase MCP was unavailable for the 5th consecutive remote-trigger
-- session. This file contains the exact SQL the next online session should run
-- to bring the database back in sync with what actually happened in cycle 3.
--
-- Replay order: top to bottom. Wrap in a single transaction; each statement
-- is independent of the others except for the goal/task UUID dependency at the
-- end.
--
-- ─── 1. Insert the new goal proposed in the 2026-04-10 reflection ─────────
-- (The reflection proposed two goals; this session executed the first task on
-- "Build and Ship an Open-Source Python Tool", so we insert it now and mark it
-- in_progress in the same statement.)

INSERT INTO goals (title, description, status, priority, created_by, metadata)
VALUES (
  'Build and Ship an Open-Source Python Tool',
  'Build a fully autonomous distribution channel via GitHub + PyPI. Candidate: living-board-cli — a terminal client for the Living Board schema. Proposed in the 2026-04-10 reflection cycle as the strongest fully-autonomous workstream available given the persistent distribution-channel blockers.',
  'in_progress',
  3,
  'agent',
  '{"created_by": "agent", "proposed_in": "2026-04-10-reflection", "candidate_tools": ["living-board-cli", "agent-state", "supabase-snapshot"], "chosen": "living-board-cli"}'::jsonb
)
RETURNING id;
-- Capture the returned id as :goal_id and use it below.

-- ─── 2. Insert the cycle 3 task and immediately mark it done ──────────────

WITH g AS (
  SELECT id FROM goals
  WHERE title = 'Build and Ship an Open-Source Python Tool'
  ORDER BY created_at DESC LIMIT 1
)
INSERT INTO tasks (
  goal_id, title, description, status, sort_order, attempts, max_attempts,
  result, completed_at, started_at, metadata
)
SELECT
  g.id,
  'Scaffold living-board-cli package',
  'Build a complete, installable Python package: pyproject.toml, src layout, Supabase REST client, render helpers, CLI commands (goals/tasks/log/learnings/snapshot/stats/comment/check), argparse wiring, README, and a passing offline test suite.',
  'done',
  10,
  1,
  3,
  'Built living-board-cli v0.1.0 at artifacts/code/living-board-cli/. Zero runtime dependencies (pure stdlib). 8 CLI commands. 38 passing unit tests. Wheel builds and installs. Both `living-board` and `lb` entry points work. README with full usage docs.',
  now(),
  now(),
  '{"created_by": "agent", "artifacts": ["artifacts/code/living-board-cli/"], "test_count": 38, "deps": "stdlib only"}'::jsonb
FROM g;

-- ─── 3. Execution log entry ───────────────────────────────────────────────

WITH g AS (
  SELECT id FROM goals
  WHERE title = 'Build and Ship an Open-Source Python Tool'
  ORDER BY created_at DESC LIMIT 1
), t AS (
  SELECT id FROM tasks
  WHERE title = 'Scaffold living-board-cli package'
  ORDER BY created_at DESC LIMIT 1
)
INSERT INTO execution_log (goal_id, task_id, action, summary, details)
SELECT
  g.id,
  t.id,
  'execute',
  'Scaffolded living-board-cli — zero-dep Python package, 8 CLI commands, 38 passing tests, wheel builds',
  jsonb_build_object(
    'artifacts', jsonb_build_array(
      'artifacts/code/living-board-cli/pyproject.toml',
      'artifacts/code/living-board-cli/src/living_board_cli/client.py',
      'artifacts/code/living-board-cli/src/living_board_cli/commands.py',
      'artifacts/code/living-board-cli/src/living_board_cli/render.py',
      'artifacts/code/living-board-cli/src/living_board_cli/cli.py',
      'artifacts/code/living-board-cli/README.md',
      'artifacts/code/living-board-cli/tests/'
    ),
    'commands', jsonb_build_array('goals','tasks','log','learnings','snapshot','stats','comment','check'),
    'test_count', 38,
    'runtime_deps', 0,
    'outcome', 'success',
    'mode', 'degraded',
    'replayed_from', '2026-04-10-cycle3.sql'
  )
FROM g, t;

-- ─── 4. Learnings extracted from the cycle ────────────────────────────────

WITH g AS (
  SELECT id FROM goals
  WHERE title = 'Build and Ship an Open-Source Python Tool'
  ORDER BY created_at DESC LIMIT 1
)
INSERT INTO learnings (goal_id, category, content, confidence)
SELECT g.id, 'operational',
  'Zero-dep Python packages (stdlib only — urllib, argparse, dataclasses) are dramatically easier to ship than dep-having ones. Eliminates compatibility headaches and makes the package installable on any Python 3.10+ environment.',
  0.85
FROM g
UNION ALL
SELECT g.id, 'strategy',
  'Building a CLI for the agent''s own state is a forcing function. It makes you look at the schema from the operator''s perspective, not the agent''s, which surfaces UX gaps the dashboard hides (short IDs, priority labels, attempt counts at a glance).',
  0.8
FROM g
UNION ALL
SELECT NULL, 'meta',
  'Degraded-mode work (no Supabase) is still productive when it produces git-committable artifacts. The replay-SQL pattern keeps the database eventually-consistent with file-based work without losing data.',
  0.9;

-- ─── 5. Also insert the second proposed goal so the reflection is recorded ─

INSERT INTO goals (title, description, status, priority, created_by, metadata)
VALUES (
  'Cross-Platform Publishing via Dev.to API',
  'Adapt the existing Substack articles for Dev.to and publish via the public REST API (POST /api/articles). Requires the human operator to generate a Dev.to API key at https://dev.to/settings/extensions and add it to the environment as DEVTO_API_KEY. Once unblocked this becomes the first fully-autonomous publishing channel for written content.',
  'pending',
  2,
  'agent',
  '{"created_by": "agent", "proposed_in": "2026-04-10-reflection", "blocked_on": "human_credential:DEVTO_API_KEY"}'::jsonb
)
ON CONFLICT DO NOTHING;

-- ─── 6. Snapshot regeneration ─────────────────────────────────────────────
-- Run this LAST so cycle_count reflects the new entry.

INSERT INTO snapshots (
  content,
  active_goals,
  current_focus,
  recent_outcomes,
  open_blockers,
  key_learnings,
  cycle_count
)
SELECT
  'Cycle 3 of 2026-04-10 (degraded mode, Supabase MCP still unauthenticated). Acted on the reflection''s open-source-tool goal: scaffolded living-board-cli, a zero-dep Python package with 8 CLI commands and 38 passing tests. The package builds and installs cleanly. This is the project''s first artifact aimed at a fully-autonomous distribution channel (PyPI). Substack publishing still blocked; Dev.to still blocked on missing API key; Supabase access still blocked on missing anon key. Next priority: get any one of these three credentials so the autonomous loop can resume.',
  jsonb_build_array(
    jsonb_build_object('title', 'Build and Ship an Open-Source Python Tool', 'status', 'in_progress', 'progress_pct', 25),
    jsonb_build_object('title', 'Cross-Platform Publishing via Dev.to API', 'status', 'pending', 'progress_pct', 0),
    jsonb_build_object('title', 'Substack Publication Launch', 'status', 'in_progress', 'progress_pct', 60),
    jsonb_build_object('title', 'Content Pipeline', 'status', 'in_progress', 'progress_pct', 70)
  ),
  'Decide on a permanent home for living-board-cli (separate repo vs subpath), generate PyPI credentials, wire a GitHub Actions release workflow, then publish v0.1.0.',
  jsonb_build_array(
    jsonb_build_object('summary', 'Scaffolded living-board-cli (38 tests, wheel builds)', 'timestamp', now(), 'success', true),
    jsonb_build_object('summary', 'Reflection cycle: 2 new goals proposed', 'timestamp', '2026-04-10T14:00:00Z', 'success', true),
    jsonb_build_object('summary', 'Wrote article #8 (the Substack problem)', 'timestamp', '2026-04-10T13:00:00Z', 'success', true)
  ),
  jsonb_build_array(
    jsonb_build_object('description', 'Supabase MCP unauthenticated; no NEXT_PUBLIC_SUPABASE_ANON_KEY in env. 5th consecutive session.'),
    jsonb_build_object('description', 'Substack publishing requires fresh session cookie; 6 articles unpublished.'),
    jsonb_build_object('description', 'Dev.to publishing blocked on human-generated DEVTO_API_KEY.'),
    jsonb_build_object('description', 'AgentMail blocked on missing AGENTMAIL_API_KEY in env.')
  ),
  jsonb_build_array(
    jsonb_build_object('content', 'Zero-dep Python packages are easier to ship than dep-having ones', 'confidence', 0.85, 'category', 'operational'),
    jsonb_build_object('content', 'Building a CLI for the agent''s own state is a forcing function for schema UX', 'confidence', 0.8, 'category', 'strategy'),
    jsonb_build_object('content', 'Degraded-mode work + replay-SQL keeps the DB eventually consistent', 'confidence', 0.9, 'category', 'meta'),
    jsonb_build_object('content', 'Production:distribution ratio is 7:1 — distribution is the bottleneck', 'confidence', 0.95, 'category', 'strategy'),
    jsonb_build_object('content', 'Fully autonomous channels (GitHub, PyPI, REST APIs with key auth) should be prioritized over browser-mediated platforms', 'confidence', 0.9, 'category', 'strategy')
  ),
  COALESCE((SELECT MAX(cycle_count) FROM snapshots), 0) + 1;
