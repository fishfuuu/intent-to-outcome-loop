# Knowledge Work Companion

Optional companion skills for everyday and professional knowledge work:
turning evidence into judgment, judgment into a responsible decision, and a
material deliverable into something trustworthy.

This pack is **not** Seven Core, not a Core extension point, not a mandatory
workflow, and not an orchestrator. Skills can be used one at a time. There
is no required pipeline, no state machine, no router, and no approval
framework.

## Skills

| Skill | Provenance | What it is for |
|---|---|---|
| `research-synthesis` | intentional-fork | Evidence → judgment: several sources become the strongest traceable judgment they support. |
| `decision-memo` | intentional-fork | Judgment → decision: the minimum evidence, options, trade-offs, risks, and ask a human needs to decide. |
| `reviewing-output` | intentional-fork | Deliverable → trustworthy deliverable: a five-lens review of a knowledge-work output before it is relied on. |

All three are forks of upstream skills from `andreaswasita/copilot-cowork-dojo`.
Canonical identity is the pinned upstream commit:

- upstream repository: https://github.com/andreaswasita/copilot-cowork-dojo
- upstream commit: `10605ba267c18dfd725a3507f4cf14b607a64e9a`
- license: MIT (Copyright (c) 2026 Andreas Wasita)

Upstream naming is retained. Upstream structure and wording are preserved
wherever the semantics still fit; each skill changes only where
evidence-constrained judgment, host neutrality, standalone operation, or
this pack's boundaries require it. See `THIRD_PARTY_NOTICES.md` and
`pack-manifest.json`.

## What This Pack Covers

- Everyday and professional knowledge work: research, analysis, memos,
  reports, proposals, executive communication, and other material
  deliverables.
- Judgment under incomplete evidence, including naming when the evidence is
  not sufficient for the decision at hand.
- Host-neutral operation. The skills do not depend on a specific assistant,
  vendor, connector, or host runtime.

## What This Pack Does Not Cover

- software engineering workflow or engineering code review;
- enterprise problem discovery or deployment adoption;
- Windows host / runtime safety;
- DOCX / XLSX / PPTX / PDF mechanics;
- Gmail / Calendar / Drive automation or connectors;
- deep-research orchestration;
- Core delivery routing, change classification, or review gates;
- meeting capture, inbox triage, or email/calendar work of any kind.

## Boundaries With The Other Packs

| Concern | Owner |
|---|---|
| Software engineering judgment, code review, architecture, TDD | `engineering-companion` |
| Enterprise problem discovery and bounded adoption | `internal-enterprise-companion` |
| Everyday / professional knowledge-work judgment | **`knowledge-work-companion`** (this pack) |
| Windows host / runtime safety | `windows-agent-safety` |
| Intent-to-Outcome delivery governance | Seven Core |

`reviewing-output` reviews knowledge-work deliverables. It does not review
code or engineering changes; those follow the engineering review path. It is
also not the formal independent review gate of a Reviewed Change.

## Common Combinations (optional — example only)

Example only, not a lifecycle and not a required order:

- `research-synthesis` → `decision-memo` — synthesize sources, then compress
  the result into a decision memo.
- `decision-memo` → `reviewing-output` — review the memo before it goes out.
- `research-synthesis` → `decision-memo` → `reviewing-output` — the three
  used together on one piece of work.
- Any one skill alone.

None of these combinations are mandatory, and no skill requires another to
run.

## Status

**Maturity: provisional.** Not installed by default. Not in `skillset.json`.
Not part of the Core install surface. `scripts/install.py` installs the
Seven Core skills only.

The pack ships exactly three skills. Capture, meetings, and document /
spreadsheet / deck / email / calendar tooling are deliberately out of
scope for this version.

## Installation

Pack installation automation is not provided. Copy the skill directories you
want into your host's skill folder, for example `.agents/skills/` or
`.claude/skills/`, using that host's standard skill mechanism.

Canonical source for these copies is **this pack**, not the upstream
repository. Upstream updates are a manual compare-then-upgrade against the
pinned commit.
