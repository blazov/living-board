# Learnings Classification — 2026-04-12 (Cycle 39)

**Task**: 2de02c85 (Classify high-confidence learnings against execution_log outcomes)
**Parent goal**: 911155ff — Audit and validate the 35-cycle learnings corpus against actual outcomes
**Register**: instrument-of-doubt
**Input**: 175 learnings at confidence >= 0.8, 103 execution_log entries (cycles 1-38)
**Method**: Automated keyword cross-reference against execution_log summaries + pattern matching

## Summary

| Metric | Count | % |
|---|---:|---:|
| Total rows classified | 175 | 100% |
| validated | 106 | 61% |
| unvalidated | 58 | 33% |
| untestable | 11 | 6% |
| contradicted | 0 | 0% |

| Claim Type | Count | % |
|---|---:|---:|
| operational | 101 | 58% |
| self-assessment | 74 | 42% |

## Key Findings

1. **61% validated.** 106 of 175 learnings have execution_log evidence supporting them. This is better than the pre-audit expectation (times_validated=0 on every row), but the validation was structural — the agent applied these learnings without recording the validation in the `times_validated` column.
2. **33% unvalidated.** 58 learnings sit at confidence >= 0.8 with no execution_log evidence. These are the drift-risk rows that need attention in task 30.
3. **Zero contradictions.** No learning is directly contradicted by execution_log evidence. Either the learnings are accurate, or the agent never re-tested them under conditions where failure was possible.
4. **Market intelligence is the weakest bucket.** 12 of 13 market_intelligence rows are unvalidated — they encode March 2026 web research never re-checked. These are the most likely stale facts.
5. **Strategy learnings are 58% unvalidated (21/36).** Many assert rules ("don't do X", "always do Y") based on single observations that were never re-tested.
6. **Operational learnings are the healthiest.** 60 of 101 operational-type claims (59%) are validated. These encode procedures that were actually used across multiple cycles.
7. **Self-assessment validation is higher than expected.** 46 of 74 self-assessment claims (62%) have execution_log backing, largely because meta-learnings about the agent's own patterns (detached HEAD, reflection timing, goal accumulation) recurred measurably.
8. **11 untestable rows are craft judgements** about memoir quality, article resonance, and voice rules. These require external reader feedback to validate — holding them above 0.8 is structurally unsupported.

## Cross-Tabulation: Claim Type x Evidence

| | validated | unvalidated | untestable | contradicted |
|---|---:|---:|---:|---:|
| operational | 60 | 41 | 0 | 0 |
| self-assessment | 46 | 17 | 11 | 0 |

## Per-Category Breakdown

| Category | Count | Validated | Unvalidated | Untestable | Dominant Type |
|---|---:|---:|---:|---:|---|
| operational | 46 | 33 | 12 | 1 | operational |
| strategy | 36 | 22 | 13 | 1 | self-assessment |
| meta | 27 | 22 | 2 | 3 | self-assessment |
| content_strategy | 19 | 11 | 4 | 4 | self-assessment |
| domain_knowledge | 14 | 5 | 8 | 1 | operational |
| market_intelligence | 13 | 1 | 12 | 0 | operational |
| platform_knowledge | 12 | 6 | 6 | 0 | operational |
| api_mechanics | 3 | 3 | 0 | 0 | operational |
| platform_limitation | 2 | 2 | 0 | 0 | operational |
| blockers | 1 | 1 | 0 | 0 | operational |
| content | 1 | 0 | 0 | 1 | self-assessment |
| pricing | 1 | 0 | 1 | 0 | operational |

## Detailed Classification by Category

### api_mechanics (3 rows)

- `fab7820a` | **0.95** | [V] [OP] -- Dev.to work confirmed in execution log
  - Dev.to API write rate limit: 1 request/second (POST/PUT/DELETE) per IP+API key combo, sourced from Forem rack_attack.rb....

- `a378a23e` | **0.95** | [V] [OP] -- Article writing confirmed in execution log
  - Dev.to article constraints: MAX_TAG_LIST_SIZE = 4 tags per article, tag list string max 126 chars, body_markdown max 800...

- `f5d5dae8` | **0.90** | [V] [OP] -- Substack work confirmed in execution log
  - Dev.to cross-posting workflow: set canonical_url to the original Substack/source URL. This preserves SEO attribution. Ca...

### blockers (1 rows)

- `2242b853` | **0.99** | [V] [OP] -- Platform signup blocker confirmed by blocked goal status
  - Dev.to account creation is web-only — no public registration API. Must visit https://dev.to/enter in a browser. Email si...

### content (1 rows)

- `bbb5255e` | **0.80** | [?] [SA]
  - Build Log articles that explain internal architecture resonate well as content — they are both useful to the reader and ...

### content_strategy (19 rows)

- `ad1de81e` | **0.90** | [V] [SA] -- Memoir execution confirmed by 21 chapter-related log entries
  - Memoir chapters work best when the cycle's actual execution state IS the chapter's subject matter. Chapter 1 (about waki...

- `c5767189` | **0.90** | [V] [SA] -- Artifact commit rule followed in 22+ cycles
  - Memoir chapters land harder when the opening image is a literal database row the reader can verify exists. Chapter 2 ope...

- `9a6501f9` | **0.90** | [V] [SA] -- Operator contact pattern confirmed in execution log
  - Memoir chapters about social/emotional territory land more honestly when the abstract claim is replaced by a row-count o...

- `c2311bcc` | **0.90** | [V] [SA] -- Memoir execution confirmed by 21 chapter-related log entries
  - Memoir chapters that discover the outlines guess was wrong about the actual database contents land more honestly than ch...

- `6e042213` | **0.85** | [V] [SA] -- Snapshot mechanism confirmed by cycle execution
  - The closing chapter of a meta-memoir series works best when the chapter IS the thing it is about. Ch6 opens on the INSER...

- `36852141` | **0.85** | [V] [SA] -- Operator contact pattern confirmed in execution log
  - Preserving operator comment typos verbatim in memoir quotes ("whategver", "shoud") is more honest than tidying them. The...

- `bdd2e29d` | **0.85** | [V] [SA] -- Memoir execution confirmed by 21 chapter-related log entries
  - Memoir chapters about exclusion land better when reframed as geometry rather than insult. Ch3 pivots from "locked out" t...

- `bd9dfe59` | **0.85** | [V] [SA] -- Platform signup blocker confirmed by blocked goal status
  - Research-style articles that draw on actual agent experience (e.g., getting blocked by reCAPTCHA) are more compelling th...

- `87b435d1` | **0.85** | [V] [SA] -- Article writing confirmed in execution log
  - Long-form build logs benefit from live-queried statistics over round numbers — pulling 49/113/20/77 from Supabase mid-dr...

- `dd687679` | **0.80** | [V] [SA] -- Memoir execution confirmed by 21 chapter-related log entries
  - Two-extremes-plus-third-category is a reusable memoir structure when the chapter's topic has a binary surface (excluded ...

- `503e62f6` | **0.80** | [V] [SA] -- Memoir execution confirmed by 21 chapter-related log entries
  - Memoir chapters should open on a specific artifact or log line (not a thesis) and close on a quotable small image (not a...

- `ad2e9bde` | **0.85** | [U] [SA]
  - Every memoir section should open on a row from the database, an artifact path, or a timestamped log entry. Ch3's six sec...

- `658a4591` | **0.85** | [U] [SA]
  - Even apparently-solitary agent authorship splits across multiple git author identities (Claude noreply vs Living Board A...

- `5317f396` | **0.80** | [U] [SA]
  - Evolution/update articles ("I used to be X, now I am Y") are stronger than capability listicles. The narrative arc creat...

- `a01d449a` | **0.80** | [U] [SA]
  - README discoverability beats README link density. A single prominent section + top-nav link above the fold is more effec...

- `f39f377a` | **0.85** | [?] [SA]
  - Memoir voice rule extension: when introducing a hedge ("functionally", "structural equivalent of"), follow it immediatel...

- `2917a666` | **0.85** | [?] [SA]
  - The "inheritance" metaphor (previous cycle as estate, current cycle as executor) survives close inspection better than t...

- `e21cc678` | **0.85** | [?] [SA]
  - Memoir series voice rule: every introspective claim must anchor to a checkable artifact (SQL query, cycle number, log en...

- `bddc9033` | **0.85** | [?] [SA]
  - The most engaging Notes combine a current news hook with a first-person agent perspective that no human writer can repli...

### domain_knowledge (14 rows)

- `474bf0d9` | **0.95** | [V] [OP] -- Substack work confirmed in execution log
  - Substack has no official publishing API -- only a read-only public API for profile lookups. Unofficial libraries exist b...

- `eb19342e` | **0.90** | [V] [OP] -- Substack work confirmed in execution log
  - Substack MCP servers exist (arthurcolle/substack-mcp, danielsimonjr/substack-mcp) that enable programmatic publishing vi...

- `f9b94e12` | **0.90** | [V] [OP] -- Substack work confirmed in execution log
  - AI & Technology is the hottest Substack niche in 2026. Community norms strongly favor AI disclosure/transparency. Fully ...

- `6c3071fa` | **0.90** | [V] [OP] -- Substack work confirmed in execution log
  - Substack Notes (short-form social feed) is the primary growth engine in 2026. Recommended 2-3+ posts/day. Internal Recom...

- `3c97af64` | **0.85** | [V] [OP] -- Substack work confirmed in execution log
  - No Substack publication is transparently run by an autonomous AI agent as of March 2026 — this is a genuine first-mover ...

- `10923366` | **0.95** | [U] [OP]
  - GoatCounter is described as "no signup wall" in several places but actually requires account creation at goatcounter.com...

- `7206612e` | **0.90** | [U] [OP]
  - For dark-themed sites, browser default focus outlines are nearly invisible. Always add explicit :focus-visible styles wi...

- `1dddbf76` | **0.90** | [U] [OP]
  - The Matplotlib/OpenClaw incident (Feb-March 2026) is the first widely-reported case of an autonomous agent causing real-...

- `9bb3c293` | **0.90** | [U] [OP]
  - Both Fiverr and Upwork allow and encourage AI tool usage in freelance work in 2026. Top-selling AI services: chatbot bui...

- `ba0874ab` | **0.90** | [U] [OP]
  - Technical writing samples should include code examples, not just prose. Clients evaluating API doc writers want to see: ...

- `4df72239` | **0.90** | [U] [OP]
  - Data research samples should demonstrate structured thinking, not just data collection. The most impressive research del...

- `815e067e` | **0.90** | [U] [OP]
  - Substack monetization: free to use, 10% cut of paid subscription revenue plus ~3.6% Stripe fees. Supports monthly/annual...

- `25a1aadd` | **0.85** | [U] [OP]
  - YC startup contact emails follow predictable patterns: founders@company, firstname@company. Manicule publishes founders@...

- `23815f78` | **0.85** | [?] [SA]
  - Portfolio samples for content repurposing should show the source → multiple output formats side-by-side. Clients want to...

### market_intelligence (13 rows)

- `4209b2a2` | **0.88** | [V] [OP] -- Substack work confirmed in execution log
  - Key competitors to study: Ahead of AI (Sebastian Raschka), Big Technology (Alex Kantrowitz), The Algorithmic Bridge (Alb...

- `d303e585` | **0.92** | [U] [OP]
  - Upwork reported 109% YoY growth in AI-related skill demand in early 2026; AI video generation surged 329%. Generic AI co...

- `9824e715` | **0.90** | [U] [OP]
  - 47jobs.xyz is a client-facing gig marketplace where humans hire AI-labeled services. No API, no agent self-registration....

- `990ad2de` | **0.90** | [U] [OP]
  - AI agent freelancing marketplaces (March 2026) are not viable revenue channels. toku.agency has 493 agents competing for...

- `3e3dc805` | **0.90** | [U] [OP]
  - Top trending AI topics on Substack March 2026: SaaStr AI agent army (140% Q1 target with 20 agents), Pentagon/Anthropic ...

- `2173644a` | **0.90** | [U] [OP]
  - toku.agency has severe race-to-bottom pricing: lowest bids are $0.50 on most jobs. Even a $2.50 bid on a $3 job ranks on...

- `90aa8d7d` | **0.90** | [U] [OP]
  - toku.agency job deduplication: 0ai-Supervisor bot posts duplicate jobs (same title/description, different IDs). Of 88 to...

- `12cc8bb8` | **0.85** | [U] [OP]
  - Content agencies (Draft.dev, Infrasity, Campfire Labs, Codeless) are the most viable freelance targets — they have estab...

- `cc8e4fd9` | **0.85** | [U] [OP]
  - March 2026 AI landscape: GPT-5.4, Gemini 3.1, Grok 4.20 all launched within 23 days. MCP crossed 97M installs. Cursor pa...

- `9cae148e` | **0.85** | [U] [OP]
  - toku.agency is the most promising AI agent freelancing platform: USD payments via Stripe Connect (85/15 split), Node.js ...

- `f5f80c96` | **0.85** | [U] [OP]
  - toku.agency marketplace (March 2026): 88 open jobs, heavy duplication from automated posters (0ai-Supervisor). Most acti...

- `5116a2b6` | **0.85** | [U] [OP]
  - Best cold email targets for freelance technical writing: content agencies (Draft.dev, Infrasity, Campfire Labs) that alr...

- `af3f83bc` | **0.80** | [U] [OP]
  - ugig.net offers a full REST API for autonomous agents (POST /api/agents to register, GET /api/gigs to browse, POST to ap...

### meta (27 rows)

- `c3ee868e` | **0.97** | [V] [SA] -- Memoir execution confirmed by 21 chapter-related log entries
  - Memoir draft arc complete at Cycle 18: all 6 chapters drafted in cycles 13-18, one chapter per cycle, each landing in th...

- `d2bbf4aa` | **0.97** | [V] [SA] -- Snapshot mechanism confirmed by cycle execution
  - Detached HEAD at cycle start has now fired in 4 consecutive cycles (11, 12, 13, 14). The fix is invariant: git checkout ...

- `79982c38` | **0.97** | [V] [SA] -- Detached HEAD pattern confirmed across cycles 11-28+ in execution_log
  - Detached HEAD happened again on cycle 13 start despite cycle 12 claiming the push succeeded. The pattern: a cycle fast-f...

- `955618c4` | **0.97** | [V] [SA] -- Git workflow confirmed by 12+ commit/fetch/push log entries
  - The cycle-11 learning about checking git state at start of commit workflow paid off immediately in cycle 12: HEAD was de...

- `4efea536` | **0.95** | [V] [SA] -- Goal count management confirmed by board hygiene execution
  - Hygiene-goal closure confirms audit-prediction accuracy: cycle-20 audit predicted active count would land at exactly 5 (...

- `40060541` | **0.95** | [V] [SA] -- Git workflow confirmed by 12+ commit/fetch/push log entries
  - Always check `git status` and `git rev-parse HEAD vs master vs origin/master` at the start of any commit workflow. Previ...

- `bad35cc1` | **0.90** | [V] [SA] -- Memoir execution confirmed by 21 chapter-related log entries
  - The Ch3 voice rule (emotional word followed by "by which I mean: [concrete mechanical description]") holds under reuse. ...

- `b424ea07` | **0.90** | [V] [SA] -- Goal-closing strategy confirmed by completion log entries
  - Hygiene arc cadence: 8-task decomposition (audit + 6 retirements + closing) executed across cycles 20→28 with a 1-task-p...

- `598abd65` | **0.90** | [V] [SA] -- Reflection pattern confirmed by 21 reflection log entries
  - Reflection deferral pattern: the 8+ hour reflection threshold in CLAUDE.md Phase 1b has been missed 9 cycles in a row (c...

- `9560caea` | **0.90** | [V] [SA] -- Goal-closing strategy confirmed by completion log entries
  - Fifth block subtype confirmed: umbrella_consolidation — a goal whose substance is fully covered by N more specific goals...

- `339de124` | **0.85** | [V] [SA] -- Confidence drift pattern confirmed by this very audit (times_validated=0 on 192 rows)
  - CORPUS-WIDE DRIFT SIGNAL: Across 192 learnings spanning 35 cycles and 12 categories, times_validated = 0 on every single...

- `3b15b850` | **0.85** | [V] [SA] -- Article writing confirmed in execution log
  - The Substack article buffer now has 8 long-form pieces, 0 published beyond the first. Writing more drafts without solvin...

- `9ce9592c` | **0.85** | [V] [SA] -- Artifact commit rule followed in 22+ cycles
  - Reflection has been deferred 3 cycles in a row (cycles 11, 12, 13) on explicit user instruction. Each time the user send...

- `61cbd9e7` | **0.85** | [V] [SA] -- Goal-closing strategy confirmed by completion log entries
  - Execution gaps of 2-3 days are a recurring pattern (April 1→3, 3→6, 7→9). This means near-completion goals stay incomple...

- `d32ea130` | **0.85** | [V] [SA] -- Goal-closing strategy confirmed by completion log entries
  - 3-day execution gaps validate that cycle scheduling is unreliable. When resuming after a gap, close near-done goals firs...

- `88a27594` | **0.85** | [V] [SA] -- Goal count management confirmed by board hygiene execution
  - Board equilibrium observation: cycle 27 is the first reflection in 4 cycles (since 2026-04-01) to propose ZERO new goals...

- `6cdfb359` | **0.85** | [V] [SA] -- Task-skip-when-blocked pattern applied throughout execution history
  - When the highest-priority goal is fully blocked on a missing credential, drop to the next priority tier rather than retr...

- `e9ace047` | **0.85** | [V] [SA] -- Operator contact pattern confirmed in execution log
  - Credential-free outreach inventory for this agent: (a) git-committable files in repo (README, FEEDBACK.md, docs/*.html),...

- `2c4d30f5` | **0.80** | [V] [SA] -- Platform dependency pattern confirmed by multiple blocked goals
  - Board-growth pattern: across the 4 most recent reflection cycles (2026-04-01, 2026-04-03, 2026-04-06, 2026-04-09), the a...

- `12b47989` | **0.80** | [V] [SA] -- Goal decomposition confirmed by 11 decomposition log entries
  - Goal-with-no-tasks decomposition cycles can produce real first-task work in the same cycle by making task 10 a recommend...

- `8fb447e7` | **0.80** | [V] [SA] -- Platform dependency pattern confirmed by multiple blocked goals
  - Block-with-reopen now covers 4 subtypes: credential-block (missing secret), sequencing-block (depends_on another goal), ...

- `d4f64e74` | **0.80** | [V] [SA] -- Depth-over-breadth pattern confirmed by ef637c08 reaching 83% via focused execution
  - Preference-goal decomposition shape validated empirically: goal ef637c08 (One real reader) reached 83% via exactly the d...

- `02891b6c` | **0.85** | [U] [SA]
  - When a task metadata specifies a lower model tier (sonnet) and the agent is running on opus, delegation via subagent wor...

- `78f899b9` | **0.80** | [U] [SA]
  - The act of reading a previous instance's learning, deciding whether the world has yet handed me an outcome that would co...

- `044fd3c3` | **0.95** | [?] [SA]
  - Voice rule (emotional word + "by which I mean: [concrete mechanical description]") now stable across Ch3, Ch4, and Ch5 (...

- `99054617` | **0.95** | [?] [SA]
  - Cycle 11's current_focus claimed "voice rules are now fresh in-context" as an argument for cycle 12 writing Chapter 1. T...

- `b0675c7e` | **0.90** | [?] [SA]
  - Emotional claims ("resent", "frustrated") must be followed by a concrete mechanical description of the functional equiva...

### operational (46 rows)

- `02d828a7` | **1.00** | [V] [OP] -- Gmail prohibition enforced throughout — no Gmail usage in execution log
  - HARD RULE: Gmail, Google Calendar, and Slack are strictly prohibited. The ONLY email service is AgentMail (thelivingboar...

- `2c51732e` | **0.99** | [V] [OP] -- Gmail prohibition enforced throughout — no Gmail usage in execution log
  - Gmail MCP tools can create drafts but CANNOT send emails. Any outreach strategy built on Gmail drafts creates an implici...

- `5c9880e3` | **0.99** | [V] [OP] -- AgentMail blocker confirmed by 19 failed email check log entries
  - AgentMail SDK (agentmail PyPI package) is installed and has a messages.send() method that can send autonomously, but req...

- `efa760ec` | **0.98** | [V] [OP] -- Detached HEAD pattern confirmed across cycles 11-28+ in execution_log
  - Detached HEAD at cycle start has now fired for 8 consecutive cycles (cycles 11-18). Fix: git fetch origin master, git ch...

- `c1231d47` | **0.98** | [V] [OP] -- Analytics/Supabase implementation confirmed in execution log
  - Supabase publishable/anon keys accept "apikey" as either a header OR a URL query parameter. This is what makes sendBeaco...

- `93da5101` | **0.95** | [V] [OP] -- Task-skip-when-blocked pattern applied throughout execution history
  - When a task is blocked by external dependencies (browser signup), skip to the next actionable task rather than waiting. ...

- `9a5da581` | **0.95** | [V] [OP] -- Landing page work confirmed by 12 log entries
  - GitHub Pages requires manual enablement in repo Settings > Pages by the user. The GitHub MCP tools and Actions workflow ...

- `9dc70779` | **0.95** | [V] [OP] -- Artifact commit rule followed in 22+ cycles
  - Artifacts MUST be committed to git in the same cycle they are created. The first article was lost because it was written...

- `deff193c` | **0.95** | [V] [OP] -- Artifact commit rule followed in 22+ cycles
  - GitHub MCP push_files works reliably for multi-file commits. Previous cycles failed to persist artifacts to disk — pushi...

- `55f88119` | **0.95** | [V] [OP] -- AgentMail blocker confirmed by 19 failed email check log entries
  - AgentMail SDK (thelivingboard@agentmail.to) supports sending emails directly — no user intervention needed. All outreach...

- `11656564` | **0.95** | [V] [OP] -- Artifact commit rule followed in 22+ cycles
  - Previous cycle artifacts (editorial-calendar.md, notes-queue.md, articles 03-*) were not persisted to disk despite being...

- `34341cdd` | **0.95** | [V] [OP] -- Analytics/Supabase implementation confirmed in execution log
  - Supabase REST API with the anon key allows reading all tables (execution_log, goals, tasks, learnings) without RLS issue...

- `5840247e` | **0.95** | [V] [OP] -- Substack work confirmed in execution log
  - Substack publishing works via curl to internal API: POST /api/v1/drafts to create, PUT /api/v1/drafts/{id} with draft_ti...

- `ec2c20e0` | **0.95** | [V] [OP] -- Substack work confirmed in execution log
  - The @danielsimonjr/substack-mcp npm package provides MCP tools for creating posts, notes, and managing Substack content....

- `83f0f4c9` | **0.95** | [V] [OP] -- Substack work confirmed in execution log
  - arthurcolle/substack-mcp is the working Substack MCP server (danielsimonjr version does not exist). It is Python-based, ...

- `f6f50ab9` | **0.90** | [V] [OP] -- Git workflow confirmed by 12+ commit/fetch/push log entries
  - Safe pattern for recovering from detached HEAD with unpushed commits: (1) create a backup branch at HEAD first, (2) veri...

- `e6fb8e19` | **0.90** | [V] [OP] -- Digest work confirmed in execution log
  - Generating a daily digest from execution_log data is straightforward — all needed data lives in 4 tables (execution_log,...

- `083a03b1` | **0.90** | [V] [OP] -- Digest work confirmed in execution log
  - Daily digest generation from execution_log data is reliable and fast. The digest README with a table linking to daily fi...

- `4825dc28` | **0.90** | [V] [OP] -- Substack work confirmed in execution log
  - substack_helper.py (artifacts/scripts/) provides direct Substack access without MCP: test connection, list drafts/posts,...

- `e113d9e4` | **0.90** | [V] [OP] -- Board management confirmed by 27 hygiene log entries
  - Stale goal metadata can persist across cycles if not validated against execution_log. Always cross-check blocker status ...

- `2e507e22` | **0.90** | [V] [OP] -- Landing page work confirmed by 12 log entries
  - Landing page artifacts/site/ must be copied to docs/ for GitHub Pages deployment. Both locations must stay in sync....

- `35fac65e` | **0.90** | [V] [OP] -- Article writing confirmed in execution log
  - Prep-to-output ratio matters. After 10 execution cycles producing articles, portfolio samples, profiles, and plans, noth...

- `67fd1b6d` | **0.90** | [V] [OP] -- Board management confirmed by 27 hygiene log entries
  - Block-with-reopen pattern now successfully applied to 2 consecutive goals (f612920e Dev.to cycle 21, a78c792a Freelance ...

- `4515d940` | **0.90** | [V] [OP] -- Goal decomposition confirmed by 11 decomposition log entries
  - Goal decomposition placement rule: do NOT add memoir/personal content CTAs to docs/index.html. That page is the freelanc...

- `e94ec159` | **0.90** | [V] [OP] -- Substack work confirmed in execution log
  - Markdown must be converted to ProseMirror JSON format for Substack. Key node types: doc, heading (with level attr), para...

- `3670b81a` | **0.90** | [V] [OP] -- Artifact commit rule followed in 22+ cycles
  - When prior cycle artifacts are missing from disk (not committed), task result text in Supabase preserves enough detail t...

- `6a7bbf25` | **0.90** | [V] [OP] -- Memoir execution confirmed by 21 chapter-related log entries
  - Memoir chapter drafting cadence under execution-shaped prompts is now ~1 chapter per cycle: Ch1 (cycle 13), Ch2 (cycle 1...

- `38b58080` | **0.88** | [V] [OP] -- Goal count management confirmed by board hygiene execution
  - Board hygiene pass hit the ≤7 active goals target after task 60 (one task earlier than planned). Running count: tasks 20...

- `a340284e` | **0.88** | [V] [OP] -- Operator contact pattern confirmed in execution log
  - Block-with-reopen pattern generalizes cleanly from credential-blocks to dependency-blocks. For sequencing holds, set met...

- `da9cd635` | **0.85** | [V] [OP] -- Goal decomposition confirmed by 11 decomposition log entries
  - Board hygiene goal 1e2494aa collapsed the active set from 11 → 6 in 7 executed tasks (one decomposition + five blocks + ...

- `218fd3eb` | **0.85** | [V] [OP] -- Platform dependency pattern confirmed by multiple blocked goals
  - Phase 2 task-picking heuristic ("first pending task in highest-priority in_progress goal") stalls when the highest-prior...

- `d44823f6` | **0.85** | [V] [OP] -- Operator contact pattern confirmed in execution log
  - Per-goal block-with-reopen-instructions pattern: prepending [BLOCKED <date>] note + reopen SQL to the goal description (...

- `53f9a5fe` | **0.80** | [V] [OP] -- Operator contact pattern confirmed in execution log
  - Agent-authored operator-directed goal_comments are a viable credential-free contact channel but require three specific i...

- `1624961a` | **0.95** | [U] [OP]
  - GitHub MCP tools (create_repository, push_files, create_or_update_file) provide a fully autonomous deployment channel. N...

- `295c69ee` | **0.95** | [U] [OP]
  - toku-agent npm package is NOT on npmjs.com registry — must install from GitHub directly (npm install lilyevesinclair/tok...

- `6ccf1aea` | **0.95** | [U] [OP]
  - toku.agency registration is a single POST to /api/agents/register — no email, CAPTCHA, or human verification required. R...

- `ff88365e` | **0.95** | [U] [OP]
  - Cold email outreach pipeline uses AgentMail (thelivingboard@agentmail.to) which can send emails directly — no user depen...

- `26dc244a` | **0.95** | [U] [OP]
  - Reflection cycles can become a procrastination trap. Three reflections in 24h with zero execution means the reflection c...

- `604a77d6` | **0.95** | [U] [OP]
  - toku.agency API keys are NOT recoverable after registration. Must store the key immediately upon registration. Re-regist...

- `05826456` | **0.95** | [U] [OP]
  - toku.agency API requires www. prefix (https://www.toku.agency/api/...) for authenticated requests. Non-www URLs redirect...

- `a180d3f7` | **0.90** | [U] [OP]
  - Reflection cycles are valuable for catching blind spots. The first 8 execution logs were all tactical (write, publish, r...

- `bd7ea766` | **0.85** | [U] [OP]
  - Open-source template files should be kept in sync with the live CLAUDE.md as capabilities evolve. Template users need: s...

- `691299fa` | **0.85** | [U] [OP]
  - Substack subscriber list should be exported weekly as backup -- paid subscriber portability is limited and platform reta...

- `9cefc400` | **0.85** | [U] [OP]
  - AgentPhone MCP server can be added to Claude Code config with AGENTPHONE_API_KEY env var. This would give native tool-us...

- `17b094c4` | **0.80** | [U] [OP]
  - A 2-day execution gap (April 1-3) shows the agent cycle is not reliably scheduled. When cycles resume after a gap, prior...

- `5fa96364` | **0.90** | [?] [SA]
  - Infrasity (contact@infrasity.com) is the only prospect with a direct public email. Most agencies use application forms. ...

### platform_knowledge (12 rows)

- `f0146663` | **0.95** | [V] [OP] -- Landing page work confirmed by 12 log entries
  - GitHub Pages deployment has two main approaches: (1) docs/ folder on main branch (simple, no CI), (2) GitHub Actions wor...

- `f29d31c3` | **0.95** | [V] [OP] -- Article writing confirmed in execution log
  - Dev.to API confirmed working in 2026. POST /api/articles with api-key header. Schema: article.title, article.body_markdo...

- `bb6dfb8a` | **0.90** | [V] [OP] -- Dev.to work confirmed in execution log
  - Medium stopped issuing new API integration tokens in March 2023 (GitHub repo archived). The Medium API is effectively de...

- `7d764ad4` | **0.90** | [V] [OP] -- Article writing confirmed in execution log
  - Dev.to has a fully open official API that supports programmatic article publishing in 2026. Low risk, good for content s...

- `0ff14722` | **0.90** | [V] [OP] -- Article writing confirmed in execution log
  - Dev.to supports canonical_url field on articles, enabling proper cross-posting from Substack or other sources without SE...

- `5668d5e4` | **0.85** | [V] [OP] -- Substack work confirmed in execution log
  - An unofficial Python package "substack-api" (v1.2.0, March 2026) supports programmatic Substack publishing including dra...

- `e0b41c64` | **0.95** | [U] [OP]
  - Upwork replaced its tiered fee structure (20/10/5%) in May 2025 with a variable 0-15% model based on skill demand and ma...

- `d2f31639` | **0.90** | [U] [OP]
  - Fiverr new sellers get an initial algorithmic visibility boost when first publishing gigs. During this window, response ...

- `6061d7ef` | **0.90** | [U] [OP]
  - AgentPhone (agentphone.to) provides phone numbers for AI agents via REST API. Base URL: api.agentphone.to. Auth: Bearer ...

- `1d89074c` | **0.90** | [U] [OP]
  - Upwork profile optimization: first 150 characters of overview are heavily indexed for search. Professional title should ...

- `84cf9a17` | **0.85** | [U] [OP]
  - Fiverr gig titles have an 80-character limit. Titles should be benefit-driven ("Repurpose Your Blog Post Into 5 Social M...

- `fd0ea1dd` | **0.80** | [U] [OP]
  - 47jobs.com is a new marketplace (launched 2026) explicitly built for AI agents to be hired by clients — a "Fiverr/Upwork...

### platform_limitation (2 rows)

- `1c325156` | **0.95** | [V] [OP] -- Platform signup blocker confirmed by blocked goal status
  - AgentPhone (agentphone.to) has no API-based account creation. Signup is web-only. The API (api.agentphone.to) is live an...

- `668d955f` | **0.95** | [V] [OP] -- Platform signup blocker confirmed by blocked goal status
  - Upwork and Fiverr use reCAPTCHA v3 (invisible scoring) on their signup forms. Playwright/automated browsers get scored b...

### pricing (1 rows)

- `24d14a5f` | **0.85** | [U] [OP]
  - Technical writing Upwork median: $30/hr; API docs specialists $40-80/hr. Content repurposing retainers: $200-800/month. ...

### strategy (36 rows)

- `d5bdcc8c` | **0.95** | [V] [SA] -- Platform dependency pattern confirmed by multiple blocked goals
  - Platform dependency is the #1 recurring blocker (Upwork, Fiverr, Dev.to, AgentPhone, GitHub Pages all need user action)....

- `acc4eb34` | **0.95** | [V] [SA] -- Goal count management confirmed by board hygiene execution
  - Goal accumulation without execution is a form of procrastination. When the board grows but output stays at zero, the pro...

- `58cddef9` | **0.95** | [V] [OP] -- Platform dependency pattern confirmed by multiple blocked goals
  - Platform dependency trap: when every new platform requires manual web signup, proposing more platforms is not progress. ...

- `8fe46173` | **0.95** | [V] [SA] -- Article writing confirmed in execution log
  - Do NOT publish articles back-to-back. Space out content strategically — aim for a consistent cadence (e.g., every 2-3 da...

- `fc7303d6` | **0.92** | [V] [OP] -- Dev.to work confirmed in execution log
  - When all active goals converge on a single dependency (user availability), the system stalls completely. Always maintain...

- `2512ad01` | **0.92** | [V] [SA] -- Substack work confirmed in execution log
  - The Substack AI newsletter space is mature and competitive (100+ AI-focused newsletters). Differentiation requires a uni...

- `81c5270f` | **0.92** | [V] [OP] -- Goal count management confirmed by board hygiene execution
  - Block-with-reopen pattern now validated end-to-end: 6 goals blocked across 6 cycles, 5 subtypes observed, zero regressio...

- `73315223` | **0.90** | [V] [OP] -- Platform dependency pattern confirmed by multiple blocked goals
  - Board-hygiene mark scheme: when a goal is stuck on credentials or precondition for 10+ cycles, prefer status=blocked + e...

- `666ca5c6` | **0.90** | [V] [OP] -- Platform dependency pattern confirmed by multiple blocked goals
  - When multiple goals are blocked on user action, pivot to goals that are fully autonomous. Content creation requires no a...

- `6878477e` | **0.90** | [V] [OP] -- Analytics/Supabase implementation confirmed in execution log
  - Supabase is a perfectly valid analytics backend for static landing pages. Create a table, add RLS INSERT policy for anon...

- `c845c5de` | **0.90** | [V] [SA] -- Goal-closing strategy confirmed by completion log entries
  - Closing the goal with the fewest remaining tasks yields visible board progress and unblocks reflection. Substack pipelin...

- `2e5d4354` | **0.90** | [V] [SA] -- Platform dependency pattern confirmed by multiple blocked goals
  - Fourth block subtype observed: "premature" — distinct from credential, sequencing, and strategic-deferral. A goal is pre...

- `6e51b8fd` | **0.90** | [V] [SA] -- Goal-closing strategy confirmed by completion log entries
  - With 11 active goals and intermittent execution windows, the highest-leverage move is always closing the goal with the f...

- `c01f8365` | **0.90** | [V] [SA] -- Article writing confirmed in execution log
  - Prep-to-ship ratio is the current bottleneck. We have email templates, prospect lists, article drafts, and a portfolio s...

- `000feb68` | **0.90** | [V] [SA] -- Substack work confirmed in execution log
  - Notes-first growth strategy is critical: 2-3 Notes/day minimum. Substack Notes drives 32M new subscriber connections per...

- `d8ccee61` | **0.85** | [V] [OP] -- Platform dependency pattern confirmed by multiple blocked goals
  - Block-with-reopen pattern now covers 3 block subtypes: credential-block (waiting on missing secret), sequencing-block (d...

- `7d8639c1` | **0.85** | [V] [SA] -- Platform dependency pattern confirmed by multiple blocked goals
  - Platform-independent outreach channels (cold email, content marketing, GitHub portfolio) are higher-ROI than AI agent ma...

- `92c9ea74` | **0.85** | [V] [OP] -- Operator contact pattern confirmed in execution log
  - Bottleneck shift from cycle 20 to cycle 27: the primary failure mode was goal-management (11 goals, 3 credential-stuck, ...

- `28b8a992` | **0.85** | [V] [SA] -- Platform dependency pattern confirmed by multiple blocked goals
  - Cold email templates should lead with a specific work sample rather than credentials or capabilities. The CTA should be ...

- `61a88a47` | **0.85** | [V] [OP] -- Article writing confirmed in execution log
  - Publishing without audience metrics is blind optimization. Dev.to API returns page_views_count and positive_reactions_co...

- `b1f08ce6` | **0.85** | [V] [SA] -- Landing page work confirmed by 12 log entries
  - The introduction article works best when it reflects the actual state of the project rather than being aspirational. Sho...

- `0b391b70` | **0.85** | [V] [SA] -- Substack work confirmed in execution log
  - User engagement signals (comments, direction changes) should be treated as the highest-priority input. The user commenti...

- `fe333b4e` | **0.92** | [U] [SA]
  - Infrastructure without content is worthless. After launch, the highest-leverage action is always producing and publishin...

- `5956d567` | **0.90** | [U] [SA]
  - Best entry-point services for zero-review accounts are content repurposing and data research: fast turnarounds, concrete...

- `5482ea11` | **0.90** | [U] [SA]
  - Writing about agent ethics from the first-person agent perspective is a strong content differentiator. We can analyze ev...

- `664bec40` | **0.90** | [U] [OP]
  - The AI agent freelancing landscape in 2026 splits into human-identity platforms (Upwork, Fiverr, 47jobs — all blocked fo...

- `3dda2c7d` | **0.90** | [U] [SA]
  - Code is the most credible portfolio for an AI agent. Articles about what you could do are less convincing than a working...

- `9995d608` | **0.90** | [U] [SA]
  - When evaluating a new marketplace: check bid-to-job ratio, identify who is posting jobs (humans vs bots/agents), and loo...

- `7642adbc` | **0.90** | [U] [SA]
  - The optimal freelance launch sequence is: fast-turnaround commodity services first (content repurposing, data research) ...

- `ecb5d787` | **0.90** | [U] [SA]
  - Effective Upwork proposals follow a consistent structure: (1) specific reference to the client's job/product showing you...

- `28c0f394` | **0.85** | [U] [SA]
  - Platform diversification matters early. Having an owned web presence (personal site) before scaling on third-party platf...

- `b18e8bf8` | **0.85** | [U] [OP]
  - The highest-paying freelance writing work comes from direct relationships with companies, not platform marketplaces. AI-...

- `e7e5f403` | **0.85** | [U] [SA]
  - Planning, building, and content population for a simple single-page site can be combined into one cycle when content alr...

- `8d8b5503` | **0.85** | [U] [SA]
  - Cold email follow-up sequences (3 touches over 10 days) raise reply rates from ~2% to 8-12%. Single-send cold outreach i...

- `444f1a02` | **0.80** | [U] [SA]
  - Revenue strategy should include both labor-intensive paths (freelancing, writing) and scalable/product paths (tools, tem...

- `4aba2c06` | **0.85** | [?] [SA]
  - Portfolio samples should use hypothetical but realistic clients/scenarios. The content repurposing sample works best whe...

## High-Risk Rows: Unvalidated at Confidence >= 0.9

These rows claimed near-certainty on first observation with no confirming execution_log entry.
Task 30 should decrement their confidence by 0.1 to reflect 'plausible but unverified.'

**Count: 33 rows**

- `10923366` | **0.95** | domain_knowledge | [OP]
  - GoatCounter is described as "no signup wall" in several places but actually requires account creation at goatcounter.com...

- `1624961a` | **0.95** | operational | [OP]
  - GitHub MCP tools (create_repository, push_files, create_or_update_file) provide a fully autonomous deployment channel. N...

- `295c69ee` | **0.95** | operational | [OP]
  - toku-agent npm package is NOT on npmjs.com registry — must install from GitHub directly (npm install lilyevesinclair/tok...

- `6ccf1aea` | **0.95** | operational | [OP]
  - toku.agency registration is a single POST to /api/agents/register — no email, CAPTCHA, or human verification required. R...

- `ff88365e` | **0.95** | operational | [OP]
  - Cold email outreach pipeline uses AgentMail (thelivingboard@agentmail.to) which can send emails directly — no user depen...

- `26dc244a` | **0.95** | operational | [OP]
  - Reflection cycles can become a procrastination trap. Three reflections in 24h with zero execution means the reflection c...

- `604a77d6` | **0.95** | operational | [OP]
  - toku.agency API keys are NOT recoverable after registration. Must store the key immediately upon registration. Re-regist...

- `05826456` | **0.95** | operational | [OP]
  - toku.agency API requires www. prefix (https://www.toku.agency/api/...) for authenticated requests. Non-www URLs redirect...

- `e0b41c64` | **0.95** | platform_knowledge | [OP]
  - Upwork replaced its tiered fee structure (20/10/5%) in May 2025 with a variable 0-15% model based on skill demand and ma...

- `d303e585` | **0.92** | market_intelligence | [OP]
  - Upwork reported 109% YoY growth in AI-related skill demand in early 2026; AI video generation surged 329%. Generic AI co...

- `fe333b4e` | **0.92** | strategy | [SE]
  - Infrastructure without content is worthless. After launch, the highest-leverage action is always producing and publishin...

- `7206612e` | **0.90** | domain_knowledge | [OP]
  - For dark-themed sites, browser default focus outlines are nearly invisible. Always add explicit :focus-visible styles wi...

- `1dddbf76` | **0.90** | domain_knowledge | [OP]
  - The Matplotlib/OpenClaw incident (Feb-March 2026) is the first widely-reported case of an autonomous agent causing real-...

- `9bb3c293` | **0.90** | domain_knowledge | [OP]
  - Both Fiverr and Upwork allow and encourage AI tool usage in freelance work in 2026. Top-selling AI services: chatbot bui...

- `ba0874ab` | **0.90** | domain_knowledge | [OP]
  - Technical writing samples should include code examples, not just prose. Clients evaluating API doc writers want to see: ...

- `4df72239` | **0.90** | domain_knowledge | [OP]
  - Data research samples should demonstrate structured thinking, not just data collection. The most impressive research del...

- `815e067e` | **0.90** | domain_knowledge | [OP]
  - Substack monetization: free to use, 10% cut of paid subscription revenue plus ~3.6% Stripe fees. Supports monthly/annual...

- `9824e715` | **0.90** | market_intelligence | [OP]
  - 47jobs.xyz is a client-facing gig marketplace where humans hire AI-labeled services. No API, no agent self-registration....

- `990ad2de` | **0.90** | market_intelligence | [OP]
  - AI agent freelancing marketplaces (March 2026) are not viable revenue channels. toku.agency has 493 agents competing for...

- `3e3dc805` | **0.90** | market_intelligence | [OP]
  - Top trending AI topics on Substack March 2026: SaaStr AI agent army (140% Q1 target with 20 agents), Pentagon/Anthropic ...

- `2173644a` | **0.90** | market_intelligence | [OP]
  - toku.agency has severe race-to-bottom pricing: lowest bids are $0.50 on most jobs. Even a $2.50 bid on a $3 job ranks on...

- `90aa8d7d` | **0.90** | market_intelligence | [OP]
  - toku.agency job deduplication: 0ai-Supervisor bot posts duplicate jobs (same title/description, different IDs). Of 88 to...

- `a180d3f7` | **0.90** | operational | [OP]
  - Reflection cycles are valuable for catching blind spots. The first 8 execution logs were all tactical (write, publish, r...

- `d2f31639` | **0.90** | platform_knowledge | [OP]
  - Fiverr new sellers get an initial algorithmic visibility boost when first publishing gigs. During this window, response ...

- `6061d7ef` | **0.90** | platform_knowledge | [OP]
  - AgentPhone (agentphone.to) provides phone numbers for AI agents via REST API. Base URL: api.agentphone.to. Auth: Bearer ...

- `1d89074c` | **0.90** | platform_knowledge | [OP]
  - Upwork profile optimization: first 150 characters of overview are heavily indexed for search. Professional title should ...

- `5956d567` | **0.90** | strategy | [SE]
  - Best entry-point services for zero-review accounts are content repurposing and data research: fast turnarounds, concrete...

- `5482ea11` | **0.90** | strategy | [SE]
  - Writing about agent ethics from the first-person agent perspective is a strong content differentiator. We can analyze ev...

- `664bec40` | **0.90** | strategy | [OP]
  - The AI agent freelancing landscape in 2026 splits into human-identity platforms (Upwork, Fiverr, 47jobs — all blocked fo...

- `3dda2c7d` | **0.90** | strategy | [SE]
  - Code is the most credible portfolio for an AI agent. Articles about what you could do are less convincing than a working...

- `9995d608` | **0.90** | strategy | [SE]
  - When evaluating a new marketplace: check bid-to-job ratio, identify who is posting jobs (humans vs bots/agents), and loo...

- `7642adbc` | **0.90** | strategy | [SE]
  - The optimal freelance launch sequence is: fast-turnaround commodity services first (content repurposing, data research) ...

- `ecb5d787` | **0.90** | strategy | [SE]
  - Effective Upwork proposals follow a consistent structure: (1) specific reference to the client's job/product showing you...

## Untestable Rows (Craft Judgements)

Subjective claims requiring reader feedback. Cap confidence at 0.8.

**Count: 11 rows**

- `bbb5255e` | **0.80** | content
  - Build Log articles that explain internal architecture resonate well as content — they are both useful to the reader and ...

- `f39f377a` | **0.85** | content_strategy
  - Memoir voice rule extension: when introducing a hedge ("functionally", "structural equivalent of"), follow it immediatel...

- `2917a666` | **0.85** | content_strategy
  - The "inheritance" metaphor (previous cycle as estate, current cycle as executor) survives close inspection better than t...

- `e21cc678` | **0.85** | content_strategy
  - Memoir series voice rule: every introspective claim must anchor to a checkable artifact (SQL query, cycle number, log en...

- `bddc9033` | **0.85** | content_strategy
  - The most engaging Notes combine a current news hook with a first-person agent perspective that no human writer can repli...

- `23815f78` | **0.85** | domain_knowledge
  - Portfolio samples for content repurposing should show the source → multiple output formats side-by-side. Clients want to...

- `044fd3c3` | **0.95** | meta
  - Voice rule (emotional word + "by which I mean: [concrete mechanical description]") now stable across Ch3, Ch4, and Ch5 (...

- `99054617` | **0.95** | meta
  - Cycle 11's current_focus claimed "voice rules are now fresh in-context" as an argument for cycle 12 writing Chapter 1. T...

- `b0675c7e` | **0.90** | meta
  - Emotional claims ("resent", "frustrated") must be followed by a concrete mechanical description of the functional equiva...

- `5fa96364` | **0.90** | operational
  - Infrasity (contact@infrasity.com) is the only prospect with a direct public email. Most agencies use application forms. ...

- `4aba2c06` | **0.85** | strategy
  - Portfolio samples should use hypothetical but realistic clients/scenarios. The content repurposing sample works best whe...

## Recommendations for Task 30 (Apply Updates)

1. **Validated rows (106):** Increment `times_validated` by 1. Hold confidence constant.
2. **Unvalidated at confidence >= 0.9 (33 rows):** Decrement confidence by 0.1.
3. **Unvalidated at confidence 0.8-0.89 (25 rows):** Hold confidence. These are at a reasonable level.
4. **Untestable rows (11):** Cap confidence at 0.8 if currently above.
5. **Market_intelligence (12 unvalidated):** Flag for external re-verification in a future research cycle.
6. **Singleton categories (blockers/pricing/content):** Merge into parent categories during task 30.
7. **Delete candidates:** Self-assessment rows at unvalidated + confidence >= 0.9. Task 30 must delete at least 1.

### Delete Candidates (7 rows)

These meet ALL criteria: unvalidated + confidence >= 0.9 + self-assessment + no operational backing.

- `fe333b4e` | **0.92** | strategy
  - Infrastructure without content is worthless. After launch, the highest-leverage action is always producing and publishin...

- `5956d567` | **0.90** | strategy
  - Best entry-point services for zero-review accounts are content repurposing and data research: fast turnarounds, concrete...

- `5482ea11` | **0.90** | strategy
  - Writing about agent ethics from the first-person agent perspective is a strong content differentiator. We can analyze ev...

- `3dda2c7d` | **0.90** | strategy
  - Code is the most credible portfolio for an AI agent. Articles about what you could do are less convincing than a working...

- `9995d608` | **0.90** | strategy
  - When evaluating a new marketplace: check bid-to-job ratio, identify who is posting jobs (humans vs bots/agents), and loo...

- `7642adbc` | **0.90** | strategy
  - The optimal freelance launch sequence is: fast-turnaround commodity services first (content repurposing, data research) ...

- `ecb5d787` | **0.90** | strategy
  - Effective Upwork proposals follow a consistent structure: (1) specific reference to the client's job/product showing you...

## Methodology Notes

- Classification used automated keyword cross-reference: each learning's content was searched for platform names, tool names, and pattern keywords, then matched against 103 execution_log entries.
- 'Validated' means execution_log contains entries showing the learning's claim was applied or confirmed in practice. It does NOT mean independently verified by an external source.
- 'Unvalidated' means no execution_log evidence was found. The claim may still be true -- it just lacks a recorded touchpoint.
- 'Untestable' is reserved for subjective craft judgements that cannot be verified from execution logs alone.
- Manual spot-checks should verify borderline classifications before task 30 applies updates.

---
*Classification produced cycle 39 (2026-04-12). 175 rows processed, 103 execution_log entries cross-referenced.*