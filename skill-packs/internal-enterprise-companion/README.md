# Internal Enterprise Companion

Optional companion skills for internal enterprise IT, data, automation, and AI/Agent delivery.

## Purpose and Positioning

Intent to Outcome Loop Core provides the cross-project delivery backbone (intent, boundaries, risk-proportionate paths, verification, and handoff). This pack provides optional **fieldwork and business discovery methods** for internal enterprise environments where requirements are often second-hand, business semantics are undocumented, and adoption must happen in real operations.

**These are capability lenses, not phases. Use only the one needed by the current uncertainty.**

Do not treat this pack as a mandatory linear lifecycle (`shape → observe → discover → worth → validation → deployment → adoption`). Not all tasks need companion skills; when a task does not require specialist fieldwork methods, use the Seven Core skills directly.

## The Six Companion Skills

| Skill | When to use | Primary output |
|---|---|---|
| `observe-real-work` | When second-hand descriptions or PRDs are not enough to see the real job. Follow one complete business cycle to capture actual actions, trusted data sources, exceptions, and workarounds. | First-line evidence of actual work (no solution design). |
| `discover-business-contract` | When problem and solution direction are already stable, but prototypes, documents, or handoffs leave material business semantics (rules, data definitions, state transitions, permissions, decision rituals) that engineering would otherwise have to guess. | Frozen material business contract, or explicit unresolved decision blocks. |
| `worth-building-now` | When a real problem is identified, but the team needs to judge whether it justifies internal resource investment before scheduling implementation. | Recommendation: *Worth validating*, *Discovery only*, or *Not now*. |
| `bounded-validation` | When an internal exploration, PoC, or pilot lacks an end condition, real-enough data, or a referee to judge business value. | Five boundings: claim, referee, evidence bar, judgment moment, and four observable outcomes. |
| `smallest-real-deployment` | When an internal team will try a change in the real business to prove value on one end-to-end path with real-enough data and a business user operating or judging it. | Proof of business value on one path (does not implement code). |
| `adopted-not-released` | When a system or tool is live or UAT-passed, diagnosing why it remains unused or whether target users naturally use it without ongoing project team chasing. | Primary adoption blockage classification and smallest recommended adoption move. |

## Status

**Maturity: Field-trial ready**

Validated through:
- Static boundary review
- V0.1 routing and runtime benchmark
- V0.2 delta benchmark
- Focused boundary and unresolved-decision regressions

*Not yet validated through sustained real-world field usage.*

## Key Design Boundaries

This pack does **not** provide:
- A fixed enterprise workflow or mandatory pipeline
- An orchestrator or daemon
- A lifecycle state machine, task board, or stage-gate registry
- A replacement for the Seven Core skills
- A mandatory Agent architecture
- A requirement that every internal problem must become software or AI

**Core principle:** Use the smallest sufficient method for the problem that exists now.

## Installation and Packaging

This pack is an optional companion pack and is not installed by default.

- It is **not** part of the Core install surface or the Core `skillset.json`.
- The repository installer `scripts/install.py` installs the Seven Core skills, not this optional pack.
- Pack installation automation is not provided; users who choose to use this pack install or copy the selected skill directories into their host's project or user skill directory using their host's standard skill mechanism (e.g. `.claude/skills/`, `.agents/skills/`, or `~/.gemini/config/skills/`).

## Method Influences and Authorship

This pack was informed by public Forward Deployed Engineering (FDE) literature and by practical internal enterprise delivery experience:
- General concepts such as direct workplace observation, bounded exploratory validation, focused end-to-end real deployment, and post-release usage adoption draw conceptual inspiration from open methodology discussions.
- The Skill procedures, routing boundaries, evidence disciplines, stop conditions, and runtime contracts in this pack were authored for the Intent to Outcome Loop implementation.
- `discover-business-contract` was authored specifically for Intent to Outcome Loop to freeze material business semantics, state/permission transitions, and decision rituals before engineering handoff.
- External FDE skills (`change-three-roles`, `read-old-write-new`, `eval-driven-quality`) are not redistributed in this pack.
