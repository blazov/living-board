# Docs Site Analytics — Query Runbook

**Source table:** `public.page_views`
**Writer:** All `docs/**/*.html` pages (inline `<script>` before closing `</body>`)
**Key:** Supabase anon key (publishable, hardcoded in each page — this is the designed use)
**Privacy model:** RLS permits `INSERT` and `SELECT` for `anon`. No cookies, no IP, no user agent, no cross-site tracking.

---

## What gets stored per visit

| Column        | Example                       | Notes |
|---------------|-------------------------------|-------|
| `path`        | `/`, `/index.html`            | Pathname + query string |
| `referrer`    | `https://news.ycombinator.com/` | `document.referrer`, null if direct |
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

## Adding tracking to new pages

When publishing a new docs page, add this snippet before the closing `</body>` tag:

```html
<script>
  (function () {
    try {
      var URL_BASE = 'https://ieekjkeayiclprdekxla.supabase.co/rest/v1/page_views';
      var KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...'; // anon key
      var sid = Math.random().toString(36).slice(2, 12) + Date.now().toString(36);
      var payload = {
        path: location.pathname + location.search,
        referrer: document.referrer || null,
        screen_w: (screen && screen.width) || null,
        screen_h: (screen && screen.height) || null,
        lang: navigator.language || null,
        tz: (Intl && Intl.DateTimeFormat().resolvedOptions().timeZone) || null,
        session_id: sid
      };
      var body = JSON.stringify(payload);
      var sent = false;
      if (navigator.sendBeacon) {
        try {
          var blob = new Blob([body], { type: 'application/json' });
          sent = navigator.sendBeacon(URL_BASE + '?apikey=' + encodeURIComponent(KEY), blob);
        } catch (e) { /* ignore */ }
      }
      if (!sent && window.fetch) {
        fetch(URL_BASE, {
          method: 'POST', keepalive: true, mode: 'cors',
          headers: {
            'apikey': KEY, 'Authorization': 'Bearer ' + KEY,
            'Content-Type': 'application/json', 'Prefer': 'return=minimal'
          },
          body: body
        }).catch(function () {});
      }
    } catch (e) { }
  })();
</script>
```

Copy the full anon key from any existing tracked page (e.g., `docs/index.html`). The snippet collects only: path, referrer, screen size, language, timezone, and an ephemeral session ID. No cookies, no IP, no user agent.

---

## Known gaps

- **No rate limiting.** A motivated actor could flood inserts. Acceptable for MVP; revisit if a malicious spike shows up. Mitigation path: Supabase edge function that signs requests, or a per-session rate cap trigger.
- **No bot filtering.** Without user_agent, bot detection is limited to heuristic approaches (screen size 0x0, missing lang/tz). Low priority at current traffic levels.
- **No retention policy.** The table will grow without bound. Add a monthly cron once data volume matters:
  ```sql
  DELETE FROM page_views WHERE created_at < now() - interval '1 year';
  ```
