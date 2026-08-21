---
name: "adopted-not-released"
description: "Use when something is \"live\", UAT-signed, or checklist-green, but it may not be part of real work: idle official tool, shadow Excel/ChatGPT, or usage that exists only while the project team is still chasing people. Adoption means target users, in the business's own rhythm, still complete the real job as intended without ongoing prompting, pairing, or human backfill. Do not use as Evaluate (no CONTINUE/PIVOT/STOP). A live unused system starts here; do not require other companions first. Use when the user runs /adopted-not-released. Triggers: 上线没人用, UAT过了, 验收, 影子Excel, 伴舞, adoption, go-live vs daily work, 项目组一走就停."
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
- The main complaint is model quality / "answers look amateur" → use original `eval-driven-quality`; do not invent an eval framework here.
- The main blockage is role/interest resistance (shop floor vs HQ, losers of automation) → use original `change-three-roles`; do not rewrite org-change here.

## Required inputs

- A named release (system, Agent, report, automation).
- Some signal of who was supposed to use it (even if only a guess to be corrected).

## Procedure

1. **Name target users and the natural rhythm.** Who should use this to finish real work? Daily ops, a close cycle, a quarterly decision? Adoption is: in that rhythm, without the project team prompting, pairing, or backfilling, they still use it as intended. Daily tools are not proven by a launch-week burst; month-end tools are not proven by daily logins.
2. **Ban vanity evidence.** Account count, training sign-in, UAT ticks, and people in the demo room do not count. Look at whether the real job still happens on the old workaround.
3. **Classify the blockage (pick a primary):**
   - **Friction** — extra login, extra step, blank first screen.
   - **Trust** — one bad output and the story spread; fixes take weeks.
   - **Relevance** — not their job; HQ toy.
   - **Organization** — missing champion, shop-floor veto, people designed as losers.
4. **Recommend the smallest adoption move matching the primary.** Friction: recommend placing it in the surface they already use (sheet, mail, ticket, existing chat). Trust: identify the blocking error and that it should be fixed on the business's clock, not the sprint board. Relevance: recommend stopping coverage expansion; narrow to the job they already have. Organization: if `change-three-roles` is available, hand off to it; otherwise report the confirmed organization blocker, identify the smallest relevant stakeholder concern, and stop without fabricating the external skill. If the move needs code, config, integration, or workflow implementation → `task-router`. Business-only moves (training, rollout audience, owner, dropping a duplicate process) may be recommended; this skill does not run an implementation lifecycle.
5. **Quality vs adoption.** If they use it but call outputs wrong: if `eval-driven-quality` is available, hand off to it; otherwise identify that business-defined quality evaluation is needed and stop without fabricating the external skill. Do not "hotfix" a missing definition of good.
6. **Exit test.** When the project team stops chasing, does the job still run on this path in the next natural cycle? If usage still tracks the team's calendar, it is accompaniment, not adoption. Do not start a new feature to celebrate go-live.

## Stop conditions

- Primary blockage located with evidence, and the smallest reasonable response identified. If engineering is needed, the handoff is `task-router`. If the primary is organization or model quality, hand off to `change-three-roles` / `eval-driven-quality` if available; otherwise report the specific organizational or evaluation blockage and stop. Do not require that the move already be implemented.
- Evidence shows value never happened in the real business → stop calling this an adoption problem; name that finding. Do not require running other companions first.
- User asked only for a verdict on the effort → stop and tell them to call `evaluate` with the evidence you gathered (you still do not emit CONTINUE/IMPROVE/PIVOT/STOP).

## Output contract

Plain text:

- **Target users + rhythm.**
- **Evidence that counts / that does not.**
- **Primary blockage:** friction / trust / relevance / organization.
- **Smallest move recommended** (business-only suggestion, or handoff to `task-router` / available external companion).
- **Exit test:** what would show the project team can stop pushing.

Do not create an adoption program registry. Do not expand to company-wide rollout as the default fix.

## Conceptual influences

Conceptual influence: post-deployment adoption and usage persistence concepts discussed in
FDE literature. This skill's procedure, blockage taxonomy, conditional handoffs, and runtime
contract were authored for Intent to Outcome Loop.
