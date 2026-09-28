# Pi host integration (retired)

This directory no longer owns or deploys Pi agent definitions.

## Canonical source

Pi Web custom agent profiles live in the `pi-extensions` repository, under
`pi-extensions/agents/`. That repository is their single canonical source.
Install them from a `pi-extensions` checkout using the command in that
directory's own `agents/README.md`.

Do not copy agent definitions into this repository, and do not re-create
`hosts/pi/agents/`. There is no sync step and no mirror: this repository keeps
no copy, so it has nothing to keep in step and nothing to disagree with.

## Why this was retired

`hosts/pi/agents/` used to version five Pi agent definitions written in the
`pi-subagents` frontmatter dialect. Pi Web's built-in Agent replaced that
runtime, and the canonical definitions now live in `pi-extensions/agents/`,
in the built-in Agent schema.

The copies kept here were stale. They carried `systemPromptMode`,
`inheritProjectContext`, `inheritSkills`, and `acceptanceRole`, none of which
the current runtime honors, and none of which any tool in this repository read
or deployed. `scripts/install.py` distributes only the Core skills declared in
`skillset.json` and never touches `hosts/`, so deployment was always manual.

A second copy therefore bought nothing and cost two things: a competing
canonical claim, and a rollback risk. A manual deploy of these files would
have silently replaced the current profiles with the retired schema.

## What this layer still means

The responsibilities those agents realized — browser-level evidence,
independent execution evidence, implementation-quality review, change-scoped
architecture review, and formal independent review — are realized on the Pi
host by the profiles in `pi-extensions/agents/`. Core (`skills/`) continues to
describe responsibility and evidence type and stays vendor-neutral: nothing
outside `hosts/` depends on any particular agent existing.
