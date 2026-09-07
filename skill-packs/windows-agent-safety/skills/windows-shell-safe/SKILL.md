---
name: "windows-shell-safe"
description: "Read-only diagnostic for Windows shell commands. Returns a deterministic, machine-verifiable JSON risk readout; never executes, never launches a shell, never writes files or registry, and never grants execution authority. Use before destructive or high-impact operations, complex quoting or arguments, cross-shell commands, uncertain path or execution environments, or when the user asks for a command diagnosis — not for ordinary, clearly safe read-only commands."
---

# windows-shell-safe

## Purpose

Analyze a Windows shell command or structured subprocess invocation and
return a deterministic, machine-verifiable JSON risk readout. The analyzer
**never executes the command, never launches a shell, never writes files,
never touches the registry, and never grants execution authority.**

## Use when

- Destructive or high-impact operations: delete commands, registry, elevation, download/install, recursive or wide-scope targets.
- Complex quoting or arguments — nested quotes, expansion, or secrets whose shell interpretation is not obvious.
- Cross-shell commands (CMD / PowerShell / Git Bash / WSL mix) or uncertain path / execution environments (PowerShell edition, executable resolution, target existence and reparse status).
- The user explicitly asks for a command risk diagnosis.

## Do not use when

- Ordinary, unambiguous read-only commands — running on Windows alone is not a trigger.
- The command is already running or done; there is nothing to analyze.
- You need the command to be executed or authorized. This skill never does either.

## Required inputs

- The command text, and a shell family if known:
  `WINDOWS_POWERSHELL_5_1`, `POWERSHELL_7_PLUS`, `CMD`, `GIT_BASH`, `WSL`,
  `WINDOWSAPPS_STUB`, `PYTHON_SUBPROCESS`, or `UNKNOWN`.
- For destructive operations: working directory, allowed root, target, and
  recursive-preview / identity evidence. Missing evidence is reported as a
  STOP finding, never silently passed.

## How to run

```text
python windows_shell_safe.py [--input <file.json>] [--context <file.json>]
```

- Payload JSON on stdin (or `--input`); result JSON on stdout. The tool is
  read-only and never writes a file.
- `--context` (or `payload.context` / `payload.context_file`) accepts the
  output of `collect_windows_context.ps1`. The analyzer consumes it to
  confirm shell identity, executable resolution, and target identity.

## Output contract

Every result contains, in this order: `shell_family`, `shell_executable`,
`shell_version`, `host_process`, `execution_mode`, `detection_confidence`,
`command_classification`, `risk_level`, `findings`, `target_identity`,
`recursive_preview_status`, `safe_command_form`, `equivalence_level`,
`execution_authorized`, `stop_reasons`.

- `execution_authorized` is always `"NO"`.
- `findings` are registry-ordered; `stop_reasons` lists every STOP finding.
- Serialization is canonical: UTF-8, LF, no BOM, sorted keys, compact
  separators. Same input in, byte-identical JSON out.
- Secrets and machine-specific path roots are redacted on every surface.

## Fail-closed rules

- Malformed input or unknown enums: exit 2, no analysis output.
- Unconfirmable shell, path, identity, or recursive scope: an explicit
  `UNKNOWN` / STOP finding, never a silent PASS.
- Destructive and high-impact operations (delete commands, registry,
  elevation, download/install) are auto-detected from the command text; the
  caller does not need to pass a destructive flag.
- Any destructive operation missing required evidence (confirmed shell,
  target containment, target identity): STOP. A caller-supplied target
  string alone is never treated as proof the target is safe.
- `safe_command_form` is a diagnostic suggestion only. A clean `safe_form`
  is not authorization; a withheld form means do not run.

## Safety rules for the agent

- Treat results as diagnostics only. Never treat a result as permission to
  execute.
- If the tool reports a STOP finding, do not run the analyzed command.
- Never modify, stage, commit, or call the network based on the tool output.
- Never paste raw commands containing credentials into other tools.

## Stop conditions

- A STOP finding is present: report it and stop.
- The shell, target, or recursive scope cannot be confirmed: report
  `UNKNOWN`/STOP and stop.
- The user redirects or the command changes: re-analyze before proceeding.
