---
name: "shape"
description: "Use when the request is vague, contradictory, or could mean several different things; names a solution before the problem is clear; or success is not measurable. Clarify problem, goal, boundary, and success criteria before engineering; do not implement or design architecture."
---

# Shape

## Purpose

Turn a vague or contested request into a short, agreed statement of what problem is being solved and what "done" means — before committing engineering effort. Shape reasons about *whether* something should be built and *what* it is, not *how* to build it.

## Use when

- The request is vague, contradictory, or could mean several different things.
- The request names a solution before the problem is clear ("build a dashboard" when the goal is unverified).
- Success is not measurable, so "done" would be a matter of opinion.
- The problem or intended outcome is not clear enough to enter engineering.

## Do not use when

- The problem, goal, and success criteria are already clear → go straight to `task-router`.
- The work is a clear engineering change → use a change skill directly.
- You only need technical design, not problem framing.
- The user wants implementation now and has already stated the goal.

## Required inputs

- A request or problem statement, however rough.
- The user, present to answer clarifying questions.

## Procedure

1. Restate the request in one sentence. Note any words that are doing too much work.
2. **Investigate first.** Look at what is discoverable in the environment — existing behavior, data, logs, prior decisions — before asking the user. Do not push a look-up-able question onto the user, and do not re-ask anything the user already stated.
3. Classify what the user brought you: is it an **underlying problem**, an **observable symptom**, or a **proposed solution**? If they are anchored on a solution, name the most critical, still-unverified **solution assumption** it rests on.
4. Sort what is unclear into two kinds:
   - **Blocking unknown** — resolving it changes the direction or the risk. Default to resolving it; the user may explicitly choose to carry it as a stated assumption/risk and continue.
   - **Assumption** — low-impact and reversible. You can state it explicitly and continue. Configurable later does not make a number an assumption: if a threshold or target defines what counts as material, success, or in scope, resolve it with the user or leave it explicitly unresolved. Technical tuning that does not materially change the intended outcome (for example page size or layout details) is a non-material assumption.
5. Keep **one primary goal / outcome**. If the request has several goals, name the primary one and treat the rest as context.
6. Ask in **small rounds**, never against a preset total. Blocking decisions have dependencies: each round, ask only the current frontier — 1–3 highest-impact questions whose prerequisites are already settled, and never ask dependent questions in the same round. Never ask what code, docs, data, logs, or the environment can answer; outcome, scope, and value tradeoffs are the user's. When useful, offer a recommended answer with the evidence or assumption behind it, so the user can react to a proposal rather than a blank question.
7. After answers, **recompute**: drop questions an answer made irrelevant and note what the answers newly unlock. Repeat rounds while materially blocking outcome-shaping decisions remain; stop once Problem, Goal, Boundary, and Success criteria are stable enough to hand off — simple requests end in one or two questions.
8. Write the brief: problem, goal, boundary (out of scope), and one or more verifiable success criteria, each connecting an **affected actor** to an **observable consequence or change**. State the assumptions you are carrying. Do not invent success thresholds (days, percentages, near-zero) — resolve them with the user or mark them explicitly unresolved. Recommend the next step (usually `task-router` or a specific change skill); do not implement, and do not grow this into a persona, PRD, opportunity-solution tree, problem-framing canvas, stakeholder map, or How-Might-We workshop.

## Stop conditions

- Problem, Goal, Boundary, and Success criteria are stable enough to hand off, with no unresolved decision that would materially change them and no unconfirmed threshold or target that materially defines success or importance — write the brief and agree it with the user.
- A necessary outcome-shaping choice cannot currently be made — state it and the assumptions you are carrying, and stop.
- The user redirects to implementation, or chooses to proceed with explicit assumptions — hand off with the brief as-is.

## Output contract

A concise brief with four labeled sections, in plain text to the user:

- **Problem:** the situation being addressed, in one or two sentences.
- **Goal:** the single desired outcome, stated as a result, not an activity.
- **Boundary:** what is explicitly out of scope.
- **Success criteria:** one or more checks that would confirm the goal is met, each connecting an affected actor to an observable consequence or change.
- **Assumptions (optional):** assumptions you are carrying, stated explicitly — ordinary low-impact reversible ones, and any material blocking unknown the user explicitly chose to carry as a stated risk. If the user was anchored on a solution, name the key solution assumption that is still unverified.

Do not produce a design document, a task list, or code. Do not create files unless the user asks to keep the brief.

## Example

> **Request:** "We need a notifications system."
>
> **Classification:** "notifications system" is a proposed solution; the underlying problem is that off-hours replies are missed — supported by logs below.
> **Investigated:** current logs show off-hours customer replies are not first acknowledged until the next business day; no existing alert channel for support.
> **Clarified:** the on-call agent must see off-hours replies within 15 minutes.
> **Brief:**
> - **Problem:** Support agents miss customer replies that arrive outside business hours.
> - **Goal:** On-call agents see customer replies within 15 minutes at any hour.
> - **Boundary:** No customer-facing UI changes; no SMS channel in this change.
> - **Success criteria:** the on-call agent (affected actor) sees an off-hours reply within 15 minutes of its arrival (observable consequence).
> - **Assumptions:** the on-call roster already covers off-hours (verified in the schedule file). Solution assumption still unverified: that a notifications system is the right fix, rather than changing the roster.