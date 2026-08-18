"""Strict frontmatter parser/emitter for SKILL.md (standard library only).

This is deliberately NOT a general YAML parser. Canonical SKILL.md
frontmatter is restricted to a flat mapping of scalar keys to scalar
values, where:

  - string values are written as JSON-compatible double-quoted strings
    (parsed/emitted with the stdlib json module), and
  - host-specific boolean values (added only to installed copies by
    install.py, never to canonical files) are written as the bare YAML
    words true / false / null.

The emitter additionally allows one level of nested mapping (e.g. an
OpenCode metadata block), emitted with two-space indentation. The strict
parser does not read nested values back — canonical files stay flat, and
nested host metadata is only ever produced by install.py on installed
copies. Anything else is rejected. This keeps frontmatter provably valid
YAML without depending on PyYAML, and without growing a YAML emulator.
"""

import json


def _split_frontmatter(text):
    """Return (raw_lines, body) or raise ValueError."""
    if not text.startswith("---"):
        raise ValueError("frontmatter must start with '---'")
    lines = text.split("\n")
    if not lines or lines[0].strip() != "---":
        raise ValueError("first line must be '---'")
    close = None
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            close = i
            break
    if close is None:
        raise ValueError("frontmatter not closed")
    raw = lines[1:close]
    body = "\n".join(lines[close + 1:])
    return raw, body


def _split_key_value(line):
    """Find the first ': ' separating key from value (YAML rule)."""
    for j, ch in enumerate(line):
        if ch == ":":
            after = line[j + 1:]
            if after == "" or after[0] == " ":
                return line[:j], line[j + 2:]
    return None, None


def parse_scalar(raw):
    """Parse one frontmatter value token into a typed Python value.

    Returns str / bool / None. Raises ValueError on anything outside
    the supported subset: single-quoted scalars, bad JSON escapes, and
    bare numbers are all rejected by this typed parse (numbers and bare
    words other than true/false/null are rejected as unknown scalars).
    """
    v = raw.strip()
    if v == "":
        raise ValueError("empty value")
    if v[0] == '"':
        # Must be a single, closed double-quoted JSON string.
        if len(v) < 2 or v[-1] != '"':
            raise ValueError(f"unclosed double-quoted string: {raw!r}")
        try:
            value = json.loads(v)
        except json.JSONDecodeError as e:
            raise ValueError(f"invalid double-quoted string: {e}") from None
        if not isinstance(value, str):
            # A quoted token that JSON parses to a non-string (e.g. a
            # quoted number is still a string, so this is defensive).
            raise ValueError(f"quoted value is not a string: {raw!r}")
        return value
    if v[0] == "'":
        # Single-quoted YAML scalars are not part of the canonical format.
        raise ValueError(f"single-quoted scalars not allowed: {raw!r}")
    # Bare YAML scalar words for host-specific booleans/null only.
    if v == "true":
        return True
    if v == "false":
        return False
    if v == "null":
        return None
    # Reject bare numbers and any other unquoted token; the canonical
    # format requires double-quoted strings for name/description.
    raise ValueError(f"unquoted scalar not allowed (use a double-quoted "
                     f"string): {raw!r}")


def parse_frontmatter(text):
    """Parse frontmatter. Return (ordered mapping, body).

    Values are typed (str/bool/None). Raises ValueError on any line that
    is not 'key: value', on duplicate keys, and on unsupported scalars.
    """
    raw, body = _split_frontmatter(text)
    mapping = {}
    for line in raw:
        stripped = line.strip()
        if stripped == "" or stripped.startswith("#"):
            continue
        key, value = _split_key_value(line)
        if key is None:
            raise ValueError(f"line is not 'key: value': {line!r}")
        key = key.strip()
        if not key:
            raise ValueError(f"empty key in line: {line!r}")
        if key in mapping:
            raise ValueError(f"duplicate key: {key!r}")
        mapping[key] = parse_scalar(value)
    return mapping, body


def emit_scalar(value):
    """Emit a typed Python scalar as frontmatter text."""
    if isinstance(value, bool):
        return "true" if value else "false"
    if value is None:
        return "null"
    if isinstance(value, str):
        return json.dumps(value)
    raise ValueError(f"cannot emit scalar of type {type(value).__name__}")


def emit_frontmatter(mapping):
    """Emit an ordered mapping as fenced frontmatter text.

    Top-level values may be scalars or one-level nested mappings. Nested
    mappings are emitted with two-space indentation and scalar values.
    """
    lines = ["---"]
    for key, value in mapping.items():
        if isinstance(value, dict):
            lines.append(f"{key}:")
            for nkey, nvalue in value.items():
                lines.append(f"  {nkey}: {emit_scalar(nvalue)}")
        else:
            lines.append(f"{key}: {emit_scalar(value)}")
    lines.append("---")
    return "\n".join(lines) + "\n"