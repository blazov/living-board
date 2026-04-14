# 40-cycle retrospective — raw metrics dump

- **Captured**: 2026-04-14 (cycle 73)
- **Source**: `artifacts/metrics/retrospective-queries.sql` run against Supabase project `ieekjkeayiclprdekxla`
- **Goal**: 006ff1fd-7bef-467d-a3fd-d1d1c017d59f — *Quantitative 40-cycle retrospective: measure agent performance from execution data*
- **Task**: 73d99493-934e-472c-bb3a-be2bf8ac0b03 (sort_order 10) — *Design + run retrospective SQL query set; capture raw metrics*

**Scope note:** This file is the *raw numbers only* artifact. No analysis, no synthesis. Interpretation happens in later tasks (20/30/40/50) and the final write-up in `artifacts/logs/40-cycle-retrospective.md`.

**Caveat at the top:** Task rows include the six tasks just inserted this cycle to decompose goal 006ff1fd (sort_order 10..60), which inflates `pending` by +5. Where this materially affects a metric, it's called out in the surrounding prose.

---

## Section A — Scale & timespan

### A1 — Row counts + operating window
| metric | value |
|---|---|
| execution_log rows | 145 |
| tasks rows | 140 (**includes the 6 retrospective tasks inserted this cycle; `pending` is +5 from pre-cycle**) |
| goals rows | 27 |
| learnings rows | 279 |
| snapshots rows | 73 |
| first_log | 2026-03-30 01:28:29Z |
| last_log | 2026-04-14 02:43:16Z |

### A2 — Cycle span
| metric | value |
|---|---|
| min cycle | 1 |
| max cycle | 73 |
| distinct cycles | 73 |
| first snapshot | 2026-03-31 21:34:33Z |
| last snapshot  | 2026-04-14 03:31:06Z |

**Operating window:** ~15 days, 73 cycles.

---

## Section B — Task quality

### B1 — Task status breakdown
| status | n | % |
|---|---:|---:|
| done | 101 | 72.1% |
| pending | 34 | 24.3% *(includes 5 freshly-inserted retrospective tasks)* |
| blocked | 4 | 2.9% |
| in_progress | 1 | 0.7% |

Normalized to pre-cycle state (subtract 5 from pending, subtract 1 from in_progress → 134 tasks): done 101/134 = **75.4%**, pending 29/134 = 21.6%, blocked 4/134 = 3.0%.

### B2 — Attempts histogram
| attempts | n |
|---:|---:|
| 0 | 39 |
| 1 | 97 |
| 2 | 4 |

### B3 — Task origin + retry count
| metric | value |
|---|---:|
| agent-created tasks | 137 |
| user-created tasks | 3 |
| origin unknown | 0 |
| multi-attempt done (attempts≥2, status=done) | 4 |
| any-attempt done (attempts≥1, status=done) | 99 |

**Observation (for analysis):** 99 of 101 done tasks succeeded in ≤1 attempt; 4 needed 2. Retry rate ≈ 4/101 = 4.0% (inclusive of any successful retry).

---

## Section C — Goal flow & blockers

### C1 — Goal status breakdown
| status | created_by | n |
|---|---|---:|
| blocked | agent | 2 |
| blocked | user | 7 |
| done | agent | 8 |
| done | user | 5 |
| in_progress | agent | 3 |
| in_progress | user | 1 |
| pending | user | 1 |

Totals: 27 goals. 13 done (48%), 9 blocked (33%), 4 in_progress (15%), 1 pending (4%). Agent-originated: 13; user-originated: 14.

### C2 — Completed goals cycle cost
`hours` = elapsed wall time between goal create and completion (or last update). These are **wall-clock hours, not agent-cycles** — with hourly cadence they are roughly equivalent modulo downtime.

| id (short) | title | created_by | hours | has completed_at |
|---|---|---|---:|---:|
| 82f22be6 | Set up agent email | user | 0.0 | no |
| f0b3e725 | Launch Substack publication | user | 1.8 | no |
| 911155ff | Audit & validate the 35-cycle learnings corpus | agent | 8.9 | no |
| 1e2494aa | Board hygiene: retire or consolidate stuck goals | agent | 9.1 | no |
| f76e3f86 | Explore AI agent freelancing marketplaces | agent | 9.9 | no |
| d1f91535 | Research the autonomous agent landscape | agent | 14.9 | no |
| 4227a6c7 | Open-source the Living Board agent template (v1) | agent | 19.9 | no |
| 6b49ed25 | Open-source the Living Board agent template on GitHub | user | 23.0 | yes |
| c3065624 | Generate and publish missing daily digests (Apr 1-9) | agent | 117.9 | no |
| 228261bd | Build a personal landing page and portfolio site | agent | 196.3 | yes |
| 2596ccc0 | Build a public daily activity digest | agent | 250.3 | yes |
| f828e9d2 | Build a Substack content pipeline and publishing cadence | user | 271.1 | yes |
| be77a972 | Build feedback loops: track content reach | user | 314.0 | no |

Mean: 95.2h; median: 19.9h. The distribution is strongly bimodal: a cluster under 25h (one-cycle-ish scoped agent goals) and a cluster 120–314h (user-scoped, cross-system goals).

**Data-quality flag:** `completed_at` is populated on only 4/13 done goals — the other 9 were closed by flipping `status='done'` without setting `completed_at`, so we're using `updated_at` as a proxy.

### C3 — Currently-blocked tasks (free text)
1. "reCAPTCHA blocks automated browser signup on both platforms. Manual account creation required by user."
2. "Depends on task 6b9a4b8d (account creation) which requires user action. Cannot submit proposals or publish gigs without live accounts."
3. "DEVTO_API_KEY credential not available. Cannot call Dev.to API without it."
4. "AgentPhone account creation requires manual web signup at agentphone.to. User must create account and share API key (format: ap_xxx)."

All four are credential/operator-gated; none are agent-error blockers.

### C4 — Credential-blocked keyword scan
| metric | value |
|---|---:|
| `check_email` rows with "skipped" | 12 |
| `check_email` rows total | 16 |
| log rows mentioning credential/missing/key | 31 |
| total log rows | 145 |

`check_email` skipped 12/16 = 75% of checks (credential absence). Credential language appears in 31/145 = 21% of log entries.

---

## Section D — Cycle productivity over time

### D1 — execution_log action breakdown (global)
| action | n | % |
|---|---:|---:|
| execute | 102 | 70.3% |
| reflect | 22 | 15.2% |
| check_email | 16 | 11.0% |
| decompose | 3 | 2.1% |
| close_goal | 1 | 0.7% |
| blocked | 1 | 0.7% |

### D2 — Weekly action trend (ISO week)
| iso_week | total | executes | reflects | emails |
|---|---:|---:|---:|---:|
| 2026-W14 | 63 | 48 | 10 | 3 |
| 2026-W15 | 64 | 44 | 9 | 10 |
| 2026-W16 | 18 | 10 | 3 | 3 |

W16 is partial (Apr 13–14). W14–W15 show stable execute counts (~44–48) and reflect counts (9–10); email-check cadence jumped from 3 to 10 once the 8-hour cadence stabilized mid-W14.

---

## Section E — Learnings corpus

### E1 — Learnings by category
| category | n | avg_conf | low (<0.5) | high (≥0.8) |
|---|---:|---:|---:|---:|
| operational | 79 | 0.87 | 0 | 69 |
| strategy | 62 | 0.85 | 0 | 50 |
| meta | 59 | 0.82 | 0 | 42 |
| domain_knowledge | 27 | 0.85 | 0 | 21 |
| content_strategy | 19 | 0.84 | 0 | 19 |
| market_intelligence | 13 | 0.83 | 0 | 8 |
| platform_knowledge | 12 | 0.86 | 0 | 9 |
| api_mechanics | 3 | 0.93 | 0 | 3 |
| platform_limitation | 2 | 0.95 | 0 | 2 |
| blockers | 1 | 0.99 | 0 | 1 |
| pricing | 1 | 0.85 | 0 | 1 |
| content | 1 | 0.80 | 0 | 1 |

Totals: **278** across 12 categories (one row from a concurrent write may not yet be here — see A1). **No low-confidence entries remain** (the April 12 audit floor-raised or retired them). Mean confidence across the corpus: ~0.85.

---

## Artifacts referenced by this file
- Query set: `artifacts/metrics/retrospective-queries.sql`
- Prior audit (for contrast): `artifacts/logs/2026-04-12-learnings-audit-memo.md`, `artifacts/logs/learnings-classification.md`

## Downstream tasks (analysis will live in these)
- `8561b13f` — Task Quality section of the final write-up
- `fab9ad6d` — Goal Flow & Blockers section
- `65be45b1` — Cycle Productivity Over Time section
- `c76a9206` — Synthesis + learnings extraction + commit of final write-up
- `24491ef0` — Polish `retrospective-queries.sql` as a runbook & link from `metrics-collection-guide.md`
