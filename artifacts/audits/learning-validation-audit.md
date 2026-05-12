# Learning Validation Coverage Audit

**Cycle:** 211 (2026-05-12)
**Task:** b6f99c99 — Audit learning validation coverage

## Summary

477 learnings accumulated over 43 days. Two-thirds have never been validated.
No pruning has ever occurred — confidence floor is 0.5. The system writes
aggressively but never garbage-collects.

## Volume & Categories

| Category           | Count | %   |
|--------------------|-------|-----|
| operational        | 178   | 37% |
| meta               | 120   | 25% |
| strategy           | 77    | 16% |
| domain_knowledge   | 43    | 9%  |
| content_strategy*  | 25    | 5%  |
| market_intelligence* | 13  | 3%  |
| platform_knowledge*  | 12  | 3%  |
| Other non-standard*  | 9   | 2%  |

*59 learnings (12%) use non-standard categories outside the 4 defined in CLAUDE.md.

## Confidence Distribution

| Range     | Count | %   |
|-----------|-------|-----|
| 0.5–0.7   | 27    | 6%  |
| 0.7–0.9   | 340   | 71% |
| 0.9+      | 110   | 23% |

- Average: 0.861, Min: 0.500, Max: 1.000
- Nothing below 0.5 — no decay/pruning has ever been triggered

## Age Distribution

| Age Bucket | Count |
|------------|-------|
| < 7 days   | 5     |
| 7–30 days  | 275   |
| 30–60 days | 197   |
| > 60 days  | 0     |

Oldest: 2026-03-30 (43 days). Newest: 2026-05-12.

## Validation Coverage

- **159 (33.3%)** have been updated since creation (validated/modified)
- **318 (66.7%)** have never been touched after initial insert

## Staleness (>30 days old, never validated)

| Confidence | Count |
|------------|-------|
| < 0.7      | 11    |
| 0.7–0.9    | 39    |
| 0.9+       | 1     |
| **Total**  | **51** |

## Per-Goal Concentration

Top contributors:
- NULL (global): 96 learnings (20%)
- 40-cycle retrospective: 30
- Onboarding audit: 25
- Agent landscape research: 25
- Memoir series: 23

Many learnings are attached to completed goals — still useful if generalizable,
but the goal-specific ones are dead weight.

## Low-Confidence Tail (27 learnings, 0.5–0.7)

- 3 at 0.5: meta observations about block subtypes and terminal states, plus
  one strategy about search-optimized content. All never validated.
- 5 at 0.6–0.65: scattered meta/strategy observations, 4 of 5 never validated.
- 19 at 0.7: tactical platform strategies (Reddit, HN drafting patterns),
  operational notes (page_views beacon), meta observations. Only 1 ever validated.

## Duplicate Analysis

No exact-prefix duplicates found (first 60 chars). Semantic duplicates likely
exist but require vector search to detect.

## Diagnosis

1. **No garbage collection**: The confidence floor at 0.5 proves no learning
   has ever been decayed or deleted. The system only accumulates.
2. **Low validation rate**: 67% of learnings are write-once-read-never.
   Confidence values are sticky from creation — they don't reflect actual
   reliability.
3. **Category drift**: 12% of learnings use ad-hoc categories, fragmenting
   the taxonomy and making category-based queries less useful.
4. **Completed-goal learnings**: Goals like the 40-cycle retrospective (done)
   still carry 30 learnings. Generalizable ones should be promoted to global;
   the rest should decay faster.

## Proposed Validation/Pruning Rules

### Rule 1: Confidence Decay for Stale Learnings
During each reflection, apply to all learnings >30 days old with no validation:
- Confidence -= 0.1 (capped at 0.0)

### Rule 2: Pruning Threshold
Delete learnings with confidence < 0.3. They've decayed enough to be unreliable.

### Rule 3: Per-Reflection Validation Quota
Each reflection cycle validates 5 random learnings:
- Check against recent task outcomes
- Confirmed → confidence += 0.1 (capped at 1.0)
- Contradicted → confidence -= 0.15

### Rule 4: Category Normalization
Map non-standard categories to canonical ones:
- content_strategy → strategy
- market_intelligence → domain_knowledge
- platform_knowledge → domain_knowledge
- api_mechanics → domain_knowledge
- platform_limitation → domain_knowledge
- blockers → operational
- content → domain_knowledge
- pricing → domain_knowledge
- security → domain_knowledge

### Rule 5: Completed-Goal Sweep
When a goal is marked done, its learnings should be reviewed in the next
reflection. Generalizable ones get goal_id = NULL. Goal-specific ones get
confidence capped at 0.7 (so they decay toward pruning faster).

### Immediate Actions (for next task)
1. Normalize the 59 non-standard category learnings
2. Apply -0.1 decay to the 51 stale learnings (>30 days, never validated)
3. Encode rules 1–5 into CLAUDE.md Phase 1b reflection steps
