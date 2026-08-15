---
name: "evaluate"
description: "User-invoked outcome check. Evaluates one target against one expected outcome and its success signals, distinguishes direct evidence from inference, applies materiality so only material findings drive action, and returns CONTINUE, IMPROVE, PIVOT, STOP, or INSUFFICIENT_EVIDENCE. Never triggers implicitly; the user must call it."
---

# Evaluate

## Purpose

A deliberate checkpoint the user invokes to judge whether an effort is heading toward its goal. Evaluate reads evidence and outcomes, then gives a single verdict and the reasoning behind it. It is a judgment tool, not an execution tool.

## Use when

- The user explicitly asks to evaluate, reflect on, or check progress.
- A chunk of work has produced results and the user wants a decision before continuing.
- Enough has changed that the user wants to know whether to continue, improve, pivot, or stop.

## Do not use when

- The user has not asked for an evaluation. Evaluate must never self-trigger from another skill, a hook, or noticing that work "feels done."
- The work is still in progress and no evidence exists yet.
- The user wants the change implemented or fixed — use a change skill, not evaluate.

## Required inputs

- **One target, one expected outcome, and the success signals** that define "on track" for that outcome.
- Evidence of current results: code, tests, output, logs, or a demonstration.
- The user's call to evaluate.

## Procedure

1. Restate the one expected outcome and its success signals in a sentence. If the outcome is missing or unclear, say so and return INSUFFICIENT_EVIDENCE.
2. Gather the evidence that actually exists. Do not infer results that were not observed or measured.
3. For each gap, judge whether the evidence is **direct** (observed) or **indirect** (inferred), and whether the gap is **material** — does it actually affect the outcome or a success signal?
4. Apply materiality: only a finding that materially affects the outcome or a success signal should drive action. A finding is not automatically a task or a backlog item.
5. If action is warranted, recommend the **smallest sufficient response** — the least change that addresses the material finding without overreaching.
6. Return exactly one verdict and a short rationale tied to the evidence.

## Stop conditions

- A verdict is returned.
- Evidence is too thin to support any verdict → return INSUFFICIENT_EVIDENCE and list what evidence is missing.

## Output contract

A single verdict line, followed by a short rationale. The five verdicts:

- **CONTINUE** — on track; keep going.
- **IMPROVE** — direction is right but quality or completeness is short of the outcome; iterate.
- **PIVOT** — direction is wrong; the approach should change before more effort.
- **STOP** — the outcome is met, no longer worth pursuing, or harmful to continue; end the effort.
- **INSUFFICIENT_EVIDENCE** — cannot judge; list the missing evidence.

When a finding is non-material, say so explicitly rather than turning it into an action.

Do not implement changes. Do not edit files. Do not create an Evaluation Record. Do not auto-invoke another skill.

## Host invocation policy

Evaluate is user-only. The skill must not be invoked implicitly by the agent or by any other skill.

- Codex: a policy file marks evaluate as user-only, so the host will not auto-invoke it.
- Claude: the installer marks the installed copy as user-only so the agent cannot auto-invoke it; only an explicit user call runs it.

See `docs/compatibility.md` for how each host enforces this.

## Example

> **Expected:** alerts reach the on-call channel within 15 minutes for all off-hours replies. **Success signals:** ≥99% within 15 min; zero lost on worker crash.
> **Evidence:** one-week trial — 94% within 15 min; six late, all in one outage; zero alerts lost on the one replayed crash.
> **Materiality:** the lost-alert signal is clean (non-material). The latency gap is material — it affects the outcome.
> **Verdict: IMPROVE** — direction is right; the smallest sufficient response is tightening the queue drain, not redesigning delivery.