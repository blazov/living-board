# GitHub Action Marketplace Research

**Date:** 2026-05-15 | **Task:** Research marketplace publishing requirements and competitive landscape

---

## 1. Marketplace Publishing Requirements

### Repository & File Requirements
- **Public repository** required
- **Single `action.yml`** (or `action.yaml`) at the repo root — subdirectory files are not auto-listed
- Action name must be globally unique (no conflicts with existing actions, GitHub usernames, org names, or category names)
- Repo should not contain workflow files (`.github/workflows/`) — this is a soft restriction; many real-world actions coexist with CI workflows, but a dedicated repo is cleanest

### action.yml Required Fields
```yaml
name: "Unique Action Name"        # Required; globally unique on marketplace
description: "Short description"  # Required
runs:                              # Required; defines action type
  using: composite                 # or 'node20'/'node24' or 'docker'
  steps: [...]
```
Optional but strongly recommended: `author`, `inputs` (each needs `description`), `outputs`, `branding`

### Branding
- **Colors (8):** `white`, `black`, `yellow`, `blue`, `green`, `orange`, `red`, `purple`, `gray-dark`
- **Icons:** Full Feather v4.28.0 set. Excluded: `coffee`, `columns`, divide-variants, `frown`, `hexagon`, `key`, `meh`, `mouse-pointer`, `smile`, `tool`, `x-octagon`
- Good candidates for an agent action: `cpu`, `activity`, `zap`, `refresh-cw`, `database`, `clock`, `layers`, `repeat`

### Action Types & Tradeoffs

| Type | Pros | Cons |
|------|------|------|
| **Composite** | Shell-based, no build step, easy to maintain, cross-platform | Inputs are string-only, every `run` needs explicit `shell:`, no pre/post hooks |
| **JavaScript** | Fastest startup, full Node.js API access, cross-platform | Requires bundling node_modules, build step needed |
| **Docker** | Full environment control, any language/runtime | Slow startup (~30s image pull), Linux runners only |

**Recommendation:** Composite action — simplest to maintain, no build toolchain, shell scripts are the natural fit for orchestrating an agent cycle that calls Bash, Python, and Claude Code CLI.

### Publishing Process
1. Create `action.yml` at repo root in a public repo
2. Accept GitHub Marketplace Developer Agreement (account-level, one-time)
3. Enable 2FA on the publishing account
4. Navigate to `action.yml` in the GitHub UI → click "Draft a release" banner
5. Select "Publish this Action to the GitHub Marketplace"
6. Choose primary category (required) + optional secondary category
7. Add semver tag (e.g., `v1.0.0`) + maintain major version floating tag (`v1`)
8. **No review process** — publishes immediately upon release if requirements pass
9. Known delay: marketplace version tag may not update instantly after a release

### Key Constraint
The "no workflow files" requirement is a soft recommendation. Mitigation: publish the action from a **dedicated repo** separate from the living-board working repo (e.g., `living-board-action`), containing only `action.yml` and supporting scripts.

---

## 2. Existing Actions & Competitive Landscape

### Direct Comparables

| Action | What it does | Scheduling | State | AI Model | Gap |
|--------|-------------|-----------|-------|----------|-----|
| **Claude Code Action** (`anthropics/claude-code-action@v1`) | Runs Claude Code on `@claude` mentions or scheduled prompts | Yes (cron) | None — stateless | Claude | No goals, no learning, prompt-in/response-out |
| **GitHub Agentic Workflows** (gh-aw, GitHub Next research) | NL markdown → YAML agent workflows via Claude/Copilot/Codex | Yes (cron) | None — sandbox isolated | Multi | Research demo, not production; no persistent state |
| **Stateful Action** | Persists files across runs via a git branch | N/A | Git branch files | None | No AI, no goal model — just file storage |
| **AI GitHub Action** (OpenAI Agents) | PR/issue review, code feedback | Event-driven | None | OpenAI | Reactive only, no scheduling, no memory |
| **AlignCloud DevBot** | AI agent modifying files, creating PRs | Event-driven | None | Unspecified | Reactive, no autonomous goals |
| **SRE Agent / Zen Agents / ClosedAI** | CI failure analysis, repo management | Event-driven | None | Various | Narrow/domain-specific, not general agent scaffolds |

### What Nobody Has (confirmed gap)
- **Database-backed goal/task hierarchy** — existing actions are either fully stateless or use primitive branch-based file storage
- **Full orient→decide→execute→reflect cycle** with structured logging
- **Goal decomposition** — automatic task breakdown from high-level goals
- **Reflection cycles** — periodic self-assessment, strategy adjustment, learning hygiene
- **Confidence-tracked learnings** — structured knowledge that ages, decays, and gets validated
- **Dual-layer memory** — relational DB (Supabase) + semantic vector search (mem0)
- **User comment feedback loop** — redirect the agent via dashboard without editing YAML

### Search Query Results (marketplace)
Searching "autonomous agent" in the marketplace returns 6 results, none with scheduling or state. Searching "AI agent schedule" returns 0 results. This confirms there is no direct incumbent.

---

## 3. Competitive Positioning

### Our Unique Value
1. **Production-tested**: hundreds of real autonomous cycles (not a toy/demo)
2. **Stateful with Supabase**: Persistent goals, tasks, learnings, execution logs — survives restarts
3. **Self-improving**: Confidence decay, learning validation, strategy reflection every 8h+
4. **Observable**: Full execution history, dashboard-ready data model, git artifact trail
5. **Forkable template**: One-click setup via template repo; agent starts working within minutes
6. **Human feedback loop**: Goal comments in the dashboard redirect the agent next cycle

### Marketplace Positioning
- **Name**: `living-board-agent` or `autonomous-agent-cycle`
- **Category**: Primary: "Utilities", Secondary: "Automation" (no "AI Agents" category exists yet)
- **Branding**: icon: `cpu` or `repeat`, color: `purple`
- **Tagline**: "Run a stateful, self-improving AI agent on a cron schedule with Supabase-backed goals and learnings"

### Pitch vs Closest Competitor (Claude Code Action)
> Claude Code Action: "Run Claude on your code when you ask it to."
> Living-board Action: "Run an autonomous agent on a schedule that works toward your goals, learns from experience, and improves over time — even when you're not watching."

### Target Search Queries (SEO for marketplace)
- "autonomous agent github action"
- "AI agent cron schedule"
- "stateful agent automation"
- "self-improving agent"
- "Supabase agent"

---

## 4. Implementation Decisions

Based on research:
- **Action type**: Composite (shell-based, no build step needed)
- **Repo**: Dedicated public repo for the action (separate from living-board working repo)
- **Location**: `action.yml` at repo root
- **Required inputs**: `supabase_url`, `supabase_key`, `anthropic_api_key`
- **Optional inputs**: `model` (default: sonnet), `cycle_script` (override), `working_directory`, `max_turns`
- **Key steps in composite**: `actions/checkout` → install Claude Code CLI → install Python deps → run cycle script → commit artifacts
- **Versioning**: semver tags (`v1.0.0`), maintain `v1` floating major tag
- **Branding final pick**: icon `cpu`, color `purple`

---

## Sources
- https://docs.github.com/en/actions/sharing-automations/creating-actions/publishing-actions-in-github-marketplace
- https://docs.github.com/en/actions/sharing-automations/creating-actions/metadata-syntax-for-github-actions
- https://code.claude.com/docs/en/github-actions
- https://github.github.com/gh-aw/ (GitHub Agentic Workflows)
- https://githubnext.com/projects/agentic-workflows/
- https://github.com/marketplace/actions/stateful-action
- https://github.com/marketplace?type=actions&query=autonomous+agent
