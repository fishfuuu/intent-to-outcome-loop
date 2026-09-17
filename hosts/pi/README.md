# Pi host integration (optional)

`hosts/pi/agents/` holds the Pi subagent definitions this project uses in
practice. This directory is an **optional Pi host integration**. It is not
part of the Seven Core, and the Core does not depend on it.

## What this layer is

- It is one host's runtime realization of ITOL responsibilities: which role
  runs on which model, with which tools, under which permissions.
- Core (`skills/`) describes *responsibility and evidence type*, and stays
  vendor-neutral and host-neutral. This layer describes *concrete agents*.
- Other hosts may realize the same responsibilities with entirely different
  agents, runtimes, or hand-offs. Nothing outside `hosts/pi/` should assume
  these agents exist, and no Core skill requires them.

## Agents

| Agent | Responsibility |
|-------|----------------|
| `browser-qa-agent` | Browser-level evidence from the running UI |
| `execution-verifier` | Independent execution evidence: tests, builds, probes |
| `code-reviewer` | Standalone implementation-quality review |
| `change-architecture-reviewer` | Architecture and structural review of the current change |
| `independent-reviewer` | Formal independent review for `reviewed-change` |

`code-reviewer` and `change-architecture-reviewer` are deliberately distinct
and both are kept. The first is generic implementation quality; the second is
change-scoped architecture. Neither substitutes for the other, and neither
substitutes for `independent-reviewer`.

## Boundaries

- The frontmatter in these files is **Pi-specific** — `model`,
  `fallbackModels`, `tools`, `thinking`, `systemPromptMode`,
  `inheritProjectContext`, `inheritSkills`, `acceptanceRole` and similar.
  These are host defaults, not an ITOL Core contract. Other hosts will
  differ, and that difference is expected.
- Specialist agents produce **evidence and findings**, not approvals.
  Browser QA, execution verification, code review and architecture review
  results are inputs the `independent-reviewer` must itself judge for
  relevance, freshness, sufficiency and contract coverage. The formal
  Reviewed lifecycle remains defined by Core and decided by the main
  session.
- `code-reviewer` is a standalone capability. It does not depend on Matt
  Pocock's `code-review`, and it must keep working for users who have no
  Matt Pocock skills installed.
- Matt Pocock skills (`code-review`, `improve-codebase-architecture`,
  `tdd`, `grilling`, `codebase-design`, `domain-modeling`, and others) are
  **optional external skills**. They are not dependencies of these agents,
  and none of their content is vendored into this repository.
- This repository is the **canonical source** for these definitions. A copy
  deployed under a Pi agent directory is a deployment, not a source of
  truth. If the two disagree, the repository wins.

## Deployment

`scripts/install.py` distributes only the Core skills declared in
`skillset.json`, to the skills directories of the supported hosts. It does
not touch `hosts/`. Deploying `hosts/pi/agents/` into a Pi agent directory is
a separate step and is currently manual.
