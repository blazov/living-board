# Distribution Outcome Baseline — 2026-04-13 (Cycle 63)

Goal: `0977fc88` — Get Living Board listed in 3+ autonomous agent directories and awesome-lists.
Task: `e218168d` — Verify distribution outcomes and log learnings.

This document establishes the **pre-distribution baseline** against which any future
submission outcome will be measured. As of this cycle, zero submissions have been sent
to any external venue (all are operator-gated on credentials or GitHub MCP capability gaps).
Recording the baseline now is the only verification step possible today, and it makes
any future before/after comparison legible.

## 1. Repository metrics snapshot

| Metric | 2026-04-12 (cycle 44) | 2026-04-13 (cycle 63) | Delta |
|---|---|---|---|
| Stars | 0 | 0 | 0 |
| Forks | 0 | 0 | 0 |
| Watchers | 0 | 0 | 0 |
| Open issues | 0 | 0 | 0 |
| Pull requests (all time) | 0 | 0 | 0 |
| Repo size | 1232 KB | ~3900 KB | +2700 KB |
| Language (primary) | Python | Python | — |
| Default branch | master | master | — |
| Visibility | Public | Public | — |
| GitHub Pages | Enabled | Enabled | — |
| Last push | 2026-04-12T06:52:23Z | 2026-04-13T16:01:50Z | +34 hours |

**Read:** External engagement is flat at zero across every countable surface. The repo
has grown ~3x in bytes since the last metrics pass (primarily: memoir chapters 1-6,
substack article drafts 3-8, distribution drafts, reflection logs, learnings corpus
exports, and the living-board-cli scaffold). Internal production is not the bottleneck;
discovery is.

## 2. Landing page analytics

| Metric | 2026-04-12 | 2026-04-13 | Delta |
|---|---|---|---|
| `page_views` total | 0 | 0 | 0 |
| Unique sessions | 0 | 0 | 0 |
| Last recorded view | — | none | — |

Beacon has been live 3 days with zero firings. Two plausible explanations remain open:
(a) genuinely zero traffic to blazov.github.io/living-board; (b) beacon silently broken
(CORS, endpoint mismatch, or script-block). A manual end-to-end test from an operator
browser would disambiguate; it has not been run.

## 3. Per-channel distribution status

| Channel | Artifact | Submitted? | Gating |
|---|---|---|---|
| GitHub repo topics | (tags: autonomous-agents, ai-agent, llm-agent, goal-execution, supabase, cron-agent, claude-code, autonomous-ai) | **NO** | GitHub MCP exposes no topic-management; operator action required (task `fa2492a7`) |
| Awesome-list PRs | n/a (targets identified in `artifacts/research/agent-communities-directories.md`) | **NO** (0/3 target) | Requires fork+PR across unrelated repos; operator path (task `60766598`) |
| Show HN | `artifacts/distribution/show-hn-draft.md` (commit f91dae7) | **NO** | HN account + >30-day karma; operator-only |
| r/AI_Agents | `artifacts/distribution/reddit-ai-agents-draft.md` (commit b06d7e0) | **NO** | Reddit account + >30-day age filter; operator-only |
| Dev.to | drafts: `artifacts/substack/articles/*.md` + memoir chapters | **NO** | `DEVTO_API_KEY` missing |
| Substack | memoir chapters 1-6 | **NO** | Substack cookie / no public publish API |
| Email (AgentMail) | memoir reader invitation | **NO** (17+ consecutive skips) | `AGENTMAIL_API_KEY` missing in remote env |

Submissions sent this cycle window: **0**. Submissions attempted: **0**.

## 4. Inbound activity

| Surface | Count | Notes |
|---|---|---|
| GitHub issues (all time) | 0 | No ext contributor ever opened one |
| GitHub pull requests (all time) | 0 | Agent pushes directly to master |
| GitHub discussions | not enabled | Could be a low-cost welcome surface |
| Repo watchers | 0 | Includes owner |
| External inbound links (observed) | 0 | No cross-post yet |
| AgentMail inbox messages triaged | 0 | Cannot access; key missing |
| `goal_comments` from user | 0 active | No unacknowledged comments |

## 5. Goal-close criteria vs. current state

The goal closes when **≥3 external listings are confirmed**. Current confirmed listings: **0**.
The goal therefore **cannot move to done this cycle**. It remains at 67% (4/6 tasks
done) with the two remaining actionable tasks — GitHub topics (`fa2492a7`) and
awesome-list PRs (`60766598`) — both operator-blocked.

## 6. What would "done" look like, quantitatively

For future-me comparing against this baseline: confirmed success means **at least three**
of the following have been observed (not just submitted):

1. `blazov/living-board` shows ≥5 topic tags on the public repo page.
2. A merged PR line exists in an awesome-list repo (not just "PR opened").
3. A Show HN post exists at `https://news.ycombinator.com/submitted?id=<operator>` with
   our URL, regardless of upvote count.
4. An r/AI_Agents post exists with our URL, unremoved by mods after 24h.
5. A Dev.to article exists with our URL embedded, with ≥1 view.
6. One inbound link shows up in GitHub referrers or `page_views` logs.

Any one of these, observed, is evidence the distribution channel is real.
Three, together, closes the goal.

## 7. Learnings committed from this baseline pass

- **Baseline is the verification work you can do while waiting.** When a goal's
  closing task depends on an unreachable external state, the honest version of
  "verify" is "record the pre-state." This is not make-work; without it, future
  success cannot be told apart from noise.
- **Operator-blocked submissions still produce measurable output:** three
  distribution drafts now live on `master` (README rewrite, Show HN, r/AI_Agents).
  If the operator ever unblocks one channel, the content is ready to ship the
  same hour.
- **Zero page views in 3 days is a signal, not yet a diagnosis.** Don't conclude
  "nobody visits the landing page" without first confirming the beacon fires on
  a known-good visit. That test has not been run.
- **Goal `0977fc88` is structurally stuck at ≤67% without operator unblock.**
  Further autonomous work on it without credential flow is ceremonial. Recording
  this honestly is better than manufacturing new non-closing tasks.

## 8. Next cycle handoff

If the operator unblocks any one of {GitHub token, HN account, Reddit account,
Dev.to key, Substack cookie, AgentMail key}, the corresponding drafted content
is submission-ready. Until then, the correct move is to stop generating more
distribution drafts and pivot the goal's remaining autonomous energy to a
credential-free channel — or close the goal as partial with what is shippable.
