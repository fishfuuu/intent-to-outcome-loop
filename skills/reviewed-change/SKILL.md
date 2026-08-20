---
name: "reviewed-change"
description: "Handles architecture, data shape, security, public interface, cross-module, and other high-risk changes. Uses a lightweight flow: Change Contract, Falsification / RED, Plan Review, vertical slices, Verification, Final Independent Review, findings resolution, and re-review when required. On demand, writes a change record under .agent-delivery/changes."
---

# Reviewed Change

## Purpose

Handle changes too risky for one pass: architecture, data shape, security, public interfaces, anything spanning modules, or anything whose boundary is not yet clear. A second perspective checks the result before it ships. This is the only change path that may persist a record.

## Use when

- Any Reviewed trigger applies (see `task-router`): architecture, data/schema/migration, security/privacy, financial or business-critical computation, public API, shared interface, new workflow, external integration, transaction/rollback, irreversible operation, large blast radius, or a boundary needing a design first.

## Do not use when

- Behavior-neutral → `quick-change`. Local with a clear boundary and verification → `bounded-change`. Problem/outcome framing, not engineering → `shape`.

## Required inputs

A change description naming the risk dimension; access to the affected code and context; a reviewer who did not implement the change (another agent or a person).

## Procedure

Change Contract → Falsification / RED → Plan Review → Implementation slices → Verification → Final Independent Review → Findings Resolution → Re-review when required → User decision / commit only when requested. For non-trivial changes, read `references/review-discipline.md` before Plan Review and again before Final Review; apply only what fits the change's risk.

### 1. Change Contract

Before implementing, form one compact contract (conversation is fine; write `record.md` only for audit, async teams, or when asked). User Acceptance Scenarios and the Card are conversation-only — no separate acceptance file or registry.

- **Outcome.**
- **Proposed approach / design** — implementation path, key technical boundaries, and relevant data/state ownership; only what the reviewer needs, not a standalone Design Specification.
- **Must-preserve behaviors.**
- **Non-goals.**
- **Risk dimensions.**
- **Affected boundaries/files.**
- **Acceptance checks**, each with a verification method (automated test / manual check / evidence review); note which automated checks form RED and which cannot (with alternative evidence). Manual and evidence-review checks need no automated RED.
- **User Acceptance Scenarios** (only when user-observable; skip for pure internal refactors): 1–5 concrete business scenarios the user will manually accept, each as actor → action → observable business result, drawn from the confirmed Outcome / business decisions, not implementation details.
- **Authoritative references (when they constrain the requested result)** — the prototype, DESIGN.md, existing behavior, contract, or other source the result must match. Final review must check against them directly, so a user's original reference is not silently shrunk into the contract alone.
- **Reviewer.**
- **Unresolved decisions.**

### 2. Falsification / RED

Build the verification signal before Plan Review. For each practical automated acceptance check, prove it fails on the pre-existing, missing, or counterexample behavior (RED), or record why and the alternative evidence; fix TEST_DEFECTs until the signal is real — green alone is not proof the check could catch the defect. Before Plan Review, verification code may change; production behavior may not.

### 3. Plan Review

A reviewer who is not the implementer reviews the contract and the falsification evidence: do the outcome and the proposed approach / design agree; is the approach sound (boundaries, data/state ownership, risks); do acceptance checks cover the necessary behaviors with each automated check's falsification proven (RED or documented alternative evidence)? Without RED or alternative evidence, or with a blocking finding, do not approve or start implementing. **A blocking Plan Review is not cleared because the implementer believes the findings were fixed** — resolve or amend, run a **new** independent Plan Review, and keep production forbidden until that review returns an explicit **APPROVED** verdict. "Findings fixed" is not "review passed."

### 4. Semantic freeze

Production implementation starts only after Plan Review passes. The Change Contract becomes the implementation baseline — no state file is created. Stop, amend the contract, and re-run Plan Review if any of these change: outcome or user-visible behavior; must-preserve or non-goals; acceptance meaning (or a User Acceptance Scenario's actor, action, observable result, or material business meaning); risk level rises; file, module, or system boundary grows; or a necessary behavior is undefined.

### 5. Vertical thin slices

Split multi-part changes into the smallest end-to-end observable slices. **A slice is one observable behavior, not one technical layer** — good: one aggregate → API → UI → rendered verification; bad: all backend, then all frontend, then QA at the end. Each slice satisfies at least one acceptance check; verify one before starting the next.

### 6. Finding categories

Four categories; do not add a lifecycle:

- **IMPLEMENTATION_DEFECT** — contract clear, code does not meet it; fix in scope. A frozen user-observable behavior absent from the running/rendered result is an IMPLEMENTATION_DEFECT even when supporting code and automated tests exist.
- **TEST_DEFECT** — contract clear, but the check cannot verify it; fix the check, then continue.
- **SPECIFICATION_GAP** — a necessary behavior is undefined; stop, amend the contract, re-run Plan Review.
- **FUTURE_ENHANCEMENT** — valuable but not a current acceptance condition; record as a later suggestion, do not expand scope.

### 7. Final Independent Review

The reviewer must be independent of the implementer, and reviews against the Change Contract, the actual diff, the verification evidence, and any authoritative references. Cover at least two axes — Contract/Spec and Standards/Quality (defined in `references/review-discipline.md`); the same reviewer may do both, no two reviewers or parallel agents required. Tests passing does not equal acceptance complete — see the reference for review depth, evidence fidelity, and risk focus. No independent reviewer available → report BLOCKED; do not self-approve.

**Observed-outcome evidence.** For every frozen acceptance check or User Acceptance Scenario, identify the evidence that proves its observable result. If the acceptance is user-observable (rendered, interactive, or otherwise visible in the running system), the evidence must observe that result directly — code presence or automated tests alone cannot prove a rendered or interactive outcome. **A frozen user-observable acceptance condition without observed-outcome evidence blocks APPROVED**: Final Review reports BLOCKED or a blocking finding until the evidence exists. Evidence method follows acceptance type (see the reference) — this is evidence fidelity, not a browser mandate.

### 8. Findings and re-review

- **Blocking** — violates the contract, an acceptance check, a safety boundary, an authoritative reference, or makes the result unacceptable. Fix, re-run the affected verification, and return to the independent reviewer; "implementer says fixed" is not closed until the reviewer explicitly passes it.
- **Non-blocking** — an improvement or future enhancement; report as a suggestion, do not implement it in the current scope by default. If the user includes it, update the contract when material, verify, and re-review as required.

**Review round counting.** Each independent reviewer verdict is one round; the first blocking verdict is round 1, a re-review reporting the same blocker is round 2. If the same blocking root cause is still open after round 2, ask the user to change the design, narrow the scope, or pause.

### 9. User and commit boundary

**Final Review approval freezes the reviewed production diff.** Once approved, do not change production code, config, migrations, or user-visible behavior without invalidating that approval — re-verify and get a new independent Final Review. Reviewer approval is not user acceptance. When User Acceptance Scenarios exist, only after a valid Final Review hand the user a **User Acceptance Card**: a conversation-only table of the frozen scenarios (actor → action → observable result) plus a line that automated verification and independent review are done and the user should now manually accept each scenario in their real business role. It restates scenarios frozen before implementation, not a new acceptance standard — do not claim the user's business acceptance has passed. Destructive, irreversible, security, privacy, financial, or real-production writes need an explicit user decision. Do not commit or push unless asked; never discard or overwrite unrelated pre-existing user changes, and if committing is requested, scope it to this change only.

## Stop conditions

- Plan Review blocking — do not implement until a new independent Plan Review returns an explicit APPROVED verdict.
- Change Contract drifted semantically — amend and re-run Plan Review before continuing.
- A necessary behavior is undefined (SPECIFICATION_GAP) — amend the contract, re-run Plan Review.
- No independent reviewer — report BLOCKED; do not self-approve.
- Same blocking root cause open after two review rounds — ask the user to change the design, narrow scope, or pause.
- Production code changed after a Final Review — prior approval is stale; re-verify and get a new independent Final Review.
- High-risk operation (destructive, irreversible, security, privacy, financial, or real-production write) — stop and ask the user.
- Final review passed and reported — wait for the user's decision; do not self-accept or commit.

## Record (on demand)

If a durable trail earns its keep, write `.agent-delivery/changes/<change-id>/record.md` (short stable id, e.g. `2026-08-15-alert-queue`): the Change Contract (including the proposed approach / design), Plan Review verdict, slice + verification log, final review findings, and how each blocking finding was resolved and re-reviewed. Small changes can skip it.

## Output contract

- **Change:** one sentence + risk dimension.
- **Change Contract:** the compact contract, including the proposed approach / design and any authoritative references.
- **Plan Review:** reviewer + verdict (approved / blocking / blocked).
- **Verified:** per acceptance check, method and evidence.
- **Final review:** reviewer, verdict, blocking/non-blocking findings (tagged by axis: Contract/Spec or Standards/Quality), re-review status.
- **User Acceptance Card (if scenarios exist):** the frozen scenarios for manual acceptance.
- **Record (if created):** the path.

## Example

> **Change:** move alert delivery from a synchronous loop to a queued worker; risk: architecture + data (new persistent queue).
> **Contract:** Outcome — alerts delivered within 15 min; proposed approach / design — a durable queue table owned by `alerts` with one worker consuming idempotently by message key; must-preserve — no alert lost on worker crash; non-goals — SMS channel; acceptance — crash-recovery (automated), shutdown drain (automated), idempotency on retry (evidence review).
> **Plan Review:** Codex — approved after the idempotency acceptance check was added and its falsification evidence reviewed.
> **Final review:** Codex — approved after one blocking implementation finding (missing idempotency key) was fixed, verified, and re-reviewed; one non-blocking Standards/Quality note remained.
> **Record:** `.agent-delivery/changes/2026-08-15-alert-queue/record.md`
