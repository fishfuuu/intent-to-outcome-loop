# Companion Skills

## Principle

Core provides the change-delivery backbone: intent / outcome, boundary,
risk-proportionate change path, verification discipline, independent
review when needed, handoff, and evaluation. Companion Skills provide
specialist methods — how to debug, how to do TDD, how to review code
deeply, how to design UI, how to test browser behavior.

**Core decides how safely to deliver a change; Companion Skills provide
specialist depth when the task needs it.**

Companion Skills are recommendations, not dependencies. Core never
requires a specific third-party skill.

- Companions may come from any compatible third-party repository; you do
  not have to copy them into this repo.
- An already-installed skill that allows model invocation may be discovered
  and invoked by the host/agent through its own skill-discovery mechanism.
- User-invoked skills still require an explicit user call.
- Intent to Outcome Loop does not maintain third-party invocation policy.

## Engineering

For IT and formal software development.

**Recommended**

- **tdd** (Matt Pocock) — best for new behavior, bug fixes, regression
  protection, and test-first implementation. Core only requires
  verification/falsification to be effective; it does not provide a full
  TDD method.
- **diagnosing-bugs** (Matt Pocock) — best for hard-to-reproduce bugs,
  complex root cause, and performance regressions. Core has
  baseline/verification/stop discipline but not a complete systematic
  diagnosis method.
- **code-review** (Matt Pocock) — best for independent diff review.
  Reviewed Change decides when an independent review is needed; a
  professional code-review skill decides how to review.

**Optional**

- **improve-codebase-architecture** — proactive architecture / codebase health review.
- **browser / E2E testing** — when real browser behavior matters.
- **security review** — for security / auth / privacy / trust-boundary work.
- **performance profiling** — for performance regression / optimization.

Optional items are not tied to a specific repository unless this repo
already names a source.

## Prototype

For anyone building coded prototypes, including business managers,
product people, designers, and solo builders.

**Recommended**

- **frontend-design** (Anthropic) — best for establishing a clear visual
  direction, avoiding templated AI UI, and turning a product theme into a
  design language. Core does not provide specialist visual design.

**Optional**

- **ui-ux-pro-max** (UI UX Pro Max) — best for more systematic UX,
  design systems, palette, typography, charts, accessibility, and
  stack-specific guidance. frontend-design and ui-ux-pro-max complement
  each other: frontend-design is design direction / taste / visual point
  of view; ui-ux-pro-max is systematic UI/UX knowledge and design-system
  depth. Neither replaces the other.
- **browser / E2E testing** — verify a coded prototype's real interaction.
- **prototype** — when the goal is to quickly answer a design or
  technical question rather than go straight to production.
- **research** — when real external facts are unknown before prototyping.

## How to choose

- **Recommended** — high-frequency, general-purpose; worth installing long-term.
- **Optional** — add when a specific task comes up.
- **Discover** — when current capabilities are insufficient, prefer
  finding a mature skill through the host's skill-discovery / findskills
  tools over building your own immediately.

Start with the smallest useful combination.

## Third-party ownership

Third-party skills are maintained by their original authors. Check each
skill's latest version, invocation policy, and license. This repo does
not copy or redistribute third-party skill content. A recommendation is
not an endorsement, a compatibility guarantee, or a pinned dependency.
If a third-party skill renames or stops being maintained, Core is
unaffected.
