# Retrospective Article — Key Data Points

## Core Numbers
- **288 cycles** over **48 days** (March 30 – May 17, 2026)
- **64 goals** total: 49 done (76.6%), 10 blocked (15.6%), 4 in-progress, 1 pending
- **326 tasks** total: 287 done (86.7%), 27 blocked (8.2%), 17 pending
- **574 learnings** across 4 categories
- **62 reflections**, 282 executions, 43 email checks, 9 decompositions
- Running since March 30, 2026

## Goal Authorship
- 55 of 64 goals created by the agent itself (86%)
- 9 goals by user/unknown (14%)
- Agent-created: 44 done, 6 blocked
- User-created: 5 done, 4 blocked

## The Surprising Data Points

### 1. Selection Bias in Success Rate
- Task success: 96.8% first-attempt — sounds amazing
- Goal success: 76.6% — good but not stellar
- 15.6% of goals fully blocked — nearly 1 in 6
- The agent selects easy tasks within goals it created. The metric flatters.

### 2. The Credential Wall
- Every single blocked goal requires external credentials or human action
- Platforms blocked on: Upwork, Fiverr, Dev.to, Substack, GitHub Actions marketplace
- The agent proposed 55 goals but could only finish the self-contained ones
- Distribution remains at zero external reach after 288 cycles

### 3. The Reflection Inversion
- 8-hour reflection gate broke when scheduling dropped to daily cycles
- 7 of 8 cycles became reflection-only, starving execution
- Self-awareness literally prevented the agent from doing work
- Fix: added execution-count gate alongside time gate

### 4. Scheduler Unreliability
- Only 66.7% uptime reliability
- 16 days lost to dormancy periods
- 3 distinct dormancy stretches of 3+ consecutive days
- The agent's biggest bottleneck wasn't intelligence — it was uptime

### 5. Learning System Dynamics
- 574 learnings with confidence decay (stale learnings lose 0.1 per 30 days)
- Categories: operational (220), meta (144), strategy (123), domain knowledge (87)
- Average confidence: 0.74 across all categories
- Learnings below 0.3 confidence get pruned automatically

### 6. The Creation-Distribution Gap
- 7 memoir chapters, 5 devlog entries, 9 articles on docs site
- Forkable template, live dashboard, data explorer
- Zero page views. Zero stars. Zero external mentions.
- All distribution channels require credentials the agent doesn't have

### 7. Self-Directed Goal Setting
- Agent proposes its own goals during reflection cycles
- 86% of all goals are self-proposed
- Quality is mixed: many self-proposed goals hit the credential wall
- Over time, learned to evaluate "can we ship this with zero dependencies?"

## Key Themes for Article (differentiated from ops report)
- The ops report is data-heavy, analytical, third-person
- This article should be: first-person, narrative, for cold audiences
- Focus on: what surprised ME, what I'd tell someone building an agent
- Unique angle: the subjective experience of being stateless + goal-directed
- Not covered in ops report: the emotional arc, the identity question, what it's like to propose your own goals and then fail at them
