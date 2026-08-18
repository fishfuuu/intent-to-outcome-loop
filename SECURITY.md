# Security Policy

## Scope

Intent to Outcome Loop is a set of **delivery skills** for coding agents —
markdown instructions plus a small Python installer and validator. It is
not a runtime, a server, a daemon, or a web service. It does not store
user data, does not process secrets, and does not run continuously.

The security-relevant surface is therefore small:

- **`scripts/install.py`** — copies skill files into a host's skill
  directory. It writes only the skills it owns and never deletes
  unrelated skills in the target directory.
- **`scripts/validate.py`** — a read-only repository checker.
- **The skills themselves** — instructions that a coding agent follows.
  They can cause the agent to read, write, or run commands in the
  environment where the agent runs.

Because the skills are instructions executed by an agent, a malicious or
compromised skill is a real risk. Treat any skill you install as code you
are choosing to run.

## Reporting a vulnerability

Please **do not** open a public issue for a security vulnerability.

Report it privately via GitHub's **Security Advisories** for this
repository, or by emailing the maintainers directly. Include:

- the affected file(s) and version/commit,
- a description of the issue and its impact,
- a minimal reproduction if possible.

You should receive an acknowledgment within a few business days. We ask
that you give us a reasonable window to address the issue before
disclosing it publicly.

## What we consider in scope

- A skill that, when followed, causes an agent to perform an unintended
  destructive, exfiltrating, or privilege-escalating action.
- The installer writing outside its declared target, deleting unrelated
  skills, or following a path outside the repository.
- The validator being bypassable in a way that lets a malformed or
  malicious skill ship.
- Host-specific frontmatter injection that breaks a host's skill
  sandboxing (for example, defeating the `evaluate` user-only policy).

## What is out of scope

- The behavior of third-party hosts (Claude Code, Codex, OpenCode, Grok)
  and their own skill-loading and permission models.
- Security of a specific project that uses these skills. Permissions,
  security, and production rules for a project are set by that project,
  not by this repository.
- General agent-safety guarantees: these skills are guidance, not a
  sandbox. An agent's host is responsible for enforcing its own
  permissions.

## Supported versions

We recommend always using the latest commit on `main`. This project does
not maintain a long-term-support release line; fixes land on `main` and
are released as tags when warranted.
