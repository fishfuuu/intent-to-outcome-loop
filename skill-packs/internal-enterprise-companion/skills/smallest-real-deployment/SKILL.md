---
name: "smallest-real-deployment"
description: "Use when an internal team will try a change in the real business — not a demo — and needs one end-to-end value path, real-enough data, the shortest cycle that can credibly falsify the claim, and a business person actually using or judging it. Do not use for Reviewed vertical slices (engineering correctness), endless PoCs, or company-wide first releases. Triggers: 最小验证, 真实数据, 一条路径, 端到端, MVD, 样例验收, 全公司第一期, Excel already enough, earliest credible feedback. Use when the user runs /smallest-real-deployment."
---

# Smallest real deployment

## Purpose

See whether **value actually happens** on this business path: real work, real-enough data,
one end-to-end slice of coverage (not a thin fake of every module), the earliest credible
falsification, and a business person operating or judging it.

This is not a Reviewed Change vertical slice. A slice there proves an engineering behavior
was implemented correctly. This skill proves a business result showed up.

This skill **defines and judges** the real-business validation path; it does **not** implement
engineering changes.

The path may conclude that Excel, SQL, a script, or a small change to an existing system is
already enough. That is a finding about the path, not this skill building the thing.

## Use when

- The first release is being scoped as "all teams / all scenarios".
- Mock, synthetic, or cherry-picked demo data is about to be called a business success.
- A "minimum validation" is being planned as a multi-month everything-project.
- The team already believes the problem is worth a real try, and someone can judge results.

## Do not use when

- No business path can be named — only a slogan or a platform name → `shape`.
- The live question is an endless PoC with no referee ("持续推进中") → `bounded-validation`.
- The live question is schema, public API, or independent review of a diff → `reviewed-change`.
- Value already happened and the question is whether people still use it without being chased → `adopted-not-released`.
- Green-field with no business path (pure product MVP for a market).

## Required inputs

- One named business path (who does what, on which artifact).
- A way to reach data that the business actually uses, or an honest statement that this is still discovery not value-proof.

## Procedure

1. **One path, full depth.** Cut coverage (one ticket type, one plant, one close packet), not value. An end-to-end path a business user can point to beats "every module at 30%".
2. **Real-enough data for the claim.** If you will say "this helped the close", you need close data the business trusts. Synthetic, mock, or cherry-picked demo data cannot pass this skill. A representative sample of real business data may count when it preserves the conditions relevant to the claim. Masked data is not automatically invalid.
3. **Shortest credible falsification, not a fixed week/month rule.** Use the business's own rhythm:
   - daily recon may falsify in a few days;
   - month-end may need one real close;
   - seasonal replenishment may need its natural cycle.
   Do not stretch the trial to look complete. Do not crush a monthly job into five days and call it proof.
4. **Business person does the thing.** Demo to IT against a checklist is not the trial. The user of the path clicks, runs, or signs the result.
5. **Allow a small existing mechanism to win.** If a query, spreadsheet, or existing-screen tweak produces the result, record that as success of the *path*, not as failure to ship a product.
6. **Do not implement here.** If the path needs a script, SQL, page, API, config, integration, or automation, define the path in this skill, hand implementation to `task-router` / a change skill, then return to judge whether value happened. Do not write code, run Plan Review, or run the Reviewed lifecycle in this skill.
7. **Decide in the open:** expand coverage, adjust the path, or stop calling it valuable. Do not silently extend into the next quarter.

## Stop conditions

- The path ran on real-enough data, a business person judged it, and you can say expand / adjust / stop.
- Still on mock data while claiming business value → refuse the claim; point at `bounded-validation` if the trial has no end.
- Scope is still "the whole company" with no one path → do not schedule this trial.
- The work has become implementation (script, SQL, page, API, config, integration) → stop implementing; hand to `task-router`. This skill resumes only to judge whether value happened.

## Output contract

Plain text:

- **Path:** one sentence the business user would recognize.
- **Data:** what was real enough, what was not used as proof.
- **Rhythm:** why this length can falsify (not "because the project plan said so").
- **What the business person did.**
- **Result:** value showed up / did not / mixed — with the observable.
- **Next:** expand coverage, adjust, stop, or "Excel/SQL/existing change is enough".

Do not implement. Do not write a Change Contract. Do not return Evaluate verdicts.

## Conceptual influences

Conceptual influence: focused end-to-end value deployment concepts discussed in FDE literature.
This skill's procedure, business-rhythm falsification, engineering handoff boundary, and
runtime contract were authored for Intent to Outcome Loop.
