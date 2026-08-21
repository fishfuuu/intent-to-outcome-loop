"""Contract and boundary tests for the internal-enterprise-companion skill pack.

Standard library only. Exercises pack manifest integrity, skill frontmatter,
and core material delivery contracts without brittle full-text overfitting.
"""

from __future__ import annotations

import json
import re
import sys
import unittest
from pathlib import Path

PACK_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = PACK_ROOT.parent.parent
SCRIPTS_DIR = REPO_ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import yaml_subset  # noqa: E402

EXPECTED_SKILLS = {
    "observe-real-work",
    "discover-business-contract",
    "worth-building-now",
    "bounded-validation",
    "smallest-real-deployment",
    "adopted-not-released",
}

FORBIDDEN_EXTERNAL_SKILLS = {
    "change-three-roles",
    "read-old-write-new",
    "eval-driven-quality",
}

LOCAL_PATH_PATTERNS = [
    re.compile(r"D:\\agent-workflow", re.IGNORECASE),
    re.compile(r"C:\\Users\\Administrator", re.IGNORECASE),
    re.compile(r"\b[A-Za-z]:\\"),
    re.compile(r"/Users/[A-Za-z0-9_-]+/"),
    re.compile(r"/home/[A-Za-z0-9_-]+/"),
]


class TestInternalEnterpriseCompanionPack(unittest.TestCase):

    def setUp(self):
        self.manifest_path = PACK_ROOT / "pack-manifest.json"
        self.assertTrue(self.manifest_path.exists(), "pack-manifest.json missing")
        self.manifest = json.loads(self.manifest_path.read_text(encoding="utf-8"))

    def test_pack_manifest_schema(self):
        self.assertEqual(self.manifest.get("pack_name"), "internal-enterprise-companion")
        self.assertIn("version", self.manifest)
        self.assertIn("status", self.manifest)
        self.assertIn("skills", self.manifest)
        self.assertIsInstance(self.manifest["skills"], list)
        self.assertIs(self.manifest.get("installed"), False)

    def test_manifest_matches_disk_skills(self):
        declared_names = {s["name"] for s in self.manifest["skills"]}
        self.assertEqual(declared_names, EXPECTED_SKILLS)

        skills_dir = PACK_ROOT / "skills"
        self.assertTrue(skills_dir.exists(), "skills directory missing")
        disk_dirs = {p.name for p in skills_dir.iterdir() if p.is_dir()}
        self.assertEqual(disk_dirs, EXPECTED_SKILLS)

    def test_external_fde_skills_not_redistributed(self):
        declared_names = {s["name"] for s in self.manifest["skills"]}
        for forbidden in FORBIDDEN_EXTERNAL_SKILLS:
            self.assertNotIn(forbidden, declared_names)
            self.assertFalse((PACK_ROOT / "skills" / forbidden).exists(),
                             f"External skill {forbidden} must not be present in pack")

    def test_all_skills_have_valid_skill_md_and_frontmatter(self):
        for s in self.manifest["skills"]:
            name = s["name"]
            entry_path = PACK_ROOT / s["entry"]
            self.assertTrue(entry_path.exists(), f"{name}: SKILL.md missing at {entry_path}")

            text = entry_path.read_text(encoding="utf-8")
            fm, body = yaml_subset.parse_frontmatter(text)

            self.assertEqual(set(fm.keys()), {"name", "description"},
                             f"{name}: canonical frontmatter must only have name and description")
            self.assertEqual(fm["name"], name)
            self.assertTrue(isinstance(fm["description"], str) and len(fm["description"].strip()) > 0)
            self.assertNotIn("<", fm["description"], f"{name}: description must not contain angle brackets")
            self.assertNotIn(">", fm["description"], f"{name}: description must not contain angle brackets")

    def test_discover_business_contract_contracts(self):
        text = (PACK_ROOT / "skills" / "discover-business-contract" / "SKILL.md").read_text(encoding="utf-8")

        # Material UNRESOLVED does not mean engineering-ready
        self.assertIn("Material UNRESOLVED still exists", text)
        self.assertIn("DO NOT mark affected behaviors as engineering-ready", text)
        self.assertIn("DO NOT let engineering choose or guess an answer", text)

        # Evidence discipline: OBSERVED does not substitute for CONFIRMED future behavior
        self.assertIn("OBSERVED", text)
        self.assertIn("CONFIRMED", text)
        self.assertIn("does not substitute for authorized confirmation", text)

        # Technical implementation strictly handed off, not designed inside skill
        self.assertIn("Strictly forbidden in this skill: designing database tables", text)
        self.assertIn("task-router", text)

    def test_observe_real_work_contracts(self):
        text = (PACK_ROOT / "skills" / "observe-real-work" / "SKILL.md").read_text(encoding="utf-8")

        # Workaround is evidence, not by itself system failure
        self.assertIn("not by itself a system failure", text)
        self.assertIn("none is a valid result", text)

        # Observation establishes today, not tomorrow's policy
        self.assertIn("Observation establishes what happens today", text)
        self.assertIn("does not by itself authorize what should happen tomorrow", text)
        self.assertIn("Do not invent a product, Agent, or architecture", text)

    def test_worth_building_now_contracts(self):
        text = (PACK_ROOT / "skills" / "worth-building-now" / "SKILL.md").read_text(encoding="utf-8")

        # Three questions + worthiness check
        self.assertIn("Pain.", text)
        self.assertIn("Impact.", text)
        self.assertIn("Feasibility.", text)
        self.assertIn("Worthiness.", text)

        # Allows Not now verdict
        self.assertIn("Not now", text)
        self.assertIn("Worth validating", text)

        # Missing owner blocks formal delivery/validation claims
        self.assertIn("Owner rule.", text)

    def test_bounded_validation_contracts(self):
        text = (PACK_ROOT / "skills" / "bounded-validation" / "SKILL.md").read_text(encoding="utf-8")

        # Five boundings
        self.assertIn("Name the claim.", text)
        self.assertIn("Name the referee.", text)
        self.assertIn("Name real-enough evidence.", text)
        self.assertIn("Name the next judgment moment.", text)
        self.assertIn("Name four outcomes in advance", text)

        # Rejects synthetic/mock data as business value proof
        self.assertIn("Synthetic, mock, cherry-picked demo data", text)
        self.assertTrue("cannot prove business value" in text or "**cannot** prove business value" in text)

    def test_smallest_real_deployment_contracts(self):
        text = (PACK_ROOT / "skills" / "smallest-real-deployment" / "SKILL.md").read_text(encoding="utf-8")

        # One path, real-enough data, business user operates/judges
        self.assertIn("One path, full depth.", text)
        self.assertIn("Real-enough data for the claim.", text)
        self.assertIn("Business person does the thing.", text)

        # Does not implement code; hands to task-router
        self.assertIn("Do not implement here.", text)
        self.assertIn("hand implementation to `task-router`", text)

    def test_adopted_not_released_contracts(self):
        text = (PACK_ROOT / "skills" / "adopted-not-released" / "SKILL.md").read_text(encoding="utf-8")

        # Rejects vanity metrics
        self.assertIn("Ban vanity evidence.", text)
        self.assertIn("Account count, training sign-in, UAT ticks", text)

        # Evaluates natural rhythm without ongoing chasing
        self.assertIn("natural rhythm", text)
        self.assertIn("Exit test.", text)

        # Standalone conditional handoff when external skills unavailable
        self.assertIn("if `change-three-roles` is available", text)
        self.assertIn("if `eval-driven-quality` is available", text)
        self.assertIn("stop without fabricating the external skill", text)

    def test_pack_readme_installability_truth(self):
        readme_text = (PACK_ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn("Installation and Packaging", readme_text)
        self.assertIn("scripts/install.py", readme_text)
        self.assertIn("Core install surface", readme_text)

    def test_expression_hygiene_guard(self):
        """Guard against re-introducing unique translated metaphors and legacy FDE skill slugs."""
        banned_phrases = [
            "not dead enough to stop",
            "not alive enough to commit",
            "## Adapted from",
            "poc-graveyard-refusal",
            "activation-not-launch",
            "psf-three-gates",
            "shadow-work-observation",
            "minimum-viable-deployment",
        ]
        for md_path in PACK_ROOT.rglob("*.md"):
            text = md_path.read_text(encoding="utf-8")
            for phrase in banned_phrases:
                self.assertNotIn(
                    phrase,
                    text,
                    f"{md_path.relative_to(PACK_ROOT)} contains banned legacy expression: {phrase!r}"
                )

    def test_no_machine_paths_in_pack_markdown(self):
        for md_path in PACK_ROOT.rglob("*.md"):
            text = md_path.read_text(encoding="utf-8")
            for pat in LOCAL_PATH_PATTERNS:
                self.assertIsNone(pat.search(text),
                                  f"{md_path.relative_to(PACK_ROOT)} contains local machine path: {pat.pattern}")


if __name__ == "__main__":
    unittest.main()
