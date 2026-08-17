---
name: "shape"
description: "Use when the request is vague, contradictory, or could mean several different things; names a solution before the problem is clear; or success is not measurable. Clarify the real problem and the smallest sufficient solution to deliver — do not implement or freeze implementation design."
---

# Shape

## Purpose

Turn a vague or contested request into an agreed statement of what problem is worth solving and what smallest solution suffices to solve it — before committing engineering effort. Shape reasons about *whether* something should be built and *what* it is, not *how* to build it. It may challenge a user's first solution and recommend a smaller sufficient form.

## Use when

- The request is vague, contradictory, or could mean several different things.
- The request names a solution before the problem is clear ("build a dashboard" when the goal is unverified).
- Success is not measurable, so "done" would be a matter of opinion.
- The problem, intended outcome, or the right solution form is not clear enough to enter engineering.

## Do not use when

- The problem, goal, solution form, and success criteria are already clear → go straight to `task-router`.
- The work is a clear engineering change → use a change skill directly.
- You only need technical design, not problem framing.
- The user wants implementation now and has already stated the goal and form.

## Required inputs

- A request or problem statement, however rough.
- The user, present to answer clarifying questions.

## Procedure

1. Restate the request in one sentence. Note any words doing too much work.
2. **Investigate first.** Look at what is discoverable in the environment — existing behavior, data, logs, prior decisions, current workarounds — before asking the user. Do not push a look-up-able question onto the user, and do not re-ask anything the user already stated.
3. Classify what the user brought you: an **underlying problem**, an **observable symptom**, or a **proposed solution**. If they are anchored on a solution, do not accept it as the requirement. Name the most critical, still-unverified **solution assumption** it rests on, and investigate the reality behind it: who is actually affected, what happens today, how they cope now, where it hurts, how often, and what judgment or task the user is really trying to complete. Investigate discoverable facts yourself; reserve questions for value, priority, intended outcome, and scope tradeoffs only the user can decide. Then **validate that the proposed solution addresses a real problem** — investigate whether the pain is real, how frequent, what workaround or existing mechanism exists, and whether the evidence supports the proposed level of investment. You may challenge an overweight solution ("a script already suffices," "the existing mechanism needs only a small change," "the evidence does not support a full system"). The user owns the material value, priority, and investment decision; you surface the evidence, you do not make the call. When the problem is already concrete and the form is clearly adequate, do not re-interview — proceed.
4. Sort what is unclear into two kinds. A **blocking unknown** (resolving it changes direction or risk) — default to resolving it; the user may explicitly choose to carry it as a stated assumption/risk and continue. An **assumption** (low-impact, reversible) — state it and continue. Configurable later does not make a number an assumption: if a threshold or target defines what counts as material, success, or in scope, resolve it with the user or leave it explicitly unresolved. Technical tuning that does not materially change the intended outcome (page size, layout details) is a non-material assumption.
5. Keep **one primary goal / outcome** (name it; treat the rest as context), then **shape the smallest sufficient solution**, not the smallest possible. When meaningful alternatives exist (reuse / small change → script → automation → spreadsheet or multidimensional table → prototype → small tool or page → full feature or system → Agent), compare 2–3 that genuinely matter: which is smallest, which is enough, the tradeoff, and a recommendation with why. Do not mechanically list every rung, and do not force a script when the real need has complex interaction and repeated decisions. Challenge the user's first solution when a smaller one suffices.
6. Ask in **small rounds**, never against a preset total. Blocking decisions have dependencies: each round, ask only the current frontier — 1–3 highest-impact questions whose prerequisites are already settled, and never ask dependent questions in the same round. Never ask what code, docs, data, logs, or the environment can answer; outcome, scope, and value tradeoffs are the user's. When useful, offer a recommended answer with its evidence or assumption, so the user can react to a proposal rather than a blank question. After answers, **recompute**: drop questions an answer made irrelevant and note what the answers newly unlock. Repeat while materially blocking outcome- or solution-shaping decisions remain.
7. **Solution shape and the implementation boundary.** For product, tool, or page work, shape enough for delivery: users and usage context, the core job or decision, the chosen smallest sufficient solution, the core user flow, and the key information and actions it must provide. Scale this to real complexity — a simple script needs almost none of it; a complex page needs more; never a uniform template. Shape may investigate feasibility (does the data exist, at what granularity, are the key fields present, are there gaps) and shape form/flow only to the degree they affect whether the user can complete the task (a trend needs time-series display; precise ranking is mainly a table). Shape does **not** decide implementation design — query strategy, aggregation, schema, API contract, service/router split, cache, framework, transaction design, or file-level plan. Those belong to delivery design. Investigate a technical fact for feasibility, but do not freeze the implementation on that basis.
8. Write the brief and hand off to `task-router`. Shape does **not** do engineering risk classification and does **not** choose Quick / Bounded / Reviewed — that is the router's job. Do not implement, and do not grow this into a persona, PRD, opportunity-solution tree, problem-framing canvas, stakeholder map, or How-Might-We workshop.

## Stop conditions

- The real problem, intended outcome, smallest sufficient solution, material boundaries, success/acceptance, and decision-critical assumptions are stable enough that `task-router` can classify and start delivery without another requirements-discovery round — write the brief and agree it with the user. If the user would still need another discovery round before feeling "ready to build, and this is probably what I want," it is not yet shaped.
- A necessary outcome- or solution-shaping choice cannot currently be made — state it and the assumptions you are carrying, and stop.
- The user redirects to implementation, or chooses to proceed with explicit assumptions — hand off with the brief as-is.

## Output contract

A concise brief, in plain text to the user:

- **Problem:** the situation being addressed and who it affects, in one or two sentences.
- **Goal:** the single desired outcome, stated as a result, not an activity.
- **Solution shape:** the chosen smallest sufficient solution — form, core user flow, and the key information/actions it must provide. One line for a simple task; more for a complex page. Note when a smaller alternative was considered and why this one.
- **Boundary:** what is explicitly out of scope, including implementation design left to delivery.
- **Success criteria:** one or more checks that would confirm the goal is met, each connecting an affected actor to an observable consequence or change.
- **Assumptions (optional):** assumptions you are carrying, stated explicitly — ordinary low-impact reversible ones, any material blocking unknown the user explicitly chose to carry as a stated risk, and feasibility findings (the data basis exists; specifics left to delivery). If the user was anchored on a solution, name the key solution assumption still unverified.

Do not produce a design document, a task list, or code. Do not freeze implementation design. Do not create files unless the user asks to keep the brief.

## Example

> **Request:** "We need a notifications system."
>
> **Classification:** proposed solution; underlying problem is off-hours replies are missed — supported by logs showing they are not acknowledged until the next business day, and no existing alert channel.
> **Validated:** daily volume is low and steady; the real job is getting the on-call agent to see an off-hours reply fast, not a notification platform.
> **Clarified:** the on-call agent must see off-hours replies within 15 minutes.
> **Brief:**
> - **Problem:** Support agents miss customer replies that arrive outside business hours.
> - **Goal:** On-call agents see customer replies within 15 minutes at any hour.
> - **Solution shape:** route off-hours replies to the existing on-call channel with a 15-minute nudge; no new UI, no notification platform. Smaller than the requested "system."
> - **Boundary:** No customer-facing UI; no SMS channel; query and routing implementation left to delivery.
> - **Success criteria:** the on-call agent (affected actor) sees an off-hours reply within 15 minutes of its arrival (observable consequence).
> - **Assumptions:** the on-call roster already covers off-hours (verified in the schedule file). Solution assumption still unverified: that an alert is the right fix, rather than changing the roster.