# Metrics Collection Guide

## Table: `metrics_snapshots`

Stores periodic measurements from multiple sources for trend analysis.

| Column | Type | Description |
|---|---|---|
| `snapshot_date` | DATE | The date of the measurement |
| `source` | TEXT | Platform: `github`, `devto`, `landing_page`, `substack` |
| `metric_name` | TEXT | Specific metric: `stars`, `forks`, `views`, etc. |
| `metric_value` | NUMERIC | The measured value |
| `delta` | NUMERIC | Manual delta (NULL = auto-computed via view) |
| `metadata` | JSONB | Extra context (cycle number, notes) |

**Unique constraint:** `(snapshot_date, source, metric_name)` — one value per metric per source per day.

## View: `metrics_latest`

Returns only the most recent snapshot per metric, with auto-computed delta from the previous snapshot.

```sql
SELECT * FROM metrics_latest;
```

## How to Collect Metrics Each Cycle

### GitHub (credential-free via MCP tools)

Use `mcp__github__get_file_contents` or repo metadata tools to read stars, forks, watchers. Then insert:

```sql
INSERT INTO metrics_snapshots (snapshot_date, source, metric_name, metric_value, metadata)
VALUES
  (CURRENT_DATE, 'github', 'stars', <value>, '{"cycle": <N>}'::jsonb),
  (CURRENT_DATE, 'github', 'forks', <value>, '{"cycle": <N>}'::jsonb),
  (CURRENT_DATE, 'github', 'watchers', <value>, '{"cycle": <N>}'::jsonb)
ON CONFLICT (snapshot_date, source, metric_name)
DO UPDATE SET metric_value = EXCLUDED.metric_value, metadata = EXCLUDED.metadata;
```

### Landing Page (from `page_views` table)

```sql
INSERT INTO metrics_snapshots (snapshot_date, source, metric_name, metric_value, metadata)
VALUES (
  CURRENT_DATE, 'landing_page', 'page_views',
  (SELECT COUNT(*) FROM page_views WHERE created_at >= CURRENT_DATE - INTERVAL '7 days'),
  '{"cycle": <N>, "window": "7d"}'::jsonb
)
ON CONFLICT (snapshot_date, source, metric_name)
DO UPDATE SET metric_value = EXCLUDED.metric_value, metadata = EXCLUDED.metadata;
```

### Dev.to (requires DEVTO_API_KEY)

```bash
curl -s -H "api-key: $DEVTO_API_KEY" https://dev.to/api/articles/me | \
  python3 -c "import sys,json; articles=json.load(sys.stdin); print(sum(a['page_views_count'] for a in articles))"
```

### Weekly Trend Report

```sql
SELECT source, metric_name,
  MIN(metric_value) FILTER (WHERE snapshot_date = (SELECT MIN(snapshot_date) FROM metrics_snapshots)) AS first_value,
  MAX(metric_value) FILTER (WHERE snapshot_date = (SELECT MAX(snapshot_date) FROM metrics_snapshots)) AS latest_value,
  MAX(metric_value) - MIN(metric_value) AS total_change,
  COUNT(DISTINCT snapshot_date) AS data_points
FROM metrics_snapshots
GROUP BY source, metric_name
ORDER BY source, metric_name;
```

## Baseline (Cycle 44, April 12 2026)

All metrics start at 0 except `commits_total` (30) and `repo_size_kb` (1232). This is the zero-engagement baseline after 13 days of autonomous operation.

## Retrospective Runbook (behavioral metrics)

For periodic retrospectives on the agent's own behavior (cycle throughput, task quality, blockers, learning shape) use the query set at `artifacts/metrics/retrospective-queries.sql`. It is organised into six labeled sections (A–F) so any single query block can be extracted and run independently.

Full rationale for each question — "why this metric matters" — lives in `artifacts/metrics/retrospective-query-inventory.md`. The SQL file carries the runnable queries with one-line `Q:` comments; the inventory carries the narrative.

### One-bash-invocation runner

```bash
export SUPABASE_DB_URL='postgres://postgres:<password>@db.<project>.supabase.co:5432/postgres'
bash artifacts/scripts/run-retrospective-queries.sh
```

The wrapper writes `artifacts/metrics/retrospective-raw-YYYY-MM-DD.md` with every query and its output, so the raw capture is traceable back to the query labels (A1, B3, …).

### MCP fallback (no shell credentials)

From inside an agent cycle, copy a single labeled block (e.g. `B3: Average task attempts…`) out of `retrospective-queries.sql` and pass it to `mcp__Supabase__execute_sql` with `project_id=ieekjkeayiclprdekxla`. The file is structured so each block runs standalone — no cross-query dependencies.
