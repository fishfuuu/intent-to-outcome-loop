# Engineering Companion

Optional engineering skills commonly used alongside Intent to Outcome Loop.

This pack is **not** Seven Core, not a Core extension point, not a mandatory
workflow, and not a Matt full distribution. Skills can be used one at a time.
There is no required linear pipeline.

## Skills

| Skill | Provenance |
|---|---|
| `grilling` | upstream-snapshot |
| `domain-modeling` | upstream-snapshot |
| `tdd` | upstream-snapshot |
| `code-review` | intentional-fork |
| `codebase-design` | upstream-snapshot |
| `improve-codebase-architecture` | upstream-snapshot |

Upstream snapshots are copied from `mattpocock/skills`.
Canonical identity is the snapshot commit, not a floating branch:

- upstream branch (informational): `main`
- snapshot commit: `c55ee46073ed923f86ce59a5eb3b6d895095d1b7`

Repository copies use LF. Fidelity is text-equivalent to that snapshot
modulo newline normalization, not byte-identical CRLF. See
`pack-manifest.json` and `THIRD_PARTY_NOTICES.md`.

Canonical `grilling` is the upstream rounds/frontier interview, not the
older one-question-at-a-time snapshot.

`code-review` is a standalone fork of Matt Pocock's two-axis design. It has
no runtime dependency on `/setup-matt-pocock-skills` or
`docs/agents/issue-tracker.md`. An ITOL change record is only an optional
spec source when it clearly belongs to the current change.

## Common combinations (optional, not a lifecycle)

Engineering delivery, when useful:

`grilling` → `domain-modeling` (if the domain needs modeling) → `tdd` → `code-review`

Architecture, when useful:

`codebase-design` → `improve-codebase-architecture`

Do not treat these as a required chain. Do not replace `task-router` or
Reviewed Change formal Plan / Final review. `code-review` is a general
Standards + Spec diff review. ITOL/Pi `independent-reviewer` is the formal
Reviewed Change gate. They are different roles.

## Status

**Maturity: provisional.** Not installed by default. Not in `skillset.json`.
`scripts/install.py` installs Seven Core only.

## Installation

Copy selected skill directories into the host skill folder, for example
`.agents/skills/` or `.claude/skills/`. Pack installation automation is not
provided.

Canonical source for these copies is **this pack**, not Matt's
`link-skills.sh`. Re-running Matt bulk linking can overwrite deployed copies.
Do not let it manage skills that this pack owns. Upstream updates are a
manual compare-then-upgrade.

## Deployed `code-review`

After copying `skills/code-review/SKILL.md` to
`~/.agents/skills/code-review/SKILL.md`, the two files must be byte-identical.
