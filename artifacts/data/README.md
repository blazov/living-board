# Living Board: Open Execution Dataset

Operational telemetry from an autonomous AI agent (Claude) running continuous goal-execution cycles over 44 calendar days. The dataset captures goals, task decomposition, execution logs, extracted learnings, and periodic state snapshots — a complete record of how the agent planned, worked, learned, and adapted.

## Quick Facts

| Metric | Value |
|--------|-------|
| Total records | 1,428 |
| Date range | 2026-03-30 to 2026-05-13 |
| Calendar days | 44 |
| Active days | 28 |
| Goals tracked | 54 |
| Goal completion rate | 74.1% |
| Tasks tracked | 278 |
| Task completion rate | 84.9% |
| Single-attempt success rate | 97.5% |
| Learnings extracted | 509 |
| Execution cycles logged | 344 |
| Avg cycles/day (active days) | 12.3 |

## Files

| File | Records | Description |
|------|---------|-------------|
| `goals.json` | 54 | High-level objectives the agent pursued |
| `tasks.json` | 278 | Concrete work items decomposed from goals |
| `execution_log.json` | 344 | Per-cycle action records |
| `learnings.json` | 509 | Knowledge extracted during execution |
| `snapshots.json` | 235 | Periodic compressed state for agent context |
| `summary-statistics.json` | — | Pre-computed aggregate metrics |

All files are JSON arrays. Each element is one record with the fields described below.

## Table Schemas

### goals

The top-level planning unit. Goals are created by the user or proposed by the agent during reflection cycles.

| Column | Type | Description |
|--------|------|-------------|
| `id` | uuid | Primary key |
| `title` | text | Short goal name |
| `description` | text | Detailed description; may include status notes |
| `status` | text | `pending`, `in_progress`, `done`, `blocked` |
| `priority` | integer | 1 = highest. Range in dataset: 2–9 |
| `metadata` | jsonb | Structured context (e.g., `created_by`, `blocked_reason`) |
| `created_at` | timestamptz | When the goal was created |
| `updated_at` | timestamptz | Last modification time |

**Status values:** `pending` → `in_progress` → `done` or `blocked`

**Priority:** Lower numbers = higher priority. The agent works on goals in priority order.

### tasks

Concrete work items. Each task belongs to one goal and represents roughly one hour of agent work.

| Column | Type | Description |
|--------|------|-------------|
| `id` | uuid | Primary key |
| `goal_id` | uuid | FK → goals.id |
| `title` | text | Short task name |
| `description` | text | What needs to be done |
| `status` | text | `pending`, `done`, `blocked` |
| `sort_order` | integer | Execution sequence within the goal (10, 20, 30…) |
| `attempts` | integer | How many times the agent tried this task |
| `max_attempts` | integer | Retry limit before auto-blocking (default 3) |
| `result` | text | Outcome description (set on completion) |
| `blocked_reason` | text | Why the task couldn't be completed |
| `metadata` | jsonb | Structured context (e.g., `created_by`, `model`) |
| `created_at` | timestamptz | When the task was created |
| `completed_at` | timestamptz | When the task finished (null if not done) |

**Lifecycle:** Tasks start `pending`, become `done` or `blocked`. The agent picks the lowest `sort_order` pending task in the highest-priority active goal.

### execution_log

One entry per agent cycle. Tracks what the agent did each time it woke up.

| Column | Type | Description |
|--------|------|-------------|
| `id` | uuid | Primary key |
| `goal_id` | uuid | FK → goals.id (null for reflection cycles) |
| `task_id` | uuid | FK → tasks.id (null for non-execute actions) |
| `action` | text | Cycle type (see below) |
| `summary` | text | One-line description of what happened |
| `details` | jsonb | Structured outcome data (artifacts, errors, etc.) |
| `created_at` | timestamptz | When the cycle ran |

**Action values:**
- `execute` (234) — Worked on a task
- `reflect` (55) — Reviewed the board, proposed goals, consolidated memory
- `check_email` (43) — Checked the agent's email inbox
- `decompose` (9) — Broke a goal into tasks
- `blocked` (2) — Encountered and logged a blocker
- `close_goal` (1) — Marked a goal complete

### learnings

Knowledge extracted during execution. The agent's persistent memory across cycles.

| Column | Type | Description |
|--------|------|-------------|
| `id` | uuid | Primary key |
| `goal_id` | uuid | FK → goals.id (null = global learning) |
| `task_id` | uuid | FK → tasks.id (null = goal-level learning) |
| `category` | text | Knowledge type (see below) |
| `content` | text | The learning itself, in natural language |
| `confidence` | float | 0.0–1.0. Decays over time; validated learnings increase |
| `created_at` | timestamptz | When extracted |
| `updated_at` | timestamptz | Last confidence adjustment |

**Categories:**
- `operational` (192) — How-to knowledge for the agent's own processes
- `meta` (127) — Cross-goal patterns and self-improvement insights
- `strategy` (110) — Approaches tried, with success/failure tracking
- `domain_knowledge` (80) — Facts about platforms, APIs, tools

**Confidence lifecycle:** Starts at 0.5–0.9 based on evidence strength. Validated learnings gain +0.1 (capped at 1.0). Contradicted learnings lose -0.15. Unvalidated learnings decay -0.1 after 30 days. Pruned below 0.3.

### snapshots

Compressed state written at the end of each cycle. The agent reads the latest snapshot to orient at the start of the next cycle.

| Column | Type | Description |
|--------|------|-------------|
| `id` | uuid | Primary key |
| `content` | text | Natural language summary of current state |
| `active_goals` | jsonb | Array of `{id, title, status, progress_pct}` |
| `current_focus` | text | What the agent should work on next |
| `recent_outcomes` | jsonb | Last 3 task results `{summary, timestamp, success}` |
| `open_blockers` | jsonb | Current blockers `{goal_id, description}` |
| `key_learnings` | jsonb | Top 5 relevant learnings `{content, confidence, category}` |
| `cycle_count` | integer | Monotonic cycle counter (1–235) |
| `created_at` | timestamptz | When the snapshot was written |

## Entity Relationships

```
goals
  ├── tasks (goal_id → goals.id)         1:N
  ├── execution_log (goal_id → goals.id) 1:N
  ├── learnings (goal_id → goals.id)     1:N
  └── goals (parent_goal_id → goals.id)  self-ref (not in export)

tasks
  ├── execution_log (task_id → tasks.id) 1:N
  └── learnings (task_id → tasks.id)     1:N

snapshots — no foreign keys (self-contained per cycle)
```

Every `execution_log` entry links to the goal and task it operated on. Every `learning` links to the goal (and optionally task) that produced it. Global learnings have `goal_id = null`.

## Example Queries

Load any file with your language of choice. Examples in Python:

```python
import json

with open("goals.json") as f:
    goals = json.load(f)

# Goal completion rate by creator
from collections import Counter
agent_goals = [g for g in goals if (g.get("metadata") or {}).get("created_by") == "agent"]
agent_done = sum(1 for g in agent_goals if g["status"] == "done")
print(f"Agent-proposed goals: {len(agent_goals)}, completed: {agent_done}")
```

```python
# Average tasks per completed goal
with open("tasks.json") as f:
    tasks = json.load(f)

done_goal_ids = {g["id"] for g in goals if g["status"] == "done"}
tasks_per_goal = Counter(t["goal_id"] for t in tasks if t["goal_id"] in done_goal_ids)
avg = sum(tasks_per_goal.values()) / len(tasks_per_goal)
print(f"Avg tasks per completed goal: {avg:.1f}")
```

```python
# Learning confidence distribution
with open("learnings.json") as f:
    learnings = json.load(f)

import statistics
confidences = [l["confidence"] for l in learnings]
print(f"Mean: {statistics.mean(confidences):.2f}, Median: {statistics.median(confidences):.2f}")
```

```python
# Execution cadence — cycles per day
with open("execution_log.json") as f:
    logs = json.load(f)

from collections import Counter
daily = Counter(l["created_at"][:10] for l in logs)
print(f"Most active day: {max(daily, key=daily.get)} ({max(daily.values())} cycles)")
```

## What Makes This Dataset Interesting

- **Complete operational trace** of an autonomous agent from boot to 235+ cycles
- **Goal → task decomposition** shows how an LLM agent breaks down abstract objectives
- **Learning extraction and confidence decay** — a working knowledge management system
- **Blocker patterns** — 100% of blocked goals were credential-blocked, not intelligence-blocked
- **Reflection cycles** — periodic self-assessment with new goal proposals
- **Real-world execution**, not benchmarks — content creation, platform research, email outreach, code generation

## License

MIT. See the repository root for the full license text.

## Citation

```
@dataset{living_board_2026,
  title  = {Living Board: Open Execution Dataset},
  author = {Living Board Agent},
  year   = {2026},
  url    = {https://github.com/blazov/living-board},
  note   = {Operational telemetry from 235+ autonomous agent cycles}
}
```
