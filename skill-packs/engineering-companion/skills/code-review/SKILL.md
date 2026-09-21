---
name: code-review
description: "Review the changes since a fixed point (commit, branch, tag, or merge-base) along two axes: Standards (does the code follow this repo's documented coding standards?) and Spec (does the code match what the originating issue/spec asked for?). Runs both reviews in parallel sub-agents and reports them side by side. Use when the user wants to review a branch, a PR, work-in-progress changes, or asks to \"review since X\"."
---

Derived from Matt Pocock's two-axis code-review design.
This standalone variant has no dependency on
`setup-matt-pocock-skills` or `docs/agents/issue-tracker.md`.

Two-axis review of the diff between `HEAD` and a fixed point the user supplies:

- **Standards**: does the code conform to this repo's documented coding standards?
- **Spec**: does the code faithfully implement the originating issue / spec?

Both axes run as **parallel sub-agents** so they don't pollute each other's context, then this skill aggregates their findings.

## Process

### 1. Pin the fixed point

Whatever the user said is the fixed point (a commit SHA, branch name, tag, `main`, `HEAD~5`, etc.). If they didn't specify one, ask for it.

Capture the diff command once: `git diff <fixed-point>...HEAD` (three-dot, so the comparison is against the merge-base). Also note the list of commits via `git log <fixed-point>..HEAD --oneline`.

Before going further, confirm the fixed point resolves (`git rev-parse <fixed-point>`) and the diff is non-empty. A bad ref or empty diff should fail here, not inside two parallel sub-agents.

### 2. Identify the spec source

Find the best available authoritative source of intended behavior, in this order:

1. **Explicit source supplied by the user or current task context**
   - spec path
   - Change Contract
   - acceptance criteria
   - issue / PR
   - task brief
   - other explicitly identified authoritative requirement source

2. **Relevant ITOL durable change record, when one clearly belongs to this change**
   - `.agent-delivery/changes/*/record.md`
   - Optional. This skill must not require Intent to Outcome Loop.
   - Use a record only when it clearly corresponds to the current change.

3. **Issue / PR references visible in commit messages**
   Examples: `#123`, `Closes #45`, GitLab `!67`.
   Resolve them using the repository's native available mechanism.
   - GitHub: if `gh` is available, use `gh issue view` / `gh pr view`. A bare `#42` may be issue or PR; resolve appropriately.
   - GitLab / another tracker: use an available native tool only when the repository clearly identifies that tracker. Do not invent setup/config.

4. **Repository spec/document source**
   Search relevant files under likely locations such as `docs/`, `specs/`, `.scratch/`, or documented requirements / design locations in the repo.
   Match using branch name, feature name, task name, changed subsystem, or explicit repository guidance.

5. **Ask once**
   If no authoritative spec source can be established, ask the user where the spec / intended behavior is.
   If the user says there is no spec:
   - skip the Spec sub-agent
   - report `no spec available`

Do **not** invent requirements from branch name alone, commit title alone, implementation code, tests alone, or inferred product intent. Those may help locate a source; they are not automatically the spec.

Missing Matt tracker config must not block this review.

### 3. Identify the standards sources

Find repository guidance that actually applies to the changed files, for example:

- `AGENTS.md`
- `CLAUDE.md`
- `CONTRIBUTING.md`
- `CODING_STANDARDS.md`
- relevant architecture guidance
- ADRs
- relevant DESIGN documents
- directory-local instructions
- language/framework-specific repo guidance

Keep the two-axis boundary. A document may contain both kinds of content; do not dump the whole file into both axes. Pass only the relevant parts to each reviewer.

**Standards axis** (conventions and implementation constraints):

- coding conventions
- layering constraints
- architecture rules
- ownership rules
- canonical helper/mechanism requirements
- naming/testing conventions
- implementation constraints

**Spec axis** (intended behavior):

- user-visible expected behavior
- business requirements
- acceptance criteria
- requested output
- explicit feature behavior

On top of whatever the repo documents, the Standards axis always carries the **smell baseline** below: a fixed set of Fowler code smells (_Refactoring_, ch.3) that applies even when a repo documents nothing. Two rules bind it:

- **The repo overrides.** A documented repo standard always wins; where it endorses something the baseline would flag, suppress the smell.
- **Always a judgement call.** Each smell is a labelled heuristic ("possible Feature Envy"), never a hard violation. Like any standard here, skip anything tooling already enforces.

Each smell reads *what it is* → *how to fix*; match it against the diff:

- **Mysterious Name**: a function, variable, or type whose name doesn't reveal what it does or holds. → rename it; if no honest name comes, the design's murky.
- **Duplicated Code**: the same logic shape appears in more than one hunk or file in the change. → extract the shared shape, call it from both.
- **Feature Envy**: a method that reaches into another object's data more than its own. → move the method onto the data it envies.
- **Data Clumps**: the same few fields or params keep travelling together (a type wanting to be born). → bundle them into one type, pass that.
- **Primitive Obsession**: a primitive or string standing in for a domain concept that deserves its own type. → give the concept its own small type.
- **Repeated Switches**: the same `switch`/`if`-cascade on the same type recurs across the change. → replace with polymorphism, or one map both sites share.
- **Shotgun Surgery**: one logical change forces scattered edits across many files in the diff. → gather what changes together into one module.
- **Divergent Change**: one file or module is edited for several unrelated reasons. → split so each module changes for one reason.
- **Speculative Generality**: abstraction, parameters, or hooks added for needs the spec doesn't have. → delete it; inline back until a real need shows.
- **Message Chains**: long `a.b().c().d()` navigation the caller shouldn't depend on. → hide the walk behind one method on the first object.
- **Middle Man**: a class or function that mostly just delegates onward. → cut it, call the real target direct.
- **Refused Bequest**: a subclass or implementer that ignores or overrides most of what it inherits. → drop the inheritance, use composition.

### 4. Spawn both sub-agents in parallel

**Standards sub-agent prompt** should include:

- The full diff command and commit list.
- The list of standards-source excerpts you found in step 3, **plus the smell baseline from step 3** pasted in full (the sub-agent has no other access to it).
- The brief: "Report, per file/hunk where relevant, (a) every place the diff violates a documented standard: cite the standard (file + the rule); and (b) any baseline smell you spot: name it and quote the hunk. Distinguish hard violations from judgement calls: documented-standard breaches can be hard, but baseline smells are always judgement calls, and a documented repo standard overrides the baseline. Skip anything tooling enforces. Under 400 words."

**Spec sub-agent prompt** should include:

- The diff command and commit list.
- The path or fetched contents of the spec.
- The brief: "Report: (a) requirements the spec asked for that are missing or partial; (b) behaviour in the diff that wasn't asked for (scope creep); (c) requirements that look implemented but where the implementation looks wrong. Quote the spec line for each finding. Under 400 words."

If the spec is missing, skip the Spec sub-agent and note this in the final report as `no spec available`.

### 5. Aggregate

Present the two reports under `## Standards` and `## Spec` headings, verbatim or lightly cleaned. Do **not** merge or rerank findings, because the two axes are deliberately separate (see _Why two axes_).

End with a one-line summary: total findings per axis, and the worst issue _within each axis_ (if any). Don't pick a single winner across axes: that's the reranking the separation exists to prevent.

## Why two axes

A change can pass one axis and fail the other:

- Code that follows every standard but implements the wrong thing → **Standards pass, Spec fail.**
- Code that does exactly what the issue asked but breaks the project's conventions → **Spec pass, Standards fail.**

Reporting them separately stops one axis from masking the other.
