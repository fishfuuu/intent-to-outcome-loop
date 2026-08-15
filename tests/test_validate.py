"""Tests for scripts/validate.py. Standard library only, temp dirs only."""

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = REPO_ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

import validate  # noqa: E402
import yaml_subset  # noqa: E402


def run_validate():
    """Run validate.main() and return its exit code."""
    return validate.main()


class TestValidate(unittest.TestCase):

    def setUp(self):
        # The validator appends to module-level lists; clear them so one
        # test's errors do not leak into another.
        validate.errors = []
        validate.warnings = []

    def test_validate_passes_on_clean_repo(self):
        code = run_validate()
        self.assertEqual(code, 0,
                         "validator failed on a clean repo; errors: "
                         + "; ".join(validate.errors))

    def test_skillset_parseable_and_seven_skills(self):
        data = json.loads((REPO_ROOT / "skillset.json")
                          .read_text(encoding="utf-8"))
        self.assertIn("skills", data)
        self.assertEqual(len(data["skills"]), 7)
        # New schema: per-skill hosts map + top-level hosts map.
        self.assertIn("hosts", data)
        for s in data["skills"]:
            self.assertIn("hosts", s)
            self.assertNotIn("supported_hosts", s)

    def test_line_budgets(self):
        total = 0
        for skill in (REPO_ROOT / "skills").iterdir():
            if not skill.is_dir():
                continue
            text = (skill / "SKILL.md").read_text(encoding="utf-8")
            lines = text.count("\n") + (0 if text.endswith("\n") else 1)
            self.assertLessEqual(lines, validate.MAX_LINES_PER_SKILL,
                                 f"{skill.name}: {lines} lines")
            total += lines
        self.assertLessEqual(total, validate.MAX_TOTAL_SKILL_LINES,
                             f"total {total} lines")

    def test_canonical_frontmatter_exactly_name_description(self):
        for skill in (REPO_ROOT / "skills").iterdir():
            if not skill.is_dir():
                continue
            text = (skill / "SKILL.md").read_text(encoding="utf-8")
            fm, _ = yaml_subset.parse_frontmatter(text)
            self.assertEqual(set(fm.keys()),
                             validate.CANONICAL_FRONTMATTER_KEYS,
                             f"{skill.name}: frontmatter keys {set(fm.keys())}")
            for key in validate.HOST_SPECIFIC_FRONTMATTER_KEYS:
                self.assertNotIn(key, fm,
                                 f"{skill.name}: canonical file has {key}")

    def test_evaluate_policy_structure(self):
        # The validator must check structure and hierarchy, not a string.
        policy = (REPO_ROOT / "skills" / "evaluate" / "agents"
                  / "openai.yaml")
        self.assertTrue(policy.exists(), "missing evaluate Codex policy")
        parsed = validate.parse_policy_yaml(policy.read_text(encoding="utf-8"))
        self.assertIsInstance(parsed, dict)
        self.assertIsInstance(parsed.get("policy"), dict)
        self.assertIs(parsed["policy"]["allow_implicit_invocation"], False)

    def test_no_machine_paths_in_shipped_markdown(self):
        for rel, path in validate.iter_shipped_markdown():
            text = path.read_text(encoding="utf-8")
            for pat in validate.LOCAL_PATH_PATTERNS:
                self.assertIsNone(pat.search(text),
                                  f"{rel}: machine path {pat.pattern}")

    def test_manifest_matches_disk(self):
        data = json.loads((REPO_ROOT / "skillset.json")
                          .read_text(encoding="utf-8"))
        declared = {s["name"] for s in data["skills"]}
        on_disk = {p.name for p in (REPO_ROOT / "skills").iterdir()
                   if p.is_dir()}
        self.assertEqual(declared, on_disk)


class TestV02Structure(unittest.TestCase):
    """Structural checks for the v0.2 contract.

    These verify repository and document STRUCTURE only: the manifest is
    7 skills at version 0.2.0, the required SKILL.md sections exist, the
    reviewed-change Procedure steps are in order, the record doc matches,
    and no governance infrastructure files exist. They do NOT assert that
    a keyword's presence proves a skill's runtime behavior — that is for
    Codex's forward tests, not these unit tests.
    """

    REQUIRED_SECTIONS = ("## Purpose", "## Use when", "## Do not use when",
                         "## Required inputs", "## Procedure",
                         "## Stop conditions", "## Output contract")

    def _skill(self, name):
        return (REPO_ROOT / "skills" / name / "SKILL.md").read_text(
            encoding="utf-8")

    def test_version_and_skill_count(self):
        data = json.loads((REPO_ROOT / "skillset.json")
                          .read_text(encoding="utf-8"))
        self.assertEqual(data["version"], "0.2.0")
        self.assertEqual(len(data["skills"]), 7)

    def test_every_skill_has_required_sections(self):
        for skill in (REPO_ROOT / "skills").iterdir():
            if not skill.is_dir():
                continue
            text = (skill / "SKILL.md").read_text(encoding="utf-8")
            for section in self.REQUIRED_SECTIONS:
                self.assertIn(section, text,
                              f"{skill.name}: missing section {section!r}")

    def test_reviewed_change_has_proposed_approach_in_contract(self):
        text = self._skill("reviewed-change")
        # Structural: the Change Contract must define the design field.
        self.assertIn("Proposed approach / design", text)
        # And Plan Review names what it reviews (structure, not behavior).
        self.assertIn("proposed approach / design agree", text.lower())

    def test_reviewed_change_procedure_steps_in_order(self):
        text = self._skill("reviewed-change")
        lines = text.split("\n")
        proc_idx = next(i for i, ln in enumerate(lines)
                        if ln.strip() == "## Procedure")
        # The ordered steps live on the first content line of Procedure.
        step_line = ""
        for ln in lines[proc_idx + 1:proc_idx + 5]:
            if "Change Contract" in ln and "Plan Review" in ln:
                step_line = ln
                break
        self.assertTrue(step_line,
                        "reviewed-change missing ordered Procedure line")
        steps = ["Change Contract", "Plan Review", "Implementation slices",
                 "Verification", "Final Independent Review",
                 "Findings Resolution", "Re-review when required",
                 "User decision / commit only when requested"]
        last = -1
        for step in steps:
            idx = step_line.find(step)
            self.assertGreater(idx, -1, f"missing step {step!r}")
            self.assertGreater(idx, last, f"{step!r} not in order")
            last = idx

    def test_reviewed_change_finding_categories(self):
        # The four category labels are a named structural contract the
        # skill must enumerate (not a behavior claim).
        text = self._skill("reviewed-change")
        for cat in ("IMPLEMENTATION_DEFECT", "TEST_DEFECT",
                    "SPECIFICATION_GAP", "FUTURE_ENHANCEMENT"):
            self.assertIn(cat, text, f"missing finding category {cat!r}")

    def test_reviewed_change_round_counting_present(self):
        text = self._skill("reviewed-change")
        self.assertIn("Review round counting", text)

    def test_record_doc_matches_skill_structure(self):
        doc = (REPO_ROOT / "docs" / "reviewed-change-record.md"
               ).read_text(encoding="utf-8")
        for section in ("## Change Contract", "## Plan Review",
                        "## Final Independent Review",
                        "## Findings resolution"):
            self.assertIn(section, doc,
                          f"record doc missing v0.2 section {section!r}")
        # The doc's Change Contract must mirror the skill's design field.
        self.assertIn("Proposed approach / design", doc)

    def test_no_governance_infrastructure_files(self):
        """A real repository-structure check, not a keyword scan.

        The v0.2 contract forbids state machines, gates, boards,
        daemons, databases, and extra runtime scripts. Assert by
        directory/file structure, not by absence of forbidden words.
        """
        # The manifest has exactly 7 skills (no hidden eighth).
        data = json.loads((REPO_ROOT / "skillset.json")
                          .read_text(encoding="utf-8"))
        self.assertEqual(len(data["skills"]), 7)

        # No governance state/lifecycle directories exist in the repo.
        forbidden_paths = [
            "state", "task-board", "delivery-state", "change-state",
            "global", "handoffs", "projects", "reviews", "archives",
        ]
        for p in forbidden_paths:
            self.assertFalse(
                (REPO_ROOT / p).exists(),
                f"forbidden governance path exists: {p}")

        # No database or daemon files.
        for bad in ("*.db", "*.sqlite", "*.sqlite3", "daemon.py",
                    "lifecycle.py", "state_machine.py", "gate.py"):
            matches = [m for m in REPO_ROOT.glob(f"**/{bad}")
                       if ".git" not in m.parts]
            self.assertEqual(matches, [],
                             f"forbidden governance file exists: {bad}")

        # The only Python runtime scripts are the installer, validator,
        # and their shared subset module; no extra runtime scripts.
        scripts = sorted(p.name for p in (REPO_ROOT / "scripts").glob("*.py"))
        self.assertEqual(scripts, ["install.py", "validate.py",
                                   "yaml_subset.py"])


class TestValidatorFailureCases(unittest.TestCase):
    """Exercise the validator against intentionally-bad temp repos."""

    def setUp(self):
        validate.errors = []
        validate.warnings = []
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        (self.root / "skills" / "bad").mkdir(parents=True)
        (self.root / "docs").mkdir()
        self._write_good_skillset()

    def _write_good_skillset(self):
        (self.root / "skillset.json").write_text(json.dumps({
            "name": "x", "version": "0.1.0",
            "hosts": {"codex": {"support": "supported"}},
            "skills": [
                {"name": "bad", "display_name": "Bad",
                 "invocation_mode": "user",
                 "hosts": {"codex": "supported"},
                 "source": "skills/bad/SKILL.md"},
                {"name": "evaluate", "display_name": "Evaluate",
                 "invocation_mode": "user-only",
                 "hosts": {"codex": "supported"},
                 "source": "skills/evaluate/SKILL.md"}
            ]
        }), encoding="utf-8")
        (self.root / "skills" / "evaluate" / "agents").mkdir(parents=True)
        (self.root / "skills" / "evaluate" / "agents"
         / "openai.yaml").write_text(
            "policy:\n  allow_implicit_invocation: false\n", encoding="utf-8")
        (self.root / "skills" / "evaluate" / "SKILL.md").write_text(
            '---\nname: "evaluate"\ndescription: "ok"\n---\n', encoding="utf-8")

    def _run_patched(self):
        validate.errors = []
        validate.warnings = []
        with mock.patch.object(validate, "REPO_ROOT", self.root), \
             mock.patch.object(validate, "SKILLS_DIR",
                               self.root / "skills"), \
             mock.patch.object(validate, "SKILLSET",
                               self.root / "skillset.json"):
            return validate.main()

    def _write_skill(self, frontmatter, body="body\n"):
        (self.root / "skills" / "bad" / "SKILL.md").write_text(
            frontmatter + body, encoding="utf-8")

    def _good_fm(self, description='"ok"'):
        return f'---\nname: "bad"\ndescription: {description}\n---\n'

    def test_invalid_colon_in_plain_description_rejected(self):
        # An unquoted value is rejected by the typed scalar parser.
        self._write_skill('---\nname: "bad"\ndescription: a: b\n---\n')
        self.assertNotEqual(self._run_patched(), 0)
        self.assertTrue(any("frontmatter" in e for e in validate.errors),
                        f"errors: {validate.errors}")

    def test_angle_brackets_in_description_rejected(self):
        # Quoted description with angle brackets is still rejected to
        # match the Codex official validator's rule.
        self._write_skill('---\nname: "bad"\ndescription: "uses <id>"\n---\n')
        self.assertNotEqual(self._run_patched(), 0)
        self.assertTrue(any("angle bracket" in e for e in validate.errors),
                        f"errors: {validate.errors}")

    def test_description_boolean_rejected(self):
        self._write_skill('---\nname: "bad"\ndescription: true\n---\n')
        self.assertNotEqual(self._run_patched(), 0)
        self.assertTrue(
            any("description" in e and ("string" in e or "frontmatter" in e)
                for e in validate.errors),
            f"errors: {validate.errors}")

    def test_description_number_rejected(self):
        self._write_skill('---\nname: "bad"\ndescription: 123\n---\n')
        self.assertNotEqual(self._run_patched(), 0)
        self.assertTrue(any("frontmatter" in e for e in validate.errors),
                        f"errors: {validate.errors}")

    def test_description_bad_json_escape_rejected(self):
        self._write_skill('---\nname: "bad"\ndescription: "bad\\q"\n---\n')
        self.assertNotEqual(self._run_patched(), 0)
        self.assertTrue(any("invalid double-quoted" in e for e in validate.errors),
                        f"errors: {validate.errors}")

    def test_description_single_quoted_rejected(self):
        self._write_skill("---\nname: \"bad\"\ndescription: 'bad q'\n---\n")
        self.assertNotEqual(self._run_patched(), 0)
        self.assertTrue(any("single-quoted" in e for e in validate.errors),
                        f"errors: {validate.errors}")

    def test_extra_frontmatter_field_rejected(self):
        self._write_skill(
            '---\nname: "bad"\ndescription: "ok"\nextra: "field"\n---\n')
        self.assertNotEqual(self._run_patched(), 0)
        self.assertTrue(any("extra keys" in e for e in validate.errors),
                        f"errors: {validate.errors}")

    def test_root_level_machine_path_rejected(self):
        # A machine path in a root-level markdown file (README) is caught.
        (self.root / "README.md").write_text(
            "see D:\\agent-workflow for context\n", encoding="utf-8")
        self._write_skill(self._good_fm())
        self.assertNotEqual(self._run_patched(), 0)
        self.assertTrue(any("README" in e and "machine-specific" in e
                            for e in validate.errors),
                        f"errors: {validate.errors}")

    def test_root_level_broken_link_rejected(self):
        (self.root / "README.md").write_text(
            "broken [link](does-not-exist.md)\n", encoding="utf-8")
        self._write_skill(self._good_fm())
        self.assertNotEqual(self._run_patched(), 0)
        self.assertTrue(any("README" in e and "broken doc link" in e
                            for e in validate.errors),
                        f"errors: {validate.errors}")

    def test_nested_doc_machine_path_rejected(self):
        # A nested markdown file under docs/ must not bypass validation.
        nested = self.root / "docs" / "subdir" / "bad.md"
        nested.parent.mkdir(parents=True)
        nested.write_text("see C:\\Users\\Administrator\\secret\n",
                          encoding="utf-8")
        self._write_skill(self._good_fm())
        self.assertNotEqual(self._run_patched(), 0)
        self.assertTrue(any("subdir" in e and "machine-specific" in e
                            for e in validate.errors),
                        f"errors: {validate.errors}")

    def test_nested_doc_broken_link_rejected(self):
        nested = self.root / "docs" / "subdir" / "bad.md"
        nested.parent.mkdir(parents=True)
        nested.write_text("broken [link](../nope.md)\n", encoding="utf-8")
        self._write_skill(self._good_fm())
        self.assertNotEqual(self._run_patched(), 0)
        self.assertTrue(any("subdir" in e and "broken doc link" in e
                            for e in validate.errors),
                        f"errors: {validate.errors}")


if __name__ == "__main__":
    unittest.main()