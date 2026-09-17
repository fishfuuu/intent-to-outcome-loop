"""Structural tests for the optional Pi host integration under hosts/pi/.

These pin the boundary the integration relies on: the Pi agents are
versioned here, are addressable as agents, and are never mistaken for Core
skills or swept into the Core markdown scan.

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

EXPECTED_AGENTS = [
    "browser-qa-agent",
    "change-architecture-reviewer",
    "code-reviewer",
    "execution-verifier",
    "independent-reviewer",
]

CORE_SKILL_COUNT = 7


FRONTMATTER_RE = re.compile(r"\A---\r?\n(.*?)\r?\n---\r?\n?(.*)\Z", re.DOTALL)


def read_agent(name):
    """Return (frontmatter, body) for a canonical Pi agent file.

    Deliberately not scripts/yaml_subset.py: that parser is the strict
    Core SKILL.md dialect, which allows only double-quoted scalars and
    exists to keep canonical frontmatter to `name` and `description`.
    Pi agent frontmatter is a richer host dialect (model, tools,
    thinking, acceptanceRole ...), so this reads the keys tolerantly
    instead of forcing host files through the Core dialect.
    """
    text = (AGENTS_DIR / f"{name}.md").read_text(encoding="utf-8")
    m = FRONTMATTER_RE.match(text)
    if m is None:
        return None, text
    frontmatter, body = m.group(1), m.group(2)
    fm = {}
    for line in frontmatter.splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        key, sep, value = line.partition(":")
        if not sep:
            continue
        fm[key.strip()] = value.strip().strip('"')
    return fm, body


class TestPiHostIntegration(unittest.TestCase):

    def test_readme_exists(self):
        self.assertTrue((HOSTS_PI / "README.md").is_file(),
                        "hosts/pi/README.md must exist")

    def test_canonical_agent_files_exist(self):
        found = sorted(p.stem for p in AGENTS_DIR.glob("*.md"))
        self.assertEqual(found, sorted(EXPECTED_AGENTS),
                         "hosts/pi/agents/ must hold exactly the five "
                         "canonical agent files")

    def test_each_agent_is_addressable(self):
        # Pi takes the agent name from frontmatter, so the declared name must
        # match the canonical filename and carry a usable description.
        for name in EXPECTED_AGENTS:
            with self.subTest(agent=name):
                fm, body = read_agent(name)
                self.assertIsInstance(fm, dict, f"{name}: unparseable frontmatter")
                self.assertEqual(fm.get("name"), name,
                                 f"{name}: frontmatter name must match filename")
                self.assertTrue(fm.get("description"),
                                f"{name}: frontmatter needs a description")
                self.assertTrue(body.strip(), f"{name}: agent body is empty")

    def test_agent_names_are_unique(self):
        declared = [read_agent(n)[0].get("name") for n in EXPECTED_AGENTS]
        self.assertEqual(len(declared), len(set(declared)))

    def test_code_reviewer_and_change_architecture_reviewer_stay_separate(self):
        # Guards against collapsing the two roles back into one file.
        code_fm, code_body = read_agent("code-reviewer")
        arch_fm, arch_body = read_agent("change-architecture-reviewer")
        self.assertNotEqual(code_fm["name"], arch_fm["name"])
        self.assertNotEqual(code_fm["description"], arch_fm["description"])
        self.assertNotEqual(code_body, arch_body)

    def test_host_agents_are_not_core_skills(self):
        data = json.loads((REPO_ROOT / "skillset.json").read_text(encoding="utf-8"))
        core = {entry["name"] for entry in data["skills"]}
        self.assertEqual(len(core), CORE_SKILL_COUNT)
        for name in EXPECTED_AGENTS:
            self.assertNotIn(name, core,
                             "host agents must not be declared as Core skills")
        on_disk = {p.name for p in (REPO_ROOT / "skills").iterdir() if p.is_dir()}
        self.assertEqual(on_disk, core,
                         "skills/ must hold exactly the declared Core skills")

    def test_host_agents_are_outside_the_core_markdown_scan(self):
        # validate.py scans README/AGENTS/CLAUDE, docs/ and skills/ only.
        # Host agent prompts must not be pulled into Core markdown checks or
        # the Core word budget.
        scanned = {rel for rel, _ in validate.iter_shipped_markdown()}
        self.assertEqual([rel for rel in scanned if rel.startswith("hosts/")], [],
                         "hosts/ must stay outside the shipped-markdown scan")


if __name__ == "__main__":
    unittest.main()
