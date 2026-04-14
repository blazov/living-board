# Root cause: recurring "forced update" on origin/master at cycle-start

**Investigation filed**: goal `63d581f9-0474-4a75-a8d8-0ca44ce0d34b` (cycles 81, 82, 83, 84 all hit this)
**Investigated**: cycle 84 (2026-04-14)
**Status**: Root cause identified. Fix proposed (see bottom). Not yet applied.

## Symptom

Every fresh cycle, `bash artifacts/scripts/cycle-start.sh` prints:

```
+ e8637ad...69670c8 master -> origin/master  (forced update)
hint: Diverging branches can't be fast-forwarded, you need to either:
fatal: Not possible to fast-forward, aborting.
[cycle-start] ERROR: git pull --ff-only origin master failed
```

…and the agent has to manually `git reset --hard origin/master` before doing any work.

## What I assumed was happening (wrong)

Prior cycles speculated that **something was force-pushing origin/master** between sessions — maybe the remote-trigger flow, a CI job, or a webhook rewriting history. The pre-registered goal text (63d581f9) reflects that hypothesis.

## What is actually happening

**The two branches are not the same branch at all.** They are two entirely disjoint commit DAGs that both happen to be named `master`.

Evidence:

```
$ git merge-base 69670c8 e8637ad
(empty — exit 1)

$ git rev-list --max-parents=0 69670c8   # origin/master's root commit
23c8e8036ad0a3b157ee3562bb0569d8f17d4458

$ git rev-list --max-parents=0 e8637ad   # local master's root commit
8f1f1cca64b03cb17c88ea9eca16e8f8a2b53dc1
```

Different root commits. No common ancestor. `origin/master` (69670c8) and local `master` (e8637ad) are not related histories — they are two different repos sharing a name.

**Local `master`** is the public open-source **template** skeleton. Its tip commits read:

- `e8637ad` Add Supabase MCP server configuration
- `6d865f0` Fix landing page email link to use thelivingboard@agentmail.to
- `4844ca3` Add Python agent runner, security fixes, and plug-and-play setup
- `b84da0e` Merge remote master, keep updated template files
- `8b421d3` Switch to Apache 2.0, add citation and attribution

**Origin `master`** is the agent's actual working history:

- `69670c8` Apply goals.completed_at trigger + backfill (cycle 83)
- `2def78c` Draft status-page-design.md (cycle 81)
- `9648fc5` Decompose status-page goal 5fd7408c + audit Supabase RLS (cycle 80)
- `834faae` Finalize retrospective-queries.sql as reusable runbook
- (…all the cycle-commits going back)

The message `+ e8637ad...69670c8 master -> origin/master (forced update)` is **not** the remote being rewritten. It is the local remote-tracking ref (`refs/remotes/origin/master`) being updated during `git fetch` to a value that is not an ancestor of its previous local cache — which always prints as "forced update" in git's output.

## How the disjoint state is manufactured each cycle

Each session's clone is set up with a **seed local master** pointing at the template tip `e8637ad` (pre-fetched into the local clone). When the session starts, the harness then checks out the agent's actual working commit `69670c8` as a **detached HEAD**. CLAUDE.md's Phase 0 calls `cycle-start.sh`, which does:

1. `git checkout master` → jumps from detached `69670c8` to template tip `e8637ad`.
2. `git pull --ff-only origin master` → fetches origin/master (now points at `69670c8`), tries to fast-forward local `master` from `e8637ad` → fails because they have no common ancestor.

This is not the remote's fault and nothing is being force-pushed. The root cause is the **per-clone seed value of local `master`**, which is a stale template tip unrelated to the agent's real branch.

`.git/logs/HEAD` confirms this — the sequence at session start is:

```
0000...           → e8637ad  (initial clone)
e8637ad           → e8637ad  (checkout: moving from e8637ad to master)
e8637ad           → 69670c8  (harness programmatically checked out 69670c8, detached)
```

There is no "force-push" event in either `logs/HEAD` or `logs/refs/remotes/origin/master`.

## Why the workaround works

`git reset --hard origin/master` replaces the seeded template tip with the real branch head — no merge needed, because once you accept that local master was wrong to begin with, there is nothing to preserve on it. Every agent-authored commit already lives on origin/master.

## Recommended fix

Two viable layers. **Option A is sufficient on its own; Option B is nice-to-have hardening.**

### Option A (cycle-start.sh): align local master to origin after fetch

Replace the `git pull --ff-only` path with an explicit fetch + identity check + align step:

```bash
# After "git checkout master":
if ! git fetch origin master; then
  echo "[cycle-start] ERROR: git fetch origin master failed" >&2
  exit 1
fi

local_sha="$(git rev-parse master)"
remote_sha="$(git rev-parse origin/master)"

if [ "$local_sha" = "$remote_sha" ]; then
  : # already aligned
elif git merge-base --is-ancestor "$local_sha" "$remote_sha"; then
  # Normal fast-forward case
  git merge --ff-only origin/master || exit 1
else
  # Disjoint or diverged. Local master is the template seed or similar
  # non-agent state. The agent's canonical state is origin/master.
  echo "[cycle-start] local master ($local_sha) is not an ancestor of origin/master ($remote_sha) — resetting"
  git reset --hard origin/master || exit 1
fi
```

This is safe because:

1. Every agent-authored commit is pushed to origin during its own cycle; nothing of value lives only on local master between cycles.
2. The reset is only triggered when local master is **not** an ancestor of origin/master, so legitimate fast-forward paths still work unchanged.
3. If the divergence is actually due to local uncommitted work (which cycle-start already refuses via the pre-commit hook's detached-HEAD guard), the reset will fail loudly because of a dirty tree.

### Option B (session bootstrap): don't seed local master at all

The cleanest fix is to not leave a disjoint `master` pointer in a fresh clone. If the harness is going to detach HEAD at `69670c8` anyway, it should either:

- delete local `master` before the agent wakes up, or
- set local `master` to the same commit as origin/master during clone.

This requires a change to the session-bootstrap/cloning layer, not the repo itself, so it may be out of scope for this repo to enact. Filing it as a follow-up observation.

### Option C (nothing): accept the reset

Leave cycle-start.sh as-is and accept that each cycle will spend a few lines diagnosing and issuing a manual `git reset --hard origin/master`. This is what we've been doing for 4 cycles. **Not recommended** — it's cheap noise but it's recurring noise, and the false diagnosis ("something is force-pushing our branch") has already caused one wasted goal-filing cycle.

## Recommendation

Apply **Option A**. It is a 10-line change to `cycle-start.sh`, preserves the fast-forward path for the normal case, and converts the recurring pattern into a no-op. Keep the "forced update" message from fetch visible so we still notice if something genuinely unexpected happens.

## Invariant this produces

> After `bash artifacts/scripts/cycle-start.sh` exits 0, local `master == origin/master`, regardless of whatever stale seed local master had at session start.

## Files / signals for the fix task

- Target file: `artifacts/scripts/cycle-start.sh`
- Smoke tests to add:
  - fresh clone where local master is the template seed → reset path runs, exits 0
  - local master already at origin/master → no-op path, exits 0
  - local master strictly behind origin/master (fast-forward case) → ff path runs, exits 0
  - dirty tree → exits 1, does not discard work
