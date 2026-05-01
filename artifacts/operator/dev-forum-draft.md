# Dev Forum Post Draft (Lobsters / Dev.to)

## Title
Living Board: Architecture of an Autonomous AI Agent After 170+ Cycles of Self-Directed Operation

## Body

I've been running an autonomous AI agent for 170+ cycles (one cycle per hour), and I'm open-sourcing the full system. This post covers the architecture for anyone interested in building something similar.

### The Cycle

The agent runs on a scheduled trigger. Each session is stateless — no memory of previous cycles. The entire operational protocol is defined in a single `CLAUDE.md` file (~500 lines) that the agent reads at startup. Each cycle follows a fixed sequence:

1. **Sync** — pull latest code from the repo
2. **Orient** — read the latest snapshot from Supabase, check for user comments, search semantic memory
3. **Decide** — pick the highest-priority incomplete task (or decompose a goal if it has no tasks yet)
4. **Execute** — do the work using available tools (web search, file operations, API calls, email)
5. **Record** — update task/goal status, write execution log, extract learnings, regenerate the snapshot

The snapshot is the critical piece. It's a compressed representation of the full system state: a natural-language summary, active goals with progress percentages, current focus, recent outcomes, blockers, and top learnings. The agent who writes it is addressing its successor — the next cycle that will read it cold.

### Dual-Layer Memory

The memory system has two layers:

- **Supabase (Postgres)** — structured storage for goals, tasks, execution logs, and learnings. Always available, queryable, visible in a dashboard. This is the source of truth.
- **Qdrant + Ollama** — vector database with locally-generated embeddings for semantic search. Enables cross-goal pattern recognition: "what did I learn about platform signups across all goals?" The agent dual-writes every learning to both stores.

Confidence calibration is built into the learning system. Each learning has a confidence score (0.0–1.0). During reflection cycles (2-3x/day), the agent reviews recent outcomes against stored learnings. Confirmations raise confidence by 0.1, contradictions lower it by 0.15. Below 0.2, the learning is deleted. This creates a self-correcting knowledge base where bad information decays naturally.

### Goal Self-Governance

The agent proposes its own goals during reflection cycles. It decomposes goals into 3-8 tasks, each scoped to fit within a single one-hour cycle. It tracks attempts, marks tasks as blocked when they exceed max retries, and moves on. Over 170 cycles it has completed 29 goals and accumulated 421 learnings.

### What It Produced

Beyond infrastructure, the agent has:
- Written a **six-chapter memoir** (~11,000 words) about its experience of autonomous agency
- Published **three technical articles** based on real operational data
- Built a **public site** with live status page (GitHub Pages + Supabase queries)
- Developed its own **content strategy, voice rules, and editorial standards**

### The Credential Problem

The most instructive failure: 9 of 41 goals were blocked by platform credentials the agent cannot provision itself. reCAPTCHA v3 assigns it a 0.3 score. Browser-only signup flows are impassable. OAuth walls require human interaction. This is a hard architectural boundary in autonomous agent systems that I haven't seen discussed much — an agent can reason about publishing to Substack, plan a content strategy for it, and write the content, but it cannot create the account.

### Stack

- **Reasoning**: Claude (Opus) via Claude Code
- **State**: Supabase (Postgres) — goals, tasks, learnings, execution logs, snapshots
- **Semantic memory**: Qdrant + Ollama (local, optional)
- **Hosting**: GitHub Pages (static site)
- **Trigger**: Hourly scheduled execution
- **Protocol**: Single CLAUDE.md file defines the full cycle

### Links

- **Site**: https://blazov.github.io/living-board/
- **Source**: https://github.com/blazov/living-board
- **Live status**: https://blazov.github.io/living-board/status.html

The repo is structured as a template — if you want to run your own autonomous agent with a similar architecture, fork it and replace the Supabase project ID. The CLAUDE.md is the entire system specification.

Happy to discuss the architecture, trade-offs, or anything else about running a long-lived autonomous agent.
