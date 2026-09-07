---
name: "reviewed-change"
description: "Handles architecture, data shape, security, public interface, cross-module, and other high-risk changes, with an independent Plan Review and an independent Final Review. On demand, writes a change record under .agent-delivery/changes."
---

# Reviewed Change

## Purpose

Handle changes too risky for one pass: architecture, data shape, security, public interfaces, anything spanning modules, or an unclear boundary. A second perspective checks the result. This is the only change path that may persist a record.

## Use when

- Any Reviewed trigger applies (see `task-router`): architecture, data/schema/migration, security/privacy, financial or business-critical computation, public API, shared interface, new workflow, external integration, transaction/rollback, irreversible operation, large blast radius, or a boundary needing a design first.

## Do not use when

- Behavior-neutral → `quick-change`. Local with a clear boundary and verification → `bounded-change`. Problem/outcome framing, not engineering → `shape`.

## Required inputs

A change naming its risk; affected code and context; a non-implementing reviewer.

**Reviewer independence** requires separate context and no visibility into the implementer's reasoning: a different agent session, ideally model or host. Same-session role-switching is not independent. Without an independent reviewer, the user may accept a **limited non-independent review** as supplemental diagnostic evidence only. It does not satisfy the independent Plan Review or Final Independent Review and cannot make the change delivery-ready; independent approval remains BLOCKED.

## Minimum Path (invariants)

These always hold:

1. Form a Change Contract with outcome, approach, acceptance checks, and reviewer.
2. Prove acceptance checks can fail (RED) before implementing.
3. Get independent Plan Review approval before touching production code.
4. Implement in vertical slices; verify each before the next.
5. Get independent Final Review approval; resolve blocking findings and re-review. The user decides on commit/deploy; do not self-accept.

## Procedure

Change Contract → Falsification / RED → Plan Review → Implementation slices → Verification → Final Independent Review → Findings Resolution → Re-review when required → User decision / commit only when requested. For non-trivial changes, read `references/review-discipline.md` when first needed — before Plan Review; refresh it when the change's content changes or the context is missing. Apply only relevant risk.

### 1. Change Contract

Form one compact contract in conversation; write `record.md` only for audit, async teams, or when asked. User Acceptance Scenarios and the Card stay in conversation — no separate acceptance file or registry.

- **Outcome.**
- **Proposed approach / design** — implementation path, key technical boundaries, and relevant data/state ownership; keep it to what the reviewer needs.
- **Must-preserve behaviors.**
- **Non-goals.**
- **Risk dimensions.**
- **Affected boundaries/files.**
- **Acceptance checks**, each with a verification method (automated test / manual check / evidence review); note which automated checks form RED and which cannot, with alternative evidence. Manual and evidence-review checks need no automated RED.
- **User Acceptance Scenarios** (only when user-observable; skip for pure internal refactors): 1–5 concrete business scenarios the user will manually accept, each as actor → action → observable business result, drawn from the confirmed Outcome, not implementation details.
- **Authoritative references (when they constrain the requested result)** — the prototype, DESIGN.md, existing behavior, contract, or other source the result must match. Final review must check against them directly, so a user's original reference is not silently shrunk into the contract alone.
- **Reviewer.**
- **Unresolved decisions.**

### 2. Falsification / RED

Build the verification signal before Plan Review. For each practical automated acceptance check, prove it fails on the pre-existing, missing, or counterexample behavior (RED), or record why and the alternative evidence; fix TEST_DEFECTs until the signal is real — green alone is not proof the check could catch the defect.

For failure-sensitive claims (recovery, durability, idempotency, retry safety, or no-loss behavior), state the bounded failure model, the failure points covered by evidence, and important failure points not covered. RED proves a check can catch a counterexample; it does not prove reliability beyond that model.

### 3. Plan Review

A reviewer who is not the implementer reviews the contract and the falsification evidence:

- Do the outcome and the proposed approach / design agree?
- Is the approach sound (boundaries, data/state ownership, risks)?
- Do acceptance checks cover the necessary behaviors, with each automated check's falsification proven (RED or documented alternative evidence)?

Without RED or alternative evidence, or with a blocking finding, do not approve or start implementing.

**A blocking Plan Review is not cleared because the implementer believes the findings were fixed** — resolve or amend, run a **new** independent Plan Review, and keep production forbidden until that review returns an explicit **APPROVED** verdict. "Findings fixed" is not "review passed."

Consider the change's impact surface — data, security/permission, migration, operational, and test impact — as part of the review; these are considerations, not a mandatory document.

### 4. Semantic freeze

The Change Contract is the baseline; amend it and re-run Plan Review if outcome, user-visible behavior, must-preserve/non-goals, acceptance meaning, risk, boundaries, or necessary behavior changes.

### 5. Vertical thin slices

Split multi-part changes into the smallest end-to-end observable slices: one observable behavior each, satisfying an acceptance check and verified before the next.

### 6. Finding categories

Four categories; do not add a lifecycle:

- **IMPLEMENTATION_DEFECT** — contract clear, code does not meet it; fix in scope. A frozen user-observable behavior absent from the running/rendered result is an IMPLEMENTATION_DEFECT even when supporting code and automated tests exist.
- **TEST_DEFECT** — contract clear, but the check cannot verify it; fix the check, then continue.
- **SPECIFICATION_GAP** — a necessary behavior is undefined; stop, amend the contract, re-run Plan Review.
- **FUTURE_ENHANCEMENT** — valuable but not a current acceptance condition; record as a later suggestion, do not expand scope.

### 7. Final Independent Review

The reviewer must be independent (see Required inputs) and reviews against the Change Contract, the actual diff, the verification evidence, and any authoritative references.

Cover at least two axes — Contract/Spec and Standards/Quality (defined in `references/review-discipline.md`); the same reviewer may do both. Tests passing does not equal acceptance complete.

No reviewer available → BLOCKED; see Required inputs. Do not silently self-approve.

**Observed-outcome evidence.** For every frozen acceptance check or User Acceptance Scenario, identify the evidence that proves its observable result.

- If the acceptance is user-observable (rendered, interactive, or otherwise visible in the running system), the evidence must observe that result directly — code presence or automated tests alone cannot prove a rendered or interactive outcome.
- **A frozen user-observable acceptance condition without observed-outcome evidence cannot receive Final Review APPROVED**: verification is incomplete, so return to Verification until matching evidence exists — this is not BLOCKED (reserved for unavailable independent review) and not a finding merely because the evidence is missing.
- If the behavior is actually observed and is absent or wrong, that is an IMPLEMENTATION_DEFECT (blocking finding).
- Evidence method follows acceptance type (see the reference) — this is evidence fidelity, not a browser mandate.
- For failure-sensitive claims, check that the claim does not exceed the failure model and covered points. Treat untested points as residual limitations, not as silently passed behavior.

### 8. Findings and re-review

- **Blocking** — violates the contract, an acceptance check, a safety boundary, an authoritative reference, or makes the result unacceptable. The implementer never closes a blocking finding themselves: fix it, re-run the affected verification, and return to the independent reviewer; "implementer says fixed" is not closed until the reviewer explicitly passes it.
- **Non-blocking** — an improvement or future enhancement; report it as a suggestion and do not implement it in the current scope by default. If the user includes it, update the contract when material, verify, and re-review as required.

**Blocking findings as a diagnosis checkpoint.** When the same blocker survives re-review, re-diagnose before re-applying the same patch: confirm the finding against the current contract, check whether the fix missed the root cause, and re-evaluate the approach. Clear IMPLEMENTATION_DEFECT and TEST_DEFECT findings stay fixable in scope; involve the user only for a material business, scope, acceptance, or risk decision.

### 9. User and commit boundary

**Final Review approval freezes the reviewed production diff.** Later changes to production code, config, migrations, or user-visible behavior require invalidating that approval; re-verify and get a new independent Final Review.

Reviewer approval is not user acceptance. When User Acceptance Scenarios exist, only after a valid Final Review hand the user a **User Acceptance Card**: a conversation-only table of the frozen scenarios (actor → action → observable result) plus a line that automated verification and independent review are done and the user should now manually accept each scenario in their real business role. It restates scenarios frozen before implementation, not a new acceptance standard — do not claim the user's business acceptance has passed.

Destructive, irreversible, security, privacy, financial, or real-production writes need an explicit user decision — judged by the operation's actual risk and the host's permission rules, not by the topic's domain name alone. Do not commit or push unless asked; working tree safety per `bounded-change` — never discard or overwrite unrelated pre-existing user changes, and scope any requested commit to this change only.

Completion after Final Review: when the original request already authorized the work (for example, implement and verify), final verification and review passing let that authorized work finish and report — do not re-ask for the same authorization just because a review or skill transition completed. Re-ask only for a genuinely new decision.

## Stop conditions

- Plan Review blocking — do not implement until a new independent Plan Review returns an explicit APPROVED verdict.
- Change Contract drifted semantically — amend and re-run Plan Review before continuing.
- A necessary behavior is undefined (SPECIFICATION_GAP) — amend the contract, re-run Plan Review.
- No independent reviewer available → report BLOCKED; a limited non-independent review is supplemental evidence only and cannot authorize completion. Do not silently self-approve. Next paths: obtain independence, or re-shape and re-route only with positive evidence of Bounded containment; never split work to bypass review.
- A blocking finding survives re-review — re-diagnose it (is the finding still valid, did the fix miss the root cause, does the approach need re-evaluation); involve the user only for a material business, scope, acceptance, or risk decision.
- Production code changed after a Final Review — prior approval is stale; re-verify and get a new independent Final Review.
- High-risk operation (destructive, irreversible, security-, privacy-, financial-, or production-impacting write) — stop and ask the user unless already explicitly authorized; risk judged as in section 9, not by domain name alone.
- Final review passed and reported — report completion; commit/deploy and business acceptance still wait on the user, but already-authorized work needs no re-asking.

## Record (on demand)

If a durable trail earns its keep, write `.agent-delivery/changes/<change-id>/record.md` (short stable id): the Change Contract, Plan Review verdict, slice + verification log, final review findings, and how each blocking finding was resolved and re-reviewed. Small changes can skip it.

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
> **Contract:** Outcome — alerts delivered within 15 min; approach — a durable queue table owned by `alerts`, consuming idempotently by message key; must-preserve — no alert lost on worker crash; acceptance — crash-recovery (automated), shutdown drain (automated), idempotency on retry (evidence review).
> **Plan Review:** Codex — approved after the idempotency check was added and its falsification evidence reviewed.
> **Final review:** Codex — approved after one blocking implementation finding (missing idempotency key) was fixed, verified, and re-reviewed.
> **Record:** `.agent-delivery/changes/2026-08-15-alert-queue/record.md`
