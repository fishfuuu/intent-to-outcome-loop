# Delivery-ready reference

How to decide whether a non-trivial brief is truly delivery-ready. Read this only when material data, judgment, workflow, or feasibility semantics must be frozen — for simple tasks, skip it and rely on the main SKILL's Procedure.

## 1. Materiality

Decide what Shape must close and what may go to delivery. Ask once:

> If this decision differed, would it materially change what the user sees, a business calculation, a classification, an action, a workflow step, an acceptance result, or the solution's viability?

- **Yes** → material. Resolve it or get the user to explicitly accept carrying it.
- **No**, and it is low-impact and reversible → a delivery detail or ordinary assumption. Do not block completion.

Common non-material items: button color, page spacing, internal function split, cache TTL, file naming, ordinary error-message wording. Do not enumerate every edge case — only material ones block.

## 2. Business contract checks

Freeze only what the chosen solution actually depends on. Never a uniform template.

- **Data semantics** — the core entity, what key fields mean, which source has authority, data granularity, time conventions, how sources link, and what missing / conflicting / 0 / empty / unmatched each mean. This is a business data contract, not a schema — no tables, joins, APIs, or interfaces.
- **Material judgment / calculation rules** — when the solution judges, calculates, ranks, flags, alerts, approves, recommends, replenishes, sets thresholds, or classifies: input/source, decision or calculation logic, any material threshold/window/default, the important exception, and the observable result.
- **Workflow / state / permission** — when it is a task, approval, state flow, or multi-person: who initiates, processes, and sees, the business states, allowed actions, what moves to the next state, how withdraw/reject/retry work, and the exception path. Not every task needs a state machine — only material user-visible behavior must not be left for delivery to guess.

Never self-invent a material value or exception. "Configurable later" is not a license to guess a default.

## 3. Delivery-ready self-check

Before calling the brief delivery-ready, run a fresh-eyes pass:

- **Completeness** — is any material rule or exception still undefined (e.g. a division where the denominator can be 0)?
- **Consistency** — does the business contract conflict with the acceptance scenarios, the solution shape, or the boundary?
- **Feasibility closure** — does any feasibility claim still require validation to know whether the chosen solution or a core acceptance scenario holds?
- **Scope** — did the agent silently add scope or a material decision the user never made?

For each problem found: resolve it, or get the user to explicitly accept carrying it as a stated assumption/risk. Otherwise the brief is not delivery-ready and must not hand off.

## 4. Anti-patterns

- "Fixed days" ≠ "5 days" — choosing the rule form does not confirm the parameter.
- "Configurable" ≠ permission to invent the default.
- Local persistence unverified ≠ acceptance established.
- The contract says "no historical edits" while an acceptance scenario allows them — a contradiction.
