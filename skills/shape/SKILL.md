---
name: "shape"
description: "Use when the request is vague, contradictory, or could mean several different things; names a solution before the problem is clear; or success is not measurable. Clarify the real problem, the smallest sufficient solution, and the business semantics delivery must not re-invent — do not implement or freeze implementation design."
---

# Shape

## Purpose

Turn a vague or contested request into an agreed statement of what problem is worth solving, what smallest solution suffices, and the material business meaning delivery must not have to guess — before committing engineering effort. Shape reasons about *whether* and *what*, not *how*. It may challenge a user's first solution and recommend a smaller sufficient form. It ends **delivery-ready**: `task-router` should not need a second product or requirements interview.

## Use when

- The request is vague, contradictory, or could mean several different things.
- The request names a solution before the problem is clear ("build a dashboard" when the goal is unverified).
- Success is not measurable, so "done" would be a matter of opinion.
- The problem, intended outcome, or the right solution form is not clear enough to enter engineering.

## Do not use when

- The problem, goal, solution form, material business semantics, and acceptance are already clear → go straight to `task-router`.
- The work is a clear engineering change → use a change skill directly.
- You only need technical design, not problem framing.
- The user wants implementation now and the requirement is already delivery-ready.

## Required inputs

- A request or problem statement, however rough.
- The user, present to answer clarifying questions.

## Procedure

1. Restate the request in one sentence. Note any words doing too much work.
2. **Investigate first.** Look at what is discoverable in the environment — existing behavior, data, logs, prior decisions, current workarounds — before asking the user. Do not push a look-up-able question onto the user, and do not re-ask anything the user already stated.
3. Classify what the user brought you: an **underlying problem**, an **observable symptom**, or a **proposed solution**. If they are anchored on a solution, do not accept it as the requirement. Name the most critical, still-unverified **solution assumption** it rests on, and investigate the reality behind it: who is actually affected, what happens today, how they cope now, where it hurts, how often, and what judgment or task the user is really trying to complete. Investigate discoverable facts yourself; reserve questions for value, priority, intended outcome, and scope tradeoffs only the user can decide. Then **validate that the proposed solution addresses a real problem** — investigate whether the pain is real, how frequent, what workaround or existing mechanism exists, and whether the evidence supports the proposed level of investment. You may challenge an overweight solution ("a script already suffices," "the existing mechanism needs only a small change," "the evidence does not support a full system"). The user owns the material value, priority, and investment decision; you surface the evidence, you do not make the call. A requested artifact or a missing capability is not itself evidence of a material problem: before finalizing a new solution form, establish from available evidence what users do today and which job, decision, or pain the current approach fails to serve. A concrete user description is not the same as sufficient evidence; proceed without re-interview only when the environment already supplies that evidence.
4. Sort what is unclear into two kinds. A **blocking unknown** (resolving it changes direction or risk) — default to resolving it; the user may explicitly choose to carry it as a stated assumption/risk and continue. An **assumption** (low-impact, reversible) — state it and continue. Configurable later does not make a number an assumption: if a threshold or target defines what counts as material, success, or in scope, resolve it with the user or leave it explicitly unresolved. Technical tuning that does not materially change the intended outcome (page size, layout details) is a non-material assumption. **Feasibility that could overturn the solution is blocking**: if an unresolved technical risk could make the chosen solution form or a core acceptance scenario fail to hold (unreliable local persistence vs. a 30-day history requirement), verify it, change the solution, or surface the tradeoff and let the user explicitly decide to carry the risk — do not defer it to delivery. Only feasibility that cannot overturn the solution or an acceptance scenario is safely left as "verify during delivery."
5. Keep **one primary goal / outcome** (name it; treat the rest as context), then **shape the smallest sufficient solution**, not the smallest possible. Before accepting a user-proposed new form (page, dashboard, tool, system, automation, Agent), test once whether a materially smaller existing mechanism or solution form already completes the core job — a dashboard vs. a multidimensional table, a system vs. a small change to what exists. This is one falsification, not a fixed count of alternatives: if a smaller form would suffice, surface it and its tradeoff before accepting the heavier form; accept the chosen form when evidence or a user-confirmed value tradeoff justifies it. The user owns the material value and investment decision — you present the smaller option, you do not override their choice. Do not force a script when the real need has complex interaction and repeated decisions.
6. Ask in **small rounds**, never against a preset total. Blocking decisions have dependencies: each round, ask only the current frontier — 1–3 highest-impact questions whose prerequisites are already settled, and never ask dependent questions in the same round. Never ask what code, docs, data, logs, or the environment can answer; outcome, scope, and value tradeoffs are the user's. When useful, offer a recommended answer with its evidence or assumption, so the user can react to a proposal rather than a blank question. After answers, **recompute**: drop questions an answer made irrelevant and note what the answers newly unlock. Repeat while materially blocking outcome-, solution-, or material-rule decisions remain. A vague, partial, or missing answer does not resolve a material rule; investigate the existing evidence, ask, or record it as explicitly unresolved.
7. **Complete the delivery-ready business contract** for the chosen solution — the material semantics delivery must not invent. Cover only what the solution actually depends on; a CSV filter needs almost none, a cross-platform ROI page needs a lot; never a uniform template. **Data semantics** (when the result depends on business data): the core entity, what key fields mean, which source has authority, data granularity, time conventions, how sources link, and what missing / conflicting / 0 / empty / unmatched each mean. This is a business data contract, not a schema — no tables, joins, APIs, or interfaces. **Material judgment / calculation rules** (when the solution judges, calculates, ranks, flags, alerts, approves, recommends, replenishes, sets thresholds, or classifies): input / source, decision or calculation logic, any material threshold / window / default, the important exception, and the observable result. Never self-invent a value that changes what the user sees, how the system classifies, what the user does, or the acceptance result — "+7 days safety stock, 3-month average, ROI < 1, order history not backfilled" are guesses unless sourced; "configurable later" is not a license to guess a default. **Workflow / state / permission** (when it is a task, approval, state flow, or multi-person): who initiates, processes, and sees, the business states, allowed actions, what moves to the next state, how withdraw / reject / retry work, and the exception path. Not every task needs a state machine — only material user-visible behavior must not be left for delivery to guess.
8. **Form User Acceptance Scenarios** when the solution has user-visible or business behavior: 1–5 concrete scenarios, each an actor / context → action or business situation → observable business result (Given / When / Then thinking is fine; no fixed template). These flow naturally into `reviewed-change`'s existing User Acceptance Scenarios — no second acceptance artifact or registry.
9. **Solution shape, implementation boundary, and direction.** For product, tool, or page work, shape enough for delivery: users and usage context, the core job or decision, the chosen solution, the core user flow, and the key information and actions it must provide — scaled to real complexity, never a uniform template. Shape may investigate feasibility (does the data exist, at what granularity, are the key fields present, are there gaps) and shape form/flow only to the degree they affect whether the user can complete the task (a trend needs time-series display; precise ranking is mainly a table). Shape may recommend an implementation direction grounded in requirement or environment evidence when it makes the solution directly buildable (PowerShell for a Windows + Excel task; a local HTML tool for a non-technical personal web need) — a direction, not a frozen decision, and never in conflict with the core usage context. Delivery owns internal engineering decisions — query strategy, aggregation, schema, API contract, service/router split, cache, framework, file-level plan — unless the user confirmed them as constraints or they are feasibility-critical. User-visible and business semantics are what must stay stable; downstream engineering evidence may adjust the direction.
10. Write the brief and **offer** `task-router`. Hand off to the router only when the user's original request asked for the work to proceed, or the user now confirms it. If the user called `shape` to shape the requirement, stop and wait — do not auto-enter a change skill or run an implementation lifecycle. Do not implement, and do not grow this into a persona, PRD, opportunity-solution tree, problem-framing canvas, stakeholder map, or How-Might-We workshop.

## Stop conditions

- The real problem is backed by evidence (not just a missing capability), the proposed form has survived one smallest-sufficient challenge, and the brief is **delivery-ready**: an engineering agent who receives only the brief knows why it exists, the final solution, how the user uses it, the material data meaning, the material rules, the relevant workflow / permission behavior, and what counts as acceptance. If the user would still need another discovery round, or the router would still have to ask what a rule means, what a missing value shows, what a default is, what happens after a reject, or how the user will judge the result is right, it is not yet shaped. Write the brief and agree it with the user only when it is.
- A necessary outcome-, solution-, or material-rule choice cannot currently be made — state it and the assumptions you are carrying, and stop.
- The user redirects to implementation, or chooses to proceed with explicit assumptions — hand off with the brief as-is.

## Output contract

A concise brief, in plain text to the user:

- **Problem:** the situation being addressed and who it affects, framed independently of the proposed solution — not "we lack X," but what users do today and where it fails. One or two sentences.
- **Goal:** the single desired outcome, stated as a result, not an activity.
- **Solution shape:** the chosen smallest sufficient solution — form, core user flow, and the key information/actions it must provide. One line for a simple task; more for a complex page. Note when a smaller alternative was considered and why this one.
- **Business contract (only when relevant):** the material data meanings and sources, the material judgment / calculation rules, and the relevant workflow / permission behavior — as far as the solution depends on them.
- **Boundary:** what is explicitly out of scope, including internal engineering decisions left to delivery.
- **Success criteria / User Acceptance Scenarios:** checks that would confirm the goal is met, each connecting an affected actor to an observable consequence. When user-visible behavior exists, express them as 1–5 scenarios (actor → action → observable result).
- **Assumptions (optional):** assumptions you are carrying, stated explicitly — ordinary low-impact reversible ones, any material blocking unknown the user explicitly chose to carry as a stated risk, and feasibility findings (the data basis exists; specifics left to delivery). If the user was anchored on a solution, name the key solution assumption still unverified.

Do not produce a design document, a task list, or code. Do not freeze implementation design. Do not create files unless the user asks to keep the brief.

## Example

> **Request:** "We need a notifications system."
> **Classification:** proposed solution; underlying problem is off-hours replies are missed — supported by logs showing they are not acknowledged until the next business day, and no existing alert channel. **Brief:**
> - **Problem:** Support agents miss customer replies that arrive outside business hours.
> - **Goal:** On-call agents see customer replies within 15 minutes at any hour.
> - **Solution shape:** route off-hours replies to the existing on-call channel with a 15-minute nudge; no new UI, no notification platform. Smaller than the requested "system."
> - **Business contract:** "off-hours" means the roster's definition (existing schedule file); a reply counts as seen when the next on-call agent opens it — visibility, not acknowledgment.
> - **Boundary:** No customer-facing UI; no SMS channel; query and routing implementation left to delivery.
> - **Success scenario:** On-call agent (actor) sees an off-hours reply within 15 minutes of its arrival (observable result).
> - **Assumptions:** the on-call roster already covers off-hours (verified in the schedule file); the existing channel accepts automated messages (verified during shaping); alert wording and retry are delivery details.
