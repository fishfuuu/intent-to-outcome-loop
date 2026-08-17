# Intent to Outcome Loop

Lightweight, vendor-neutral **delivery skills** for coding agents.
Seven small skills that help an agent work in a way that is verifiable
and reviewable — without becoming a platform.

This is *not* an agent runtime, a scheduler, a workflow server, a
daemon, or a project management system. There is no global state, no
task board, no database, no web UI. The only persistent artifacts any
skill can create are on demand: a Reviewed Change record, and — when
the user explicitly asks — one Handoff Markdown from `coordinate`.

## What problem this solves

When you use a coding agent seriously, the hard parts are not the code
— they are deciding what to build, picking the right-sized process for
the risk, verifying the result, and handing work between people and
agents without losing context. These seven skills give the agent a
small, consistent vocabulary for those parts.

## The seven skills

| Skill | What it does | State |
| --- | --- | --- |
| `shape` | Optional. Clarifies an unclear problem into a brief: problem, goal, the smallest sufficient solution, boundary, and success criteria. May challenge an over-heavy proposed solution. | None |
| `evaluate` | User-invoked checkpoint. Returns CONTINUE / IMPROVE / PIVOT / STOP / INSUFFICIENT_EVIDENCE. Never auto-runs. | None |
| `task-router` | The default entry point. Classifies a task as Quick, Bounded, or Reviewed and hands off to the matching change skill. Read-only. | None |
| `quick-change` | Docs, copy, comments, formatting, behavior-neutral edits. | None |
| `bounded-change` | Local behavior-affecting change with a clear boundary and a verify loop. | None |
| `reviewed-change` | Architecture, data, security, interface, cross-module changes. Change Contract → Falsification / RED → Plan Review → slices → Verification → independent review. | Optional record |
| `coordinate` | Writes handoff, review-request, and findings-summary packets for people/agent and agent/agent handoffs. | None |

## Two ways in

- **Most users** only need `task-router`. Give it a software task; it
  reads the task and the code, classifies Quick / Bounded / Reviewed,
  fills in a short Route Brief (goal, boundary, risk, verification), and
  — if you asked for the work to be done and nothing blocks it — hands
  off to the matching change skill **in the same conversation**. You do
  not need to understand the three tiers or re-type a skill name.
- **Engineers** who already know the tier can call `quick-change`,
  `bounded-change`, or `reviewed-change` directly. `task-router` is a
  convenience, not a gate.

`task-router` itself never edits files; "hand off" means the matching
change skill takes over the editing.

## The requirement–implementation–evaluation flywheel

The seven skills form a light cognitive model, not a mandatory pipeline.
There is no single master entry skill, and you never have to run all of
them. Use the part you are in:

```
Requirement unclear?            shape
Ready to implement?             task-router → quick-change / bounded-change / reviewed-change
Want to judge the result?       evaluate   (only when you call it)
Need to switch person/agent/session or request review?   coordinate
```

How it stays user-driven:

- **shape** is for when the requirement is unclear — not a required first step.
- **task-router** is the default entry when you want a task done; it hands
  off to a change skill in the same conversation. Engineers who already
  know the tier can call a change skill directly.
- **evaluate** is only ever called by you. No skill or the flywheel itself
  auto-triggers it.
- **coordinate** is an on-demand connector for switching people, agents,
  sessions, or requesting review — not a step you pass through every round.
- The flywheel is a mental model, not a lifecycle state machine.

Core stays aimed at individuals, solo super-individuals, and small teams.
It is not marketed as an enterprise governance system.

## Core and Companion Skills

Core provides the cross-project backbone: outcome and boundary
(`shape`), risk-proportionate routing (`task-router`), an
evidence-bearing implementation loop (`quick-change` /
`bounded-change` / `reviewed-change`), independent review discipline
(`reviewed-change`), handoff (`coordinate`), and user-owned evaluation
(`evaluate`).

Deeper specialist methods are **Companion Skills** — separate,
optionally-installed skills you combine with Core for a given task, not
install dependencies of Core. Examples (inspirations, not mandatory and
not bundled here):

- hard-to-reproduce bugs or performance regressions → systematic debugging
- new behavior or regression protection → TDD
- independent diff review → code review
- browser behavior → browser or end-to-end testing
- security → security review
- performance → profiling and performance testing
- architecture or simplification → architecture / code-simplification skills
- product discovery or ROI → product-management or value-evaluation skills

Core does not copy these methods' full processes. When a Companion
Skill is not installed, Core still works on its own — it just will not
apply that specialist depth. Do not treat any external repository or
third-party skill as a required dependency of Core.

### Companion Skills recommendation

Companion Skills are recommendations, not dependencies — Core never
requires a specific third-party skill.

Two common starting points:

**Engineering** — IT / formal software development

- Recommended: `tdd`, `diagnosing-bugs`, `code-review`
- Optional: `improve-codebase-architecture`, browser / E2E testing, security review, performance profiling

**Prototype** — anyone building runnable prototypes, including business, product, design, and solo builders

- Recommended: `frontend-design`
- Optional: `ui-ux-pro-max`, browser / E2E testing, `prototype`, `research`

See [docs/companion-skills.md](docs/companion-skills.md) for what each covers and how to choose.

## Quick vs Bounded vs Reviewed

Pick the **lightest** path that is still safe:

- **Quick** — behavior-neutral, exact boundary, trivially reversible. No verification of behavior needed beyond "nothing changed that matters."
- **Bounded** — behavior-affecting, but contained in one function/module/feature with a clear boundary and a verification method. Record a baseline, verify the same way before and after, iterate the implementation not the goal.
- **Reviewed** — touches architecture, data shape, security, a public interface, or spans modules. A lightweight flow: Change Contract → Falsification / RED → Plan Review → vertical slices → Verification → Final Independent Review → findings resolution → re-review when required.

Escalation is built in: a Quick change that affects behavior becomes
Bounded; a Bounded change that grows past its boundary becomes
Reviewed.

## Install

Requirements: Python 3.8+ (standard library only).

### Codex

```bash
python scripts/install.py --target codex --scope user
```

Installs the skills into `~/.agents/skills`. The `evaluate` user-only
policy is enforced via `skills/evaluate/agents/openai.yaml`.

### Claude Code

```bash
python scripts/install.py --target claude --scope user
```

Installs the skills into `~/.claude/skills`. The installer adds
`disable-model-invocation: true` to the installed copy of `evaluate`
so the agent cannot auto-invoke it; only an explicit user call runs it.

### Options

- `--scope project` — install into the **current project** (cwd)
  instead of the user directory. The target path depends on the host:
  - Codex: `<project>/.agents/skills`
  - Claude Code: `<project>/.claude/skills`

  The project is the current working directory, never the toolkit's own
  location or the user home.
- `--dry-run` — report what would be written, without writing or
  deleting anything.
- `--destination <dir>` — install into an explicit directory, for tests
  and non-standard hosts. Overrides scope-based resolution. With a
  single `--target`, skills are written directly under `<dir>`.
- `--target both --destination <dir>` — install for both Codex and
  Claude into **separate subdirectories** `<dir>/codex/` and
  `<dir>/claude/`, so the two host views never overwrite each other.

The installer **never deletes** unrelated skills in the target
directory. It only writes the skills it owns. If a target skill already
exists, the installer reports which files would be overwritten.

## Validate

```bash
python scripts/validate.py
```

Checks the skill manifest, the skills directory, frontmatter, line
budgets, host policies, local-path leakage, and doc links. Exits
non-zero on errors.

## Run the tests

```bash
python -m unittest discover -s tests -v
```

## OpenCode and Grok (experimental)

OpenCode and Grok can read the canonical `SKILL.md` files directly as
plain markdown — copy the `skills/` tree into your host's skill
directory manually. v0.4 does not yet generate adapter metadata for
these hosts, so the `evaluate` user-only policy is a convention the
operator must respect until a future version adds the metadata. See
[docs/compatibility.md](docs/compatibility.md) for the full compatibility
table.

## License

MIT. See [LICENSE](LICENSE).

## Contributing

See [AGENTS.md](AGENTS.md) for the contribution rules. This repo does
not require you to use its own delivery skills to maintain itself.