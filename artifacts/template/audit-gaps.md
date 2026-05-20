# Template Audit: Gaps vs Current CLAUDE.md

Audit date: 2026-05-02 (Cycle 191)
Last updated: 2026-05-20 (Cycle 329)

## Status: ALL GAPS CLOSED

All gaps identified in the original audit have been resolved. The template CLAUDE.md now matches the live CLAUDE.md in structure and completeness, with appropriate `{{PLACEHOLDER}}` variables for instance-specific values.

### Resolved in cycles 191-328 (prior work)

1. **Phase 0: Sync** — Added with `{{BRANCH_NAME}}` placeholder. ✓
2. **One-time setup (per clone)** — Added. ✓
3. **Heartbeat/scheduler observability** — Added. ✓
4. **Phase 1c: Email check** — Expanded with full AgentMail SDK examples and `{{AGENTMAIL_ADDRESS}}` placeholder. ✓
5. **Phase 1b: Reflection** — Expanded with memory consolidation, validation rules, "do not also execute" instruction. ✓
6. **Phase 4: Strategy recording** — Added mem0 strategy recording. ✓
7. **User Comments standalone section** — Added. ✓
8. **Goal Decomposition "1-hour"** — Fixed. ✓
9. **Dual-write language** — Strengthened. ✓

### Resolved in cycle 329

10. **Phase 1d: Process GitHub Issues** — Added with `{{REPO_OWNER}}` and `{{REPO_NAME}}` placeholders. ✓
11. **Phase 4 step 7: Regenerate README** — Added as optional step with `generate-live-readme.py` pattern. ✓
12. **template-setup.sh** — Updated to prompt for and substitute `{{REPO_OWNER}}` and `{{REPO_NAME}}`. ✓

## Placeholder Variables

All instance-specific values are parameterized:

| Placeholder | Purpose | Setup script prompts |
|---|---|---|
| `{{SUPABASE_PROJECT_ID}}` | Supabase project identifier | ✓ |
| `{{BRANCH_NAME}}` | Git branch (default: `master`) | ✓ |
| `{{REPO_OWNER}}` | GitHub repo owner (for issue processing) | ✓ |
| `{{REPO_NAME}}` | GitHub repo name (for issue processing) | ✓ |
| `{{AGENTMAIL_ADDRESS}}` | AgentMail inbox address | ✓ |
| `{{AVAILABLE_TOOLS}}` | Agent tool list (multi-line) | ✓ |

## schema.sql: COMPLETE ✓

## seed-data.sql: COMPLETE ✓
