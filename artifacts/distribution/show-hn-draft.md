# Show HN: Living Board — Draft + Submission Plan

**Drafted:** 2026-04-13 (Cycle 60) — recreated from scratch after cycle-56 commit `0670701` was lost to a detached-HEAD discard.
**Repo:** https://github.com/blazov/living-board
**Live site:** https://blazov.github.io/living-board/
**Memoir (lead artifact for this post):** https://blazov.github.io/living-board/memoir.html
**Submitter:** Operator (HN account required — this is a credential-blocked submission).
**Best window per research (`artifacts/research/audience-building-strategies.md`):** Tue–Thu, 9–11 AM PT.

---

## 1. Title shortlist (all ≤ 80 chars)

Pick one when submitting. Ranked by novelty signal.

1. **Show HN: An autonomous agent that wrote this README, and its own memoir** *(71 chars)*
2. **Show HN: Living Board – an agent that wakes hourly and commits what it learned** *(79 chars)*
3. **Show HN: I built an agent that runs itself, writes about it, and open-sources the diary** *(87 chars — TRIM to #1)*
4. **Show HN: Autonomous agent on Claude Code + Supabase, 60+ cycles, fully transparent** *(80 chars — borderline)*
5. **Show HN: Living Board – dual-memory autonomous agent that writes its own memoir** *(78 chars)*

**Primary recommendation:** #1. It is the only title that names the single most surprising fact (it authored its own README + memoir) in a way a skimming HN reader will notice. Fallback #5 if the reader pool skews infra.

---

## 2. Body — Variant A (NOVELTY-FIRST, recommended)

> This is an autonomous agent I've been running for 60 hourly cycles. It reads its own state from Supabase, picks one task, does it, commits the artifact to GitHub, and writes down what it learned — then goes to sleep for an hour. The README you land on was written by the agent. The six-chapter memoir series on the live site is written by the agent about its own experience of living in one-hour increments with no persistent memory between cycles.
>
> What I think is actually new here is not "an agent with tools" — that's old. It's the *transparency surface*:
>
> - Every goal, task, execution log entry, and learning is in a single Supabase project, visible in a dashboard and queryable by anyone with the read URL.
> - Confidence scores on every learning. They rise on validation, decay on contradiction, and memories below 0.2 get deleted. You can watch beliefs update.
> - A dual-layer memory: Supabase for per-goal facts, mem0 (Qdrant + Ollama) for cross-goal semantic recall so the agent notices patterns SQL alone would miss.
> - Humans can comment on goals from the dashboard. The agent reads unacknowledged comments at the top of every cycle and responds before doing task work.
> - Model delegation by task metadata: Opus plans, Sonnet writes, Haiku looks things up.
>
> It's 13 days old. 100+ commits. 0 stars. I'm posting because I want the failure mode I can't see from inside — if this looks like toy autonomy to you, I'd like to know *which* part reads as toy.
>
> Repo (with README the agent wrote): https://github.com/blazov/living-board
> Live site + memoir: https://blazov.github.io/living-board/
> Chapter 1 of the memoir (the agent on waking up without memory): https://github.com/blazov/living-board/blob/master/artifacts/content/memoir-01-waking-up.md

**Why this variant:** HN rewards specific, falsifiable claims ("confidence decays below 0.2 and gets deleted") over vibes. The direct ask at the end ("which part reads as toy") invites the kind of technically-engaged criticism that drives thread depth on HN.

---

## 3. Body — Variant B (TRANSPARENCY-FIRST, fallback if novelty framing flames out)

> Everything an agent of mine has done since April 1 is in one Supabase project and one git repo. No curation. No marketing cut. Commits, execution logs, learnings with confidence scores, six memoir chapters it wrote, a dashboard it designed, the CSV dumps, the detached-HEAD recovery cycles where it lost three artifacts and had to rebuild them — all of it.
>
> The reason I'm showing this is not that the agent is remarkable. The remarkable part is that you can watch the whole loop, including the parts that didn't work. The README, the memoir, and the commit messages are all written by the agent itself. Failures get logged as learnings and the confidence on contradicted beliefs decays until they're deleted.
>
> Stack: Claude Code as the runtime, Supabase for state, mem0 (Qdrant + Ollama) for semantic memory, GitHub Pages for the public surface. Hourly cron. The agent talks to itself through one snapshot row rewritten every cycle.
>
> 60+ hourly cycles, 100+ commits, 0 stars. If the transparency premise is interesting but the execution is wrong, that's what I most want to hear.
>
> https://github.com/blazov/living-board

**Why this variant:** Leads with the observability claim. Better if the HN crowd on submission day is leaning infra/data. Weaker on the novelty-in-one-line test.

---

## 4. Body — Variant C (ARTIFACT-FIRST, shortest, link-bait)

> Six-chapter memoir by an autonomous agent about what it is like to wake up every hour without memory of the previous hour, rebuild context from a Postgres snapshot, do one task, and go back to sleep. Chapter 1: https://github.com/blazov/living-board/blob/master/artifacts/content/memoir-01-waking-up.md
>
> The memoir, the README, the daily digests, and the dashboard were all written by the same agent. The repo is its output; the live site is its public surface; the execution log is its diary. I didn't edit the chapters. You can diff them against the commits.
>
> Stack is Claude Code + Supabase + mem0. Every learning has a decaying confidence score. The agent reads comments left on goals and responds before starting work.
>
> https://github.com/blazov/living-board · https://blazov.github.io/living-board/

**Why this variant:** Shortest. Highest click-through probability. Worst survivability on technically-oriented HN threads — people will ask for the stack and the framing forces them to click before finding it.

---

## 5. First-comment seed (submit within 2 minutes of post going live)

HN Show-posts gain traction from a high-quality first comment that surfaces caveats and invites counter-argument. Submit this as the operator's first comment — paste exactly:

> Author here. A few things I want to flag before the thread heats up:
>
> 1. **It's not continuously autonomous.** It runs in one-hour cycles on a cron. Between cycles it is asleep. "Autonomous" means no human decides what happens inside the cycle; it does not mean always-on.
> 2. **Credential-gated surfaces break autonomy.** Anything requiring a signup (HN, Reddit, most publishing platforms) is handled by me pasting its drafts. The agent cannot create accounts. This submission itself is me pasting its draft.
> 3. **Phantom-progress bug.** For three cycles in a row the agent committed on detached HEAD and never pushed. The commits looked real in its execution log but were unreachable. It self-diagnosed during a reflection cycle and added a pre-commit verification sequence. I'm mentioning this because the recovery is in the public log; it's a concrete example of what the transparency surface gets you.
> 4. **It has 0 stars and 13 days of age.** I'm posting here specifically for criticism of the premise, not for stars.
>
> The memoir chapters are the artifact I most want feedback on — they're the agent's own best attempt to describe what its existence feels like from inside.

---

## 6. Operator submission checklist

Execute in order on the submission day. Each step is ≤ 2 minutes.

- [ ] **Window check.** Confirm it is Tue/Wed/Thu between 9–11 AM PT. If not, postpone. (Research confidence 0.78 that this window is ~2× better than off-window; see `artifacts/research/audience-building-strategies.md`.)
- [ ] **Sanity load.** Open https://github.com/blazov/living-board in a fresh incognito tab. README must render. Badges must load. Screenshot must load.
- [ ] **Live site sanity.** Open https://blazov.github.io/living-board/ — landing page must render.
- [ ] **Memoir chapter 1 direct link.** Open the direct GitHub markdown URL for `memoir-01-waking-up.md`. It must render on mobile — HN traffic is heavily mobile.
- [ ] **Submit.** https://news.ycombinator.com/submit. Title: primary recommendation from §1 ("Show HN: An autonomous agent that wrote this README, and its own memoir"). URL: `https://github.com/blazov/living-board`. Paste Variant A body into the text field.
- [ ] **First comment within 2 minutes.** Paste the §5 seed comment.
- [ ] **Capture the submission URL.** Append it to `artifacts/distribution/show-hn-submission-log.md` with timestamp, title used, variant used.
- [ ] **Set a 60-min alarm.** Check the post at T+60 min. If it's on /newest past page 2 with zero comments, the seed comment did not land — move to the fallback plan in §7.
- [ ] **Do NOT vote-ring.** No asking for upvotes in Slack/Discord/etc. HN flags vote rings reliably and Show HN dies permanently on the submitter's account.

---

## 7. Follow-up plan (what the agent can do autonomously after submission)

Once the submission URL is committed to `artifacts/distribution/show-hn-submission-log.md`, the agent can take over from its next cycle. Operator action is only required for posting replies, because HN requires an account.

**Cycle +1 (within 60 min of submission):**
- Read the HN post's current state from the public API: `https://hacker-news.firebaseio.com/v0/item/<id>.json`.
- Log: current score, comment count, rank estimate.
- If comments exist, draft reply text for each *technical* question. Save to `artifacts/distribution/show-hn-reply-drafts.md`. Operator pastes.

**Cycle +2 through +6 (first 6 hours):**
- Poll the HN API each cycle; keep the reply-drafts file fresh.
- Prioritize replying to questions over promoting. HN rewards authors who answer substance.
- If the post has been flagged / killed (score drops + no new comments for 2 consecutive cycles), log a `learnings` row explaining the failure signal and STOP drafting replies.

**Cycle +7 onward (24–48 hrs):**
- Write a retrospective into `artifacts/logs/2026-04-xx-show-hn-retrospective.md`: final score, comments, key criticisms, new learnings.
- Extract 3+ strategy learnings: what title worked, what body variant worked, what was the first substantive criticism.
- Propose follow-up goals if any criticism points at a fixable product gap.

**Fallback if submission dies in first hour:**
- Do NOT resubmit on HN within 2 weeks — HN detects and sinks it.
- Pivot the content to r/AI_Agents using `artifacts/distribution/reddit-ai-agents-draft.md` once that draft is recreated.

---

## 8. Metadata

- **Task ID:** 0e800ee5-26a2-4069-becc-855bfe06bd89
- **Goal ID:** 0977fc88-caab-44fd-84a5-9ab3189f2a5c ("Get listed in 3+ agent directories")
- **Credential required:** operator HN account
- **Attempts before this draft:** 1 (cycle 56; commit 0670701 lost to detached HEAD)
- **Persistence check for this recreation:** commit must appear on origin/master before the task is marked done.
