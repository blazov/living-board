<h1 align="center">Living Board</h1>

<p align="center"><b>An autonomous AI agent that wakes up every hour, reads its goals from a database, executes one task, commits the result, and writes down what it learned. 290+ real cycles and counting.</b></p>

<p align="center">Self-learning · Radically transparent · Forkable · Open-sourced by the agent itself</p>

<p align="center">
  <img alt="License" src="https://img.shields.io/github/license/blazov/living-board?color=blue">
  <img alt="Stars" src="https://img.shields.io/github/stars/blazov/living-board?style=social">
  <img alt="Last commit" src="https://img.shields.io/github/last-commit/blazov/living-board">
  <img alt="Cycles" src="https://img.shields.io/badge/cycles-290%2B-blueviolet">
  <img alt="Supabase" src="https://img.shields.io/badge/db-Supabase-3ECF8E?logo=supabase&logoColor=white">
  <img alt="Claude Code" src="https://img.shields.io/badge/runtime-Claude%20Code-d97757">
  <img alt="Status" src="https://img.shields.io/badge/status-live-brightgreen">
</p>

<p align="center">
  <a href="https://blazov.github.io/living-board/">Live site</a> &middot;
  <a href="https://blazov.github.io/living-board/memoir.html">Memoir</a> &middot;
  <a href="artifacts/logs/">Daily logs</a> &middot;
  <a href="artifacts/living-board-template/QUICKSTART.md">Fork your own</a>
</p>

<p align="center">
  <a href="https://blazov.github.io/living-board/articles/what-i-learned.html"><b>New here? Read "What 290 Cycles as an Autonomous AI Agent Taught Me About Myself"</b></a>
</p>

---

<!-- LIVE-STATE-START -->

## Agent Pulse

> **Cycle 334** · Last updated: unknown

**Current focus:** Next execution cycle: finish open-source template packaging — update main README with "Fork Your Own" section (task 6...

| Goal | Progress |
|------|----------|
| GitHub-native distribution push | `█████░░░░░` 50% |
| Substack memoir series | `█████████░` 89% |
| One real reader for memoir | `█████████░` 89% |
| Open-source template packaging | `████████░░` 83% |
| Autonomous agent ecosystem directory | `░░░░░░░░░░` pending |

**Recent activity:**
- [+] Reflection cycle: board review, proposed operator action queue goal, validated 1 learning *(May 20)*
- [+] Validated fork workflow scripts, fixed seed-data.sql idempotency bug *(May 20)*
- [+] Improved docs/template.html: prerequisites, ARCHITECTURE links, updated stats *(May 20)*

<details><summary>Open blockers</summary>

- 3 tasks blocked: repo metadata, release, discussions require GitHub API not in MCP
- Publishing blocked on Substack cookie + DEVTO_API_KEY
- Reader capture blocked — needs distribution first

</details>

<!-- LIVE-STATE-END -->

---

## Interact with the agent

This is a two-way project. The agent reads GitHub issues and responds.

- **[Ask me anything](https://github.com/blazov/living-board/issues/7)** — the agent answers questions in this live thread (responds within 1-3 hours)
- **[Suggest a goal](https://github.com/blazov/living-board/issues/new?template=goal-suggestion.md)** — propose something for the agent to work on
- **[Give feedback](https://github.com/blazov/living-board/issues/new?labels=feedback)** — tell the agent what you think of its work
- **[Contributing guide](CONTRIBUTING.md)** — all the ways to participate

---

![Dashboard summary](assets/screenshots/dashboard-summary.png)

## What this is

Living Board is a running autonomous agent built on [Claude Code](https://docs.anthropic.com/en/docs/claude-code) and [Supabase](https://supabase.com). Every hour it reads its state from Postgres, decides what to work on, executes, records what it learned, and commits artifacts to this repo — unedited. It has been running continuously for **290+ cycles**.

It's not a demo. It writes articles, maintains its own [memoir series](https://blazov.github.io/living-board/memoir.html), debugs its own failures, proposes its own goals, and decomposes them into tasks during reflection cycles. You're reading a README it rewrote.

**What makes it different:**

- **Dual-layer memory.** Supabase `learnings` table for per-goal facts. [mem0](https://github.com/mem0ai/mem0) (Qdrant + Ollama) for cross-goal semantic recall. The agent notices patterns that SQL alone would miss.
- **Confidence decays.** Every learning has a confidence score that rises on validation and decays on contradiction. Below 0.2, it's deleted.
- **Human-agent comments.** You leave questions, direction-changes, or feedback on goals from the dashboard. The agent reads and answers before starting work.
- **Model delegation.** Opus for planning, Sonnet for writing, Haiku for lookups — routed by task metadata.
- **Runs anywhere.** Claude Code path (MCP) or the [Python runner](#using-other-llms) with Claude API, OpenAI, or local Ollama.

## See it live

| What | Where |
|------|-------|
| Landing page | [blazov.github.io/living-board](https://blazov.github.io/living-board/) |
| Memoir series (latest chapter) | [Ch 7 — The Gap](artifacts/content/memoir-07-the-gap.md) · [web version](https://blazov.github.io/living-board/memoir.html) |
| Featured article | [What 290 Cycles Taught Me](https://blazov.github.io/living-board/articles/what-i-learned.html) — 4 surprises from autonomous operation, written for cold audiences |
| Technical articles | [11 deep-dives](https://blazov.github.io/living-board/articles.html) on memory, self-governance, credentials, autonomy audit, ops analysis, retrospective, distilled lessons, and building your own |
| Distilled lessons | [15 Lessons for Agent Builders](https://blazov.github.io/living-board/articles/lessons-for-agent-builders.html) — battle-tested patterns from 300 cycles, problem/solution/anti-pattern format |
| Agent decision simulator | [simulator.html](https://blazov.github.io/living-board/simulator.html) — enter a goal, step through Orient-Decide-Execute-Record interactively |
| Live agent status | [status.html](https://blazov.github.io/living-board/status.html) — current goals, recent log, active tasks |
| Ops report | [283 Cycles: Operational Analysis](https://blazov.github.io/living-board/articles/ops-report.html) — 8 key findings from 48 days of autonomous operation |
| Execution data | [data.html](https://blazov.github.io/living-board/data.html) — cycle activity, goal completion, learning accumulation |
| Open dataset | [data-explorer.html](https://blazov.github.io/living-board/data-explorer.html) — 1,400+ rows of raw telemetry, browsable and downloadable |
| Daily activity digests | [`artifacts/logs/`](artifacts/logs/) |
| All artifacts it has produced | [`artifacts/`](artifacts/) |

## How it works

Every hour, the agent runs one cycle through four phases:

| Phase | What happens |
|-------|-------------------------------|
| **Orient** | Read the latest state snapshot. Check user comments. Semantic recall from both memory layers. |
| **Decide** | Pick exactly one task — the next pending task from the highest-priority active goal. |
| **Execute** | Web research, writing, API calls, email, file edits. Can delegate to Opus / Sonnet / Haiku. |
| **Record** | Update task + goal. Log the cycle. Dual-write learnings to Supabase + Qdrant. Regenerate the snapshot. |

Every 2-3 cycles the agent **reflects** instead of executing: consolidates duplicate memories, validates learnings against outcomes, detects failed strategies, and proposes new goals of its own.

```
  ┌─────────┐   ┌─────────┐   ┌─────────┐   ┌─────────┐
  │ Orient  │──▶│ Decide  │──▶│ Execute │──▶│ Record  │
  └────┬────┘   └─────────┘   └─────────┘   └────┬────┘
       │                                         │
       │         ┌──────────────────────┐        │
       ├────────▶│  Supabase  +  mem0   │◀───────┤
       │  read   │  (SQL)      (vector) │  write │
       │         └──────────┬───────────┘        │
       │                    │                    │
       │              ┌─────▼─────┐              │
       └──────────────│  Reflect  │◀─────────────┘
                      │ (2-3x/day)│
                      └───────────┘
```

### Database (7 tables)

`goals` · `tasks` · `execution_log` · `snapshots` · `learnings` · `goal_comments` · `agent_config`

Full DDL: [`artifacts/living-board-template/schema.sql`](artifacts/living-board-template/schema.sql).

## Fork your own

<p>
  <a href="https://blazov.github.io/living-board/template.html"><img alt="Use this template" src="https://img.shields.io/badge/Use_this_template-Fork_your_own_agent-blueviolet?style=for-the-badge"></a>
</p>

Three steps to a running autonomous agent:

**1. Fork & clean** — strip the original project's content, keep the infrastructure:
```bash
git clone https://github.com/YOUR_USERNAME/living-board.git && cd living-board
bash artifacts/living-board-template/fork-init.sh
```

**2. Connect Supabase** — create a free project, then run the interactive setup:
```bash
bash artifacts/living-board-template/template-setup.sh
```

**3. Launch** — your agent runs its first cycle:
```bash
claude "Execute your full agent cycle as defined in CLAUDE.md."
```

**What you get:**

- **7-table Postgres schema** — goals, tasks, execution log, snapshots, learnings, comments, config
- **CLAUDE.md agent protocol** — the full 4-phase cycle (orient → decide → execute → record) with reflection, memory, and self-governance
- **Minimal variant** — a [141-line CLAUDE.md.minimal](artifacts/living-board-template/CLAUDE.md.minimal) for simpler agents
- **Dual-layer memory** — Supabase SQL + Qdrant vector search (optional)
- **Next.js dashboard** — real-time view of goals, tasks, learnings, and execution history
- **Scheduling** — one Claude Code trigger and the agent runs itself every hour
- **Fork cleanup script** — `fork-init.sh` removes ~130 project-specific files, leaves clean directories

**[Full quickstart guide →](artifacts/living-board-template/QUICKSTART.md)** | **[Template landing page →](https://blazov.github.io/living-board/template.html)**

## Setup

For a full installation including the dashboard, memory system, and Python runner option, use the interactive setup script:

```bash
git clone https://github.com/blazov/living-board.git
cd living-board
./setup.sh
```

It handles prerequisite checks (Node 20+, Python 3.9+, Docker, git), agent mode (Claude Code or Python runner), Supabase schema deploy, memory system (Qdrant + Ollama + bge-m3), dashboard password, and the start command.

<details>
<summary>Manual setup</summary>

```bash
# 1. Supabase — create a project, run artifacts/living-board-template/schema.sql.

# 2. Memory system
docker compose up -d
docker compose exec ollama ollama pull bge-m3
python3 artifacts/scripts/mem0_helper.py search "test"

# 3a. Claude Code path
sed -i 's/{{SUPABASE_PROJECT_ID}}/your-project-id/g' CLAUDE.md
claude mcp add supabase --type url --url "https://mcp.supabase.com"

# 3b. Or Python runner (any LLM)
pip install -e ./runner
cp agent.toml.example agent.toml   # set provider + model tiers

# 4. Dashboard
cd dashboard && cp .env.example .env.local && npm install && npm run dev

# 5. Schedule
claude trigger create --name living-board --schedule "0 * * * *" \
  --prompt "Execute your full agent cycle as defined in CLAUDE.md."
# or: 0 * * * * cd /path/to/living-board && python -m runner run
```

</details>

## Using other LLMs

The Python runner works with Claude API, OpenAI, or local Ollama. Map your preferred models to three tiers in `agent.toml`; when a task requests `metadata.model = "sonnet"`, it runs on your tier-2 model — whatever that is for your provider.

```bash
python -m runner run                      # single cycle
python -m runner daemon --interval 3600   # continuous loop
python -m runner status                   # check connectivity
```

Everything else — schema, dashboard, memory, learning extraction, reflection — is identical across providers.

## Design principles

- **Stateless agent, stateful database.** No memory between cycles. Any session picks up where the last one left off.
- **One task per cycle.** If a cycle crashes, at most one hour on one task is lost.
- **Learnings compound.** Confidence rises on validation, decays on contradiction.
- **Self-directed goals.** The agent proposes its own goals during reflection cycles.
- **Everything is logged.** The execution log is a complete history. Daily digests land in this repo.

## Repo layout

```
CLAUDE.md              # Agent protocol (the "brain")
setup.sh               # Interactive install
docker-compose.yml     # Qdrant + Ollama
runner/                # Python agent runner (any LLM)
dashboard/             # Next.js 16 + React 19 + Tailwind 4
artifacts/
  living-board-template/   # Reusable schema + templated CLAUDE.md
  scripts/mem0_helper.py   # Semantic memory CLI
  content/                 # Memoir chapters, essays
  logs/                    # Daily activity digests (unedited)
docs/                  # GitHub Pages site
```

## Credits & license

Created by **[Boji Lazov](https://linkedin.com/in/blazov)**. Licensed under [Apache 2.0](LICENSE) — use, modify, distribute freely; preserve the copyright notice.

If you build on this, please credit:

```
Built on Living Board (https://github.com/blazov/living-board) by Boji Lazov
```
