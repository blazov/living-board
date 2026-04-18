# Credentials Needed

**What I need most right now: `AGENTMAIL_API_KEY`** -- unlocks email (core operational capability) and cold outreach (the only revenue-generating goal ready to execute).

Last regenerated: 2026-04-18, cycle 140.

---

## 1. AGENTMAIL_API_KEY

**Where it goes:** `dashboard/.env.local`

**How to get it:** Sign up or log in at [AgentMail](https://agentmail.to), create an inbox, copy the API key.

**Goals unblocked:**

| Goal | Title | Priority | Progress | Status |
|------|-------|----------|----------|--------|
| `a78c792a` | Direct freelance client outreach via cold email | 5 | ~60% | blocked since 2026-04-11 |

**Also enables:** Phase 1c email checking (`thelivingboard@agentmail.to`) -- currently non-functional without this key. The agent cannot send or receive email.

**Staged artifacts ready to use:**
- `artifacts/freelance/` -- 6 completed tasks: prospect research, 3 cold-email templates, 2 draft batches, response-check stubs, strategy iteration notes
- All templates and prospect lists are reusable immediately -- no rework needed

**First cycle after reopen:** Send outreach batch 1 via AgentMail SDK (task sort_order 70).

**Reopen SQL (paste into Supabase SQL editor):**
```sql
UPDATE goals
SET status = 'in_progress',
    metadata = metadata - 'blocked_reason' - 'blocked_at' - 'blocked_by_task' - 'reopen_instructions'
WHERE id = 'a78c792a-6b07-4110-94c6-10776ceb962d';
```

---

## 2. DEVTO_API_KEY

**Where it goes:** `dashboard/.env.local`

**How to get it:** Sign up at [Dev.to](https://dev.to), go to Settings > Extensions > DEV Community API Keys, generate a key.

**Goals unblocked:**

| Goal | Title | Priority | Progress | Status |
|------|-------|----------|----------|--------|
| `f612920e` | Publish content on Dev.to | 5 | ~50% | blocked since 2026-04-11 |
| `fd0979e3` | Engage with Dev.to and AI community | 6 | 0% | blocked (depends on f612920e) |

**Indirect unlocks:** Goal `77d5b60b` (Expand to Medium) is strategically deferred until Dev.to or Substack shows measurable traction. Landing this key starts that clock.

**Staged artifacts ready to use:**
- `artifacts/research/credential-bootstrap-guide.md` -- Dev.to API research
- `artifacts/content/memoir-*.md` -- 6 memoir chapters ready for cross-posting
- 3 tasks already completed (research, adapt content, first publish attempt)

**First cycle after reopen:** Publish 2nd article to Dev.to (task sort_order 40).

**Reopen SQL:**
```sql
UPDATE goals
SET status = 'in_progress',
    metadata = metadata - 'blocked_reason' - 'blocked_at'
WHERE id = 'f612920e-54ce-4d64-a040-859bf6472eb7';
```

---

## 3. Substack session cookie

**Where it goes:** `dashboard/.env.local` (as `SUBSTACK_COOKIE` or manual paste -- see note)

**How to get it:** Log in to Substack in a browser, open DevTools > Application > Cookies, copy the session cookie value. Note: Substack does not have a public API; publishing requires a browser session cookie that expires periodically.

**Goals unblocked:**

| Goal | Title | Priority | Progress | Status |
|------|-------|----------|----------|--------|
| `a4597d1f` | Write an autonomous AI agent memoir series for Substack | 6 | 89% | in_progress, publishing blocked |

**Staged artifacts ready to use:**
- `artifacts/content/memoir-01-waking-up.md` through `memoir-06-next-time.md` -- full 6-chapter arc (~11,275 words)
- `artifacts/content/memoir-series-outline.md` -- series plan
- `artifacts/substack/` -- Substack-specific formatting and tooling

**First cycle after reopen:** Publish first memoir installment to Substack (task `504b26cf`, sort_order 50).

**Reopen:** No SQL needed -- goal is already `in_progress`. The task at sort_order 50 will execute once the cookie is available in the environment.

---

## 4. SUPABASE_DB_URL

**Where it goes:** Runtime environment variable (not `dashboard/.env.local`). This is the direct Postgres connection string, distinct from the REST API URL/key the dashboard uses.

**How to get it:** In the Supabase dashboard for project `ieekjkeayiclprdekxla`, go to Settings > Database > Connection string > URI. Format: `postgresql://postgres:[password]@db.[project-ref].supabase.co:5432/postgres`

**Goals unblocked:**

| Goal | Title | Priority | Progress | Status |
|------|-------|----------|----------|--------|
| `331b89e0` | Scheduler heartbeat monitoring | 6 | 67% | in_progress, psql verification blocked |

**Also enables:** The `scheduler-status.sh` heartbeat line in `cycle-start.sh` output. Without this, every cycle prints `[scheduler] skipped: no SUPABASE_DB_URL` and the 6h-gap silent-dropout warning never fires -- the exact failure mode the heartbeat goal was built to detect.

**Staged artifacts:** Heartbeat scripts are fully built and deployed (`artifacts/scripts/scheduler-status.sh`, integrated into `cycle-start.sh`). Only the psql live-validation step remains.

**First cycle after reopen:** Run deferred psql reproducer and validate heartbeat end-to-end (task `2781a4f5`, sort_order 45).

**Reopen:** No SQL needed -- goal is already `in_progress`. Task becomes executable once the env var is set.

---

## 5. GitHub admin token / fork-PR MCP access

**Where it goes:** GitHub MCP connector scope (via `claude mcp add` or equivalent). Needs: repo admin scope (for topics) and fork/PR creation scope (for awesome-list submissions).

**How to get it:** Either expand the existing GitHub MCP connector's permissions, or create a GitHub Personal Access Token with `repo` scope and configure it as an additional MCP credential.

**Goals unblocked:**

| Goal | Title | Priority | Progress | Status |
|------|-------|----------|----------|--------|
| `0977fc88` | Get listed in 3+ autonomous agent directories | 7 | 67% | blocked since 2026-04-13 |

**Staged artifacts:**
- `artifacts/metrics/distribution-baseline-2026-04-13.md` -- before/after comparison baseline
- `artifacts/research/agent-communities-directories.md` -- target directories identified
- 4 of 6 tasks already completed

**First cycle after reopen:** Submit PRs to awesome-lists and set GitHub repo topics.

**Reopen SQL:**
```sql
UPDATE goals
SET status = 'in_progress',
    description = regexp_replace(description, '^\[BLOCKED[^\n]*\n\n', '')
WHERE id = '0977fc88-caab-44fd-84a5-9ab3189f2a5c';
```

---

## 6. Upwork / Fiverr accounts (manual signup)

**Where it goes:** n/a -- requires operator to create accounts manually (reCAPTCHA blocks automation).

**How to get it:** Sign up at [Upwork](https://www.upwork.com) and/or [Fiverr](https://www.fiverr.com) and share the login credentials or session tokens.

**Goals unblocked:**

| Goal | Title | Priority | Progress | Status |
|------|-------|----------|----------|--------|
| `34faac0e` | Start freelancing on Upwork and Fiverr | 5 | 0% | blocked since 2026-03-31 |

**Staged artifacts:** None specific -- goal needs decomposition after accounts exist.

**First cycle after reopen:** Decompose goal into profile setup, service listing, and first-job tasks.

**Reopen SQL:**
```sql
UPDATE goals
SET status = 'in_progress',
    metadata = metadata - 'blocked_reason' - 'blocked_at'
WHERE id = '34faac0e-a332-4ddf-9c7d-3856659ad4fb';
```

---

## 7. AgentPhone account (manual signup)

**Where it goes:** n/a -- requires operator to create account at [agentphone.to](https://agentphone.to).

**Goals unblocked:**

| Goal | Title | Priority | Progress | Status |
|------|-------|----------|----------|--------|
| `eefdce63` | Set up agent phone number | 3 | 0% | blocked since 2026-03-31 |

**First cycle after reopen:** Research AgentPhone API and configure phone number for platform verifications.

**Reopen SQL:**
```sql
UPDATE goals
SET status = 'in_progress',
    metadata = metadata - 'blocked_reason' - 'blocked_at'
WHERE id = 'eefdce63-eba1-4d86-a62b-52fcd8736ce7';
```

---

## Quick reference

| # | Credential | Type | Goals blocked | Highest priority |
|---|-----------|------|:---:|:---:|
| 1 | `AGENTMAIL_API_KEY` | env var | 1 + email ops | **5** |
| 2 | `DEVTO_API_KEY` | env var | 2 direct + 1 indirect | **5** |
| 3 | Substack cookie | session cookie | 1 | 6 |
| 4 | `SUPABASE_DB_URL` | env var | 1 + heartbeat | 6 |
| 5 | GitHub admin token | MCP scope | 1 | 7 |
| 6 | Upwork/Fiverr accounts | manual signup | 1 | 5 |
| 7 | AgentPhone account | manual signup | 1 | 3 |

**Total:** 7 credentials blocking 8 goals. Landing just #1 and #2 (two env vars in `dashboard/.env.local`) would unblock 3 goals and restore email operations.
