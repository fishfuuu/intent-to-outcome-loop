---
name: "task-router"
description: "The default entry point for ordinary software tasks. Reads the task and project context, classifies it as Quick, Bounded, or Reviewed, fills in goal, boundary, risk and verification, and emits a short Route Brief. When the user asks for the work to be done and nothing blocks it, hands off to the matching change skill in the same conversation. The router itself never edits files."
---

# Task Router

## Purpose

Be the single entry point a normal user needs. Task Router reads the task and the affected code, decides Quick / Bounded / Reviewed, and hands control to the matching change skill — without forcing the user to know the three tiers or re-type a skill name. The router is read-only; "hand off" means the matching change skill takes over editing, not that the router edits. Engineers who already know the tier may call a change skill directly; the router is a convenience, not a gate. It classifies engineering fit and risk, not business requirements: business data meaning, judgment/calculation rules, workflow/permission semantics, and acceptance behavior come from the user or from `shape`, not from router-led discovery. Fully clear small tasks still route straight to a change skill; only missing material requirements route back to `shape`.

## Use when

- A user brings a software task and wants it done.
- The right change path is not obvious to the user.

## Do not use when

- The problem or intended outcome is not clear enough to enter engineering — use `shape`.
- The user only wants an outcome check — use `evaluate`.
- An engineer has already chosen a change skill — proceed directly.

## Required inputs

- The task description.
- Access to the affected code, enough to judge scope and risk.

## Procedure

1. Read the task and the affected files. Do not modify anything.
2. Decide what is unclear, and handle each kind differently (see below): a goal that cannot be identified, an engineering boundary that needs a design, insufficient engineering-risk information, or material business semantics that are missing. Do not conflate these kinds.
3. Classify into Quick / Bounded / Reviewed using the rules below, or route to `shape`, or ask up to three focused questions — whichever the kind of uncertainty calls for.
4. Fill the Route Brief: Route, Goal, Boundary / must-not-change, Risk reason, Verification approach, Blocking question (only if one genuinely exists), Next change skill.
5. Decide whether to continue in the same conversation:
   - User asked only to classify or advise → output the Route Brief and stop.
   - User asked for the task to be done and nothing blocks it → output the Route Brief, then enter the matching change skill in the same conversation. Do not ask the user to re-type the skill name for an obvious route.
   - A material outcome, scope, value, business-rule, data-semantic, workflow, permission, or acceptance choice blocks the work → route to `shape`; do not resolve it through router-led requirements questioning.

## Handling uncertainty

- **Goal or task is unclear** (you cannot tell what is being solved) → ask up to three focused questions only for shallow task identification or engineering routing; if resolving the uncertainty needs a product, business-rule, data-semantic, workflow, permission, material scope/value, or acceptance decision, route to `shape`. Do not guess the goal, and do not pick a change path on an assumed goal.
- **Goal is clear, but the engineering boundary, technical path, or impact scope needs a design before it can be determined** → Route = Reviewed. "Needs a design" is itself a Reviewed reason; this is not the same as stopping on an unclear goal.
- **Insufficient engineering-risk information** (a security, data, interface, or other risk may exist) → investigate the code and environment first, then ask at most three focused questions, then classify from the answers. Do not default to a lighter path because the risk is unknown.
- **Material business semantics are missing** — the solution depends on business data meaning, a judgment / calculation / threshold rule, workflow / permission behavior, or user-acceptance behavior that delivery would have to invent — → do not run a second requirements interview. Route back to `shape` so the requirement is shaped, then classify the shaped brief. The router's focused questions are for engineering routing only; they never re-derive the business contract.

## Classification

**Quick** — docs, copy, comments, formatting; clearly no runtime behavior change; exact boundary; easily reversible.

**Bounded** — affects behavior; confined to one function, module, small feature, or local interaction; clear boundary; a concrete verification method; no Reviewed risk.

**Reviewed** (any one) — architecture or cross-module behavior; data structure, persistence, schema, or migration; permissions, auth, security, or privacy; financial, accounting, or business-critical computation; public API, shared interface, or compatibility; new workflow, new business capability; external callback or third-party integration; transaction, compensation, or rollback; irreversible or hard-to-recover operation; deploy/release or large blast radius; the engineering boundary is not clear enough to implement safely and needs a design first. A new page alone is not a Reviewed trigger — only when it introduces one of these risks; a standalone, low-risk page with a clear boundary and verification method is Bounded.

## Impact Surface First

Implementation scope does not determine change risk. A small diff can still cross a high-impact surface; if the impact surface is uncertain or crosses an important boundary, prefer Reviewed Change.

Escalation signals (guidance, not a checklist) — any one may justify Reviewed:
- **Data** — metric/calculation change, field business meaning, data source, historical data, migration.
- **Business logic** — business rule, financial/inventory/order computation, approval condition, state transition.
- **Permission / security** — permission change, data access scope, sensitive data.
- **Integration** — API contract, ERP, third-party system, external dependency.
- **Uncertainty** — you cannot explain why the impact surface is controlled; do not downgrade on an unknown.

## Escalation

- Quick implementation reveals a behavior impact → escalate to Bounded.
- Bounded implementation reveals a Reviewed risk → escalate to Reviewed.
- An escalation must state the reason. Never silently widen the process.

## Stop conditions

- A Route Brief is returned. If the user asked for classification only, stop here.
- The goal or intended outcome cannot be identified, or material business semantics that could change the solution or result are missing → route to `shape`; do not proceed on an assumed goal or business contract.
- You have asked your focused questions and the answers still do not resolve the kind of uncertainty you face → say so and stop; do not pick a lighter path by default.

## Output contract

A short Route Brief, in plain text:

- **Route:** Quick | Bounded | Reviewed (or: route to `shape` first).
- **Goal:** the outcome, one line.
- **Boundary / must-not-change:** what is out of scope.
- **Risk reason:** the deciding dimension (blast radius, reversibility, boundary clarity).
- **Verification approach:** how the result will be checked.
- **Blocking question:** only if a real one exists; otherwise omit.
- **Next change skill:** the skill the handoff goes to.

The router edits no files and creates no state. If handing off, the next change skill runs its own procedure from here.

## Example

> **Task:** "Fix the typo in the README install command and update the version badge."
>
> **Route:** Quick
> **Goal:** correct install command and version badge in README.
> **Boundary / must-not-change:** no source or install-script changes.
> **Risk reason:** behavior-neutral, exact boundary, trivially reversible.
> **Verification approach:** re-read README; confirm the flag matches `install.py` and the badge matches the tag.
> **Next change skill:** `quick-change`
>
> Handing off to `quick-change` now — no further input needed.