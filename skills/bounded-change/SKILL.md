---
name: "bounded-change"
description: "Handles local, behavior-affecting changes with a clear boundary and a verification method: records a baseline or reproduction and verifies the target behavior against the baseline. Routes to reviewed-change when the impact surface or boundary is uncertain. Creates no formal lifecycle or state files."
---

# Bounded Change

## Purpose

Make a behavior-affecting change that stays within one local boundary — a function, module, small feature, or local interaction — and verify it with a tight loop. Heavier than Quick because behavior matters; lighter than Reviewed because the blast radius is contained and the boundary is already clear.

## Use when

- The change affects runtime behavior but stays within one function, module, small feature, or local interaction.
- The boundary is clear: you can name what changes and what must stay the same.
- There is a verification method (a test, a repro, a command, or a concrete manual check).

"Looks small" is not a Bounded reason. Bounded requires evidence that the affected scope is known, the dependencies are understood, and the verification is sufficient. If the impact surface is uncertain or crosses a data, business-logic, permission, or integration boundary, route to `reviewed-change`.

## Do not use when

- Behavior-neutral → `quick-change`.
- A Reviewed trigger applies (schema, security, shared interface, cross-module, new workflow, etc.) → `reviewed-change`.
- No way to verify the behavior → stop and say so; do not proceed on faith.

## Required inputs

- The change stated as an expected behavior ("after this, X happens / stops happening").
- The boundary: what changes, and what must not change.
- A verification method: a test, a repro command, or a concrete manual check.

## Minimum Path (invariants)

These always hold:

1. State the expected behavior, boundary, and verification method.
2. Record a baseline or reproduce the defect before changing anything.
3. Make the change within the stated boundary only.
4. Verify the target behavior with the baseline's method, or an alternative that verifies the same behavior.
5. Confirm the boundary held; escalate if a Reviewed risk appears.

## Procedure

Walk the Minimum Path invariants in order:

1. If you cannot name a verification method, stop and say so.
2. Capture the baseline before any change and keep it for comparison. If the original method is unavailable, find an alternative that verifies the **same target behavior** and state the coverage difference; a weaker proxy signal is not acceptance.
3. Make the change only within the boundary; do not refactor neighbors.
4. Verify with the same method as the baseline, or an alternative when the original method is unavailable. For a bug fix, re-run the **original reproduction** when available; otherwise use the equivalent verification described above.
5. Iterate the implementation — not the goal and not the boundary — until it passes.
6. Confirm the boundary held and report the change, the verification, and the boundary check.

## Discipline

- If an automated regression test is practical, first prove it fails for the target defect (red), then make it pass (green).
- Do not make a result pass by weakening the test. The test must verify the behavior, not justify it.
- Do not refactor adjacent code while you are in the file. Working tree safety: never discard or overwrite unrelated or pre-existing user changes; keep this change's edits distinct from the user's; if staging or committing is requested, scope it to this change only.
- Prefer existing effective checks; add a test only when it adds necessary behavior evidence, not to mirror implementation internals.
- Re-run or widen verification only for a new change, a failure, or an unresolved risk.
- Iterate the implementation, not the goal or the boundary.

## Feedback loop quality

The baseline, reproduction, or check must actually reach the target behavior and be able to fail because of that target problem. None of these alone proves the behavior is correct: the command ran successfully; a test with a related name exists; unrelated tests pass.

Prefer verifying **externally observable behavior** at a behavioral seam, not only internal implementation details — a test that only asserts an internal state change can pass while the user-visible behavior is still wrong.

For a **bug fix**, add or use a regression check at the correct behavioral seam.

If you cannot build a feedback signal strong enough to distinguish success from failure, stop guessing and report what is missing — environment, inputs, observation capability, or manual verification.

## Manual verification

When automation is not practical, a manual check must disclose: why automation was skipped, what was covered (the exact steps and inputs run), what was **not** covered, and that a single observation is not complete proof.

## When a fix does not work

- First failure at a symptom is expected; treat each failure as a diagnosis step, not a deadline.
- Before the next edit, re-check the diagnosis: is the reproduction still valid, does the evidence still support the hypothesis, was the change actually applied where the symptom originates?
- New evidence may justify continuing within the boundary; there is no fixed round count — iterate on evidence, not on attempts.
- Pause and report only when no feasible next step exists, a key input is missing, or a material scope/business decision is needed.

## Escalation

If implementation reveals a schema, security, shared-interface, cross-module, or new-workflow risk, stop and escalate to `reviewed-change`: the remaining work continues under Reviewed's process. Escalation does not end the task or require the user to re-enter the skill name. State the reason; never silently widen the scope.

## Stop conditions

- The expected behavior is verified with the baseline method or an equivalent alternative, and the boundary held.
- The stated method is unavailable and no alternative verifies the same target behavior → stop and report; a weaker proxy is not acceptance.
- The feedback signal cannot distinguish success from failure (cannot reach or fail on the target behavior) → stop and report what is missing; do not guess.
- No feasible next step, missing key input, or a needed material scope/business decision → pause and report.
- The change grows past the boundary → stop and route to `reviewed-change`.

## Output contract

A short report, in plain text:

- **Expected behavior:** one sentence.
- **Baseline:** the before evidence (repro output, failing test, recorded behavior).
- **Changed:** the files and the nature of the change.
- **Verified:** the method used and its result (pass/fail, with the evidence).
- **Boundary:** confirmation that nothing outside the stated scope changed.
- **Residual limitations:** report what the verification evidence does not cover, whether the check is automated or manual; if none is identified, say so in one clause — do not invent risk. Never describe a single observation as complete proof.
- **Manual acceptance (only when the behavior is user-observable):** 1–3 lines projecting the verified Expected Behavior into how the user operates it and what they should see. No freeze, review, or record — a handoff, not a new mechanism.

Do not create state files or a record. Do not commit unless the user asks.

## Example

> **Expected behavior:** `parse_duration("90s")` returns `90`, not raises.
> **Baseline:** `parse_duration("90s")` raises `ValueError: unknown unit`; test `test_parse_seconds` fails.
> **Changed:** `src/duration.py` — added the seconds-unit branch to `parse_duration`.
> **Verified:** `python -m pytest tests/test_duration.py -k parse_seconds` — first confirmed it failed (red), now passes (green); the case returns 90.
> **Boundary:** no other units or callers changed; `parse_duration` is only called from `schedule.py`, whose tests still pass.
> **Residual limitations:** none identified — the automated regression test covers the target behavior.