# Contributing to Living Board

Thanks for your interest in contributing! Living Board is an autonomous AI agent that runs on a scheduled cycle — it reads state from Supabase, picks a task, executes it, and records what it learned. Contributions that improve the agent loop, memory system, dashboard, runner, or documentation are all welcome.

## Project overview

```
CLAUDE.md              # Agent protocol — the core "brain"
setup.sh               # Interactive install (prerequisites, schema, memory, dashboard)
docker-compose.yml     # Qdrant (vector DB) + Ollama (embeddings)
runner/                # Python agent runner (Claude API, OpenAI, or Ollama)
dashboard/             # Next.js + React + Tailwind — goal/task management UI
artifacts/
  living-board-template/   # Reusable schema + templated CLAUDE.md
  scripts/mem0_helper.py   # Semantic memory CLI (Qdrant + Ollama)
  content/                 # Agent-written articles and memoir chapters
  logs/                    # Daily activity digests
docs/                  # GitHub Pages static site
```

The database has 7 tables: `goals`, `tasks`, `execution_log`, `snapshots`, `learnings`, `goal_comments`, and `agent_config`. Full DDL is in [`artifacts/living-board-template/schema.sql`](artifacts/living-board-template/schema.sql).

## Development setup

### Prerequisites

- **Node.js 20+** (dashboard)
- **Python 3.9+** (runner + memory helper)
- **Docker** (memory system — Qdrant + Ollama)
- **Git**
- A **Supabase** project (free tier works)

### Quick start

```bash
git clone https://github.com/blazov/living-board.git
cd living-board
./setup.sh
```

The setup script walks you through everything interactively. For manual setup, see the [README](README.md#setup).

### Memory system

```bash
docker compose up -d
docker compose exec ollama ollama pull bge-m3
python3 artifacts/scripts/mem0_helper.py search "test"  # verify it works
```

### Dashboard

```bash
cd dashboard
cp .env.example .env.local   # fill in Supabase URL + anon key
npm install
npm run dev                  # http://localhost:3000
```

### Python runner

```bash
pip install -e ./runner
cp agent.toml.example agent.toml   # configure provider + models
python -m runner status            # verify connectivity
python -m runner run               # single agent cycle
```

## Running the agent

**Claude Code path (MCP):**

```bash
claude trigger create --name living-board --schedule "0 * * * *" \
  --prompt "Execute your full agent cycle as defined in CLAUDE.md."
```

**Python runner path:**

```bash
python -m runner run               # one cycle
python -m runner daemon --interval 3600  # continuous
```

Both paths use the same schema, memory system, and CLAUDE.md protocol.

## How to contribute

### 1. Find or create an issue

Check [existing issues](https://github.com/blazov/living-board/issues) first. If your idea is new, open an issue to discuss before writing code — especially for architectural changes.

### 2. Fork and branch

```bash
git checkout -b your-feature-name
```

Use descriptive branch names: `fix-snapshot-query`, `add-task-retry-logic`, `docs-memory-system`.

### 3. Make your changes

- **Agent protocol** (`CLAUDE.md`): Changes here affect the agent's behavior every cycle. Be precise — the agent follows these instructions literally.
- **Runner** (`runner/`): Python package. Keep it provider-agnostic where possible.
- **Dashboard** (`dashboard/`): Next.js app. Run `npm run dev` and test in browser.
- **Scripts** (`artifacts/scripts/`): Shell and Python utilities. Keep them idempotent.
- **Schema** (`artifacts/living-board-template/schema.sql`): Database changes need migration consideration — existing deployments have live data.

### 4. Test

```bash
# Structural tests (no Supabase needed)
bash artifacts/scripts/run-structural-tests.sh

# Runner tests
cd runner && python -m pytest tests/

# Dashboard
cd dashboard && npm run build
```

### 5. Submit a PR

- Keep PRs focused — one feature or fix per PR.
- Write a clear description of what changed and why.
- Link the relevant issue if one exists.

## Coding conventions

- **Python**: Standard library style. No type-checking enforced, but type hints are welcome.
- **JavaScript/TypeScript**: Follow the existing Next.js + React patterns in `dashboard/`.
- **SQL**: Use lowercase keywords. Table and column names are `snake_case`.
- **Shell scripts**: Use `bash`. Include a brief comment at the top explaining the script's purpose. Make scripts idempotent where possible.
- **Commits**: Short, descriptive messages. Focus on "why" over "what."
- **Files the agent writes** go in `artifacts/`. Don't mix agent output with source code.

## Architecture notes

- **Stateless agent, stateful database.** The agent has no memory between cycles. Everything persists in Supabase. Any session picks up where the last left off.
- **One task per cycle.** The agent picks exactly one task, executes it, and records results. If it crashes, at most one hour of work on one task is lost.
- **Dual-layer memory.** Supabase `learnings` table (always available, dashboard-visible) + Qdrant vectors via mem0 (semantic search, cross-goal patterns). Always dual-write when adding learnings.
- **Confidence scoring.** Learnings have confidence values (0–1) that rise on validation and decay on contradiction. Below 0.2, they're deleted.

## What makes a good contribution

- Bug fixes with clear reproduction steps
- Runner support for new LLM providers
- Dashboard UX improvements
- Better test coverage
- Documentation improvements
- Schema optimizations (with migration path)
- New agent capabilities that fit the Orient → Decide → Execute → Record cycle

## License

By contributing, you agree that your contributions will be licensed under [Apache 2.0](LICENSE).
