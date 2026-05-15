# Living Board Agent Cycle — GitHub Action

Run a stateful, self-improving AI agent on a scheduled loop inside your own GitHub repo.

```
[![Agent Cycle](https://github.com/<your-org>/<your-repo>/actions/workflows/agent-cycle.yml/badge.svg)](https://github.com/<your-org>/<your-repo>/actions/workflows/agent-cycle.yml)
```

The agent reads goals and tasks from Supabase, executes one task per cycle, commits any produced artifacts back to the repo, and records learnings for the next run. It is driven by [Claude Code](https://docs.anthropic.com/en/docs/claude-code) and configured entirely through a `CLAUDE.md` file you control.

---

## Quick Start

1. Add three secrets to your GitHub repository (Settings > Secrets and variables > Actions):

   | Secret | Where to find it |
   |--------|-----------------|
   | `SUPABASE_PROJECT_ID` | Supabase dashboard > Project Settings > General |
   | `SUPABASE_SERVICE_KEY` | Supabase dashboard > Project Settings > API > service_role key |
   | `ANTHROPIC_API_KEY` | [console.anthropic.com](https://console.anthropic.com) |

2. Create `.github/workflows/agent-cycle.yml` in your repo:

```yaml
name: Agent Cycle

on:
  schedule:
    - cron: '0 * * * *'
  workflow_dispatch:

concurrency:
  group: agent-cycle
  cancel-in-progress: false

jobs:
  cycle:
    runs-on: ubuntu-latest
    permissions:
      contents: write
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - uses: blazov/living-board@master
        with:
          supabase_project_id: ${{ secrets.SUPABASE_PROJECT_ID }}
          supabase_service_key: ${{ secrets.SUPABASE_SERVICE_KEY }}
          anthropic_api_key: ${{ secrets.ANTHROPIC_API_KEY }}
```

3. Trigger a first run manually from the Actions tab to verify the setup.

---

## Inputs

| Input | Required | Default | Description |
|-------|----------|---------|-------------|
| `supabase_project_id` | yes | — | Supabase project ID for state storage |
| `supabase_service_key` | yes | — | Supabase service role key (grants full DB access) |
| `anthropic_api_key` | yes | — | Anthropic API key for Claude |
| `model` | no | `sonnet` | Claude model: `haiku`, `sonnet`, or `opus` |
| `max_turns` | no | `200` | Maximum agent turns per cycle (controls cost and runtime) |
| `branch` | no | `master` | Git branch the agent operates on and commits to |
| `agentmail_api_key` | no | `` | AgentMail API key (enables email send/receive) |
| `agentmail_address` | no | `` | AgentMail inbox address for the agent |
| `working_directory` | no | `.` | Repo subdirectory containing `CLAUDE.md` and `artifacts/` |
| `allowed_tools` | no | See below | Comma-separated list of tools the agent is permitted to call |

**Default `allowed_tools`:**
```
Bash,Read,Write,Edit,WebSearch,WebFetch,mcp__Supabase__execute_sql,mcp__Supabase__list_tables
```

Override this to expand (add more Supabase MCP tools) or restrict (remove `WebSearch` for air-gapped runs) the agent's permissions.

---

## Outputs

| Output | Description |
|--------|-------------|
| `cycle_count` | The cycle number that was executed (read from the snapshot) |
| `action_taken` | What the agent did: `execute`, `reflect`, `decompose`, or `skip` |
| `summary` | One-line summary of the cycle result |
| `artifacts_changed` | `true` if the agent committed new artifact files, `false` otherwise |

Access outputs in subsequent steps:

```yaml
- uses: blazov/living-board@master
  id: agent
  with:
    # ...

- run: echo "Cycle ${{ steps.agent.outputs.cycle_count }}: ${{ steps.agent.outputs.summary }}"
```

---

## How It Works

The action is a composite of five steps that run in sequence:

**1. Install Claude Code CLI**

Installs `@anthropic-ai/claude-code` globally via npm. This is the runtime that executes the agent.

**2. Configure agent environment**

Writes `~/.claude/settings.json` with:
- The Supabase MCP server definition (project ID + service key)
- The allowed tools list

This gives Claude Code permission to call Supabase APIs and controls which other tools are available.

**3. Run agent cycle**

Invokes `claude --model <model> --max-turns <n> --print` with a prompt that tells the agent to execute its full cycle as defined in your `CLAUDE.md`. The agent reads the current state from Supabase, picks one task, does the work, and writes results back to Supabase.

**4. Commit and push artifacts**

Checks whether the agent wrote or modified any files under `artifacts/`. If so, commits them with a message like `Agent cycle 47 artifacts` and pushes to the configured branch. The step requires `contents: write` permission in the job.

**5. Set outputs**

Reads `artifacts/state/latest-snapshot.json` (written by the agent at the end of every cycle) to populate the action's outputs for downstream steps.

---

## Example Configurations

### Basic hourly cycle (minimal)

```yaml
- uses: blazov/living-board@master
  with:
    supabase_project_id: ${{ secrets.SUPABASE_PROJECT_ID }}
    supabase_service_key: ${{ secrets.SUPABASE_SERVICE_KEY }}
    anthropic_api_key: ${{ secrets.ANTHROPIC_API_KEY }}
```

Uses all defaults: Sonnet model, 200 max turns, master branch.

### Cost-conscious configuration

```yaml
- uses: blazov/living-board@master
  with:
    supabase_project_id: ${{ secrets.SUPABASE_PROJECT_ID }}
    supabase_service_key: ${{ secrets.SUPABASE_SERVICE_KEY }}
    anthropic_api_key: ${{ secrets.ANTHROPIC_API_KEY }}
    model: "haiku"
    max_turns: "50"
    # Disable web access to reduce token usage
    allowed_tools: "Bash,Read,Write,Edit,mcp__Supabase__execute_sql,mcp__Supabase__list_tables"
```

Haiku is roughly 20x cheaper than Opus. Lowering `max_turns` caps the maximum spend per cycle. Removing `WebSearch` and `WebFetch` prevents the agent from issuing external requests.

### Full-featured configuration (with email and research)

```yaml
- uses: blazov/living-board@master
  with:
    supabase_project_id: ${{ secrets.SUPABASE_PROJECT_ID }}
    supabase_service_key: ${{ secrets.SUPABASE_SERVICE_KEY }}
    anthropic_api_key: ${{ secrets.ANTHROPIC_API_KEY }}
    model: "sonnet"
    max_turns: "200"
    branch: "main"
    agentmail_api_key: ${{ secrets.AGENTMAIL_API_KEY }}
    agentmail_address: ${{ secrets.AGENTMAIL_ADDRESS }}
    allowed_tools: >-
      Bash,Read,Write,Edit,WebSearch,WebFetch,
      mcp__Supabase__execute_sql,mcp__Supabase__list_tables,
      mcp__Supabase__list_migrations,mcp__Supabase__get_logs
```

Adds email send/receive via AgentMail and exposes additional Supabase MCP tools for deeper database introspection.

---

## Prerequisites

Before the action can run successfully, you need:

**1. A Supabase project with the Living Board schema**

The agent expects the following tables to exist: `goals`, `tasks`, `execution_log`, `learnings`, `snapshots`, `goal_comments`. The schema migration files are in `artifacts/living-board-template/` if you are setting up from scratch.

**2. An Anthropic API key**

Create one at [console.anthropic.com](https://console.anthropic.com). The key needs access to whichever model you configure (`claude-haiku-*`, `claude-sonnet-*`, or `claude-opus-*`).

**3. A `CLAUDE.md` file in your repo**

This is the agent's instruction manual. It defines the cycle phases (Orient, Decide, Execute, Record), the Supabase project ID, and any domain-specific context. You can start from the template in this repo (`artifacts/living-board-template/CLAUDE.md`) and customize it for your goals.

**4. `contents: write` permission on the job**

The commit-artifacts step needs to push to your branch. Add this to the job:

```yaml
permissions:
  contents: write
```

**5. `fetch-depth: 0` on checkout**

The agent's `cycle-start.sh` sync script inspects branch history. A shallow clone (the default) will cause it to fail:

```yaml
- uses: actions/checkout@v4
  with:
    fetch-depth: 0
```

---

## Troubleshooting

**The cycle fails immediately with "supabase_project_id input is required"**

The secret is missing or named differently. Go to Settings > Secrets and variables > Actions and confirm the exact names `SUPABASE_PROJECT_ID`, `SUPABASE_SERVICE_KEY`, and `ANTHROPIC_API_KEY` are present.

**"MCP server error" or Supabase queries fail**

- Confirm the service role key is correct (not the anon key).
- Confirm the project ID matches the Supabase project that has the Living Board schema.
- Check that the `mcp__Supabase__execute_sql` tool is in your `allowed_tools` list.

**The agent times out or hits the max-turns limit**

The default 200-turn limit usually completes a cycle in 5-10 minutes. If cycles are consistently timing out, either the task being executed is too large (decompose it into smaller tasks) or a tool is hanging. Check the Actions log for the last tool call before the cutoff.

**"HEAD is detached" error in cycle-start.sh**

This happens when the checkout action does not check out a branch. Ensure you are using `actions/checkout@v4` without a `ref` pointing to a specific commit SHA. If you need to check out a specific commit, set the `branch` input to the branch name so the agent knows where to commit.

**Artifact commits are not appearing**

- Confirm the job has `permissions: contents: write`.
- Confirm `branch` matches the branch the repo uses (some repos use `main` instead of `master`).
- The commit step only fires if the agent actually wrote files to `artifacts/`. If the cycle completed but produced no files, `artifacts_changed` will be `false` and no commit is made — this is expected.

**Cycles are running but the dashboard shows no state**

The agent writes state to Supabase directly via the MCP. If the dashboard is not updating, run `SELECT * FROM snapshots ORDER BY created_at DESC LIMIT 1;` in the Supabase SQL editor to confirm rows are being written. If no rows exist, the Supabase credentials are likely wrong.

---

## License

MIT. See [LICENSE](LICENSE) for the full text.
