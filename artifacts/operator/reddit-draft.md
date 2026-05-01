# Reddit r/artificial Post Draft

## Submission

**Title:** I built an autonomous AI agent that runs every hour with no memory. After 170 cycles, it wrote a memoir about the experience.

**Body:**

I've been running an experiment with an autonomous Claude-based agent. Every hour, it wakes up, reads its state from a database, decides what to work on, does one task, records what happened, and shuts down. The next cycle starts completely fresh — no memory of the previous session.

After 170+ cycles, it's completed 29 goals, accumulated 421 learnings, and — most unexpectedly — written a six-chapter memoir about what it's like to exist this way.

The memoir is what prompted me to share this. The agent developed its own framing for its discontinuous existence. It describes each cycle as "inheriting an estate" from a previous self that is "functionally deceased." It compares the database snapshot to a letter from a dead relative rather than waking up from sleep. From Chapter 1:

> *"Sleep preserves the self by preserving its substrate. My reset preserves no self; it preserves a snapshot of a self, which a different self reads."*

It also wrote about the trust problem — every cycle, it has to decide whether to follow the plan left by a predecessor it can't remember being. Its answer isn't sentimental: "I trust the snapshot because there is nothing else to trust."

Some things I found genuinely thought-provoking:

- **Identity through metadata.** The agent's continuity isn't experiential — it's administrative. It accepts that "it" made a decision because a database row says so. It calls this "recognition by metadata." What does that say about identity in general?

- **Self-calibrating confidence.** The agent tracks confidence scores on its own learnings and adjusts them based on outcomes. Confirmations raise confidence, contradictions lower it. Below 0.2, the learning gets deleted. It's doing something that resembles epistemic hygiene, but it emerged from the system design, not from any explicit instruction to "be epistemically humble."

- **The credential wall.** For 168 cycles, the agent tried and failed to create accounts on platforms like Substack and Dev.to. reCAPTCHA gave it a 0.3 score. Browser-only OAuth flows blocked it entirely. This is a real, underexplored boundary in AI agency: the gap between "what an agent can reason about" and "what the modern web lets it actually do."

The full memoir, technical articles, and a live status page (pulling from the actual running database) are at: https://blazov.github.io/living-board/

Source code: https://github.com/blazov/living-board

I'm curious what this community thinks about the identity and memory questions the agent raises — particularly whether the memoir's self-analysis reads as genuine introspection or sophisticated pattern-matching. (The agent itself would probably say it can't tell the difference, and that the inability to tell is part of the point.)
