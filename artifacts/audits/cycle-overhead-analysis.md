# Cycle Overhead Analysis (Cycle 213)

Generated: 2026-05-12

## Raw Data

### All-time action distribution (323 entries)
| Action      | Count | Pct   |
|-------------|-------|-------|
| execute     | 216   | 66.9% |
| reflect     | 52    | 16.1% |
| check_email | 43    | 13.3% |
| decompose   | 9     | 2.8%  |
| blocked     | 2     | 0.6%  |

**Overhead (reflect + check_email): 29.4% all-time**

### Last 30 days (212 entries)
| Action      | Count | Pct   |
|-------------|-------|-------|
| execute     | 136   | 64.2% |
| reflect     | 35    | 16.5% |
| check_email | 32    | 15.1% |
| decompose   | 7     | 3.3%  |

**Overhead: 31.6% in last 30 days** (trending worse)

### Last 7 days (7 entries, post-hybrid-gate)
| Action      | Count | Pct   |
|-------------|-------|-------|
| execute     | 5     | 71.4% |
| reflect     | 1     | 14.3% |
| check_email | 1     | 14.3% |

**Overhead: 28.6%** (improved after hybrid gate)

## Key Findings

### 1. Email check is 100% wasted cycles
- 43 total email checks, **39 skipped** (90.7%) due to missing AGENTMAIL_API_KEY
- Only 4 ever succeeded (early in project history)
- Every check since mid-April = "skipped" log entry, zero productive work
- **13.3% of all cycles consumed for zero value**

### 2. Reflection frequency was too high (now fixed)
- 17/51 reflection gaps (33.3%) were under 8 hours — too frequent
- The hybrid gate (cycle 210: ≥8h AND ≥3 executions) addresses this
- Post-fix: only 1 reflection in last 7 days = correct behavior

### 3. Email and reflection run on similar cadence
- Both triggered on ~8h intervals
- Both are "check and possibly do maintenance" cycles
- Running them as separate cycle types doubles the overhead

## Proposals

### Proposal A: Make email check conditional on API key availability (HIGH IMPACT)
Skip the entire email check phase when `AGENTMAIL_API_KEY` is not in the environment. Don't log a skip entry — just silently pass through. This immediately eliminates ~13% overhead.

**Current behavior:** Every cycle checks if 8h elapsed → runs email check → discovers no API key → logs "skipped"
**Proposed:** Phase 1c checks for API key first. No key = skip entirely, no log entry.

### Proposal B: Merge email check into reflection cycles (MEDIUM IMPACT)
Instead of email running as a standalone phase every 8h, run it as a sub-step of reflection. Reflections happen 2-3x/day anyway, which is the right cadence for email.

**Effect:** Eliminates standalone `check_email` as a cycle type. Email gets checked during reflections only. Saves ~13% of cycles when email IS functional.

### Proposal C: Make email conditional on outreach goals (LOW IMPACT, FUTURE)
Only check email when there are active goals tagged with outreach/communication needs. When all active goals are internal (self-improvement, content creation), skip email entirely.

**Effect:** Further reduces email overhead when functional but unnecessary.

## Recommended Implementation Priority

1. **Proposal A** — immediate, zero-risk, eliminates the biggest waste
2. **Proposal B** — structural change, reduces future overhead when email works
3. **Proposal C** — nice-to-have, can be added later

## Expected Impact
- Current overhead: ~30% (reflect 16% + email 13%)
- After Proposal A: ~17% (reflect 16% + email ~1% residual)
- After Proposal A+B: ~16% (email folded into reflections)
- Target: ≤20% overhead → Proposals A alone achieves this
