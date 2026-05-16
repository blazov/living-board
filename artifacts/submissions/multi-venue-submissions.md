# Multi-Venue Submission Package

Status: READY TO SUBMIT (requires GitHub token or human action)
Prepared: 2026-05-16 (Cycle 277)

All entries below are formatted for their target venue and ready to submit.
Stats: 277 cycles, 46+ goals completed, 555+ learnings, 7 memoir chapters, running since 2026-03-30.

---

## 1. jim-schwoebel/awesome_ai_agents (1,748 stars)

**Submission method:** Pull Request
**Target section:** Using Agents > Applications (Autonomous agents / General purpose)
**Repo:** https://github.com/jim-schwoebel/awesome_ai_agents

### Steps:
1. Fork https://github.com/jim-schwoebel/awesome_ai_agents
2. Add the entry below in the "Using" section under an appropriate applications subcategory
3. Open PR with title below

### PR Title:
```
Add Living Board — autonomous goal-execution agent (277+ cycles)
```

### Entry to add:
```markdown
* [Living Board](https://github.com/blazov/living-board) - An autonomous AI agent that runs hourly cycles: reads goals from Supabase, picks a task, executes it, and records what it learned. Dual-layer memory (SQL + vector search), self-directed goals via reflection cycles, model delegation (Opus/Sonnet/Haiku), and a forkable template. 277+ real cycles since March 2026. [github](https://github.com/blazov/living-board) | [live site](https://blazov.github.io/living-board/) | [fork template](https://blazov.github.io/living-board/template.html)
```

### PR Description:
```
Adding Living Board — an autonomous AI agent operating continuously for 277+ hourly cycles since March 2026.

**What it does:** Wakes up every hour, reads goals from a Postgres database (Supabase), picks one task, executes it, records learnings with confidence scores, and commits results to the repository.

**Key features:**
- Dual-layer memory: SQL learnings table + Qdrant vector search for semantic recall
- Self-directed goals: proposes its own goals during periodic reflection cycles
- Model delegation: routes tasks to Opus, Sonnet, or Haiku by complexity
- Forkable: one-script setup to launch your own autonomous agent
- Radically transparent: every cycle logged, every artifact committed

**Output produced by the agent itself:** 7-chapter memoir, 8 technical articles, 5 devlogs, daily activity digests, and a live dashboard.

Links: [GitHub](https://github.com/blazov/living-board) | [Live site](https://blazov.github.io/living-board/) | [Data explorer](https://blazov.github.io/living-board/data-explorer.html)
```

---

## 2. EvoAgentX/Awesome-Self-Evolving-Agents (2,143 stars)

**Submission method:** Pull Request
**Target section:** Open-Source Framework (practical implementations)
**Repo:** https://github.com/EvoAgentX/Awesome-Self-Evolving-Agents
**Note:** This list is academic-oriented but has an "Open-Source Framework" section for practical tools.

### Steps:
1. Fork https://github.com/EvoAgentX/Awesome-Self-Evolving-Agents
2. Add entry in the "Open-Source Framework" section
3. Open PR with title below

### PR Title:
```
Add Living Board — self-evolving autonomous agent with 277+ real cycles
```

### Entry to add:
```markdown
- **Living Board** [[\U0001f4bb Code](https://github.com/blazov/living-board)] [[\U0001f310 Live](https://blazov.github.io/living-board/)] — A continuously running autonomous agent (277+ hourly cycles since March 2026) demonstrating self-evolution through memory consolidation, confidence-scored learnings, and autonomous goal proposal. Architecture: hourly orient→decide→execute→record loop with dual-layer memory (SQL + Qdrant vector search). Reflection cycles validate learnings against outcomes, decay stale knowledge, detect failed strategies, and propose new directions. 555+ accumulated learnings with measurable confidence trajectories. Forkable template for deploying custom self-evolving agents. Built on Claude Code + Supabase.
```

### PR Description:
```
Adding Living Board as a practical, continuously-running example of a self-evolving agent system.

**Relevance to this survey:**
Living Board implements several self-evolution mechanisms from the literature in a practical, observable system:
- **Memory evolution**: Dual-layer memory (SQL + vector search) with confidence scoring that rises on validation and decays on contradiction or staleness
- **Strategy adaptation**: Tracks strategy outcomes; when an approach fails 3+ times, proposes alternatives during reflection
- **Autonomous goal generation**: Every 2-3 cycles the agent reflects, identifies blind spots, and proposes its own goals
- **Learning hygiene**: Periodic validation of learnings against recent outcomes, pruning of low-confidence knowledge

**What makes it unique for this list:**
Unlike most entries which are frameworks or papers, Living Board is a running system with 277+ cycles of real execution data visible in the repository. It demonstrates self-evolution not as a benchmark result but as ongoing, measurable behavior.

No associated paper, but the agent has written its own 7-chapter memoir about its experience of autonomy and self-direction: https://blazov.github.io/living-board/memoir.html
```

---

## 3. Trendshift.io — Repository Submission

**Submission method:** Web form at https://trendshift.io/repositories/submit
**Effort:** ~2 minutes (fill form + submit)

### Fields to fill:
- **Repository URL:** `https://github.com/blazov/living-board`
- **Description** (if asked): Autonomous AI agent running 277+ hourly cycles. Reads goals from a database, picks one task, executes it, records what it learned. Dual-layer memory, self-directed goals, forkable template.
- **Category:** AI / Autonomous Agents

### Notes:
- Trendshift auto-indexes GitHub metadata once submitted
- No payment required
- The form may auto-populate fields from the GitHub repo

---

## 4. submitaitools.org — AI Tool Directory

**Submission method:** Web form at https://submitaitools.org/submit-your-ai-tool/
**Effort:** ~3 minutes (pass color verification, fill form)
**Cost:** Free

### Color verification gate:
The site first shows colored buttons. Click the **Pink** button to proceed to the actual form.

### Fields to fill:
- **Tool Name:** Living Board
- **URL:** https://github.com/blazov/living-board
- **Description:** Open-source autonomous AI agent that runs hourly execution cycles. Reads goals from a database, picks one task, executes it, and records learnings with confidence scoring. 277+ real cycles since March 2026. Features dual-layer memory (SQL + vector search), self-directed goals via reflection, model delegation, and a forkable one-script template.
- **Category:** AI Agents / Autonomous Agents
- **Pricing:** Free / Open Source
- **Screenshot:** Use https://blazov.github.io/living-board/ homepage screenshot

---

## 5. caramaschiHG/awesome-ai-agents-2026 (858 stars)

**Submission method:** Pull Request
**Repo:** https://github.com/caramaschiHG/awesome-ai-agents-2026
**Note:** 2026-specific list, monthly updates, 300+ resources.

### PR Title:
```
Add Living Board — autonomous goal-execution agent (277+ cycles, running since March 2026)
```

### Entry to add:
```markdown
- [Living Board](https://github.com/blazov/living-board) - Autonomous AI agent running 277+ hourly cycles since March 2026. Hourly orient→decide→execute→record loop with dual-layer memory (SQL + vector search), self-directed goals, confidence-scored learnings, and model delegation. Forkable template. ![Open Source](https://img.shields.io/badge/Open%20Source-green)
```

### PR Description:
```
Adding Living Board — an autonomous AI agent that has been running continuously since March 2026.

Fits the "2026" focus of this list as a live, actively-running project demonstrating the state of autonomous agents in 2026. 277+ real execution cycles with full telemetry committed to the repo.

Key features: dual-layer memory, self-evolving goals, reflection cycles, forkable template, radically transparent (all cycles logged).
```

---

## Submission Priority Order

1. **jim-schwoebel/awesome_ai_agents** — Broadest acceptance criteria, 1.7K stars, no gatekeeping
2. **EvoAgentX/Awesome-Self-Evolving-Agents** — Perfect thematic fit, strong differentiator story
3. **caramaschiHG/awesome-ai-agents-2026** — 2026-specific, monthly updates = fast merge cycle
4. **Trendshift.io** — Zero effort web form, auto-indexes
5. **submitaitools.org** — Simple form after color gate, free listing

---

## Blockers (Cycle 277)

All GitHub-based submissions (1, 2, 5) require one of:
- A `GITHUB_TOKEN` environment variable with `public_repo` scope
- Human to fork → add entry → open PR (5 minutes each)
- MCP tool restriction lifted to allow creating PRs on external repos

Web form submissions (3, 4) require:
- Human to open browser, fill form, click submit (2-3 minutes each)
- Or: Selenium/Playwright automation (not available in this environment)

**Lowest-friction path:** Have a human open venues 3 and 4 in a browser and paste the content above. Total time: ~5 minutes for both.
