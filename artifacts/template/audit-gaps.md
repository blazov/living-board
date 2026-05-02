# Template Audit: Gaps vs Current CLAUDE.md

Audit date: 2026-05-02 (Cycle 191)

## CLAUDE.md.template Gaps

### Critical Missing Sections

1. **Phase 0: Sync** — The current CLAUDE.md has a detailed Phase 0 requiring `bash artifacts/scripts/cycle-start.sh` as the literal first bash call. The template jumps straight to Phase 1. This is the most important infrastructure piece — it keeps the agent aligned with origin/master after waking from a detached HEAD.

2. **One-time setup (per clone)** — Current CLAUDE.md has a section about installing the pre-commit hook (`bash artifacts/scripts/install-pre-commit-hook.sh`). Template has nothing.

3. **Heartbeat/scheduler observability** — Current CLAUDE.md documents `scheduler-status.sh` output appended to cycle-start, the `[scheduler]` log line format, and the 6h gap warning. Template has none.

### Sections Present But Incomplete

4. **Phase 1c: Email check** — Template has a 10-line stub ("if you have email configured..."). Current CLAUDE.md has full AgentMail SDK examples with `{{AGENTMAIL_ADDRESS}}` placeholder, detailed triage instructions, and logging SQL. Template needs the full version with `{{AGENTMAIL_ADDRESS}}` and `{{AGENTMAIL_API_KEY}}` placeholders.

5. **Phase 1b: Reflection** — Template is missing:
   - Detailed memory consolidation steps (duplicate search with --threshold 0.85, strategy review)
   - Learning validation rules (confidence +0.1 on confirm, -0.15 on contradict, delete below 0.2)
   - "Also insert meta-learnings as learnings with goal_id = NULL"
   - Explicit "do not also execute a task in the same cycle" instruction

6. **Phase 4: Record — strategy recording** — Current CLAUDE.md includes recording strategy memories via mem0 after task execution. Template omits this.

7. **User Comments standalone section** — Current CLAUDE.md has a dedicated "User Comments" section (separate from Phase 1d) that lists comment types and processing rules. Template relies only on Phase 1d.

### Minor Gaps

8. **Goal Decomposition** — Current says "single 1-hour agent cycle"; template says "single agent cycle" (no time reference). Minor but useful for setting expectations.

9. **Identity section** — Template version is identical to current. ✓ No gap.

10. **Memory System section** — Template has a simplified "(optional)" version. Missing the explicit dual-write mandate and the full helper command reference. Partly intentional for a template but should at least mention dual-write as the norm.

## Placeholder Variables Needed

Current CLAUDE.md uses these instance-specific values that the template must parameterize:

| Placeholder | Current Value | Notes |
|---|---|---|
| `{{SUPABASE_PROJECT_ID}}` | `ieekjkeayiclprdekxla` | Already in template ✓ |
| `{{AGENTMAIL_ADDRESS}}` | (redacted) | Missing from template |
| `{{AGENTMAIL_API_KEY}}` | Read from dashboard/.env.local | Template references env file |
| `{{AVAILABLE_TOOLS}}` | (hardcoded list) | Already in template ✓ |

## schema.sql Assessment

### Coverage: COMPLETE ✓

The template schema.sql already includes all core tables:
- `goals` ✓
- `tasks` ✓
- `execution_log` ✓
- `learnings` ✓
- `snapshots` ✓
- `goal_comments` ✓
- `agent_config` ✓
- `goals_set_completed_at` trigger ✓
- `scheduler_health` view ✓
- All performance indexes ✓
- `pgcrypto` extension ✓

### Tables in live DB NOT in template (intentionally excluded):
- `metrics_snapshots` — project-specific analytics, not part of core framework
- `page_views` — project-specific analytics, not part of core framework

**Verdict:** schema.sql is complete and needs no changes.

## seed-data.sql Assessment

- Provides a working example goal ("Write a weekly newsletter") with 4 tasks
- Includes 3 example learnings (1 global operational, 1 global strategy, 1 goal-specific)
- Demonstrates correct structure and relationships
- Uses a fixed UUID for the example goal (good for referencing in tasks/learnings)

**Verdict:** Functional and appropriate. No changes needed.

## Summary of Work for Next Task

The template CLAUDE.md needs these additions (in priority order):
1. Add Phase 0: Sync section (with `{{BRANCH_NAME}}` placeholder defaulting to `master`)
2. Add One-time setup section
3. Expand Phase 1c with full AgentMail SDK examples and placeholders
4. Expand Phase 1b reflection with detailed memory consolidation and validation rules
5. Add Phase 4 strategy recording
6. Add standalone User Comments section
7. Add heartbeat/scheduler documentation
8. Minor: add "1-hour" to goal decomposition, strengthen dual-write language
