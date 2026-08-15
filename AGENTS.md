# Contributing to Coding Agent Delivery

This repository is kept deliberately small. The rules below are for
anyone changing it.

## Keep it light

- Seven skills, one installer, one validator. Do not add a state
  machine, a task board, a daemon, a database, a web UI, or an MCP
  server.
- Python standard library only for `install.py` and `validate.py`. No
  third-party dependencies, no package manager, no build system.
- No abstractions for "things we might need later." Add structure only
  when the existing tests cannot reliably check something with simple
  code.

## Skills

- Each `SKILL.md` uses the shared structure: YAML frontmatter, Purpose,
  Use when, Do not use when, Required inputs, Procedure, Stop
  conditions, Output contract, and an example when it genuinely helps.
- Canonical `SKILL.md` frontmatter uses only `name` and `description`.
  Never put host-specific keys (for example `disable-model-invocation`)
  in the canonical file — those are added to the installed copy by
  `install.py`.
- No machine-specific absolute paths anywhere in shipped markdown. This
  includes drive-letter paths, home-directory paths, and any path tied to
  a developer's machine or to another repository on the same machine.
  Use repo-relative paths or host-neutral placeholders instead.
- Line budget: ~120 lines per skill (reviewed-change may go to ~160),
  ~650 lines total across all seven. The validator enforces the total.

## After a change

Run, and make sure all pass:

```bash
python scripts/validate.py
python -m unittest discover -s tests -v
python scripts/install.py --target codex --scope user --dry-run
python scripts/install.py --target claude --scope user --dry-run
python scripts/install.py --target both --destination <tmpdir>
```

CI runs `validate` and `unittest` on Windows and Ubuntu.

## Tests

- Use temporary directories. Never write to a real `~/.agents`,
  `~/.claude`, or any old workflow directory.
- `install.py` and `validate.py` are exercised by the tests; keep them
  readable as small scripts.

## This repo is not maintained by its own skills

You do not need to run `shape`, `task-router`, or any change skill to
maintain this repository. The skills are the product. Use judgment and
the commands above.