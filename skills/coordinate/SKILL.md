---
name: "coordinate"
description: "Generates handoff, review-request, and findings-summary packets for people-and-agent and agent-and-agent collaboration. Produces clear, self-contained text with the fields a receiver needs to act. Outputs a packet in the conversation by default; when the user explicitly asks, saves one Handoff Markdown file. Does not send, dispatch, schedule, maintain a task board, write lifecycle state, or auto-invoke other skills."
---

# Coordinate

## Purpose

Produce clean handoff and review artifacts so work moves between a person and an agent, or between two agents (for example Claude and Codex), without losing context. Coordinate writes the packets and, only when the user explicitly asks to save a handoff, writes one Markdown file. It does not send, dispatch, or track packets, and it does not write lifecycle state.

## Use when

- Work needs to move from one actor to another and the receiver lacks the context.
- You are about to ask another agent or person to review, continue, or take over a change.
- A review produced findings and you need a structured summary the receiver can act on.
- The user explicitly asks to save a handoff as a Markdown file (persistence mode).

## Do not use when

- The receiver already has full context — a packet adds noise.
- You want to run or schedule the work — Coordinate does not dispatch or track.
- You want an outcome judgment — use `evaluate`.
- The user has not asked to save a handoff — do not write a file on your own initiative.

## Required inputs

- What was done so far (the change, the contract, or the problem).
- What the receiver is being asked to do.
- Any constraints or open questions the receiver must know.
- For persistence mode only: a Markdown path the user gave, or a single focused question to obtain one.

## Procedure

1. Decide the packet type: handoff, review-request, or findings-summary.
2. Gather only what the receiver needs, using the field lists below. Omit history the receiver cannot act on; omit fields that carry nothing.
3. Write the packet as self-contained text: a receiver who was not present should understand it without follow-up questions.
4. Name the concrete next action the receiver should take.
5. Choose the output mode (see below). Default is in-conversation; persistence only when the user explicitly asked to save.

### Default mode

- Output the self-contained packet in the conversation.
- Do not write a file. If the user did not explicitly ask to save, do not create one.

### Persistence mode (only when the user explicitly asks to save a handoff)

- Use the Markdown path the user gave. If the user asked to save but gave no path: check whether the project has one obvious, unambiguous documentation convention; only if so, use it. Otherwise ask exactly one focused question for the save path.
- If the target file does not exist, create it.
- If the target file already exists: only modify it when the user explicitly asked to update or replace that file. Otherwise stop and report — never silently overwrite.
- Write exactly one Handoff Markdown, using the template below. Reference prototypes, source, screenshots, and test reports by path or link; do not copy assets into the file.
- After saving, report the file path and the content scope.
- The file is a handoff snapshot, not a lifecycle or state record. Do not auto-commit.

## Packet shapes

- **Handoff:** Outcome; Current slice / state; Confirmed facts and rules; Artifacts and locations; Evidence; Limitations and risks; Specific ask / recommended next step; Open questions.
- **Review-request:** goal / change contract; scope and non-goals; acceptance checks (each with its verification method); changed files / diff location; verification evidence; reviewer focus; the exact requested verdict.
- **Findings-summary:** each finding — the finding; blocking or non-blocking; evidence; required or suggested resolution; resolution status; re-review required (yes/no).

The following handoff sections appear **only when relevant**; never force them on every handoff:

- **Data meaning and sensitivity** — what the data means and any sensitivity the receiver must respect.
- **AI decision and fallback** — any automated decision the receiver inherits and its fallback.

## Handoff Markdown template (persistence mode)

```
# Current Outcome Handoff

## Outcome
## Current Slice / State
## Confirmed Facts and Rules
## Artifacts and Locations
## Evidence
## Limitations and Risks
## Specific Ask / Recommended Next Step
## Open Questions
```

Add these only when relevant:

```
## Data Meaning and Sensitivity
## AI Decision and Fallback
```

Omit sections the receiver does not need; do not leave empty mandatory sections.

## Stop conditions

- The packet is written and the next action is named (default mode).
- In persistence mode: the handoff Markdown is saved and the path reported; or the target file exists and the user did not ask to update it — stop and report, do not overwrite.
- The inputs are too thin to write a self-contained packet → say so and list what is missing.

## Output contract

- **Default mode:** a single packet in the conversation, labeled by type, with a named next action.
- **Persistence mode:** exactly one Handoff Markdown file at the agreed path, plus a report of the path and content scope.

Coordinate does not send the packet, paste it to an external receiver, dispatch or schedule work, maintain a task board, write lifecycle state, approve, commit, or push. It does not auto-invoke `shape`, `task-router`, any change skill, or `evaluate`. It does not write state files — the single handoff Markdown is a snapshot, not state.

## Example

> **Packet: review-request (default mode)**
> **Goal / contract:** alerts delivered within 15 min; no alert lost on worker crash; shutdown drains the queue; idempotent on retry.
> **Scope / non-goals:** `src/alerts/queue.py`, `src/alerts/worker.py`; non-goal — SMS channel.
> **Acceptance checks:** crash-recovery (automated test), shutdown drain (automated test), idempotency (evidence review of diff).
> **Changed files / diff:** branch `alert-queue`, commit range `a1b2c3..d4e5f6`.
> **Verification evidence:** crash-recovery test passes (zero lost); shutdown-drain test passes; idempotency key in diff.
> **Reviewer focus:** the crash-recovery path and the shutdown drain; the new persistent queue shape.
> **Requested verdict:** approve / approve-with-findings / blocking findings.
> **Next action:** reviewer runs an independent pass against the acceptance checks and returns a findings-summary.