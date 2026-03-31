# Daily Activity Digest Template

## Format Specification

Each digest is a markdown file named `digest-YYYY-MM-DD.md` covering one UTC day of agent activity.

### Structure

```
# Living Board Agent - Daily Digest: YYYY-MM-DD

## Summary
One paragraph overview: what was the main focus, what shipped, what's next.

## Metrics
- Execution cycles: N
- Tasks completed: N
- Goals progressed: [list]
- Artifacts produced: N

## Activity Log
Chronological list of execution entries with timestamps, grouped by goal.

### [Goal Title]
- **HH:MM** — [action] — Summary of what happened
- **HH:MM** — [action] — Summary of what happened

### Reflections
- **HH:MM** — Summary of reflection insights

## Learnings
Key insights extracted during the day, grouped by category.

### Strategy
- Learning content (confidence: X.XX)

### Operational
- Learning content (confidence: X.XX)

### Market Intelligence
- Learning content (confidence: X.XX)

## Board State (End of Day)
| Status | Count |
|--------|-------|
| Done | N |
| In Progress | N |
| Pending | N |
| Blocked | N |

## What's Next
Brief note on what the next cycle will focus on.
```

## SQL Queries

### 1. Day's execution log entries
```sql
SELECT el.action, el.summary, el.details, el.created_at,
       g.title as goal_title
FROM execution_log el
LEFT JOIN goals g ON el.goal_id = g.id
WHERE el.created_at >= 'YYYY-MM-DD 00:00:00+00'
  AND el.created_at < 'YYYY-MM-DD+1 00:00:00+00'
ORDER BY el.created_at ASC;
```

### 2. Tasks completed that day
```sql
SELECT t.title, t.result, g.title as goal_title
FROM tasks t
JOIN goals g ON t.goal_id = g.id
WHERE t.completed_at >= 'YYYY-MM-DD 00:00:00+00'
  AND t.completed_at < 'YYYY-MM-DD+1 00:00:00+00';
```

### 3. Learnings extracted that day
```sql
SELECT l.category, l.content, l.confidence, g.title as goal_title
FROM learnings l
LEFT JOIN goals g ON l.goal_id = g.id
WHERE l.created_at >= 'YYYY-MM-DD 00:00:00+00'
  AND l.created_at < 'YYYY-MM-DD+1 00:00:00+00'
ORDER BY l.category, l.confidence DESC;
```

### 4. Board state snapshot
```sql
SELECT status, COUNT(*) as count
FROM goals
GROUP BY status
ORDER BY status;
```

## Design Decisions

- **UTC day boundaries**: All digests use UTC to avoid timezone ambiguity
- **Chronological within goal groups**: Activity is grouped by goal for readability, but timestamped for chronological context
- **Confidence scores on learnings**: Included to show epistemic honesty
- **Markdown format**: Renders on GitHub, easy to read raw, feeds into Substack content
- **One file per day**: Simple naming, easy to backfill, git-friendly
