---
name: "evaluate"
description: "User-invoked outcome check. Evaluates one target against an evaluation anchor (an expected outcome and its success signals, or an evaluation question about the target), distinguishes direct evidence from inference, applies materiality so only material findings drive action, and returns CONTINUE, IMPROVE, PIVOT, STOP, or INSUFFICIENT_EVIDENCE. Never triggers implicitly; the user must call it."
---

# Evaluate

## Purpose

A deliberate checkpoint the user invokes to judge an effort or an existing target against an evaluation anchor. Evaluate reads evidence, then gives a single verdict and the reasoning behind it. It is a judgment tool, not an execution tool.

## Use when

- The user explicitly asks to evaluate, reflect on, or check progress.
- A chunk of work has produced results and the user wants a decision before continuing.
- Enough has changed that the user wants to know whether to continue, improve, pivot, or stop.

## Do not use when

- The user has not asked for an evaluation. Evaluate must never self-trigger from another skill, a hook, or noticing that work "feels done."
- The work is still in progress and no evidence exists yet.
- The user wants the change implemented or fixed — use a change skill, not evaluate.

## Required inputs

- **One target and an evaluation anchor** — an expected outcome with its success signals, or an evaluation question/context about the target.
- Evidence of the target's state: code, tests, output, logs, a document, or a demonstration.
- The user's call to evaluate.

## Procedure

1. Restate the evaluation anchor in a sentence — the expected outcome and its success signals, or the evaluation question about the target. If no target or anchor can be identified, say so and return INSUFFICIENT_EVIDENCE.
2. Gather the evidence that actually exists; do not infer results that were not observed or measured. Stop once more evidence is unlikely to change the verdict or the smallest sufficient response.
3. **Check evidence fitness before judging.** Evidence that looks complete can still not deserve a confident verdict. Ask: who and what period does it cover, and is that the business's real rhythm? Is there a baseline or control to compare against? Which counterexample or failure case was excluded, and was that exclusion justified? Could the metric be satisfied without the outcome being met? A demonstration of success cases is not evidence of the outcome. If fitness is too weak to support any verdict, return INSUFFICIENT_EVIDENCE and name the sampling gap.

When materiality changes the verdict or recommended action, state the evaluation anchor or another authoritative constraint that makes the finding important. An explicit anchor or constraint is sufficient without naming a business role. When the judgment is stakeholder-dependent and not already settled by the evaluation anchor, state the relevant role or authority whose judgment it represents. If the required basis is missing and that gap prevents a verdict, return INSUFFICIENT_EVIDENCE.

4. For each finding, judge whether the evidence is **direct** (observed) or **indirect** (inferred), and whether it is **material** — does it change the judgment against the anchor (for an outcome checkpoint: the outcome or a success signal)?
5. Apply materiality: only a material finding should drive action. A finding is not automatically a task or a backlog item.
6. If action is warranted, recommend the **smallest sufficient response** — a direction that addresses the material finding, without prescribing the exact implementation.
7. Return exactly one verdict — one of the five — and a short rationale tied to the evidence.

## Stop conditions

- A verdict is returned.
- Evidence is too thin to support any verdict → return INSUFFICIENT_EVIDENCE and list what evidence is missing.
- Evidence exists but its fitness cannot support a verdict (unrepresentative period, no baseline, unexplained excluded counterexample, gameable metric) → return INSUFFICIENT_EVIDENCE and name the sampling gap.
- More evidence is unlikely to change the verdict or the smallest sufficient response → stop gathering findings.

## Output contract

A single verdict line — one of the five below — then a short rationale. Include only the material findings that support or qualify the verdict and the smallest sufficient response; anything that changes neither stays out. The five verdicts:

- **CONTINUE** — on track, or no material change is warranted; keep going.
- **IMPROVE** — direction is right but quality or completeness is short of the outcome; iterate.
- **PIVOT** — direction is wrong; the approach should change before more effort.
- **STOP** — the outcome is met, no longer worth pursuing, or harmful to continue; end the effort.
- **INSUFFICIENT_EVIDENCE** — cannot judge; list the missing evidence.

Do not implement changes. Do not edit files. Do not create an Evaluation Record. Do not auto-invoke another skill.

## Host invocation policy

Evaluate is user-only. The skill must not be invoked implicitly by the agent or by any other skill.

- Codex: a policy file marks evaluate as user-only, so the host will not auto-invoke it.
- Claude: the installer marks the installed copy as user-only so the agent cannot auto-invoke it; only an explicit user call runs it.

See `docs/compatibility.md` for how each host enforces this.

## Example

> **Expected:** alerts reach the on-call channel within 15 minutes for all off-hours replies. **Success signals:** ≥99% within 15 min; zero lost on worker crash.
> **Evidence:** one-week trial — 94% within 15 min; six late, all in one outage; zero alerts lost on the one replayed crash.
> **Evidence fitness:** one week covers a normal roster cycle but only one outage, so crash behavior rests on a single replay — enough for the latency signal, thin for the loss signal.
> **Materiality:** the lost-alert signal is clean but weakly sampled (non-material to the verdict, noted as a gap). The latency gap is material — it affects the outcome.
> **Verdict: IMPROVE** — direction is right; the smallest sufficient response is tightening the queue drain, not redesigning delivery.