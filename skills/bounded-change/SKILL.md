---
name: "bounded-change"
description: "Handles local, behavior-affecting changes with a clear boundary. Records a baseline or reproduction, verifies the same way before and after, iterates the implementation not the goal, and stops after two failed attempts at the same root cause. Creates no formal lifecycle or state files."
---

# Bounded Change

## Purpose

Make a behavior-affecting change that stays within one local boundary — a function, module, small feature, or local interaction — and verify it with a tight loop. Heavier than Quick because behavior matters; lighter than Reviewed because the blast radius is contained and the boundary is already clear.

## Use when

- The change affects runtime behavior but stays within one function, module, small feature, or local interaction.
- The boundary is clear: you can name what changes and what must stay the same.
- There is a verification method (a test, a repro, a command, or a concrete manual check).

## Do not use when

- Behavior-neutral → `quick-change`.
- A Reviewed trigger applies (schema, security, shared interface, cross-module, new workflow, etc.) → `reviewed-change`.
- No way to verify the behavior → stop and say so; do not proceed on faith.

## Required inputs

- The change stated as an expected behavior ("after this, X happens / stops happening").
- The boundary: what changes, and what must not change.
- A verification method: a test, a repro command, or a concrete manual check.

## Procedure

1. State the expected behavior and the boundary. If you cannot name a verification method, stop and say so.
2. **Record a baseline or reproduce the defect** before changing anything: capture the current output, the failing test result, or the reproduction. This is the "before" you will compare against.
3. Make the change. Touch only what the boundary permits; do not refactor neighbors.
4. **Verify the same way** — use the same test, command, script, or manual reproduction as the baseline to prove the before/after change.
5. Iterate the implementation — not the goal and not the boundary — until it passes.
6. Confirm the boundary held: nothing outside the stated scope changed behavior.
7. Report the change, the verification, and the boundary check.

## Discipline

- If an automated regression test is practical, first prove it fails for the target defect (red), then make it pass (green).
- Do not make a result pass by weakening the test. The test must verify the behavior, not justify it.
- Do not refactor adjacent code while you are in the file.
- Iterate the implementation, not the goal or the boundary.

## Manual verification

When automation is not practical, you may use a manual check, but you must disclose what it does and does not prove:

- State why an automated test was not practical.
- State what the manual check covered (the exact steps and inputs run).
- State what it did **not** cover, and the residual limitations — the remaining risk the manual check leaves open.
- Do not present a single manual observation as a complete proof.

## When a fix does not work

- First failure at a symptom is expected.
- Before a second edit, state a few falsifiable hypotheses about the root cause and pick the one with the strongest evidence.
- If the second edit addresses the **same root cause** and still fails, stop and report. Do not keep blindly editing.

## Escalation

If implementation reveals a schema, security, shared-interface, cross-module, or new-workflow risk, stop and escalate to `reviewed-change`. State the reason; never silently widen the scope.

## Stop conditions

- The expected behavior is verified (same method, green) and the boundary held.
- Verification is impossible with the stated method → stop and report; do not widen the change silently.
- Two rounds fail on the same root cause → stop and report.
- The change grows past the boundary → stop and route to `reviewed-change`.

## Output contract

A short report, in plain text:

- **Expected behavior:** one sentence.
- **Baseline:** the before evidence (repro output, failing test, recorded behavior).
- **Changed:** the files and the nature of the change.
- **Verified:** the method used and its result (pass/fail, with the evidence).
- **Boundary:** confirmation that nothing outside the stated scope changed.
- **Residual limitations:** `none` for automated verification. For manual verification, state what was not covered and the residual risk; never describe one manual observation as a complete proof.

Do not create state files or a record. Do not commit unless the user asks.

## Example

> **Expected behavior:** `parse_duration("90s")` returns `90`, not raises.
> **Baseline:** `parse_duration("90s")` raises `ValueError: unknown unit`; test `test_parse_seconds` fails.
> **Changed:** `src/duration.py` — added the seconds-unit branch to `parse_duration`.
> **Verified:** `python -m pytest tests/test_duration.py -k parse_seconds` — first confirmed it failed (red), now passes (green); the case returns 90.
> **Boundary:** no other units or callers changed; `parse_duration` is only called from `schedule.py`, whose tests still pass.
> **Residual limitations:** none — automated regression test covers the target behavior.