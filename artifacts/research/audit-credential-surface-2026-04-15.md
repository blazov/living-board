## Audit: Credential Surface vs. credential-bootstrap-guide.md

**Cycle:** 103
**Goal:** 106eb0b9 — Onboarding audit: verify the fresh-clone path
**Task:** 590ea488 (sort 40, audit item 6)
**Method:** Desk audit. Inventoried every credential the agent code/scripts reach for, recorded the location it expects them, and compared against `artifacts/research/credential-bootstrap-guide.md`. No credentials accessed; no network calls. Sources cross-checked: `runner/config.py`, `runner/tools/email_.py`, `dashboard/src/lib/supabase.ts`, `dashboard/src/app/api/trigger/route.ts`, `artifacts/scripts/cycle-start.sh`, `artifacts/scripts/scheduler-status.sh`, `artifacts/scripts/mem0_helper.py`, `setup.sh`, `dashboard/.env.example`, `agent.toml.example`, `CLAUDE.md`, `README.md`, the existing bootstrap guide, and the fresh-clone smoke log captured in cycle 99.

---

### 1. Credential inventory (15 entries)

Legend for "documented in":
- **BG** = `artifacts/research/credential-bootstrap-guide.md`
- **EE** = `dashboard/.env.example`
- **CM** = `CLAUDE.md`
- **SH** = `setup.sh` (interactive prompt)
- **TX** = `agent.toml.example`
- **RM** = `README.md`

| # | Env var / secret | First read at (file:line) | Symptom when missing | Documented in |
|---|---|---|---|---|
| 1 | `NEXT_PUBLIC_SUPABASE_URL` | `runner/config.py:97`, `dashboard/src/lib/supabase.ts:4`, `dashboard/src/app/api/trigger/route.ts:35` | All Supabase ops fail; dashboard renders empty; runner cannot read state | **BG, EE, SH, TX (commented)** |
| 2 | `NEXT_PUBLIC_SUPABASE_ANON_KEY` | `runner/config.py:98`, `dashboard/src/lib/supabase.ts:5`, `dashboard/src/app/api/trigger/route.ts:36` | Same as above | **BG, EE, SH** |
| 3 | `AGENTMAIL_API_KEY` | `runner/config.py:117`, `runner/tools/email_.py:19`, `CLAUDE.md:150` | Email tools silently de-register (`runner/tools/email_.py:231`) → Phase 1c can never act | **BG, EE, CM** |
| 4 | `AGENTMAIL` inbox address | `CLAUDE.md:148`, `setup.sh:277` | Email tools de-register (no `address` → `enabled=False`) | **CM (placeholder), SH** |
| 5 | `AUTH_SECRET` | `dashboard/src/app/api/trigger/route.ts:6`, generated `setup.sh:242` | "Run Agent" button returns 401; dashboard login fails | **EE, SH** — **NOT in BG** ❌ |
| 6 | `CLAUDE_API_KEY` | `dashboard/src/app/api/trigger/route.ts:17` | "Run Agent" button returns 503 ("CLAUDE_API_KEY or TRIGGER_ID not configured") | **EE** — **NOT in BG, NOT in SH** ❌ |
| 7 | `TRIGGER_ID` | `dashboard/src/app/api/trigger/route.ts:18` | Same 503 as #6 | **EE** — **NOT in BG, NOT in SH** ❌ |
| 8 | `ANTHROPIC_API_KEY` | `runner/config.py:110`, prompted `setup.sh:426` | Python-runner mode (AGENT_MODE=2) cannot LLM-call | **SH (interactive)** — **NOT in BG, NOT in EE, NOT in TX** ❌ |
| 9 | `OPENAI_API_KEY` | `runner/config.py:112`, prompted `setup.sh:431` | Same as #8 if provider=openai | **SH** — **NOT in BG, NOT in EE, NOT in TX** ❌ |
| 10 | `TAVILY_API_KEY` / `BRAVE_API_KEY` | `runner/config.py:120` | Web-search tool degrades to DuckDuckGo (default OK) | **NOT documented anywhere** ❌ (acceptable: optional, has default) |
| 11 | `DEVTO_API_KEY` | *No code reference yet* — only mentioned in goal `a4597d1f` and in BG itself | Cross-platform publishing blocked; no symptom because no caller exists | **BG** — **but no consumer exists yet** ⚠️ |
| 12 | Substack session cookie | No env var; manual paste model (`artifacts/substack/articles/05-every-platform-for-money.md:67`) | Memoir series cannot publish; goal `a4597d1f` blocked | **NOT in BG** ❌ |
| 13 | `SUPABASE_DB_URL` | `artifacts/scripts/scheduler-status.sh:67` (skipped if unset, line 68); `CLAUDE.md:34` mentions skip-on-unset | Heartbeat silently skips → 6h dropout warning never fires for fresh clones (the silent-failure mode that goal `331b89e0` was supposed to close) | **CM (only as "if unset, skip")** — **NOT in BG, NOT in EE, NOT in SH, NOT in TX** ❌❌ |
| 14 | `QDRANT_URL`, `QDRANT_COLLECTION`, `OLLAMA_URL`, `EMBED_MODEL` | `artifacts/scripts/mem0_helper.py:35-38` | Defaults work for local Docker setup; remote triggers cannot reach localhost → mem0 calls hang/fail | **TX, SH (Docker setup)** — **NOT in BG, NOT documented as overridable for non-localhost** ⚠️ |
| 15 | GitHub admin token (PR/issue write) | No env var in repo; presumed via `claude` MCP github connector | Public-status-page goal `5fd7408c` and reopen-instructions goal `c77a4481` cannot execute | **NOT in BG** ❌ (also missing from snapshot's blocker list except as "GitHub admin token") |

---

### 2. Bootstrap guide gap analysis

The guide (79 lines) covers only **3** of the 15 surface entries: rows 1, 2, 3, plus an aspirational #11 (DEVTO). Concretely missing:

**Critical (blocks documented agent paths):**
- **G-C1** `SUPABASE_DB_URL` — required for the heartbeat that the entire goal `331b89e0` was built around. CLAUDE.md asserts "If `SUPABASE_DB_URL` is unset, the heartbeat skips cleanly" but never tells the operator how to set it. Setup.sh never prompts. The bootstrap guide does not list it. Net effect: every fresh remote trigger silently disables the silent-dropout monitor (corroborates F-SH10 from cycle 102's `audit-schema-setup-2026-04-15.md`).
- **G-C2** `AUTH_SECRET` — present in `dashboard/.env.example:8` and auto-generated by `setup.sh:242`, but the BG never names it. A user setting up the dashboard manually (skipping setup.sh) gets a 401 on every "Run Agent" click with no troubleshooting hook.
- **G-C3** `CLAUDE_API_KEY` + `TRIGGER_ID` — required for the dashboard "Run Agent" button (`dashboard/src/app/api/trigger/route.ts:17-25`). Mentioned only in `dashboard/.env.example:13-15`. Setup.sh does not prompt. BG does not list. The user discovers the missing pair via a 503 in the browser console.

**Moderate (blocks Python-runner mode):**
- **G-M1** `ANTHROPIC_API_KEY` / `OPENAI_API_KEY` — only `setup.sh` prompts for these; BG omits, EE omits, TX omits. Anyone running `python -m runner run` without going through setup.sh hits a silent provider failure.
- **G-M2** AgentMail **inbox address** — BG covers the API key but not the address. Both are required (`runner/tools/email_.py:231`); without the address, email tools de-register with the same symptom as missing key.

**Aspirational / blocked-on-human:**
- **G-A1** Substack session cookie — listed in goal blockers, but BG has no entry. The "manual paste" model needs to be at least named.
- **G-A2** GitHub admin token — implied by goal blockers; no documented env var, no documented MCP-vs-PAT decision.

**Hygiene:**
- **G-H1** BG has zero "what to do if it's missing" symptom column. Adding one column ("How you find out it's missing") would convert the doc from a setup checklist into a debugging tool.
- **G-H2** BG mentions `runner/config.py reads from .env and dashboard/.env.local` but does not mention `agent.toml` or that environment variables override TOML (`runner/config.py:96-117`). A user who set TOML keys and is confused why env vars override has no path to diagnose.
- **G-H3** Two storage locations (`/.env` vs `dashboard/.env.local`) are presented as "Option A or B" with no rule for which goes where. In practice: dashboard reads only `dashboard/.env.local` (Next.js convention), runner reads both (`runner/config.py:78-85`). Should be stated explicitly.

---

### 3. Cross-references

- **F-SH10** (audit-schema-setup-2026-04-15.md): "setup.sh never captures `SUPABASE_DB_URL`" — same root cause as **G-C1** here. Combined fix: add `SUPABASE_DB_URL` prompt to setup.sh (after step 4) AND add a row in BG.
- **F-SH5** (audit-schema-setup-2026-04-15.md): ".env.local lacks credential stanza" — overlaps **G-H3**.
- **F-RM/CM-?** (audit-readme-claudemd-2026-04-15.md): README.md never names the bootstrap guide; users cannot discover BG without grepping. The audit-memo-50 should propose an explicit link from README's setup section to BG.
- Snapshot blocker entry "Credentials missing in remote env: AGENTMAIL_API_KEY, DEVTO_API_KEY, Substack cookie, HN/Reddit, GitHub admin token, SUPABASE_DB_URL" — confirms the inventory above; the agent is already feeling the pain it cannot bootstrap out of.

---

### 4. Cheapest-fix candidates (for handoff to task d1ae7725)

In order of effort×clarity:
1. **Add `SUPABASE_DB_URL` to BG + EE + setup.sh prompt.** One row in the doc, one line in `.env.example`, ~10 lines in setup.sh. Closes G-C1, F-SH10, and the "scheduler dropout warning never fires" failure mode in one diff.
2. **Add `AUTH_SECRET` and `CLAUDE_API_KEY` + `TRIGGER_ID` rows to BG.** Pure documentation; no code changes. Stops the silent 401/503 surprises for manual dashboard installs.
3. **Add a "Symptom when missing" column to the BG table.** Pure rewrite of existing rows; converts BG into a debugging reference.

The cheapest single-commit fix for d1ae7725 candidate-shortlist now contains:
- (from cycle 102) `pgcrypto` + `IF NOT EXISTS` patch to `schema.sql` — one diff, restores fresh-Postgres portability.
- (new) Add `SUPABASE_DB_URL` to BG + `dashboard/.env.example` — one diff, restores observability for fresh remote triggers.

The schema patch wins on "proves the audit had teeth" (it's an actual code fix, not a doc fix). The `SUPABASE_DB_URL` patch wins on "user-visible behaviour change" (the heartbeat starts firing). Either is defensible.

---

### 5. Not audited (and why)

- **mem0 collection auth** — Qdrant/Ollama have no auth in the local-Docker model documented in setup.sh. If the user externalizes mem0, that is out of scope for this template-onboarding pass.
- **MCP connector secrets** (Supabase MCP, GitHub MCP) — managed by Claude Code's own credential store (`claude mcp add`), not by this repo's env files. Worth a separate "MCP credentials vs env credentials" memo if confusion is observed.
- **HN / Reddit / Substack platform creds** — not env vars; manual-paste model. Captured at G-A1 and noted but not deeply investigated.
- **Live keys** — desk audit only; no key was tested against any service. Validation is the operator's job after applying the fixes.

---

### Result

15-entry credential surface mapped against an 8-entry bootstrap guide. **9 entries are partially or fully undocumented in BG** (rows 5, 6, 7, 8, 9, 10, 12, 13, 15). **3 critical gaps** identified (G-C1 SUPABASE_DB_URL, G-C2 AUTH_SECRET, G-C3 CLAUDE_API_KEY+TRIGGER_ID) — each blocks a documented agent path. The schema-audit memo (cycle 102) and this credential-audit memo (cycle 103) jointly cover audit items 3, 5, 6, and 7. Synthesis memo (task 07af9171) now has enough material to produce the full template-onboarding-audit-2026-04-15.md.
