# Review discipline reference

How to review a non-trivial Reviewed Change with discipline. Read this before Plan Review and again before Final Review, and apply only the parts that fit the change's risk. For a small, low-risk reviewed change, rely on the main SKILL's Procedure.

## 1. Reviewer independence

**Minimum independence criteria:**

- Separate context: the reviewer cannot see the implementer's reasoning, intermediate attempts, or conversation history.
- Different session: same-session role-switching is not independent.
- Ideally different model or host: the strongest independence comes from a different reasoning system.

**Minimum reviewer evidence** (every review must show these):

1. Restate the Change Contract in the reviewer's own words.
2. The reviewer must actively attempt to identify a material counterexample or failure path. Report any found; if none, say no material uncovered path was identified. Do not invent an uncovered path.
3. Compare the actual diff against the contract and verification evidence.
4. State explicitly what was reviewed and what was not reviewed.

**Limited non-independent review:**

When no independent reviewer is available (solo developer, blocked access), the user may explicitly accept a **limited non-independent review**:

- It is supplemental diagnostic evidence only.
- It does not satisfy the independent Plan Review or Final Independent Review; it cannot authorize shipping, completion, commit, or deployment.
- Record the limitation; it is not independent approval.
- Use only when no review is the alternative or blocking is indefinite.

**Coordinate integration:**

When requesting review across sessions or agents, use `coordinate`'s review-request packet as the transport format. The packet must include the Change Contract, diff location, acceptance checks, and verification evidence so the reviewer has sufficient context.

## 2. Transition discipline

The two review transitions are real stop/re-start points, not paperwork:

- **Plan Review is blocking** — production implementation stays forbidden until a **new** independent Plan Review returns an explicit **APPROVED** verdict. "Findings fixed" by the implementer is not "review passed."
- **Final Review approval freezes the reviewed production diff** — once approved, changing production code, config, migrations, or user-visible behavior invalidates that approval: re-verify, then get a new independent Final Review.
- The implementer saying "fixed" is never reviewer closure. Only the independent reviewer's explicit verdict closes a finding.

## 3. Evidence sufficiency

Use the verification method the Change Contract promised. Do not substitute a cheaper signal for the actual acceptance evidence:

- browser / rendered QA ≠ lint / build
- rendered prototype comparison ≠ "the component is imported"
- a manual user flow ≠ an API unit test
- financial / business calculation acceptance ≠ "the endpoint returns HTTP 200"
- migration safety ≠ "the schema compiles"

Code presence or automated tests alone cannot prove a rendered or interactive outcome. If a check cannot be run as promised, do not silently replace it: record the limitation and use an explicit alternative evidence method. Passing an easier proxy does not satisfy a different acceptance method, and a green suite does not override a Contract/Standards finding.

For failure-sensitive acceptance claims — such as recovery, durability, idempotency, retry safety, or no-loss behavior — review the bounded failure model and the failure points covered by the evidence. RED proves that a check can catch a counterexample; it does not prove reliability beyond that model. Treat important untested failure points as residual limitations, and do not approve a broader claim than the evidence supports.

### Evidence type follows acceptance type

Evidence method follows what the frozen acceptance actually claims, not a blanket browser mandate:

- **Pure calculation / data semantics** (SUM(gmv)/SUM(cost), a window delta, a permission-boundary function) — automated tests can be primary, even sufficient. Do not force a browser for a financial formula.
- **API / permission / runtime behavior** — automated tests plus API/runtime evidence, sized to risk; not every API must be clicked by hand.
- **UI / rendered / interactive behavior** ("each row shows a sparkline", "expand shows child rows", "filter leaves only bound stores", "click enters a given state") — direct observation of the running result: browser/rendered verification, a manual runtime check by the implementing agent, or other direct observation of the running UI. The tool is not fixed; the requirement is that the evidence actually observes what the user is supposed to see or do.

### Acceptance → evidence mapping

For every frozen acceptance check or User Acceptance Scenario, the reviewer states which evidence proves it. Judge evidence type, not just whether some check passed: a spark-data unit test proves data logic, not a rendered sparkline. A type mismatch (UI outcome "verified" by a data test) is evidence insufficient for that acceptance, so verification is incomplete and Final Review cannot APPROVED yet — return to Verification, it is not a finding merely because the evidence is wrong type. If the behavior is actually observed and is absent or wrong, that is an IMPLEMENTATION_DEFECT (blocking finding).

## 4. Review focus by risk

- **UI / user-visible** — when the contract names a prototype, screenshot, DESIGN.md, or existing product reference, review the rendered result directly: hierarchy, layout/density, composition, interaction, states, and visual consistency against the reference. Using an existing component does not make a UI correct.
- **Data / business-critical calculation** — check data semantics, aggregation, thresholds, exceptions, scope/permission, and calculation correctness.
- **Architecture / integration** — check ownership, interface boundaries, failure behavior, blast radius, and compatibility.

## 5. Final Review depth

The two review axes:

- **Contract / Spec axis** — does the implementation satisfy the agreed Change Contract and any authoritative references, with evidence that corresponds to the success criteria?
- **Standards / Quality axis** — does it meet the repository's applicable standards, with tests that prove the target behavior?

The same reviewer may do both; no two reviewers or parallel agents are required, and this is not a new gate. Tests passing does not equal acceptance complete — manual and evidence-review checks must also run. Map each frozen User Acceptance Scenario to its evidence, and check authoritative references directly.

## 6. Finding classification

Four categories only (see the main SKILL). One rule is decisive:

> If the implementation fails an existing Contract, User Acceptance Scenario, or authoritative reference, it is **not** "non-blocking" merely because the fix is small.

If the contract says role switching affects the visible scope but the UI selector changes nothing, that is an IMPLEMENTATION_DEFECT, not a non-blocking polish item. Likewise, if the contract says each row shows a sparkline but the rendered row shows "—" while the spark-data unit test is green, that is an IMPLEMENTATION_DEFECT — the rendered outcome is absent. A non-blocking finding stays a suggestion; do not implement it in the current scope by default. If evidence is simply missing and the implementation has not yet been shown wrong, verification is incomplete and Final Review cannot approve yet, but it is not yet a finding.