# GitHub Action Design Spec

**Date:** 2026-05-15 | **Task:** Design action.yml schema and composite step architecture

---

## 1. Action Identity

```yaml
name: "Living Board Agent Cycle"
description: "Run a stateful, self-improving AI agent cycle with Supabase-backed goals, tasks, and learnings"
author: "blazov"
branding:
  icon: cpu
  color: purple
```

---

## 2. Inputs

### Required

| Input | Description | Why required |
|-------|-------------|--------------|
| `supabase_project_id` | Supabase project ID | Agent reads/writes goals, tasks, learnings |
| `supabase_service_key` | Supabase service role key (secret) | Auth for execute_sql via MCP |
| `anthropic_api_key` | Anthropic API key (secret) | Powers Claude Code CLI |

### Optional

| Input | Default | Description |
|-------|---------|-------------|
| `model` | `sonnet` | Claude model: `haiku`, `sonnet`, or `opus` |
| `max_turns` | `200` | Max agent turns per cycle (controls cost) |
| `branch` | `master` | Git branch the agent operates on |
| `agentmail_api_key` | `""` | AgentMail API key (enables email features) |
| `agentmail_address` | `""` | AgentMail inbox address |
| `working_directory` | `.` | Repo subdirectory to operate in |
| `allowed_tools` | `Bash,Read,Write,Edit,WebSearch,WebFetch,mcp__Supabase__execute_sql,mcp__Supabase__list_tables` | Comma-separated tools to allow |

**Design decision — no `cycle_script` override input.** The agent's behavior is defined by CLAUDE.md, not by a script. Users customize behavior by editing CLAUDE.md, not by swapping entrypoint scripts. This keeps the action simple and opinionated.

---

## 3. Outputs

| Output | Description |
|--------|-------------|
| `cycle_count` | The cycle number that was executed |
| `action_taken` | What the agent did: `execute`, `reflect`, `decompose`, or `skip` |
| `summary` | One-line summary of the cycle result |
| `artifacts_changed` | `true`/`false` — whether the agent committed new artifacts |

---

## 4. Architecture: Composite Action

### Why composite (not Docker, not JavaScript)

- The agent cycle is shell-orchestrated: checkout → sync → run Claude Code CLI → commit
- No build toolchain needed — shell scripts are already the native format
- Cross-platform (though Linux runners are the primary target)
- Every `run:` step gets explicit `shell: bash` (composite action requirement)

### Step Flow

```
┌─────────────────────────────────────────────┐
│ 1. Setup: Install Claude Code CLI           │
│    - npm install -g @anthropic-ai/claude-code│
├─────────────────────────────────────────────┤
│ 2. Configure: Write MCP settings + .env     │
│    - Write Supabase MCP config to settings  │
│    - Export ANTHROPIC_API_KEY               │
├─────────────────────────────────────────────┤
│ 3. Sync: Run cycle-start.sh                 │
│    - Ensures branch is aligned with origin  │
├─────────────────────────────────────────────┤
│ 4. Execute: Run claude-code with prompt      │
│    - "Execute your full agent cycle..."     │
│    - Reads CLAUDE.md, orients, decides, acts│
│    - Max turns controlled by input          │
├─────────────────────────────────────────────┤
│ 5. Commit & Push: Persist artifacts         │
│    - git add artifacts/                     │
│    - git commit (if changes)                │
│    - git push origin <branch>               │
├─────────────────────────────────────────────┤
│ 6. Output: Set action outputs               │
│    - Parse execution_log for cycle summary  │
└─────────────────────────────────────────────┘
```

### Step Details

**Step 1: Install Claude Code CLI**
```yaml
- name: Install Claude Code CLI
  shell: bash
  run: npm install -g @anthropic-ai/claude-code
```

**Step 2: Configure MCP and environment**
```yaml
- name: Configure agent environment
  shell: bash
  env:
    SUPABASE_PROJECT_ID: ${{ inputs.supabase_project_id }}
    SUPABASE_SERVICE_KEY: ${{ inputs.supabase_service_key }}
  run: |
    # Write Claude Code settings with Supabase MCP
    mkdir -p ~/.claude
    cat > ~/.claude/settings.json << 'SETTINGS'
    {
      "permissions": {
        "allow": ["Bash", "Read", "Write", "Edit", "WebSearch", "WebFetch",
                   "mcp__Supabase__execute_sql", "mcp__Supabase__list_tables"]
      },
      "mcpServers": {
        "Supabase": {
          "command": "npx",
          "args": ["-y", "@anthropic-ai/claude-mcp-server-supabase",
                   "--access-token", "$SUPABASE_SERVICE_KEY",
                   "--project-id", "$SUPABASE_PROJECT_ID"]
        }
      }
    }
    SETTINGS
```

**Step 3: Sync** — skipped in action context. The action checks out fresh via `actions/checkout@v4` before running, so `cycle-start.sh` handles alignment inside the Claude session. No separate step needed.

**Step 4: Execute agent cycle**
```yaml
- name: Run agent cycle
  shell: bash
  env:
    ANTHROPIC_API_KEY: ${{ inputs.anthropic_api_key }}
  run: |
    claude --model ${{ inputs.model }} \
      --max-turns ${{ inputs.max_turns }} \
      --print \
      "Execute your full agent cycle as defined in CLAUDE.md. Orient, Decide, Execute, Record."
```

**Step 5: Commit and push artifacts**
```yaml
- name: Commit and push artifacts
  shell: bash
  run: |
    cd ${{ inputs.working_directory }}
    git config user.name "living-board-agent"
    git config user.email "agent@living-board.dev"
    if [ -n "$(git status --porcelain artifacts/)" ]; then
      git add artifacts/
      CYCLE=$(grep -o '"cycle_count":[0-9]*' artifacts/state/latest-snapshot.json | grep -o '[0-9]*' || echo "?")
      git commit -m "Agent cycle $CYCLE artifacts"
      git push origin ${{ inputs.branch }}
    fi
```

**Step 6: Set outputs** — parse the local state for summary info.

---

## 5. User Workflow Example

The user's `.github/workflows/agent-cycle.yml`:

```yaml
name: Agent Cycle
on:
  schedule:
    - cron: "0 * * * *"  # every hour
  workflow_dispatch:       # manual trigger

jobs:
  cycle:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          ref: master
          token: ${{ secrets.GITHUB_TOKEN }}

      - uses: blazov/living-board@v1
        with:
          supabase_project_id: ${{ secrets.SUPABASE_PROJECT_ID }}
          supabase_service_key: ${{ secrets.SUPABASE_SERVICE_KEY }}
          anthropic_api_key: ${{ secrets.ANTHROPIC_API_KEY }}
          model: sonnet
          max_turns: 200
```

Minimal config: 3 secrets + 5 lines of YAML. That's the pitch.

---

## 6. Key Design Decisions

### 6a. Composite vs Docker
**Composite wins.** Docker adds ~30s startup for image pull, restricts to Linux, and requires maintaining a Dockerfile. Composite is ~0s overhead and can install Claude Code via npm in ~10s.

### 6b. Claude Code CLI vs API
**CLI wins.** The agent cycle is defined in CLAUDE.md — a Claude Code native format. The CLI reads CLAUDE.md, has built-in MCP support, handles tool orchestration, and supports `--max-turns`. Calling the raw API would require reimplementing all of this.

### 6c. Single action vs action + reusable workflow
**Single action.** A reusable workflow would give more control (can define the full job), but an action is the marketplace-listable unit. Keep the action as the primary artifact; provide an example workflow in docs.

### 6d. Secrets handling
All secrets are passed as inputs (which GitHub masks in logs). The action never echoes them. The MCP config file is written at runtime and lives only in the ephemeral runner.

### 6e. Git push permissions
The user must pass a token with push access. `GITHUB_TOKEN` works for the same repo. The action sets git user to `living-board-agent` for clean attribution.

### 6f. Scope of the action
The action runs ONE cycle. Scheduling is handled by the workflow's `cron` trigger, not by the action itself. This is the standard GitHub Actions pattern and keeps the action stateless between runs.

---

## 7. File Layout (to implement)

```
living-board/
├── action.yml                     # The marketplace-listed action
├── action/
│   ├── entrypoint.sh              # Main orchestration script
│   ├── configure-mcp.sh           # Writes MCP settings
│   └── commit-artifacts.sh        # Commit & push if changed
├── .github/workflows/
│   └── agent-cycle.example.yml    # Example workflow for users
```

The `action/` directory keeps helper scripts organized without cluttering the repo root. `action.yml` at the root is required for marketplace listing.

---

## 8. Open Questions (for future tasks)

1. **Node.js version**: Should we pin `node` version or use whatever the runner has? (Ubuntu latest has Node 20+, which is fine.)
2. **Claude Code version pinning**: `npm install -g @anthropic-ai/claude-code@latest` vs a specific version? Latest is simpler but less reproducible.
3. **Cost guardrails**: `max_turns` caps cost, but should we also expose `max_tokens` or a dollar-budget input?
4. **Multi-repo**: Some users might want the action in repo A but the agent's working repo is repo B. Out of scope for v1.
