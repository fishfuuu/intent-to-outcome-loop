"""Contract tests for the optional engineering-companion skill pack.

Standard library only. Checks pack structure and distribution boundaries,
not prompt wording of upstream snapshots.
"""

from __future__ import annotations

import json
import re
import unittest
from pathlib import Path

PACK_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = PACK_ROOT.parent.parent

EXPECTED = [
    "grilling",
    "domain-modeling",
    "tdd",
    "code-review",
    "codebase-design",
    "improve-codebase-architecture",
]
SNAPSHOTS = {
    "grilling",
    "domain-modeling",
    "tdd",
    "codebase-design",
    "improve-codebase-architecture",
}
FORKS = {"code-review"}
UPSTREAM_SNAPSHOT_COMMIT = "c55ee46073ed923f86ce59a5eb3b6d895095d1b7"
OLD_SNAPSHOT_COMMIT = "2ab958093e83e0ec752e6c1c5932da465bf23e0c"


def _frontmatter_name(text: str) -> str:
    match = re.search(r"^name:\s*[\"']?([^\"'\r\n]+)[\"']?\s*$", text, re.M)
    if not match:
        raise AssertionError("frontmatter name missing")
    return match.group(1).strip()


class EngineeringCompanionTests(unittest.TestCase):
    def test_pack_files_exist(self):
        self.assertTrue((PACK_ROOT / "README.md").is_file())
        self.assertTrue((PACK_ROOT / "pack-manifest.json").is_file())
        self.assertTrue((PACK_ROOT / "THIRD_PARTY_NOTICES.md").is_file())

    def test_exactly_six_expected_skill_directories(self):
        skills_dir = PACK_ROOT / "skills"
        names = sorted(p.name for p in skills_dir.iterdir() if p.is_dir())
        self.assertEqual(names, sorted(EXPECTED))

    def test_frontmatter_names_match_directories_and_are_unique(self):
        seen = []
        for name in EXPECTED:
            text = (PACK_ROOT / "skills" / name / "SKILL.md").read_text(encoding="utf-8")
            fm_name = _frontmatter_name(text)
            self.assertEqual(fm_name, name)
            seen.append(fm_name)
        self.assertEqual(len(seen), len(set(seen)))

    def test_not_in_seven_core_or_skillset(self):
        skillset = json.loads((REPO_ROOT / "skillset.json").read_text(encoding="utf-8"))
        core_names = [s["name"] for s in skillset["skills"]]
        self.assertEqual(len(core_names), 7)
        for name in EXPECTED:
            self.assertNotIn(name, core_names)
            self.assertFalse((REPO_ROOT / "skills" / name).exists())

    def test_manifest_optional_and_provenance(self):
        manifest = json.loads((PACK_ROOT / "pack-manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["pack_name"], "engineering-companion")
        self.assertIs(manifest["installed"], False)
        by_name = {s["name"]: s for s in manifest["skills"]}
        self.assertEqual(set(by_name), set(EXPECTED))
        for name in SNAPSHOTS:
            self.assertEqual(by_name[name]["provenance"], "upstream-snapshot")
            self.assertEqual(by_name[name]["upstream_repository"], "mattpocock/skills")
            self.assertEqual(by_name[name]["upstream_commit"], UPSTREAM_SNAPSHOT_COMMIT)
        fork = by_name["code-review"]
        self.assertEqual(fork["provenance"], "intentional-fork")
        self.assertEqual(fork["upstream_commit"], UPSTREAM_SNAPSHOT_COMMIT)
        self.assertIn("issue-tracker", fork["local_reason"])
        pack_text = (PACK_ROOT / "pack-manifest.json").read_text(encoding="utf-8")
        readme = (PACK_ROOT / "README.md").read_text(encoding="utf-8")
        notices = (PACK_ROOT / "THIRD_PARTY_NOTICES.md").read_text(encoding="utf-8")
        for blob in (pack_text, readme, notices):
            self.assertIn(UPSTREAM_SNAPSHOT_COMMIT, blob)
            self.assertNotIn(OLD_SNAPSHOT_COMMIT, blob)

    def test_code_review_has_no_runtime_matt_setup_dependency(self):
        text = (PACK_ROOT / "skills" / "code-review" / "SKILL.md").read_text(encoding="utf-8")
        self.assertNotIn("tell the user to run `/setup-matt-pocock-skills`", text)
        self.assertNotIn("If `docs/agents/issue-tracker.md` is missing", text)
        self.assertNotIn("fetched via the workflow in `docs/agents/issue-tracker.md`", text)
        self.assertIn("has no dependency on", text)
        self.assertIn("Missing Matt tracker config must not block this review.", text)

    def test_third_party_notice_names_snapshots_and_fork(self):
        text = (PACK_ROOT / "THIRD_PARTY_NOTICES.md").read_text(encoding="utf-8")
        self.assertIn("Copyright (c) 2026 Matt Pocock", text)
        self.assertIn("mattpocock/skills", text)
        for name in SNAPSHOTS:
            self.assertIn(name, text)
        self.assertIn("code-review", text)
        self.assertIn("intentional fork", text.lower() + text)


if __name__ == "__main__":
    unittest.main()
