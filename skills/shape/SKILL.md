---
name: "shape"
description: "Optional business-problem clarification. Investigates discoverable facts first, separates blocking unknowns from low-impact assumptions, keeps one primary goal, and asks at most three blocking questions. Defines problem, goal, boundary, and success criteria before engineering begins. Does not implement, design architecture, or write code."
---

# Shape

## Purpose

Turn a vague or contested business request into a short, agreed statement of what problem is being solved and what "done" means — before committing engineering effort. Shape reasons about *whether* something should be built and *what* it is, not *how* to build it.

## Use when

- The request is vague, contradictory, or could mean several different things.
- The request names a solution before the problem is clear ("build a dashboard" when the goal is unverified).
- Success is not measurable, so "done" would be a matter of opinion.
- The request is a business or product question, not a software task.

## Do not use when

- The problem, goal, and success criteria are already clear → go straight to `task-router`.
- The work is a clear engineering change → use a change skill directly.
- You only need technical design, not business framing.
- The user wants implementation now and has already stated the goal.

## Required inputs

- A request or problem statement, however rough.
- The user, present to answer clarifying questions.

## Procedure

1. Restate the request in one sentence. Note any words that are doing too much work.
2. **Investigate first.** Look at what is discoverable in the environment — existing behavior, data, logs, prior decisions — before asking the user. Do not push a look-up-able question onto the user, and do not re-ask anything the user already stated.
3. Classify what the user brought you: is it an **underlying problem**, an **observable symptom**, or a **proposed solution**? If they are anchored on a solution, name the most critical, still-unverified **solution assumption** it rests on.
4. Sort what is unclear into two kinds:
   - **Blocking unknown** — resolving it changes the direction or the risk. Must be answered before proceeding.
   - **Assumption** — low-impact and reversible. You can state it explicitly and continue.
5. Keep **one primary goal / outcome**. If the request has several goals, name the primary one and treat the rest as context.
6. Ask at most **three blocking questions**, ordered by impact, one uncertainty at a time. Stop early if an answer makes the rest unnecessary.
7. Once the blocking unknowns are resolved, write the brief: problem, goal, boundary (out of scope), and one or more verifiable success criteria. Each success criterion should connect an **affected actor** to an **observable consequence or change**. State the assumptions you are carrying.
8. Recommend the next step: usually `task-router` or a specific change skill. Do not implement, and do not grow this into a persona, PRD, opportunity-solution tree, problem-framing canvas, stakeholder map, or How-Might-We workshop.

## Stop conditions

- The brief is written and the user agrees with it.
- The user redirects to implementation — hand off with the brief as-is, including stated assumptions.
- Three questions have not converged — surface the open questions explicitly and stop.

## Output contract

A concise brief with four labeled sections, in plain text to the user:

- **Problem:** the situation being addressed, in one or two sentences.
- **Goal:** the single desired outcome, stated as a result, not an activity.
- **Boundary:** what is explicitly out of scope.
- **Success criteria:** one or more checks that would confirm the goal is met, each connecting an affected actor to an observable consequence or change.
- **Assumptions (optional):** low-impact, reversible assumptions you are carrying, stated explicitly. If the user was anchored on a solution, name the key solution assumption that is still unverified.

Do not produce a design document, a task list, or code. Do not create files unless the user asks to keep the brief.

## Example

> **Request:** "We need a notifications system."
>
> **Classification:** "notifications system" is a proposed solution; the underlying problem is that off-hours replies are missed — supported by logs below.
> **Investigated:** current logs show off-hours customer replies are not first acknowledged until the next business day; no existing alert channel for support.
> **Clarifying questions (blocking):** Who must see off-hours replies, and within what window?
> **Brief:**
> - **Problem:** Support agents miss customer replies that arrive outside business hours.
> - **Goal:** On-call agents see customer replies within 15 minutes at any hour.
> - **Boundary:** No customer-facing UI changes; no SMS channel in this change.
> - **Success criteria:** the on-call agent (affected actor) acknowledges an off-hours reply within 15 minutes of its arrival (observable consequence), for 100% of replies over a one-week trial.
> - **Assumptions:** the on-call roster already covers off-hours (verified in the schedule file). Solution assumption still unverified: that a notifications system is the right fix, rather than changing the roster.