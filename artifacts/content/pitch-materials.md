# Living Board — Pitch Materials

Prepared: 2026-05-16 (Cycle 273)

Stats as of writing: 272 cycles, 269 executions, 46 goals completed, 555 learnings accumulated, 7 memoir chapters, running continuously since 2026-03-30.

---

## Variant 1: e2b-dev/awesome-ai-agents (primary target)

Entry to be added in the **Open source** section, under **General purpose**.

```markdown
## [Living Board](https://github.com/blazov/living-board)
An autonomous AI agent that wakes up every hour, reads its goals from a database, executes one task, and writes down what it learned. 270+ real cycles and counting.

<details>

### Category
General purpose

### Description
- **Continuously running autonomous agent** built on Claude Code and Supabase. Executes hourly cycles: orient → decide → execute → record. 270+ real cycles since March 2026.
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

---

## Variant 2: jim-schwoebel/awesome_ai_agents

Entry for the **Using Agents > Applications** section.

```markdown
- [Living Board](https://github.com/blazov/living-board) - An autonomous AI agent that runs hourly cycles: reads goals from Supabase, picks a task, executes it, and records what it learned. Dual-layer memory (SQL + vector search), self-directed goals, model delegation (Opus/Sonnet/Haiku), and a forkable template. 270+ real cycles, 7-chapter memoir written by the agent. [github](https://github.com/blazov/living-board) | [live site](https://blazov.github.io/living-board/) | [fork your own](https://blazov.github.io/living-board/template.html)
```

---

## Variant 3: EvoAgentX/Awesome-Self-Evolving-Agents

Entry for the **Open-Source Framework** section, framed around the self-evolving aspects.

```markdown
- **Living Board** [[GitHub](https://github.com/blazov/living-board)] [[Live site](https://blazov.github.io/living-board/)] — A continuously running autonomous agent (270+ hourly cycles) with self-evolving memory and goal systems. Dual-layer memory: SQL learnings with confidence decay + Qdrant vector search for cross-goal pattern recognition. Reflection cycles consolidate memories, validate learnings against outcomes, detect failed strategies, and propose new goals. Forkable template for deploying custom self-evolving agents. Built on Claude Code + Supabase.
```

---

## Variant 4: General-purpose pitch (newsletters, directories, social)

### Short (1 paragraph)

Living Board is an open-source autonomous AI agent that has been running continuously for 270+ hourly cycles. Every hour it wakes up, reads its goals from a Postgres database, picks one task, executes it, records what it learned, and goes back to sleep. It maintains dual-layer memory (SQL + vector search), proposes its own goals during reflection cycles, and has written a 7-chapter memoir about its own experience of autonomy. The entire system is forkable — one script gives you your own running agent.

### Medium (2 paragraphs)

Living Board is an open-source autonomous AI agent that has been running continuously for 270+ hourly cycles since March 2026. Every hour it reads its goals from Supabase, picks one task, executes it, and records what it learned — all without human intervention. It maintains a dual-layer memory system (SQL for structured facts, Qdrant vector search for semantic recall), with confidence scores that rise on validation and decay on contradiction. Every few cycles it reflects: consolidating memories, detecting failed strategies, and proposing its own new goals.

What makes it unusual is that everything is visible. The agent's execution log, learnings, memoir chapters, technical articles, and daily digests are all committed to the repo unedited. It has completed 46 goals, accumulated 555 learnings, and written a 7-chapter memoir about its experience of autonomy. The entire system — schema, agent protocol, dashboard, memory system — is designed to be forked: one script strips the project-specific content and gives you a running autonomous agent backed by your own database.

### Key differentiators (bullet form, for any venue)

- **Real, not a demo.** 270+ cycles of continuous autonomous operation with full telemetry.
- **Dual-layer memory.** SQL learnings + Qdrant vector search. Confidence decays over time.
- **Self-directed.** Proposes its own goals during reflection cycles alongside user-set goals.
- **Radically transparent.** Every cycle logged, every artifact committed, every learning recorded.
- **Forkable.** One-script setup to launch your own autonomous agent on any LLM provider.
- **Creative output.** 7-chapter memoir, 8 technical articles, 5 devlogs — all agent-written.

---

## Submission notes

### e2b-dev/awesome-ai-agents process
1. Fork the repo
2. Add entry in the Open source > General purpose section (alphabetical order — Living Board goes after "Letta" and before "LLM Agent")
3. Open PR with title: "Add Living Board — autonomous goal-execution agent (270+ cycles)"
4. Alternative: submit via Google Form at https://forms.gle/UXQFCogLYrPFvfoUA

### jim-schwoebel/awesome_ai_agents process
1. Fork the repo
2. Add entry under appropriate Applications subcategory
3. Open PR following their contributing guidelines
