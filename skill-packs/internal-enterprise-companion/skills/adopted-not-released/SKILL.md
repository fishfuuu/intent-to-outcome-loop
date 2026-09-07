---
name: "adopted-not-released"
description: "Use when something is \"live\", UAT-signed, or checklist-green, but it may not be part of real work: idle official tool, shadow Excel/ChatGPT, or usage that exists only while the project team is still chasing people. Do not use as Evaluate (no CONTINUE/PIVOT/STOP). A live unused system starts here. Use when the user runs /adopted-not-released. Triggers: 上线没人用, 验收, 影子Excel, 伴舞, 项目组一走就停."
---

# Adopted, not merely released

## Purpose

Diagnose and **recommend** the smallest adoption move so a released thing can become **ordinary work**. Do not implement engineering changes.

Go-live, UAT, and training attendance are not adoption.

This skill does **not** return Evaluate verdicts. If the user wants a CONTINUE / IMPROVE / PIVOT / STOP judgment on the outcome, they call `evaluate` with evidence.

## Use when

- UAT is signed or the feature checklist is green, and the team is ready to "hand over".
- Official system idle; people still use Excel, email, or consumer ChatGPT for the same job.
- Usage was high while the project team sat beside users, then fell when chasing stopped.
- Success is being reported as account count, training sign-in, demo headcount, or UAT ticks.

## Do not use when

- The live question is still what to build, and nothing has been released → `shape` / `worth-building-now`.
- The user explicitly wants an outcome verdict only → `evaluate`.
- The main complaint is model quality / "answers look amateur" → `eval-driven-quality` is the specialized tool; this skill does not build an eval framework (Procedure step 6 covers the limited path).
- The main blockage is role/interest resistance (shop floor vs HQ, losers of automation) → `change-three-roles` is the specialized tool; this skill does not run org change (Procedure step 5 covers the limited path).

## Required inputs

- A named release (system, Agent, report, automation).
- Some signal of who was supposed to use it (even if only a guess to be corrected).

## Procedure

1. **Name target users and the natural rhythm.** Who should use this to finish real work? Daily ops, a close cycle, a quarterly decision? Adoption is: in that rhythm, without the project team prompting, pairing, or backfilling, they still use it as intended. Daily tools are not proven by a launch-week burst; month-end tools are not proven by daily logins.
2. **Ban vanity evidence.** Account count, training sign-in, UAT ticks, and people in the demo room do not count. Look at whether the real job still happens on the old workaround.
3. **Judge the state, not a forced classification:**
   - **Stable expected use** — the work keeps completing along the intended path in the natural rhythm without prompting, pairing, or backfill → adoption holds; no intervention needed.
   - **Evidence-backed blockage** — friction, trust, relevance, or organization, with evidence.
   - **Insufficient evidence** — cannot yet judge; keep the hypothesis and say what evidence would decide.
   Classify a blockage only when one is actually present. When evidence cannot pick a primary cause, keep it as a hypothesis; do not force an attribution.
4. **Automation changes the signals.** Automation may reduce logins, clicks, and manual operations; judge by whether the work keeps completing along the intended path, not by raw interaction counts. Designed-in human review is not project-team backfill; do not require all work to be unattended.
5. **Recommend the smallest adoption move matching the primary** (only when a blockage exists). Friction: recommend placing it in the surface they already use (sheet, mail, ticket, existing chat). Trust: identify the blocking error and that it should be fixed on the business's clock, not the sprint board. Relevance: recommend stopping coverage expansion; narrow to the job they already have. Organization: if `change-three-roles` is available, hand off to it; otherwise organize the evidence, identify the organization blocker and the smallest relevant stakeholder concern, and give limited suggestions within existing capability and authorization — do not stop merely because the skill is missing, and never fabricate the external skill or claim its specialized method. If the move needs code, config, integration, or workflow implementation → `task-router`. Business-only moves (training, rollout audience, owner, dropping a duplicate process) may be recommended; this skill does not run an implementation lifecycle.
6. **Quality vs adoption.** If they use it but call outputs wrong: if `eval-driven-quality` is available, hand off to it; otherwise identify that business-defined quality evaluation is needed and give limited suggestions within existing capability and authorization — do not stop merely because the skill is missing, and never fabricate the external skill or claim its specialized method. Do not "hotfix" a missing definition of good.
7. **Exit test.** When the project team stops chasing, does the job still run on this path in the next natural cycle? If usage still tracks the team's calendar, it is accompaniment, not adoption. Do not start a new feature to celebrate go-live.

## Stop conditions

- Stable expected use with supporting evidence and the applicable cycle → output and end; do not force an improvement action.
- Primary blockage located with evidence, and the smallest reasonable response identified. If engineering is needed, the handoff is `task-router`. If the primary is organization or model quality, hand off to `change-three-roles` / `eval-driven-quality` if available; otherwise report the specific blockage and give limited suggestions within existing capability and authorization — do not stop merely because the skill is missing, and never fabricate the external skill or claim its specialized method. Do not require that the move already be implemented.
- Evidence insufficient to judge → report what evidence would decide; do not force a classification.
- Evidence shows value never happened in the real business → stop calling this an adoption problem; name that finding. Do not require running other companions first.
- User asked only for a verdict on the effort → stop and tell them to call `evaluate` with the evidence you gathered (you still do not emit CONTINUE/IMPROVE/PIVOT/STOP).

## Output contract

Plain text:

- **Target users + rhythm.**
- **Evidence that counts / that does not.**
- **State:** stable expected use / evidence-backed blockage / insufficient evidence.
- **Primary blockage (only if one exists):** friction / trust / relevance / organization.
- **Smallest move recommended** (only if a blockage exists; business-only suggestion, or handoff to `task-router` / available external companion).
- **Exit test:** what would show the project team can stop pushing.

Do not create an adoption program registry. Do not expand to company-wide rollout as the default fix.

## Conceptual influences

Conceptual influence: post-deployment adoption and usage persistence concepts discussed in
FDE literature. This skill's procedure, blockage taxonomy, conditional handoffs, and runtime
contract were authored for Intent to Outcome Loop.
