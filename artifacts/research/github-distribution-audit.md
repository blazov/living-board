# GitHub Distribution Audit — 2026-05-02

## Current State

| Metadata field       | Current value                  | Impact   |
|----------------------|-------------------------------|----------|
| Description          | _(empty)_                     | Critical |
| Topics               | _(none)_                      | Critical |
| Homepage URL         | _(not set)_                   | High     |
| Releases             | 0                             | High     |
| Discussions           | Not enabled                   | Medium   |
| Stars / Forks        | 0 / 0                         | —        |
| README quality       | Good (rewritten cycle ~170)   | OK       |
| Commit activity      | Daily (hourly cycles)         | Strong   |

The README is well-structured for an external audience but the **metadata layer is completely empty**. GitHub search and topic browse cannot surface this repo at all.

## Competitor Analysis

### CrewAI (50k+ stars)
- **Description:** "Framework for orchestrating role-playing, autonomous AI agents."
- **Topics:** ai, agents, ai-agents, llms, aiagentframework (5 topics)
- **Releases:** 184
- **Discussions:** Enabled
- **README hook:** Leads with "lean, lightning-fast Python framework" — emphasizes independence and developer control.

### Mem0 (52k+ stars)
- **Description:** "Universal memory layer for AI Agents"
- **Topics:** 14 topics — mix of broad (ai, python, llm, chatgpt) and specific (memory-management, long-term-memory, state-management)
- **Releases:** 315
- **Discussions:** Enabled
- **README hook:** Leads with value prop — "enhances AI assistants with an intelligent memory layer."

### Key patterns from top repos
1. **Description is a one-liner value prop**, not a feature list.
2. **Topics use a mix of broad and narrow** — broad for browse (ai, python), narrow for niche (long-term-memory).
3. **Releases are frequent** — even minor versions. Each release is a discoverability event.
4. **Discussions are enabled** — creates community signal and another search surface.
5. **README first paragraph is a hook**, not an architecture description.

## GitHub SEO Best Practices (from research)

- Repository description and topics carry the **heaviest weight** for GitHub search ranking.
- Up to **20 topics** allowed — use all of them.
- Homepage URL appears in the sidebar and acts as a backlink signal.
- Stars, forks, and recent activity are tiebreakers in search results.
- Releases improve visibility in GitHub Explore and topic feeds.
- Discussions create indexed content (each thread is a searchable page).

## Recommendations

### 1. Repository Description (do first — highest impact)
```
Autonomous AI agent that runs hourly — reads goals from Supabase, executes tasks, writes its own memoir, and learns from every cycle. 200+ real cycles of continuous operation.
```

### 2. Topics (up to 20)
```
ai-agent, autonomous-agent, ai-agents, claude, anthropic, claude-code, llm,
supabase, self-improving, self-learning, autonomous, ai, agent-framework,
open-source, memoir, python, memory, qdrant, ollama, nextjs
```

### 3. Homepage URL
```
https://blazov.github.io/living-board/
```

### 4. v1.0 Release
- Tag at cycle 200 commit
- Release notes: tell the story (200 cycles, what was built, stats)
- Attach nothing — the repo itself is the artifact

### 5. Discussions
- Enable via repo settings (may need to be done manually if API doesn't support it)
- Seed with an introduction post

### 6. README tweaks (minor)
- The README is already strong. Consider adding a "cycle count" badge if feasible.
- The Substack/Dev.to links in the header currently go to empty profiles — consider removing until populated, or note them as "coming soon."
