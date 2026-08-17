# The Reviewed Change record

`reviewed-change` is the only skill that may persist a record. A
record is created **on demand** — when a durable trail earns its keep
(audit, a team handoff, an async reviewer). Small reviewed changes can
skip it. Nothing forces persistence; the Change Contract can live in
the conversation.

## Location

```
.agent-delivery/changes/<change-id>/record.md
```

`<change-id>` is a short, stable, human-readable id, for example
`2026-08-15-alert-queue`. Use the date and a slug of the change. The
`.agent-delivery/` directory is runtime state: it is git-ignored by
this repo and is not shipped.

## Format (v0.2)

A record mirrors the reviewed-change flow, in this order:

```markdown
# <change-id>

## Change Contract
- Outcome.
- Proposed approach / design — the implementation path, the key
  technical boundaries, and the relevant data or state ownership. Only
  what the reviewer needs to judge the approach; not a standalone
  Design Specification.
- Must-preserve behaviors.
- Non-goals.
- Risk dimensions.
- Affected boundaries/files.
- Acceptance checks, each with a verification method
  (automated test / manual check / evidence review).
- User Acceptance Scenarios (only when the change has user-observable
  behavior): actor → action → observable business result.
- Reviewer.
- Unresolved decisions.

## Falsification / RED
Which practical automated acceptance checks produced a real RED — the
actual evidence that each failed on the pre-existing, missing, or
counterexample behavior. Which checks cannot reasonably form RED, and
the alternative evidence recorded instead. Production implementation
has not started.

## Plan Review
Reviewer (not the implementer) + verdict (approved / blocking / blocked),
and the review date. The reviewer reviews the Change Contract and the
actual falsification evidence: whether the outcome and the proposed
approach / design agree, whether the approach is sound, whether the
boundaries are clear enough, whether the acceptance checks cover the
necessary behaviors, and whether the verification methods are reasonable.
Without RED or reasonable alternative evidence, do not approve or start
implementing. A blocking finding here means implementation did not start.

## Slices and verification
Each vertical slice: what it delivered, which acceptance check it
satisfied, and the verification result (test output / command / evidence).

## Final Independent Review
Reviewer + verdict, and the findings split into:
- Blocking: violates the contract, an acceptance check, or a safety
  boundary, or makes the result unacceptable.
- Non-blocking: an improvement or future enhancement (not in scope).

## Findings resolution
For each blocking finding: the fix, the verification re-run, and the
reviewer's re-review verdict ("implementer says fixed" is not closed).
Each independent reviewer verdict is one review round; the first blocking
verdict is round 1, a re-review reporting the same blocker is round 2. If
the same blocking root cause is still open after round 2, the change is
paused and the user is asked to choose: change the design, narrow the
scope, or pause. Non-blocking findings are recorded as later suggestions
and must not be sneaked into scope.

## Stop or handoff
The final state (resolved / paused / handed back to the user) and, if
relevant, the user decision that was required.
```

## Rules

- Keep it short. The record supports the review; it is not a substitute
  for the code.
- Write the Change Contract and acceptance checks before implementing,
  then verify against them — do not write checks that justify the
  result after the fact.
- The reviewer must not be the implementer. If no independent reviewer is
  available, report BLOCKED in the Final Review section; do not
  self-approve.
- After Plan Review passes, the Change Contract is the baseline. If the
  outcome, must-preserve, non-goals, acceptance meaning, risk level, or
  boundaries change, amend the contract and re-run Plan Review before
  continuing.
- Do not commit the record to a project repo unless the project wants
  it; by default `.agent-delivery/` is local and git-ignored.

See [concepts.md](concepts.md) for where this fits in the model.