---
name: "reviewed-change"
description: "Handles architecture, data shape, security, public interface, cross-module, and other high-risk changes. Uses a lightweight flow: Change Contract, Falsification / RED, Plan Review, vertical slices, Verification, Final Independent Review, findings resolution, and re-review when required. On demand, writes a change record under .agent-delivery/changes."
---

# Reviewed Change

## Purpose

Handle changes too risky for one pass: architecture, data shape, security, public interfaces, anything spanning modules, or anything whose boundary is not yet clear. A second perspective checks the result before it ships. This is the only change path that may persist a record.

## Use when

- Any Reviewed trigger applies (see `task-router`): architecture, data/schema/migration, security/privacy, financial or business-critical computation, public API, shared interface, new workflow, external integration, transaction/rollback, irreversible operation, large blast radius, or a boundary that needs a design first.

## Do not use when

- Behavior-neutral → `quick-change`. Local with a clear boundary and verification → `bounded-change`. Problem/outcome framing, not engineering → `shape`.

## Required inputs

- A change description naming the risk dimension.
- Access to the affected code and context.
- A reviewer who did not implement the change (another agent or a person).

## Procedure

Change Contract → Falsification / RED → Plan Review → Implementation slices → Verification → Final Independent Review → Findings Resolution → Re-review when required → User decision / commit only when requested.

### 1. Change Contract

Before implementing, form one compact contract (conversation is fine; write `record.md` only for audit, async teams, or when the user asks). User Acceptance Scenarios and the User Acceptance Card are conversation-only by default — no separate acceptance file or registry, and no split into User Intent Contract, Design Specification, Acceptance Rubric, or other governance files.

- **Outcome.**
- **Proposed approach / design** — the implementation path, the key technical boundaries, and the relevant data or state ownership. Include only what the reviewer needs to judge the approach; do not write a standalone Design Specification.
- **Must-preserve behaviors.**
- **Non-goals.**
- **Risk dimensions.**
- **Affected boundaries/files.**
- **Acceptance checks**, each with a verification method: automated test / manual check / evidence review; note which automated checks should form RED and which cannot reasonably form RED (with the alternative evidence). Manual and evidence-review checks need no automated RED.
- **User Acceptance Scenarios** (only when the change has user-observable behavior; skip for pure internal refactors): 1–5 concrete business scenarios the user will manually accept, each as actor → action → observable business result, drawn from the already-confirmed Outcome / business decisions, not from implementation details.
- **Reviewer.**
- **Unresolved decisions.**

### 2. Falsification / RED

Build the verification signal before Plan Review. For each practical automated acceptance check, prove it fails on the pre-existing, missing, or counterexample behavior (RED), or record why and the alternative evidence; fix TEST_DEFECTs until the signal is real. Green alone is not proof the check could have caught the defect. Before Plan Review, verification code may change; production behavior may not.

### 3. Plan Review

A reviewer who is not the implementer reviews the contract and the falsification evidence:

- Do the outcome and the proposed approach / design agree?
- Is the proposed approach sound — are the technical boundaries and data/state ownership right, and are the risks handled, and the boundaries clear enough?
- Do acceptance checks cover the necessary behaviors, with each automated check's falsification ability proven (RED shown, or documented alternative evidence)? Without RED or alternative evidence, or with a blocking finding, do not approve or start implementing.

### 4. Semantic freeze

Production implementation starts only after Plan Review passes. The Change Contract becomes the implementation baseline — but no state file is created. Stop, amend the contract, and re-run Plan Review if any of these change:

- Outcome or user-visible behavior.
- Must-preserve or non-goals.
- Acceptance meaning, or a User Acceptance Scenario's actor, action, observable result, or material business meaning.
- Risk level rises.
- File, module, or system boundary grows.
- A necessary behavior is undefined.

### 5. Vertical thin slices

Split multi-part changes into the smallest end-to-end observable slices. Each slice delivers one observable behavior and satisfies at least one acceptance check. Prefer slices that can be verified or demonstrated alone. Do not stack unverifiable half-finished work by technical layer (database/backend/frontend). Verify a slice before starting the next.

### 6. Finding categories

Use four categories; do not add a lifecycle:

- **IMPLEMENTATION_DEFECT** — the contract is clear, the code does not meet it; fix in the current scope.
- **TEST_DEFECT** — the contract is clear, but the check cannot verify it correctly; fix the check, then continue.
- **SPECIFICATION_GAP** — a necessary behavior is undefined; stop, amend the contract, re-run Plan Review.
- **FUTURE_ENHANCEMENT** — valuable but not a current acceptance condition; record as a later suggestion, do not expand scope.

### 7. Final Independent Review

The reviewer must be independent of the implementer, and reviews against the Change Contract, the actual diff, and the verification evidence. The review must cover at least two axes — the same reviewer may do both; no two reviewers or parallel agents are required, and this is not a new gate:

- **Contract / Spec axis** — does the implementation satisfy the agreed Change Contract? Look for omissions, misreadings, or scope drift, and confirm the verification evidence actually corresponds to the success criteria, not just that some check passed.
- **Standards / Quality axis** — does it meet the repository's applicable standards? Look for unnecessary complexity, risk, or maintenance burden, and confirm the tests actually prove the target behavior rather than only reporting that commands ran.

Tests passing does not equal acceptance complete — manual and evidence-review checks must also run, and a green suite does not override a Contract/Standards finding. When User Acceptance Scenarios exist, the verification evidence must map to them: for each frozen scenario, say which evidence supports it. If no independent reviewer is available, report BLOCKED; do not self-approve.

### 8. Findings and re-review

- **Blocking** — violates the contract, an acceptance check, a safety boundary, or makes the result unacceptable. Fix, re-run the affected verification, and return to the independent reviewer. "Implementer says fixed" is not closed; the reviewer must explicitly pass it.
- **Non-blocking** — an improvement or future enhancement; do not sneak it into the current scope.

**Review round counting.** Each independent reviewer verdict is one round. The first blocking verdict is round 1. A re-review that still reports the same blocker is round 2. If the same blocking root cause is still open after round 2, stop and ask the user to choose: change the design, narrow the scope, or pause.

### 9. User and commit boundary

Reviewer approval is not user acceptance. After the final review passes, when User Acceptance Scenarios exist, hand the user a **User Acceptance Card** — a light table of the frozen scenarios (actor → action → observable result) plus a line that automated verification and independent review are done and the user should now manually accept each scenario in their real business role. The card is conversation-only by default and restates the scenarios frozen before implementation, not a new acceptance standard. Do not claim the user's business acceptance has passed. Routine, explicitly authorized implementation needs no extra confirmation. Destructive, irreversible, security, privacy, financial, or real-production writes need an explicit user decision. Do not commit or push unless the user asks. Working tree safety: never discard or overwrite unrelated or pre-existing user changes; keep this change's edits distinct from the user's; if staging or committing is requested, scope it to this change only.

## Stop conditions

- Plan Review returned a blocking finding — do not start implementing until it is resolved and the contract re-reviewed.
- The Change Contract drifted semantically (outcome, must-preserve, non-goals, acceptance meaning, risk level, or boundaries changed) — amend the contract and re-run Plan Review before continuing.
- A necessary behavior is undefined — a SPECIFICATION_GAP; stop implementing, amend the contract, re-run Plan Review.
- No independent reviewer is available — report BLOCKED; do not self-approve.
- The same blocking root cause is open after two review rounds — stop and ask the user to choose: change the design, narrow the scope, or pause.
- A high-risk operation needs a user decision (destructive, irreversible, security, privacy, financial, or real-production write) — stop and ask.
- The final review passed and has been reported — stop and wait for the user's decision; do not self-accept or commit.

## Record (on demand)

If a durable trail earns its keep, write `.agent-delivery/changes/<change-id>/record.md` (short stable id, e.g. `2026-08-15-alert-queue`). Holds the Change Contract (including the proposed approach / design), Plan Review verdict, slice + verification log, final review findings, and how each blocking finding was resolved and re-reviewed. Small reviewed changes can skip it.

## Output contract

- **Change:** one sentence + risk dimension.
- **Change Contract:** the compact contract, including the proposed approach / design.
- **Plan Review:** reviewer + verdict (approved / blocking / blocked).
- **Verified:** per acceptance check, the method and evidence.
- **Final review:** reviewer, verdict, blocking/non-blocking findings, re-review status. Findings are tagged by axis: Contract/Spec or Standards/Quality.
- **User Acceptance Card (if scenarios exist):** the frozen scenarios handed to the user for manual acceptance.
- **Record (if created):** the path.

## Example

> **Change:** move alert delivery from a synchronous loop to a queued worker; risk: architecture + data (new persistent queue).
> **Contract:** Outcome — alerts delivered within 15 min; proposed approach / design — a durable queue table owned by `alerts` with a single worker consuming idempotently by message key; must-preserve — no alert lost on worker crash; non-goals — SMS channel; acceptance — crash-recovery test (automated), shutdown drain (automated), idempotency on retry (evidence review).
> **Plan Review:** Codex — approved, one note to add idempotency acceptance check.
> **Verified:** crash-recovery test passes (zero lost); shutdown-drain test passes; idempotency key visible in diff.
> **Final review:** Codex — approved after one blocking finding (missing idempotency key, Contract/Spec axis) fixed and re-reviewed (round 2 passed); one non-blocking note (worker logging could be simpler, Standards/Quality axis).
> **Record:** `.agent-delivery/changes/2026-08-15-alert-queue/record.md`