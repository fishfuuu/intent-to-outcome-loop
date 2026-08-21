---
name: "bounded-validation"
description: "Use when an internal team is about to start (or is stuck in) a PoC, pilot, \"exploration\", or \"we'll see\" initiative and it may never end. Before anyone claims business value was validated, name who judges, what real evidence counts, when to judge again, and what result means continue, expand, adjust, or stop. Do not use for Shape, for Reviewed Change / Plan Review, or to design the implementation. Triggers: PoC, 试点, 探索, 持续推进中, 毕业标准, 样例数据, mock, 概念验证, no end date, who decides this worked. Use when the user runs /bounded-validation."
---

# Bounded validation

## Purpose

Make sure an exploration or PoC has an **end condition and a referee**. This skill does not
run engineering Plan Review, write a Change Contract, or design the system.

It prevents open-ended exploratory initiatives that lack an explicit claim, credible
evaluation criteria, and a designated referee.

## Use when

- Someone proposes a PoC, pilot, spike, or "explore AI for X" without saying how it ends.
- A pilot has been "ongoing" across reporting cycles with no number and no one who can call it.
- Mock, synthetic, or cherry-picked demo data is being treated as proof the business value is real.
- The first meeting wants "all scenarios company-wide" before any one path can be judged.

## Do not use when

- The question is still "what is the problem / is this form too heavy" → `shape`.
- The question is "is this worth any more investment" → `worth-building-now`.
- End conditions already exist, real-enough data is in reach, a business judge is named, and the live task is to run one real path → `smallest-real-deployment`.
- You need architecture, RED tests, or independent review → `reviewed-change`.
- Pure lab model bake-off with no business claim.

## Required inputs

- The proposed (or ongoing) exploration, however informal.
- Who currently talks as if they will decide.

## Procedure

Do not mint a gate, registry, or stage file. Write the answers in the conversation.

1. **Name the claim.** What business result would "this worked" mean, in one sentence, in the business's language — not "we deployed a model".
2. **Name the referee.** Who will look at evidence and say continue / expand / adjust / stop. An IT liaison who cannot use the result is not enough to *claim value*. If no referee yet, you may keep **discovery/feasibility**; you may not claim value validation.
3. **Name real-enough evidence.** What data or working item would count. Synthetic, mock, cherry-picked demo data, or data transformed so heavily that material business conditions disappear **cannot** prove business value. A representative sample of real business data **may** count when it preserves the conditions relevant to the claim (distribution, exceptions, joins, missingness, business judgment). Masked/desensitized data is not automatically invalid — judge whether enough of those conditions remain. Mock or synthetic data may help test an interface, workflow, or technical hypothesis, but cannot establish that real business data exists, is accessible, or is fit for the validation claim.
4. **Name the next judgment moment.** Pick the soonest time when the business's own rhythm could produce a credible signal (a few daily closes; one month-end; not "next year"). The calendar is a judgment aid, not a stage gate.
5. **Name four outcomes in advance:** continue, expand, adjust, stop — each tied to an observable result, not to "stakeholders felt good".
6. **Use risk signals to narrow, not to auto-reject.** Treat as reasons to shrink and to doubt: no business owner, look-but-don't-touch on real data, universe-scale first scope. Two signals mean raise suspicion and tighten 2–5; they do **not** by themselves equal "refuse everything". Evidence still decides.

## Stop conditions

- The five names above exist → output them; do not start a delivery program inside this skill.
- People want to call mock/demo a business-value pass → refuse that claim; discovery may continue.
- Nobody can judge results and nobody will look at real work items → you may list what discovery remains; you may not open a "value PoC".
- The user wants Plan Review, test RED, or a Change Contract → stop and point to `reviewed-change`.

## Output contract

Plain text:

- **Claim:** one business sentence.
- **Referee:** role who will judge.
- **Evidence that may count:** real enough vs explicitly "not yet, discovery only".
- **Next judgment moment:** when, and why that rhythm can falsify the claim.
- **Continue / expand / adjust / stop:** each as an observable result.
- **Open risks:** owner / data / scope — as suspicion, not as an automatic veto.

Do not create workflow state. Do not return Evaluate verdicts.

## Conceptual influences

Conceptual influence: graduation and bounding criteria for exploratory pilots discussed in
FDE literature. This skill's procedure, boundaries, evidence rules, and runtime contract
were authored for Intent to Outcome Loop.
