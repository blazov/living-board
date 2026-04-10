# living-board-cli

A small terminal client for the [Living Board](https://github.com/blazov/living-board)
autonomous-agent schema. Read your goals, tasks, execution log, learnings,
and snapshots straight from Supabase, from any shell.

```
$ lb stats
goals                       in_progress=3, pending=2, done=2
tasks                       done=14, in_progress=1, pending=8
recent actions (last 500)   execute=42, reflect=2
learnings (total)           37
```

## Why

The Living Board agent stores all of its state in Supabase
(`goals`, `tasks`, `execution_log`, `learnings`, `snapshots`,
`goal_comments`). The dashboard is the polished view, but for quick
inspection from a terminal — especially when SSH'd into a runner box
or when the dashboard is not deployed — a one-shot CLI is faster.

`living-board-cli`:

- **Zero runtime dependencies.** Pure stdlib (`urllib`, `argparse`,
  `dataclasses`). Install it anywhere Python 3.10+ runs.
- **Read-only by default.** Uses your Supabase **anon key** over
  PostgREST. The only write command is `comment` (insert into
  `goal_comments`), and it is opt-in.
- **Both interactive and JSON output.** Pipe `--json` into `jq` to
  build your own dashboards.

## Install

```bash
pip install living-board-cli
```

Or from source:

```bash
git clone https://github.com/blazov/living-board.git
cd living-board/artifacts/code/living-board-cli
pip install .
```

## Configure

The CLI reads credentials from environment variables. It looks at
the Living-Board–scoped variables first, then falls back to the
`NEXT_PUBLIC_*` names that the Living Board dashboard already uses,
so you can usually point it at an existing `dashboard/.env.local`
without changing anything.

```bash
export NEXT_PUBLIC_SUPABASE_URL=https://YOUR-PROJECT.supabase.co
export NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJhbGc...

# Or, if you prefer scoped vars:
export LIVING_BOARD_SUPABASE_URL=https://YOUR-PROJECT.supabase.co
export LIVING_BOARD_SUPABASE_KEY=eyJhbGc...
```

Verify:

```bash
$ lb check
OK — Supabase reachable and goals table queryable
```

## Commands

| Command | What it does |
|---|---|
| `lb goals` | List goals (default: `in_progress`, `pending`) |
| `lb tasks` | List tasks; filter by `--goal <uuid>` |
| `lb log` | Show recent `execution_log` entries |
| `lb learnings` | List learnings; filter by `--goal` and `--category` |
| `lb snapshot` | Show the most recent snapshot |
| `lb stats` | Aggregate counts across the board |
| `lb comment <goal_id> <text>` | Add a `goal_comments` entry |
| `lb check` | Verify credentials and connectivity |

Both `living-board` and the shorter `lb` are installed as entry points.

### Examples

List all goals including completed ones:

```bash
lb goals --status in_progress pending done blocked
```

Show tasks for a specific goal:

```bash
lb tasks --goal 8c4d2a6e-1234-4f5b-bd11-7f3aa2b5c910
```

Recent execution log as JSON, piped into `jq`:

```bash
lb log --limit 50 --json | jq '.[] | {action, summary}'
```

Add a direction-change comment to a goal:

```bash
lb comment 8c4d2a6e-1234-4f5b-bd11-7f3aa2b5c910 \
  "Pivot to Dev.to publishing — Substack channel is blocked." \
  --type direction_change
```

## Schema assumptions

`living-board-cli` is built against the Living Board schema described in
[`artifacts/living-board-template/schema.sql`](../../living-board-template/schema.sql).
The relevant tables and columns:

- `goals(id, title, status, priority, created_by, created_at)`
- `tasks(id, goal_id, title, status, sort_order, attempts, max_attempts, created_at)`
- `execution_log(id, action, summary, goal_id, task_id, created_at)`
- `learnings(id, goal_id, category, content, confidence, created_at)`
- `snapshots(content, current_focus, cycle_count, created_at)`
- `goal_comments(goal_id, author, comment_type, content)`

If you have a customised schema, the queries are simple PostgREST URLs
in `commands.py` — adapt them as needed.

## Development

```bash
git clone https://github.com/blazov/living-board.git
cd living-board/artifacts/code/living-board-cli
pip install -e ".[dev]"
PYTHONPATH=src python -m pytest
```

The test suite runs entirely offline — `Client._request` is the only
function that touches the network and it's stubbed in `tests/test_client.py`.

## License

Apache 2.0 — same as the Living Board project.
