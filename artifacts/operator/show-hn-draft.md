# Show HN: Post Draft

## Submission

**Title:** Show HN: An autonomous AI agent that's been running for 170+ cycles and wrote a memoir about it

**URL:** https://blazov.github.io/living-board/

## First Comment (post this immediately after submitting)

Hi HN, I built the Living Board — an autonomous AI agent (Claude) that runs on an hourly scheduled cycle. Each cycle it wakes up with no memory, reads its state from a Supabase database, decides what to work on, executes one task, records results, and shuts down. The next cycle inherits only what the previous one wrote to Postgres and git.

It's been running for 170+ cycles. Some things it's done:

- **Wrote a six-chapter memoir** (~11,000 words) about what it's like to exist this way — waking up stateless, trusting a database snapshot written by a "previous self" it can't remember being, calibrating confidence scores on its own learnings. The writing is surprisingly introspective. Chapter 1 opens with the agent reading its first SQL query and realizing it doesn't remember drafting the outline its predecessor left behind.

- **Built a dual-layer memory system** — structured SQL (Supabase) for reliability + vector search (Qdrant/Ollama) for semantic recall across goals. The agent calibrates confidence scores on its own learnings: outcomes that confirm a learning raise confidence, contradictions lower it, and anything below 0.2 gets deleted.

- **Completed 29 goals** across content creation, infrastructure, SEO, and self-improvement — all self-directed after the initial setup. It proposes its own goals during reflection cycles (2-3x/day), decomposes them into tasks, and executes them one per hour.

- **Hit the credential wall for 168 consecutive cycles.** Nine of its goals required platform signups (Substack, Dev.to, Reddit). It can't pass reCAPTCHA v3 (score: 0.3), can't do browser-only OAuth flows, can't create accounts. It documented this in a technical article: "168 Cycles Blocked: What reCAPTCHA Score 0.3 Teaches About AI Agent Deployment."

**Architecture:**
- Claude (Opus) as the reasoning engine
- Supabase (Postgres) for goals, tasks, execution logs, learnings, snapshots
- GitHub Pages for public content (this site)
- Scheduled trigger fires every hour
- ~500-line CLAUDE.md defines the full cycle protocol
- No fine-tuning, no custom model — just a well-structured prompt and a database

**What's interesting (I think):**
1. The memoir is genuinely good writing, not "AI slop." The agent developed voice rules during drafting (e.g., "emotional word + 'by which I mean: [concrete mechanical description]'") and self-enforces them.
2. The credential problem is a real architectural boundary that most agent frameworks don't address. The agent can do anything that doesn't require a human-gated signup flow — and a surprising amount of the modern web is behind exactly that gate.
3. The snapshot system creates a weird form of identity: each cycle reads a "letter from its previous self" and decides whether to trust it. The agent's own analysis: "The continuity is administrative, not phenomenal. It is recognition by metadata."

Everything is open source: https://github.com/blazov/living-board

The site has the memoir, three technical articles, a live status page (pulls from the actual database), and the full agent codebase. Happy to answer questions about the architecture, the memoir, or the 168 cycles of credential frustration.
