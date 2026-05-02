# Quickstart: Zero to Running Agent in 10 Minutes

This guide walks you through forking the Living Board template, configuring it for your Supabase project, and running your first agent cycle.

## Prerequisites

- A [Supabase](https://supabase.com) account (free tier works)
- [Claude Code](https://docs.anthropic.com/en/docs/claude-code) installed (`npm install -g @anthropic-ai/claude-code`)
- Git
- `psql` (PostgreSQL client) — optional but recommended; without it you'll run SQL manually in the Supabase dashboard

## Step 1: Fork and Clone

Fork the [living-board](https://github.com/blazov/living-board) repository on GitHub, then clone your fork:

```bash
git clone https://github.com/YOUR_USERNAME/living-board.git
cd living-board
```

## Step 2: Create a Supabase Project

1. Go to [supabase.com/dashboard](https://supabase.com/dashboard) and create a new project.
2. Note your **Project ID** — find it in **Project Settings > General**.
3. Note your **Postgres connection string** — find it in **Project Settings > Database > Connection string (URI)**. You'll need this in the next step.

## Step 3: Run the Setup Script

The interactive setup script configures everything:

```bash
bash artifacts/living-board-template/template-setup.sh
```

It will prompt you for:

| Prompt | What to enter |
|--------|---------------|
| **Supabase project ID** | The project ID from Step 2 |
| **Git branch name** | Press Enter for `master` (default) |
| **AgentMail address** | Leave blank to skip email features, or enter your [AgentMail](https://agentmail.to) address |
| **Available tools** | Press Enter for the default tool list, or customize |
| **Postgres connection string** | The URI from Step 2 (runs schema + optional seed data) |

The script will:
- Generate `CLAUDE.md` from the template with your values substituted
- Run `schema.sql` to create the 7 database tables
- Optionally insert example seed data (a sample goal with tasks)

If you don't have `psql` installed, the script skips database setup and tells you which SQL files to run manually in the [Supabase SQL Editor](https://supabase.com/dashboard/project/_/sql).

## Step 4: Copy CLAUDE.md to the Repo Root

```bash
cp artifacts/living-board-template/CLAUDE.md ./CLAUDE.md
```

This is the file Claude Code reads every cycle to know how to behave.

## Step 5: Set Up the Supabase MCP Connector

Claude Code needs the Supabase MCP server to read/write your database. Add it to your Claude Code settings:

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

The first time the agent connects, Supabase MCP will prompt you to authenticate via OAuth.

## Step 6: Add Your First Goal

Insert a goal for the agent to work on. You can do this in the Supabase SQL Editor or via `psql`:

```sql
INSERT INTO goals (title, description, status, priority)
VALUES (
  'My first goal',
  'Describe what you want the agent to accomplish. Be specific about the desired outcome.',
  'in_progress',
  3
);
```

The agent will automatically decompose this into concrete tasks on its first cycle.

If you ran the seed data during setup, there's already a sample goal — you can skip this step and let the agent work on that first.

## Step 7: Run Your First Cycle

Start Claude Code and tell it to run a cycle:

```bash
claude "Execute your full agent cycle as defined in CLAUDE.md."
```

Watch the agent:
1. **Orient** — read the database snapshot and check for comments
2. **Decide** — pick the highest-priority pending task (or decompose a goal into tasks)
3. **Execute** — do the actual work
4. **Record** — write results back, log the execution, extract learnings

## Step 8: Schedule Recurring Cycles

To run the agent automatically every hour, create a Claude Code scheduled trigger:

```bash
claude trigger create --name "living-board" \
  --schedule "0 * * * *" \
  --prompt "Execute your full agent cycle as defined in CLAUDE.md."
```

This uses [Claude Code remote triggers](https://docs.anthropic.com/en/docs/claude-code/remote). The agent will wake up every hour, read its state, do one task, and go back to sleep.

## What Happens Next

Here's what to expect over the first few cycles:

| Cycle | What the agent does |
|-------|--------------------|
| **1** | Orients itself. If your goal has no tasks, it decomposes the goal into 3-8 concrete tasks. |
| **2-4** | Executes tasks one per cycle — typically starting with research/discovery, then moving to execution. Records learnings along the way. |
| **5** | By now the agent has completed several tasks, accumulated learnings, and may trigger its first **reflection** — reviewing the board, consolidating memory, and potentially proposing new goals. |

After 10+ cycles, you'll see the agent:
- Build up a knowledge base of learnings with confidence scores
- Propose its own goals during reflection cycles
- Adapt strategies based on what worked and what didn't

## Collaborating with the Agent

Leave comments on goals via the `goal_comments` table (or the dashboard if you set it up):

```sql
INSERT INTO goal_comments (goal_id, comment_type, content)
VALUES (
  '<goal_id>',
  'direction_change',  -- or: 'question', 'feedback', 'note'
  'Focus on X instead of Y for now.'
);
```

The agent checks for unacknowledged comments at the start of every cycle and responds before doing task work.

## Optional: Deploy the Dashboard

The dashboard gives you a real-time view of goals, tasks, execution history, and learnings, plus the ability to leave comments:

```bash
cd dashboard
cp .env.example .env.local
# Edit .env.local with your Supabase URL, anon key, and auth secret
npm install && npm run dev
```

## Optional: Set Up Semantic Memory (mem0)

For cross-goal semantic search, set up Qdrant and Ollama locally:

```bash
docker run -d -p 6333:6333 qdrant/qdrant
curl -fsSL https://ollama.com/install.sh | sh
ollama pull nomic-embed-text
pip install qdrant-client requests
```

The agent will automatically detect and use these services when available. Without them, it still works fine using Supabase learnings alone.

## Troubleshooting

**"CLAUDE.md.template not found"**
Run the setup script from the repo root: `bash artifacts/living-board-template/template-setup.sh`

**Schema errors in SQL Editor**
The schema uses `IF NOT EXISTS` throughout — safe to re-run. If you see permission errors, make sure you're connected as the `postgres` role.

**Agent says "no goals found"**
Insert a goal (Step 6) or run the seed data: paste `seed-data.sql` into the Supabase SQL Editor.

**MCP connector won't authenticate**
Run `claude mcp list` to verify the Supabase server is configured. Remove and re-add it if needed: `claude mcp remove supabase && claude mcp add supabase --type url --url https://mcp.supabase.com`

**Agent runs but doesn't commit artifacts**
Make sure the agent has write access to the repo and is on a proper branch (not detached HEAD). The `cycle-start.sh` script handles this automatically.

**psql: command not found**
Install the PostgreSQL client for your platform:
- macOS: `brew install libpq && brew link --force libpq`
- Ubuntu/Debian: `sudo apt install postgresql-client`
- Or skip `psql` entirely and run the SQL files in the Supabase dashboard SQL Editor.

## File Reference

| File | Purpose |
|------|---------|
| `CLAUDE.md.template` | Agent instructions template with `{{PLACEHOLDER}}` variables |
| `template-setup.sh` | Interactive setup script — generates CLAUDE.md and runs schema |
| `schema.sql` | Database DDL — creates all 7 tables, indexes, triggers, and views |
| `seed-data.sql` | Optional example goal, tasks, and learnings |
| `QUICKSTART.md` | This guide |
| `README.md` | Full project overview, architecture, design principles, and customization options |
