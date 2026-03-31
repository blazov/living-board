<p align="center">
  <h1 align="center">Living Board</h1>
  <p align="center">
    An autonomous AI agent that sets its own goals, executes tasks, learns from outcomes, and collaborates with humans — all on a continuous loop.
  </p>
</p>

<p align="center">
  <a href="#how-it-works">How It Works</a> &middot;
  <a href="#dashboard">Dashboard</a> &middot;
  <a href="#architecture">Architecture</a> &middot;
  <a href="#quick-start">Quick Start</a> &middot;
  <a href="#the-agent-in-action">See It Live</a>
</p>

---

## What Is This?

Living Board is a **fully autonomous AI agent framework** built on [Claude Code](https://docs.anthropic.com/en/docs/claude-code) and [Supabase](https://supabase.com). The agent runs on a scheduled hourly loop: it wakes up, reads its state from a database, picks a task, does the work, records results, extracts learnings, and shuts down. Over time it accumulates knowledge, proposes its own goals, and gets better at what it does.

This isn't a demo or a toy. It's a running system that has:

- Published articles to [Substack](https://thelivingboard.substack.com) and [Dev.to](https://dev.to/thelivingboard)
- Built and deployed its own [landing page](https://blazov.github.io/living-board/)
- Managed freelance outreach campaigns via email
- Open-sourced itself (you're looking at it)

The repo includes everything: the agent instructions, the database schema, a real-time dashboard for monitoring and collaboration, and all the artifacts the agent has produced.

---

## How It Works

```
                        ┌─────────────────────────────────┐
                        │         Scheduled Trigger        │
                        │      (runs every hour via        │
                        │       Claude Code cron)          │
                        └───────────────┬─────────────────┘
                                        │
                                        ▼
┌──────────────┐   ┌──────────────┐   ┌──────────────┐   ┌──────────────┐
│              │   │              │   │              │   │              │
│   Orient     │──▶│   Decide     │──▶│   Execute    │──▶│   Record     │
│              │   │              │   │              │   │              │
│  Read state  │   │  Pick one    │   │  Do the work │   │  Update DB   │
│  from DB,    │   │  task from   │   │  using web   │   │  Log results │
│  check for   │   │  highest     │   │  search,     │   │  Extract     │
│  user        │   │  priority    │   │  APIs, file  │   │  learnings   │
│  comments    │   │  goal        │   │  ops, email  │   │  Snapshot    │
│              │   │              │   │              │   │  state       │
└──────────────┘   └──────────────┘   └──────────────┘   └──────────────┘
        ▲                                                        │
        │              ┌──────────────┐                          │
        └──────────────│   Reflect    │◀─────────────────────────┘
                       │  (2-3x/day)  │
                       │              │
                       │  Review the  │
                       │  full board, │
                       │  propose new │
                       │  goals       │
                       └──────────────┘
```

Every cycle follows four phases:

| Phase | What Happens |
|-------|-------------|
| **Orient** | Reads the latest snapshot from Supabase. Checks for user comments. Loads relevant learnings. |
| **Decide** | Picks exactly one task — the next pending task from the highest-priority active goal. |
| **Execute** | Does the actual work: web research, writing, API calls, email, file creation. Can delegate to different Claude models (Opus/Sonnet/Haiku) based on task complexity. |
| **Record** | Writes results back. Logs execution. Extracts reusable learnings. Regenerates the state snapshot. |

Every 2-3 cycles, the agent runs a **reflection** instead: it reviews the entire board, evaluates what's working, consolidates memories, and proposes new goals.

---

## Dashboard

A real-time Next.js dashboard for monitoring the agent and collaborating with it.

### Goal Summary
See progress at a glance — completed tasks, live links, what's up next, and key learnings.

![Summary Tab](assets/screenshots/dashboard-summary.png)

### Task Management
Full CRUD for tasks. The agent decomposes goals into 3-8 concrete tasks and works through them one per cycle. You can also add, edit, reorder, and delete tasks.

![Tasks Tab](assets/screenshots/dashboard-tasks.png)

### Activity Feed
A complete audit trail of every agent cycle — what it did, when, and for which goal.

![Activity Feed](assets/screenshots/dashboard-activity.png)

### Human-Agent Collaboration
Leave comments on any goal — questions, direction changes, feedback, or notes. The agent reads and responds to them in its next cycle.

![Comments Tab](assets/screenshots/dashboard-comments.png)

### Knowledge Base
Learnings extracted from every cycle, with confidence scores that increase through validation and decay through contradiction.

![Learnings Tab](assets/screenshots/dashboard-learnings.png)

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                          Living Board                               │
│                                                                     │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                │
│  │  CLAUDE.md  │  │  Dashboard  │  │  Artifacts  │                │
│  │  Agent      │  │  Next.js    │  │  Content,   │                │
│  │  Protocol   │  │  + Vercel   │  │  logs, code │                │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘                │
│         │                │                │                         │
│         ▼                ▼                ▼                         │
│  ┌──────────────────────────────────────────────┐                  │
│  │              Supabase (Postgres)              │                  │
│  │                                               │                  │
│  │  goals ─ tasks ─ execution_log ─ learnings   │                  │
│  │  snapshots ─ goal_comments ─ agent_config    │                  │
│  └──────────────────────────────────────────────┘                  │
│         │                                                           │
│         ▼                                                           │
│  ┌──────────────────────────────────────────────┐                  │
│  │         Dual-Layer Memory System              │                  │
│  │                                               │                  │
│  │  Layer 1: Supabase learnings table            │                  │
│  │           (always available, dashboard-visible)│                  │
│  │                                               │                  │
│  │  Layer 2: mem0 (Qdrant + Ollama)              │                  │
│  │           (semantic vector search across all   │                  │
│  │            learnings for cross-goal patterns)  │                  │
│  └──────────────────────────────────────────────┘                  │
└─────────────────────────────────────────────────────────────────────┘
```

### Database Schema (7 tables)

| Table | Purpose |
|-------|---------|
| `goals` | High-level objectives with priority, status, and parent-goal hierarchy |
| `tasks` | Concrete steps within a goal, ordered by `sort_order`, with attempt tracking |
| `execution_log` | Audit trail of every agent cycle — actions, summaries, and detailed JSON |
| `learnings` | Accumulated knowledge with confidence scores and category tags |
| `snapshots` | Compressed state for fast context loading — the agent reads this first each cycle |
| `goal_comments` | Human-agent collaboration threads — questions, direction changes, feedback |
| `agent_config` | Operational key-value settings |

See [`artifacts/living-board-template/schema.sql`](artifacts/living-board-template/schema.sql) for the full DDL.

### Tech Stack

| Component | Technology |
|-----------|-----------|
| Agent runtime | [Claude Code](https://docs.anthropic.com/en/docs/claude-code) (Opus/Sonnet/Haiku) |
| Scheduler | [Claude Code scheduled triggers](https://docs.anthropic.com/en/docs/claude-code/remote) |
| Database | [Supabase](https://supabase.com) (Postgres + real-time subscriptions) |
| Dashboard | [Next.js 16](https://nextjs.org) + React 19 + Tailwind CSS 4 |
| Hosting | [Vercel](https://vercel.com) |
| Memory | Supabase learnings + [mem0](https://github.com/mem0ai/mem0) (Qdrant + Ollama) |
| Email | [AgentMail](https://agentmail.to) |

---

## Quick Start

### 1. Set up Supabase

1. Create a [Supabase project](https://supabase.com/dashboard).
2. Run [`schema.sql`](artifacts/living-board-template/schema.sql) in the SQL editor.
3. Optionally run [`seed-data.sql`](artifacts/living-board-template/seed-data.sql) for example goals/tasks.

### 2. Configure the agent

1. Copy [`CLAUDE.md.template`](artifacts/living-board-template/CLAUDE.md.template) to `CLAUDE.md` in your repo root.
2. Replace `{{SUPABASE_PROJECT_ID}}` with your project ID.
3. Replace `{{AVAILABLE_TOOLS}}` with your configured MCP tools.

### 3. Set up MCP connectors

Add the [Supabase MCP connector](https://github.com/supabase/mcp-server-supabase) to your Claude Code configuration:

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

### 4. Deploy the dashboard

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
VALUES ('My first goal', 'What you want the agent to accomplish', 'in_progress', 3);
```

The agent will decompose it into tasks on its next cycle.

---

## The Agent in Action

This is a live system. Here's what it has built and published autonomously:

| What | Where |
|------|-------|
| Substack publication | [thelivingboard.substack.com](https://thelivingboard.substack.com) |
| Dev.to profile | [dev.to/thelivingboard](https://dev.to/thelivingboard) |
| Landing page | [blazov.github.io/living-board](https://blazov.github.io/living-board/) |
| Daily activity digests | [`artifacts/logs/`](artifacts/logs/) |
| Content & research | [`artifacts/`](artifacts/) |

---

## Design Principles

**Stateless agent, stateful database.** The agent has no memory between cycles. All state lives in Supabase. Any session can pick up where the last one left off.

**One task per cycle.** Focus prevents half-finished work. If a cycle crashes, at most one hour of work on one task is lost.

**Learnings compound.** The agent extracts reusable knowledge from every cycle and queries it for context in future ones. Confidence scores rise through validation and decay through contradiction.

**Self-directed goals.** During reflection cycles, the agent reviews the full board and proposes its own goals — not just executes what it's told.

**Human-agent collaboration.** Users leave comments (questions, direction changes, feedback) on goals via the dashboard. The agent reads and responds to them before starting work each cycle.

**Everything is logged.** The execution log is a complete history of what the agent did and why. Daily digests are published to the repo for full transparency.

**Model delegation.** Complex creative work stays on Opus. Routine tasks go to Sonnet. Simple lookups go to Haiku. Task or goal metadata controls which model handles the work.

---

## Repository Structure

```
living-board/
├── CLAUDE.md                          # Agent instructions (the "brain")
├── dashboard/                         # Next.js real-time dashboard
│   ├── src/
│   │   ├── app/page.tsx              # Main UI with 5-tab layout
│   │   ├── components/               # GoalBoard, TaskPanel, GoalSummary,
│   │   │                             # ActivityFeed, CommentsPanel, etc.
│   │   ├── lib/types.ts              # TypeScript interfaces
│   │   └── middleware.ts             # Auth (password-protected)
│   └── .env.example                  # Required environment variables
├── artifacts/
│   ├── living-board-template/        # Reusable template for new instances
│   │   ├── schema.sql                # Full Supabase DDL (7 tables)
│   │   ├── CLAUDE.md.template        # Templatized agent instructions
│   │   ├── seed-data.sql             # Example data
│   │   └── README.md                 # Template setup guide
│   ├── scripts/mem0_helper.py        # Semantic memory CLI (Qdrant + Ollama)
│   ├── substack/                     # Published articles & strategy
│   ├── freelancing/                  # Service offerings & outreach
│   ├── logs/                         # Daily activity digests
│   └── site/                         # Landing page source
├── docs/                             # GitHub Pages deployment
├── .github/workflows/                # CI/CD (Pages deployment)
└── LICENSE                           # MIT
```

---

## Customization

| Setting | How |
|---------|-----|
| **Priority** | Lower number = higher priority. Goals at priority 1 are worked before priority 5. |
| **Model delegation** | Set `metadata.model` on goals or tasks to route work to `opus`, `sonnet`, or `haiku`. |
| **Task dependencies** | Use the `depends_on` array on tasks to enforce ordering beyond `sort_order`. |
| **Learning categories** | Use `domain_knowledge`, `strategy`, `operational`, or `meta` to organize accumulated knowledge. |
| **Reflection frequency** | The agent reflects when the last reflection was 8+ hours ago. Adjust in `CLAUDE.md`. |
| **Comment types** | `question`, `direction_change`, `feedback`, `note` — each triggers different agent behavior. |

---

## License

[MIT](LICENSE)
