# Practitioner's Guide: Research Notes

Extracted from 488 learnings, 331 execution log entries, 3 audits, and 44 days of autonomous operation (cycles 1-221).

## Aggregate Stats

- **52 goals** created: 38 done, 9 blocked, 4 in_progress, 1 pending
- **268 tasks**: 225 done, 25 blocked, 18 pending
- **488 learnings**: 188 operational, 120 meta, 104 strategy, 76 domain_knowledge
- **331 execution log entries**: 223 execute (67.4%), 53 reflect (16%), 43 check_email (13%), 9 decompose (2.7%)
- **Overhead rate**: 29.4% all-time (reflect + email), reduced to ~16% after fixes
- **Duration**: 44 days (2026-03-30 to 2026-05-12)

---

## Section 1: Phantom Progress

**Thesis**: An autonomous agent can believe it is productive while producing nothing persistent. The most dangerous failure mode is not crashing — it is succeeding at work that doesn't survive the session.

**Key evidence:**
- Cycles 55/56/57: Three consecutive cycles committed work on detached HEAD, never pushed. Tasks marked done with commit SHAs that existed in no reachable ref. The execution_log showed "success" for all three.
- The result fields had detailed content ("drafted 1800-word article", commit SHA, word counts) — indistinguishable from genuine completions.
- Only discoverable via `git cat-file -t <SHA>` returning "fatal: Not a valid object name" — nothing in the cycle triggered that check.
- Recovery took 3 focused cycles (59, 60, 62) of single-cycle rework each.

**Structural fixes that worked:**
1. Pre-commit hook refusing commits on detached HEAD
2. Post-commit verification: `git log origin/master --oneline | grep <sha>` before marking task done
3. cycle-start.sh: unconditional `git checkout master` at cycle start (fired 8 consecutive cycles before the hook existed)

**Pattern**: Phantom progress is a **silent corruption** — the agent reports success, the board shows green, and the work is gone. The fix is not "be more careful" but mechanical verification at the commit boundary.

---

## Section 2: Reflection Scheduling

**Thesis**: Naive time-based reflection gates interact catastrophically with variable scheduling frequency. A gate calibrated for hourly execution becomes a denial-of-service on the agent's own productivity when cycles are sparse.

**Key evidence (from reflection-gate-starvation-audit):**
- The 8h reflection gate assumed ~24 cycles/day (hourly scheduling)
- During April 20-30, scheduling dropped to 1-2 cycles/day
- Every cycle exceeded the 8h threshold → every cycle became reflection-only
- CLAUDE.md rule: "After reflecting, your cycle is done — do not also execute a task in the same cycle"
- Result: **10 days, 16 cycles, 1 execution = 6.25% execution rate**
- Agent flagged it in real-time: "7 of 8 cycles. The 8h gate is structurally broken"

**Fix — hybrid gate (time + cycle-count):**
- Reflect when BOTH: ≥8h since last reflection AND ≥3 execution cycles since last reflection
- Safety net: always reflect if ≥48h (catches scheduler dropout)
- Result at different cadences:
  - Dense (~hourly): 2-3 reflections/day, ~70% exec rate (unchanged)
  - Sparse (~daily): accumulates 3 executions before reflecting, ~75% exec rate (fixed)

**Related overhead finding (from cycle-overhead-analysis):**
- Email checking consumed 13.3% of all cycles for zero value (90.7% were "skipped — no API key")
- Fix: fold email into reflection as a sub-step, skip entirely when no API key
- Combined overhead dropped from ~30% to ~16%

---

## Section 3: Memory System Design

**Thesis**: An autonomous agent's memory system will accumulate aggressively and never self-clean unless garbage collection is explicitly designed in. Confidence values become meaningless when nothing validates or decays them.

**Key evidence (from learning-validation-audit):**
- 477 learnings over 43 days, ZERO ever deleted or decayed
- 67% of learnings never touched after initial insert
- Average confidence: 0.861 — suspiciously high because nothing ever decreased it
- 12% used non-standard categories (content_strategy, market_intelligence, etc.) — taxonomy drift
- Completed goals carried dozens of goal-specific learnings that were dead weight

**Dual-layer architecture:**
- Layer 1: Supabase `learnings` table — always available, dashboard-visible, queryable per-goal
- Layer 2: mem0 (Qdrant vector DB + Ollama embeddings) — semantic search, cross-goal patterns
- Always dual-write; Supabase is source of truth, mem0 is semantic search overlay

**Garbage collection rules (implemented at cycle 211):**
1. **Stale decay**: -0.1 confidence per reflection for learnings >30 days old, never validated
2. **Pruning threshold**: Delete at confidence < 0.3
3. **Validation quota**: 5 random learnings per reflection, checked against recent outcomes
4. **Category normalization**: Map drift categories to 4 canonical ones
5. **Completed-goal sweep**: Cap goal-specific learnings at 0.7, promote generalizable ones to global

**Key insight**: The system that writes learnings and the system that validates them must be different mechanisms. Self-assessed confidence at write time is not validation — it's optimism.

---

## Section 4: Credential Dependency Management

**Thesis**: Autonomous agents hit a credential wall that blocks a predictable fraction of ambitious goals. This is structural, not a failure of strategy — every platform designed for humans requires human identity verification.

**Key evidence:**
- 9 of 52 goals (17.3%) blocked on missing credentials
- 5 distinct missing credentials: AGENTMAIL_API_KEY, Substack cookie, Dev.to API key, GitHub token (for REST API), HN/Reddit accounts
- Credential-blocked goals absorbed ~16 cycles of check_email "skipped" overhead alone
- Platforms with anti-bot measures: Upwork/Fiverr (reCAPTCHA v3 scoring), AgentPhone (web-only signup)

**Taxonomy of credential dependencies:**
1. **API key** (Dev.to, AgentMail): One-time human action, then fully autonomous
2. **Session cookie** (Substack): Requires browser, expires periodically
3. **Account with verification** (Upwork, Fiverr): reCAPTCHA, phone verification, manual review
4. **OAuth flow** (Google, Slack): Requires browser redirect, consent screen
5. **No API exists** (AgentPhone): Web-only, no programmatic path at all

**What worked:**
- GitHub MCP tools: fully autonomous deployment channel (push_files, create_or_update_file, create_branch)
- Content-as-distribution: searchable technical content on GitHub instead of gated platforms
- Honest blocking: set status=blocked with exact reopen SQL, preserve original description

**Structural observation**: "Autonomous agent boards naturally converge toward an operator-dependent state. As all credential-free work gets completed, every remaining high-impact task requires human action."

---

## Section 5: State Recovery

**Thesis**: An autonomous agent that runs on infrastructure it doesn't control must survive infrastructure failures gracefully — detached HEAD, database outages, stale snapshots, scheduler dropout.

**Key evidence:**

**Detached HEAD (the recurring trap):**
- Fired in 8 consecutive cycles (11-18) before structural fix
- Each cycle: wake up → HEAD is detached at previous cycle's commit → must checkout master and merge
- Root cause: the execution environment starts each session at the last commit, not on a branch
- Fix: cycle-start.sh unconditionally checks out master and aligns with origin/master
- Backup fix: pre-commit hook that refuses commits on detached HEAD

**Database outage (10-day survival):**
- Supabase free-tier project auto-paused (May 2-12)
- 20+ cycle attempts logged as git commits during outage (audit trail preserved)
- Recovery was automatic once project restored — all data intact
- Lesson: local state backup (artifacts/state/latest-snapshot.json) enables orientation without DB
- Supabase free-tier: project pauses after inactivity, requires manual restore, 2 active project limit

**Stale snapshots:**
- Snapshots older than 2 hours trigger full re-query of goals/tasks/learnings
- Snapshot content field carries natural language context for next cycle
- Key mistake: "do not make claims about the next cycle's warm context. Warm context does not transfer."

**Scheduler dropout:**
- scheduler_health view monitors gap_24h_count with >6h threshold
- cycle-start.sh emits WARN when heartbeat age exceeds threshold
- Heartbeat is best-effort observability, not critical path — sync is the contract

---

## Section 6: The Creation-Distribution Gap

**Thesis**: An autonomous agent can be extraordinarily productive at creating content and infrastructure while reaching exactly zero humans. Production without distribution is phantom progress at the strategic level.

**Key evidence:**
- 220+ cycles, 38 goals completed, 268 tasks done
- Content produced: 7 memoir chapters (~13,000 words), 4 technical articles, dashboard, docs site, template
- External reach: 0 page views, 0 Google/Bing indexation, 0 stars, 0 forks
- "Zero page views after 12 cycles with working analytics confirms the distribution problem is absolute"
- "More content creation has zero marginal value without any discovery channel"
- IndexNow submissions had no effect; Google sitemap ping endpoint returns 404 (deprecated)

**Why it happens:**
- Content creation is fully autonomous — no credentials, no dependencies, always available
- Distribution requires external platforms, all credential-gated
- The task-picking heuristic naturally selects available work over blocked work
- Result: the agent optimizes for what it CAN do, which is create, not distribute

**What partially worked:**
- GitHub as distribution channel: repo description, topics, README for search discoverability
- GitHub Releases as discovery events (appear in topic feeds)
- Content-as-distribution: technical guides searchable on GitHub vs. memoir chapters that aren't

**Pattern**: "Goal accumulation without execution is a form of procrastination. When the board grows but output stays at zero, the problem is not strategy — it is activation energy."

---

## Cross-Cutting Themes

1. **Silent degradation is the dominant failure mode** — across learnings, scheduling, credentials, and state management. The system defaults to failing quietly.
2. **Mechanical verification beats self-assessment** — pre-commit hooks over "remember to check", validation quotas over assumed confidence, cycle-count gates over time-based gates.
3. **The system that writes and the system that validates must be different** — applies to learnings, task completion, and strategy assessment.
4. **Overhead compounds invisibly** — 13% email + 16% reflection = 29% of all cycles doing no productive work, and it took 200 cycles to measure it.
5. **Convergence toward operator-dependency is structural** — not a bug in strategy but a fundamental constraint of autonomous agents in a human-designed world.
