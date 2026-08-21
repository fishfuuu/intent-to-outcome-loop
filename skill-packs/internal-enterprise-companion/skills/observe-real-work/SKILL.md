---
name: "observe-real-work"
description: "Use when a PRD, interview notes, IT/procurement restatement, or \"just start from the spec\" is about to become the work order, but nobody has watched the actual job. Follow one complete business cycle; capture actual actions, the data source people actually trust, key exceptions, and any workarounds if they exist. Do not use when the real work is already observed; when the need is Shape (problem vs solution form); for pure technical debugging; or to design a system/Agent. Triggers: 影子观察, 二手需求, PRD开工, 变通, workaround, 这事得问老王, translated requirements, follow the real work, job shadow, official process vs actual work. Use when the user runs /observe-real-work."
---

# Observe real work

## Purpose

When second-hand descriptions are not enough to see the real job, get first-line evidence:
actual actions, workarounds, trusted data, exceptions, and the person who knows why.

This skill does **not** decide what problem is worth solving, what form the solution should take,
or whether to invest. That is Shape / other skills.

## Use when

- The request is a PRD, 规格书, 访谈纪要, or a restated "we need a platform / Agent / dashboard".
- People say they would use a tool, but daily behavior may not match.
- Official flowcharts look complete, yet someone exports to Excel, keeps a private sheet, or says "问老王".
- IT, procurement, or a vendor translated the pain into a system request.

## Do not use when

- The real job has already been watched and written as who / when / which system / which action.
- Problem, outcome, or solution direction are not yet stable or contested → `shape`.
- Problem and solution direction are already stable, but complex business semantics, prototype behavior, or handoff rules need freezing → `discover-business-contract`.
- Pure technical debugging (auth, API, stack traces) with no workflow discovery.
- The user only wants a research-method lecture and will not contact front-line people.
- The system is already live and unused → `adopted-not-released`, not a new observation tour.

## Required inputs

- A proposed work order or restated demand (however rough).
- Access, or a path to access, at least one person who actually does the job (not only an IT liaison).

## Procedure

Depth follows evidence. Stop once a complete-enough cycle has been watched and the captures below are named.

1. **Name the hand-off chain.** Who originated the request, who restated it, who will actually do the work. If the front-line user is not at the end of the chain, treat "start from the spec" as high risk.
2. **Pick one complete business cycle, not a calendar day.** Walk through the most recent real instance of work ("带我走一遍最近一次真实发生的案例"), rather than asking how work is "usually" done. If needed, observe a second instance covering a material exception. Choose the smallest cycle that could expose a workaround *if one exists*: one reconciliation batch, one warehouse shift, one month-end close packet, one exception ticket. Sit beside the person who does it. Do not turn it into a structured interview.
3. **Watch actual work, not only the official map.** Record systems opened, copy-paste, private sheets, skipped steps, who they actually call. Treat each workaround as evidence of a mismatch, constraint, or local adaptation worth understanding. Do not assume the system is the root cause. Excel, copy-paste, or a human check is not by itself a system failure, and not a reason to build software or automate.
4. **Capture, named:**
   - actual actions in the cycle (whether they match the official flow or not);
   - the data source people actually trust (official vs private);
   - key exceptions or judgment points;
   - the person who knows why it is that way;
   - whether any *material* workaround or say-do gap exists — **none is a valid result**.
5. **If you must speak, ask what they are doing on a real item**, not "what system do you need". Do not probe for a defect that is not there.
6. **Preserve conflicts between observation and intended future.** When observed reality materially conflicts with an inherited requirement, prototype, SOP, policy, or stated workflow, preserve both versions and the evidence for the conflict. Do not silently decide that observed practice is the intended future behavior. Observation establishes what happens today; it does not by itself authorize what should happen tomorrow. If the conflict affects material future behavior, identify the authority who can decide intended future behavior, mark intended future behavior as unresolved, and let appropriate shaping or business contract work handle the disposition. This skill does not redesign future workflows or run change management.
7. **Hand back evidence only.** Do not invent a product, Agent, or architecture. Do not treat a workaround as a mandate to automate. If official data is distrusted, say so; do not help design a platform on the untrusted source.

## Stop conditions

- A complete-enough business cycle was watched: actual actions, trusted data source, key exceptions/judgment points, and whether any material workaround or say-do gap exists → output and stop. **No material deviation is a valid completion.** Do not invent a problem.
- Front-line work is unreachable and the spec is treated as the only truth → do **not** approve production implementation from that spec; you may still list what discovery would take. Do not pretend observation happened.
- Watching is forbidden (security) → switch to doing one real item together (one ticket, one recon). Remote interview alone is not a substitute.

## Output contract

Plain text, short:

- **Cycle watched:** which business cycle, with whom (role, not necessarily a legal name).
- **Actual actions:** what they did, briefly.
- **Trusted data source:** which artifact is believed, and whether it matches the official source.
- **Key exceptions / judgment points.**
- **Who knows why:** the knowledge holder for the real process.
- **Material workaround or deviation:** 1–5 if material, or **no material deviation**.
- **Observed vs intended conflict (if seen):** observed today vs stated/intended future, evidence for both, and decision authority (or unresolved).
- **Say vs do:** one mismatch if seen, else none.
- **Not claimed:** no solution form, no investment decision, no "system failed", no "ready to build".

Do not create files unless asked. Do not start a five-map diligence. Do not run a Shape brief inside this skill.

## Conceptual influences

Conceptual influence: direct workplace observation methods discussed in FDE literature.
This skill's procedure, business cycle definition, evidence boundaries, and runtime contract
were authored for Intent to Outcome Loop.
