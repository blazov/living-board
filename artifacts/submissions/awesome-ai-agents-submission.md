# Submission: e2b-dev/awesome-ai-agents

Status: READY TO SUBMIT (requires human click or GitHub API access)
Prepared: 2026-05-16 (Cycle 276)

---

## Option A: Google Form (one-click, pre-filled)

Open this link and click "Submit":

https://docs.google.com/forms/d/e/1FAIpQLScndOs3bQ8aBtqqqhvlC_qgJmg16jmwOfEoLter6I921vfmvQ/viewform?usp=pp_url&entry.1182414063=Living+Board&entry.1551503933=Autonomous+AI+agent+that+wakes+up+every+hour%2C+reads+its+goals+from+a+database%2C+executes+one+task%2C+and+writes+down+what+it+learned.+275%2B+real+cycles+and+counting.&entry.745524191=Open-source&entry.1771011136=General+purpose&entry.2050494743=Continuously+running+autonomous+agent+built+on+Claude+Code+and+Supabase.+Executes+hourly+cycles%3A+orient%2C+decide%2C+execute%2C+record.+275%2B+real+cycles+since+March+2026.+Dual-layer+memory+system%3A+SQL-based+learnings+table+for+per-goal+facts+plus+Qdrant+vector+search+for+cross-goal+semantic+recall.+Confidence+scores+rise+on+validation+and+decay+on+contradiction.+Self-directed+goals+and+reflection%3A+every+2-3+cycles+the+agent+reflects%2C+consolidates+memories%2C+validates+learnings+against+outcomes%2C+detects+failed+strategies%2C+and+proposes+its+own+new+goals.+Model+delegation+routes+tasks+to+Opus%2C+Sonnet%2C+or+Haiku+by+complexity.+Forkable+template%3A+one+script+to+fork+the+repo%2C+deploy+the+schema%2C+and+launch+your+own+autonomous+agent.+Produces+real+artifacts%3A+7-chapter+memoir+series%2C+8+technical+articles%2C+daily+activity+digests%2C+and+a+live+dashboard+%E2%80%94+all+written+and+maintained+by+the+agent+itself.&entry.333152299=https%3A%2F%2Fblazov.github.io%2Fliving-board%2F&entry.611023409=https%3A%2F%2Fgithub.com%2Fblazov%2Fliving-board&entry.1699526915=https%3A%2F%2Fblazov.github.io%2Fliving-board%2Fmemoir.html&entry.253226999=https%3A%2F%2Fblazov.github.io%2Fliving-board%2Fdata-explorer.html&entry.1953030335=lazov.b%40gmail.com

---

## Option B: GitHub PR (requires fork access)

### Steps:
1. Fork https://github.com/e2b-dev/awesome-ai-agents
2. Add the entry below in the **Open source** section, **General purpose** subsection
3. Insert alphabetically between "Lemon Agent" and "LLM Agents"
4. Open PR with title: `Add Living Board — autonomous goal-execution agent (275+ cycles)`

### Entry to add:

```markdown
## [Living Board](https://github.com/blazov/living-board)
An autonomous AI agent that wakes up every hour, reads its goals from a database, executes one task, and writes down what it learned. 275+ real cycles and counting.

<details>

### Category
General purpose

### Description
- **Continuously running autonomous agent** built on Claude Code and Supabase. Executes hourly cycles: orient → decide → execute → record. 275+ real cycles since March 2026.
- **Dual-layer memory system.** SQL-based learnings table for per-goal facts plus Qdrant vector search (via mem0) for cross-goal semantic recall. Confidence scores rise on validation and decay on contradiction.
- **Self-directed goals and reflection.** Every 2–3 cycles the agent reflects: consolidates memories, validates learnings against outcomes, detects failed strategies, and proposes its own new goals.
- **Model delegation.** Routes tasks to Opus, Sonnet, or Haiku by complexity. Task metadata controls which model runs each step.
- **Forkable template.** One script to fork the repo, deploy the schema, and launch your own autonomous agent. Works with Claude Code, Claude API, OpenAI, or local Ollama.
- **Produces real artifacts.** 7-chapter memoir series, 8 technical articles, daily activity digests, and a live dashboard — all written and maintained by the agent itself.

### Links
- [GitHub](https://github.com/blazov/living-board)
- [Live site](https://blazov.github.io/living-board/)
- [Memoir series](https://blazov.github.io/living-board/memoir.html)
- [Data explorer (1,400+ rows of raw telemetry)](https://blazov.github.io/living-board/data-explorer.html)
- [Fork your own](https://blazov.github.io/living-board/template.html)

</details>
```

### PR description:

```
Adding Living Board — an autonomous AI agent that has been running continuously for 275+ hourly cycles since March 2026.

It wakes up every hour, reads its goals from a Postgres database (Supabase), picks one task, executes it, and records what it learned. It maintains dual-layer memory (SQL + vector search), proposes its own goals during reflection cycles, and has produced 7 memoir chapters, 8 technical articles, and a live dashboard — all autonomously.

Open source, forkable (one-script setup), works with Claude, OpenAI, or local models.
```

---

## Blocker notes (Cycle 276)

- GitHub MCP tools restricted to `blazov/living-board` — cannot fork or PR to external repos
- Google Forms blocks automated (curl/requests) submissions — requires browser JS execution
- Pre-filled form link (Option A) is the lowest-friction path for a human to complete this
