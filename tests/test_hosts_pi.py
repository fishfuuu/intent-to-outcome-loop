"""Retirement invariants for the Pi host integration under hosts/pi/.

`hosts/pi/agents/` used to version five Pi agent definitions. That ownership
was retired: Pi Web's built-in Agent replaced the runtime those definitions
targeted, and the canonical profiles now live in the `pi-extensions`
repository.

These tests pin the retirement, so the old canonical claim, the deleted
definitions, and the retired `pi-subagents` frontmatter cannot quietly come
back. They assert what this repository must *not* do; they do not mirror the
Pi agent schema and do not read `pi-extensions`.

Standard library only. Read-only: no temporary directories are needed.
"""

import json
import re
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = REPO_ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

import validate  # noqa: E402

HOSTS_PI = REPO_ROOT / "hosts" / "pi"
AGENTS_DIR = HOSTS_PI / "agents"
README = HOSTS_PI / "README.md"

# The host agents this repository stopped owning.
RETIRED_AGENT_NAMES = [
    "browser-qa-agent",
    "change-architecture-reviewer",
    "code-reviewer",
    "execution-verifier",
    "independent-reviewer",
]

# Where those definitions live now. Referenced by repository name rather than
# by a local path, so nothing here is tied to one machine's checkout.
CANONICAL_REPO = "pi-extensions"
CANONICAL_AGENTS_PATH = "pi-extensions/agents"

CORE_SKILL_COUNT = 7

# Frontmatter keys of the retired `pi-subagents` agent dialect. The current
# runtime does not honor them, and no tool here reads or deploys them, so they
# are not an ITOL host contract. Pinned because the supported runtime proved
# it, not because this file mirrors Pi's schema: new legitimate Pi fields must
# keep working without editing this list.
RETIRED_PI_AGENT_FRONTMATTER_FIELDS = {
    "systemPromptMode",
    "inheritProjectContext",
    "inheritGlobalContext",
    "inheritSkills",
    "acceptanceRole",
    "completionGuard",
    "fallbackModels",
}

# A line that hands canonical ownership of the Pi agent definitions back to
# this repository. Scoped to one line so prose *about* the retirement, which
# necessarily names the old claim, does not trip it.
OWNERSHIP_CLAIM_RE = re.compile(
    r"this\s+(repository|repo|directory)\b[^.\n]{0,80}\bcanonical\b",
    re.IGNORECASE,
)

# The retired claim in the form it used to be written. Kept separately because
# it is short enough to read as a claim even without the word "this".
LEGACY_OWNERSHIP_CLAIM = "canonical source for these definitions"

FRONTMATTER_RE = re.compile(r"\A---\r?\n(.*?)\r?\n---\r?\n?(.*)\Z", re.DOTALL)


def frontmatter_keys(text):
    """Return the frontmatter keys of a markdown file, or an empty set."""
    match = FRONTMATTER_RE.match(text)
    if match is None:
        return set()
    keys = set()
    for line in match.group(1).splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        key, sep, _ = line.partition(":")
        if sep:
            keys.add(key.strip())
    return keys


class TestPiHostRetirement(unittest.TestCase):

    def test_readme_exists(self):
        self.assertTrue(README.is_file(),
                        "hosts/pi/README.md must exist as the retirement notice")

    def test_no_agent_definitions_are_versioned_here(self):
        # The directory itself may be absent; what must not return is a
        # definition. Pi Web treats every *.md in an agent directory as a
        # profile, so a stray file here is a profile someone will deploy.
        present = sorted(p.name for p in AGENTS_DIR.glob("*.md")) \
            if AGENTS_DIR.is_dir() else []
        self.assertEqual(
            present, [],
            "hosts/pi must not version Pi agent definitions again; the "
            f"canonical profiles live in {CANONICAL_AGENTS_PATH}")

    def test_readme_points_at_the_canonical_source(self):
        text = README.read_text(encoding="utf-8")
        self.assertIn(CANONICAL_REPO, text,
                      "hosts/pi/README.md must name the canonical source repository")
        self.assertIn(CANONICAL_AGENTS_PATH, text,
                      "hosts/pi/README.md must name the canonical profiles directory")
        self.assertIn("no longer owns or deploys", text,
                      "hosts/pi/README.md must state the retirement in its opening")
        for name in RETIRED_AGENT_NAMES:
            with self.subTest(agent=name):
                self.assertNotIn(
                    f"| `{name}` |", text,
                    f"hosts/pi/README.md must not table {name} as an agent this "
                    "repository provides")

    def test_readme_does_not_claim_canonical_ownership(self):
        for number, line in enumerate(README.read_text(encoding="utf-8").splitlines(),
                                      start=1):
            with self.subTest(line=number):
                self.assertIsNone(
                    OWNERSHIP_CLAIM_RE.search(line),
                    f"hosts/pi/README.md:{number} claims this repository is canonical")
                self.assertNotIn(
                    LEGACY_OWNERSHIP_CLAIM, line,
                    f"hosts/pi/README.md:{number} restores the retired claim")

    def test_no_retired_subagent_schema_ships_as_a_host_contract(self):
        # Guards reintroduction of a profile file, not the README: the README
        # names these fields on purpose, in prose, as the reason for the
        # retirement.
        for path in sorted(HOSTS_PI.rglob("*.md")):
            with self.subTest(path=path.name):
                keys = frontmatter_keys(path.read_text(encoding="utf-8"))
                found = sorted(RETIRED_PI_AGENT_FRONTMATTER_FIELDS.intersection(keys))
                self.assertEqual(
                    found, [],
                    f"{path.name}: retired pi-subagents frontmatter fields: {found}")

    def test_retired_agent_names_are_not_core_skills(self):
        data = json.loads((REPO_ROOT / "skillset.json").read_text(encoding="utf-8"))
        core = {entry["name"] for entry in data["skills"]}
        self.assertEqual(len(core), CORE_SKILL_COUNT)
        for name in RETIRED_AGENT_NAMES:
            self.assertNotIn(name, core,
                             f"{name}: a retired host agent must not become a Core skill")
        on_disk = {p.name for p in (REPO_ROOT / "skills").iterdir() if p.is_dir()}
        self.assertEqual(on_disk, core,
                         "skills/ must hold exactly the declared Core skills")

    def test_hosts_pi_is_outside_the_core_markdown_scan(self):
        # validate.py scans README/AGENTS/CLAUDE, docs/ and skills/ only.
        # Host prompts must not be pulled into Core markdown checks or the
        # Core word budget.
        scanned = {rel for rel, _ in validate.iter_shipped_markdown()}
        self.assertEqual([rel for rel in scanned if rel.startswith("hosts/")], [],
                         "hosts/ must stay outside the shipped-markdown scan")


if __name__ == "__main__":
    unittest.main()
