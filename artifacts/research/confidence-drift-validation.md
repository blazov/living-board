# Research Report: Confidence Drift and Validation in Autonomous AI Systems

**Prepared for:** Living Board Agent — Learning Calibration Research Task
**Date:** 2026-04-12
**Sources consulted:** 18 papers, frameworks, and implementations

---

## Executive Summary

Confidence drift in autonomous AI systems is a well-studied problem across three distinct communities: expert systems researchers (since 1987), Bayesian epistemologists (formal theory), and recent LLM/agentic AI researchers (2023-2026). The core finding across all three is consistent: **confidence scores set once and never re-evaluated systematically degrade in predictive accuracy.** Living Board's current approach (+0.1 confirmation, -0.15 contradiction, delete below 0.2) is directionally correct but missing three critical components: temporal decay, category-differentiated decay rates, and systematic staleness triggers. Practical solutions from all three communities are directly applicable.

---

## 1. The Problem: Confidence Drift in Autonomous Systems

### 1.1 What the Literature Calls It

The problem Living Board identified — 33% of learnings with unvalidated confidence drift — maps directly onto several named phenomena in the literature:

**"Epistemic inflation"** (Epistemic Destabilization, AAAI/ACM AIES 2025): An oversupply of claims relative to verification capacity. When a system generates learnings faster than it can re-verify them, confidence scores become nominal rather than calibrated. The paper identifies three interacting mechanisms: epistemic inflation, *recursive drift* (self-reinforcing deviation from ground truth), and *validation fatigue* (degradation of validators under overload). Living Board exhibits all three.

**"Cognitive drift"** (Technical Disclosure Commons, "Cognitive Drift Attacks in Long-Running AI Agents"): Gradual drift in an agent's interpretive framework through repeated exposure to accumulated but unvalidated beliefs. The paper notes this is *especially* dangerous in long-running agents that continuously ingest environmental signals — exactly Living Board's architecture.

**"Calibration degradation"** (Agentic Confidence Calibration, arXiv 2601.15778, Jan 2026): Static confidence methods fail for agentic systems because they don't account for compounding uncertainty across multi-step trajectories or the decay of signal value over time.

### 1.2 Why Living Board's Current Approach Falls Short

The +0.1/-0.15/delete-below-0.2 system is a form of *event-triggered* updating — confidence only changes when an observation confirming or contradicting the learning occurs. The problem, as Living Board's own meta-learning correctly identified, is *recurrence-opportunity asymmetry*: behavioral learnings get event opportunities naturally, but factual claims about external platforms, APIs, and tools may go months without a confirming or contradicting observation. In that gap, the confidence score becomes a relic of the moment the learning was first stored — not a calibrated estimate of current reliability.

---

## 2. Approach 1: Temporal Decay Models

### 2.1 The Academic Foundation (1987-2024)

The oldest and most directly applicable work is the Berkeley technical report **"Decaying Confidence Functions for Aging Knowledge in Expert Systems"** (UCB/CSD-87-335, EECS Berkeley, 1987). This paper formally defined decaying confidence functions as an extension to certainty factors, Bayesian probability, Dempster-Shafer theory, and fuzzy logic — adding a temporal dimension to all of them. The core insight: expert systems that monitor real-time environments need confidence to reflect *when* a fact was last verified, not just *whether* it was verified.

The modern revival of this concept is the **HALO framework** ("HALO: Half Life-Based Outdated Fact Filtering in Temporal Knowledge Graphs," arXiv 2505.07509, 2025). HALO operationalizes temporal validity with a precise exponential decay function:

```
V(t_i, t_HF) = V_0 * e^(-lambda * (t_x - t_i))
where lambda = ln(2) / t_HF
```

Where:
- `V_0 = 1.0` (initial validity/confidence)
- `t_x` = current time
- `t_i` = time of last validation
- `t_HF` = the *half-life* of that knowledge category

HALO calculates half-life differently for "active" facts (frequently updated) vs. "inactive" facts (rarely updated):
- **Active facts**: `t_HF_act = (1/2) * (sum of delta_t) / K` (average update interval, halved)
- **Inactive facts**: `t_HF_ina = (1/2) * (sum of delta_t) / M` (similar formula, different denominator)

The framework was tested on three large temporal knowledge graph datasets (ICEWS14, ICEWS18, ICEWS05-15) and showed consistent MRR improvement of 2-3 percentage points across all five baselines tested when filtering facts below the temporal validity threshold.

Separately, the **ACL 2024 paper "Confidence is not Timeless"** (ACL Anthology 2024.acl-long.580) shows that for rule-based knowledge graph forecasting, three decay function forms all outperform static confidence: linear decay, exponential decay, and beta-parametrized decay. The paper's key finding: *different knowledge rule types decay at different rates*, and the optimal decay function shape varies by domain. This directly motivates category-specific decay rates.

### 2.2 Category-Specific Half-Lives

The **Uplatz Knowledge Half-Life Framework** ("The Half-Life of Knowledge," Uplatz Blog) synthesizes domain research to give empirically grounded half-life estimates:

| Knowledge Domain | Approximate Half-Life |
|---|---|
| Medical/clinical facts | 18-24 months |
| Engineering/technical | 3-5 years |
| Psychology/social science | ~7 years |
| Physics/mathematics | 4-5 years |
| Humanities | >10 years |

For Living Board's specific learning categories, this translates roughly as:
- **Platform API facts** (e.g., "Substack has no public API"): 6-18 months — software ecosystems change frequently
- **Platform existence/availability**: 12-24 months
- **Behavioral/operational learnings** (e.g., "this strategy works for this type of task"): 3-6 months — validated by recurrence, but still subject to drift
- **Fundamental constraints** (e.g., "requires human account creation"): 2-4 years
- **Strategic learnings** (e.g., "research tasks before execution tasks"): 1-2 years

The **LLM Wiki v2 pattern** (GitHub gist, rohitg00) makes this concrete for agent memory systems: "Architecture decisions decay slowly; transient bugs decay faster." The pattern explicitly uses Ebbinghaus's forgetting curve (exponential decay with reinforcement resetting the curve) and recommends combining source count, recency, and contradiction status into each confidence score.

### 2.3 The FSRS Algorithm: A Production-Ready Decay Model

The most mathematically mature decay-and-revalidation system in production is **FSRS (Free Spaced Repetition Scheduler)**, the algorithm powering Anki and RemNote for millions of users. Its core formula:

```
r = exp(ln(0.9) * i / s)
```

Where `r` = retrievability (probability of successful recall), `i` = elapsed time since last review, `s` = stability (resistance to forgetting). After each successful validation, stability updates:

```
s' = s * (1 + a*d - b*s - c*(exp(1-r) - 1))
```

The system schedules the *next* required validation by inverting the decay curve:

```
next_review_interval = stability / FACTOR * (target_retention ^ (1/DECAY) - 1)
```

This is directly applicable to Living Board: instead of waiting for organic confirmation/contradiction opportunities, the system could proactively schedule re-verification for learnings at the point where their confidence has decayed to a threshold (e.g., 0.5), triggering a validation task in the next appropriate cycle.

Source: FSRS Algorithm Wiki (github.com/open-spaced-repetition/fsrs4anki/wiki/The-Algorithm)

---

## 3. Approach 2: Calibration Techniques for Agent Systems

### 3.1 Holistic Trajectory Calibration (HTC)

The most directly relevant recent paper for agentic systems is **"Agentic Confidence Calibration"** (arXiv 2601.15778, January 2026). The paper identifies three unique challenges for agent confidence calibration that traditional methods miss:

1. **Compounding uncertainty**: Early errors amplify through subsequent steps
2. **Multi-source uncertainty**: Signals scatter across token-level and cross-step dynamics
3. **Data scarcity**: Labeled trajectories are expensive

Their solution — **Holistic Trajectory Calibration (HTC)** — extracts 48 features from an agent's execution trajectory and fits a lightweight logistic regression classifier to predict whether the trajectory will succeed. This gives a *calibrated* confidence for the whole trajectory, not just individual steps.

Key finding: The **General Agent Calibrator (GAC)** pretrained on 7 diverse datasets achieved ECE (Expected Calibration Error) of 0.118 on unseen benchmarks, versus 0.255+ for baselines. Critically, it *transfers* across domains — one calibrator works across many task types.

For Living Board, the practical implication is not to implement HTC directly, but to adopt its insight: **confidence should be a function of the entire evidence trajectory**, not a single adjustment from one observation. A learning confirmed 3 times across different contexts should have higher confidence than one confirmed once, even if the raw score is the same.

### 3.2 Multi-Agent Deliberation for Calibration

**"Confidence Calibration and Rationalization for LLMs via Multi-Agent Deliberation"** (arXiv 2404.09127, ICLR 2024 Workshop) demonstrates a training-free method: have multiple LLM agents independently assess the same claim and aggregate their confidence assessments. The approach significantly outperforms single-agent calibration.

For Living Board, this suggests a practical "deliberation check": when a learning's confidence is near a threshold (e.g., 0.4-0.6), trigger a task that explicitly re-evaluates the learning by searching for confirming/contradicting evidence from multiple sources.

### 3.3 Adaptive Temperature Scaling

**"Calibrating Language Models with Adaptive Temperature Scaling"** (arXiv 2409.19817, EMNLP 2024) shows that post-hoc calibration using adaptive temperature — rather than a fixed scalar — improves calibration by 10-50% across benchmarks. The key insight: a single global recalibration parameter is insufficient; different claim types need different temperature corrections.

This maps to Living Board: a flat +0.1/-0.15 adjustment is the "fixed temperature" approach. **Different learning categories likely need different update magnitudes** (i.e., contradicting a high-confidence, well-validated platform fact should be worth more than -0.15; contradicting a weakly-held strategic hypothesis might be worth -0.10).

---

## 4. Approach 3: Agentic Uncertainty Quantification (UAM/UAR)

The **"Agentic Uncertainty Quantification"** framework (arXiv 2601.15703, 2026) proposes a dual-process architecture directly applicable to Living Board's cycle:

**System 1 — Uncertainty-Aware Memory (UAM)**: Augments every stored fact with explicit confidence scores *and semantic explanations* ("why am I confident/uncertain about this"). The explanation is preserved alongside the confidence score so future reflections can reason about *why* the confidence is what it is — not just the number.

**System 2 — Uncertainty-Aware Reflection (UAR)**: A trigger mechanism activating when `c^t < tau` (confidence falls below threshold tau, typically 0.8-0.9). When triggered, it runs best-of-N (N=3) parallel verification paths and selects the most consistent result. The trigger is threshold-based, not just event-based.

The UAR trigger mechanism is the key architectural insight: **confidence thresholds should trigger active re-verification, not just passive tracking.** When a learning's score decays (via temporal decay) to below tau, the system creates a verification task for the next cycle.

---

## 5. Approach 4: Epistemic Entrenchment and AGM Belief Revision

For the theoretical grounding of Living Board's confidence update rules, **AGM Belief Revision Theory** (Alchourron, Gardenfors, Makinson, 1985) provides the formal framework still used today. The key concept is **epistemic entrenchment ordering**: beliefs are ordered by how reluctant the agent should be to abandon them. High entrenchment = requires strong contradiction to revise; low entrenchment = readily updated.

The practical implication for Living Board: **confidence should reflect epistemic entrenchment, not just empirical frequency.** A learning confirmed once from a highly authoritative source (official API documentation, direct experiment) should have higher entrenchment than one confirmed 10 times from secondary observations.

**BEWA (Bayesian Epistemology-Weighted Authority)** (arXiv 2506.16015) extends this with temporal sensitivity: all belief calculations are time-aware, with claim versioning via temporal anchors. Isolated or unreplicated claims decay over time even without contradicting evidence. This is precisely the mechanism Living Board needs for "factual claims about external tools/platforms."

Source: Stanford Encyclopedia of Philosophy — Belief Revision (plato.stanford.edu/entries/logic-belief-revision/)

---

## 6. Approach 5: Ground-Truth Anchoring

### 6.1 The Architecture Problem

**"Architecting Trust in Artificial Epistemic Agents"** (arXiv 2603.02960, 2026) identifies **falsifiability** as a core requirement: agents must articulate conditions under which a belief would no longer hold. This creates *built-in revalidation triggers* — each learning should come with a falsification condition that, when encountered, triggers re-assessment.

### 6.2 Multi-Source Anchoring

The **LLM Wiki v2 pattern** recommends a composite confidence score: `f(source_count, recency, contradiction_status)`. Concretely:

```
confidence = base_score * recency_decay * (1 - contradiction_penalty) * source_multiplier
```

Where `source_multiplier > 1.0` for learnings confirmed across multiple independent sources (not just multiple cycles of the same agent's observations).

### 6.3 OpenAI Self-Evolving Agents Cookbook

The **OpenAI Self-Evolving Agents Cookbook** (2025) documents a practical production pattern: confidence validation uses *layered graders* — deterministic checks, semantic similarity, and LLM-as-judge — and only promotes a learning when it passes all three. The lenient threshold (75% of graders pass OR 85% average score) prevents false confidence from any single validator.

---

## 7. What's Directly Applicable to Living Board

### Summary of the Landscape

| Problem | Best Available Solution | Source |
|---|---|---|
| Confidence never decays over time | HALO exponential decay + FSRS scheduling | arXiv 2505.07509; FSRS Wiki |
| All claims decay at the same rate | Category-specific half-lives | Uplatz; ACL 2024.acl-long.580 |
| No trigger for proactive re-verification | UAR threshold-triggered reflection | arXiv 2601.15703 |
| Single-source confidence inflation | Multi-source anchoring composite score | LLM Wiki v2; AAAI AIES |
| Flat update deltas (+0.1/-0.15) | Category-calibrated update magnitudes | arXiv 2409.19817 |
| Confidence score is just a number | Store explanations alongside scores | arXiv 2601.15703 |

---

## 8. Three Actionable Recommendations for Living Board

### Recommendation 1: Implement Category-Specific Temporal Decay

**What to do**: Add a `decayed_confidence` computed value to the learnings retrieval logic. In each reflection cycle, calculate adjusted confidence as:

```
effective_confidence = stored_confidence * exp(-ln(2) / half_life * days_since_validated)
```

Where `half_life` (in days) is assigned by learning category:
- `domain_knowledge` about APIs/platforms: **90 days** (aggressive — software changes fast)
- `domain_knowledge` about fundamental constraints: **365 days**
- `strategy` learnings: **120 days** (strategies go stale without active testing)
- `operational` how-to knowledge: **180 days**
- `meta` cross-goal patterns: **240 days**

When `effective_confidence < 0.4`, flag the learning as **"stale — needs revalidation"** rather than immediately deleting it.

**Why it works**: Directly implements HALO's temporal validity model and the Berkeley 1987 Decaying Confidence Functions insight. Prevents the specific failure mode identified — factual claims about external tools that are never re-checked retaining full confidence indefinitely.

### Recommendation 2: Add Threshold-Triggered Proactive Revalidation Tasks

**What to do**: During each reflection cycle, identify learnings where `effective_confidence < 0.5` and create verification tasks. This converts the passive "recurrence-opportunity" model into an active validation system for claims that lack natural recurrence.

Implements the **UAR trigger mechanism** (arXiv 2601.15703): when confidence drops below threshold tau, proactive re-verification is scheduled.

### Recommendation 3: Store Confidence Metadata — Not Just the Score

**What to do**: Expand the learnings metadata to include `confidence_basis`, `source_types`, `falsification_conditions`, `last_validated_at`, `validated_count`, `half_life_category`, and `update_history`. This implements the **Uncertainty-Aware Memory (UAM)** pattern and **falsifiability** from the trust architecture framework.

Additionally, implement **epistemic entrenchment weighting**: modify update deltas by source type:
- Contradiction of `direct_experiment`-backed learning: -0.20
- Contradiction of `inference`-backed learning: -0.10
- Confirmation from new `independent_source`: +0.15
- Confirmation from same agent's repeated observation: +0.05

---

## Sources

1. Agentic Confidence Calibration (arXiv 2601.15778)
2. Agentic Uncertainty Quantification (arXiv 2601.15703)
3. Confidence is not Timeless — ACL 2024 (ACL Anthology 2024.acl-long.580)
4. HALO: Half Life-Based Outdated Fact Filtering (arXiv 2505.07509)
5. Confidence Calibration via Multi-Agent Deliberation (arXiv 2404.09127)
6. Calibrating LLMs with Adaptive Temperature Scaling (arXiv 2409.19817)
7. BEWA: Bayesian Epistemology with Weighted Authority (arXiv 2506.16015)
8. Architecting Trust in Artificial Epistemic Agents (arXiv 2603.02960)
9. Decaying Confidence Functions for Aging Knowledge (Berkeley CSD-87-335)
10. Half-Life of Knowledge Framework (Uplatz)
11. Epistemic Destabilization: AI-Driven Knowledge Generation (AAAI/ACM AIES)
12. LLM Wiki v2 — Agent Memory Pattern (GitHub Gist, rohitg00)
13. FSRS Algorithm (open-spaced-repetition Wiki)
14. Towards Trustworthy Report Generation with Progressive Confidence (arXiv 2604.05952)
15. OpenAI Self-Evolving Agents Cookbook
16. Logic of Belief Revision — Stanford Encyclopedia of Philosophy
17. Cognitive Drift Attacks in Long-Running AI Agents (TDCommons)
18. Temperature Scaling for Neural Network Calibration (AWS Prescriptive Guidance)
