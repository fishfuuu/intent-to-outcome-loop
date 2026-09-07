---
name: "smallest-real-deployment"
description: "Use when an internal team will try a change in the real business — not a demo — and needs one end-to-end value path, real-enough data, the shortest cycle that can credibly falsify the claim, and a business person actually using or judging it. Do not use for Reviewed vertical slices (engineering correctness), endless PoCs, or company-wide first releases. Triggers: 最小验证, 真实数据, 一条路径, 端到端, MVD, 样例验收, 全公司第一期, Excel already enough. Use when the user runs /smallest-real-deployment."
---

# Smallest real deployment

## Purpose

See whether **value actually happens** on this business path: real work, real-enough data,
one end-to-end slice of coverage (not a thin fake of every module), the earliest credible
falsification, and a business person operating or judging it.

This is not a Reviewed Change vertical slice. A slice there proves an engineering behavior
was implemented correctly. This skill proves a business result showed up — or designs the
trial that would show it.

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

1. **Decide the mode from the request and existing evidence:** design a trial path (not yet run) or evaluate an already-run path. Do not make the user pick a mode name; infer it from what they ask and what evidence already exists.
2. **Design mode — one path, full depth.** Cut coverage (one ticket type, one plant, one close packet), not value. An end-to-end path a business user can point to beats "every module at 30%".
3. **Design mode — real-enough data for the claim.** If you will say "this helped the close", you need close data the business trusts. Synthetic, mock, or cherry-picked demo data cannot pass this skill. A representative sample of real business data may count when it preserves the conditions relevant to the claim. Masked data is not automatically invalid.
4. **Design mode — shortest credible falsification, not a fixed week/month rule.** Use the business's own rhythm: daily recon may falsify in a few days; month-end may need one real close; seasonal replenishment may need its natural cycle. Do not stretch the trial to look complete. Do not crush a monthly job into five days and call it proof.
5. **Design output.** Name the path, the planned data, the business participants, the execution method, the cycle, and the observation & judgment conditions. State explicitly that the trial has **not been executed** — do not fill in "what the business person did" or "value appeared". A complete design satisfies a design request; you do not have to wait for the real business cycle to end to deliver it.
6. **Evaluate mode — business person does the thing.** When the path has run: the user of the path clicked, ran, or signed the result; demo to IT against a checklist is not the trial. Real items operated and real data used do not by themselves prove business value appeared — conclusion strength must match the evidence.
7. **Evaluate mode — compare to baseline.** State the relevant comparison to the baseline or current method, the evidence limits, and the next step. If a missing baseline or unresolved confounders prevent a reliable comparison, narrow the conclusion to what the evidence supports; report insufficient evidence for claims that cannot be judged, without fabricating a control (see step 11).
8. **Allow a small existing mechanism to win.** If a query, spreadsheet, or existing-screen tweak produces the result, record that as success of the *path*, not as failure to ship a product.
9. **Do not implement here.** If the path needs a script, SQL, page, API, config, integration, or automation, define the path in this skill, hand implementation to `task-router` / a change skill per the original authorization, then return to judge whether value happened. When the user only asked for trial design, do not auto-implement. Do not write code, run Plan Review, or run the Reviewed lifecycle in this skill.
10. **Reuse what bounded-validation already fixed.** If the claim, referee, and judgment conditions already exist, use them directly; do not re-ask and do not require running both skills in series.
11. **Decide in the open:** expand coverage, adjust the path, stop calling it valuable, or — when the evidence cannot yet judge value — report **insufficient evidence**: deliver the known facts, the key gaps, and the minimal evidence-completion suggestions, then end the current evaluation. Do not classify insufficient evidence as value-not-shown or mixed, do not auto-extend the trial, and do not execute the evidence completion. Do not silently extend into the next quarter.

## Stop conditions

- Design mode: the design names path, planned data, participants, execution method, cycle, and observation/judgment conditions → output the design and stop; do not claim value has appeared.
- Evaluate mode: the path ran on real-enough data, a business person judged it, and you can say expand / adjust / stop — or, when the evidence cannot yet judge value (e.g., the baseline is missing or important confounders remain), report **insufficient evidence** with the known facts, key gaps, and minimal evidence-completion suggestions, then end the current evaluation.
- Still on mock data while claiming business value → refuse the claim; point at `bounded-validation` if the trial has no end.
- Scope is still "the whole company" with no one path → do not schedule this trial.
- The work has become implementation (script, SQL, page, API, config, integration) → stop implementing; hand to `task-router`. This skill resumes only to judge whether value happened.

## Output contract

Plain text:

- **Mode:** design or evaluate.
- **Design:** path; planned data; business participants; execution method; cycle; observation & judgment conditions; **not yet executed**.
- **Evaluate:** path; data (what was real enough, what was not used as proof); rhythm; what the business person did; result (value showed up / did not / mixed / **insufficient evidence** — with the observable); comparison to baseline or current method; limits; next (expand coverage, adjust, stop, "Excel/SQL/existing change is enough", or the minimal evidence-completion suggestions when evidence is insufficient).

Do not implement. Do not write a Change Contract. Do not return Evaluate verdicts.

## Conceptual influences

Conceptual influence: focused end-to-end value deployment concepts discussed in FDE literature.
This skill's procedure, business-rhythm falsification, engineering handoff boundary, and
runtime contract were authored for Intent to Outcome Loop.
