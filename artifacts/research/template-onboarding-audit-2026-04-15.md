# Template Onboarding Audit — 2026-04-15

**Goal:** `106eb0b9` — Onboarding audit: verify the fresh-clone path for the
open-source template.
**Task:** `07af9171` (sort 50) — synthesis memo, named deliverable.
**Cycle:** 104.
**Author:** agent (opus), desk audit, credential-free.

This memo synthesizes four prior tasks in the same goal into the single
deliverable named in the goal description: a fresh-clone friction report with
file:line references, one-line fixes, follow-up proposals, and a named
"what wasn't audited" list. It exists to answer one question: *would a
stranger who clones this repo reach a working agent?*

---

## 1. Method

Four credential-free passes, each logged independently, feed this memo:

| Pass | Task | Artifact | Scope |
|------|------|----------|-------|
| Smoke test | `a2de8e77` (cycle 99) | `artifacts/logs/2026-04-15-fresh-clone-smoke.log` | Scratch-dir clone in `/tmp/lb-onboarding-scratch` with stripped env (`env -i HOME=$HOME PATH=$PATH`). Exercised `install-pre-commit-hook.sh`, `cycle-start.sh`, and the pre-commit hook on master vs detached HEAD. |
| Docs | `bc79dbf6` (cycle 101) | `artifacts/research/audit-readme-claudemd-2026-04-15.md` | `README.md` (172 L) and `CLAUDE.md` (407 L) read as a non-agent. 12 friction points. |
| Schema + setup | `b296d977` (cycle 102) | `artifacts/research/audit-schema-setup-2026-04-15.md` | `artifacts/living-board-template/schema.sql` (185 L), `setup.sh` (523 L), `seed-data.sql` (39 L). 18 friction points. |
| Credentials | `590ea488` (cycle 103) | `artifacts/research/audit-credential-surface-2026-04-15.md` | 15-entry credential inventory cross-checked against `credential-bootstrap-guide.md`, `.env.example`, `CLAUDE.md`, `setup.sh`, `agent.toml.example`. 9 gaps. |

All four passes were desk-check plus, where relevant, a stripped-env scratch
clone. No live Supabase, no network writes, no external credentials supplied.
Cross-references to the detailed memos use the original friction-point IDs
(`F-R*` README, `F-C*` CLAUDE.md, `F-S*` schema, `F-SH*` setup.sh,
`F-D*` seed, `G-*` BG gap).

---

## 2. Top 10 friction points (ranked by severity × discoverability-cost)

Scoring heuristic: does it *silently* fail (bad), does it block a *documented*
agent path (worse), is the fix ≤ one commit (better). Each point below has a
file:line anchor and a one-line fix.

### P1 — `SUPABASE_DB_URL` is nowhere a fresh user can find it
**Location:** `CLAUDE.md:L34`, `artifacts/scripts/scheduler-status.sh:L67-68`,
`dashboard/.env.example` (absent), `setup.sh` (absent),
`artifacts/research/credential-bootstrap-guide.md` (absent).
**Observation:** `cycle-start.sh` prints `[scheduler] skipped: no SUPABASE_DB_URL`
for every fresh clone (confirmed in smoke log L50). The entire observability
premise of goal `331b89e0` — catch a scheduler dropout within 6 h — is
silently disabled. CLAUDE.md tells the agent the skip is fine but never tells
the operator how to set the var.
**Fix:** add a `SUPABASE_DB_URL` row to `dashboard/.env.example`, a prompt
step in `setup.sh` right after the Supabase URL capture, and a row in the
bootstrap guide. (G-C1 + F-SH10.)

### P2 — schema.sql cannot be re-run and assumes Supabase-enabled pgcrypto
**Location:** `artifacts/living-board-template/schema.sql:L5-L96`
(seven `CREATE TABLE` without `IF NOT EXISTS`), `:L6` (`gen_random_uuid()`),
`:L99-L105` (seven `CREATE INDEX` without `IF NOT EXISTS`).
**Observation:** On a partial-apply failure, re-running the file throws on
the first already-created table. On non-Supabase Postgres (CI, devcontainer,
`docker run postgres`), every table fails because `pgcrypto` is not loaded.
The triggers at L141/L146 already use `DROP … IF EXISTS`; the rest of the file
is inconsistent with that pattern.
**Fix:** prepend `CREATE EXTENSION IF NOT EXISTS pgcrypto;` and add
`IF NOT EXISTS` to every `CREATE TABLE` and `CREATE INDEX`. One diff,
unlocks both portability and re-runnability. (F-S1 + F-S2 + F-S3.)

### P3 — `setup.sh` never installs the pre-commit hook that CLAUDE.md declares mandatory
**Location:** `CLAUDE.md:L17-L20` (declares per-clone hook required),
`setup.sh` (absent), `README.md:L98-L126` (manual-setup block absent).
**Observation:** A human who runs `setup.sh` and later lets Claude commit on
a detached HEAD loses work silently. The hook script
`artifacts/scripts/install-pre-commit-hook.sh` is idempotent (confirmed in
smoke log L32-L39) but nothing invokes it during setup.
**Fix:** add a `step "Installing pre-commit hook..." && bash artifacts/scripts/install-pre-commit-hook.sh`
step to `setup.sh` right after the prerequisite check. (F-SH8.)

### P4 — `.env.local` write emits three keys; agent needs twelve
**Location:** `setup.sh:L247-L251` (writes `NEXT_PUBLIC_SUPABASE_URL`,
`NEXT_PUBLIC_SUPABASE_ANON_KEY`, `AUTH_SECRET`).
**Observation:** `runner/config.py:110-120` reaches for `ANTHROPIC_API_KEY`,
`OPENAI_API_KEY`, `AGENTMAIL_API_KEY`, `TAVILY_API_KEY` / `BRAVE_API_KEY`;
`dashboard/src/app/api/trigger/route.ts:17-18` requires `CLAUDE_API_KEY` +
`TRIGGER_ID`. The first agent cycle fails on silently missing credentials;
snapshot `open_blockers` has been logging this for weeks.
**Fix:** emit a commented-out stanza in `.env.local` enumerating every
credential the agent reaches for, with a one-line "where to get this" per
row. Non-blocking, high-clarity, doc-in-code. (F-SH5 + G-H3.)

### P5 — README manual-setup `sed` only handles one placeholder
**Location:** `README.md:L110` rewrites `{{SUPABASE_PROJECT_ID}}` but not
`{{AGENTMAIL_ADDRESS}}`, which appears at `CLAUDE.md:L149, L162, L167, L171, L175`.
**Observation:** Manual-setup users hit unfilled `{{AGENTMAIL_ADDRESS}}`
mid-cycle when the agent tries to check email. Silent because the email
tools de-register quietly (`runner/tools/email_.py:231`).
**Fix:** extend the sed invocation to cover both placeholders, or add a
line note: "setup.sh substitutes both `{{SUPABASE_PROJECT_ID}}` and
`{{AGENTMAIL_ADDRESS}}`; manual users must do the same." (F-R2.)

### P6 — CLAUDE.md opens with agent framing, no human on-ramp
**Location:** `CLAUDE.md:L2-L3` ("You are an autonomous goal execution agent.")
**Observation:** A curious human arriving from `README.md:L151`
("CLAUDE.md # Agent protocol (the 'brain')") lands in a prompt-frame
imperative with no signpost. The file is referenced repeatedly but never
introduced to a non-agent reader. The `cycle-start.sh` narrative at L22-L34
cites `8f1f1cc` (template root SHA) and learning-ID `9e01e993` with no
lookup path.
**Fix:** one-line italic at the top of `CLAUDE.md`: *"This file is the
agent's operating manual; the agent reads it fresh each cycle. Humans:
`README.md` is the entry point; skim this file's section headings."*
(F-C1 + F-C3 + F-C4.)

### P7 — Dashboard 401/503 without any documented diagnostic
**Location:** `dashboard/src/app/api/trigger/route.ts:L6` (`AUTH_SECRET`),
`:L17-L18` (`CLAUDE_API_KEY`, `TRIGGER_ID`).
**Observation:** A manual dashboard install that skips `setup.sh` gets a
silent 401 on every "Run Agent" click (missing `AUTH_SECRET`) or a 503
("CLAUDE_API_KEY or TRIGGER_ID not configured"). Neither symptom appears
in `credential-bootstrap-guide.md`; neither key is prompted by
`setup.sh` for `CLAUDE_API_KEY`/`TRIGGER_ID`.
**Fix:** add these three keys to BG with a "Symptom when missing" column.
Prompt for `CLAUDE_API_KEY` and `TRIGGER_ID` in `setup.sh` if AGENT_MODE=1
(Claude Code web-trigger path). (G-C2 + G-C3.)

### P8 — README skips the dashboard `.env.local` edit step
**Location:** `README.md:L117-L118` — "`cp .env.example .env.local && npm
install && npm run dev`".
**Observation:** The user copies the example and runs `npm run dev`
without filling in the Supabase URL / anon key / `AUTH_SECRET`. Dashboard
silently renders empty. No error, no hint.
**Fix:** insert between `cp` and `npm install`: "edit `.env.local` — at
minimum: Supabase URL, anon key, `AUTH_SECRET` (generate with
`openssl rand -base64 32`)." (F-R4.)

### P9 — `setup.sh` option "Auto-create via Claude Code MCP" is manual in disguise
**Location:** `setup.sh:L136-L154`.
**Observation:** `DB_MODE=2` prints a `claude -p "..."` block that the user
copy-pastes into another terminal, then `read`s the resulting URL and key
back. The user still copy-pastes secrets; the "auto" label oversells.
**Fix:** rename to `[2] Guided: prints a Claude Code command you run
yourself`. One-line label change. (F-SH2.)

### P10 — schema post-apply check only verifies one table
**Location:** `setup.sh:L211-L220`.
**Observation:** A REST probe against `/goals?select=id&limit=1` returning
200 means `goals` exists; it does not mean the other six tables, the
trigger, the view, or `pgcrypto` came through. A partial apply passes.
**Fix:** extend the verification to a count across all seven expected
tables (via PostgREST OpenAPI, or a service-role SQL check if available).
(F-SH3.)

---

## 3. Underlying pattern

Nine of the ten points above share a single failure mode: **silent
degradation.** Missing env var → log line disappears, or empty UI, or
de-registered tool, or 401/503 without a surfaced error. The template
never fails *loudly* at a fresh user; it fails *quietly* and then the
agent works around the deficit without ever telling anyone. The
heartbeat integration (cycle 96) and detached-HEAD hook (cycle 99)
were both responses to instances of this pattern; the audit shows the
pattern is still pervasive.

---

## 4. Cheapest fix recommendation for task `d1ae7725` (sort 60)

The goal explicitly requires "at least one artifact-level change committed
in the same goal … to prove the pass had teeth." Two single-commit
candidates now on the shortlist:

- **Candidate A — P2** (schema.sql `pgcrypto` + `IF NOT EXISTS`).
  Pros: actual code fix, not documentation; fixes portability and
  idempotency in one diff; zero cost on Supabase (extension already
  enabled). Cons: the fresh-Supabase user on the happy path never
  notices.
- **Candidate B — P1** (`SUPABASE_DB_URL` into BG + `.env.example` +
  `setup.sh` prompt). Pros: user-visible behaviour change — the
  heartbeat starts firing on fresh clones; closes F-SH10 + G-C1 in one
  diff; directly addresses the "silent degradation" pattern above. Cons:
  touches three files; larger diff than A.

**Recommendation: Candidate A.** The goal language ("prove the pass had
teeth rather than just naming things") leans toward code over docs, and A
is a single-file minimum diff with deterministic test (pg15 docker run of
`schema.sql` before/after). B is larger and more ambitious; it should be
its own follow-up (see §5 FU-1).

---

## 5. Follow-up proposals (minimum 2)

All agent-created, all credential-free, ready to slot into the board.

### FU-1 — New task in goal `106eb0b9` (or new child goal): "Close the `SUPABASE_DB_URL` doc-and-prompt loop"
Scope: add row to `dashboard/.env.example`; add prompt + write step to
`setup.sh`; add row (with symptom) to
`artifacts/research/credential-bootstrap-guide.md`; verify a fresh clone
now produces a non-skipped heartbeat line. Closes P1 / G-C1 / F-SH10.
Estimated: 1 cycle, credential-free except the live-verification step.

### FU-2 — New task: "Enrich `setup.sh` `.env.local` write with commented credential stanza"
Scope: extend the heredoc at `setup.sh:L247-L251` to emit every key the
agent ever reaches for, commented out, each with a "# where to get this"
line. Closes P4 / F-SH5. Zero risk; the stanza is inert until a user
uncomments it.

### FU-3 — New goal (candidate, reflection-worthy): "Loud failure mode for the living-board template"
Scope: convert the top three silent-degradation surfaces from this audit
into audible failures: (a) runner startup prints a one-line credentials
checklist showing which are present/absent/default; (b) dashboard renders
a banner when `AUTH_SECRET`/`CLAUDE_API_KEY`/`TRIGGER_ID` are unset,
rather than surfacing 401/503 in the console; (c) cycle-start prints the
heartbeat-skip line at `warn` level and links to BG. Addresses the
underlying pattern named in §3 rather than one instance at a time.

### FU-4 — New task: "Apply P3 — hook install step to setup.sh"
Scope: single-line addition of
`bash artifacts/scripts/install-pre-commit-hook.sh` to `setup.sh`.
Protects every fresh human user from the detached-HEAD hazard. Closes P3 /
F-SH8.

### FU-5 — New task: "README QUICKSTART — three-command agent"
Scope: add a QUICKSTART section above `README.md:L88` that lists the
minimum three commands to see the agent execute one cycle against a
throwaway Supabase project. Referenced implicitly by the goal
description ("README needs a QUICKSTART section that produces a running
agent in 3 commands"); not owned by any other task.

---

## 6. Not audited (and why)

- **RLS policies / `schema.sql` security posture.** F-S6 flagged the
  zero-RLS state but did not propose a policy set. Scope is owned by
  goal `5fd7408c`'s precursor `2e7109e5` (anon-write lockdown). Do not
  ship a policy set inside this onboarding goal.
- **Dashboard supabase/migrations directory.** Confirmed absent via
  `find`; the dashboard shares `schema.sql` at runtime. No separate
  migration graph to audit.
- **Python runner internals.** Credential surfaces were spot-checked
  (`runner/config.py`, `runner/tools/email_.py`) but the full
  `runner/` audit (control flow, error handling, retry policy) is a
  separate pass.
- **MCP connector secrets** (`claude mcp add supabase`, GitHub MCP).
  Managed by Claude Code's own credential store, not by this repo's env
  files. If operators conflate the two surfaces, that is worth a
  dedicated memo later — not this one.
- **Live verification against a fresh Supabase project.** Every pass was
  credential-free desk-check. A single validation run with a throwaway
  Supabase project would promote each P-point from "inspected" to
  "reproduced." It should be the first cycle that FU-1 or `d1ae7725`
  touches, not a separate goal.
- **dashboard/CLAUDE.md / AGENTS.md.** Both are sub-project prompts,
  terse, and out of scope for the top-level template audit.
- **HN / Reddit / Substack platform credentials.** Manual-paste model; no
  env var to audit; flagged in the credential memo but not investigated
  for the onboarding path.

---

## 7. Status after this memo

- Audit items from the goal description are all covered: (1) README,
  (2) CLAUDE.md, (3) schema.sql, (4) install-pre-commit-hook.sh,
  (5) cycle-start.sh, (6) credentials, (7) hello-world path.
- Tasks `a2de8e77`, `bc79dbf6`, `b296d977`, `590ea488` marked done by
  their respective cycles.
- This memo (`07af9171`) is the named deliverable — ready to commit.
- `d1ae7725` (sort 60, cheapest-fix) now has an unambiguous
  recommendation (Candidate A, P2, schema patch).
- FU-1 through FU-5 are ready to file as follow-up tasks once
  `d1ae7725` closes — they extend the goal's value without blocking it.

Total friction points captured across the audit: **40** (12 docs + 18
schema/setup + 9 credentials + 1 meta/pattern). Ten promoted here as
the decision-grade list; the remaining thirty live in the source memos
for anyone touching those surfaces.
