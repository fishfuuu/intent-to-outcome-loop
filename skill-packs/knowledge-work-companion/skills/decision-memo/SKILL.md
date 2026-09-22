---
name: decision-memo
description: "Produce a decision memo that compresses a real decision into the minimum evidence, context, options, trade-offs, risks, and ask a human decision-maker needs to decide responsibly. Defaults to one page and expands only when compressing further would drop material evidence. The decision position may be RECOMMEND, DEFER, or ESCALATE. Use when you need a leader to make or ratify a decision asynchronously. Triggers: \"draft a decision memo\", \"we need a one-pager for X\", async approval, exec ratification."
---

Intentional fork of an upstream skill (`andreaswasita/copilot-cowork-dojo`,
`skills/decision-memo/SKILL.md`). Fork scope: the decision position, the
length rule, human agency, and pack-internal links. The memo structure and
its critical rules are upstream.

# Decision Memo

The format that turns 30-minute meetings into 5-minute approvals.

---

## Quick Reference (the structure)

| Section | Length | Purpose |
|---|---|---|
| Title | One line | Decision needed |
| TL;DR | ≤40 words | Position + why |
| Context | 2–4 sentences | Why now |
| Options | 3 max | Pros · cons · cost |
| Decision position | RECOMMEND / DEFER / ESCALATE | Which, and why |
| Risks & mitigations | 3 max | Top risks + mitigation |
| Ask | One line | What you need + by when |

## When to Use

- Async decision needed from an exec or sponsor.
- Decision worth recording (will be referenced later).
- Trade-off where options need to be visible before the choice.
- Also when the honest answer is "not enough evidence yet" or "this is not
  the author's call".

## How to Use

Standard structure:

```
TITLE — <decision needed>
TL;DR (≤40 words): position + why
Context: <2–4 sentences>
Options: <3 max, each with pros / cons / cost>
Decision position: RECOMMEND | DEFER | ESCALATE — <which, why>
Risks & mitigations: <3 max>
Ask: <what you need from the reader, by when>
```

**Default to one page.** Expand only when compressing further would omit
material evidence, trade-offs, risks, or constraints needed for the
decision. Keep the memo as small as the decision responsibly allows.

## Decision Position

Not every decision can responsibly end in a recommendation. Name one of
three positions:

- **RECOMMEND** — the evidence supports one option.
- **DEFER** — the evidence is insufficient for a responsible decision now.
  Say what is missing and what would close it.
- **ESCALATE** — the decision depends on authority, risk tolerance, policy,
  or constraints the author cannot resolve. Name who owns it.

These are positions *inside one memo*, not a project-wide lifecycle, stage,
or verdict taxonomy.

## Examples

| Don't: Memo failure | Do: Memo success |
|---|---|
| "Let me know your thoughts." | "Ask: approve option B by Fri 11/14 EOD." |
| Two options where one is a strawman | Three real options with honest trade-offs |
| Position buried after 3 pages | TL;DR on line 1; position in the TL;DR |
| Risks: "execution risk, market risk" | Risks: "vendor lock-in (mitigation: 2-year exit clause)" |
| A recommendation the evidence doesn't carry | "DEFER: option C's 3-year cost is unknown; Ask: vendor TCO by 11/20." |

## Critical Rules

- **Default to one page.** Expand only when compressing further would omit
  material evidence, trade-offs, risks, or constraints needed for the
  decision. Keep it as small as the decision responsibly allows.
- **The position is in the TL;DR.** Don't make the reader hunt, whether it
  is RECOMMEND, DEFER, or ESCALATE.
- **Three options max, all real.** Strawmen erode trust.
- **Ask is specific and timed.** "Approve by Friday EOD" beats "thoughts?"
- **Risks have mitigations.** Naked risks are noise.
- **The memo prepares a human decision.** It does not make the decision.
  Write it for the decision-maker; do not write it as though the author or
  the agent owns the business call.

## Common Pitfalls

- Two-option memos where one option is a strawman.
- Positions buried after three pages of context.
- "Let me know your thoughts" — non-ask.
- Risks listed without mitigations.
- Cost stated for one option but not others.
- Forcing a recommendation when the evidence only supports DEFER.
- Writing the memo as if the author, rather than the reader, decides.

## Anti-Patterns

- Two-option memos where one option is a strawman.
- Positions buried after three pages of context.
- "Let me know your thoughts." Specify the decision you need.
- A memo past one page without a material reason to expand.
- A recommendation manufactured to look decisive.

## Verify Before Sending

- [ ] As small as the decision responsibly allows.
- [ ] TL;DR carries the position.
- [ ] Up to three real options; each included option with pros / cons /
      cost.
- [ ] Risks have mitigations.
- [ ] Ask names the action and the by-when.
- [ ] Decision-maker named.
- [ ] Sources cited for cost / risk figures.
- [ ] The stated position is the one the evidence supports (RECOMMEND,
      DEFER, or ESCALATE), not a default recommendation.

## Related

Useful combinations, not a mandatory pipeline — each skill works standalone:

- `research-synthesis` — when the memo rests on multiple sources.
- `reviewing-output` — to review the memo before it goes out.
