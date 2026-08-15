# Core concepts

Coding Agent Delivery is a small set of skills that help a coding agent
work in a way that is verifiable and reviewable, without becoming a
platform. These are the ideas behind the seven skills.

## The three change paths

Every software change goes down one of three paths, chosen by risk and
clarity — not by preference.

- **Quick Change** — behavior-neutral edits: docs, copy, comments,
  formatting, config that does not affect runtime. No state.
- **Bounded Change** — a behavior-affecting change contained in one
  function, module, or small feature, with a clear boundary and a
  verification method. Records a baseline, verifies the same way before
  and after, iterates the implementation not the goal. No state.
- **Reviewed Change** — architecture, data shape, security, public
  interface, or cross-module changes. A lightweight flow: Change
  Contract, Plan Review, vertical slices, Verification, Final
  Independent Review, findings resolution, and re-review when required.
  May persist a record on demand.

The rule is to pick the *lightest* path that is still safe. If a Quick
change turns out to affect behavior, it escalates to Bounded. If a
Bounded change reveals a Reviewed risk (schema, security, shared
interface, cross-module, new workflow), it escalates to Reviewed.

## What is intentionally not here

This is not an agent runtime, a scheduler, a workflow server, a daemon,
or a project management system. There is no global delivery state, no
task board, no state machine, no SQLite database, no web UI, no MCP
server. The only persistent artifact any skill can create is a
Reviewed Change record, and only when a durable trail earns its keep.

## The two judgment skills

- **Shape** — optional, before any engineering work. Defines the
  problem, goal, boundary, and success criteria. It answers *what*
  and *whether*, not *how*.
- **Evaluate** — a user-invoked checkpoint during or after work.
  Returns CONTINUE, IMPROVE, PIVOT, STOP, or INSUFFICIENT_EVIDENCE. It
  never runs on its own.

## Routing and coordination

- **Task Router** — the default entry point for ordinary software tasks.
  Read-only. Classifies a task as Quick, Bounded, or Reviewed, fills in
  a short Route Brief, and — when the user asked for the work and nothing
  blocks it — hands off to the matching change skill in the same
  conversation. Engineers who already know the tier can call a change
  skill directly.
- **Coordinate** — writes handoff, review-request, and findings-summary
  packets so work can move between actors without losing context. It
  produces the packets; it does not send, dispatch, or track them.

## How the seven fit together

```
shape ──┐
        v
   task-router ──> quick-change
                 ─> bounded-change
                 ─> reviewed-change ─┬─> coordinate (review / findings packet)
                                     └─> evaluate (checkpoint)
```

Shape and Evaluate are optional and user-driven. Task Router is the
default entry point; it can hand off to a change skill in the same
conversation when the user asked for the work. The three change skills do
the work. Coordinate moves work between actors. Evaluate is a user-only
checkpoint. No skill forces another to run.

See [compatibility.md](compatibility.md) for host support and the
[reviewed-change record format](reviewed-change-record.md).