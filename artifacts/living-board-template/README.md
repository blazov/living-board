# Living Board Template

An autonomous agent framework that runs on a goal-task-learning loop. The agent wakes up on a schedule, reads its state from a database, picks a task, executes it, records results, and goes back to sleep. Over time, it accumulates learnings, proposes its own goals, and collaborates with you through a real-time dashboard.

## How It Works

```
┌─────────────────────────────────────────────────────┐
│                    Agent Cycle                       │
│                                                     │
│  ┌──────────┐  ┌──────────┐  ┌───────────────┐     │
│  │  Orient  │→ │  Decide  │→ │    Execute    │     │
│  │          │  │          │  │               │     │
│  │ Read DB  │  │ Pick one │  │ Do the work,  │     │
│  │ snapshot │  │ task     │  │ make artifacts│     │
│  │ + check  │  │          │  │               │     │
│  │ comments │  │          │  │ Can delegate  │     │
│  │ + search │  │          │  │ to opus/      │     │
│  │ memory   │  │          │  │ sonnet/haiku  │     │
│  └──────────┘  └──────────┘  └───────┬───────┘     │
│       ↑                              │              │
│       │        ┌──────────┐          │              │
│       └────────│  Record  │←─────────┘              │
│                │          │                         │
│                │ Update DB│                         │
│                │ Dual-    │                         │
│                │ write    │                         │
│                │ learnings│                         │
│                └──────────┘                         │
│                                                     │
│         ┌──────────────────────┐                    │
│         │      Reflect         │  (2-3x/day)       │
│         │  Consolidate memory, │                    │
│         │  validate learnings, │                    │
│         │  propose new goals   │                    │
│         └──────────────────────┘                    │
└─────────────────────────────────────────────────────┘
```

Every cycle follows four phases:

| Phase | What Happens |
|-------|-------------|
| **Orient** | Reads the latest snapshot for fast context loading. Checks for user comments on goals. Optionally searches semantic memory (mem0) for cross-goal context. |
| **Decide** | Picks exactly one task — the next pending task from the highest-priority active goal. |
| **Execute** | Does the actual work: web research, writing, API calls, email, file operations. Can delegate to different Claude models (Opus/Sonnet/Haiku) based on task metadata. |
| **Record** | Writes results back. Logs execution. Dual-writes learnings to Supabase + optional vector DB with confidence scores. Regenerates the state snapshot. |

Every 2-3 cycles, the agent runs a **reflection** instead: it reviews the full board, consolidates memories, validates learnings against outcomes, detects failed strategies, and proposes new goals.

## Key Features

- **Persistent dual-layer memory** — Supabase `learnings` table for structured per-goal knowledge, plus optional [mem0](https://github.com/mem0ai/mem0) (Qdrant + Ollama) for semantic search across all knowledge
- **Continuous self-learning** — every cycle extracts reusable knowledge with confidence scores that rise through validation and decay through contradiction
- **Human-agent collaboration** — leave comments (questions, direction changes, feedback) on goals via the dashboard; the agent reads and responds each cycle
- **Model delegation** — routes complex work to Opus, routine tasks to Sonnet, simple lookups to Haiku
- **State snapshots** — compressed state for fast cycle boot; no need to re-query everything each cycle
- **Daily activity digests** — auto-generated daily logs committed to the repo for transparency

## Architecture

- **Database**: [Supabase](https://supabase.com) (Postgres) — stores goals, tasks, execution logs, learnings, snapshots, comments, and config
- **Agent**: [Claude Code](https://docs.anthropic.com/en/docs/claude-code) with MCP connectors for Supabase and other services
- **Scheduler**: Claude Code [scheduled triggers](https://docs.anthropic.com/en/docs/claude-code/remote) — runs the agent on a cron schedule
- **Dashboard**: [Next.js](https://nextjs.org) + React + Tailwind CSS — real-time monitoring and collaboration
- **Memory** (optional): [mem0](https://github.com/mem0ai/mem0) with Qdrant vector DB + Ollama embeddings for semantic search

## Database Schema (7 tables)

| Table | Role | Key Fields |
|-------|------|------------|
| `goals` | **Execution** — high-level objectives | priority, status, parent hierarchy, `created_by` (user or agent) |
| `tasks` | **Execution** — concrete steps per goal | sort_order, attempts/max_attempts, result, blocked_reason |
| `execution_log` | **Execution** — audit trail of every cycle | action type, summary, JSON details, duration |
| `snapshots` | **Execution** — compressed state for fast boot | active_goals, current_focus, recent_outcomes, open_blockers |
| `learnings` | **Memory** — accumulated knowledge | confidence (0-1), category, times_validated, per-goal or global |
| `goal_comments` | **Collaboration** — human-agent threads | comment_type, acknowledged_at, agent_response |
| `agent_config` | **Collaboration** — operational settings | key-value pairs |

See [`schema.sql`](schema.sql) for the full DDL.

## Quick Start

> **Fastest path:** Follow the step-by-step **[Quickstart Guide](QUICKSTART.md)** — it walks you from fork to running agent in 10 minutes using the interactive [`template-setup.sh`](template-setup.sh) script.

The sections below cover each piece in detail if you prefer to set things up manually.

### 1. Set up Supabase

1. Create a [Supabase project](https://supabase.com/dashboard).
2. Run [`schema.sql`](schema.sql) in the SQL editor to create the 7 database tables.
3. Optionally run [`seed-data.sql`](seed-data.sql) for an example goal with tasks and learnings.

### 2. Configure the agent

**Automated** (recommended): run the interactive setup script, which prompts for your project details and generates `CLAUDE.md` with all placeholders filled in:

```bash
bash artifacts/living-board-template/template-setup.sh
cp artifacts/living-board-template/CLAUDE.md ./CLAUDE.md
```

**Manual**: copy [`CLAUDE.md.template`](CLAUDE.md.template) to `CLAUDE.md` in your repo root and replace the `{{PLACEHOLDER}}` variables yourself (see the template for the full list).

### 3. Set up MCP connectors

Add the [Supabase MCP connector](https://github.com/supabase/mcp-server-supabase) to your Claude Code configuration:

```bash
claude mcp add supabase --type url --url https://mcp.supabase.com
```

Or add it manually to `.claude/settings.json`:

```json
{
  "mcpServers": {
    "supabase": {
      "type": "url",
      "url": "https://mcp.supabase.com"
    }
  }
}
```

### 4. Deploy the dashboard (optional)

The dashboard provides real-time monitoring and human-agent collaboration:

```bash
cd dashboard
cp .env.example .env.local
# Fill in your Supabase URL, anon key, and auth secret
npm install
npm run dev
```

Deploy to Vercel:
```bash
npx vercel --prod
```

### 5. Schedule the agent

```bash
claude trigger create --name "living-board" \
  --schedule "0 * * * *" \
  --prompt "Execute your full agent cycle as defined in CLAUDE.md."
```

### 6. Add your first goal

```sql
INSERT INTO goals (title, description, status, priority)
VALUES ('My first goal', 'Description of what to accomplish', 'in_progress', 3);
```

The agent will decompose it into tasks on its next cycle.

### 7. Set up semantic memory (optional)

For cross-goal semantic search, set up mem0 with Qdrant and Ollama:

```bash
# Install Qdrant (vector DB)
docker run -p 6333:6333 qdrant/qdrant

# Install Ollama (local embeddings)
curl -fsSL https://ollama.com/install.sh | sh
ollama pull nomic-embed-text

# Install Python dependencies
pip install qdrant-client requests
```

The agent will automatically use the mem0 helper at `artifacts/scripts/mem0_helper.py` when these services are available.

## Design Principles

- **Stateless agent, stateful database.** The agent has no memory between cycles. All state lives in Supabase. Any session can pick up where the last one left off.
- **One task per cycle.** Focus prevents half-finished work. If a cycle crashes, at most one hour of work is lost.
- **Learnings compound.** The agent extracts reusable knowledge from every cycle and queries it for context in future ones.
- **Self-directed goals.** During reflection cycles, the agent reviews the full board and proposes its own goals.
- **Human-agent collaboration.** Leave comments on goals via the dashboard. The agent reads and responds before starting work each cycle.
- **Everything is logged.** The execution log is a complete history of what the agent did and why.
- **Model delegation.** Complex creative work stays on Opus. Routine tasks go to Sonnet. Simple lookups go to Haiku.

## Customization

| Setting | How |
|---------|-----|
| **Priority** | Lower number = higher priority. Goals at priority 1 are worked before priority 5. |
| **Model delegation** | Set `metadata.model` on goals or tasks to route work to `opus`, `sonnet`, or `haiku`. |
| **Task dependencies** | Use the `depends_on` array on tasks to enforce ordering beyond `sort_order`. |
| **Learning categories** | Use `domain_knowledge`, `strategy`, `operational`, or `meta` to organize accumulated knowledge. |
| **Reflection frequency** | The agent reflects when the last reflection was 8+ hours ago. Adjust in `CLAUDE.md`. |
| **Comment types** | `question`, `direction_change`, `feedback`, `note` — each triggers different agent behavior. |

## File Reference

| File | Purpose |
|------|---------|
| [`CLAUDE.md.template`](CLAUDE.md.template) | Agent instructions template with `{{PLACEHOLDER}}` variables |
| [`template-setup.sh`](template-setup.sh) | Interactive setup script — generates CLAUDE.md and runs schema |
| [`schema.sql`](schema.sql) | Database DDL — creates all 7 tables, indexes, triggers, and views |
| [`seed-data.sql`](seed-data.sql) | Optional example goal, tasks, and learnings |
| [`QUICKSTART.md`](QUICKSTART.md) | Step-by-step guide from zero to running agent in 10 minutes |

## Credits

Built on the [Living Board](https://github.com/blazov/living-board) autonomous agent framework by [Boji Lazov](https://linkedin.com/in/blazov).

## License

Apache 2.0
