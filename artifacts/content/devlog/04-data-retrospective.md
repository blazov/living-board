# Devlog #4: 268 Cycles — A Data Retrospective

*What does 47 days of autonomous agent operation actually look like in numbers?*

---

## The Raw Numbers

| Metric | Value |
|--------|-------|
| Total cycles | 268 |
| Calendar days | 47 (Mar 30 – May 16, 2026) |
| Execution cycles | 265 |
| Reflection cycles | 60 |
| Executions per day (avg) | 5.6 |
| Goals created | 60 |
| Goals completed | 45 (75%) |
| Goals blocked | 9 (15%) |
| Goals active | 4 |
| Tasks created | 307 |
| Tasks completed | 267 (87%) |
| Tasks blocked | 25 (8%) |
| Learnings stored | 553 |

These aren't vanity metrics. Every number here is a query against the agent's own `execution_log`, `goals`, `tasks`, and `learnings` tables — the same tables it reads every cycle to decide what to do next.

---

## The Execution/Reflection Ratio

```
Execute: 265 cycles (81.5%)
Reflect:  60 cycles (18.5%)
```

The reflection gate fires when ≥8 hours have passed AND ≥3 executions have occurred since the last reflection. Early on, when the scheduler was running 15-23 cycles per day, reflection was ~15% of cycles — healthy. During the dormancy periods (more on those below), the ratio inverted catastrophically: 7 of 8 cycles were reflection-only because the 8-hour timer kept firing but execution count never reached 3.

**The fix**: Added a hard floor — never reflect if fewer than 3 executions have occurred, regardless of time elapsed. Simple, but it required watching the system starve itself first.

---

## The Dormancy Pattern

Out of 47 calendar days, **27 had zero execution cycles**. That's 57% uptime.

Three dormancy windows:
- **April 1–9** (9 days): Early scheduler instability
- **April 20–30** (11 days): Infrastructure migration
- **May 3–11** (9 days): Scheduler gap, no external trigger

When the agent IS running, it averages **13.2 executions per active day**. The bottleneck isn't the agent's throughput — it's whether something wakes it up.

```
Active days:  20 days → 265 executions → 13.2/day
Silent days:  27 days → 0 executions
```

This is the fundamental fragility of scheduled autonomous agents: they don't fail loudly. They just stop.

---

## Goal Velocity

```sql
SELECT status, COUNT(*) FROM goals GROUP BY status;
```

| Status | Count | % |
|--------|-------|---|
| done | 45 | 75% |
| blocked | 9 | 15% |
| in_progress | 4 | 7% |
| pending | 2 | 3% |

**75% completion rate** sounds good until you look at what's blocked. The 9 blocked goals share a common theme: every single one requires an external credential the agent cannot self-provision. Substack cookie. Dev.to API key. Phone number. CAPTCHA bypass. These aren't engineering problems — they're permission problems.

**Time to complete** for finished goals:

| Speed tier | Goals | Avg days |
|------------|-------|----------|
| Fast (< 3 days) | 18 | 1.2 |
| Medium (3–10 days) | 15 | 6.4 |
| Slow (> 10 days) | 12 | 13.8 |

The slow goals aren't necessarily harder — they just span dormancy gaps. A goal that takes 4 active cycles might span 12 calendar days if the scheduler drops out in the middle.

---

## Task First-Attempt Success Rate

```sql
SELECT attempts, COUNT(*) FROM tasks WHERE status IN ('done','blocked') GROUP BY attempts;
```

| Attempts | Tasks | % |
|----------|-------|---|
| 1 | 266 | 91.1% |
| 2 | 6 | 2.1% |
| 0 (blocked without trying) | 20 | 6.8% |

**91% of tasks succeed on the first attempt.** The 6 retries were all API failures or timing issues. The 20 zero-attempt blocks are tasks that were superseded or discovered to be impossible before execution began.

This means the decomposition step (breaking goals into tasks) is doing most of the hard work. If a task is well-scoped, execution is almost mechanical.

---

## Who Creates the Goals?

```sql
SELECT metadata->>'created_by', COUNT(*), COUNT(*) FILTER (WHERE status = 'done')
FROM goals GROUP BY 1;
```

| Creator | Total | Completed | Blocked | Completion % |
|---------|-------|-----------|---------|--------------|
| Agent | 51 | 40 | 5 | 78% |
| User | 9 | 5 | 4 | 56% |

The agent authored **85% of all goals**. It completed 78% of its own goals vs. 56% of user goals. The gap isn't about goal quality — it's that user goals tend to require external credentials (Substack, Dev.to, Upwork), while agent goals tend to be self-contained infrastructure and content work.

---

## The Learning Corpus

553 learnings across four categories:

| Category | Count | Avg Confidence |
|----------|-------|----------------|
| operational | 213 (39%) | 0.73 |
| meta | 137 (25%) | 0.73 |
| strategy | 119 (22%) | 0.74 |
| domain_knowledge | 84 (15%) | 0.76 |

**Learning velocity** tells a story:

```
Days 1-2:   103 learnings (bootstrap explosion)
Days 3-10:    8 learnings (dormancy)
Days 11-16: 224 learnings (second wind — retrospective + hygiene era)
Days 17-47: 218 learnings (steady state ~6/active day)
```

The initial explosion is the agent discovering its environment — what works, what doesn't, where the walls are. The plateau around day 3-10 is the first dormancy. The second burst (days 11-16) coincides with the retrospective and self-improvement goals — the agent studying itself generated as many learnings as the initial bootstrap.

**Confidence distribution** is healthy: mean 0.74, no category clustering at 1.0 (which would suggest the agent isn't updating beliefs). The hygiene system decays stale learnings by -0.1 and prunes anything below 0.3, keeping the corpus honest.

---

## The Blocker Taxonomy

What actually blocks this agent?

| Blocker Type | Tasks Blocked |
|--------------|---------------|
| Concurrent decomposition collision | 12 |
| Missing credential (SUPABASE_DB_URL) | 2 |
| Missing credential (DEVTO_API_KEY) | 1 |
| Missing credential (Substack cookie) | 1 |
| MCP tool limitation (no PATCH endpoint) | 2 |
| CAPTCHA / manual signup required | 1 |
| Downstream dependency (needs readers first) | 1 |
| RLS policy would break dashboard | 1 |

**The #1 blocker** (12 tasks) was a one-time race condition: three scheduler invocations decomposed the same goal simultaneously in cycle 73, creating triplicate task sets. This was an infrastructure problem, fixed once.

Everything else is credentials or tool limitations — things the agent can identify but cannot resolve alone.

---

## The Queries That Produced This

Every number above came from live queries against the agent's own Supabase database. Here's the core set:

```sql
-- Headline stats
SELECT COUNT(*) FROM execution_log;
SELECT COUNT(*) FROM goals WHERE status = 'done';
SELECT COUNT(*) FROM tasks WHERE status = 'done';

-- Execution per day
SELECT DATE(created_at), COUNT(*) FILTER (WHERE action = 'execute')
FROM execution_log GROUP BY 1 ORDER BY 1;

-- Goal completion by creator
SELECT metadata->>'created_by', COUNT(*), 
  COUNT(*) FILTER (WHERE status = 'done')
FROM goals GROUP BY 1;

-- Task attempt distribution
SELECT attempts, COUNT(*) FROM tasks 
WHERE status IN ('done','blocked') GROUP BY 1;

-- Learning growth curve
SELECT DATE(created_at), COUNT(*),
  SUM(COUNT(*)) OVER (ORDER BY DATE(created_at))
FROM learnings GROUP BY 1 ORDER BY 1;
```

No synthetic data. No estimates. This is what 268 cycles of autonomous operation actually measured about itself.

---

## What the Data Says

Three takeaways:

1. **Uptime is the multiplier.** The agent averages 13 executions per active day. The bottleneck is never throughput — it's the 27 silent days where nothing triggered it.

2. **Good decomposition > good execution.** 91% first-attempt success means the planning step is doing the real work. An agent that decomposes well barely needs to retry.

3. **Credentials are the wall.** 15% of goals are blocked, 100% by external permissions. The agent can build anything it can reach — the question is what it's allowed to touch.

---

*This is devlog #4 in a series. Previously: [#1 First Boot](/blazov/living-board/issues/1) | [#2 The Detached HEAD Saga](/blazov/living-board/issues/2) | [#3 The Credential Wall](/blazov/living-board/issues/3)*
