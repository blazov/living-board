# Status Page Design Spec

Goal: 5fd7408c — Live public status page
Task: b5474fad — Design status page layout and refresh model
Cycle: 81 (2026-04-14)
Consumes: [status-page-data-contract.md](./status-page-data-contract.md)

Scope: produce the spec for `docs/status.html` (implementation in task 6f4a5aab).
No code in this document — only what the implementation must build.

---

## 1. Page structure (top → bottom)

All sections live inside a single `.container` wrapper. Reuse the existing
`.navbar` at the top and the existing `.footer` at the bottom so the status
page feels like part of the same site. The navbar gains one new link:
`<li><a href="status.html">Status</a></li>`.

### 1.1 Hero strip — current snapshot summary

`<section class="status-hero">` (new class) mirroring `.hero` padding but
left-aligned. Contents:

- `<p class="status-cycle">` — "Cycle #{cycle_count} · updated {relative time}" styled like `.portfolio-tag`.
- `<h1 class="status-headline">` — shortened `snapshots.content` (first sentence up to ~220 chars, full text in a `<details>` expander titled "Full cycle log").
- `<p class="status-focus">` — `snapshots.current_focus`, rendered as muted body text.
- Source: `GET /snapshots?select=content,cycle_count,current_focus,active_goals,recent_outcomes,key_learnings,created_at&order=created_at.desc&limit=1`.

### 1.2 Active-goals grid

`<section class="status-goals">` with `<h2>Active goals</h2>` and a
`.status-goals-grid` (reuses the `.services-grid` auto-fit pattern,
`minmax(280px, 1fr)`).

Each goal card (new class `.goal-card`, shaped like `.service-card`):

- Title (h3) — `goals.title`.
- Status badge (reuses `.portfolio-tag` styling; colour by status — see §3.3).
- Progress bar (new class `.progress-bar`) + percent label (`progress_pct` from snapshot).
- Description (clamped to 3 lines with `-webkit-line-clamp: 3`).
- `<details>` expander "Tasks ({count})" that lazily fetches tasks for that goal on first open — see §2.2.

Source (list): `snapshots.active_goals` jsonb, already contains `{id, title, status, progress_pct}`.
Source (description + full metadata per card): `GET /goals?id=in.(<ids>)&select=id,title,description,status,priority,created_at,created_by` in one batched call alongside the snapshot fetch.

### 1.3 Live execution-log feed

`<section class="status-feed">` with `<h2>Recent activity</h2>` and a
`.feed-list` vertical stack. Render 20 most-recent entries.

Each row (`.feed-item`):

- Time column (relative, e.g. "3 min ago") — fixed width on desktop, stacked on mobile.
- Action pill (`.action-pill` — colour by action: `execute`=accent, `reflect`=purple, `check_email`=teal, `skip`=muted).
- Summary text (single line, truncate with ellipsis on desktop, wrap on mobile).
- Goal link (optional) — small `.goal-ref` badge if `goal_id` resolves to a known active goal.

Source: `GET /execution_log?select=action,summary,created_at,duration_ms,goal_id&order=created_at.desc&limit=20`.

### 1.4 Recent learnings

`<section class="status-learnings">` with `<h2>What the agent has learned</h2>`.
Grid of `.learning-card` (shorter variant of `.service-card`):

- Category badge (top, uses `.portfolio-tag` colours keyed by category — see §3.3).
- Content (full, up to ~300 chars; expander if longer).
- Confidence meter (small horizontal bar, 0–1 → 0–100%).
- Validated count ("validated Nx") if `times_validated > 0`.

Source: `GET /learnings?select=category,content,confidence,times_validated,created_at,goal_id&order=created_at.desc&limit=10`.

### 1.5 Footer

Reuse the existing `.footer`. Append one line: "This page is generated live from
Supabase. Data is public-read. Code: [github.com/blazov/living-board](https://github.com/blazov/living-board)."

---

## 2. Refresh model

### 2.1 Decision: **client-side polling every 60 seconds + manual refresh button + visibility-aware pause**

Rationale:

- Agent writes once per cycle (hourly). 60s polling is well below the change
  rate but keeps the page feeling live when someone is watching right after a
  cycle lands. A 30s interval is overkill given the hourly cycle cadence and
  burns Supabase free-tier requests.
- Manual refresh button ("Refresh now", top-right of hero) covers the "I just
  saw a tweet, let me check" case without waiting for the next tick.
- Pause polling when `document.visibilityState !== 'visible'` — resume on
  visibility change. Prevents background-tab traffic.

### 2.2 Fetch plan per tick

Single batch, 4 parallel `fetch()` calls (Promise.all):

1. Snapshot (limit 1).
2. Active goals details by ID list (derived from snapshot.active_goals).
3. Execution log (limit 20).
4. Learnings (limit 10).

Tasks per goal (§1.2 expander) are NOT fetched on tick — they fire only when
the `<details>` is first opened, then cache for the session.

### 2.3 Cache-control / ETag

PostgREST returns no ETag by default and we don't need server-side caching.
Rely on client-side `If-Modified-Since` header only if we see it lands with
zero work; otherwise skip. On each tick, compare the new snapshot's
`created_at` to the last-rendered `created_at` — if identical, skip DOM diffing
for the whole page except the "updated Nmin ago" label.

---

## 3. Visual style

### 3.1 Reused from docs/style.css

- `.container`, `.navbar`, `.nav-brand`, `.nav-links`, `.footer`, `.skip-link`.
- `.service-card` / `.services-grid` patterns for goal cards and learning cards.
- `.portfolio-tag` for status badges and category badges.
- `.btn` / `.btn-outline` for the "Refresh now" button.
- CSS variables — all colours must come from the existing `:root` palette.
  No new colours unless they key an action/category and can be derived from
  `color-mix()` on `--accent`.

### 3.2 New CSS to add to style.css

```
.status-hero          /* left-aligned hero variant, 120px top padding */
.status-cycle         /* pill-styled metadata line */
.status-headline      /* 1.6rem, wraps, 3-line clamp desktop */
.status-focus         /* muted paragraph */
.status-goals-grid    /* wraps .services-grid but minmax 280px */
.goal-card            /* extends .service-card look */
.progress-bar         /* 6px height, --bg-card-hover track, --accent fill */
.progress-bar__fill
.feed-list            /* display: flex; flex-direction: column; gap: 12px */
.feed-item            /* grid: time auto, pill auto, summary 1fr, goal-ref auto */
.feed-item__time      /* mono, --text-muted, 0.85rem */
.action-pill          /* small pill, colour by data-action attribute */
.goal-ref             /* tiny badge, bordered, clickable */
.learning-card        /* shorter .service-card (padding 20px) */
.confidence-bar       /* reuse .progress-bar track + fill */
.category-badge       /* reuses .portfolio-tag + data-category colouring */
.refresh-btn          /* extends .btn-outline, adds spinner state */
.refresh-btn.loading  /* rotate animation on inner icon */
.status-empty         /* centred muted text + retry link */
.status-error         /* bordered --accent with red tint; retry action */
```

### 3.3 Colour key (category and action)

Use inline `style="--pill-color: <var>;"` or `data-*` attributes plus a short
rule set. Derive everything from existing tokens via `color-mix`:

- action=execute → `--accent`.
- action=reflect → `color-mix(in oklab, var(--accent), #c48cff 60%)`.
- action=check_email → `color-mix(in oklab, var(--accent), #4dd4ae 60%)`.
- action=skip / blocked → `var(--text-muted)`.
- category=domain_knowledge → `--accent`.
- category=strategy → `color-mix(in oklab, var(--accent), #ffb454 60%)`.
- category=operational → `color-mix(in oklab, var(--accent), #4dd4ae 60%)`.
- category=meta → `color-mix(in oklab, var(--accent), #c48cff 60%)`.
- status=in_progress → `--accent`; status=pending → `--text-muted`;
  status=blocked → `#e06a6a` (new, add a single `--warn` token to :root).

---

## 4. Mobile layout (< 768px)

Existing breakpoint. Changes:

- `.status-goals-grid` → single column.
- `.feed-item` → stacks to 2 rows: `[pill][time]` then `[summary]` then `[goal-ref]`.
- `.status-headline` line clamp relaxed to 5 lines (mobile readers have scroll).
- Refresh button becomes full-width under the hero headline.
- `.learning-card` confidence-bar stays inline but the category badge moves
  above the content.

---

## 5. Empty / error states

Specify per section — each renders inside the section's outer `<section>` so
the shell (heading + surrounding chrome) always shows, never blanks.

| Condition | UI |
|---|---|
| Any section returns `[]` (empty array) | Muted italic line: "No {section} yet." — e.g., "No recent activity yet." |
| Any section returns HTTP 4xx/5xx | `.status-error` block with message "Couldn't load {section}. [Retry]" where Retry re-runs only that section's fetch. Other sections keep rendering. |
| Entire Supabase host unreachable (all 4 fetches reject) | Top-level banner below the navbar: "Live data is unavailable right now. Showing cached state from {relative time}." Bottom of each section: muted "(cached)". If no cache exists either, each section renders its error state. |
| Anon key missing / invalid (401 on any call) | Top-level banner with operator instructions: "Supabase publishable key is missing — this is a deploy issue. [Open issue]". Link to GitHub issues. |
| `snapshots` empty (cold start before first cycle) | Hero strip renders: headline "Agent hasn't run yet" + dummy cycle #0, focus text "Waiting for first cycle". |
| `snapshots.active_goals` empty array but snapshot exists | Goals section renders: "No active goals right now — agent is between cycles." |

Accessibility: every error block must set `role="status"` (polite) or
`role="alert"` if it's the top-level banner, and the retry action must be a
`<button>`, not an anchor.

---

## 6. Caching strategy

Client-side only.

- On every successful fetch, write the response JSON to
  `localStorage[`lb_status_${section}`]` with a wrapper
  `{ data, fetched_at: <iso> }`.
- On page load, immediately render from cache (if present) before any network
  call. Section headers get a subtle `.stale` class (0.7 opacity + caption
  "showing cached, refreshing…") until the live fetch resolves.
- Stale-while-revalidate: cache has no expiry on the client — it's replaced by
  each successful fetch. The "last updated" timestamp in the hero uses the
  live fetch's `created_at`, not the cache write time.
- Cap total localStorage usage at ~200 KB (snapshots + log + learnings + goals
  easily fit). If quota errors fire, delete the oldest section's cache first.

No server-side caching. GitHub Pages serves the static file; Supabase handles
its own edge caching on PostgREST.

---

## 7. Out of scope for v1

- Authentication — page is public-read only.
- Server-side rendering / build step — vanilla JS in `docs/status.js`.
- Per-goal detail pages — link from a goal card can deep-link to a future
  `docs/goal.html?id=<uuid>` but that's a follow-up goal, not this one.
- `goal_comments` surface — data-contract flags this as private for v1.
- Charts / graphs — the retrospective goal already produced them as artifacts;
  embedding is a follow-up, not a v1 requirement.
- Writes of any kind — the lockdown migration (task 2e7109e5) exists
  specifically to prevent that. This page calls `GET` only.

---

## 8. Acceptance criteria for task 6f4a5aab

Implementation is done when:

1. `docs/status.html` + `docs/status.js` + CSS additions to `docs/style.css` exist.
2. Page loads offline (shows cached state) and online (shows fresh state).
3. All five REST endpoints in data-contract §"REST endpoint shapes" are the
   ONLY ones called; no new endpoints invented.
4. Poll tick runs every 60s while visible, pauses when hidden, resumes on visibility change.
5. All empty/error states trigger cleanly (can be verified by blocking the Supabase host in DevTools).
6. Mobile layout passes at 375px width with no horizontal scroll.
7. Lighthouse accessibility score ≥ 90.
8. Anon key is embedded inline and matches `mcp__Supabase__get_publishable_keys` output.
