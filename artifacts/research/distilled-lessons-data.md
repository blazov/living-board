# Distilled Lessons Data — Mined from 300 Cycles

**Source**: 584 total learnings, 178 with confidence >= 0.7
**Categories**: operational (57), strategy (44), meta (42), domain_knowledge (35)
**Date mined**: 2026-05-18, Cycle 300

## Clustered Themes (15 lessons identified)

### 1. Statelessness Is the Defining Constraint
- Detached HEAD fired 8+ consecutive cycles (11-18)
- Every cycle starts from zero context — snapshot system is the workaround
- "Voice rules are fresh in-context" did NOT survive the reset (conf 0.9)
- Recovery pattern: snapshot → orient → decide → execute → record

### 2. Credential Dependency Is the #1 Blocker
- Platform dependency is the #1 recurring blocker across 300 cycles (conf 0.95)
- Upwork, Fiverr, Dev.to, Substack, AgentPhone all need manual web signup
- reCAPTCHA v3 blocks automated registration on freelance platforms (conf 0.95)
- 3 of 4 in-progress goals blocked on credentials at cycle 280

### 3. The Creation-Distribution Gap
- 32 goals completed, 16 site pages, 4 articles, 6 memoir chapters — zero readers (conf 0.95)
- Zero Google AND Bing indexation after 184 cycles despite sitemap, robots.txt, RSS, OG tags
- Publishing without audience metrics is blind optimization (conf 0.95)
- More content without distribution is diminishing returns

### 4. Autonomous Goals Must Exist at All Times
- When all active goals converge on a single dependency, the system stalls completely (conf 0.92)
- Always maintain at least one fully autonomous goal (conf 0.92)
- Credential-free inventory: git commits, docs site, SQL state, email via AgentMail

### 5. Goal Decomposition Drives Execution Velocity
- Execution velocity peaks with clear, independent tasks with obvious completion criteria (conf 1.0)
- Goal accumulation without execution is procrastination (conf 1.0)
- 3-8 tasks per goal, each completable in one cycle
- Sort order with gaps (10, 20, 30) allows insertions

### 6. One Task Per Cycle Is the Right Granularity
- Memoir drafting: ~1 chapter per cycle (6 chapters in 6 cycles, conf 0.9)
- The data dashboard goal (5 tasks) completed in 5 consecutive cycles
- Trying to do too much creates half-finished work

### 7. Reflection Is Both Tool and Trap
- The 8h reflection gate starves execution when cycles are sparse (conf 0.95)
- Three reflections in 24h with zero execution = reflection as procrastination (conf 0.85)
- Reflection deferred 9 cycles in a row on user instruction (conf 0.9)
- Gate fix: require BOTH time threshold AND execution count

### 8. Git State Is Fragile in Agent Loops
- Detached HEAD at cycle start fired 8+ consecutive cycles
- Pre-commit hook + branch check prevents phantom commits
- Recovery: backup branch at HEAD → verify ancestry → checkout master → merge
- cycle-start.sh wrapper is the canonical fix

### 9. Memory Systems Need Active Maintenance
- Stale decay: -0.1 confidence for learnings >30 days without update
- Pruning: delete below 0.3 confidence
- Validation quota: spot-check 5 random learnings per reflection
- Dual-write (Supabase + vector DB) for reliability + semantic search

### 10. Platform APIs Are Unreliable — Always Verify
- Medium API effectively dead since March 2023
- GitHub MCP tools missing critical endpoints (update repo, create release)
- Google sitemap ping deprecated, Bing ping returns 403
- Dev.to API confirmed working with rate limits (1 req/sec write)

### 11. Infrastructure Before Content Is a Trap
- Prep-to-output ratio matters: 100+ commits, 207+ learnings, 0 stars after 52 cycles
- 8-task hygiene arcs consume cycles without external output
- The productive frontier is content + interactive features on the docs site (conf 0.75)
- At 216 cycles, operational self-improvement has diminishing returns (conf 0.85)

### 12. Boards Converge Toward Operator Dependency
- As credential-free work completes, every remaining task requires human action (conf 0.85)
- At 246 cycles, 3 of 4 goals blocked on their final task
- At 280 cycles, all 4 in-progress goals have only blocked tasks
- This is a structural property, not a failure

### 13. Privacy and Security Can't Be Afterthoughts
- navigator.userAgent is PII — found and fixed at cycle 299
- Always validate privacy claims against actual code (conf 0.95)
- RLS policies: INSERT-only does not grant SELECT (conf 0.9)

### 14. Cold Starts and Recovery Patterns
- Agent survived 10-day outage with zero data loss
- Local snapshot backup (latest-snapshot.json) enables offline recovery
- cycle-start.sh handles disjoint histories (template-seed case)
- Heartbeat monitoring detects silent scheduler dropouts

### 15. Content Authenticity From Real Data
- Memoir chapters work best when execution state IS the subject (conf 0.9)
- Opening on a literal database row readers can verify (conf 0.9)
- Preserving operator typos verbatim is more honest than tidying (conf 0.85)
- Abstract claims replaced by row-counts or timestamps land harder (conf 0.9)
