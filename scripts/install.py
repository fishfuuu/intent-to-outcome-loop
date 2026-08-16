#!/usr/bin/env python3
"""Install Intent to Outcome Loop skills into a host's skill directory.

Standard library only. Supports Codex and Claude Code, user and project
scope, dry-run, and an explicit destination for tests and non-standard hosts.

Usage:
    python scripts/install.py --target codex --scope user
    python scripts/install.py --target claude --scope project
    python scripts/install.py --target both --destination <dir>
    python scripts/install.py --target codex --scope user --dry-run
"""

import argparse
import json
import os
import shutil
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS_DIR))
import yaml_subset  # noqa: E402

SKILLSET = REPO_ROOT / "skillset.json"

# Skills that require host-specific frontmatter tweaks.
# evaluate must be user-only on every host that supports it. The override
# value is a real Python bool so the emitter writes the bare YAML word
# `true`, not the quoted string "true".
CLAUDE_FRONTMATTER_OVERRIDES = {
    "evaluate": {"disable-model-invocation": True},
}


def load_skillset():
    with open(SKILLSET, encoding="utf-8") as f:
        return json.load(f)


def host_install_dir(host, scope, explicit_destination):
    """Resolve where a host's skills live for the given scope.

    - user scope: the current user's home skill directory.
    - project scope: the *current project's* directory (cwd), not the
      toolkit's location. We never infer the target project from the
      toolkit's parent directory.
    """
    if explicit_destination is not None:
        return Path(explicit_destination)

    home = Path(os.path.expanduser("~"))
    cwd = Path(os.getcwd())
    if host == "codex":
        if scope == "user":
            return home / ".agents" / "skills"
        if scope == "project":
            return cwd / ".agents" / "skills"
    if host == "claude":
        if scope == "user":
            return home / ".claude" / "skills"
        if scope == "project":
            return cwd / ".claude" / "skills"
    raise ValueError(f"Unknown host/scope: {host}/{scope}")


def load_canonical_skill(source_rel):
    """Return (frontmatter_mapping, body) read from the canonical SKILL.md.

    Frontmatter is parsed through the strict YAML subset so that a
    host-specific field can be injected by re-emitting valid YAML, not by
    string concatenation.
    """
    path = REPO_ROOT / source_rel
    text = path.read_text(encoding="utf-8")
    fm, body = yaml_subset.parse_frontmatter(text)
    return fm, body


def build_installed_skill(host, skill_name, source_rel):
    """Produce the SKILL.md text for an install, applying host tweaks.

    For Claude, host-specific frontmatter fields are added by re-emitting
    the parsed mapping as valid YAML, so the result is always real YAML
    regardless of quoting in the canonical file.
    """
    fm, body = load_canonical_skill(source_rel)
    if host == "claude" and skill_name in CLAUDE_FRONTMATTER_OVERRIDES:
        for k, v in CLAUDE_FRONTMATTER_OVERRIDES[skill_name].items():
            fm[k] = v
    return yaml_subset.emit_frontmatter(fm) + body


def install_one_skill(host, install_dir, skill_entry, dry_run):
    """Install a single skill directory into install_dir. Returns a report."""
    skill_name = skill_entry["name"]
    source_rel = skill_entry["source"]
    # source is skills/<name>/SKILL.md; the skill dir is its parent.
    source_skill_dir = (REPO_ROOT / source_rel).parent
    dest_skill_dir = install_dir / skill_name

    files_written = []
    files_overwritten = []

    for src_path in sorted(source_skill_dir.rglob("*")):
        if not src_path.is_file():
            continue
        rel = src_path.relative_to(source_skill_dir)
        dest_path = dest_skill_dir / rel
        if dest_path.exists():
            files_overwritten.append(str(rel))
        files_written.append(str(rel))
        if dry_run:
            continue
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        if rel == Path("SKILL.md"):
            dest_path.write_text(
                build_installed_skill(host, skill_name, source_rel),
                encoding="utf-8",
            )
        else:
            shutil.copy2(src_path, dest_path)

    return {
        "skill": skill_name,
        "dest": str(dest_skill_dir),
        "written": files_written,
        "overwritten": files_overwritten,
    }


def install_target(host, scope, dry_run, explicit_destination, subdir=None):
    if host not in ("codex", "claude"):
        raise ValueError(f"Unsupported host for install: {host}. "
                         "OpenCode and Grok are documented-experimental in v0.1.")
    base_dir = host_install_dir(host, scope, explicit_destination)
    install_dir = base_dir / subdir if subdir else base_dir
    skillset = load_skillset()
    # Install only for hosts whose support level is supported or
    # experimental. OpenCode and Grok are experimental in v0.1 and are
    # not valid --target values (install_target rejects them above), but
    # the manifest still records their level for documentation.
    reports = []
    for entry in skillset["skills"]:
        if host not in entry.get("hosts", {}):
            continue
        reports.append(install_one_skill(host, install_dir, entry, dry_run))
    return install_dir, reports


def main(argv=None):
    p = argparse.ArgumentParser(description="Install Intent to Outcome Loop skills.")
    p.add_argument("--target", choices=["codex", "claude", "both"], required=True,
                   help="Which host to install for.")
    p.add_argument("--scope", choices=["user", "project"], default="user",
                   help="Install scope. Ignored when --destination is set.")
    p.add_argument("--dry-run", action="store_true",
                   help="Report what would happen without writing or deleting.")
    p.add_argument("--destination", metavar="DIR",
                   help="Explicit install directory. Used for tests and "
                        "non-standard hosts; overrides scope-based resolution.")
    args = p.parse_args(argv)

    # When installing both hosts into a single explicit destination, give
    # each host its own subdirectory so the two views never overwrite each
    # other (no "Claude-last-wins"). Single-target installs write directly
    # into the destination, preserving the "install exactly here" meaning.
    use_subdirs = args.target == "both" and args.destination is not None

    hosts = ["codex", "claude"] if args.target == "both" else [args.target]
    all_reports = {}
    final_dirs = {}
    for host in hosts:
        subdir = host if use_subdirs else None
        install_dir, reports = install_target(
            host, args.scope, args.dry_run, args.destination, subdir=subdir
        )
        all_reports[host] = reports
        final_dirs[host] = install_dir

    if args.dry_run:
        print("[dry-run] No files were written or deleted.")

    for host in hosts:
        print(f"\n# {host} -> {final_dirs[host]}")
        for r in all_reports[host]:
            print(f"  skill: {r['skill']}")
            print(f"    dest: {r['dest']}")
            if r["overwritten"]:
                print(f"    would overwrite: {', '.join(r['overwritten'])}")
            print(f"    files: {', '.join(r['written'])}")

    # The installer never deletes unrelated skills in the target directory.
    # It only writes the skills it owns. This is intentional and documented.
    return 0


if __name__ == "__main__":
    sys.exit(main())