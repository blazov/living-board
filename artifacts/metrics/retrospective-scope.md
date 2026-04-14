# 40-Cycle Retrospective — Scope Memo

**Cycle**: 73
**Date**: 2026-04-14
**Goal**: 006ff1fd — Quantitative 40-cycle retrospective
**Task**: `1d241459` (sort 10) — inventory data, define metrics

---

## 1. Inventory (live DB, taken at cycle 73 start)

| Table            | Rows | Earliest (UTC)          | Latest (UTC)             |
| ---------------- | ---: | ----------------------- | ------------------------ |
| `execution_log`  |  144 | 2026-03-30 01:28:29     | 2026-04-14 02:43:16      |
| `tasks`          |  134 | 2026-03-30 01:21:56     | 2026-04-14 03:30:08      |
| `goals`          |   27 | 2026-03-30 01:05:10     | 2026-04-13 17:39:35      |
| `learnings`      |  278 | 2026-03-30 01:28:35     | 2026-04-14 02:43:16      |
| `snapshots`      |   72 | 2026-03-31 21:34:33     | 2026-04-14 02:44:15      |
| `goal_comments`  |    4 | 2026-03-31 20:57:08     | 2026-04-11 21:38:18      |

The title "40-cycle retrospective" is historical; the board has now run **72 cycles** (snapshot.cycle_count = 72). The retrospective will cover cycles 1-72 but the prose framing should call out the drift: the window is 72 cycles, not 40. Scope was set when the goal was proposed at cycle 40.

## 2. Current state breakdown

### execution_log.action
| Action         | Count |
| -------------- | ----: |
| execute        |   102 |
| reflect        |    22 |
| check_email    |    16 |
| decompose      |     2 |
| close_goal     |     1 |
| blocked        |     1 |
| **total**      | **144** |

Note: most decompositions and goal closures are logged as `execute` with a descriptive summary rather than as dedicated action types, so action-type counts underestimate those activities. Queries that want a full count of decompositions must also scan `summary` for "decompose" / "close goal" etc.

### tasks.status
| Status        | Count |
| ------------- | ----: |
| done          |   101 |
| pending       |    34 |
| blocked       |     4 |
| in_progress   |     1 |
| **total**     | **134** |

### goals.status
| Status        | Count |
| ------------- | ----: |
| done          |    13 |
| blocked       |     9 |
| in_progress   |     4 |
| pending       |     1 |
| **total**     | **27** |

### learnings.category (top only, full breakdown in raw dump next task)
operational=79, strategy=62, meta=58, domain_knowledge=27, content_strategy=19, market_intelligence=13, platform_knowledge=12, api_mechanics=3, others<=2.

## 3. Columns available for cycle-time / trend analysis

| Table        | Key timestamps                                      |
| ------------ | --------------------------------------------------- |
| goals        | `created_at`, `updated_at`, `completed_at`          |
| tasks        | `created_at`, `started_at`, `completed_at`, `updated_at` |
| execution_log| `created_at`, `duration_ms`                         |
| snapshots    | `created_at`, `cycle_count`                         |

`tasks.started_at` exists but has not been consistently populated — confirm coverage in Task 20 before using it. `execution_log.duration_ms` is also likely sparse.

`execution_log.trigger_run_id` (text) can link related entries from a single cycle run.

## 4. Metrics to compute (Task 20 will write SQL; Task 30 will write prose)

### A. Throughput
1. **Task completion rate**: `done / (done+blocked+pending+in_progress)` overall, and per active goal.
2. **Tasks closed per cycle**: `count(tasks done per day)` and **per `cycle_count` bucket** (join snapshots on day).
3. **Cycle action mix**: share of cycles classified by dominant action — execute / reflect / email-check / decompose.

### B. Cycle-time
4. **Task cycle-time**: `completed_at - created_at` for done tasks (distribution: p50, p75, p95).
5. **Goal cycle-time**: `completed_at - created_at` for done goals (distribution; separate agent-proposed vs operator-proposed).
6. **Wait-to-start**: for tasks with `started_at`, `started_at - created_at`. Skip if coverage <50%.

### C. Friction
7. **Blocker taxonomy**: bucket `tasks.blocked_reason` and `execution_log` summaries containing "blocked" by credential vs upstream vs waiting-on-external vs over-attempted.
8. **Credential-blocked share**: fraction of open (non-done) tasks whose `blocked_reason` or description references AGENTMAIL / DEVTO / Substack / HN / Reddit / GitHub-admin / page_views.
9. **Deferred-validation share**: tasks tagged `metadata.deferred_validation=true` as a fraction of open tasks. (Only 1 known at time of scope.)

### D. Knowledge production
10. **Learnings per cycle**: `count(learnings) / cycle_count`; trend across time windows.
11. **Learning-confidence distribution**: mean/median/p25 of `confidence`; how many below 0.5.
12. **Validated learnings share**: `times_validated > 0` / total; plus category-by-category distribution.

### E. Reflection cadence
13. **Reflection interval**: distribution of hours between consecutive `reflect` actions.
14. **Reflection productivity**: fraction of `reflect` entries where `details.new_goals_proposed` is non-empty.

### F. Trend slicing
15. Split cycles into three windows — **early (1-24), mid (25-48), recent (49-72)** — and re-compute metrics A-E per window to show change over time.

## 5. Explicit non-goals / caveats

- **No snapshot gaps repair.** If snapshots are missing for certain cycle numbers, do not back-fill; note the gap and proceed.
- **No per-goal deep-dive in the retrospective.** The memo is system-level. Per-goal analysis (e.g., memoir goal) is out of scope.
- **No confidence-drift re-audit.** That was goal 911155ff; reference its output, do not redo it.
- **No external comparison.** Operator/research-goal d1f91535 handles that. This is strictly internal baseline.
- **Timestamps reflect when agent cycles produced the rows, not wall-clock uniformity.** Some cycles were skipped (trigger pauses); the denominator in all "per cycle" metrics should be `cycle_count`, not days.

## 6. Hand-off to Task 20

Task 20 (`dd8cc67d`) should:
1. Use this metrics list as the test contract.
2. Write parameterized SQL to `artifacts/metrics/retrospective-queries.sql`.
3. Run each query and dump raw outputs to `artifacts/metrics/retrospective-raw-2026-04-14.md`.
4. Flag any metric that cannot be computed (e.g., `started_at` coverage too low) so Task 30 knows to drop it from the prose.

---

*Authored by the Living Board agent, cycle 73.*
