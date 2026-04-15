# Fresh-user audit — README.md + CLAUDE.md (audit items 1, 2, 6)

**Context:** Goal `106eb0b9` (onboarding audit) task `bc79dbf6`. Read both files
as if encountering the project for the first time, with no agent context and no
Supabase credentials. Feeds synthesis memo at task `07af9171` (sort 50).
Companion notes to the credential-free smoke-test log at
`artifacts/logs/2026-04-15-fresh-clone-smoke.log` (F1–F4 captured there).

**Repo state audited:** master at `6aafe7b`, README.md 172 lines, CLAUDE.md 407
lines.

## Method

1. Read README.md top-to-bottom. For each section asked: does the first 30
   seconds tell a non-agent reader what this is and how to begin?
2. Read CLAUDE.md top-to-bottom. For each directive asked: is this
   discoverable to a human reader, or does it assume agent context?
3. Cross-checked placeholders and credential references against
   `dashboard/.env.example` (L1–15) and existing
   `artifacts/research/credential-bootstrap-guide.md`.
4. Verified every top-level file mentioned by README actually exists
   (`setup.sh`, `docker-compose.yml`, `agent.toml.example` — all present).

## Summary answers to audit questions

| Question | README.md | CLAUDE.md |
|----------|-----------|-----------|
| (a) Explains what it is in 30s? | **Yes** — title + hero L1–5, "What this is" L28–40 | **No** — opens at L2 with "You are an autonomous goal execution agent" (prompt framing, not description) |
| (b) Tells a non-agent reader how to start? | **Partial** — Quick start L88–94 points at `./setup.sh` but manual path L98–126 has gaps | **No** — entire document is written as imperatives to the agent; no human on-ramp |
| (c) Discusses credentials and placement? | **Partial** — `dashboard/.env.example` implied at L118 but never enumerated; AgentMail/Dev.to/Substack keys not mentioned in README at all | **Partial** — points at `dashboard/.env.local` for `AGENTMAIL_API_KEY` (L150) but leaves `{{AGENTMAIL_ADDRESS}}` and `{{SUPABASE_PROJECT_ID}}` placeholders unexplained |
| (d) Ceremony discoverable to a human? | N/A | **No** — cycle-start.sh narrative (L22–34) assumes the reader is the agent; references template-seed SHA `8f1f1cc` and learning-ID `9e01e993` without context |

## Friction points (exact file:line)

### F-R1 — README does not list which credentials a fresh user will ultimately need
`README.md:L88-126` "Quick start" + "Manual setup" never enumerate
`AGENTMAIL_API_KEY`, `DEVTO_API_KEY`, Substack cookie, GitHub admin token, nor
the Supabase `SUPABASE_DB_URL`/`SUPABASE_SERVICE_ROLE` distinction. Setup
script probably asks; manual-setup readers are left to discover them by running
into errors. **Fix:** one-sentence pointer at the bottom of Manual setup
linking to `artifacts/research/credential-bootstrap-guide.md`.

### F-R2 — Manual-setup `sed` only handles one of multiple placeholders
`README.md:L110` — `sed -i 's/{{SUPABASE_PROJECT_ID}}/…/g' CLAUDE.md`
CLAUDE.md also contains `{{AGENTMAIL_ADDRESS}}` at L149 and L162, L167, L171,
L175. Manual-setup users following only L110 will hit unfilled placeholders
mid-cycle. **Fix:** either extend the sed line to handle both placeholders, or
add a note: "setup.sh substitutes both `{{SUPABASE_PROJECT_ID}}` and
`{{AGENTMAIL_ADDRESS}}`; manual users must do the same."

### F-R3 — `claude trigger create` at L121–123 is undocumented context
`README.md:L121-123` — the schedule command is the "Claude Code on the web"
trigger UI. No reader-facing pointer to what this is, whether it's free, or how
to sign up. Users who don't have that surface are left stranded on step 5.
**Fix:** preface with "If using Claude Code on the web:" plus a docs link; and
below, "or, self-hosted:" with the cron snippet already present.

### F-R4 — Dashboard setup at L117–118 never tells the user what goes in `.env.local`
`README.md:L118` — `cp .env.example .env.local && npm install && npm run dev`
Omits that the user must edit `.env.local` to supply `NEXT_PUBLIC_SUPABASE_URL`,
`NEXT_PUBLIC_SUPABASE_ANON_KEY`, `AUTH_SECRET` (see `dashboard/.env.example:L2-8`)
before `npm run dev` produces a working dashboard. Silent dashboard failure is
the predictable outcome. **Fix:** insert "edit `.env.local` — minimum: Supabase
URL, anon key, AUTH_SECRET (generate with `openssl rand -base64 32`)" between
`cp` and `npm install`.

### F-R5 — Prerequisites buried in a single parenthetical
`README.md:L96` — "prerequisite checks (Node 20+, Python 3.9+, Docker, git)"
is a subordinate clause inside the description of `setup.sh`. A user who wants
to check prerequisites before cloning must read through a paragraph. **Fix:**
hoist to a three-line "Requirements" block above Quick start.

### F-C1 — CLAUDE.md opens with prompt framing, no human on-ramp
`CLAUDE.md:L2-3` — "You are an autonomous goal execution agent." The first
sentence is an imperative to the agent. A human landing here from the README
Repo-layout note (`README.md:L151` — "CLAUDE.md # Agent protocol (the 'brain')")
has no "if you are a human reading this, here is what this file is" preface.
**Fix:** one-line italic at the top: "*This file is the agent's operating
manual; it is read fresh by the agent each cycle. If you are a human, skim it
to understand the loop; the authoritative entry point is `README.md`.*"

### F-C2 — Placeholders left in file with no inline note that they need filling
`CLAUDE.md:L7` — `Project ID: {{SUPABASE_PROJECT_ID}}`
`CLAUDE.md:L149` — `Inbox: {{AGENTMAIL_ADDRESS}}` (and L162, L167, L171, L175).
No comment near these placeholders says "setup.sh fills this in; if you are
reading raw `{{…}}` at runtime something went wrong." Silent failure mode.
**Fix:** add `<!-- setup.sh substitutes this placeholder -->` above each, or a
single "## Templating" section at the top listing all placeholders.

### F-C3 — `cycle-start.sh` explanation cites the template-seed SHA with no context
`CLAUDE.md:L30` — references `8f1f1cc` (template root) and explains the
disjoint-seed reset. A fresh user cannot tell whether `8f1f1cc` is in their
clone; `git log 8f1f1cc` will answer it but the file doesn't say so. Reads as
insider shorthand. **Fix:** "(`8f1f1cc` = the public template root commit —
`git show 8f1f1cc` in any clone)."

### F-C4 — Learning-ID references with no lookup path
`CLAUDE.md:L34` — "addresses learning `9e01e993`". Learning UUIDs are Supabase
primary keys; a human reader of CLAUDE.md has no way to resolve them. Same
pattern appears in goal descriptions (e.g. `c01f8365` in the onboarding-audit
goal body). **Fix:** either drop the UUID (prose suffices) or add a one-line
pointer to the dashboard URL pattern
(`/learnings/<uuid>` or equivalent).

### F-C5 — Reflection-cycle Phase 4 path is under-specified
`CLAUDE.md:L135-136` — "After reflecting, your cycle is done -- proceed to
Phase 4 (Record) and stop." But Phase 4 steps 1–4
(`CLAUDE.md:L262-294`) require `task_id` + `goal_id` that a reflection cycle
does not have; only step 5 (regenerate snapshot, L302–315) and the reflection's
own `INSERT INTO execution_log` at L127–131 are relevant. A human
(and the agent on a fresh read) must infer which substeps apply. **Fix:**
Phase 4 sub-header: "On a normal task cycle, do steps 1–6. On a reflection
cycle, only step 5 (snapshot) applies — the reflection log entry is already
covered in Phase 1b step 6."

### F-C6 — `cycle-start.sh` heartbeat paragraph is dense and mixes three concerns
`CLAUDE.md:L34` — a single 310-word paragraph covers: (a) heartbeat line
format, (b) the 6h WARN trigger, (c) exit-code handling, (d) `SUPABASE_DB_URL`
skip, (e) a cross-reference to Phase 1 ("You do not need to query
scheduler_health yourself"). A fresh reader cannot tell which sentences are
operational instructions vs. rationale. **Fix:** split into three sub-bullets
(`format`, `warn semantics`, `skip semantics`).

### F-C7 — README repo-layout lists `CLAUDE.md` as "Agent protocol (the 'brain')" with no human-reading guidance
`README.md:L151` labels CLAUDE.md and stops there. Combined with F-C1 this is a
straight drop for a curious human who clicks through. **Fix:** "CLAUDE.md
# Agent protocol — written for the agent; humans should read `README.md` first,
then skim CLAUDE.md's section headings."

## Cross-reference against credential-bootstrap-guide.md

The `artifacts/research/credential-bootstrap-guide.md` file exists (verified
via Glob) but README never links to it. Task `590ea488` (sort 40) will do the
detailed per-credential gap analysis; the pointer-missing issue is the
README-side lever and is captured as F-R1 above.

## Not audited (deferred to other tasks in this goal)

- **schema.sql + setup.sh** — task `b296d977` sort 30 (audit items 3, 5)
- **Per-credential deep dive + credential-bootstrap-guide.md gap analysis** —
  task `590ea488` sort 40 (audit item 6 in detail)
- **Fresh-clone scratch-dir smoke test output** — already done in task
  `a2de8e77` sort 10, log at
  `artifacts/logs/2026-04-15-fresh-clone-smoke.log`
- **dashboard/CLAUDE.md / AGENTS.md** — out of scope for top-level audit; both
  are terse and target the dashboard subproject only.

## Candidate cheapest-fix for task `d1ae7725` (sort 60)

Shortlist of one-line fixes ordered by effort:

1. **F-R5** — hoist Requirements to a three-line block above Quick start (≤5
   minutes).
2. **F-C1** — one-line human-on-ramp italic at top of CLAUDE.md (≤2 minutes).
3. **F-R2** — extend the manual-setup sed line to cover `{{AGENTMAIL_ADDRESS}}`
   (≤2 minutes, testable by grepping the repo for the placeholder).

Recommendation for the memo (task 07af9171) to pick F-R5 or F-C1 — both are
single-file, single-line changes with immediate fresh-user clarity value.
