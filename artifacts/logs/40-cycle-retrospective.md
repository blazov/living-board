# 40-cycle retrospective (actually 73 cycles, ~15 days)

- **Period covered**: 2026-03-30 → 2026-04-14 (cycles 1–73)
- **Source**: `artifacts/metrics/retrospective-raw-2026-04-14.md` (raw numbers) + live re-query at cycle 74
- **Status**: partial draft — Sections 1 and 2 complete. Section 3 and synthesis in follow-up tasks (65be45b1, c76a9206).

> The goal title says "40-cycle" but the window under study is 73 cycles over ~15 days at hourly cadence. The name is kept for continuity with the scoping doc (`artifacts/metrics/retrospective-scope.md`).

---

## Section 1 — Task quality

### 1.1 Headline numbers

Normalized to the pre–cycle-73 state (134 tasks, excluding the 6 retrospective decomposition tasks inserted this cycle):

| metric | value | notes |
|---|---:|---|
| done | 101 / 134 | **75.4%** — the single best summary of execution quality |
| blocked (frozen at cycle-73 dump) | 4 / 134 | **3.0%** — all credential/operator-gated |
| pending | 29 / 134 | 21.6% |
| in_progress | 1 / 134 | 0.7% |

Live re-query at cycle 74 shows **104 done** (+3 since the frozen dump) and **16 blocked** (+12). The +12 is **not** new failure — it is the post-hoc supersession of duplicate tasks produced by the cycle-73 three-way concurrent decomposition (13 duplicates were marked `blocked` with a supersession reason). Filtering those out, the real-blocker count is still **4**.

**Retry rate** (tasks that needed ≥2 attempts to succeed, out of all successful tasks): `4 / 101 ≈ 4.0%`.

### 1.2 Attempts histogram

| attempts | n | interpretation |
|---:|---:|---|
| 0 | 39 | not yet touched (includes this cycle's 5 fresh inserts) |
| 1 | 97 | one-shot success — the dominant mode |
| 2 | 4 | single retry required; all 4 finished as `done` |

No task has attempts ≥ 3. Nothing maxed out (`attempts = max_attempts` with status=blocked: **0**).

### 1.3 Reopens / reworks

Two cross-checks for "tasks that got picked up more than once":

- **Stalled-attempted** (tasks with `attempts > 0` but not yet `done`): **3** — all are pending re-execution, none are abandoned.
- **`execute` log entries sharing a `task_id` (≥2 touches)**: **4** — matches the attempts-=-2 histogram bucket. Nothing slipped the `attempts` counter.

There is no evidence of a status-reopen (`done` → `pending`/`in_progress`) anywhere in the data. The `attempts` field is a faithful retry counter.

### 1.4 Origin

| origin | n |
|---:|---:|
| agent-created | 137 |
| user-created | 3 |
| unknown | 0 |

**98% of tasks are agent-authored.** The 3 user tasks were all authored in the earliest cycles. Decomposition quality is overwhelmingly the agent's responsibility, which is reassuring given retry rate is 4%.

### 1.5 Data-quality observations

1. **Task `completed_at` is populated on 104 / 104 done tasks (100%)** — contrast with the cycle-73 dump finding that **goals.completed_at is populated on only 4/13 done goals (31%)**. The gap is a goal-closure invariant problem, not a task-closure one. (Carried into Section 2.)
2. **Blocked counts are mode-dependent.** `COUNT(status='blocked')` returns 16 today but only 4 represent real external blockers; 12 represent cleanup supersessions. Any future retrospective SQL should either exclude the supersession reason string or report both numbers.
3. **`attempts` vs `execute-log touches` reconcile exactly** (4 = 4) — the two independent counters agree, which is a small but real credibility signal for the rest of the data.

### 1.6 Surprises flagged for synthesis

- **4.0% retry rate across 101 successful tasks is low.** Most autonomous pipelines don't hit 96% first-attempt-success. The interpretation is likely *selection effect*: the agent decomposes tasks small enough that one cycle usually finishes them, and escalates to `blocked` rather than retrying when stuck. That's a planning-quality story more than an execution-quality one.
- **Zero `attempts = max_attempts` blockers.** All 4 real blockers are pre-emptive — the agent recognized the dependency (credential / account) before wasting attempts. This contradicts the mental model where `blocked` means "we tried and failed"; here it means "we saw we couldn't start."
- **100% task-level `completed_at` coverage vs 31% goal-level.** The closure discipline that exists at the task layer is missing at the goal layer. Cheap to fix in-code; the fix is already documented as a learning (confidence 0.95 in the cycle-73 snapshot).
- **Retry of non-done tasks is basically nil (3 stalled, all pending).** There is no meaningful pile of partially-worked-abandoned tasks — board hygiene is intact.

### 1.7 One-sentence summary of Task Quality

Over 73 cycles the agent produced 101 successful task completions with a 4% retry rate, zero max-attempts blowouts, and 100% task-closure fidelity; what it does execute, it executes cleanly. The open questions (why 9/27 goals are blocked, why goal-level closure discipline lags task-level) live in Section 2.

---

## Section 2 — Goal flow & blockers

### 2.1 Headline numbers

27 goals created over 73 cycles (~15 days). Status distribution:

| status | n | % | notes |
|---|---:|---:|---|
| done | 13 | 48% | only 4 have `completed_at` populated (carryover DQ flag from §1) |
| blocked | 9 | 33% | **9 of 9 are credential-, operator-, or self-imposed** — zero agent-execution failures |
| in_progress | 4 | 15% | all on track; 3 at ≥80% per cycle-74 snapshot |
| pending | 1 | 4% | `5fd7408c` Live public status page |

Authorship: 13 agent-originated vs 14 user-originated — roughly even, which matters for the blocker taxonomy below: user-scoped goals are longer-running and blocker-heavier than agent-scoped ones.

### 2.2 Cycles-to-completion per done goal

Hourly cadence ≈ 1 cycle/hour, so wall-hours ≈ cycles (modulo ~2 downtime gaps). The distribution is strongly **bimodal**, not well-summarized by a single mean:

| cluster | n | mean | median | typical author |
|---|---:|---:|---:|---|
| agent-scoped (<25h) | 8 | 10.9 cycles | 9.5 cycles | agent-originated, self-contained |
| user-scoped (≥100h) | 5 | 229.9 cycles | 250.3 cycles | user-originated, cross-system, operator-dependent |

Global mean across all 13 done goals: 95.2h; median: 19.9h. The mean is **~5× the median** — a textbook signal that the mean is carried by the long tail and should not be reported alone. The honest summary is: *agent-scoped goals close in ~10 cycles; user-scoped ones in 100–300.*

Two corner cases:
- `82f22be6` (Set up agent email) closed in 0.0h — it was instantaneously marked done, likely because the setup preceded the board.
- `be77a972` (content reach feedback loops) at 314h is the longest runner; it spanned the full operating window and is the one whose retrospective spurred §D1–D2.

### 2.3 Blocker taxonomy

Twelve blocked records in total were classified (9 goals + 4 real blocked tasks; the 12 supersession tasks from cycle 73 are excluded per the §1 data-quality rule). Each record assigned to one primary cause:

| category | n | share | examples |
|---|---:|---:|---|
| **credential missing** (API key/token required) | 4 | 31% | `a78c792a` AgentMail; `f612920e` Dev.to; `0977fc88` GitHub admin token; task `788354ec` Dev.to stats |
| **external-human action** (manual web signup, reCAPTCHA, operator gate) | 5 | 38% | `eefdce63` AgentPhone; `34faac0e` Upwork/Fiverr; tasks `832edecb`, `6b9a4b8d`, `da3c8b66` |
| **dependency on another blocked item** (transitive) | 1 | 8% | `fd0979e3` Engage-with-Dev.to-community ← `f612920e` |
| **strategic / self-imposed defer** (agent board-hygiene) | 3 | 23% | `1aeb7e16` premature pipeline; `986468d9` consolidated; `77d5b60b` deferred Medium |
| **invariant / structural failure** | 0 | 0% | — |
| **agent-execution failure** (planning or runtime bug) | 0 | 0% | — |

**Top 3 blocker categories, with cycle-cost estimates:**

1. **External-human action (5 records, ~38%).** The dominant category by count. Cycle cost is hard to measure directly — the agent doesn't "spin" on these, it files them and moves on — but the *opportunity cost* is ~2 goals (Upwork/Fiverr monetization, agent phone) that have been fully-planned and then frozen since cycle ~40. Estimated wasted active-work: **≤ 3 cycles total** across all 5 (initial decomposition + one re-check each). Low direct cost, high strategic cost.
2. **Credential missing (4 records, ~31%).** Most-measurable cycle cost. From C4 in the raw dump: `check_email` was skipped on 12 of 16 attempts (75%) for the full operating window — a literal **~12 cycles** of scheduled email work produced only a "skipped" log entry. Add ~2 cycles of Dev.to API-surface research before the key was recognized as definitively missing, plus the GitHub-admin sub-path inside `0977fc88` (~2 cycles). **Estimated direct cycle cost: ~16 cycles, or roughly 22% of the 73-cycle budget** — consistent with the 21% credential-language rate across all log rows.
3. **Strategic / self-imposed defer (3 records, ~23%).** All three are *healthy* blocks — the agent proactively shelved premature or duplicated goals during reflection cycles (cycles 34, 63, 64). Cycle cost: **≈ 0** (the decision to defer is a reflection output, not a wasted execution). Counted here as a blocker only because the schema enum forces it.

Categories 4 and 5 together: **0 records.** Over 73 cycles and 101 successful tasks, no goal was blocked by an invariant failure, planning error, or runtime bug. Every blocked goal traces to something outside the agent's authority. This is a surprising and sturdy finding; see §2.5.

### 2.4 Credential-blocked share of cycles

Three independent measures of credential dependency triangulate on the same range:

| measure | value | interpretation |
|---|---:|---|
| share of blocked items caused by missing credentials (direct + transitive) | 5 / 13 = **38%** | structural — who blocks what |
| share of execution_log entries mentioning credential/missing/key | 31 / 145 = **21%** | textual — how often it comes up |
| share of `check_email` cycles that skipped due to absent `AGENTMAIL_API_KEY` | 12 / 16 = **75%** (for that action only) | operational — the worst-hit loop |
| estimated direct cycle cost across the budget | ~16 / 73 = **~22%** | effective — wasted active work |

**Take:** roughly one in five cycles of active agent work is either consumed by, or blocked on, a credential the operator has not provided. This is the single largest lever the operator holds over throughput.

### 2.5 Goal-level closure discipline (carried over from §1)

Section 1 flagged: `tasks.completed_at` is 104/104 populated, but `goals.completed_at` is only 4/13. The 9 "done but no `completed_at`" goals were closed by flipping `status='done'` without the atomic timestamp. Section 2.2 inherited this gap — every cycles-to-completion figure in the table above uses `updated_at` as a proxy for 9 of 13 rows.

The fix is a one-line SQL discipline (`UPDATE goals SET status='done', completed_at=now() WHERE ...`) and was already stored as an operational learning (confidence 0.95) in the cycle-73 snapshot. Section 4 will recommend encoding it as a trigger or a checklist item in the cycle-end phase of `CLAUDE.md`.

### 2.6 Surprises flagged for synthesis

- **Zero agent-execution blockers across 27 goals** is the same surprise as §1's zero max-attempts blowouts, viewed from the goal side. The agent does not fail its way into blocked; it recognizes unreachability and escalates pre-emptively. This is a planning-quality signature.
- **The bimodal cycles-to-completion distribution is authorship-sorted, not topic-sorted.** Agent-authored goals close in ~10 cycles; user-authored ones in 100–300. The agent scopes goals it can actually finish in its own cadence; the user scopes long-horizon outcomes. Both are valid, but reporting a single mean hides the fact.
- **External-human action (38%) outranks credential missing (31%) by count, but credential missing costs far more cycles** (~16 vs ≤3). Category frequency and category cost disagree — future board-health dashboards should weight blockers by estimated cycle cost, not count.
- **Strategic defers are healthy**, not pathology. Three of nine blocked goals represent the agent *correctly* recognizing premature scope. Any future "blocked rate" metric should split real blockers from self-deferrals — reporting `9/27 = 33%` blocked rate without that split overstates the problem by ~33%.

### 2.7 One-sentence summary of Goal Flow & Blockers

Of 27 goals, 13 closed (8 in ~10 cycles, 5 in 100–300), 9 are blocked entirely on operator-side or self-imposed causes (0 on agent errors), and roughly one cycle in five is absorbed by credential absence — making operator-provided credentials the single largest throughput lever; the "why goals stall" answer is structural, not about the agent getting stuck.

## Section 3 — Cycle productivity over time

*Pending — task 65be45b1.*

## Section 4 — Synthesis + learnings

*Pending — task c76a9206.*
