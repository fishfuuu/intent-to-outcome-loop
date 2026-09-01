#!/usr/bin/env python3
"""Validate the Intent to Outcome Loop repository.

Standard library only. Checks:

- skillset.json is parseable and internally consistent.
- the manifest matches the skills directory.
- every skill has a SKILL.md with valid YAML frontmatter (parsed by a
  strict YAML subset, not a naive colon split).
- canonical frontmatter contains exactly `name` and `description`.
- name matches the directory; description is non-empty and free of
  angle brackets and stray colons that break YAML.
- word budgets per skill and across all skills, plus per-line density.
- machine-specific absolute paths appear in no shipped markdown.
- all relative markdown links in shipped markdown resolve.
- the evaluate Codex policy file has the required nested structure.
- no unexpected build artifacts ship.

Usage:
    python scripts/validate.py
"""

import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS_DIR))
import yaml_subset  # noqa: E402

SKILLS_DIR = REPO_ROOT / "skills"
SKILLSET = REPO_ROOT / "skillset.json"

# Word budgets replace line budgets to prevent density creep.
MAX_WORDS_PER_SKILL = 2000  # reviewed-change ceiling; others target ~1300
MAX_TOTAL_SKILL_WORDS = 9200
MAX_WORDS_PER_LINE = 90  # force scannability; prevent 185-word paragraphs

# Canonical SKILL.md frontmatter must contain exactly these keys.
CANONICAL_FRONTMATTER_KEYS = {"name", "description"}

# The set of host-specific keys that are allowed only in installed
# copies, never in canonical files.
HOST_SPECIFIC_FRONTMATTER_KEYS = {"disable-model-invocation"}

# Machine-specific absolute path patterns. Any match in shipped markdown
# is a hard error. Drive letters and home roots, plus the specific old
# repo path, cover the cases this repo must avoid.
LOCAL_PATH_PATTERNS = [
    re.compile(r"D:\\agent-workflow", re.IGNORECASE),
    re.compile(r"C:\\Users\\Administrator", re.IGNORECASE),
    # Any Windows drive-letter absolute path.
    re.compile(r"\b[A-Za-z]:\\"),
    # Any POSIX home or known-machine path.
    re.compile(r"/Users/[A-Za-z0-9_-]+/"),
    re.compile(r"/home/[A-Za-z0-9_-]+/"),
]

errors = []
warnings = []


def err(msg):
    errors.append(msg)


def warn(msg):
    warnings.append(msg)


# ---------------------------------------------------------------------------

def check_skillset():
    if not SKILLSET.exists():
        err("skillset.json not found")
        return None
    try:
        data = json.loads(SKILLSET.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        err(f"skillset.json not parseable: {e}")
        return None
    if "skills" not in data or not isinstance(data["skills"], list):
        err("skillset.json missing 'skills' list")
        return None
    # Top-level hosts map for documentation of support levels.
    if "hosts" not in data or not isinstance(data["hosts"], dict):
        err("skillset.json missing top-level 'hosts' map")
    return data


def check_manifest_entries(skillset):
    declared = {}
    for s in skillset["skills"]:
        if not isinstance(s, dict):
            err("skillset entry is not an object")
            continue
        name = s.get("name")
        for field in ("name", "display_name", "invocation_mode",
                      "hosts", "source"):
            if field not in s:
                err(f"skillset entry '{name or '?'}' missing field '{field}'")
        if name:
            declared[name] = s
        # Reject the legacy schema field.
        if "supported_hosts" in s:
            err(f"skillset entry '{name}': uses legacy 'supported_hosts'; "
                "use the 'hosts' map instead")
        # Validate the hosts map values.
        hosts = s.get("hosts", {})
        if isinstance(hosts, dict):
            for host, level in hosts.items():
                if level not in ("supported", "experimental"):
                    err(f"skillset entry '{name}': host '{host}' has "
                        f"invalid support level '{level}'")
    return set(declared.keys())


def check_manifest_matches_dir(declared):
    on_disk = {p.name for p in SKILLS_DIR.iterdir() if p.is_dir()}
    if declared - on_disk:
        err(f"Declared skills missing on disk: {sorted(declared - on_disk)}")
    if on_disk - declared:
        err(f"Skills on disk not in manifest: {sorted(on_disk - declared)}")


def check_skill_files(skillset):
    total_words = 0
    word_counts = {}
    for s in skillset["skills"]:
        name = s["name"]
        src = REPO_ROOT / s["source"]
        if not src.exists():
            err(f"{name}: SKILL.md missing at {s['source']}")
            continue
        text = src.read_text(encoding="utf-8")
        lines = text.split("\n")
        words = sum(len(line.split()) for line in lines)
        word_counts[name] = words
        total_words += words
        if words > MAX_WORDS_PER_SKILL:
            err(f"{name}: {words} words exceeds budget of {MAX_WORDS_PER_SKILL}")

        # Check per-line density to enforce scannability.
        for i, line in enumerate(lines, 1):
            line_words = len(line.split())
            if line_words > MAX_WORDS_PER_LINE:
                err(f"{name}: line {i} has {line_words} words, "
                    f"exceeds per-line limit of {MAX_WORDS_PER_LINE}")

        # Parse frontmatter through the strict YAML subset. A parse
        # failure means the frontmatter is not valid YAML.
        try:
            fm, body = yaml_subset.parse_frontmatter(text)
        except ValueError as e:
            err(f"{name}: invalid frontmatter YAML: {e}")
            continue

        # Canonical frontmatter must contain exactly name and description.
        fm_keys = set(fm.keys())
        if fm_keys != CANONICAL_FRONTMATTER_KEYS:
            extra = fm_keys - CANONICAL_FRONTMATTER_KEYS
            missing = CANONICAL_FRONTMATTER_KEYS - fm_keys
            if missing:
                err(f"{name}: frontmatter missing keys {sorted(missing)}")
            if extra:
                err(f"{name}: canonical frontmatter has extra keys "
                    f"{sorted(extra)}; only name and description allowed")

        if fm.get("name") != name:
            err(f"{name}: frontmatter name '{fm.get('name')}' != dir name '{name}'")
        desc = fm.get("description", "")
        # A description must be a non-empty string. Reject non-string
        # values (e.g. a bare true/123) explicitly and skip the
        # string-only checks below, which would crash on a non-string.
        if not isinstance(desc, str):
            err(f"{name}: description must be a string, "
                f"got {type(desc).__name__}")
            continue
        if not desc.strip():
            err(f"{name}: description is empty")
            continue

        # Description must not contain angle brackets (Codex rule).
        if "<" in desc or ">" in desc:
            err(f"{name}: description contains angle brackets")

        for key in HOST_SPECIFIC_FRONTMATTER_KEYS:
            if key in fm:
                err(f"{name}: canonical frontmatter must not contain "
                    f"host-specific key '{key}'")

    if total_words > MAX_TOTAL_SKILL_WORDS:
        err(f"Total skill words {total_words} exceeds budget "
            f"of {MAX_TOTAL_SKILL_WORDS}")
    return word_counts, total_words


def check_local_paths_in_file(rel_label, text):
    for pat in LOCAL_PATH_PATTERNS:
        for m in pat.finditer(text):
            err(f"{rel_label}: contains machine-specific path '{m.group(0)}'")


def check_doc_links_in_file(rel_label, source_file):
    text = source_file.read_text(encoding="utf-8")
    link_base = source_file.parent
    for m in re.finditer(r"\]\(([^)]+)\)", text):
        target = m.group(1)
        if target.startswith(("http://", "https://", "#", "mailto:")):
            continue
        if target.startswith(".agent-delivery/"):
            continue  # runtime path, documented, not in repo
        resolved = (link_base / target).resolve()
        try:
            resolved.relative_to(REPO_ROOT.resolve())
        except ValueError:
            err(f"{rel_label}: link escapes repo root: {target}")
            continue
        if not resolved.exists():
            err(f"{rel_label}: broken doc link: {target}")


def iter_shipped_markdown():
    """Yield (rel_label, Path) for every shipped markdown file."""
    roots = [
        REPO_ROOT / "README.md",
        REPO_ROOT / "AGENTS.md",
        REPO_ROOT / "CLAUDE.md",
    ]
    # docs/ is scanned recursively so a nested markdown file cannot bypass
    # the machine-path and link checks.
    if (REPO_ROOT / "docs").exists():
        roots += sorted((REPO_ROOT / "docs").rglob("*.md"))
    roots += sorted((REPO_ROOT / "skills").rglob("*.md"))
    for p in roots:
        if not p.exists():
            continue
        yield p.relative_to(REPO_ROOT).as_posix(), p


def check_all_markdown():
    """Scan every shipped markdown file for local paths and doc links."""
    for rel, path in iter_shipped_markdown():
        text = path.read_text(encoding="utf-8")
        check_local_paths_in_file(rel, text)
        check_doc_links_in_file(rel, path)


def check_evaluate_policy():
    policy = SKILLS_DIR / "evaluate" / "agents" / "openai.yaml"
    if not policy.exists():
        err("evaluate: missing Codex policy at skills/evaluate/agents/openai.yaml")
        return
    text = policy.read_text(encoding="utf-8")
    # Parse a minimal YAML mapping-with-nesting for the policy file. We
    # only need to prove structure and hierarchy, not search strings.
    parsed = parse_policy_yaml(text)
    if parsed is None:
        err("evaluate: openai.yaml is not valid YAML")
        return
    policy_map = parsed.get("policy")
    if not isinstance(policy_map, dict):
        err("evaluate: openai.yaml missing top-level 'policy' mapping")
        return
    value = policy_map.get("allow_implicit_invocation")
    if value is not False:
        err("evaluate: openai.yaml policy.allow_implicit_invocation "
            "must be the boolean false")
        return


def parse_policy_yaml(text):
    """Parse the small nesting used by the evaluate policy file.

    Supports a top-level mapping where values are either scalars or
    nested mappings. Returns a dict or None on failure. This is not a
    general YAML parser; it is a strict check of the documented policy
    structure.
    """
    result = {}
    current_key = None
    current_map = None
    for raw in text.splitlines():
        line = raw.rstrip()
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        indent = len(line) - len(line.lstrip(" "))
        stripped = line.strip()
        if ":" not in stripped:
            return None
        key, _, value = stripped.partition(":")
        key = key.strip()
        value = value.strip()
        if indent == 0:
            if value == "":
                current_key = key
                current_map = {}
                result[key] = current_map
            else:
                result[key] = parse_yaml_scalar(value)
                current_key = None
                current_map = None
        else:
            if current_map is None:
                return None
            current_map[key] = parse_yaml_scalar(value)
    return result


def parse_yaml_scalar(value):
    if value in ("false", "true", "null"):
        return {"false": False, "true": True, "null": None}[value]
    return value


def check_cache_files():
    stray_patterns = (".pytest_cache", "*.egg-info", "dist", "build")
    for pat in stray_patterns:
        for p in REPO_ROOT.glob(f"**/{pat}"):
            if ".git" in p.parts:
                continue
            err(f"stray cache/build artifact: {p.relative_to(REPO_ROOT)}")


def main():
    skillset = check_skillset()
    if skillset is not None:
        declared = check_manifest_entries(skillset)
        if declared is not None:
            check_manifest_matches_dir(declared)
        check_skill_files(skillset)
        check_evaluate_policy()
    check_cache_files()
    check_all_markdown()

    for w in warnings:
        print(f"WARN: {w}", file=sys.stderr)

    if errors:
        print("\nVALIDATION FAILED", file=sys.stderr)
        for e in errors:
            print(f"  ERROR: {e}", file=sys.stderr)
        return 1

    print("VALIDATION OK")
    if skillset is not None and "skills" in skillset:
        print(f"  skills: {len(skillset['skills'])}")
    return 0


if __name__ == "__main__":
    sys.exit(main())