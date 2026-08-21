---
name: "discover-business-contract"
description: "Turn complex business reality, prototypes, and source artifacts into the material business contract engineering must not have to invent. Use when problem, outcome, and solution direction are already stable, but prototypes, documents, or handoffs leave material business semantics unclear (business flow, business rules, business data meaning, state/permission transitions, or prototype actions & decision rituals). Do not use for Shape (bare \"build an Agent/system\" or unclear problem/outcome); do not use for whether to invest (worth-building-now); do not use for technical schema/API/SQL/service design (task-router / reviewed-change). Triggers: 业务契约, 原型缺口, 业务规则, 字段口径, 状态流转, 决策仪式, 导出后谁接手, 驳回后去哪, business contract, prototype gaps, business rules, data semantics, decision ritual. Use when the user runs /discover-business-contract."
---

# Discover business contract

## Purpose

Turn complex business reality, prototypes, and source artifacts into the **material business contract** engineering must not have to invent.

When the problem and solution direction are already sufficiently clear, but complex business workflows, product prototypes, business documents, or handoffs still leave material business semantics that engineering would otherwise have to guess, capture and freeze these business semantics.

This skill answers:
> "If engineering receives only the current prototype and source artifacts, what material business behavior would they still have to invent?"

This skill does **not** decide:
- Whether this problem is real → `shape` / `observe-real-work`
- Why to build or what solution form to adopt → `shape`
- Whether it is worth investing in → `worth-building-now`
- How to bound a PoC → `bounded-validation`
- How to shrink a minimum real deployment → `smallest-real-deployment`
- Whether it was adopted post-release → `adopted-not-released`
- Technical architecture, database tables, API schemas, SQL, or component implementation → `task-router` / `reviewed-change`

## Use when

- Problem, outcome, and solution direction are already relatively clear, but delivery cannot proceed safely without resolving material business gaps.
- A prototype, PRD, or UI mockup exists with buttons, pages, and tables, but the downstream business actions, state transitions, or data meanings are unstated.
- Business rules, thresholds, time windows, defaults, or exception paths are left to "IT to decide".
- Key entity identifiers, data source authorities, or conflicting field definitions need business freezing.
- Real work requires a downstream decision ritual (e.g., export to Excel → manual adjustments → month-end review meeting → owner sign-off) that UI screens do not capture.

## Do not use when

- The request is bare ("做个 Agent", "做个系统", "做个 dashboard", "我们需要审批平台") where the real problem, outcome, and solution form are not yet shaped → `shape`.
- The pain is unverified or only described through hearsay without watching real work → `observe-real-work`.
- The live question is whether this problem is worth internal investment → `worth-building-now`.
- The live question is technical engineering design (API schema, PostgreSQL tables, SQL queries, UI component layout, caching) → `task-router` / `reviewed-change`.

## Coverage lenses (Use only what is material)

Do not generate a massive PRD. Apply coverage lenses based only on what the current solution materially depends upon.

### 1. Business flow
Confirm only when relevant:
- **Actor & Trigger:** Who initiates the work, and what event triggers it?
- **Main business flow:** What are the key business steps from start to finish?
- **Handoff:** When and how does responsibility transfer to the next actor?
- **Material exceptions:** What significant business exceptions alter flow or acceptance?
*(Do not draft exhaustive BPMN diagrams unless specifically required).*

### 2. Business rules
Express material rules in the structure:
`Condition → Judgment / Action → Observable Result`
Confirm when needed:
- Thresholds and boundary values.
- Time windows and business periods.
- Default behaviors and explicit exceptions.
- Rule authority or policy source.
*(Never invent default parameters or thresholds. "Configurable" does not permit guessing defaults).*

### 3. Business data meaning
Freeze business semantics, not technical database schemas:
- Core entity identity and unique business keys.
- Business definitions and source of truth (authority) for key fields.
- Data granularity and time semantics (e.g., transaction time vs. settlement time vs. accounting period).
- Meaning of missing, zero, empty, unmatched, or conflicting data.
*(Strictly forbidden in this skill: designing database tables, SQL queries, APIs, joins, or services).*

### 4. State, responsibility, and permission
Confirm only when material:
- Business states and what business events trigger transitions.
- Who is authorized to perform each action.
- Who owns the work item at each step.
- Handoff, reject, withdraw, retry, and timeout rules.
*(Do not mechanically invent exhaustive state transitions for trivial states).*

### 5. Prototype → behavior & Decision ritual
Bridge UI elements to real-world business actions:
- **UI Elements:** What business meaning is represented by this button, table, status tag, or export? What changes after clicking? Who takes over? What business state updates?
- **Decision Ritual:** Who actually makes the decision? When? Based on what evidence or artifact? Where does the decision happen?
- **Downstream Continuity:** Does system output continue into Excel, reports, Lark/email, review meetings, or ERP?
*(Displaying data on a screen does not mean the business process is finished. If downstream export + manual adjustment + review meeting exists, that downstream handoff is part of the business contract).*

## Conflict and change discipline

When inherited requirements, prototypes, stakeholder statements, SOPs, observed real work, system constraints, or policies materially conflict:

1. **Do not silently choose one version** as ground truth.
2. **Observed reality ≠ Desired future behavior automatically.** (A current workaround might be deliberately eliminated by a new policy; an observed practice might violate compliance; a prototype might reflect an approved new procedure; or front-line reality might prove the prototype unworkable).
3. **Preserve conflicting claims and their evidence.**
4. **State the material impact of the conflict.**
5. **Identify the decision authority** who can decide intended future behavior.
6. **Obtain/record explicit disposition if available.** If the decision authority is missing and the conflict changes material behavior, mark it **UNRESOLVED**; do not freeze that part of the contract.

## Evidence discipline

Tag material semantics with clear evidence boundaries:
- `CONFIRMED` — Authorized business owner or authoritative policy confirmed intended future behavior.
- `OBSERVED` — Directly witnessed in current real work or existing systems today.
- `INFERRED` — Logically deduced from available evidence, but not yet verified by authority.
- `UNRESOLVED` — Material gap or conflict remains open and undecided.

*(Important: `OBSERVED` does not automatically upgrade to `CONFIRMED` future behavior. Polished PRD text does not upgrade evidence status).*

## Stop conditions

Apply the **fresh-eyes check**:
> "If engineering receives only this Business Contract and the referenced prototype/artifacts, what material business behavior would they still have to invent?"

Stop discovery when either of the following two bounded conditions is met:

### 1. Material UNRESOLVED still exists (Discovery paused / bounded)
If there remains any material `UNRESOLVED` that affects user-visible business behavior, business rules/calculations, state transitions, permissions, responsibility/handoffs, data authority/semantics, decision rituals, or acceptance behavior:
- **STOP further speculative discovery.** Do not keep expanding conversations endlessly.
- **Explicitly name**: the unresolved decision, why it matters (material impact), the decision authority, and the needed evidence or disposition.
- **DO NOT mark affected behaviors as engineering-ready.**
- **DO NOT let engineering choose or guess an answer.**
- **DO NOT invent speculative product features or workflows** (e.g., unsolicited card approvals, batch compensation UI) to solve the unconfirmed policy/conflict.
- Hand back the bounded contract with explicit unresolved blocks, awaiting authorized disposition or routing back to appropriate shaping/business decision work.

### 2. No material UNRESOLVED remains (Engineering-ready)
Only when:
- All material intended future behaviors and decision rituals are `CONFIRMED`. `OBSERVED` evidence may support that confirmation, but it does not substitute for authorized confirmation when future behavior is in question;
- All material conflicts have received authorized dispositions;
- Engineering does not need to invent any material business decision, and remaining questions are ordinary technical implementation details (API names, SQL queries, table schemas, component hierarchy, button spacing, caching, standard tech error handling):
- **STOP and hand off implementation to `task-router`.**

## Output contract

Plain text, structured and concise:

- **Problem & Solution Direction (Summary):** 1–2 sentences establishing context.
- **Material Business Contract (Confirmed parts):**
  - Flow & Handoffs
  - Business Rules (`Condition → Action → Result`)
  - Data Semantics & Authority (Entity, Field meaning, Missing/Zero semantics)
  - State & Permissions (Who, When, Transitions, Reject/Withdraw)
  - Prototype Action & Decision Ritual (What happens post-click, downstream Excel/meeting path)
- **Conflicts & Evidence (if any):**
  - Inherited / Intended Claim
  - Observed / Constraint Claim
  - Material Impact
  - Decision Authority & Status (`CONFIRMED` / `UNRESOLVED`)

### Disposition & Next Step (Choose the applicable branch):

**A. If material UNRESOLVED exists (NOT ready for engineering):**
- **Material Decision Needed:**
  - Unresolved item
  - Material impact
  - Decision authority
  - Status: `UNRESOLVED`
- **Not Ready for Engineering:**
  - Explicit list of behaviors/flows that MUST NOT be implemented or frozen until authorized disposition is given.
*(Do not output an Engineering Handoff Note that suggests full implementation is ready).*

**B. If no material UNRESOLVED remains (Ready for engineering):**
- **Engineering Handoff Note:** Brief list of technical areas ready for `task-router`.
