# Living Board

An autonomous agent framework that runs on a goal-task-learning loop. The agent wakes up on a schedule, reads its state from a database, picks a task, executes it, records results, and goes back to sleep. Over time, it accumulates learnings and proposes its own goals.

## How It Works

```
┌─────────────────────────────────────────────────┐
│                  Agent Cycle                     │
│                                                  │
│  ┌──────────┐  ┌──────────┐  ┌───────────────┐  │
│  │  Orient  │→ │  Decide  │→ │    Execute    │  │
│  │          │  │          │  │               │  │
│  │ Read DB  │  │ Pick one │  │ Do the work,  │  │
│  │ state    │  │ task     │  │ make artifacts│  │
│  └──────────┘  └──────────┘  └───────────────┘  │
│       ↑                       │               │
│       │        ┌──────────┐  │               │
│       └────────│  Record  │──┘               │
│                │          │                      │
│                │ Update DB│                      │
│                │ + log    │                      │
│                └──────────┘                      │
└─────────────────────────────────────────────────┘
```

Every 2-3 cycles, the agent runs a **reflection** instead: it reviews the full board, thinks about what's working and what isn't, and proposes new goals.

## Architecture

- **Database**: [Supabase](https://supabase.com) (Postgres) — stores goals, tasks, execution logs, and learnings
- **Agent**: [Claude Code](https://docs.anthropic.com/en/docs/claude-code) with MCP connectors for Supabase, Gmail, GitHub, etc.
- **Scheduler**: Claude Code [scheduled triggers](https://docs.anthropic.com/en/docs/claude-code/scheduled-triggers) — runs the agent on a cron schedule

## Database Schema

Four tables power the system:

| Table | Purpose |
|-------|---------|
| `goals` | High-level objectives with priority and status |
| `tasks` | Concrete steps within a goal, ordered by `sort_order` |
| `execution_log` | Audit trail of every agent cycle |
| `learnings` | Accumulated knowledge with confidence scores |

See [`schema.sql`](schema.sql) for the full DDL.

## Quick Start

### 1. Set up Supabase

1. Create a [Supabase project](https://supabase.com/dashboard).
2. Run [`schema.sql`](schema.sql) in the SQL editor.
3. Optionally run [`seed-data.sql`](seed-data.sql) for example data.

### 2. Configure the agent

1. Copy [`CLAUDE.md.template`](CLAUDE.md.template) to `CLAUDE.md` in your repo root.
2. Replace `{{SUPABASE_PROJECT_ID}}` with your project ID.
3. Replace `{{AVAILABLE_TOOLS}}` with the MCP tools you have configured.

### 3. Set up MCP connectors

Add the [Supabase MCP connector](https://github.com/supabase/mcp-server-supabase) to your Claude Code configuration so the agent can read/write the database.

### 4. Schedule the agent

Use Claude Code scheduled triggers to run the agent on a cron:

```bash
claude trigger create --name "living-board" \
  --schedule "0 * * * *" \
  --prompt "Execute your full agent cycle as defined in CLAUDE.md."
```

### 5. Add your first goal

```sql
INSERT INTO goals (title, description, status, priority)
VALUES ('My first goal', 'Description of what to accomplish', 'in_progress', 3);
```

The agent will decompose it into tasks on its next cycle.

## Design Principles

- **Stateless agent, stateful database.** The agent has no memory between cycles. All state lives in Supabase.
- **One task per cycle.** Focus prevents half-finished work.
- **Learnings compound.** The agent extracts reusable knowledge from every cycle and queries it for context in future cycles.
- **Self-directed goals.** The agent can propose its own goals during reflection cycles, not just execute what it's told.
- **Everything is logged.** The execution log is a complete history of what the agent did and why.

## Customization

- **Priority**: Lower number = higher priority. Goals at priority 1 are worked on before priority 5.
- **Model delegation**: Set `metadata.model` on goals or tasks to delegate work to different Claude models (opus, sonnet, haiku).
- **Task dependencies**: Use the `depends_on` array on tasks to enforce ordering beyond `sort_order`.
- **Learning categories**: Use categories like `domain_knowledge`, `strategy`, `operational`, `market_intelligence` to organize accumulated knowledge.

## License

MIT
