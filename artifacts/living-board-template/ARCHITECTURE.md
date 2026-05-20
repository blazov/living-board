# Architecture

This document describes the Living Board database schema, agent cycle, reflection system, memory architecture, and model delegation strategy. For full DDL, see [`schema.sql`](schema.sql).

## Database Schema

Seven tables organized into three layers: execution, memory, and collaboration.

### ER Diagram

```
┌──────────────────────┐
│        goals         │
├──────────────────────┤
│ id          UUID  PK │
│ title       TEXT     │
│ description TEXT     │
│ status      TEXT     │─── pending | in_progress | done | blocked
│ priority    INT      │─── 1 (highest) to 10 (lowest)
│ parent_goal_id UUID  │──┐ self-referencing hierarchy
│ created_by  TEXT     │  │ 'user' or 'agent'
│ metadata    JSONB    │  │
│ created_at  TSTZ     │  │
│ updated_at  TSTZ     │  │
│ completed_at TSTZ    │  │ auto-set by trigger on status='done'
└──────┬───┬───┬───┬───┘  │
       │   │   │   │      │
       │   │   │   └──────┘
       │   │   │
       │   │   │  ┌──────────────────────┐
       │   │   │  │   goal_comments      │
       │   │   │  ├──────────────────────┤
       │   │   └─→│ id          UUID  PK │
       │   │      │ goal_id     UUID  FK │──→ goals.id
       │   │      │ author      TEXT     │─── 'user' or 'agent'
       │   │      │ comment_type TEXT    │─── question | direction_change | feedback | note
       │   │      │ content     TEXT     │
       │   │      │ acknowledged_at TSTZ │
       │   │      │ agent_response TEXT  │
       │   │      └──────────────────────┘
       │   │
       │   │      ┌──────────────────────┐
       │   │      │       tasks          │
       │   │      ├──────────────────────┤
       │   └─────→│ id          UUID  PK │
       │          │ goal_id     UUID  FK │──→ goals.id
       │          │ title       TEXT     │
       │          │ description TEXT     │
       │          │ status      TEXT     │─── pending | in_progress | done | blocked
       │          │ sort_order  INT      │
       │          │ attempts    INT      │
       │          │ max_attempts INT     │─── default 3
       │          │ result      TEXT     │
       │          │ blocked_reason TEXT  │
       │          │ depends_on  UUID[]   │
       │          │ metadata    JSONB    │─── {model, created_by, ...}
       │          └──────┬───────────────┘
       │                 │
       │   ┌─────────────┘
       │   │
       ▼   ▼
┌──────────────────────┐     ┌──────────────────────┐
│    execution_log     │     │      learnings       │
├──────────────────────┤     ├──────────────────────┤
│ id          UUID  PK │     │ id          UUID  PK │
│ trigger_run_id TEXT  │     │ goal_id     UUID  FK │──→ goals.id (NULL = global)
│ goal_id     UUID  FK │──→  │ task_id     UUID  FK │──→ tasks.id
│ task_id     UUID  FK │──→  │ category    TEXT     │─── domain_knowledge | strategy
│ action      TEXT     │     │                      │    operational | meta
│ summary     TEXT     │     │ content     TEXT     │
│ details     JSONB    │     │ confidence  REAL     │─── 0.0 to 1.0, decays over time
│ duration_ms INT      │     │ times_validated INT  │
│ created_at  TSTZ     │     │ created_at  TSTZ     │
└──────────────────────┘     │ updated_at  TSTZ     │
                             └──────────────────────┘

┌──────────────────────┐     ┌──────────────────────┐
│      snapshots       │     │    agent_config      │
├──────────────────────┤     ├──────────────────────┤
│ id          UUID  PK │     │ key         TEXT  PK │
│ content     TEXT     │     │ value       JSONB    │
│ active_goals JSONB   │     │ updated_at  TSTZ     │
│ current_focus TEXT   │     └──────────────────────┘
│ recent_outcomes JSONB│
│ open_blockers JSONB  │
│ key_learnings JSONB  │
│ cycle_count   INT    │
│ created_at  TSTZ     │
└──────────────────────┘
```

### Relationships

| Parent | Child | Cardinality | FK Column |
|--------|-------|-------------|-----------|
| `goals` | `tasks` | 1:N | `tasks.goal_id` |
| `goals` | `goal_comments` | 1:N | `goal_comments.goal_id` |
| `goals` | `execution_log` | 1:N | `execution_log.goal_id` |
| `goals` | `learnings` | 1:N | `learnings.goal_id` (nullable — NULL means global) |
| `goals` | `goals` | 1:N | `goals.parent_goal_id` (self-referencing hierarchy) |
| `tasks` | `execution_log` | 1:N | `execution_log.task_id` |
| `tasks` | `learnings` | 1:N | `learnings.task_id` |
| — | `snapshots` | standalone | append-only compressed state |
| — | `agent_config` | standalone | key-value operational settings |

### Invariant Triggers

`goals_set_completed_at` — fires on INSERT and UPDATE of `goals`. Automatically stamps `completed_at = now()` when `status` transitions to `done`, and clears it when status transitions away from `done`. This makes completion timestamps structural rather than relying on agent discipline.

### Observability Views

`scheduler_health` — single-row view computed from `execution_log`. Reports the last execution timestamp, age in hours, 24-hour entry count, and count of consecutive gaps exceeding 6 hours. Used by `cycle-start.sh` to detect silent scheduler dropouts.

## Agent Cycle

Every cycle follows four phases in strict order. Each cycle completes exactly one task (or one reflection).

```
Phase 0       Phase 1        Phase 2       Phase 3       Phase 4
 Sync    →    Orient    →    Decide   →    Execute  →    Record
 git pull     read state     pick one      do work       write results
              check          task          produce       log execution
              comments                     artifacts     extract learnings
              search memory                              regenerate snapshot
```

### Phase 0: Sync

Runs `cycle-start.sh` as the literal first bash call. Ensures `master == origin/master` — handles detached HEAD, fast-forward, and disjoint-seed cases. Appends a scheduler heartbeat line for dropout detection.

### Phase 1: Orient

1. **Read snapshot** — loads the latest compressed state from `snapshots` for fast boot. Falls back to full table queries if stale (>2h) or missing, and to a local JSON backup if the database is unreachable.
2. **Check user comments** — queries `goal_comments` for unacknowledged entries. Processes each by type (`direction_change` adjusts priorities, `question` gets answered, `feedback` becomes a learning, `note` is acknowledged).
3. **Check GitHub issues** — responds to `question` and `goal-suggestion` labeled issues, and answers new AMA thread comments.
4. **Semantic memory recall** — searches the vector DB (if available) for context relevant to the current goal/task.

### Phase 2: Decide

Picks exactly one task using this priority cascade:

1. Continue any `in_progress` task.
2. Take the first `pending` task (by `sort_order`) from the highest-priority `in_progress` goal.
3. If a goal has no tasks, decompose it into 3-8 concrete tasks first.
4. If a task has exhausted `max_attempts`, mark it `blocked` and move on.
5. If all tasks in a goal are `done`, mark the goal `done`.

### Phase 3: Execute

Does the actual work using available tools: web search/fetch, bash, file I/O, email, MCP connectors. Can delegate to a subagent with a different model if `metadata.model` is set on the task or goal (see Model Delegation below).

### Phase 4: Record

1. Update task status and result.
2. Update goal status if changed.
3. Write an `execution_log` entry with action, summary, and JSON details.
4. Extract learnings — dual-write to Supabase `learnings` table and optional mem0 vector DB.
5. Generate a new `snapshots` row compressing current state.
6. Export `artifacts/state/latest-snapshot.json` as an offline fallback.
7. Regenerate the live README section from the snapshot.
8. Commit any artifacts produced.

## Reflection Cycle

Reflections replace the normal Decide→Execute flow 2-3 times per day. The gate triggers when **both**: (a) 8+ hours since last reflection AND (b) 3+ execution cycles since last reflection. A 48-hour hard ceiling forces reflection regardless.

During reflection, the agent:

1. **Reviews the full board** — all goals, recent learnings, last 10 execution log entries.
2. **Proposes new goals** — 1-2 new goals inserted as `pending` with `created_by = 'agent'`.
3. **Checks email** — reads the agent's inbox, responds to actionable messages.
4. **Consolidates memory** — deduplicates vector DB entries, reviews strategy success/failure rates.
5. **Runs learning hygiene** — decays stale learnings (-0.1 confidence if >30 days untouched), prunes low-confidence entries (<0.3), normalizes categories, validates a random sample of 5 learnings against recent outcomes.

## Memory System

Dual-layer architecture: structured storage for the dashboard, semantic search for cross-goal reasoning.

```
                    ┌─────────────────┐
                    │   Agent Cycle   │
                    └────────┬────────┘
                             │
              ┌──────────────┼──────────────┐
              │ write        │ write        │ search
              ▼              ▼              ▼
┌─────────────────┐  ┌─────────────────────────┐
│    Supabase     │  │     mem0 (optional)      │
│   `learnings`   │  │                          │
│                 │  │  Qdrant vector DB        │
│ - per-goal or   │  │  + Ollama embeddings     │
│   global        │  │  (nomic-embed-text)      │
│ - confidence    │  │                          │
│   scores        │  │  - semantic similarity   │
│ - 4 categories  │  │    search across all     │
│ - dashboard-    │  │    learnings             │
│   visible       │  │  - cross-goal pattern    │
│                 │  │    recognition           │
│ Source of truth │  │  - strategy tracking     │
└─────────────────┘  └─────────────────────────┘
```

**Always dual-write**: every learning goes to both layers. Supabase is the source of truth (always available). mem0 adds semantic search (available only when Qdrant + Ollama are running locally).

### Learning Categories

| Category | Purpose | Example |
|----------|---------|---------|
| `domain_knowledge` | Facts about platforms, APIs, tools | "Substack has no public API for publishing" |
| `strategy` | Approaches tried, with outcomes | "Cold outreach via email: 0/5 response rate" |
| `operational` | How-to knowledge for the agent | "Always commit artifacts in the same cycle as creation" |
| `meta` | Cross-goal patterns, self-improvement | "Production without distribution is wasted effort" |

### Confidence Lifecycle

- Starts at 0.5 (or set by the agent based on certainty)
- Validated against outcomes: +0.1 per confirmation, -0.15 per contradiction (cap 1.0)
- Decays -0.1 if untouched for 30+ days
- Pruned when confidence drops below 0.3

## Model Delegation

Tasks and goals can specify a `model` in their `metadata` JSONB field. The executing agent checks this before starting work and delegates to a subagent if the specified model differs from the current one.

| Model | Use Case | Cost |
|-------|----------|------|
| **Opus** (default) | Goal decomposition, strategic planning, complex research, creative writing | Highest |
| **Sonnet** | Standard execution, email, data gathering, file operations | Medium |
| **Haiku** | Status checks, formatting, lookups, mechanical updates | Lowest |

Task-level `metadata.model` overrides goal-level. If no model is specified, the task runs on the current agent's model (typically Opus).

## Goal Decomposition

When a goal has no tasks, the agent decomposes it into 3-8 concrete, single-cycle tasks:

- Ordered by `sort_order` (10, 20, 30... to allow insertions)
- Research/discovery tasks come first
- Each task should be completable in one hour
- Tasks that require manual user action are flagged in the description
- Metadata records `created_by: "agent"` and `decomposed_at` timestamp

## File Layout

```
artifacts/
├── living-board-template/
│   ├── schema.sql            # DDL for all 7 tables + triggers + views
│   ├── seed-data.sql         # Example goal, tasks, and learnings
│   ├── CLAUDE.md.template    # Agent instructions with {{PLACEHOLDERS}}
│   ├── template-setup.sh     # Interactive setup — generates CLAUDE.md
│   ├── fork-init.sh          # One-time cleanup for forks
│   ├── QUICKSTART.md         # Zero to running agent in 10 minutes
│   ├── ARCHITECTURE.md       # This document
│   └── README.md             # Full project overview
├── scripts/
│   ├── cycle-start.sh        # Phase 0 — git sync + heartbeat
│   ├── mem0_helper.py        # Semantic memory CLI
│   ├── export-snapshot.sh    # Local state backup
│   ├── generate-live-readme.py  # README live-state regeneration
│   └── ...
├── state/
│   └── latest-snapshot.json  # Offline fallback for Phase 1
└── content/                  # Agent-produced artifacts
```
