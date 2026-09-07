---
name: "worth-building-now"
description: "Use when a relatively clear internal problem exists and the question is whether it is worth further investment to validate or solve — not what the problem is, and not which product to build. Do not use for Shape (problem vs solution form), for engineering design, or after the team has already decided to run a bounded real-world validation. Triggers: 值不值得做, 要不要投入, 痛点是真的但值不值得开发, go/no-go, no business owner. Use when the user runs /worth-building-now."
---

# Worth building now

## Purpose

Given a problem that is already reasonably specific, decide whether it is worth spending more
internal resources to **validate or solve**. A pass means: worth a small change now (when the
basis is sufficient), or worth a real-world validation next — not approval of a system, Agent,
or dashboard, and not a claim that business value is proven.

Do **not** re-Shape the solution form. If the request is still a vague "build X", that is `shape`.

## Use when

- Someone asks "is this worth doing / worth a project / worth an Agent".
- The pain can be pointed at, but it is unclear whether it is worth the team's time.
- A business unit named a solution ("对账 Agent", "经营驾驶舱") and Shape already challenged the form, or the form is not the live question — the live question is investment.
- There is no person who will own the business result, and the team is about to schedule implementation.

## Do not use when

- Problem, outcome, and solution form are still unclear or contested → `shape`.
- The user's ask is only to obtain first-line work evidence (shadow, follow the job) → `observe-real-work`.
- Formal implementation or value-validation is already in flight with an owner and a way to judge results.
- Pure technical debugging, or the user only wants a definition of "PSF".

## Required inputs

- A problem statement that names (or can name) who is hurt and what they do today.
- Enough context to talk about impact and data reality; if that is missing, this skill may send the team back to observation, not to coding.

## Procedure

Check four lenses against what the user already provided; reuse stated facts directly and do not
mechanically re-ask them as questions. None requires CEO Top-5, "technically hard", a money
number, or a formal ROI model.

1. **Pain.** Can you name a person (role), a time/cycle, a system or artifact, and an observable action that hurts? Direction words ("赋能", "智能化", "全公司") fail this question. Simple, high-frequency pain still counts — "hard" is not a gate.
2. **Impact.** What happens if we do nothing for one planning cycle? Time, rework, error cost, delayed decisions, revenue, cost, risk, or experience are all valid. A rough magnitude is enough (size, frequency, who is hit). "The board wants AI" with no magnitude fails. Do **not** require customer-contract monetization.
3. **Feasibility.** Where is the data, who trusts it, what quality bar is acceptable (including "90% plus a human check")? Guessing in a meeting is not feasibility.
4. **Worthiness.** Evidence that pain, impact, and feasibility *exist* is not a pass. Compare the expected benefit against the total cost of implementing, validating, maintaining, coordinating, and exiting — considering only what is relevant. No mandatory ROI table; do not invent amounts. A real but tiny pain is not automatically **Not now**: if the total cost is also tiny, a small change may still be worth it; if the benefit is small relative to the cost or an already-sufficient workaround, it is **Not now**.

**Owner rule.** If nobody can be responsible for the business result or can judge the result, do **not** enter formal implementation or "we are validating business value". You **may** continue the smallest discovery to find the problem, the responsibility boundary, and a potential owner. Continuing investigation ≠ starting delivery.

The agent **recommends** from the evidence; the user or accountable business owner retains the material investment and priority decision. Do not require the user to rubber-stamp every sub-finding.

## Recommendation exits

- **Worth a small change** — facts and outcome basis are sufficient, risk is low, and total cost is small; recommend adopting the small change directly, without first building a PoC. This is a recommendation, not user authorization to execute, and it does not skip the relevant engineering verification or review.
- **Worth validating** — the direction is worth pursuing but a valuable uncertainty still needs resolving; recommend a bounded validation next.
- **Discovery only** — keep investigating owner/data/pain; do not schedule implementation or call it a value PoC.
- **Not now** — do not invest further now; say what would have to change (including "pain is real but too small / already handled").

## Stop conditions

- Pain, impact, and feasibility have evidence, worthiness holds, and someone can judge the result → recommend **Worth a small change** (basis sufficient, risk low, cost small) or **Worth validating** (a valuable uncertainty remains). Neither is "approved to build the named Agent" nor "evidence exists therefore do it".
- Pain, impact, and feasibility can be described, but benefit is too small vs total cost or an already-sufficient workaround → **Not now**.
- Pain still a slogan → stop; do not green-light implementation. Observation may still be appropriate.
- No owner for the result → block formal implementation and value-validation claims; allow listed discovery only.
- Data cannot be touched even for discovery, and quality bar is a slogan ("must be 99%") with no consequence if wrong → not worth validation yet.

## Output contract

Plain text:

- **Pain:** who / cycle / system / observable hurt — or "not specific yet".
- **Impact:** one magnitude in whatever unit is honest (hours, error rate, delay, risk) — or "cannot tell".
- **Feasibility:** data reality + acceptable quality bar — or "unknown".
- **Owner:** who can judge the result, or "none yet".
- **Verdict (exactly one):**
  - **Worth a small change** — basis sufficient, low risk, small total cost; recommend adopting it directly (not authorization to execute, no skipped verification).
  - **Worth validating** — impact justifies further validation effort; this is not solution approval and not an auto-charter.
  - **Discovery only** — keep investigating owner/data/pain; do not schedule implementation or call it a value PoC.
  - **Not now** — recommended: do not invest further now; say what would have to change.

Do not return Evaluate's CONTINUE / IMPROVE / PIVOT / STOP. Do not write an implementation plan. Do not pick the product form here.

## Conceptual influences

Conceptual influence: opportunity and feasibility screening concepts discussed in FDE literature.
This skill's procedure, worthiness criteria, owner boundaries, and runtime contract
were authored for Intent to Outcome Loop.
