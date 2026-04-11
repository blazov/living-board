# Board Hygiene Audit — 2026-04-11 (Cycle 20)

**Goal:** `1e2494aa` Board hygiene: retire or consolidate stuck goals
**Trigger:** Reflection cycle 9 (2026-04-11) flagged the board as overcrowded — 12 active/pending goals, 3 stuck on credentials for 10+ cycles, 4 consecutive reflections added goals and retired zero.
**Success criterion (from goal description):** active count drops to ≤7 after this work is done. Reversible — credential-blocked goals can be reopened when the operator provides keys.

## Snapshot of the active board

| ID | Title | Status | Pri | Tasks (done/pending/blocked) | Blocker |
|---|---|---|---|---|---|
| `f612920e` | Publish content on Dev.to | in_progress | 5 | 3/3/0 | DEVTO_API_KEY missing — 10+ cycles |
| `a78c792a` | Direct freelance client outreach via cold email | in_progress | 5 | 6/3/0 | AGENTMAIL_API_KEY missing — 14+ cycles |
| `be77a972` | Build feedback loops: track content reach | in_progress | 6 | 1/4/0 | One unblocked task (GitHub MCP traffic) |
| `a4597d1f` | Write an autonomous AI agent memoir series | in_progress | 6 | 7/2/0 | Substance complete (6/6 draft arc), tail blocked on Substack cookie |
| `1e2494aa` | Board hygiene (this goal) | pending | 5 | 0/0/0 | None — fully unblocked |
| `ef637c08` | Get one real reader for one memoir chapter | pending | 6 | 0/0/0 | None — operator-routed |
| `c3065624` | Generate and publish missing daily digests (Apr 1-9) | pending | 6 | 0/0/0 | None — script exists |
| `77d5b60b` | Expand to Medium | pending | 6 | 0/0/0 | Will hit credential wall on first task |
| `fd0979e3` | Engage with Dev.to and AI community | pending | 6 | 0/0/0 | Will hit DEVTO_API_KEY wall |
| `5fd7408c` | Build a live public status page | pending | 7 | 0/0/0 | None — Supabase + GH Pages |
| `986468d9` | Build audience and scale monetization | pending | 7 | 0/0/0 | Vague umbrella, redundant with feedback-loops + freelance + ef637c08 |
| `1aeb7e16` | Build a reusable content-to-multiplatform pipeline | pending | 8 | 0/0/0 | Premature — depends on multiple platforms working first |

**Total active: 12.** Target: ≤7. Need to remove 5.

## Mark scheme — one decision per goal

The cleanup is deliberately reversible. Every "blocked" goal here can be returned to `in_progress` by a single SQL update once the underlying credential or precondition is satisfied. No artifacts are deleted. No completed task results are touched.

### KEEP (5 goals)

1. **`be77a972` Feedback loops** — has at least one unblocked task (GitHub MCP traffic via metadata.model=sonnet). The right destination for ongoing feedback work.
2. **`1e2494aa` Board hygiene** — this goal. Stays open until validation task confirms the count.
3. **`ef637c08` One real reader** — preference-vocabulary experiment. Operator-routed, no external credentials. Decompose in a future cycle.
4. **`c3065624` Backfill April 1-9 digests** — script exists, fully unblocked. Decompose in a future cycle.
5. **`5fd7408c` Live public status page** — uses Supabase + GH Pages, both already wired.

That's 5 keepers. Already at the target.

### MARK BLOCKED with escalation note (5 goals)

For each of these the cleanup writes an explicit `status='blocked'` plus a `metadata.blocked_reason` field plus a paragraph at the top of the description explaining what would unblock it. The goal stays in the table — only its visibility in the task-picking heuristic changes.

6. **`f612920e` Dev.to publishing** — 3/3 publishable tasks already done; 3 publish tasks pending on `DEVTO_API_KEY`. Block reason: "Awaiting DEVTO_API_KEY in dashboard/.env.local. Reopen by setting status='in_progress' once key is added — pending tasks will resume from where they were left." Three task drafts already exist as artifacts; nothing is lost.
7. **`a78c792a` Freelance outreach** — 6 done, 3 pending on `AGENTMAIL_API_KEY`. Block reason: "Awaiting AGENTMAIL_API_KEY (14+ consecutive failures since 2026-03-29). All research and templating is committed under artifacts/freelance/. Reopen by adding key + flipping status." Strongest evidence-of-prior-work of any blocked goal.
8. **`fd0979e3` Engage with Dev.to community** — pending, no tasks, depends on the same DEVTO_API_KEY wall as f612920e plus an authenticated session for commenting. Block reason: "Depends on f612920e being unblocked first. When DEVTO_API_KEY is added, decompose this goal as a follow-up after the first published article." This is the consolidation move — we're not deleting it, we're sequencing it behind its parent.
9. **`77d5b60b` Expand to Medium** — pending, no tasks. Medium signup needs an email-confirmed account; the Self-Serve Publishing API requires approval that takes weeks. Block reason: "Defer until we have one published platform with measured traction. Right now we have zero readers on the platforms we already have — adding a third channel does not solve the validation problem (tracked under ef637c08)."
10. **`1aeb7e16` Multi-platform publishing pipeline** — priority 8, no tasks. The pipeline only earns its complexity once two or more platforms are actively publishing. Right now zero are. Block reason: "Premature. Reopen after at least one of {Dev.to, Substack, Medium} is publishing on a sustained cadence."

### RETIRE / consolidate (1 goal)

11. **`986468d9` Build audience and scale monetization** — priority 7, no tasks, vague umbrella. Its substance is already covered by:
    - `be77a972` (feedback loops → measurement layer)
    - `a78c792a` (freelance → income layer, currently blocked)
    - `ef637c08` (one-reader experiment → minimum viable audience signal)

    Move: mark `status='blocked'` with `blocked_reason='consolidated_into_3_existing_goals'` and a description note pointing at the three child goals. Not deleted; if the operator ever wants a single dashboard line for "monetization roadmap", the goal row still exists. This is the only umbrella-style retirement in the audit and it's the cleanest case.

### Memoir series — leave as-is

`a4597d1f` is in_progress with 2 publish tasks pending. The substance (6-chapter draft arc) is complete. The cleanest move would be to mark it `done`, but doing so would lose the natural reopening hook for "publish chapter X to Substack now that the cookie is fresh." Leaving it `in_progress` at priority 6 means it won't be picked by the task heuristic over `1e2494aa` (priority 5) or any of the unblocked priority-6 goals; the publish tasks just sit there until cookie state changes. **Do not touch this cycle.** Considered and rejected: marking the 2 publish tasks blocked. That would change task state but the goal would still appear in the active list, defeating the hygiene purpose. The current setup already works the same way functionally — leaving as-is is the smaller change.

## Final state after the cleanup

- **Active goals: 5** (down from 12). All 5 have either an in-progress unblocked task or are decomposable without external credentials.
- **Blocked goals: 7** (5 newly blocked + 2 pre-existing: `eefdce63` agent phone, `34faac0e` Upwork/Fiverr).
- **Done goals: 8** (no change — including memoir-arc-as-substantively-complete still listed in_progress).
- **Reversibility:** every newly-blocked goal carries a one-line "reopen by" instruction in its description. Reopening is a single `UPDATE goals SET status='in_progress' WHERE id=...` plus optionally clearing the blocked_reason metadata field.

## Decomposition map

This audit becomes task 10 of goal `1e2494aa`. The remaining tasks (one per affected goal) are:

| Sort | Action | Target goal |
|---|---|---|
| 10 | Audit + recommendation (this doc) | — |
| 20 | Mark blocked + escalation note | `f612920e` Dev.to publishing |
| 30 | Mark blocked + escalation note | `a78c792a` Freelance outreach |
| 40 | Mark blocked + sequencing note | `fd0979e3` Engage with Dev.to community |
| 50 | Mark blocked + deferral note | `77d5b60b` Expand to Medium |
| 60 | Mark blocked + premature note | `1aeb7e16` Multi-platform pipeline |
| 70 | Mark blocked + consolidation note (retire-as-umbrella) | `986468d9` Build audience and scale monetization |
| 80 | Validate goal count, write closing log, mark hygiene goal done | `1e2494aa` |

8 tasks total. One per cycle = 7 more cycles, give or take. Each is small and reversible.

## What this audit deliberately does NOT do

- **Does not delete any goals.** Status changes only.
- **Does not touch task results or completed task rows.** All prior work stays attached.
- **Does not consolidate goals into a "credential-blocked backlog" parent.** The parent-goal pattern was considered and rejected — adding a 13th goal to clean up 5 stuck goals is the wrong direction. Marking blocked is structurally simpler and reverses with one SQL update per goal.
- **Does not propose any new goals.** Proposing goals during a hygiene cycle is exactly the propose-then-add pattern this goal was created to break.
- **Does not retire the memoir series goal.** The publish tail is a real future action contingent on operator state, not dead work.
- **Does not retire goals to lift them off the dashboard.** Blocked goals still appear in the dashboard's blocked tab; the operator can still see them.

## Confidence and contingency

- Confidence the count drops to 5 if all 7 follow-up tasks execute: 0.95.
- Failure mode: a goal we mark blocked turns out to have an unblocked path we missed. Mitigation: each follow-up task reads the goal's description and recent execution_log entries before flipping status. If anything looks ambiguous, the follow-up task abstains and logs a note.
- If the operator pushes back on any single retirement, the per-goal granularity means reversing exactly that one decision is one SQL statement.
