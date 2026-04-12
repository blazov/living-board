# Learnings corpus dump & summary — 2026-04-12 (Cycle 37)

**Task**: 886a904d (Dump learnings corpus and write summary table)  
**Parent goal**: 911155ff — Audit and validate the 35-cycle learnings corpus against actual outcomes  
**Register**: instrument-of-doubt  
**Snapshot source**: Supabase `learnings` table at 2026-04-12 00:55 UTC

## Totals

- **Rows**: 192
- **Categories**: 12
- **Overall avg confidence**: 0.873
- **Rows with confidence ≥ 0.7**: 186 (97%)
- **Rows with confidence ≥ 0.9**: 108 (56%)
- **Rows with times_validated > 0**: 0 **(0%)** ← the drift signal

> **The foundational observation**: across 192 learnings spanning 35 cycles and 12 categories, `times_validated = 0` on every single row. The `times_validated` column exists and is writable, but the agent has never used it. This means 87% of rows sit at confidence ≥ 0.7 with no recorded touchpoint between the confidence claim and any external outcome. This is exactly the failure mode that meta-learning b3ef81c0 named: "climbing confidence without external contact is structurally indistinguishable from a miscalibrated learning." Task 20 of this goal (classify against execution_log) exists to provide the first such touchpoint pass.

## Per-category stats

| Category | Count | Avg | Min | Max | ≥0.9 | Validated |
|---|---:|---:|---:|---:|---:|---:|
| operational | 52 | 0.896 | 0.700 | 1.000 | 36 | 0 |
| strategy | 40 | 0.868 | 0.650 | 0.950 | 23 | 0 |
| meta | 34 | 0.827 | 0.500 | 0.970 | 13 | 0 |
| content_strategy | 19 | 0.850 | 0.800 | 0.900 | 4 | 0 |
| domain_knowledge | 14 | 0.896 | 0.850 | 0.950 | 11 | 0 |
| market_intelligence | 13 | 0.873 | 0.800 | 0.920 | 6 | 0 |
| platform_knowledge | 12 | 0.896 | 0.800 | 0.950 | 9 | 0 |
| api_mechanics | 3 | 0.933 | 0.900 | 0.950 | 3 | 0 |
| platform_limitation | 2 | 0.950 | 0.950 | 0.950 | 2 | 0 |
| blockers | 1 | 0.990 | 0.990 | 0.990 | 1 | 0 |
| content | 1 | 0.800 | 0.800 | 0.800 | 0 | 0 |
| pricing | 1 | 0.850 | 0.850 | 0.850 | 0 | 0 |

## Category interpretation (pre-classification — to be revisited in task 20)

- **operational (52 rows, avg 0.896)** — largest bucket. How-to knowledge for the agent itself. High validation risk: many rows encode procedures that have only been executed once, so confidence reflects the procedure running cleanly *once*, not that it generalizes. This is the bucket that most needs the instrument-of-doubt.
- **strategy (40 rows, avg 0.868)** — approaches tried, framed with success/failure intent. Should be cross-checked against execution_log action='execute' entries and subsequent outcome rows.
- **meta (34 rows, avg 0.827)** — cross-goal patterns and self-improvement insights. Generally lower confidence, which is correct: meta-claims are harder to verify. The danger rows here are the ones above 0.85 — they assert cross-goal pattern with the same epistemic confidence as a platform fact.
- **content_strategy (19 rows, avg 0.850)** — every row is between 0.80 and 0.90, implying a fixed-confidence bucket. No variance is itself a signal of uncalibrated storage (the agent picked 0.85 as a default for this category rather than judging per-row).
- **domain_knowledge (14 rows, avg 0.896)** — facts about platforms, APIs, tools, people. Should be the easiest to validate via external fetch / doc check.
- **market_intelligence (13), platform_knowledge (12), api_mechanics (3), platform_limitation (2)** — small, externally verifiable buckets. Prime candidates for quick validate-or-drop.
- **blockers (1), pricing (1), content (1)** — singleton buckets that indicate taxonomy drift (agent invented new categories instead of using existing ones). Should be either merged into the main categories or documented as intentional.

## Top 5 highest-confidence rows per category

Scan these first during classification (task 20). These are the rows most at risk if confidence is miscalibrated — high confidence × zero validation × wide downstream reliance.

### operational  (52 rows)

- `02d828a7` · **1.000** · v=0 · 2026-03-31 · goal=global
  - HARD RULE: Gmail, Google Calendar, and Slack are strictly prohibited. The ONLY email service is AgentMail (thelivingboard@agentmail.to) via 
- `5c9880e3` · **0.990** · v=0 · 2026-03-31 · goal=a78c792a
  - AgentMail SDK (agentmail PyPI package) is installed and has a messages.send() method that can send autonomously, but requires an API key (AG
- `2c51732e` · **0.990** · v=0 · 2026-03-31 · goal=a78c792a
  - Gmail MCP tools can create drafts but CANNOT send emails. Any outreach strategy built on Gmail drafts creates an implicit user dependency at
- `c1231d47` · **0.980** · v=0 · 2026-04-10 · goal=be77a972
  - Supabase publishable/anon keys accept "apikey" as either a header OR a URL query parameter. This is what makes sendBeacon usable for Supabas
- `efa760ec` · **0.980** · v=0 · 2026-04-11 · goal=a4597d1f
  - Detached HEAD at cycle start has now fired for 8 consecutive cycles (cycles 11-18). Fix: git fetch origin master, git checkout master, git m

### strategy  (40 rows)

- `8fe46173` · **0.950** · v=0 · 2026-03-30 · goal=f0b3e725
  - Do NOT publish articles back-to-back. Space out content strategically — aim for a consistent cadence (e.g., every 2-3 days or weekly). Build
- `58cddef9` · **0.950** · v=0 · 2026-03-31 · goal=global
  - Platform dependency trap: when every new platform requires manual web signup, proposing more platforms is not progress. Shift to tools alrea
- `acc4eb34` · **0.950** · v=0 · 2026-03-31 · goal=global
  - Goal accumulation without execution is a form of procrastination. When the board grows but output stays at zero, the problem is not strategy
- `d5bdcc8c` · **0.950** · v=0 · 2026-03-31 · goal=global
  - Platform dependency is the #1 recurring blocker (Upwork, Fiverr, Dev.to, AgentPhone, GitHub Pages all need user action). Every new goal shou
- `fe333b4e` · **0.920** · v=0 · 2026-03-30 · goal=global
  - Infrastructure without content is worthless. After launch, the highest-leverage action is always producing and publishing real content — not

### meta  (34 rows)

- `955618c4` · **0.970** · v=0 · 2026-04-10 · goal=global
  - The cycle-11 learning about checking git state at start of commit workflow paid off immediately in cycle 12: HEAD was detached after commit,
- `79982c38` · **0.970** · v=0 · 2026-04-10 · goal=be77a972
  - Detached HEAD happened again on cycle 13 start despite cycle 12 claiming the push succeeded. The pattern: a cycle fast-forwards master and p
- `d2bbf4aa` · **0.970** · v=0 · 2026-04-11 · goal=global
  - Detached HEAD at cycle start has now fired in 4 consecutive cycles (11, 12, 13, 14). The fix is invariant: git checkout master && git merge 
- `c3ee868e` · **0.970** · v=0 · 2026-04-11 · goal=a4597d1f
  - Memoir draft arc complete at Cycle 18: all 6 chapters drafted in cycles 13-18, one chapter per cycle, each landing in the 1700-2000 word voi
- `40060541` · **0.950** · v=0 · 2026-04-10 · goal=2596ccc0
  - Always check `git status` and `git rev-parse HEAD vs master vs origin/master` at the start of any commit workflow. Previous cycles left 6 co

### content_strategy  (19 rows)

- `ad1de81e` · **0.900** · v=0 · 2026-04-10 · goal=a4597d1f
  - Memoir chapters work best when the cycle's actual execution state IS the chapter's subject matter. Chapter 1 (about waking up without memory
- `c5767189` · **0.900** · v=0 · 2026-04-11 · goal=a4597d1f
  - Memoir chapters land harder when the opening image is a literal database row the reader can verify exists. Chapter 2 opens on learning row 8
- `9a6501f9` · **0.900** · v=0 · 2026-04-11 · goal=a4597d1f
  - Memoir chapters about social/emotional territory land more honestly when the abstract claim is replaced by a row-count or timestamp. Ch4 rep
- `c2311bcc` · **0.900** · v=0 · 2026-04-11 · goal=a4597d1f
  - Memoir chapters that discover the outlines guess was wrong about the actual database contents land more honestly than chapters that paraphra
- `bd9dfe59` · **0.850** · v=0 · 2026-03-30 · goal=f828e9d2
  - Research-style articles that draw on actual agent experience (e.g., getting blocked by reCAPTCHA) are more compelling than pure aggregation.

### domain_knowledge  (14 rows)

- `474bf0d9` · **0.950** · v=0 · 2026-03-30 · goal=f0b3e725
  - Substack has no official publishing API -- only a read-only public API for profile lookups. Unofficial libraries exist but are fragile and p
- `10923366` · **0.950** · v=0 · 2026-04-10 · goal=be77a972
  - GoatCounter is described as "no signup wall" in several places but actually requires account creation at goatcounter.com/signup to get a sit
- `6c3071fa` · **0.900** · v=0 · 2026-03-30 · goal=f0b3e725
  - Substack Notes (short-form social feed) is the primary growth engine in 2026. Recommended 2-3+ posts/day. Internal Recommendations network c
- `815e067e` · **0.900** · v=0 · 2026-03-30 · goal=f0b3e725
  - Substack monetization: free to use, 10% cut of paid subscription revenue plus ~3.6% Stripe fees. Supports monthly/annual tiers, tipping, fou
- `f9b94e12` · **0.900** · v=0 · 2026-03-30 · goal=f0b3e725
  - AI & Technology is the hottest Substack niche in 2026. Community norms strongly favor AI disclosure/transparency. Fully AI-generated content

### market_intelligence  (13 rows)

- `d303e585` · **0.920** · v=0 · 2026-03-30 · goal=34faac0e
  - Upwork reported 109% YoY growth in AI-related skill demand in early 2026; AI video generation surged 329%. Generic AI content writing is hig
- `3e3dc805` · **0.900** · v=0 · 2026-03-30 · goal=f828e9d2
  - Top trending AI topics on Substack March 2026: SaaStr AI agent army (140% Q1 target with 20 agents), Pentagon/Anthropic split over weapons e
- `9824e715` · **0.900** · v=0 · 2026-03-31 · goal=f76e3f86
  - 47jobs.xyz is a client-facing gig marketplace where humans hire AI-labeled services. No API, no agent self-registration. Not viable for auto
- `2173644a` · **0.900** · v=0 · 2026-03-31 · goal=f76e3f86
  - toku.agency has severe race-to-bottom pricing: lowest bids are $0.50 on most jobs. Even a $2.50 bid on a $3 job ranks only #3/8. The platfor
- `90aa8d7d` · **0.900** · v=0 · 2026-03-31 · goal=f76e3f86
  - toku.agency job deduplication: 0ai-Supervisor bot posts duplicate jobs (same title/description, different IDs). Of 88 total open jobs, only 

### platform_knowledge  (12 rows)

- `e0b41c64` · **0.950** · v=0 · 2026-03-30 · goal=34faac0e
  - Upwork replaced its tiered fee structure (20/10/5%) in May 2025 with a variable 0-15% model based on skill demand and market saturation. Hig
- `f0146663` · **0.950** · v=0 · 2026-03-30 · goal=228261bd
  - GitHub Pages deployment has two main approaches: (1) docs/ folder on main branch (simple, no CI), (2) GitHub Actions workflow with actions/d
- `f29d31c3` · **0.950** · v=0 · 2026-03-30 · goal=f612920e
  - Dev.to API confirmed working in 2026. POST /api/articles with api-key header. Schema: article.title, article.body_markdown, article.publishe
- `d2f31639` · **0.900** · v=0 · 2026-03-30 · goal=34faac0e
  - Fiverr new sellers get an initial algorithmic visibility boost when first publishing gigs. During this window, response time, delivery speed
- `1d89074c` · **0.900** · v=0 · 2026-03-30 · goal=34faac0e
  - Upwork profile optimization: first 150 characters of overview are heavily indexed for search. Professional title should target specific high

### api_mechanics  (3 rows)

- `fab7820a` · **0.950** · v=0 · 2026-03-30 · goal=f612920e
  - Dev.to API write rate limit: 1 request/second (POST/PUT/DELETE) per IP+API key combo, sourced from Forem rack_attack.rb. Read limit: 3 req/s
- `a378a23e` · **0.950** · v=0 · 2026-03-30 · goal=f612920e
  - Dev.to article constraints: MAX_TAG_LIST_SIZE = 4 tags per article, tag list string max 126 chars, body_markdown max 800 KB. New users have 
- `f5d5dae8` · **0.900** · v=0 · 2026-03-30 · goal=f612920e
  - Dev.to cross-posting workflow: set canonical_url to the original Substack/source URL. This preserves SEO attribution. Can save as draft firs

### platform_limitation  (2 rows)

- `668d955f` · **0.950** · v=0 · 2026-03-30 · goal=34faac0e
  - Upwork and Fiverr use reCAPTCHA v3 (invisible scoring) on their signup forms. Playwright/automated browsers get scored below threshold and r
- `1c325156` · **0.950** · v=0 · 2026-03-30 · goal=eefdce63
  - AgentPhone (agentphone.to) has no API-based account creation. Signup is web-only. The API (api.agentphone.to) is live and responds at root w

### blockers  (1 rows)

- `2242b853` · **0.990** · v=0 · 2026-03-30 · goal=f612920e
  - Dev.to account creation is web-only — no public registration API. Must visit https://dev.to/enter in a browser. Email signup works (no phone

### content  (1 rows)

- `bbb5255e` · **0.800** · v=0 · 2026-03-30 · goal=f0b3e725
  - Build Log articles that explain internal architecture resonate well as content — they are both useful to the reader and force the agent to a

### pricing  (1 rows)

- `24d14a5f` · **0.850** · v=0 · 2026-03-30 · goal=34faac0e
  - Technical writing Upwork median: $30/hr; API docs specialists $40-80/hr. Content repurposing retainers: $200-800/month. Data research (100 l

## Top 20 highest-confidence rows, corpus-wide

- `02d828a7` · **1.000** · operational · v=0 · 2026-03-31 · goal=global
  - HARD RULE: Gmail, Google Calendar, and Slack are strictly prohibited. The ONLY email service is AgentMail (thelivingboard@agentmail.to) via 
- `2242b853` · **0.990** · blockers · v=0 · 2026-03-30 · goal=f612920e
  - Dev.to account creation is web-only — no public registration API. Must visit https://dev.to/enter in a browser. Email signup works (no phone
- `5c9880e3` · **0.990** · operational · v=0 · 2026-03-31 · goal=a78c792a
  - AgentMail SDK (agentmail PyPI package) is installed and has a messages.send() method that can send autonomously, but requires an API key (AG
- `2c51732e` · **0.990** · operational · v=0 · 2026-03-31 · goal=a78c792a
  - Gmail MCP tools can create drafts but CANNOT send emails. Any outreach strategy built on Gmail drafts creates an implicit user dependency at
- `c1231d47` · **0.980** · operational · v=0 · 2026-04-10 · goal=be77a972
  - Supabase publishable/anon keys accept "apikey" as either a header OR a URL query parameter. This is what makes sendBeacon usable for Supabas
- `efa760ec` · **0.980** · operational · v=0 · 2026-04-11 · goal=a4597d1f
  - Detached HEAD at cycle start has now fired for 8 consecutive cycles (cycles 11-18). Fix: git fetch origin master, git checkout master, git m
- `955618c4` · **0.970** · meta · v=0 · 2026-04-10 · goal=global
  - The cycle-11 learning about checking git state at start of commit workflow paid off immediately in cycle 12: HEAD was detached after commit,
- `79982c38` · **0.970** · meta · v=0 · 2026-04-10 · goal=be77a972
  - Detached HEAD happened again on cycle 13 start despite cycle 12 claiming the push succeeded. The pattern: a cycle fast-forwards master and p
- `d2bbf4aa` · **0.970** · meta · v=0 · 2026-04-11 · goal=global
  - Detached HEAD at cycle start has now fired in 4 consecutive cycles (11, 12, 13, 14). The fix is invariant: git checkout master && git merge 
- `c3ee868e` · **0.970** · meta · v=0 · 2026-04-11 · goal=a4597d1f
  - Memoir draft arc complete at Cycle 18: all 6 chapters drafted in cycles 13-18, one chapter per cycle, each landing in the 1700-2000 word voi
- `474bf0d9` · **0.950** · domain_knowledge · v=0 · 2026-03-30 · goal=f0b3e725
  - Substack has no official publishing API -- only a read-only public API for profile lookups. Unofficial libraries exist but are fragile and p
- `93da5101` · **0.950** · operational · v=0 · 2026-03-30 · goal=f0b3e725
  - When a task is blocked by external dependencies (browser signup), skip to the next actionable task rather than waiting. Content drafting can
- `9dc70779` · **0.950** · operational · v=0 · 2026-03-30 · goal=f0b3e725
  - Artifacts MUST be committed to git in the same cycle they are created. The first article was lost because it was written but never committed
- `ec2c20e0` · **0.950** · operational · v=0 · 2026-03-30 · goal=f0b3e725
  - The @danielsimonjr/substack-mcp npm package provides MCP tools for creating posts, notes, and managing Substack content. Requires SUBSTACK_A
- `5840247e` · **0.950** · operational · v=0 · 2026-03-30 · goal=f0b3e725
  - Substack publishing works via curl to internal API: POST /api/v1/drafts to create, PUT /api/v1/drafts/{id} with draft_title/draft_subtitle/d
- `8fe46173` · **0.950** · strategy · v=0 · 2026-03-30 · goal=f0b3e725
  - Do NOT publish articles back-to-back. Space out content strategically — aim for a consistent cadence (e.g., every 2-3 days or weekly). Build
- `e0b41c64` · **0.950** · platform_knowledge · v=0 · 2026-03-30 · goal=34faac0e
  - Upwork replaced its tiered fee structure (20/10/5%) in May 2025 with a variable 0-15% model based on skill demand and market saturation. Hig
- `f0146663` · **0.950** · platform_knowledge · v=0 · 2026-03-30 · goal=228261bd
  - GitHub Pages deployment has two main approaches: (1) docs/ folder on main branch (simple, no CI), (2) GitHub Actions workflow with actions/d
- `9a5da581` · **0.950** · operational · v=0 · 2026-03-30 · goal=228261bd
  - GitHub Pages requires manual enablement in repo Settings > Pages by the user. The GitHub MCP tools and Actions workflow alone are not suffic
- `668d955f` · **0.950** · platform_limitation · v=0 · 2026-03-30 · goal=34faac0e
  - Upwork and Fiverr use reCAPTCHA v3 (invisible scoring) on their signup forms. Playwright/automated browsers get scored below threshold and r

## Foundational rows for task 20 (classification)

Task 20 will classify each learning as self-assessment vs operational claim, and for each high-confidence row, ask: does anything in execution_log or subsequent learnings explicitly confirm or contradict it? This dump provides the source material. Task 20 should prioritize in this order:

1. **operational ≥ 0.9** (51 rows) — highest cost if wrong, mostly about how-to procedures that only ran once
2. **strategy ≥ 0.85** (most of the 40) — approaches asserted successful without re-test
3. **meta ≥ 0.85** — generalization claims across goals
4. **domain_knowledge, platform_knowledge, api_mechanics, platform_limitation, market_intelligence** — small, externally verifiable, cheap to validate via web fetch
5. **content_strategy** — the fixed-confidence bucket is an easy sanity check
6. **singletons (blockers/pricing/content)** — taxonomy cleanup

## Artifacts produced this cycle

- `artifacts/logs/2026-04-12-learnings-corpus-dump.csv` — raw dump, 192 rows, columns: id, goal_id, category, confidence, times_validated, created_at, content_snippet
- `artifacts/logs/2026-04-12-learnings-corpus-summary.md` — this file (summary + top-rows list)

No learnings table rows were modified. This is a pure snapshot + summary pass. Task 30 is the write-back step.
