# Core concepts

Intent to Outcome Loop is a small set of skills that help a coding agent
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
server. The only persistent artifacts any skill can create are on
demand: a Reviewed Change record when a durable trail earns its keep,
and — when the user explicitly asks — one Handoff Markdown from
`coordinate` (a snapshot, not state).

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
                 ─> reviewed-change ─┬─> coordinate (review / findings / handoff packet)
                                     └─> evaluate (checkpoint, user-invoked only)
```

Shape and Evaluate are optional and user-driven. Task Router is the
default entry point; it can hand off to a change skill in the same
conversation when the user asked for the work. The three change skills do
the work. Coordinate moves work between actors. Evaluate is a user-only
checkpoint. No skill forces another to run.

## The requirement–implementation–evaluation flywheel

The seven skills are best understood as a light cognitive flywheel, not a
pipeline you must complete or a lifecycle state machine:

```
shape → task-router / change skill → observable result → user-invoked evaluate
        ↑                                                              │
        └──────────────────────────────────────────────────────────────┘
```

- **Requirement unclear** → `shape`.
- **Ready to implement** → `task-router` (or a change skill directly).
- **An observable result exists** → the user may call `evaluate`.
- **Need to switch person, agent, session, or request review** → `coordinate` (on demand, not every round).

The flywheel is a mental model. There is no master entry skill, and you do
not have to run every skill each round.

### How evaluate's verdict shapes the next step

`evaluate` is only ever called by the user; it never auto-triggers another
skill. Its verdict says what the user should do next — the user, not the
flywheel, decides and invokes the next step:

- **CONTINUE** — keep the direction; move to the next implementation slice.
- **IMPROVE** — direction holds, but make a minimal correction to the requirement or the implementation boundary.
- **PIVOT** — go back to the requirement; redefine the method or the boundary.
- **STOP** — the outcome is met, or the effort is no longer worth it; the reason lives in the rationale.
- **INSUFFICIENT_EVIDENCE** — gather more evidence, then evaluate again.

No skill auto-triggers `evaluate`, and `evaluate` auto-triggers nothing.

### Shared meaning across skills

Several terms express the same idea in different skills' contexts. The
names are not unified into one vocabulary on purpose — each skill keeps
the word that reads naturally in its own section. They carry the same
content as it moves:

| Cross-skill meaning | shape | router / change | evaluate | carried across contexts by |
| --- | --- | --- | --- | --- |
| What to achieve | Goal | Outcome / Expected behavior | Expected outcome | coordinate |
| How "done" is judged | Success criteria | Acceptance checks | Success signals | coordinate |
| What is out of scope | Boundary | Non-goals / Must-preserve | (applied, not restated) | coordinate |
| What was observed | — | Baseline / Verified | Evidence | coordinate |
| What is not yet proven | — | Residual limitations | Gaps | coordinate |
| Open points | (in the brief) | Open questions | (in the rationale) | coordinate |

`coordinate` is the carrier: when work crosses a person/agent/session
boundary, it packs these into a handoff packet so the receiver does not
re-derive them.

### Prototype to formal engineering

Moving from a prototype to formal engineering is a change in engineering
depth and risk, not a Core lifecycle transition. Treat it as a Reviewed
change when it carries that risk.

- The business goal, the rules, the data meaning, and the acceptance
  meaning should stay continuous from prototype to formal.
- The prototype's technical implementation may be rewritten by the formal
  build.
- Prototype evidence must not be presented as production evidence.
- Permissions, security, and production rules for a specific project are
  set by that project, not by Core.

## Core and Companion Skills

Core is the cross-project backbone: outcome and boundary, risk-proportionate
routing, an evidence-bearing implementation loop, independent review
discipline, handoff, and user-owned evaluation. It deliberately does not
contain deep specialist methods.

Specialist depth comes from **Companion Skills** — separate, optionally
installed skills combined with Core for a given task. They are not
install dependencies of Core, and Core does not copy their full
processes. Examples (inspirations, not bundled and not required):
systematic debugging for hard-to-reproduce bugs; TDD for new behavior
and regression protection; code review for independent diff review;
browser or end-to-end testing for browser behavior; security review;
profiling and performance testing; architecture or code-simplification
skills; product-management or value-evaluation skills for discovery and
ROI.

When a Companion Skill is not installed, Core still works on its own —
it just will not apply that specialist depth. No external repository or
third-party skill is a required dependency of Core.

See [compatibility.md](compatibility.md) for host support and the
[reviewed-change record format](reviewed-change-record.md).