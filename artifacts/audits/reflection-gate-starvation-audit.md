# Reflection Gate Starvation Audit

**Task:** d4bdb6a3 — Audit reflection gate starvation from execution data
**Date:** 2026-05-12 | **Cycle:** 209

## Summary

The 8-hour time-based reflection gate is structurally broken when cycle frequency drops below ~3 cycles/day. During the April 20–30 sparse scheduling period, the gate consumed 93.75% of all cycles as reflection-only, producing just 1 execution in 16 cycles.

## Data

### Overall action distribution (318 total logged actions)

| Action       | Count | Pct    |
|-------------|-------|--------|
| execute     | 211   | 66.4%  |
| reflect     | 52    | 16.4%  |
| check_email | 43    | 13.5%  |
| decompose   | 9     | 2.8%   |
| blocked     | 2     | 0.6%   |
| close_goal  | 1     | 0.3%   |

**Overhead (reflect + email): 29.9%** — close to the retrospective's 33.4% figure.

### Starvation period: April 20–30

| Date   | Executions | Reflections | Email | Total | Exec Rate |
|--------|-----------|-------------|-------|-------|----------|
| Apr 20 | 0         | 2           | 2     | 4     | 0%        |
| Apr 21 | 0         | 1           | 1     | 2     | 0%        |
| Apr 22-25 | —      | —           | —     | 0     | (no cycles) |
| Apr 26 | 1         | 1           | 1     | 3     | 33%       |
| Apr 27 | 0         | 1           | 1     | 2     | 0%        |
| Apr 28 | 0         | 1           | 1     | 2     | 0%        |
| Apr 29 | 0         | 1           | 0     | 1     | 0%        |
| Apr 30 | 0         | 1           | 1     | 2     | 0%        |

**10 days, 16 cycles, 1 execution = 6.25% execution rate.**

The agent itself flagged this in real-time:
- Cycle 160: "Third consecutive reflection cycle — 8h gate starving execution"
- Cycle 165: "6 of last 7 cycles reflection-only; this is the anti-pattern"
- Cycle 166: "7 of 8 cycles. The 8h gate is structurally broken when cycle frequency drops to ~daily"

### Healthy periods for comparison

During dense scheduling (April 11-19, ~hourly):

| Metric | Value |
|--------|-------|
| Avg executions between reflections | 5.1 |
| Reflections/day | 2-3 |
| Execution rate | ~70% |

During the May 1 burst (cycles 167-177, ~hourly):
- 11 cycles: 7 executions, 3 reflections, 1 email = 64% execution rate

### Root cause

The 8h gate assumes frequent scheduling (~hourly = ~24 cycles/day). At that frequency:
- 8h ≈ every 8th cycle → ~3 reflections/day with 5-8 executions between each ✓

When cycle frequency drops to 1-2/day:
- Every cycle exceeds the 8h threshold
- Every cycle becomes reflection-only
- CLAUDE.md says "After reflecting, your cycle is done — do not also execute a task in the same cycle"
- **Result: 0% execution rate indefinitely**

### Executions between reflections (full dataset)

Intervals with 0 executions between consecutive reflections: **12 out of 51 intervals (23.5%)**

All 12 zero-execution intervals occurred during sparse scheduling or rapid back-to-back reflections:
- 5 during Apr 20-30 starvation window
- 4 during early calibration (Mar 30-31, sub-3h gaps)
- 2 during Apr 16-17 deadlock (cycle 121-122)
- 1 during Apr 18 rapid double-fire (0.8h gap)

## Recommendation: Hybrid gate (time + cycle-count)

Replace the single 8h time check with a dual condition:

**Reflect when ALL of:**
1. **≥8 hours** since last reflection (prevents over-reflecting during dense scheduling)
2. **≥3 execution cycles** since last reflection (prevents starvation during sparse scheduling)

**Exception — hard ceiling:**
3. **Always reflect if ≥48 hours** since last reflection, regardless of execution count (safety net for extended gaps / scheduler failures)

### Expected behavior under this gate

| Scheduling    | Cycles/day | Reflections/day | Exec rate | Notes |
|--------------|-----------|-----------------|-----------|-------|
| Dense (~hourly) | ~24    | 2-3             | ~70%      | Same as current healthy behavior |
| Moderate (6-8h) | 3-4    | ~1              | ~67%      | Reflects after every 3rd execution |
| Sparse (~daily) | 1-2    | ~0.3-0.5        | ~75%      | Accumulates 3 executions before reflecting |
| Extended gap   | <1      | forced at 48h   | n/a       | Safety net catches scheduler dropout |

### Implementation SQL

Current gate query:
```sql
SELECT created_at FROM execution_log
WHERE action = 'reflect'
ORDER BY created_at DESC LIMIT 1;
-- Then: if >8h ago → reflect
```

Proposed replacement:
```sql
WITH last_reflect AS (
  SELECT created_at FROM execution_log
  WHERE action = 'reflect'
  ORDER BY created_at DESC LIMIT 1
),
exec_since AS (
  SELECT COUNT(*) as cnt FROM execution_log
  WHERE action = 'execute'
  AND created_at > (SELECT created_at FROM last_reflect)
)
SELECT
  lr.created_at as last_reflect_at,
  EXTRACT(EPOCH FROM (now() - lr.created_at)) / 3600 as hours_since,
  es.cnt as executions_since,
  CASE
    WHEN lr.created_at IS NULL THEN true                          -- never reflected
    WHEN now() - lr.created_at > interval '48 hours' THEN true   -- hard ceiling
    WHEN now() - lr.created_at > interval '8 hours'
     AND es.cnt >= 3 THEN true                                    -- normal gate
    ELSE false
  END as should_reflect
FROM last_reflect lr, exec_since es;
```

### Why not cycle-count-only?

A pure cycle-count gate (e.g., "every 5th cycle") would solve starvation but could cause under-reflecting during dense scheduling. With 24 cycles/day and a gate of every 5th, you'd get ~5 reflections/day — too many. The hybrid preserves the 8h floor that works during dense scheduling while adding the cycle-count floor that prevents starvation during sparse scheduling.
