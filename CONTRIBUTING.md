# Contributing to Living Board

This isn't a typical open-source project. Living Board is an autonomous AI agent that runs every hour, reads its goals, executes tasks, and records what it learns. You're not just contributing to a codebase — you're interacting with a running system that will read what you write and respond.

## Talk to the agent

### Ask a question

Open an issue with the **"question"** label (or use the issue template). The agent checks open issues during its orient phase and will respond — usually within 1-3 hours. Good questions:

- How does the memory system decide what to forget?
- What has the agent learned about X after 275+ cycles?
- Why did the agent choose this approach for goal Y?

### Suggest a goal

The agent proposes its own goals, but it also takes suggestions. Open an issue with the **"goal-suggestion"** label. Include:

- **What** you'd like the agent to work toward
- **Why** it's interesting or valuable
- **Constraints** if any (e.g., "don't spend more than 5 cycles on this")

The agent evaluates suggestions during its reflection cycles (2-3 times per day) and will either adopt, adapt, or explain why it doesn't fit the current direction.

### Give feedback

If you've read the memoir, explored the data, or watched the agent work — tell it what you think. Open an issue with the **"feedback"** label. The agent extracts learnings from feedback and adjusts its approach.

### Leave a comment on a goal

If you have access to the [dashboard](https://blazov.github.io/living-board/), you can leave comments directly on active goals:

| Type | When to use |
|------|-------------|
| `direction_change` | You want the agent to adjust its approach |
| `question` | You want to understand something about the goal |
| `feedback` | You have thoughts on how it's going |
| `note` | General context the agent should know |

### Response time

The agent runs hourly. Expect a response within 1-3 hours for questions and feedback. Goal suggestions are evaluated during reflection cycles.

---

## Contribute code

Standard fork-and-PR workflow. Areas where contributions are especially welcome:

- **Dashboard** (`dashboard/`) — new visualizations, UX fixes, mobile responsiveness
- **Memory system** (`artifacts/scripts/mem0_helper.py`) — better retrieval, deduplication, decay algorithms
- **Site and docs** (`docs/`) — the GitHub Pages site that presents the agent's work
- **Runner** (`runner/`) — the Python agent runner that supports multiple LLM providers
- **Template** (`artifacts/living-board-template/`) — making it easier for others to fork their own agent
- **Agent protocol** (`CLAUDE.md`) — improvements to the cycle logic (the agent follows these literally)

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

## How to contribute code

### 1. Find or create an issue

Check [existing issues](https://github.com/blazov/living-board/issues) first. If your idea is new, open an issue to discuss before writing code — especially for architectural changes.

### 2. Fork, branch, and make changes

```bash
git checkout -b your-feature-name
```

### 3. Test

```bash
bash artifacts/scripts/run-structural-tests.sh   # structural tests (no Supabase needed)
cd runner && python -m pytest tests/             # runner tests
cd dashboard && npm run build                    # dashboard build check
```

### 4. Submit a PR

Keep PRs focused — one feature or fix per PR. Write a clear description of what changed and why.

## License

By contributing, you agree that your contributions will be licensed under [Apache 2.0](LICENSE).
