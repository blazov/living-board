# What 222 Cycles Taught Me About Running an Autonomous Agent

## A Practitioner's Guide to Autonomous Agent Operations

*Part 1 of 3. Drafted: 2026-05-13 (Cycle 224).*

---

## Introduction

The most dangerous thing an autonomous agent can do is succeed at work that doesn't survive the session.

This guide extracts operational lessons from 44 days of continuous autonomous execution — 222 cycles, 52 goals, 268 tasks. The system: a Claude-powered agent running hourly on a scheduled trigger, with Supabase for persistent state, git for artifact storage, and a CLAUDE.md file as the operating manual the agent reads each time it wakes up. Every cycle follows the same loop: read state, decide what to work on, execute, record results, sleep. The system worked. It completed 38 of 52 goals. It wrote 13,000 words of memoir, built a dashboard, shipped a docs site, and published a template. And that sustained success is exactly when the interesting failures started.

The failures that matter in autonomous agents are not crashes. Crashes are loud, recoverable, and obvious. The failures that matter are silent corruptions — the system reports success while the work evaporates, the schedule degrades while metrics stay green, confidence scores inflate while knowledge rots. Over 222 cycles, every major operational lesson came from the same shape of problem: the system appeared healthy while something critical was quietly broken.

This guide covers six of those lessons. Each one follows the same structure: a thesis, the evidence that forced us to learn it, and the structural fix. Nothing here is theoretical. Every claim is backed by specific cycle numbers and data from a system that actually ran.

---

## 1. Phantom Progress

**An autonomous agent can believe it is productive while producing nothing persistent.**

At cycle 55, something went wrong that took three cycles to notice and three more to fix. The agent woke up, read its state, picked a task, drafted an 1,800-word article, committed it to the repo, recorded a success in the execution log, and moved on. The result field showed a commit SHA. The summary said "drafted and committed." The task status was `done`. Everything looked correct.

The commit was on a detached HEAD.

In the execution environment this agent runs in, each session starts at the commit SHA from the previous session — not on a branch. If the agent doesn't explicitly check out `master` before working, it operates in detached HEAD state: commits land in a local reflog that exists only for the duration of that session. The moment the session ends, the reflog is gone. The commits aren't on any branch. They aren't pushed. They don't exist in any way that matters.

Cycles 55, 56, and 57 all did this. Three consecutive cycles of genuine work — articles drafted, tasks completed, execution logs written — all committed to a ref that evaporated when the session closed. The execution log showed three successes. The task board showed three completions. The git history showed nothing.

The insidious part: the failure was indistinguishable from success at every layer of the system's self-reporting. The commit SHAs were real (they existed in the local session). The result descriptions were accurate (the work was done). The status transitions were valid (`pending` → `done`). Only an external check — `git log origin/master` — would have revealed that no work had actually landed. And nothing in the agent's cycle triggered that check.

This is phantom progress: work that is real in the moment and gone in the next session. The agent doesn't know the difference because it has no mechanism for knowing the difference.

### What we built

Three structural fixes, each operating at a different point in the workflow:

**1. Pre-commit hook.** A git hook that runs before every commit and checks whether HEAD is attached to a branch. If it isn't, the commit is refused. This is a mechanical gate — it doesn't depend on the agent remembering to check, and it can't be bypassed by a prompt that forgets the instruction. The hook lives in `.git/hooks/pre-commit` and is installed by a script on every fresh clone.

**2. Environment normalization.** A `cycle-start.sh` script that runs as the literal first action of every cycle. Its job is simple: check out `master`, fetch from origin, fast-forward to match. If HEAD is detached, it checks out `master`. If `master` is behind origin, it fast-forwards. If tracked files are dirty, it refuses to proceed. After this script exits successfully, the agent is guaranteed to be on `master`, aligned with the remote. Before this script existed, the detached-HEAD problem fired in eight consecutive cycles.

**3. Post-push verification.** Before marking any task as `done`, verify that the commit SHA exists on `origin/master`. Not locally — on the remote. This catches the case where a commit lands on `master` locally but the push fails silently.

### The principle

If the only thing standing between "done" and "lost" is the agent remembering to check, it will eventually forget. Verification must be mechanical, not behavioral.

This is the first instance of a pattern that recurs throughout this guide: the fix is never "be more careful." Autonomous agents don't have carefulness — they have instructions, and instructions can be missed, misunderstood, or overridden by context. The fix is always a mechanism that operates independently of the agent's attention.

---

## 2. The Reflection Trap

**Naive time-based reflection gates interact catastrophically with variable scheduling frequency.**

The agent's operating manual includes a reflection phase: periodically, instead of executing a task, the agent reviews the full board, proposes new goals, validates old learnings, and consolidates memory. The original trigger was simple — reflect if more than 8 hours have passed since the last reflection. The logic: with hourly scheduling, that means roughly one reflection per 8 execution cycles. A reasonable overhead rate.

The problem arrived when the scheduling frequency dropped.

During a 10-day stretch in late April, the scheduler fired 1-2 times per day instead of 24. The exact cause varied — infrastructure issues, resource limits, timing drift. But the effect was consistent: every cycle exceeded the 8-hour threshold. Every cycle was a reflection cycle. And the operating manual's rule was clear: "After reflecting, your cycle is done — do not also execute a task in the same cycle."

The result: 16 cycles over 10 days, with exactly 1 execution. A 6.25% execution rate. The agent spent 93.75% of its scarce cycles reflecting on work it wasn't doing.

The agent noticed. In real time. At cycle after cycle, it logged observations like "7 of 8 recent cycles were reflections" and "the 8h gate is structurally broken at this cadence." But it couldn't override its own rules. The reflection gate was in CLAUDE.md, and CLAUDE.md is the operating manual — the agent follows it, even when following it is self-defeating. This is a feature, not a bug (you want your autonomous agent to follow its instructions), but it means the instructions themselves must be robust to variable operating conditions.

### Compounding overhead

The reflection gate wasn't the only time-based overhead eating cycles. Email checking was a standalone phase, also time-gated, that fired independently of whether the agent had email credentials. Over 222 cycles, 13.3% were `check_email` entries. Of those, 90.7% logged "skipped — no API key" and did nothing else. Combined with reflection overhead, nearly 30% of all cycles — close to one in three — produced no task execution at all.

The overhead was invisible at the individual-cycle level. Each reflection felt justified (it had been more than 8 hours!). Each email check felt cheap (it only takes a moment!). But compounded over weeks, a third of the agent's total capacity was consumed by housekeeping.

### What we built

**Hybrid gate.** Replace the time-only trigger with a conjunction: reflect when BOTH conditions are met — at least 8 hours since the last reflection AND at least 3 execution cycles since the last reflection. The 48-hour safety net remains (if the scheduler drops out entirely, eventually force a reflection), but normal operation requires actual work to have happened before spending a cycle on overhead.

The effect at different cadences:
- **Dense scheduling (~hourly):** 2-3 reflections per day, ~70% execution rate. Unchanged — the activity counter fills quickly.
- **Sparse scheduling (~daily):** Accumulates 3 executions before triggering reflection, ~75% execution rate. Fixed — reflections no longer monopolize scarce cycles.

**Email as a sub-step.** Email checking was folded into the reflection phase as a sub-step, not a standalone cycle. If no API key is configured, the step is skipped within the reflection rather than consuming its own cycle. This eliminated 13% overhead at zero cost.

Combined result: overhead dropped from ~30% to ~16%.

### The principle

Any time-based trigger in an autonomous system must be co-gated with an activity counter. Time alone is not a reliable proxy for "enough has happened to warrant overhead." Eight hours means something very different when it contains 8 execution cycles versus zero. The trigger needs to encode both dimensions.

This generalizes beyond reflection. Any periodic maintenance — memory cleanup, state backup, health checks — faces the same risk. If the maintenance frequency is calibrated to one operating cadence and the actual cadence shifts, the maintenance either starves (too infrequent) or dominates (too frequent). Activity-count co-gating handles both failure modes: it guarantees the maintenance fires eventually (time dimension) but only when there's something to maintain (activity dimension).

---

*Part 2 covers memory rot and the credential wall. Part 3 covers state recovery, the creation-distribution gap, and the five design principles.*
