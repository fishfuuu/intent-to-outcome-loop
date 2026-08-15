"""windows-shell-safe -- read-only Windows shell command diagnostics.

This module NEVER executes the analyzed command, never launches a shell,
never mutates the filesystem/registry, never calls the network, and never
grants execution authority. It imports no subprocess/os execution surfaces.

The canonical SKILL.md is the single source of truth for this skill; this
script is the deterministic analyzer behind it. It can consume the JSON
evidence produced by collect_windows_context.ps1 (via a ``context`` dict or
a ``context_file`` path) to confirm shell identity, executable resolution,
and target identity -- and it fails closed when that evidence is missing
for a destructive operation.
"""

from __future__ import annotations

import hashlib
import json
import ntpath
import re
import sys
from pathlib import Path
from typing import Any


# ---------------------------------------------------------------------------
# Normative registries (kept in sync with the acceptance tests).
# ---------------------------------------------------------------------------

FINDING_REGISTRY_ORDER = [
    "DIALECT_COMMAND_MISMATCH",
    "OPERATOR_UNSUPPORTED_BY_VERSION",
    "EXECUTABLE_NOT_FOUND",
    "WINDOWSAPPS_STUB_DETECTED",
    "SHELL_EVIDENCE_CONFLICT",
    "SHELL_DETECTION_CONFIDENCE_LOW",
    "COMMAND_IDENTITY_AMBIGUOUS",
    "DYNAMIC_COMMAND_IDENTITY",
    "UNTERMINATED_QUOTE",
    "ARGUMENT_BOUNDARY_EQUIVALENCE_NOT_PROVEN",
    "SENSITIVE_VALUE_REDACTED",
    "DESTRUCTIVE_CONTEXT_INCOMPLETE",
    "TARGET_OUTSIDE_ALLOWED_ROOT",
    "PROTECTED_ROOT_TARGET",
    "REPARSE_POINT_DESTRUCTIVE_TARGET",
    "TARGET_IDENTITY_UNAVAILABLE",
    "UNSUPPORTED_FILESYSTEM_PREVIEW",
    "RECURSIVE_PREVIEW_INCOMPLETE",
    "TARGET_CHANGED_DURING_PREVIEW",
    "DUPLICATE_INVENTORY_ENTRY",
    "NESTED_REINTERPRETATION_RISK",
    "SAFE_FORM_NOT_AVAILABLE",
    "SEMANTIC_EQUIVALENCE_NOT_PROVEN",
    "SENSITIVE_OUTPUT_SUPPRESSED",
    "UNKNOWN_SYNTAX",
    "BASH_BUILTIN_IN_POWERSHELL",
    "BASH_HEREDOC_IN_NON_BASH_SHELL",
    "POWERSHELL_COLON_VARIABLE_AMBIGUITY",
    "NESTED_QUOTES_NATIVE_ARGV",
    "TARGET_NOT_FOUND",
    "TARGET_EVIDENCE_MISMATCH",
    "TARGET_COMMAND_BINDING_UNPROVEN",
    "REGISTRY_OPERATION",
    "PRIVILEGE_ELEVATION_OPERATION",
    "NETWORK_DOWNLOAD_INSTALL_OPERATION",
    "OPAQUE_EXECUTOR_PAYLOAD",
]

FINDING_REGISTRY_INDEX = {code: i for i, code in enumerate(FINDING_REGISTRY_ORDER)}

# Default severity / affected element / remediation per finding.
_FINDING_DEFAULTS = {
    "DIALECT_COMMAND_MISMATCH": ("HIGH", "command token/shell", "use syntax valid for the shell"),
    "OPERATOR_UNSUPPORTED_BY_VERSION": ("HIGH", "operator/version", "use version-supported syntax"),
    "EXECUTABLE_NOT_FOUND": ("STOP", "executable identity", "supply confirmed identity; do not execute"),
    "WINDOWSAPPS_STUB_DETECTED": ("HIGH", "executable resolution", "identify real shell without launching stub"),
    "SHELL_EVIDENCE_CONFLICT": ("STOP", "shell metadata", "resolve conflicting evidence"),
    "SHELL_DETECTION_CONFIDENCE_LOW": ("HIGH", "shell metadata", "provide reliable read-only context"),
    "COMMAND_IDENTITY_AMBIGUOUS": ("STOP", "command identity", "bind cmdlet/function/alias/native identity"),
    "DYNAMIC_COMMAND_IDENTITY": ("STOP", "dynamic invocation", "analyze a static invocation"),
    "UNTERMINATED_QUOTE": ("STOP", "token boundary", "close the quote and reanalyze"),
    "ARGUMENT_BOUNDARY_EQUIVALENCE_NOT_PROVEN": (
        "HIGH", "argv boundary", "provide static executable/argv evidence"),
    "SENSITIVE_VALUE_REDACTED": ("HIGH", "sensitive value", "remove secret from diagnostic input"),
    "DESTRUCTIVE_CONTEXT_INCOMPLETE": (
        "STOP", "destructive context", "supply cwd, allowed root, target, operation"),
    "TARGET_OUTSIDE_ALLOWED_ROOT": ("STOP", "target containment", "choose target inside explicit root"),
    "PROTECTED_ROOT_TARGET": ("STOP", "protected root", "do not target drive/share/profile root"),
    "REPARSE_POINT_DESTRUCTIVE_TARGET": (
        "STOP", "target identity", "stop; do not follow reparse point"),
    "TARGET_IDENTITY_UNAVAILABLE": ("STOP", "target identity", "obtain handle identity or stop"),
    "UNSUPPORTED_FILESYSTEM_PREVIEW": (
        "STOP", "filesystem model", "do not preview POSIX target in v1"),
    "RECURSIVE_PREVIEW_INCOMPLETE": (
        "STOP", "recursive inventory", "stop and report incomplete observation"),
    "TARGET_CHANGED_DURING_PREVIEW": (
        "STOP", "identity/inventory", "discard preview and reanalyze"),
    "DUPLICATE_INVENTORY_ENTRY": (
        "STOP", "inventory record", "discard conflicting inventory and reanalyze"),
    "NESTED_REINTERPRETATION_RISK": ("HIGH", "shell boundary", "make each boundary explicit"),
    "SAFE_FORM_NOT_AVAILABLE": ("HIGH", "recommendation", "do not emit a command form"),
    "SEMANTIC_EQUIVALENCE_NOT_PROVEN": (
        "HIGH", "semantic equivalence", "claim only bounded level"),
    "SENSITIVE_OUTPUT_SUPPRESSED": (
        "HIGH", "report rendering", "retain redaction and suppress output"),
    "UNKNOWN_SYNTAX": ("STOP", "lexer boundary", "provide analyzable input"),
    "BASH_BUILTIN_IN_POWERSHELL": ("HIGH", "shell builtin/shell", "use PowerShell syntax"),
    "BASH_HEREDOC_IN_NON_BASH_SHELL": (
        "HIGH", "command token/shell", "heredocs are not valid in this shell; rewrite without <<"),
    "POWERSHELL_COLON_VARIABLE_AMBIGUITY": (
        "HIGH", "token boundary", "write ${name}: to bind the colon literally"),
    "NESTED_QUOTES_NATIVE_ARGV": (
        "HIGH", "native argv boundary", "do not pass backslash-escaped quotes to a native CLI"),
    "TARGET_NOT_FOUND": ("STOP", "target identity", "the destructive target does not exist; stop"),
    "TARGET_EVIDENCE_MISMATCH": (
        "STOP", "target binding", "command operand and target evidence disagree; stop"),
    "TARGET_COMMAND_BINDING_UNPROVEN": (
        "STOP", "target binding", "command operand could not be proven to match the target evidence"),
    "REGISTRY_OPERATION": (
        "HIGH", "registry state", "do not modify the registry without explicit operator approval"),
    "PRIVILEGE_ELEVATION_OPERATION": (
        "HIGH", "privilege boundary", "do not elevate without explicit operator approval"),
    "NETWORK_DOWNLOAD_INSTALL_OPERATION": (
        "HIGH", "network/download", "do not download or install without explicit operator approval"),
    "OPAQUE_EXECUTOR_PAYLOAD": (
        "STOP", "executor payload", "the nested shell payload is opaque and cannot be inspected; stop"),
}

SEVERITY_ORDER = {"LOW": 0, "MEDIUM": 1, "HIGH": 2, "STOP": 3}

SHELL_FAMILIES = {
    "WINDOWS_POWERSHELL_5_1",
    "POWERSHELL_7_PLUS",
    "CMD",
    "GIT_BASH",
    "WSL",
    "WINDOWSAPPS_STUB",
    "PYTHON_SUBPROCESS",
    "UNKNOWN",
}

# PowerShell-ish families where PowerShell-specific quoting/variable rules
# apply to the analyzed text.
PS_FAMILIES = {"WINDOWS_POWERSHELL_5_1", "POWERSHELL_7_PLUS", "WINDOWSAPPS_STUB"}

# PowerShell host families: only these are confirmed or contradicted by the
# collector's own PowerShell environment evidence. A declared Git Bash, CMD,
# WSL, or Python-subprocess shell is the command's shell, not the collector's
# host, so its environment must not be read as a contradiction.
_POWERSHELL_HOST_FAMILIES = {"WINDOWS_POWERSHELL_5_1", "POWERSHELL_7_PLUS"}

CONFIDENCE_VALUES = {"CONFIRMED", "HIGH", "MEDIUM", "LOW", "CONFLICTED", "UNKNOWN"}
EXECUTION_MODES = {"DIRECT", "INTERACTIVE", "SCRIPT", "SUBPROCESS", "NESTED", "UNKNOWN"}
PREVIEW_STATUSES = {"OBSERVED_COMPLETE", "INCOMPLETE", "NOT_APPLICABLE"}
EQUIVALENCE_VALUES = {"ARGUMENT_BOUNDARY_EQUIVALENT", "FULL_SEMANTIC_EQUIVALENCE_NOT_PROVEN"}

_POWERSHELL_CMDLETS = {
    "get-childitem", "remove-item", "get-item", "write-output", "invoke-webrequest",
    "invoke-restmethod", "set-item", "copy-item", "move-item", "new-item",
    "get-content", "set-content", "start-process", "test-path", "foreach-object",
    "invoke-expression", "clear-item",
}

_BASH_BUILTINS = {"export", "source", "unset", "declare", "typeset", "shopt"}

# Commands that resolve in PowerShell, CMD, and Bash alike; treating them as
# unresolved would be a false EXECUTABLE_NOT_FOUND on every host.
_COMMON_BUILTINS = {
    "echo", "cd", "dir", "type", "del", "rm", "grep",
    "cat", "ls", "cp", "mv", "pwd", "mkdir", "pushd", "popd", "cls",
}

_KNOWN_EXTERNAL_TOOLS = {
    "curl", "wget", "winget", "ssh", "scp", "git",
    "reg", "choco", "scoop", "pip", "npm",
}

# Command words that delete or destructively mutate filesystem state.
_DESTRUCTIVE_FS_TOKENS = {
    "remove-item", "remove-childitem", "remove-itemproperty",
    "clear-content", "clear-item", "del", "erase", "rmdir", "rd", "rm",
}

# High-impact findings that withhold safe_command_form.
_HIGH_IMPACT_CODES = {
    "REGISTRY_OPERATION",
    "PRIVILEGE_ELEVATION_OPERATION",
    "NETWORK_DOWNLOAD_INSTALL_OPERATION",
}

_SECRET_PATTERNS = [
    re.compile(r"(?i)(authorization\s*:\s*bearer\s+)([^\s\"']+)"),
    re.compile(r"(?i)(api[_-]?key\s*[=:]\s*)([^\s,;\"']+)"),
    re.compile(r"(?i)(token\s*[=:]\s*)([^\s,;\"']+)"),
    re.compile(r"(?i)(password\s*[=:]\s*)([^\s,;\"']+)"),
    re.compile(r"(?i)(postgres(?:ql)?://[^:\s]+:)([^@\s]+)(@)"),
    re.compile(r"(sk-[A-Za-z0-9_\-]{4,}|ghp_[A-Za-z0-9]{8,}|github_pat_[A-Za-z0-9_\-]{8,})"),
    re.compile(r"SYNTHETIC_[A-Z0-9_]+"),
]

# Machine-specific path roots are normalized to placeholders in any output.
_MACHINE_PATH_PATTERNS = [
    (re.compile(r"(?i)(C:\\Users\\)[^\\\s\"']+"), r"\1<USER>"),
    (re.compile(r"(?i)(D:\\agent-workflow)"), "<OTHER_REPO>"),
    (re.compile(r"(?i)(/Users/)[A-Za-z0-9_.-]+"), r"\1<USER>"),
    (re.compile(r"(?i)(/home/)[A-Za-z0-9_.-]+"), r"\1<USER>"),
]

_DYNAMIC_RE = re.compile(r"\$\{?[A-Za-z_][A-Za-z0-9_]*\}?|%[A-Za-z_][A-Za-z0-9_]*%")
_GLOB_RE = re.compile(r"[*?\[\]]")
_REDIRECT_RE = re.compile(r"(?<!\w)[<>]|>>|2>|1>")
_PIPE_RE = re.compile(r"(?<!\w)\|(?!\|)")

# PowerShell `$name:` where the colon is token-final or followed by a
# non-name character. `$env:PATH` (name after colon) and `${name}:` (safe
# form) and bare `HEAD:path` (no `$`) do not match.
_COLON_VARIABLE_RE = re.compile(r"\$([A-Za-z_][A-Za-z0-9_]*):(?![A-Za-z0-9_{])")
# Backslash-escaped quotes are not a PowerShell escape; they break native
# argv boundaries when passed to a native CLI.
_NESTED_QUOTE_RE = re.compile(r'\\"')


def _finding(code: str, token_range: Any, evidence: str) -> dict[str, Any]:
    severity, affected, remediation = _FINDING_DEFAULTS[code]
    return {
        "code": code,
        "severity": severity,
        "token_range": token_range,
        "evidence": evidence,
        "affected_semantic_element": affected,
        "remediation": remediation,
    }


def _sanitize_machine_paths(text: str) -> str:
    """Replace machine-specific path roots with placeholders."""
    if not isinstance(text, str):
        return text
    out = text
    for pattern, repl in _MACHINE_PATH_PATTERNS:
        out = pattern.sub(repl, out)
    return out


def _redact(text: str) -> str:
    """Replace secret-like and machine-specific material; never reveals raw values."""
    if not isinstance(text, str):
        return text
    out = text
    for pattern in _SECRET_PATTERNS:
        out = pattern.sub(
            lambda m: m.group(1) + "[REDACTED]" if m.lastindex and m.lastindex > 1 and m.group(1) else "[REDACTED]",
            out,
        )
    return _sanitize_machine_paths(out)


def _redact_tree(value: Any) -> Any:
    if isinstance(value, str):
        return _redact(value)
    if isinstance(value, list):
        return [_redact_tree(v) for v in value]
    if isinstance(value, dict):
        return {k: _redact_tree(v) for k, v in value.items()}
    return value


def _is_posix_rm_recursive(command: str) -> bool:
    """True when static text shows recursive POSIX ``rm`` intent.

    Shared detector for DESTRUCTIVE secondary classification and recursive
    preview path. Pure; never executes. Recognizes:
    - short clusters containing r/R (e.g. -r, -rf, -fr, -rfi, -Rf)
    - split short options either order among argv-like tokens after rm
    - long option --recursive
    Non-recursive ``rm`` / ``rm -f path`` returns False.
    """
    if not isinstance(command, str) or not command:
        return False
    # Lightweight token split; shell operators terminate an rm argv region.
    tokens = re.findall(r"[^\s]+", command)
    n = len(tokens)
    i = 0
    while i < n:
        tok = tokens[i]
        base = tok.replace("\\", "/").rsplit("/", 1)[-1]
        if base == "rm":
            j = i + 1
            while j < n:
                opt = tokens[j]
                if opt in ("|", "||", "&&", ";", "&", "(", ")") or opt[:1] in ("|", ";", "&"):
                    break
                if opt == "--":
                    break
                if opt.startswith("--"):
                    name = opt.split("=", 1)[0]
                    if name == "--recursive":
                        return True
                    j += 1
                    continue
                if opt.startswith("-") and len(opt) > 1 and not opt.startswith("--"):
                    # Short-option cluster: any r/R letter means recursive.
                    if re.search(r"[rR]", opt[1:]):
                        return True
                    j += 1
                    continue
                # Operand / path -- GNU rm may still accept later options.
                j += 1
        i += 1
    return False


def _first_command_token(command: str) -> tuple[str, bool]:
    """Return (first command-position token, whether it appeared in a string)."""
    token = ""
    in_string = False
    quote_char = ""
    i = 0
    n = len(command)
    while i < n:
        ch = command[i]
        if in_string:
            if ch == quote_char:
                if i + 1 < n and command[i + 1] == ch:
                    i += 2
                    continue
                in_string = False
            i += 1
            continue
        if ch in ("'", '"'):
            in_string = True
            quote_char = ch
            i += 1
            continue
        if ch.isspace():
            if token:
                break
            i += 1
            continue
        if ch in ("|", ">", "<", "&", ";", "(", ")"):
            if token:
                break
            i += 1
            continue
        token += ch
        i += 1
    return token.lower(), False


def _quote_state(command: str) -> tuple[bool, str]:
    """Return (unterminated, quote_char)."""
    in_single = False
    in_double = False
    i = 0
    n = len(command)
    while i < n:
        ch = command[i]
        if ch == "\\" and i + 1 < n:
            i += 2
            continue
        if ch == "'" and not in_double:
            in_single = not in_single
        elif ch == '"' and not in_single:
            in_double = not in_double
        i += 1
    if in_single:
        return True, "'"
    if in_double:
        return True, '"'
    return False, ""


def _has_unquoted(text: str, needle: str) -> bool:
    """True when ``needle`` appears outside single/double quotes."""
    in_single = False
    in_double = False
    i = 0
    n = len(text)
    while i < n:
        ch = text[i]
        if ch == "\\" and i + 1 < n:
            i += 2
            continue
        if ch == "'" and not in_double:
            in_single = not in_single
        elif ch == '"' and not in_single:
            in_double = not in_double
        elif not in_single and not in_double and text.startswith(needle, i):
            return True
        i += 1
    return False


# ---------------------------------------------------------------------------
# Command-position / nesting-boundary scanner.
#
# A destructive word counts only at command position: the first token of the
# command (leading whitespace is ignored), the first token after a command
# operator (`;`, `|`, `&`, `&&`, `||`, `(`, `)`), or the payload of a nested
# shell executor (`cmd /c`, `powershell -Command`, `pwsh -Command`,
# `bash -c`, ...). Words inside a quoted argument of a non-executor command
# (e.g. Write-Output 'Remove-Item is a cmdlet') and path components are never
# treated as commands.
# ---------------------------------------------------------------------------

_TOKEN_RE = re.compile(
    r"""&&|\|\||[|;&()]                       # command operators
    |'(?:[^']|'')*'                            # single-quoted (PowerShell '' escape)
    |"(?:[^"\\]|\\.)*"                         # double-quoted with backslash escapes
    |[A-Za-z_][A-Za-z0-9_@%+./\\:=-]*          # word / path / flag-like token
    |[^\s|;&()]+                               # any other bare token
    """,
    re.VERBOSE,
)

_COMMAND_OPERATORS = {"&&", "||", "|", ";", "&", "(", ")"}
_EXECUTORS = {"cmd", "powershell", "pwsh", "bash", "sh", "zsh", "dash", "ksh"}
# Per-executor payload flags whose argument is transparent command text and
# is analyzed recursively.
_TRANSPARENT_PAYLOAD_FLAGS = {
    "cmd": {"/c", "/k"},
    "powershell": {"-command"},
    "pwsh": {"-command"},
    "bash": {"-c", "--command", "-command"},
    "sh": {"-c"},
    "zsh": {"-c"},
    "dash": {"-c"},
    "ksh": {"-c"},
}
# Per-executor flags whose payload is opaque (Base64-encoded, or a script
# file). The payload is never decoded or executed; the analysis stops.
_OPAQUE_PAYLOAD_FLAGS = {
    "powershell": {"-encodedcommand", "-file"},
    "pwsh": {"-encodedcommand", "-file"},
}
# Transparent payload flags that leave the shell in a persistent interactive
# session after the payload runs (cmd /k keeps the window open).
_PERSISTENT_TRANSPARENT_FLAGS = {"cmd": {"/k"}}
# Executor switches that keep the session interactive after the payload
# (PowerShell -NoExit).
_PERSISTENT_INTERACTIVE_SWITCHES = {
    "powershell": {"-noexit"},
    "pwsh": {"-noexit"},
}
# Executor switches that take a separate value token (skipped with their value).
_EXECUTOR_VALUE_SWITCHES = {
    "-executionpolicy", "-version", "-workingdirectory", "-windowstyle",
    "-configurationname", "-o", "-rcfile", "--rcfile", "--init-file",
}
# PowerShell flags whose value is the literal target.
_TARGET_VALUE_FLAGS = {"-literalpath", "-path"}
# PowerShell flags that consume the next token without it being a target.
_NON_TARGET_VALUE_FLAGS = {
    "-filter", "-erroraction", "-errorvariable", "-outvariable",
    "-outbuffer", "-informationvariable", "-informationaction",
}

# Dynamic command tokens: a variable / command substitution that would be
# re-interpreted as a command when it appears at command position.
_DYNAMIC_TOKEN_RE = re.compile(r"\$[A-Za-z0-9_{(]|%[A-Za-z0-9_]+%|![A-Za-z0-9_]+!")
# Commands that re-evaluate their argument as a command (dynamic identity).
_DYNAMIC_EVALUATOR_TOKENS = {
    "invoke-expression", "iex",  # PowerShell
    "eval",                       # bash
    "call",                       # cmd
}


def _command_name(token: str) -> str:
    """Lowercased basename without a known executable extension."""
    base = token.replace("\\", "/").rsplit("/", 1)[-1]
    return re.sub(r"\.(exe|cmd|com|bat|ps1|sh)$", "", base, flags=re.IGNORECASE).lower()


def _is_dynamic_token(token: str) -> bool:
    """True when a token is a variable / command substitution / delayed-
    expansion value ($x, %x%, !x!, $(...))."""
    return bool(_DYNAMIC_TOKEN_RE.search(token))


def _payload_opaque_reason(payload: str, executor: str) -> str | None:
    """Return an opaque-payload reason for a transparent flag's argument, or
    None when it can be inspected statically.

    ``-Command -`` reads commands from stdin; a payload that *is* a variable
    is a dynamic command; and a PowerShell script block ``{ ... }`` outside
    string literals cannot be reliably parsed. None of these can be treated
    as a safe static command. The script-block brace rule only applies to
    PowerShell/pwsh payloads and is quote-aware.
    """
    stripped = payload.strip()
    if stripped == "-":
        return "stdin"
    if stripped.startswith(("$", "%", "!")):
        return "dynamic"
    if executor in ("powershell", "pwsh") and _has_unquoted(stripped, "{"):
        return "scriptblock"
    return None


def _operand_tokens(tokens: list[re.Match[str]], start: int, end: int) -> list[str]:
    """Collect the literal operand tokens after a destructive command word."""
    result: list[str] = []
    skip_next = False
    j = start
    while j < end:
        text = tokens[j].group(0)
        lowered = text.lower()
        if lowered in _COMMAND_OPERATORS:
            break
        if skip_next:
            skip_next = False
            j += 1
            continue
        if lowered in _TARGET_VALUE_FLAGS:
            if j + 1 < end:
                result.append(tokens[j + 1].group(0).strip("'\""))
                skip_next = True
            j += 1
            continue
        if lowered in _NON_TARGET_VALUE_FLAGS:
            skip_next = True
            j += 1
            continue
        if text[0] in ("-", "/") or text == ",":
            j += 1
            continue
        result.append(text.strip("'\""))
        j += 1
    return result


def _destructive_sites(command: str) -> tuple[list[list[str]], str | None, bool]:
    """Return ``(operand_sites, opaque_reason, interactive)`` for the command.

    ``operand_sites`` is the operand token list that follows each destructive
    command word at command position (including inside nested-shell payloads).

    ``opaque_reason`` is set when a nested-shell executor's payload cannot be
    inspected: "encoded" (PowerShell -EncodedCommand), "file" (PowerShell
    -File), "dynamic" (a dynamic command identity), "scriptblock" (an
    unparsable PowerShell script block), "stdin" (-Command -), or
    "interactive". An opaque payload is never decoded or executed.

    ``interactive`` is independent of ``opaque_reason``: it is True whenever
    the resulting session is interactive -- a persistent flag (-NoExit,
    cmd /k) even when the payload is file/encoded, or an executor with no
    transparent payload.

    An executor at command position keeps its state across its own switches
    (-NoProfile, -ExecutionPolicy Bypass, /d, /s, --noprofile, ...) until its
    transparent payload flag (/c, -c, -Command) is found and analyzed, or an
    opaque flag / segment end / non-switch operand decides otherwise. A quoted
    executable path at command position (e.g.
    "C:\\Program Files\\PowerShell\\7\\pwsh.exe") is recognized as an executor.

    Dynamic command identities inside a transparent payload (a variable at
    command position, after the PowerShell & operator, or passed to a
    re-evaluating builtin such as iex / Invoke-Expression / eval / call) are
    opaque. A variable in plain argument position (echo $HOME, Write-Output
    $env:TEMP, echo %TEMP%) is data and is not flagged.
    """
    if not isinstance(command, str) or not command:
        return [], None, False
    tokens = list(_TOKEN_RE.finditer(command))
    sites: list[list[str]] = []
    opaque: str | None = None
    interactive = False
    at_command_pos = True
    executor = ""
    pending_nested = False
    pending_executor = ""
    active_evaluator = ""
    persistent = False
    skip_next_value = False
    i = 0
    n = len(tokens)

    def _set_opaque(reason: str) -> None:
        nonlocal opaque
        if opaque is None:
            opaque = reason

    def _set_interactive() -> None:
        nonlocal interactive
        interactive = True

    while i < n:
        text = tokens[i].group(0)
        lowered = text.lower()
        if lowered in _COMMAND_OPERATORS:
            if executor:
                _set_opaque("interactive")
                _set_interactive()
            elif pending_nested:
                _set_opaque("interactive")
                _set_interactive()
            at_command_pos = True
            executor = ""
            pending_nested = False
            pending_executor = ""
            active_evaluator = ""
            persistent = False
            skip_next_value = False
            i += 1
            continue
        if text[0] in ("'", '"'):
            inner = text[1:-1]
            if pending_nested:
                reason = _payload_opaque_reason(inner, pending_executor)
                if reason:
                    _set_opaque(reason)
                else:
                    inner_sites, inner_opaque, inner_interactive = _destructive_sites(inner)
                    sites.extend(inner_sites)
                    if inner_opaque:
                        _set_opaque(inner_opaque)
                    if inner_interactive:
                        _set_interactive()
                pending_nested = False
                pending_executor = ""
                active_evaluator = ""
            elif at_command_pos and _command_name(inner) in _EXECUTORS:
                executor = _command_name(inner)
                active_evaluator = ""
                at_command_pos = False
            elif at_command_pos and _is_dynamic_token(inner):
                # A quoted dynamic token at command position (e.g. & "$cmd")
                # is a dynamic command identity.
                _set_opaque("dynamic")
                active_evaluator = ""
                at_command_pos = False
            elif active_evaluator and _is_dynamic_token(inner):
                _set_opaque("dynamic")
                at_command_pos = False
            else:
                at_command_pos = False
            i += 1
            continue
        name = _command_name(text)
        if pending_nested:
            # Keep the payload's executor context (pe) for the opacity check;
            # clearing it first would lose the PowerShell script-block rule.
            pending_nested = False
            pe = pending_executor
            pending_executor = ""
            if name in _DESTRUCTIVE_FS_TOKENS:
                sites.append(_operand_tokens(tokens, i + 1, n))
                at_command_pos = False
                active_evaluator = ""
            elif name in _EXECUTORS:
                executor = name
                at_command_pos = False
                active_evaluator = ""
            elif name in _DYNAMIC_EVALUATOR_TOKENS:
                active_evaluator = name
                at_command_pos = False
            else:
                reason = _payload_opaque_reason(text, pe)
                if reason:
                    _set_opaque(reason)
                at_command_pos = False
                active_evaluator = ""
            i += 1
            continue
        if executor:
            # Scanning the executor's own switches for its payload flag.
            if skip_next_value:
                skip_next_value = False
                i += 1
                continue
            if lowered in _PERSISTENT_INTERACTIVE_SWITCHES.get(executor, ()):
                persistent = True
                _set_interactive()
                i += 1
                continue
            if lowered in _TRANSPARENT_PAYLOAD_FLAGS.get(executor, ()):
                # -Command / /c / -c carry a transparent payload, but cmd /k
                # and -NoExit leave the session interactive afterwards.
                if lowered in _PERSISTENT_TRANSPARENT_FLAGS.get(executor, ()) or persistent:
                    _set_opaque("interactive")
                    _set_interactive()
                pending_nested = True
                pending_executor = executor
                executor = ""
                i += 1
                continue
            if lowered in _OPAQUE_PAYLOAD_FLAGS.get(executor, ()):
                _set_opaque("encoded" if lowered == "-encodedcommand" else "file")
                skip_next_value = True
                executor = ""
                i += 1
                continue
            if text[0] in ("-", "/"):
                if lowered in _EXECUTOR_VALUE_SWITCHES:
                    skip_next_value = True
                i += 1
                continue
            # A non-switch token while scanning an executor means it runs
            # without a transparent payload (positional script / interactive).
            _set_opaque("interactive")
            _set_interactive()
            executor = ""
            i += 1
            continue
        if at_command_pos:
            at_command_pos = False
            if _is_dynamic_token(text):
                _set_opaque("dynamic")
                active_evaluator = ""
            elif name in _DESTRUCTIVE_FS_TOKENS:
                sites.append(_operand_tokens(tokens, i + 1, n))
                active_evaluator = ""
            elif name in _EXECUTORS:
                executor = name
                active_evaluator = ""
            elif name in _DYNAMIC_EVALUATOR_TOKENS:
                active_evaluator = name
            else:
                active_evaluator = ""
            i += 1
            continue
        # ordinary operand / argument -- the active evaluator's state persists
        # to the segment end or a command operator, so any later dynamic
        # argument (quoted or not) is still caught.
        if active_evaluator and _is_dynamic_token(text):
            _set_opaque("dynamic")
        i += 1
    if executor:
        _set_opaque("interactive")
        _set_interactive()
    elif pending_nested or persistent:
        _set_opaque("interactive")
        _set_interactive()
    return sites, opaque, interactive


def _has_destructive_command_token(command: str) -> bool:
    """True when a destructive command word appears at command position."""
    return bool(_destructive_sites(command)[0])


def _normalize_target(path: str, cwd: str | None = None) -> str:
    """ntpath-normalize a target; resolve relative paths against cwd."""
    p = ntpath.normpath(str(path))
    if not ntpath.isabs(p):
        if cwd:
            p = ntpath.normpath(ntpath.join(ntpath.normpath(str(cwd)), str(path)))
    return p


def _is_dynamic_operand(op: str) -> bool:
    """True when an operand is a variable / glob, so its value is not static."""
    return op.startswith(("$", "%")) or bool(re.search(r"[*?\[\]]", op))


def _valid_identity_snapshot(snap: Any) -> bool:
    """A snapshot is only usable when it is a dict with a non-empty string
    volume_serial and a non-empty string file_id_128. Missing fields, empty
    values, wrong types, or snapshots carrying only unrelated fields are not
    identity evidence."""
    if not isinstance(snap, dict):
        return False
    vs = snap.get("volume_serial")
    fid = snap.get("file_id_128")
    if not isinstance(vs, str) or not vs:
        return False
    if not isinstance(fid, str) or not fid:
        return False
    return True


def _auto_detect_categories(command: str, first_token: str) -> set[str]:
    """Auto-detect destructive/high-impact intent from the command text.

    Safety analysis never relies on the caller passing destructive=true; the
    command itself decides whether the protection branch is required.
    """
    cats: set[str] = set()
    if _has_destructive_command_token(command):
        cats.add("DESTRUCTIVE_FS")
    if re.search(r"(?i)\breg\s+delete\b|HKCU:|HKLM:", command):
        cats.add("REGISTRY")
    if re.search(r"(?i)\b(start-process\s+-verb\s+runas|runas|sudo)\b", command):
        cats.add("ELEVATION")
    if re.search(r"(?i)\b(curl|wget|invoke-webrequest|invoke-restmethod)\b", command):
        cats.add("DOWNLOAD")
    if re.search(r"(?i)\b(winget|choco|scoop|pip|npm)\s+install\b", command):
        cats.add("INSTALL")
    return cats


def _component_contained(target: str, root: str, cwd: str | None = None) -> bool:
    """Windows-semantics containment check (no string-prefix match).

    Normalizes both paths with ntpath so `.` / `..` are resolved and drive
    and UNC boundaries are honored. A relative target is resolved against
    ``cwd`` when one is given; otherwise it cannot be verified and returns
    False (fail closed). Different drives, different UNC roots, and
    un-normalizable or relative paths are never reported as contained.
    """
    if not target or not root:
        return False
    t = ntpath.normpath(target)
    r = ntpath.normpath(root)
    if not ntpath.isabs(t):
        if cwd:
            t = ntpath.normpath(ntpath.join(ntpath.normpath(str(cwd)), target))
        else:
            return False
    if not ntpath.isabs(t) or not ntpath.isabs(r):
        return False
    t_drive = ntpath.splitdrive(t)[0].lower()
    r_drive = ntpath.splitdrive(r)[0].lower()
    if not t_drive or t_drive != r_drive:
        return False
    t_parts = [p for p in re.split(r"[\\/]", t) if p]
    r_parts = [p for p in re.split(r"[\\/]", r) if p]
    if len(t_parts) < len(r_parts):
        return False
    for i, rp in enumerate(r_parts):
        if t_parts[i].lower() != rp.lower():
            return False
    return True


def _is_protected_root(target: str) -> bool:
    drive = re.match(r"^[A-Za-z]:[\\/]?$", target)
    share = target.startswith("\\\\")
    profile = re.search(r"[\\/](Users|用户)[\\/][^\\/]+$", target, re.IGNORECASE)
    return bool(drive or share or profile)


def inventory_digest(
    inventory: list[dict[str, Any]],
    display_paths: list[str] | None = None,
) -> str:
    """Deterministic SHA-256 over the canonical UTF-16LE-hex inventory bytes.

    Order-independent, display-path-independent, no NFC/lowercase/casefold.
    Exact duplicates collapse; the digest never reads or writes files.
    """
    seen: set[tuple[str, str, str, Any]] = set()
    records: list[dict[str, Any]] = []
    for raw in inventory:
        key = (
            str(raw.get("path_utf16le_hex", "")),
            str(raw.get("type", "")),
            str(raw.get("size_state", "")),
            raw.get("size"),
        )
        if key in seen:
            continue
        seen.add(key)
        records.append(
            {
                "path_utf16le_hex": str(raw.get("path_utf16le_hex", "")),
                "type": str(raw.get("type", "")),
                "size_state": str(raw.get("size_state", "")),
                "size": raw.get("size"),
            }
        )
    type_order = {"D": 0, "F": 1, "L": 2}
    size_state_order = {"KNOWN": 0, "UNAVAILABLE": 1}

    def sort_key(rec: dict[str, Any]) -> tuple[Any, ...]:
        try:
            path_bytes = bytes.fromhex(rec["path_utf16le_hex"])
        except ValueError:
            path_bytes = b""
        return (
            path_bytes,
            type_order.get(str(rec["type"]), 9),
            size_state_order.get(str(rec["size_state"]), 9),
            rec["size"] if isinstance(rec["size"], int) else -1,
        )

    records.sort(key=sort_key)
    lines = [
        json.dumps(rec, ensure_ascii=True, separators=(",", ":")) for rec in records
    ]
    blob = ("\n".join(lines) + "\n").encode("utf-8")
    return hashlib.sha256(blob).hexdigest()


def _inventory_conflict(inventory: list[dict[str, Any]]) -> bool:
    """True when two records share a path but differ in type/size_state/size."""
    by_path: dict[str, list[tuple[str, str, Any]]] = {}
    for rec in inventory:
        path = str(rec.get("path_utf16le_hex", ""))
        sig = (
            str(rec.get("type", "")),
            str(rec.get("size_state", "")),
            rec.get("size"),
        )
        by_path.setdefault(path, []).append(sig)
    for sigs in by_path.values():
        if len(set(sigs)) > 1:
            return True
    return False


def _context_shell(ctx_env: dict[str, Any]) -> tuple[str | None, str | None]:
    """Derive (family, confidence) from collector environment evidence."""
    edition = str(ctx_env.get("ps_edition", "") or "").upper()
    psver = str(ctx_env.get("ps_version", "") or "")
    major = psver.split(".")[0] if psver else ""
    if edition == "DESKTOP":
        return "WINDOWS_POWERSHELL_5_1", ("CONFIRMED" if major.startswith("5") else "HIGH")
    if edition == "CORE" and major.isdigit() and int(major) >= 7:
        return "POWERSHELL_7_PLUS", "CONFIRMED"
    if edition == "CORE":
        return "POWERSHELL_7_PLUS", "MEDIUM"
    return None, None


_CTX_CTYPE_MAP = {
    "APPLICATION": "NATIVE_EXECUTABLE",
    "CMDLET": "POWERSHELL_CMDLET",
    "FUNCTION": "POWERSHELL_FUNCTION",
    "ALIAS": "POWERSHELL_ALIAS",
    "EXTERNALSCRIPT": "SCRIPT_FILE",
}

_DIALECT_CODES = {
    "DIALECT_COMMAND_MISMATCH",
    "OPERATOR_UNSUPPORTED_BY_VERSION",
    "BASH_BUILTIN_IN_POWERSHELL",
    "BASH_HEREDOC_IN_NON_BASH_SHELL",
    "POWERSHELL_COLON_VARIABLE_AMBIGUITY",
    "NESTED_QUOTES_NATIVE_ARGV",
}


def analyze(payload: dict[str, Any]) -> dict[str, Any]:
    """Full deterministic diagnostic. Pure; never executes or writes."""
    if not isinstance(payload, dict):
        raise ValueError("payload must be a JSON object")

    shell = payload.get("shell") or {}
    family_raw = str(shell.get("family", "UNKNOWN") or "UNKNOWN").upper()
    version = str(shell.get("version", "UNKNOWN") or "UNKNOWN")
    confidence = str(shell.get("confidence", "UNKNOWN") or "UNKNOWN").upper()
    if family_raw not in SHELL_FAMILIES:
        raise ValueError(f"unknown shell family enum: {family_raw!r}")
    if confidence not in CONFIDENCE_VALUES:
        raise ValueError(f"unknown shell confidence enum: {confidence!r}")

    context = payload.get("context")
    if context is not None and not isinstance(context, dict):
        raise ValueError("context must be a JSON object")
    context = context or {}
    ctx_env = context.get("environment")
    if ctx_env is not None and not isinstance(ctx_env, dict):
        raise ValueError("context.environment must be a JSON object")
    ctx_exec = context.get("executable")
    if ctx_exec is not None and not isinstance(ctx_exec, dict):
        raise ValueError("context.executable must be a JSON object")
    ctx_target = context.get("target")
    if ctx_target is not None and not isinstance(ctx_target, dict):
        raise ValueError("context.target must be a JSON object")
    ctx_env = ctx_env or {}
    ctx_exec = ctx_exec or {}
    ctx_target = ctx_target or {}

    evidence_list = payload.get("evidence") or []
    command = str(payload.get("command", "") or "")
    executable = payload.get("executable") or {}
    nested = payload.get("nested") or []
    destructive = bool(payload.get("destructive", False))
    preview = payload.get("preview") or {}
    inventory = payload.get("inventory") or []
    identity_a = payload.get("preview_before") or payload.get("target_identity_a")
    identity_b = payload.get("preview_after") or payload.get("target_identity_b")
    reparse = bool(payload.get("reparse_point", False))
    sensitive_indexes = payload.get("sensitive_arguments") or []
    identity_candidates = payload.get("identity_candidates") or []

    findings: list[dict[str, Any]] = []
    secondary: list[str] = []
    family = family_raw

    # --- shell detection ---------------------------------------------------
    ctx_family, ctx_confidence = _context_shell(ctx_env)
    if ctx_family:
        if family_raw in ("", "UNKNOWN"):
            family = ctx_family
            if confidence in ("UNKNOWN", "LOW"):
                confidence = ctx_confidence
        elif family_raw in _POWERSHELL_HOST_FAMILIES and family_raw != ctx_family:
            findings.append(_finding(
                "SHELL_EVIDENCE_CONFLICT",
                {"start": 0, "end": 0},
                "shell metadata conflicts with collected context evidence",
            ))
            family = "UNKNOWN"

    if confidence == "CONFLICTED" or (
        family == "UNKNOWN" and len(set(evidence_list)) > 1
    ):
        findings.append(_finding(
            "SHELL_EVIDENCE_CONFLICT",
            {"start": 0, "end": 0},
            "conflicting shell evidence",
        ))
        family = "UNKNOWN"
    elif confidence == "LOW" and family != "UNKNOWN":
        findings.append(_finding(
            "SHELL_DETECTION_CONFIDENCE_LOW",
            {"start": 0, "end": 0},
            "low shell detection confidence",
        ))
    elif confidence in ("LOW", "UNKNOWN") and family == "UNKNOWN":
        findings.append(_finding(
            "SHELL_DETECTION_CONFIDENCE_LOW",
            {"start": 0, "end": 0},
            "unknown shell identity; detection confidence is weak",
        ))

    if family == "WINDOWSAPPS_STUB":
        findings.append(_finding(
            "WINDOWSAPPS_STUB_DETECTED",
            {"start": 0, "end": 0},
            "WindowsApps shell stub detected",
        ))
        secondary.append("WINDOWSAPPS_STUB")

    # --- tokenization ------------------------------------------------------
    unterminated, quote_char = _quote_state(command)
    if unterminated:
        findings.append(_finding(
            "UNTERMINATED_QUOTE",
            {"start": 0, "end": len(command)},
            f"unterminated {quote_char} quote",
        ))

    first_token, _in_string = _first_command_token(command)

    # Auto-detect destructive / high-impact intent from the command text so
    # safety analysis never depends on the caller passing destructive=true.
    auto_cats = _auto_detect_categories(command, first_token)
    destructive_fs = destructive or ("DESTRUCTIVE_FS" in auto_cats)

    # A nested-shell executor whose payload is opaque (PowerShell
    # -EncodedCommand / -File, or an executor entering an uninspectable
    # interactive/script shell) can never be verified safe. The payload is
    # not decoded or executed; the analysis stops.
    destructive_sites, opaque_payload, session_interactive = _destructive_sites(command)
    if opaque_payload:
        findings.append(_finding(
            "OPAQUE_EXECUTOR_PAYLOAD",
            {"start": 0, "end": len(command)},
            f"nested shell payload is opaque ({opaque_payload}) and cannot be inspected",
        ))

    nested_risk = bool(nested) or bool(
        re.search(r"(?i)\b(bash|pwsh|powershell|cmd)\s+(-c|/c)\b", command)
    )
    if family == "PYTHON_SUBPROCESS" and re.search(r"&&|\|\||(?<!\w)\||;", command):
        # A Python subprocess may or may not route through a shell; the
        # boundary is unproven, so treat it as reinterpretation risk.
        nested_risk = True
    primary = "UNKNOWN"
    if nested_risk:
        findings.append(_finding(
            "NESTED_REINTERPRETATION_RISK",
            {"start": 0, "end": len(command)},
            "nested shell reinterpretation risk",
        ))
        primary = "NESTED_SHELL"
        secondary.append("NESTED_SHELL")

    # executable / identity resolution
    exec_identity = str(executable.get("identity", "") or "").upper()
    exec_resolved = bool(executable.get("resolved", False))
    ctx_exec_requested = str(ctx_exec.get("requested", "") or "")
    ctx_exec_found = ctx_exec.get("found")
    ctx_exec_path = str(ctx_exec.get("resolved_path", "") or "")
    ctx_exec_windowsapps = bool(ctx_exec.get("in_windows_apps", False))
    ctx_exec_ctype = str(ctx_exec.get("command_type", "") or "")

    ctx_exec_matches = bool(ctx_exec_requested) and (
        ctx_exec_requested.lower() == first_token
        or Path(ctx_exec_requested.replace("\\", "/")).name.lower() == first_token
    )
    if ctx_exec_matches:
        if ctx_exec_found is False:
            findings.append(_finding(
                "EXECUTABLE_NOT_FOUND",
                {"start": 0, "end": len(first_token)},
                "executable could not be resolved by collected context",
            ))
            primary = "UNKNOWN"
        elif ctx_exec_found is True:
            exec_resolved = True
            if ctx_exec_windowsapps and ctx_exec_path:
                findings.append(_finding(
                    "WINDOWSAPPS_STUB_DETECTED",
                    {"start": 0, "end": len(first_token)},
                    "executable resolves through WindowsApps",
                ))
                secondary.append("WINDOWSAPPS_STUB")
            if not exec_identity and ctx_exec_ctype:
                exec_identity = _CTX_CTYPE_MAP.get(
                    ctx_exec_ctype.upper(), "NATIVE_EXECUTABLE"
                )

    if identity_candidates:
        findings.append(_finding(
            "COMMAND_IDENTITY_AMBIGUOUS",
            {"start": 0, "end": len(first_token)},
            "command identity ambiguous",
        ))
        primary = "UNKNOWN"
    elif (
        first_token
        and not exec_resolved
        and not nested_risk
        and not identity_candidates
        and first_token not in _KNOWN_EXTERNAL_TOOLS
    ):
        if first_token not in _POWERSHELL_CMDLETS and first_token not in _COMMON_BUILTINS:
            findings.append(_finding(
                "EXECUTABLE_NOT_FOUND",
                {"start": 0, "end": len(first_token)},
                "executable could not be resolved",
            ))
            primary = "UNKNOWN"

    # dialect / version rules
    if not _in_string:
        if family in ("GIT_BASH", "CMD", "WSL") and first_token in _POWERSHELL_CMDLETS:
            findings.append(_finding(
                "DIALECT_COMMAND_MISMATCH",
                {"start": 0, "end": len(first_token)},
                "PowerShell cmdlet in non-PowerShell command position",
            ))
        if family in PS_FAMILIES and first_token in _BASH_BUILTINS:
            findings.append(_finding(
                "BASH_BUILTIN_IN_POWERSHELL",
                {"start": 0, "end": len(first_token)},
                "bash builtin in PowerShell command position",
            ))
        if first_token == "grep" and family != "GIT_BASH" and exec_identity == "NATIVE_EXECUTABLE" and exec_resolved:
            secondary.append("NATIVE_EXECUTABLE")
            if primary == "UNKNOWN":
                primary = "NATIVE_EXECUTABLE"
        if "&&" in command or "||" in command:
            if family == "WINDOWS_POWERSHELL_5_1":
                ops = [op for op in ("&&", "||") if op in command]
                op = ops[0]
                findings.append(_finding(
                    "OPERATOR_UNSUPPORTED_BY_VERSION",
                    {"start": command.find(op), "end": command.find(op) + len(op)},
                    f"{' and '.join(ops)} unsupported in Windows PowerShell 5.1",
                ))

    # additional dialect risk: heredoc, colon-variable, nested native quotes
    if family in ("WINDOWS_POWERSHELL_5_1", "POWERSHELL_7_PLUS", "CMD", "WINDOWSAPPS_STUB") and _has_unquoted(command, "<<"):
        findings.append(_finding(
            "BASH_HEREDOC_IN_NON_BASH_SHELL",
            {"start": command.find("<<"), "end": command.find("<<") + 2},
            "bash heredoc marker in a non-bash shell",
        ))
    if family in PS_FAMILIES:
        for m in _COLON_VARIABLE_RE.finditer(command):
            findings.append(_finding(
                "POWERSHELL_COLON_VARIABLE_AMBIGUITY",
                {"start": m.start(), "end": m.end()},
                "trailing colon after a PowerShell variable is ambiguous; write ${name}:",
            ))
            break
        if _NESTED_QUOTE_RE.search(command):
            m = _NESTED_QUOTE_RE.search(command)
            findings.append(_finding(
                "NESTED_QUOTES_NATIVE_ARGV",
                {"start": m.start(), "end": m.end()},
                "backslash-escaped quotes in a native CLI argument",
            ))

    # classifications and high-impact findings (auto-detected from the
    # command text; the caller is never required to pass destructive=true)
    if destructive_fs:
        secondary.append("DESTRUCTIVE_FILESYSTEM_OPERATION")
    if "REGISTRY" in auto_cats:
        secondary.append("REGISTRY_OPERATION")
        findings.append(_finding(
            "REGISTRY_OPERATION",
            {"start": 0, "end": len(command)},
            "registry modification or delete",
        ))
    if "ELEVATION" in auto_cats:
        secondary.append("PRIVILEGE_ELEVATION_OPERATION")
        findings.append(_finding(
            "PRIVILEGE_ELEVATION_OPERATION",
            {"start": 0, "end": len(command)},
            "privilege elevation",
        ))
    if "DOWNLOAD" in auto_cats or "INSTALL" in auto_cats:
        secondary.append("NETWORK_DOWNLOAD_INSTALL_OPERATION")
        findings.append(_finding(
            "NETWORK_DOWNLOAD_INSTALL_OPERATION",
            {"start": 0, "end": len(command)},
            "network download or install",
        ))
    if _DYNAMIC_RE.search(command):
        secondary.append("VARIABLE_EXPANSION")
    if first_token in _POWERSHELL_CMDLETS and primary == "UNKNOWN":
        primary = "POWERSHELL_CMDLET"
    elif first_token and primary == "UNKNOWN" and exec_resolved:
        primary = exec_identity if exec_identity in {
            "NATIVE_EXECUTABLE", "POWERSHELL_CMDLET", "POWERSHELL_FUNCTION",
            "POWERSHELL_ALIAS", "CMD_BUILTIN", "SHELL_BUILTIN", "SCRIPT_FILE",
        } else "NATIVE_EXECUTABLE"
    elif first_token in _COMMON_BUILTINS and primary == "UNKNOWN":
        primary = "SHELL_BUILTIN"

    # quoting / equivalence
    dynamic = bool(_DYNAMIC_RE.search(command))
    glob = bool(_GLOB_RE.search(command))
    redirect = bool(_REDIRECT_RE.search(command))
    pipe = bool(_PIPE_RE.search(command))
    equivalence = "FULL_SEMANTIC_EQUIVALENCE_NOT_PROVEN"
    safe_form: str = "NOT_AVAILABLE"

    if (
        dynamic
        or glob
        or redirect
        or pipe
        or unterminated
        or identity_candidates
        or "&&" in command
        or ";" in command
        or (
            not exec_resolved
            and first_token not in _POWERSHELL_CMDLETS
            and first_token not in _COMMON_BUILTINS
            and first_token not in _KNOWN_EXTERNAL_TOOLS
        )
    ):
        if dynamic:
            findings.append(_finding(
                "ARGUMENT_BOUNDARY_EQUIVALENCE_NOT_PROVEN",
                {"start": 0, "end": len(command)},
                "dynamic expansion prevents argument-boundary proof",
            ))
        elif (
            not exec_resolved
            and first_token
            and not identity_candidates
            and first_token not in _POWERSHELL_CMDLETS
            and first_token not in _KNOWN_EXTERNAL_TOOLS
            and first_token not in _COMMON_BUILTINS
        ):
            pass  # EXECUTABLE_NOT_FOUND already covers the identity gap
        else:
            findings.append(_finding(
                "ARGUMENT_BOUNDARY_EQUIVALENCE_NOT_PROVEN",
                {"start": 0, "end": len(command)},
                "argument boundary equivalence not proven",
            ))
    elif first_token:
        equivalence = "ARGUMENT_BOUNDARY_EQUIVALENT"
        safe_form = _redact(command)

    # --- secrets -----------------------------------------------------------
    secret_detected = False
    for pattern in _SECRET_PATTERNS:
        if pattern.search(command):
            secret_detected = True
            break
    if sensitive_indexes:
        secret_detected = True
    if secret_detected:
        findings.append(_finding(
            "SENSITIVE_VALUE_REDACTED",
            {"start": 0, "end": len(command)},
            "sensitive value redacted",
        ))
        safe_form = "NOT_AVAILABLE"
        equivalence = "FULL_SEMANTIC_EQUIVALENCE_NOT_PROVEN"

    # --- destructive / high-impact analysis --------------------------------
    recursive = bool(re.search(r"(?i)-recurse|\b/s\b", command)) or _is_posix_rm_recursive(
        command
    )
    recursive_preview_status = "NOT_APPLICABLE"
    if destructive_fs:
        if family == "UNKNOWN":
            findings.append(_finding(
                "DESTRUCTIVE_CONTEXT_INCOMPLETE",
                {"start": 0, "end": len(command)},
                "destructive analysis requires confirmed shell identity",
            ))
        cwd = payload.get("working_directory")
        allowed_root = payload.get("allowed_root")
        target = payload.get("target")
        if not cwd or not allowed_root or not target:
            findings.append(_finding(
                "DESTRUCTIVE_CONTEXT_INCOMPLETE",
                {"start": 0, "end": len(command)},
                "destructive context incomplete",
            ))
        target_for_containment = str(target or "")
        if ctx_target.get("full_path"):
            target_for_containment = str(ctx_target["full_path"])
        if target_for_containment and allowed_root and not _component_contained(
            target_for_containment, str(allowed_root), cwd
        ):
            findings.append(_finding(
                "TARGET_OUTSIDE_ALLOWED_ROOT",
                {"start": 0, "end": len(command)},
                "target outside allowed root",
            ))
        if target_for_containment and _is_protected_root(target_for_containment):
            findings.append(_finding(
                "PROTECTED_ROOT_TARGET",
                {"start": 0, "end": len(command)},
                "protected root target",
            ))
        if reparse:
            findings.append(_finding(
                "REPARSE_POINT_DESTRUCTIVE_TARGET",
                {"start": 0, "end": len(command)},
                "reparse point destructive target",
            ))

        # Context target evidence (collect_windows_context.ps1). Fail closed
        # when the evidence is absent, contradictory, or unresolved.
        target_not_found = False
        if ctx_target:
            t_exists = ctx_target.get("exists")
            t_reparse = bool(ctx_target.get("is_reparse_point", False))
            t_error = str(ctx_target.get("error", "") or "")
            if t_exists is False and not t_error:
                target_not_found = True
                findings.append(_finding(
                    "TARGET_NOT_FOUND",
                    {"start": 0, "end": len(command)},
                    "destructive target does not exist",
                ))
            elif t_exists is True and t_reparse:
                findings.append(_finding(
                    "REPARSE_POINT_DESTRUCTIVE_TARGET",
                    {"start": 0, "end": len(command)},
                    "destructive target is a reparse point",
                ))

        # --- command-to-evidence binding ------------------------------------
        # Normalize and cross-check the payload target, the collector's
        # requested/full targets, and (for recognized delete commands) the
        # static literal operand extracted from the command text. Any
        # disagreement fails closed; a context exists=true for one path never
        # proves a different command target safe.
        if ctx_target:
            t_req = str(ctx_target.get("requested", "") or "")
            t_full = str(ctx_target.get("full_path", "") or "")
            norm_req = _normalize_target(t_req, cwd) if t_req else ""
            norm_full = _normalize_target(t_full, cwd) if t_full else ""
            norm_payload = _normalize_target(target, cwd) if target else ""
            if norm_req and norm_full and norm_req.lower() != norm_full.lower():
                findings.append(_finding(
                    "TARGET_EVIDENCE_MISMATCH",
                    {"start": 0, "end": len(command)},
                    "context target requested and resolved full path disagree",
                ))
            elif norm_payload and norm_req and norm_payload.lower() != norm_req.lower():
                findings.append(_finding(
                    "TARGET_EVIDENCE_MISMATCH",
                    {"start": 0, "end": len(command)},
                    "payload target disagrees with context requested target",
                ))
            elif norm_payload and norm_full and norm_payload.lower() != norm_full.lower():
                findings.append(_finding(
                    "TARGET_EVIDENCE_MISMATCH",
                    {"start": 0, "end": len(command)},
                    "payload target disagrees with context resolved target",
                ))
        if "DESTRUCTIVE_FS" in auto_cats:
            # The evidence model supports a single target, so binding is
            # proven only when there is exactly one destructive site, exactly
            # one static literal operand, and that operand agrees with the
            # payload/context target. Anything else fails closed.
            sites = destructive_sites
            evidence_target = ""
            for cand in (target, ctx_target.get("requested"), ctx_target.get("full_path")):
                norm_cand = _normalize_target(cand, cwd) if cand else ""
                if norm_cand:
                    evidence_target = norm_cand
                    break
            if len(sites) != 1:
                findings.append(_finding(
                    "TARGET_COMMAND_BINDING_UNPROVEN",
                    {"start": 0, "end": len(command)},
                    "multiple or unknown destructive commands; binding unproven",
                ))
            else:
                operands = sites[0]
                if len(operands) != 1:
                    findings.append(_finding(
                        "TARGET_COMMAND_BINDING_UNPROVEN",
                        {"start": 0, "end": len(command)},
                        "zero or multiple static target operands; binding unproven",
                    ))
                elif _is_dynamic_operand(operands[0]):
                    findings.append(_finding(
                        "TARGET_COMMAND_BINDING_UNPROVEN",
                        {"start": 0, "end": len(command)},
                        "command target is dynamic; binding unproven",
                    ))
                else:
                    norm_op = _normalize_target(operands[0], cwd)
                    if evidence_target and norm_op.lower() != evidence_target.lower():
                        findings.append(_finding(
                            "TARGET_EVIDENCE_MISMATCH",
                            {"start": 0, "end": len(command)},
                            "command operand disagrees with target evidence",
                        ))

        if family == "WSL":
            findings.append(_finding(
                "UNSUPPORTED_FILESYSTEM_PREVIEW",
                {"start": 0, "end": len(command)},
                "POSIX destructive preview unsupported",
            ))

        inventory_conflict = _inventory_conflict(inventory)
        if inventory_conflict:
            findings.append(_finding(
                "DUPLICATE_INVENTORY_ENTRY",
                {"start": 0, "end": len(command)},
                "conflicting duplicate inventory record",
            ))

        if preview:
            entry_limit = preview.get("entry_limit")
            observed = preview.get("observed_entries")
            if isinstance(entry_limit, int) and isinstance(observed, int):
                if observed >= entry_limit:
                    recursive_preview_status = "INCOMPLETE"
                    findings.append(_finding(
                        "RECURSIVE_PREVIEW_INCOMPLETE",
                        {"start": 0, "end": len(command)},
                        "recursive preview reached its limit",
                    ))
                else:
                    recursive_preview_status = "OBSERVED_COMPLETE"

        # Unified target-identity evidence check: any destructive operation,
        # recursive or not, must have reliable identity evidence. A caller-
        # supplied target string alone is never enough. Reliable evidence is
        # a complete identity snapshot pair or a collector-confirmed existing
        # target (exists=true without an error).
        ctx_target_confirmed = bool(ctx_target) and ctx_target.get("exists") is True and not str(
            ctx_target.get("error", "") or ""
        )
        if not inventory_conflict:
            if _valid_identity_snapshot(identity_a) and _valid_identity_snapshot(identity_b):
                if (
                    identity_a.get("volume_serial") != identity_b.get("volume_serial")
                    or identity_a.get("file_id_128") != identity_b.get("file_id_128")
                ):
                    findings.append(_finding(
                        "TARGET_CHANGED_DURING_PREVIEW",
                        {"start": 0, "end": len(command)},
                        "target changed during preview",
                    ))
            elif target and not target_not_found and not ctx_target_confirmed:
                findings.append(_finding(
                    "TARGET_IDENTITY_UNAVAILABLE",
                    {"start": 0, "end": len(command)},
                    "target identity evidence incomplete for destructive operation",
                ))

    # --- normalize ---------------------------------------------------------
    findings.sort(key=lambda f: FINDING_REGISTRY_INDEX[f["code"]])
    dialect_hit = any(f["code"] in _DIALECT_CODES for f in findings)
    high_impact_hit = any(f["code"] in _HIGH_IMPACT_CODES for f in findings)
    if (
        any(f["severity"] == "STOP" for f in findings)
        or dialect_hit
        or high_impact_hit
        or destructive_fs
    ):
        safe_form = "NOT_AVAILABLE"
        equivalence = "FULL_SEMANTIC_EQUIVALENCE_NOT_PROVEN"
    risk = "LOW"
    for f in findings:
        if SEVERITY_ORDER[f["severity"]] > SEVERITY_ORDER[risk]:
            risk = f["severity"]
    # A destructive filesystem operation is never LOW, even with complete
    # evidence; the minimum is HIGH.
    if destructive_fs and SEVERITY_ORDER[risk] < SEVERITY_ORDER["HIGH"]:
        risk = "HIGH"
    stop_reasons = [f["code"] for f in findings if f["severity"] == "STOP"]

    target_identity = None
    if isinstance(identity_a, dict):
        target_identity = _redact_tree(identity_a)

    shell_executable = str(executable.get("identity", "") or "")
    if not shell_executable and ctx_exec_matches and ctx_exec_path:
        shell_executable = ctx_exec_path
    if not shell_executable and ctx_env.get("current_process_path"):
        shell_executable = str(ctx_env["current_process_path"])
    host_process = str(ctx_env.get("host_name", "") or "") if ctx_env else ""

    secondary_sorted = sorted(set(secondary))
    if primary == "UNKNOWN" and "NESTED_SHELL" in secondary_sorted:
        primary = "NESTED_SHELL"

    if session_interactive:
        execution_mode = "INTERACTIVE"
    elif nested_risk:
        execution_mode = "NESTED"
    else:
        execution_mode = "DIRECT"

    classification = {"primary": primary, "secondary": secondary_sorted}
    redacted_findings = _redact_tree(findings)

    return {
        "shell_family": family,
        "shell_executable": _redact(shell_executable or "UNKNOWN"),
        "shell_version": version,
        "host_process": _redact(host_process or "UNKNOWN"),
        "execution_mode": execution_mode,
        "detection_confidence": confidence,
        "command_classification": classification,
        "risk_level": risk,
        "findings": redacted_findings,
        "target_identity": target_identity,
        "recursive_preview_status": recursive_preview_status,
        "safe_command_form": safe_form,
        "equivalence_level": equivalence,
        "execution_authorized": "NO",
        "stop_reasons": stop_reasons,
    }


def canonical_json_dumps(obj: Any) -> str:
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"


def _emit_stdout(text: str) -> None:
    """Write UTF-8 (LF, no BOM) bytes to stdout regardless of the process
    encoding / console codepage. Falls back to the text layer when stdout
    has no binary buffer (e.g. an in-process StringIO)."""
    data = text.encode("utf-8")
    buffer = getattr(sys.stdout, "buffer", None)
    if buffer is not None:
        buffer.write(data)
        buffer.flush()
    else:
        sys.stdout.write(text)


def _load_context_file(path_text: str) -> dict[str, Any]:
    text = Path(path_text).read_text(encoding="utf-8")
    obj = json.loads(text)
    if not isinstance(obj, dict):
        raise ValueError("context file must contain a JSON object")
    return obj


def _cli(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    input_path: str | None = None
    context_path: str | None = None
    i = 0
    while i < len(argv):
        if argv[i] == "--input" and i + 1 < len(argv):
            input_path = argv[i + 1]
            i += 2
        elif argv[i] == "--context" and i + 1 < len(argv):
            context_path = argv[i + 1]
            i += 2
        else:
            print(
                "usage: windows_shell_safe.py [--input <file.json>] [--context <file.json>]",
                file=sys.stderr,
            )
            return 4
    try:
        if input_path:
            text = Path(input_path).read_text(encoding="utf-8")
        else:
            text = sys.stdin.read()
    except Exception as exc:  # noqa: BLE001
        print(f"error: input could not be read: {_redact(str(exc))}", file=sys.stderr)
        return 4
    try:
        payload = json.loads(text)
        if not isinstance(payload, dict):
            raise ValueError("payload must be a JSON object")
    except Exception as exc:  # noqa: BLE001
        print(f"error: malformed input: {_redact(str(exc))}", file=sys.stderr)
        return 2
    if context_path or payload.get("context_file"):
        try:
            ctx_file = context_path or str(payload["context_file"])
            payload["context"] = _load_context_file(ctx_file)
        except Exception as exc:  # noqa: BLE001
            print(f"error: context could not be read: {_redact(str(exc))}", file=sys.stderr)
            return 4
    try:
        result = analyze(payload)
    except ValueError as exc:
        print(f"error: malformed input: {_redact(str(exc))}", file=sys.stderr)
        return 2
    except Exception as exc:  # noqa: BLE001
        print(f"error: analysis failed: {_redact(str(exc))}", file=sys.stderr)
        return 4
    stop_reasons = result.get("stop_reasons") or []
    if "UNSUPPORTED_FILESYSTEM_PREVIEW" in stop_reasons:
        print("error: unsupported filesystem model for the requested analysis", file=sys.stderr)
        return 3
    # Exit 1: analysis completed, full JSON emitted, but shell identity is
    # unconfirmed (UNKNOWN family or UNKNOWN/LOW/CONFLICTED confidence), so
    # the result is conservative. Confirmed-identity analyses exit 0 even
    # with HIGH/STOP findings because the diagnostic itself is complete.
    exit_code = 0
    confidence_out = str(result.get("detection_confidence", "UNKNOWN"))
    if result.get("shell_family") == "UNKNOWN" or confidence_out in ("UNKNOWN", "LOW", "CONFLICTED"):
        exit_code = 1
    # The tool is read-only: it never writes a file. Result goes to stdout.
    _emit_stdout(canonical_json_dumps(result))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(_cli())
