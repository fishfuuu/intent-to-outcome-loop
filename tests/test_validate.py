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


class TestV04Structure(unittest.TestCase):
    """Structural checks for the v0.4 contract.

    These verify repository and document STRUCTURE only: the manifest is
    7 skills at version 0.4.0, required SKILL.md sections exist, the
    reviewed-change Procedure steps and baseline contract (proposed
    approach, finding categories, round counting) hold, the record doc
    matches, the coordinate Handoff Markdown template exists, and no
    governance infrastructure files exist. They do NOT assert that a
    keyword's presence proves a skill's runtime behavior — coordinate's
    default-no-write, explicit-request gating, and overwrite protection,
    and the shape/bounded-change/reviewed-change cognitive upgrades, are
    covered by manual scenario walk-throughs and Codex's forward tests.
    """

    REQUIRED_SECTIONS = ("## Purpose", "## Use when", "## Do not use when",
                         "## Required inputs", "## Procedure",
                         "## Stop conditions", "## Output contract")

    def _skill(self, name):
        return (REPO_ROOT / "skills" / name / "SKILL.md").read_text(
            encoding="utf-8")

    def _skillset(self):
        return json.loads((REPO_ROOT / "skillset.json")
                          .read_text(encoding="utf-8"))

    def test_version_and_skill_count(self):
        data = self._skillset()
        self.assertEqual(data["version"], "0.4.0")
        self.assertEqual(len(data["skills"]), 7)

    def test_every_skill_has_required_sections(self):
        for skill in (REPO_ROOT / "skills").iterdir():
            if not skill.is_dir():
                continue
            text = (skill / "SKILL.md").read_text(encoding="utf-8")
            for section in self.REQUIRED_SECTIONS:
                self.assertIn(section, text,
                              f"{skill.name}: missing section {section!r}")

    def test_coordinate_frontmatter_is_only_name_and_description(self):
        fm, _ = yaml_subset.parse_frontmatter(self._skill("coordinate"))
        self.assertEqual(set(fm.keys()), validate.CANONICAL_FRONTMATTER_KEYS,
                         "coordinate canonical frontmatter must be only "
                         "name and description")
        for key in validate.HOST_SPECIFIC_FRONTMATTER_KEYS:
            self.assertNotIn(key, fm)

    def test_coordinate_persistence_template_present(self):
        # Structural contract: the persistence-mode Handoff Markdown
        # template must be a fenced block under the named heading, with
        # the title and the eight base sections in exact order. This is a
        # real structure check (ordered section set), not a keyword test.
        # Behavior such as default-no-write and overwrite protection is
        # covered by the three manual scenario walk-throughs.
        text = self._skill("coordinate")
        lines = text.split("\n")

        # Locate the template heading, then the first fenced block after it.
        heading_idx = next(
            (i for i, ln in enumerate(lines)
             if ln.strip() == "## Handoff Markdown template (persistence mode)"),
            None)
        self.assertIsNotNone(heading_idx,
                             "coordinate missing Handoff Markdown template heading")

        # The non-empty lines of the first fenced block must be exactly
        # the title and the eight base sections, in this order.
        fence_idxs = [i for i, ln in enumerate(lines[heading_idx + 1:], start=heading_idx + 1)
                      if ln.strip() == "```"]
        self.assertGreaterEqual(len(fence_idxs), 2,
                                "coordinate missing the persistence template "
                                "fenced block")
        first_open, first_close = fence_idxs[0], fence_idxs[1]
        block = lines[first_open + 1:first_close]
        expected = [
            "# Current Outcome Handoff",
            "## Outcome",
            "## Current Slice / State",
            "## Confirmed Facts and Rules",
            "## Artifacts and Locations",
            "## Evidence",
            "## Limitations and Risks",
            "## Specific Ask / Recommended Next Step",
            "## Open Questions",
        ]
        actual = [ln.strip() for ln in block if ln.strip()]
        self.assertEqual(actual, expected,
                         "coordinate persistence template sections do not match "
                         f"the ordered contract; got:\n{actual}")

        # The optional Data/AI sections live in a second fenced block.
        optional = [
            "## Data Meaning and Sensitivity",
            "## AI Decision and Fallback",
        ]
        # Collect all fenced blocks after the heading; the second one is
        # the optional-sections block.
        fence_idxs = [i for i, ln in enumerate(lines[heading_idx + 1:], start=heading_idx + 1)
                      if ln.strip() == "```"]
        self.assertGreaterEqual(len(fence_idxs), 4,
                                "coordinate missing the optional Data/AI "
                                "fenced block")
        second_open, second_close = fence_idxs[2], fence_idxs[3]
        opt_actual = [ln.strip() for ln in lines[second_open + 1:second_close]
                      if ln.strip()]
        self.assertEqual(opt_actual, optional,
                         "coordinate optional Data/AI template sections do not "
                         f"match; got:\n{opt_actual}")

    def test_reviewed_change_has_proposed_approach_in_contract(self):
        # Baseline regression: the Change Contract must define the design
        # field. (reviewed-change is in the v0.4 change set; this guards
        # the proposed-approach field against regression.)
        text = self._skill("reviewed-change")
        self.assertIn("Proposed approach / design", text)
        self.assertIn("proposed approach / design agree", text.lower())

    def test_reviewed_change_finding_categories(self):
        # Baseline regression: the four category labels are a named
        # structural contract the skill must enumerate.
        text = self._skill("reviewed-change")
        for cat in ("IMPLEMENTATION_DEFECT", "TEST_DEFECT",
                    "SPECIFICATION_GAP", "FUTURE_ENHANCEMENT"):
            self.assertIn(cat, text, f"missing finding category {cat!r}")

    def test_reviewed_change_round_counting_present(self):
        # Baseline regression: review round counting must be defined.
        text = self._skill("reviewed-change")
        self.assertIn("Review round counting", text)

    def test_shape_partial_confirmation_does_not_set_parameter(self):
        # Case A regression (repeated drift): choosing a rule form
        # ("fixed days" / "configurable threshold") confirms the form, not
        # its material parameter — the skill must keep demanding the
        # specific value or leave it explicitly unresolved.
        text = self._skill("shape")
        self.assertIn("A recommendation is not confirmation", text)
        self.assertIn("confirms the form, not its parameter", text)

    def test_shape_explicit_value_confirmation_is_enough(self):
        # Case B regression: selecting a recommended option that names the
        # specific value ("7-day window") IS confirmation — the skill must
        # not re-ask it as unresolved.
        text = self._skill("shape")
        self.assertIn("explicit user choice settles a material value", text)
        self.assertIn("choosing a recommended option that names the specific value", text)

    def test_shape_unresolved_blocker_forbids_delivery_ready_brief(self):
        # Case C regression: Shape discovers a material unresolved rule or
        # blocking feasibility, then still calls the brief delivery-ready
        # and offers task-router. The skill must forbid that completion.
        text = self._skill("shape")
        self.assertIn("before calling it delivery-ready or offering", text)
        self.assertIn("able to overturn the solution or acceptance", text)

    def test_shape_explicit_user_risk_acceptance_allows_continuation(self):
        # Case D regression guard: the skill must not become so risk-averse
        # that it forbids a user from explicitly accepting a blocking risk
        # and continuing. Lock in the dual invariant.
        text = self._skill("shape")
        self.assertIn("get the user to explicitly accept carrying it", text)
        self.assertIn("stated assumption/risk", text)

    def test_shape_brief_self_check_blocks_delivery_ready(self):
        # Case E regression: Shape forms a brief with material incompleteness
        # or internal contradiction (e.g., business contract vs. acceptance
        # scenario) and still calls it delivery-ready. The skill must check
        # the brief once before handoff.
        text = self._skill("shape")
        self.assertIn("check it once", text)
        self.assertIn("material incompleteness or contradiction", text)
        self.assertIn("conflict between the business contract, acceptance scenarios", text)

    def test_reviewed_change_procedure_steps_in_order(self):
        text = self._skill("reviewed-change")
        lines = text.split("\n")
        proc_idx = next(i for i, ln in enumerate(lines)
                        if ln.strip() == "## Procedure")
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

    def test_record_doc_matches_skill_structure(self):
        doc = (REPO_ROOT / "docs" / "reviewed-change-record.md"
               ).read_text(encoding="utf-8")
        for section in ("## Change Contract", "## Plan Review",
                        "## Final Independent Review",
                        "## Findings resolution"):
            self.assertIn(section, doc,
                          f"record doc missing section {section!r}")
        self.assertIn("Proposed approach / design", doc)

    def test_reviewed_change_plan_review_blocking_needs_new_approved(self):
        # Transition discipline: a blocking Plan Review is not cleared by
        # the implementer's belief; production implementation stays
        # forbidden until a NEW independent review says APPROVED.
        text = self._skill("reviewed-change")
        self.assertIn("new independent Plan Review", text)
        self.assertIn("explicit APPROVED verdict", text)
        self.assertIn("Findings fixed", text)

    def test_reviewed_change_final_approval_freezes_diff(self):
        # Transition discipline: Final Review approval freezes the reviewed
        # production diff; a later production change invalidates it and
        # requires re-review.
        text = self._skill("reviewed-change")
        self.assertIn("freezes the reviewed production diff", text)
        self.assertIn("invalidating that approval", text)

    def test_reviewed_change_non_blocking_not_auto_in_scope(self):
        # Non-blocking findings stay suggestions; the implementer must not
        # expand the current scope on their own.
        text = self._skill("reviewed-change")
        self.assertIn("do not implement it in the current scope by default", text)

    def test_reviewed_change_evidence_fidelity(self):
        # Evidence must match the promised method, not a cheaper proxy.
        text = self._skill("reviewed-change")
        self.assertIn("verification evidence", text)
        ref = (REPO_ROOT / "skills" / "reviewed-change" / "references"
               / "review-discipline.md").read_text(encoding="utf-8")
        self.assertIn("browser", ref)
        self.assertIn("Do not substitute a cheaper signal", ref)

    def test_reviewed_change_authoritative_references_supported(self):
        # Change Contract may carry authoritative references, and Final
        # Review must use them when provided.
        text = self._skill("reviewed-change")
        self.assertIn("Authoritative references", text)
        self.assertIn("review must check against them directly", text)

    def test_reviewed_change_observable_evidence_required(self):
        # Repeated runtime failure (~3 times): Final Review APPROVED on
        # code + automated tests, but the frozen user-observable behavior
        # was visibly absent in the running page. The main SKILL must state
        # at high salience that a frozen user-observable acceptance needs
        # observed-outcome evidence, and that without it Final Review
        # cannot APPROVED.
        text = self._skill("reviewed-change")
        self.assertIn("Observed-outcome evidence", text)
        self.assertIn("user-observable", text)
        self.assertIn("observed-outcome evidence", text)
        self.assertIn("cannot receive Final Review APPROVED", text)
        # Missing evidence is verification incomplete -> return to
        # Verification, NOT BLOCKED and NOT a finding merely for absence.
        self.assertIn("verification is incomplete", text)
        self.assertIn("return to Verification", text)
        self.assertIn("not BLOCKED", text)
        self.assertIn("not a finding merely because the evidence is missing", text)
        # Code/tests alone cannot stand in for a rendered/interactive result.
        self.assertIn("cannot prove a rendered or interactive outcome", text)

    def test_reviewed_change_observable_absence_is_defect(self):
        # A frozen user-observable behavior actually observed and absent
        # from the running result is an IMPLEMENTATION_DEFECT (blocking
        # finding), even when code and automated tests exist.
        text = self._skill("reviewed-change")
        self.assertIn("absent from the running/rendered result", text)
        self.assertIn("IMPLEMENTATION_DEFECT", text)
        self.assertIn("blocking finding", text)

    def test_reviewed_change_evidence_type_mismatch_in_reference(self):
        # The reference must explain that evidence type follows acceptance
        # type, and that a type mismatch (UI outcome "verified" by a data
        # test) means verification incomplete / cannot APPROVED yet (not a
        # finding merely for wrong evidence type). Also pins that this is
        # not a browser mandate.
        ref = (REPO_ROOT / "skills" / "reviewed-change" / "references"
               / "review-discipline.md").read_text(encoding="utf-8")
        self.assertIn("Evidence type follows acceptance type", ref)
        self.assertIn("browser mandate", ref)
        self.assertIn("type mismatch", ref)
        self.assertIn("verification is incomplete", ref)
        self.assertIn("cannot APPROVED yet", ref)
        self.assertIn("not a finding merely because the evidence is wrong type", ref)
        # Code/tests alone cannot prove a rendered/interactive outcome.
        self.assertIn("cannot prove a rendered or interactive outcome", ref)
        # User acceptance is not weakened: reviewer approval still != user
        # acceptance, which lives in the main SKILL.
        text = self._skill("reviewed-change")
        self.assertIn("Reviewer approval is not user acceptance", text)

    def test_review_discipline_reference_exists_and_is_referenced(self):
        # The reference exists and the SKILL points to it.
        ref = (REPO_ROOT / "skills" / "reviewed-change" / "references"
               / "review-discipline.md")
        self.assertTrue(ref.exists(), "missing review-discipline.md")
        text = self._skill("reviewed-change")
        self.assertIn("references/review-discipline.md", text)

    def test_no_governance_infrastructure_files(self):
        """A real repository-structure check, not a keyword scan.

        The v0.4 contract forbids state machines, gates, boards,
        daemons, databases, and extra runtime scripts. Assert by
        directory/file structure, not by absence of forbidden words.
        """
        self.assertEqual(len(self._skillset()["skills"]), 7)

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