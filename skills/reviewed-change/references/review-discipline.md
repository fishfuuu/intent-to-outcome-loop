# Review discipline reference

How to review a non-trivial Reviewed Change with discipline. Read this before Plan Review and again before Final Review, and apply only the parts that fit the change's risk. For a small, low-risk reviewed change, rely on the main SKILL's Procedure.

## 1. Transition discipline

The two review transitions are real stop/re-start points, not paperwork:

- **Plan Review is blocking** — production implementation stays forbidden until a **new** independent Plan Review returns an explicit **APPROVED** verdict. "Findings fixed" by the implementer is not "review passed."
- **Final Review approval freezes the reviewed production diff** — once approved, changing production code, config, migrations, or user-visible behavior invalidates that approval: re-verify, then get a new independent Final Review.
- The implementer saying "fixed" is never reviewer closure. Only the independent reviewer's explicit verdict closes a finding.

## 2. Evidence sufficiency

Use the verification method the Change Contract promised. Do not substitute a cheaper signal for the actual acceptance evidence:

- browser / rendered QA ≠ lint / build
- rendered prototype comparison ≠ "the component is imported"
- a manual user flow ≠ an API unit test
- financial / business calculation acceptance ≠ "the endpoint returns HTTP 200"
- migration safety ≠ "the schema compiles"

If a check cannot be run as promised, do not silently replace it: record the limitation and use an explicit alternative evidence method. Passing an easier proxy does not satisfy a different acceptance method, and a green suite does not override a Contract/Standards finding.

## 3. Review focus by risk

- **UI / user-visible** — when the contract names a prototype, screenshot, DESIGN.md, or existing product reference, review the rendered result directly: hierarchy, layout/density, composition, interaction, states, and visual consistency against the reference. Using an existing component does not make a UI correct.
- **Data / business-critical calculation** — check data semantics, aggregation, thresholds, exceptions, scope/permission, and calculation correctness.
- **Architecture / integration** — check ownership, interface boundaries, failure behavior, blast radius, and compatibility.

## 4. Final Review depth

The two review axes:

- **Contract / Spec axis** — does the implementation satisfy the agreed Change Contract and any authoritative references, with evidence that corresponds to the success criteria?
- **Standards / Quality axis** — does it meet the repository's applicable standards, with tests that prove the target behavior?

The same reviewer may do both; no two reviewers or parallel agents are required, and this is not a new gate. Tests passing does not equal acceptance complete — manual and evidence-review checks must also run. Map each frozen User Acceptance Scenario to its evidence, and check authoritative references directly.

## 5. Finding classification

Four categories only (see the main SKILL). One rule is decisive:

> If the implementation fails an existing Contract, User Acceptance Scenario, or authoritative reference, it is **not** "non-blocking" merely because the fix is small.

If the contract says role switching affects the visible scope but the UI selector changes nothing, that is an IMPLEMENTATION_DEFECT, not a non-blocking polish item. A non-blocking finding stays a suggestion; do not implement it in the current scope by default.