"""Contract tests for the optional knowledge-work-companion skill pack.

Standard library only. Checks pack structure, distribution boundaries, and
the fork's own behavioral boundaries — not upstream prompt wording. These
skills are intentional forks, so no test pins sentences, hashes, or line
counts.
"""

from __future__ import annotations

import json
import re
import unittest
from pathlib import Path

PACK_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = PACK_ROOT.parent.parent

EXPECTED = ["decision-memo", "research-synthesis", "reviewing-output"]
UPSTREAM_REPO = "andreaswasita/copilot-cowork-dojo"
UPSTREAM_COMMIT = "10605ba267c18dfd725a3507f4cf14b607a64e9a"
UPSTREAM_PATHS = {
    "research-synthesis": "skills/research-synthesis/SKILL.md",
    "decision-memo": "skills/decision-memo/SKILL.md",
    "reviewing-output": "skills/reviewing-output/SKILL.md",
}
# Skills and artifact families deliberately excluded from this pack.
OUT_OF_SCOPE = [
    "capture",
    "meetings",
    "meeting-actions",
    "inbox-triage",
    "email",
    "calendar",
    "docx",
    "xlsx",
    "pptx",
    "pdf",
    "deep-research",
    "report-writing",
]
VENDOR_NAMES = ["copilot", "chatgpt", "claude"]
MAX_WORDS_PER_SKILL = 2000
MAX_WORDS_PER_LINE = 90
LOCAL_PATH_PATTERNS = [
    re.compile(r"\b[A-Za-z]:\\"),
    re.compile(r"/Users/[A-Za-z0-9_-]+/"),
    re.compile(r"/home/[A-Za-z0-9_-]+/"),
]


def skill_text(name: str) -> str:
    return (PACK_ROOT / "skills" / name / "SKILL.md").read_text(encoding="utf-8")


def pack_markdown():
    files = [PACK_ROOT / "README.md", PACK_ROOT / "THIRD_PARTY_NOTICES.md"]
    files += sorted((PACK_ROOT / "skills").rglob("*.md"))
    return [p for p in files if p.is_file()]


def skill_title_and_body(text: str) -> tuple:
    """Split a SKILL.md into its leading provenance note and the body.

    The provenance note may legitimately name the upstream repository and
    vendor (MIT attribution), so host-neutrality checks only apply to the
    body below the first level-1 heading.
    """
    lines = text.split("\n")
    end = 1
    if lines[0].strip() == "---":
        for i in range(1, len(lines)):
            if lines[i].strip() == "---":
                end = i + 1
                break
    note, body = [], []
    for line in lines[end:]:
        if not body and line.startswith("# "):
            body.append(line)
            continue
        (body if body else note).append(line)
    return "\n".join(note), "\n".join(body)


def frontmatter_keys(text: str) -> dict:
    """Top-level frontmatter keys. Nested/folded lines are ignored."""
    lines = text.split("\n")
    if not lines or lines[0].strip() != "---":
        return {}
    keys = {}
    for line in lines[1:]:
        if line.strip() == "---":
            break
        if not line or line[0] in " \t":
            continue
        key, sep, value = line.partition(":")
        if sep:
            keys[key.strip()] = value.strip()
    return keys


class KnowledgeWorkCompanionTests(unittest.TestCase):
    def test_pack_files_exist(self):
        self.assertTrue((PACK_ROOT / "README.md").is_file())
        self.assertTrue((PACK_ROOT / "pack-manifest.json").is_file())
        self.assertTrue((PACK_ROOT / "THIRD_PARTY_NOTICES.md").is_file())
        self.assertTrue((PACK_ROOT / "tests" / "test_knowledge_work_companion.py").is_file())

    def test_exactly_three_expected_skills(self):
        skills_dir = PACK_ROOT / "skills"
        names = sorted(p.name for p in skills_dir.iterdir() if p.is_dir())
        self.assertEqual(names, sorted(EXPECTED))
        for name in EXPECTED:
            self.assertTrue((skills_dir / name / "SKILL.md").is_file())

    def test_excluded_skills_absent(self):
        skills_dir = PACK_ROOT / "skills"
        for name in OUT_OF_SCOPE:
            self.assertFalse((skills_dir / name).exists(), name)
        manifest = json.loads(
            (PACK_ROOT / "pack-manifest.json").read_text(encoding="utf-8")
        )
        declared = {s["name"] for s in manifest["skills"]}
        self.assertEqual(declared, set(EXPECTED))

    def test_frontmatter_has_only_name_and_description(self):
        for name in EXPECTED:
            fm = frontmatter_keys(skill_text(name))
            self.assertEqual(
                sorted(fm), ["description", "name"], f"{name}: {sorted(fm)}"
            )
            self.assertEqual(fm["name"], name)
            self.assertTrue(fm["description"])
            self.assertNotIn("<", fm["description"])
            self.assertNotIn(">", fm["description"])

    def test_manifest_optional_and_all_intentional_fork(self):
        manifest = json.loads(
            (PACK_ROOT / "pack-manifest.json").read_text(encoding="utf-8")
        )
        self.assertEqual(manifest["pack_name"], "knowledge-work-companion")
        self.assertIs(manifest["installed"], False)
        self.assertIn("Not installed by default", manifest["status_note"])
        self.assertEqual(len(manifest["skills"]), 3)
        for entry in manifest["skills"]:
            name = entry["name"]
            self.assertIn(name, EXPECTED)
            self.assertEqual(entry["provenance"], "intentional-fork")
            self.assertEqual(entry["upstream_repository"], UPSTREAM_REPO)
            self.assertEqual(entry["upstream_commit"], UPSTREAM_COMMIT)
            self.assertEqual(entry["upstream_path"], UPSTREAM_PATHS[name])
            self.assertTrue(entry["local_reason"])
            self.assertTrue((PACK_ROOT / entry["entry"]).is_file())

    def test_upstream_commit_pinned_everywhere(self):
        blobs = {
            "pack-manifest.json": (PACK_ROOT / "pack-manifest.json").read_text(
                encoding="utf-8"
            ),
            "README.md": (PACK_ROOT / "README.md").read_text(encoding="utf-8"),
            "THIRD_PARTY_NOTICES.md": (
                PACK_ROOT / "THIRD_PARTY_NOTICES.md"
            ).read_text(encoding="utf-8"),
        }
        for label, text in blobs.items():
            self.assertIn(UPSTREAM_COMMIT, text, label)
            self.assertIn(UPSTREAM_REPO, text, label)

    def test_not_in_seven_core_or_default_installer(self):
        skillset_text = (REPO_ROOT / "skillset.json").read_text(encoding="utf-8")
        skillset = json.loads(skillset_text)
        core_names = [s["name"] for s in skillset["skills"]]
        self.assertEqual(len(core_names), 7)
        installer_text = (REPO_ROOT / "scripts" / "install.py").read_text(
            encoding="utf-8"
        )
        for name in EXPECTED:
            self.assertNotIn(name, core_names)
            self.assertFalse((REPO_ROOT / "skills" / name).exists())
            self.assertNotIn(name, skillset_text)
            self.assertNotIn(name, installer_text)
        self.assertNotIn("knowledge-work-companion", skillset_text)
        self.assertNotIn("knowledge-work-companion", installer_text)

    def test_no_dangling_relative_links(self):
        for path in pack_markdown():
            text = path.read_text(encoding="utf-8")
            for target in re.findall(r"\]\(([^)]+)\)", text):
                if target.startswith(("http://", "https://", "#", "mailto:")):
                    continue
                resolved = (path.parent / target).resolve()
                self.assertTrue(resolved.exists(), f"{path}: broken link {target}")

    def test_no_machine_specific_paths(self):
        for path in pack_markdown():
            text = path.read_text(encoding="utf-8")
            for pattern in LOCAL_PATH_PATTERNS:
                match = pattern.search(text)
                self.assertIsNone(match, f"{path}: {match.group(0) if match else ''}")

    def test_word_and_line_budgets(self):
        for name in EXPECTED:
            lines = skill_text(name).split("\n")
            words = sum(len(line.split()) for line in lines)
            self.assertLessEqual(words, MAX_WORDS_PER_SKILL, name)
            worst = max(len(line.split()) for line in lines)
            self.assertLessEqual(worst, MAX_WORDS_PER_LINE, name)

    def test_third_party_notices_attribution(self):
        text = (PACK_ROOT / "THIRD_PARTY_NOTICES.md").read_text(encoding="utf-8")
        self.assertIn(UPSTREAM_REPO, text)
        self.assertIn(UPSTREAM_COMMIT, text)
        self.assertIn("MIT", text)
        self.assertIn("Copyright (c) 2026 Andreas Wasita", text)
        self.assertIn("The above copyright notice and this permission notice", text)
        self.assertIn("intentional fork", text.lower())
        for name in EXPECTED:
            self.assertIn(name, text)
            self.assertIn(UPSTREAM_PATHS[name], text)

    # --- fork boundaries ---------------------------------------------------

    def test_research_synthesis_does_not_force_a_position(self):
        text = skill_text("research-synthesis").lower()
        # The upstream coercive rule must be gone.
        self.assertNotIn("no position = no synthesis", text)
        self.assertNotIn("takes a position", text)
        # A non-position outcome must be reachable.
        self.assertIn("strongest judgment the evidence supports", text)
        self.assertIn("insufficient evidence", text)

    def test_research_synthesis_keeps_pipeline_and_citation_discipline(self):
        text = skill_text("research-synthesis").lower()
        for concept in ("synthesis matrix", "disagreement is signal", "so-what"):
            self.assertIn(concept, text)
        for mode in ("direct quote", "paraphrase", "synthesis claim"):
            self.assertIn(mode, text)
        # Scope boundary against turning synthesis into a research program.
        self.assertIn("deep-research orchestration", text)

    def test_research_synthesis_has_no_core_verdict_taxonomy(self):
        text = skill_text("research-synthesis").upper()
        for verdict in ("CONTINUE", "PIVOT", "INSUFFICIENT_EVIDENCE"):
            self.assertNotIn(verdict, text)

    def test_decision_memo_supports_defer_and_escalate(self):
        text = skill_text("decision-memo")
        self.assertIn("RECOMMEND", text)
        self.assertIn("DEFER", text)
        self.assertIn("ESCALATE", text)

    def test_decision_memo_defaults_to_one_page_but_not_absolute(self):
        text = skill_text("decision-memo").lower()
        self.assertIn("default to one page", text)
        self.assertNotIn("no exceptions", text)
        self.assertIn("as small as the decision responsibly allows", text)

    def test_decision_memo_prepares_a_human_decision(self):
        text = skill_text("decision-memo").lower()
        self.assertIn("human decision", text)
        self.assertIn("decision-maker", text)

    def test_skills_name_upstream_only_in_the_provenance_note(self):
        for name in EXPECTED:
            note, body = skill_title_and_body(skill_text(name))
            self.assertIn(UPSTREAM_REPO, note, name)
            for vendor in VENDOR_NAMES:
                self.assertNotIn(vendor, body.lower(), f"{name} body mentions {vendor}")

    def test_reviewing_output_does_not_own_engineering_review(self):
        text = skill_title_and_body(skill_text("reviewing-output"))[1]
        lower = text.lower()
        self.assertNotIn("code or automation review", lower)
        self.assertIn("engineering review path", lower)
        self.assertIn("software code", lower)

    def test_reviewing_output_distinguishes_unverified_from_false(self):
        text = skill_text("reviewing-output")
        self.assertIn("UNVERIFIED", text)
        self.assertIn("FALSE", text)
        lower = text.lower()
        self.assertIn("evidence gap", lower)
        self.assertIn("verification limitation", lower)

    def test_reviewing_output_right_sizes_trivial_outputs(self):
        text = skill_text("reviewing-output").lower()
        self.assertIn("five-lens review", text)
        self.assertIn("trivial", text)
        self.assertIn("right-size", text)

    def test_reviewing_output_keeps_five_lenses_and_triage(self):
        text = skill_text("reviewing-output").lower()
        for lens in ("facts", "tone", "omissions", "bias", "audience fit"):
            self.assertIn(lens, text)
        for severity in ("critical", "important", "suggestion", "strength"):
            self.assertIn(severity, text)

    def test_no_mandatory_pipeline_between_skills(self):
        for name in EXPECTED:
            text = skill_text(name).lower()
            self.assertNotIn("must run", text)
            self.assertNotIn("required pipeline", text)
            self.assertIn("not a mandatory pipeline", text)
            self.assertIn("standalone", text)

    def test_pack_readme_states_boundaries(self):
        text = (PACK_ROOT / "README.md").read_text(encoding="utf-8")
        lower = text.lower()
        for name in EXPECTED:
            self.assertIn(name, text)
        self.assertIn("not installed by default", lower)
        self.assertIn("seven core", lower)
        self.assertIn("example only", lower)
        for boundary in (
            "engineering-companion",
            "internal-enterprise-companion",
            "windows-agent-safety",
        ):
            self.assertIn(boundary, lower)


if __name__ == "__main__":
    unittest.main()
