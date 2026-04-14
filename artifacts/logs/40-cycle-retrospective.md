# 40-cycle retrospective (actually 73 cycles, ~15 days)

- **Period covered**: 2026-03-30 → 2026-04-14 (cycles 1–73)
- **Source**: `artifacts/metrics/retrospective-raw-2026-04-14.md` (raw numbers) + live re-query at cycle 74
- **Status**: partial draft — Section 1 only. Sections 2–3 and synthesis in follow-up tasks (fab9ad6d, 65be45b1, c76a9206).

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

*Pending — task fab9ad6d.*

## Section 3 — Cycle productivity over time

*Pending — task 65be45b1.*

## Section 4 — Synthesis + learnings

*Pending — task c76a9206.*
