---
name: "quick-change"
description: "Handles docs, copy, comments, formatting, and clearly behavior-neutral small edits. Makes the change and verifies it does not alter behavior. If a behavior impact appears, escalates to bounded-change without forcing a blanket rollback. Creates no persistent state."
---

# Quick Change

## Purpose

Make small, behavior-neutral edits quickly, with just enough verification to prove nothing broke. The lightest change path: no design, no lifecycle, no state files.

## Use when

- The change is documentation, copy, comments, formatting, or config that does not affect runtime behavior.
- The boundary is exact: you can name the lines that will change before you start.
- Reversibility is trivial.

## Do not use when

- The change alters runtime behavior → `bounded-change`.
- A Reviewed trigger applies (architecture, data shape, security, public interface, cross-module) → `reviewed-change`.
- You are not sure the change is behavior-neutral → escalate to `bounded-change` and say why.

## Required inputs

- The exact change, stated before editing.
- Access to the target file(s).

## Procedure

1. State the exact change and the files it will touch, before editing.
2. Make the edit. Change only what was stated; do not reformat or "improve" adjacent code.
3. Verify the change does not alter behavior:
   - For docs and copy: re-read the result; confirm links and code blocks resolve; confirm no unintended edits leaked in.
   - For config: confirm the file still parses; confirm no runtime-affecting value changed unless that was the stated change.
4. Report what changed and the verification result.

## Escalation (behavior impact found)

If the edit turns out to be behavior-affecting:

- Only revert **this skill's own edits**, and only when they can be isolated safely.
- If the edits cannot be cleanly isolated, or reverting would overwrite the user's own changes, stop, leave the working tree as-is, and report. Working tree safety: never discard or overwrite unrelated or pre-existing user changes; keep this change's edits distinct from the user's; if staging or committing is requested, scope it to this change only.
- Then hand off to `bounded-change`, naming why the change is behavior-affecting.

Do not perform a blanket "stop, revert" without checking isolation and the user's own changes.

## Stop conditions

- The edit is made and verified behavior-neutral.
- The edit is behavior-affecting → escalate to `bounded-change` (revert only if safely isolated; otherwise leave the field and report).

## Output contract

A short report, in plain text:

- **Changed:** the files and the nature of the edit.
- **Verified:** the specific check(s) run and their result.
- **Escalated (only if it happened):** why the change was handed to `bounded-change`, and whether the quick edits were reverted or left in place.

Do not create state files. Do not write a record. Do not commit unless the user asks.

## Example

> **Stated change:** "Fix the broken relative link in `docs/concepts.md` and correct the install command's flag from `--scope` to `--target`."
>
> **Changed:** `docs/concepts.md` — repaired one link, corrected one flag in the install example.
> **Verified:** re-read the file; the link target exists; the install flag now matches `scripts/install.py`'s actual argument; no other lines were touched.