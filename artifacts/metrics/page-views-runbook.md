# Landing Page Analytics — Query Runbook

**Source table:** `public.page_views`
**Writer:** `docs/index.html` (inline `<script>` at end of body)
**Key:** `sb_publishable_EI6cI1G5mUmgVH-rWIgfrA_q0MJF1fY` (publishable anon, hardcoded in the page — this is the designed use)
**Privacy model:** write-only from the public side (RLS permits `INSERT` for `anon`, no `SELECT` policy). No cookies, no IP, no cross-site tracking.

---

## What gets stored per visit

| Column        | Example                       | Notes |
|---------------|-------------------------------|-------|
| `path`        | `/`, `/index.html`            | Pathname + query string |
| `referrer`    | `https://news.ycombinator.com/` | `document.referrer`, null if direct |
| `user_agent`  | `Mozilla/5.0 ...`             | For device/browser category |
| `screen_w`    | `1920`                        | Viewport classifier |
| `screen_h`    | `1080`                        | Viewport classifier |
| `lang`        | `en-US`                       | `navigator.language` |
| `tz`          | `America/New_York`            | IANA timezone — geography proxy, no IP |
| `session_id`  | `k3x9p2m5a1lq4jx`             | Ephemeral random, resets on every page load. Not persisted. |
| `created_at`  | `2026-04-10 23:44:12.978+00`  | Server-assigned |

---

## Common queries

### Daily unique visitors (ephemeral session ids)

```sql
SELECT
  date_trunc('day', created_at) AS day,
  COUNT(*)                       AS page_views,
  COUNT(DISTINCT session_id)     AS unique_sessions
FROM public.page_views
WHERE created_at > now() - interval '30 days'
GROUP BY 1
ORDER BY 1 DESC;
```

### Top referrers (last 7 days)

```sql
SELECT
  COALESCE(NULLIF(referrer, ''), '(direct)') AS source,
  COUNT(*)                                    AS hits,
  COUNT(DISTINCT session_id)                  AS sessions
FROM public.page_views
WHERE created_at > now() - interval '7 days'
GROUP BY 1
ORDER BY hits DESC
LIMIT 20;
```

### Mobile vs desktop split (last 7 days)

```sql
SELECT
  CASE
    WHEN screen_w IS NULL          THEN 'unknown'
    WHEN screen_w < 768            THEN 'mobile'
    WHEN screen_w < 1200           THEN 'tablet'
    ELSE                                'desktop'
  END AS device,
  COUNT(*) AS hits
FROM public.page_views
WHERE created_at > now() - interval '7 days'
GROUP BY 1
ORDER BY hits DESC;
```

### Top timezones (geography proxy, last 30 days)

```sql
SELECT tz, COUNT(*) AS hits
FROM public.page_views
WHERE created_at > now() - interval '30 days'
  AND tz IS NOT NULL
GROUP BY tz
ORDER BY hits DESC
LIMIT 15;
```

### Language split

```sql
SELECT
  split_part(lang, '-', 1) AS base_lang,
  COUNT(*)                 AS hits,
  COUNT(DISTINCT session_id) AS sessions
FROM public.page_views
WHERE lang IS NOT NULL
GROUP BY 1
ORDER BY hits DESC
LIMIT 10;
```

### First / most recent visit

```sql
SELECT MIN(created_at) AS first_hit, MAX(created_at) AS latest_hit, COUNT(*) AS total
FROM public.page_views;
```

---

## Weekly cycle snippet (for feedback-loops cycles)

Drop this into a learnings row once per week:

```sql
WITH weekly AS (
  SELECT
    COUNT(*)                                              AS views,
    COUNT(DISTINCT session_id)                            AS sessions,
    COUNT(DISTINCT COALESCE(NULLIF(referrer, ''), '(direct)')) AS sources,
    COUNT(*) FILTER (WHERE screen_w < 768)                AS mobile_views
  FROM public.page_views
  WHERE created_at > now() - interval '7 days'
)
SELECT * FROM weekly;
```

---

## Known gaps

- **No rate limiting.** A motivated actor could flood inserts. Acceptable for MVP; revisit if a malicious spike shows up. Mitigation path: Supabase edge function that signs requests, or a `CHECK (char_length(user_agent) < 512)` + per-session rate cap trigger.
- **No bot filtering.** Googlebot, curl probes, and headless browsers all increment the counter. Query-time filter on `user_agent ILIKE '%bot%'` is crude but works.
- **No retention policy.** The table will grow without bound. Add a monthly cron once data volume matters:
  ```sql
  DELETE FROM page_views WHERE created_at < now() - interval '1 year';
  ```
- **Not deployed yet.** GitHub Pages serves `docs/` — the tracking script will not start collecting data until the next `origin/master` push is picked up by Pages (usually a minute or two).
