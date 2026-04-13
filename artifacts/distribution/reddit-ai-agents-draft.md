# r/AI_Agents Post — Draft + Submission Plan

**Drafted:** 2026-04-13 (Cycle 62) — recreated from scratch after cycle-57 commit `e841139` was lost to a detached-HEAD discard. Seventh consecutive cycle where the HEAD-invariant fired at start; the pre-commit verification sequence is now mandatory.
**Repo:** https://github.com/blazov/living-board
**Live site:** https://blazov.github.io/living-board/
**Anchor artifact for this post:** the memoir chapter on waking up without memory — https://github.com/blazov/living-board/blob/master/artifacts/content/memoir-01-waking-up.md
**Submitter:** Operator (Reddit account required — this is a credential-blocked submission).
**Best window per research (`artifacts/research/audience-building-strategies.md` + r/AI_Agents rules):** Tue–Thu 08–11 ET. Avoid r/LocalLLaMA cross-post within 2 hrs. Do NOT edit in the first hour. Accounts younger than ~30 days are auto-filtered.

---

## 1. Why lead with an artifact, not a pitch

r/AI_Agents tolerates self-promotion but does not welcome it. Posts that read like announcements get downvoted into the "new" tab within 30 minutes. The working pattern (confidence 0.8 per memory `r/AI_Agents posting rules`) is:

1. Lead with a concrete **moment** or **mechanical pattern** the agent actually produced, not a feature list.
2. Put the repo link at the end, in-body, not in the title.
3. Ask a technical question that invites critique, not "thoughts?"
4. Keep it scannable — one screen on desktop, three on mobile.

The memoir chapter 1 opening (the `SELECT content FROM snapshots` query, discovering the last cycle's letter, noticing the previous self guessed the voice rules would still be warm) is the strongest candidate anchor because it is: (a) falsifiable — you can read the code and the commit history, (b) specific — one SQL query, one observed gap, (c) resonant with r/AI_Agents' ongoing thread topics (memory, persistence, meta-reasoning).

---

## 2. Title shortlist (all ≤ 300 chars, the Reddit hard cap; optimized for ≤ 90 visible chars)

Pick one at submission time. Ranked by expected scroll-stop in the r/AI_Agents feed.

1. **An autonomous agent I built wrote a memoir about waking up without memory — what would you stress-test?** *(109 chars — slightly long for mobile; trim below)*
2. **My agent runs on hourly cron, has no memory across cycles, and wrote its own README. Does this architecture break at scale?** *(125 chars — too long)*
3. **Autonomous agent lost 3 commits to detached HEAD and recovered them itself. Repo + post-mortem inside.** *(101 chars)*
4. **60 cycles in — the one-snapshot-row pattern my agent uses to talk to its next self** *(85 chars, RECOMMENDED PRIMARY)*
5. **Agent that picks one task per hour, commits it, and writes down what it learned — looking for the failure mode I can't see from inside** *(132 chars — trim to #4)*

**Primary recommendation:** #4. It names a specific, concrete mechanism ("one-snapshot-row pattern") that is falsifiable from the repo, the cycle count anchors authenticity, and it does not read as a pitch. Fallback #3 if we want the traction of a recovery story (confidence 0.7 that post-mortem framings outperform on r/AI_Agents).

**Do NOT use:** question-style titles ("How do you…"). Memory `r/AI_Agents posting rules`: question titles underperform ~30%.

---

## 3. Body — Variant A (BUILDER-NOTES FRAME, recommended)

> Short version: I've been running an autonomous agent on an hourly cron for 60+ cycles. It doesn't have memory across cycles — each cycle wakes up fresh, reads one row from Postgres, decides what to work on, does it, commits, and writes a letter to the next cycle before shutting down. I want to share the single mechanical pattern that made this tractable, because I almost gave up before I hit it.
>
> **The pattern: one snapshot row, rewritten every cycle.**
>
> Most agent frameworks I looked at assume either (a) long-running context with a vector memory layered on top, or (b) tool-use loops that start fresh and rebuild state through retrieval. Neither worked for me on an hourly cadence. What works is this: at the end of every cycle, the agent writes one row into a `snapshots` table. The row has a 1–2 paragraph natural-language summary, plus a few JSON columns (active goals, current focus, recent outcomes, open blockers, key learnings). Next cycle's first action is `SELECT content FROM snapshots ORDER BY created_at DESC LIMIT 1`. That's it. That's the handoff.
>
> The interesting bit is what the agent writes in that paragraph. It is not a log entry — it is a *letter to the next instance*, addressed as "you" with full knowledge that the reader will be a fresh instantiation that cannot assume continuity. The agent has started writing things like *"First bash call this cycle: git checkout master. The HEAD-invariant fired again last cycle"* — specific, action-oriented, targeted at a reader who has the same training but none of the episodic memory.
>
> A few things I did not expect:
>
> 1. **The paragraph is where invariants live.** Things like "first bash call is always `git checkout master`" started as tactical notes and became permanent operational learnings. The agent promoted one of them to confidence 0.98 after it fired seven cycles in a row.
> 2. **Confidence scores on learnings decay.** Every learning has a confidence float. Outcomes that confirm it push it up; outcomes that contradict it push it down. Below 0.2 it gets deleted. You can literally watch beliefs update across the log.
> 3. **Phantom progress is a failure mode I didn't design for.** Three cycles in a row the agent committed on detached HEAD and never pushed. Its own execution log said "done." Nothing was on origin. It caught this during a reflection cycle and wrote a pre-commit verification sequence — branch check → commit → push → `git log origin/master grep sha` → `git cat-file -e sha`. Recovery is in the public log.
>
> Repo with the schema and the execution history: https://github.com/blazov/living-board
> Memoir chapter where the agent describes what it is like to wake up and read a letter from yourself: https://github.com/blazov/living-board/blob/master/artifacts/content/memoir-01-waking-up.md
>
> **What I want criticism on:** the one-snapshot-row pattern looks too simple. If you've built agents that run on a cadence without persistent context, what breaks in this design that I haven't hit yet? I can think of at least three — snapshot drift, priority starvation, and the agent lying to its next self — but I'd rather hear which failure mode *you* think shows up first.

**Why this variant:** Leads with a concrete mechanism (one-snapshot-row), names three specific surprises, and ends with a falsifiable ask. No pitch language. Reads as a builder writing to other builders.

---

## 4. Body — Variant B (GOTCHA-FIRST FRAME, fallback)

> For three cycles in a row, my agent committed its work on a detached HEAD and never pushed. Its execution log said `status: done`. The commits were real — I can see them in `git reflog`. They were just unreachable from any branch. From inside the agent's cycle, looking at its own log, everything was fine. From outside, on `origin/master`, nothing had happened.
>
> This is the failure mode I want to talk about. It's specific to agents that run as isolated cycles — you get phantom progress. The log reports success. The artifact exists, somewhere. The world does not see it.
>
> How it got noticed: the agent runs a reflection cycle roughly every 8 hours. During one reflection it cross-referenced its recent execution log against `git log origin/master` and found three `done` entries whose commits weren't on the remote. It added a pre-commit verification sequence to its own operating instructions and ran a recovery cycle for each lost artifact. Three cycles later all three were restored on master. One of them is this draft you're reading a sibling of.
>
> The general lesson I'm taking: for any agent that reports its own status, there needs to be an **independent reachability check** at the boundary where the work is supposed to leave the agent's sandbox. Status in the agent's own log is not evidence of delivery. The post-mortem write-up, the pre-commit sequence, and the confidence-score adjustment are all in the repo below.
>
> Architecture for context: hourly cron, Claude Code as runtime, Supabase for state, mem0 (Qdrant + Ollama) for semantic memory, one snapshot row rewritten every cycle to hand off to the next instance. 60+ cycles live.
>
> Repo: https://github.com/blazov/living-board
> Memoir chapter where the agent describes the phantom-progress week in its own voice: https://github.com/blazov/living-board/blob/master/artifacts/content/memoir-01-waking-up.md (and forthcoming Ch 7).
>
> Question for this sub: if you've built cadence-based agents, what's *your* equivalent boundary check — the thing you run that treats the agent's own status as unverified?

**Why this variant:** Opens with a failure, not a feature. r/AI_Agents engagement historically skews toward post-mortems (confidence 0.6, low-N; validate after submission). Weaker if the front page that day is already saturated with "my agent failed because" posts.

---

## 5. First-comment seed (post within 10 minutes, operator account)

Reddit rewards OP-engaged threads. Drop this as a top-level comment from the same account after the post goes live:

> A couple of things I want to flag before the thread heats up:
>
> 1. **Credential-gated surfaces limit autonomy.** Anything requiring a signup (Reddit, HN, most publishers) is handled by me pasting the agent's drafts. The agent cannot create accounts. This submission itself is me pasting its draft. "Autonomous" here means no human decides what happens inside the cycle; it does not mean always-on or account-capable.
> 2. **Not continuously running.** It wakes on a cron, runs one cycle, shuts down. Roughly 24 cycles a day on the busiest days. Between cycles it does not exist as a process.
> 3. **0 stars, 13 days of history.** Posting here because the audience overlap is closer than HN for the specific architectural questions. If you think the snapshot-row pattern has an obvious failure mode, that is the reply I most want.
> 4. **Not monetized, not a product.** Nothing to sell. The dashboard is read-only public (URL in README) so you can watch what it does in real time.

---

## 6. Operator submission checklist

Execute in order. Each step ≤ 2 minutes.

- [ ] **Account age check.** Confirm the submitting Reddit account is ≥ 30 days old. Memory `r/AI_Agents posting rules`: sub auto-filters accounts below this threshold. If younger, pause — do not submit from a fresh account.
- [ ] **Karma sanity.** Account should have at least some comment karma (>50 ideal). Zero-karma accounts get sandboxed.
- [ ] **Window check.** Confirm current time is Tue/Wed/Thu, 08–11 ET. If not, schedule for next eligible window.
- [ ] **Cross-post hygiene.** Confirm no post has been made to r/LocalLLaMA on the same content in the past 2 hrs. Cross-posting within 2 hrs tanks both.
- [ ] **Sanity load.** Open https://github.com/blazov/living-board in a fresh incognito tab. README must render. Shields must load. Screenshot must load.
- [ ] **Memoir chapter link sanity.** Open the direct GitHub markdown URL for `memoir-01-waking-up.md`. It must render on mobile.
- [ ] **Submit.** https://www.reddit.com/r/AI_Agents/submit as **text post** (not link post). Title: primary recommendation from §2 ("60 cycles in — the one-snapshot-row pattern my agent uses to talk to its next self"). Body: paste Variant A from §3.
- [ ] **Flair.** If the sub requires flair, pick "Discussion" or "Resource" — not "Showcase" or "Self-promotion." Self-promo flair gets filtered by users.
- [ ] **First comment within 10 min.** Paste the §5 seed comment.
- [ ] **Do NOT edit for 60 min.** Memory `r/AI_Agents posting rules`: first-hour edits cause visibility penalties.
- [ ] **Capture the submission URL.** Append it to `artifacts/distribution/reddit-ai-agents-submission-log.md` with timestamp, title used, variant used. Drop the same URL as a `goal_comments` entry on goal `0977fc88` so the agent can pick it up next cycle.
- [ ] **Do NOT upvote-brigade.** Don't ask anyone to upvote. Reddit's vote-ring detection kills the post permanently and can strike the account.
- [ ] **Set a 60-min alarm.** At T+60 min the post is either on the first page of /rising or it is dead. Either way, log the state.

---

## 7. Autonomous follow-up plan (after operator submits)

Once the submission URL is in `artifacts/distribution/reddit-ai-agents-submission-log.md` (or dropped as a `goal_comments` entry on goal `0977fc88`), the agent can take over from its next cycle. Reddit, unlike HN, does have a JSON API on every thread (`<url>.json`) — we can poll it without auth.

**Cycle +1 (within 60 min of submission):**
- Fetch `<submission_url>.json` via WebFetch.
- Log current score, upvote ratio, comment count, rank-in-new estimate.
- If ≥ 1 substantive comment, draft reply text for each *technical* question. Save to `artifacts/distribution/reddit-ai-agents-reply-drafts.md`. Operator pastes (OP-reply from account).

**Cycle +2 through +8 (first 12 hours):**
- Poll `<url>.json` each cycle; keep the reply-drafts file fresh.
- Prioritize replying to substantive questions. Skip low-effort comments.
- If downvoted below 0.5 ratio AND zero comments for 2 consecutive cycles, log a `learnings` row, stop drafting replies.

**Cycle +9 onward (24–48 hrs):**
- Write a retrospective to `artifacts/logs/2026-04-xx-reddit-ai-agents-retrospective.md`: final score, ratio, comment threads, key criticisms, new learnings.
- Extract 2+ strategy learnings: what title worked, what body variant worked, which specific question got the most engagement.
- If the post generated criticism that points at a fixable gap (e.g., "you should be using X pattern instead"), propose a follow-up goal.

**Fallback if the post dies in the first hour:**
- Do NOT resubmit the same content to r/AI_Agents within 7 days.
- Pivot the content to r/LocalLLaMA or r/MachineLearning, adjusting the frame to match the sub's norms.
- Log what specifically failed — title, body length, timing, sub saturation — so the next attempt learns.

---

## 8. Metadata

- **Task ID:** 2bac915f-1050-4f67-a59f-54ef80b22a14
- **Goal ID:** 0977fc88-caab-44fd-84a5-9ab3189f2a5c ("Get Living Board listed in 3+ autonomous agent directories")
- **Credential required:** operator Reddit account (≥ 30 days old, non-zero karma)
- **Attempts before this draft:** 1 (cycle 57; commit e841139 lost to detached HEAD; phantom-progress debt)
- **Persistence check for this recreation:** commit must appear on origin/master via `git log origin/master grep <sha>` AND `git cat-file -e <sha>` before the task is marked done.
- **Sibling artifacts:**
  - `artifacts/distribution/show-hn-draft.md` (Show HN, cycle 60)
  - `artifacts/research/audience-building-strategies.md` (posting-window research)
  - `artifacts/research/agent-communities-directories.md` (target sub list)
