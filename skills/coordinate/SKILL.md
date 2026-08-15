---
name: "coordinate"
description: "Generates handoff, review-request, and findings-summary packets for people-and-agent and agent-and-agent collaboration. Produces clear, self-contained text with the fields a reviewer or receiver needs to act. Does not send, dispatch, schedule, maintain a task board, or write lifecycle state."
---

# Coordinate

## Purpose

Produce clean handoff and review artifacts so work moves between a person and an agent, or between two agents (for example Claude and Codex), without losing context. Coordinate writes the packets; it does not send, dispatch, or track them.

## Use when

- Work needs to move from one actor to another and the receiver lacks the context.
- You are about to ask another agent or person to review, continue, or take over a change.
- A review produced findings and you need a structured summary the receiver can act on.

## Do not use when

- The receiver already has full context — a packet adds noise.
- You want to run or schedule the work — Coordinate does not dispatch or track.
- You want an outcome judgment — use `evaluate`.

## Required inputs

- What was done so far (the change, the contract, or the problem).
- What the receiver is being asked to do.
- Any constraints or open questions the receiver must know.

## Procedure

1. Decide the packet type: handoff, review-request, or findings-summary.
2. Gather only what the receiver needs, using the field lists below. Omit history the receiver cannot act on.
3. Write the packet as self-contained text: a receiver who was not present should understand it without follow-up questions.
4. Name the concrete next action the receiver should take.
5. Output the packet to the user. Coordinate does not send the packet, paste it into an external receiver, or auto-dispatch. Delivery is the user's call.

## Packet shapes

- **Handoff:** goal, current state, what is done, what is left, the specific ask, constraints, open questions.
- **Review-request:** goal / change contract; scope and non-goals; acceptance checks (each with its verification method); changed files / diff location; verification evidence; reviewer focus (what to check first); the exact requested verdict.
- **Findings-summary:** each finding — the finding; blocking or non-blocking; evidence; required or suggested resolution; resolution status; re-review required (yes/no).

## Stop conditions

- The packet is written and the next action is named.
- The inputs are too thin to write a self-contained packet → say so and list what is missing.

## Output contract

A single packet in plain text, labeled by type, with a named next action. The packet is the only output. Coordinate does not send it, paste it to an external receiver, write state files, populate a board, or trigger dispatch.

## Example

> **Packet: review-request**
> **Goal / contract:** alerts delivered within 15 min; no alert lost on worker crash; shutdown drains the queue; idempotent on retry.
> **Scope / non-goals:** `src/alerts/queue.py`, `src/alerts/worker.py`; non-goal — SMS channel.
> **Acceptance checks:** crash-recovery (automated test), shutdown drain (automated test), idempotency (evidence review of diff).
> **Changed files / diff:** branch `alert-queue`, commit range `a1b2c3..d4e5f6`.
> **Verification evidence:** crash-recovery test passes (zero lost); shutdown-drain test passes; idempotency key in diff.
> **Reviewer focus:** the crash-recovery path and the shutdown drain; the new persistent queue shape.
> **Requested verdict:** approve / approve-with-findings / blocking findings.
> **Next action:** reviewer runs an independent pass against the acceptance checks and returns a findings-summary.