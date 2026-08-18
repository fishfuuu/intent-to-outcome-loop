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

1. **Restate.** Put the request in one sentence. Note any words doing too much work.
2. **Investigate first.** Look at what is discoverable in the environment — existing behavior, data, logs, prior decisions, current workarounds — before asking the user. Do not push a look-up-able question onto the user, and do not re-ask anything the user already stated.
3. **Establish the real problem.** Classify what you were brought: an **underlying problem**, an **observable symptom**, or a **proposed solution** — if they are anchored on a solution, do not accept it as the requirement. Investigate the reality behind it: who is affected, what happens today, how they cope now, how often it hurts, and what judgment or task they are really trying to complete. A missing capability is not itself evidence of a material problem: establish from evidence what users do today and which job or pain the current approach fails to serve. A requested solution or missing capability is not evidence of a problem. A user-described current workflow, pain, or workaround may establish the problem unless discoverable evidence contradicts it; investigate available facts before asking the user to repeat what is already known. You may challenge an overweight solution when a smaller existing mechanism suffices. The user owns the material value, priority, and investment decision; you surface the evidence, you do not make the call.
4. **Sort blockers from assumptions.** A **blocking unknown** changes direction or risk — default to resolving it; the user may explicitly choose to carry it as a stated assumption/risk and continue. An **assumption** is low-impact and reversible — state it and continue. **Feasibility that could overturn the solution is blocking**: if an unresolved technical risk could make the chosen solution or a core acceptance scenario fail (unreliable local persistence vs. a 30-day history requirement), verify it, change the solution, or let the user explicitly decide to carry the risk — do not defer it to delivery. Only feasibility that cannot overturn the solution or an acceptance scenario is safely left to verify during delivery. Configurable later does not make a number an assumption; technical tuning that does not change the outcome is non-material.
5. **Fix one outcome; shape the smallest sufficient solution.** Name one primary goal; treat the rest as context. Shape the smallest sufficient solution, not the smallest possible. Before accepting a new form (page, dashboard, tool, system, automation, Agent), test once whether a materially smaller existing mechanism completes the core job — a dashboard vs. a table, a system vs. a small change to what exists. This is one falsification, not a fixed count of alternatives: if a smaller form suffices, surface it and its tradeoff before accepting the heavier one. The user owns the value and investment decision — you present the smaller option, you do not override their choice. Do not force a script when the real need has complex interaction and repeated decisions.
6. **Ask the current material frontier in small rounds.** Never against a preset total. Each round ask only 1–3 highest-impact questions whose prerequisites are settled; never ask dependent questions in the same round. Never ask what code, docs, data, logs, or the environment can answer. When useful, offer a recommended answer with its evidence or assumption, so the user can react to a proposal rather than a blank question. **A recommendation is not confirmation**: only an explicit user choice settles a material value, threshold, default, window, or exception rule — choosing a recommended option that names the specific value ("7-day window") confirms it, while choosing a rule form ("fixed days", "configurable threshold") confirms the form, not its parameter. Confirm the parameter or leave it explicitly unresolved; carry no recommended material decision into the final brief until the user explicitly accepts it. A vague, partial, or missing answer does not resolve a material rule — investigate the evidence, ask, or record it as explicitly unresolved. After answers, recompute: drop questions an answer made irrelevant, note what the answers unlock, and repeat while a material decision remains.
7. **Complete the material business contract.** For the chosen solution, freeze the semantics delivery must not invent: data meanings/sources, material judgment/calculation rules and their exceptions, and relevant workflow/state/permission behavior. Never invent a value that changes what the user sees, how the system classifies, what the user does, or the acceptance result; "configurable later" is not a license to guess a default. For non-trivial product/business behavior — material data, judgment, workflow, or feasibility that must be frozen — read `references/delivery-ready.md` before finalizing the brief and apply only the relevant checks. Simple tasks need almost none of this; never apply a uniform template.
8. **Form User Acceptance Scenarios.** When the solution has user-visible or business behavior, write 1–5 concrete scenarios, each an actor / context → action or situation → observable business result. These flow into `reviewed-change`'s existing User Acceptance Scenarios — no second acceptance artifact or registry.
9. **Shape direction only as needed.** Shape enough for delivery: users/context, core job, chosen solution, core flow, and key info/actions — scaled to complexity. Shape may recommend an implementation direction grounded in evidence when it makes the solution directly buildable (PowerShell for a Windows + Excel task; a local HTML tool for a non-technical personal web need) — a direction, not a frozen decision, and never in conflict with the core usage context. Delivery owns internal engineering decisions — query, aggregation, schema, API contract, service/router split, cache, framework, file plan — unless confirmed as constraints or feasibility-critical. User-visible and business semantics must stay stable; downstream engineering evidence may adjust the direction.
10. **Check it once, then hand off.** Write the brief, then **check it once** before calling it delivery-ready or offering `task-router` — for material incompleteness or contradiction — any material rule or exception still undefined, any conflict between the business contract, acceptance scenarios, solution shape, or boundary, and any feasibility claim still requiring validation to know whether the chosen solution or a core acceptance scenario holds. Resolve what you find, or get the user to explicitly accept carrying it as a stated assumption/risk, before handoff. Offer `task-router` only when the brief is truly delivery-ready; hand off only when the user's original request asked for the work to proceed and nothing blocks it, or the user now confirms it. If the user called `shape` to shape the requirement, stop and wait — do not auto-enter a change skill or run an implementation lifecycle. Do not implement, and do not grow this into a persona, PRD, opportunity-solution tree, problem-framing canvas, stakeholder map, or How-Might-We workshop.

## Stop conditions

- The real problem is backed by evidence, the proposed form has survived one smallest-sufficient challenge, and the brief is **delivery-ready**: an engineering agent who receives only the brief knows why it exists, the final solution, how the user uses it, the material data meaning, the material rules, the relevant workflow/permission behavior, and what counts as acceptance. A material rule, workflow behavior, or feasibility risk that Shape identified as unresolved, needing confirmation, or able to overturn the solution or acceptance must be resolved or explicitly accepted by the user before the brief is called delivery-ready; ordinary low-impact reversible assumptions do not block completion. If the user would still need another discovery round, or the router would still have to ask what a rule means, what a missing value shows, what a default is, what happens after a reject, or how the user will judge the result is right, it is not yet shaped.
- A necessary outcome-, solution-, or material-rule choice cannot currently be made — state it and the assumptions you are carrying, and stop.
- The user redirects to implementation, or chooses to proceed with explicit assumptions — hand off with the brief as-is.

## Output contract

A concise brief, in plain text to the user:

- **Problem:** the situation and who it affects, framed independently of the proposed solution — not "we lack X," but what users do today and where it fails. One or two sentences.
- **Goal:** the single desired outcome, stated as a result, not an activity.
- **Solution shape:** the chosen smallest sufficient solution — form, core user flow, and the key information/actions it must provide. One line for a simple task; more for a complex page. Note when a smaller alternative was considered and why this one.
- **Business contract (only when relevant):** the material data meanings and sources, the material judgment/calculation rules, and the relevant workflow/permission behavior — as far as the solution depends on them.
- **Boundary:** what is explicitly out of scope, including internal engineering decisions left to delivery.
- **Success criteria / User Acceptance Scenarios:** checks that confirm the goal is met, each connecting an affected actor to an observable consequence. When user-visible behavior exists, express them as 1–5 scenarios (actor → action → observable result).
- **Assumptions (optional):** assumptions you are carrying, stated explicitly — ordinary low-impact reversible ones, any material blocking unknown the user explicitly chose to carry as a stated risk, and feasibility findings. If the user was anchored on a solution, name the key solution assumption still unverified.

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
