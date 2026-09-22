---
name: research-synthesis
description: "Synthesize multiple sources into the strongest traceable judgment the evidence supports, with per-claim citations. Use for competitive analyses, policy reviews, market scans, due-diligence summaries. Triggers: \"synthesize these sources\", \"what's the takeaway across...\", \"build the matrix\", \"compare these reports\"."
---

Intentional fork of an upstream skill (`andreaswasita/copilot-cowork-dojo`,
`skills/research-synthesis/SKILL.md`). Fork scope: the position rule, the
so-what, a scope boundary, host neutrality, and pack-internal links. The
pipeline, citation discipline, and matrix audit trail are upstream.

# Research Synthesis

Synthesis ≠ summary. A summary repeats. A synthesis reaches the strongest
judgment the evidence supports.

---

## Quick Reference (the synthesis pipeline)

| Step | Output |
|---|---|
| 1. List sources | 3–10 sources, each named |
| 2. Extract per source | Claim · evidence · date · confidence |
| 3. Synthesis matrix | Rows = themes, cols = sources, cells = each source's view |
| 4. Synthesis paragraph | Where they agree, disagree, contradict |
| 5. So-what | What the evidence supports doing, not doing, or resolving next |

## When to Use

- Competitive analyses, market scans, policy reviews, due-diligence.
- When 3+ sources need a single point of view.
- When the reader needs a judgment across sources, not a literature review.

## Scope Boundary

This skill synthesizes available or gathered evidence. It does **not**
inherently require:

- deep-research orchestration;
- large parallel research programs;
- source-directory machinery;
- a fixed agent fan-out.

If additional evidence is needed, identify the gap and say what would close
it. Do not automatically turn a synthesis into a research program.

## How to Use

1. List sources up front (3–10 is the sweet spot).
2. Extract, *per source*: claim, evidence, date, confidence.
3. Build the **synthesis matrix**: rows = themes, cols = sources, cells =
   what each source says.
4. Write the **synthesis paragraph**: where do sources agree, disagree,
   contradict?
5. Write the **so-what**: what the evidence supports doing, what it supports
   not doing, what remains unresolved, and what evidence is still needed
   before acting.

Every claim in the final output cites which source supports it.

## Examples

| Don't: Summary masquerading as synthesis | Do: Real synthesis |
|---|---|
| "All four reports agree growth is slowing." | "Reports A, B agree on slowing; C disagrees citing different methodology; synthesis: directionally slowing, magnitude contested." |
| No so-what | "So-what: hold off the Q4 expansion plan until the C methodology is replicated." |
| No matrix; conclusions invented | Matrix attached; every cell traceable |
| Skipping disagreement | Disagreement is signal — name it |
| A position manufactured the sources don't carry | "A and B point to slowing; C's methodology contradicts it — directionally slowing, magnitude contested, and not enough to act on" |

## Critical Rules

- **Synthesis must reach the strongest judgment the evidence supports.** A
  supported result may be: a directional judgment; a bounded conclusion;
  competing interpretations; or insufficient evidence. Never manufacture a
  position merely to complete the synthesis.
- **Every claim cites which source.** Inline.
- **Disagreement is signal.** Don't paper over it.
- **The so-what is mandatory.** Name what the evidence supports doing, what
  it supports not doing, what remains unresolved, and what evidence is still
  needed before acting. An honest "not yet, and this is what would settle
  it" is a complete so-what; a manufactured recommendation is not.
- **An unsupported inference must not masquerade as fact.** A claim that
  fits no citation category is an open question, not a finding.
- **Matrix is reproducible.** A second analyst with the same sources should
  land within 90% of the same matrix.

## Citation Discipline

Every factual claim in the final output is one of:

1. **Direct quote** — verbatim from a source, in quotes, with section / page
   reference.
2. **Paraphrase with cite** — your wording, source named inline, link to the
   artifact.
3. **Synthesis claim** — your inference across multiple sources, *labeled as
   such* ("Synthesis: "), and reproducible from the matrix.

No fourth category. If a claim doesn't fit one of the three, it's a guess —
cut it or downgrade it to an open question.

## Hook & So-What Discipline

A synthesis that opens with "This document covers…" gets skipped. Force
these two beats:

- **Hook (first 2 sentences):** the single most consequential finding,
  stated in the reader's vocabulary, with the magnitude. Not the
  methodology.
- **So-what (closing paragraph):** what the evidence supports doing, what it
  argues against, what stays unresolved, and what would change the picture.
  "Nothing to act on yet" is legitimate only when it says what evidence
  would change that.

Produce these two beats *separately* from the body — they need different
attention and different review.

## Common Pitfalls

- Synthesizing without naming the sources first.
- Inventing agreement that isn't there.
- A synthesis that reaches no judgment at all — or one the sources do not
  carry.
- Skipping the matrix — it's the audit trail.
- Hook that opens with methodology instead of finding.
- Treating "insufficient evidence" as failure and forcing a position to
  avoid it.

## Anti-Patterns

- Synthesizing without naming the sources first.
- Inventing agreement that isn't there. Disagreement is signal.
- A synthesis with no judgment. That's a literature review.
- A recommendation stronger than the evidence supports.
- Treating a first-pass synthesis as the synthesis.

## Verify Before Sending

- [ ] Sources listed (3–10).
- [ ] Per-source extraction complete.
- [ ] Matrix attached.
- [ ] Every claim cites source(s).
- [ ] Disagreements named, not papered over.
- [ ] Hook leads with finding + magnitude.
- [ ] So-what names what the evidence supports, leaves unresolved, or still
      requires — and asserts no position beyond what the sources carry.

## Related

Useful combinations, not a mandatory pipeline — each skill works standalone:

- `decision-memo` — when the synthesis feeds a decision a human must make.
- `reviewing-output` — to review the synthesis itself as a deliverable.
