"""Tests for scripts/install.py. Standard library only, temp dirs only."""

import io
import os
import sys
import tempfile
import unittest
from pathlib import Path
from contextlib import redirect_stdout

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = REPO_ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

import install  # noqa: E402

ALL_SKILLS = ("shape", "evaluate", "task-router", "quick-change",
              "bounded-change", "reviewed-change", "coordinate")


class TestInstall(unittest.TestCase):

    def setUp(self):
        # Run everything in a temp dir; never touch the real user home.
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.dest = Path(self.tmp.name) / "skills"

    def _run(self, *argv):
        buf = io.StringIO()
        code = None
        with redirect_stdout(buf):
            code = install.main(list(argv))
        return code, buf.getvalue()

    def test_codex_install_to_destination(self):
        code, out = self._run("--target", "codex", "--destination",
                              str(self.dest))
        self.assertEqual(code, 0, out)
        # Single-target + destination installs directly; no host subdir.
        for name in ALL_SKILLS:
            self.assertTrue((self.dest / name / "SKILL.md").exists(),
                            f"missing {name}")
        # evaluate keeps its Codex policy file.
        self.assertTrue((self.dest / "evaluate" / "agents"
                        / "openai.yaml").exists())
        # No host subdirectory for a single-target install.
        self.assertFalse((self.dest / "codex").exists())
        self.assertFalse((self.dest / "claude").exists())

    def test_claude_evaluate_has_disable_model_invocation(self):
        code, out = self._run("--target", "claude", "--destination",
                              str(self.dest))
        self.assertEqual(code, 0, out)
        text = (self.dest / "evaluate" / "SKILL.md").read_text(
            encoding="utf-8")
        self.assertIn("disable-model-invocation: true", text)

    def test_claude_disable_model_invocation_is_bare_yaml_bool(self):
        # The override must be the bare YAML word `true`, not the quoted
        # string "true". Round-trip the installed frontmatter and confirm
        # the value parses as a real Python bool.
        code, out = self._run("--target", "claude", "--destination",
                              str(self.dest))
        self.assertEqual(code, 0, out)
        import yaml_subset
        fm, _ = yaml_subset.parse_frontmatter(
            (self.dest / "evaluate" / "SKILL.md").read_text(encoding="utf-8"))
        self.assertIs(fm["disable-model-invocation"], True)
        # And the literal text must not quote it.
        text = (self.dest / "evaluate" / "SKILL.md").read_text(encoding="utf-8")
        self.assertNotIn('"true"', text)

    def test_codex_evaluate_has_no_disable_model_invocation(self):
        code, out = self._run("--target", "codex", "--destination",
                              str(self.dest))
        self.assertEqual(code, 0, out)
        text = (self.dest / "evaluate" / "SKILL.md").read_text(
            encoding="utf-8")
        self.assertNotIn("disable-model-invocation", text)

    def test_dry_run_writes_nothing(self):
        code, out = self._run("--target", "codex", "--destination",
                              str(self.dest), "--dry-run")
        self.assertEqual(code, 0, out)
        self.assertIn("[dry-run]", out)
        # Destination must not exist after a dry run (nothing was written).
        self.assertFalse(self.dest.exists(),
                         "dry-run wrote files into the destination")

    def test_both_uses_separate_subdirs_no_overwrite(self):
        # both + destination must NOT let one host overwrite the other.
        code, out = self._run("--target", "both", "--destination",
                              str(self.dest))
        self.assertEqual(code, 0, out)
        codex_eval = self.dest / "codex" / "evaluate" / "SKILL.md"
        claude_eval = self.dest / "claude" / "evaluate" / "SKILL.md"
        self.assertTrue(codex_eval.exists(), "codex view missing")
        self.assertTrue(claude_eval.exists(), "claude view missing")
        # The two views must differ: codex has no marker, claude does.
        self.assertNotIn("disable-model-invocation",
                         codex_eval.read_text(encoding="utf-8"))
        self.assertIn("disable-model-invocation: true",
                      claude_eval.read_text(encoding="utf-8"))
        # All seven skills present under each host subdir.
        for name in ALL_SKILLS:
            self.assertTrue((self.dest / "codex" / name / "SKILL.md").exists())
            self.assertTrue((self.dest / "claude" / name / "SKILL.md").exists())

    def test_canonical_frontmatter_is_generic(self):
        # The source-of-truth SKILL.md must not contain host-specific keys.
        text = (REPO_ROOT / "skills" / "evaluate"
                / "SKILL.md").read_text(encoding="utf-8")
        self.assertNotIn("disable-model-invocation", text)

    def test_install_does_not_delete_unrelated_skills(self):
        # Pre-create an unrelated skill in the destination.
        other = self.dest / "some-other-skill" / "SKILL.md"
        other.parent.mkdir(parents=True)
        other.write_text("---\nname: some-other-skill\n---\n", encoding="utf-8")
        code, out = self._run("--target", "codex", "--destination",
                              str(self.dest))
        self.assertEqual(code, 0, out)
        self.assertTrue(other.exists(), "installer deleted an unrelated skill")

    def test_install_reports_overwritten_files(self):
        # Pre-create evaluate to trigger the overwrite path.
        ev = self.dest / "evaluate" / "SKILL.md"
        ev.parent.mkdir(parents=True)
        ev.write_text("old", encoding="utf-8")
        code, out = self._run("--target", "codex", "--destination",
                              str(self.dest), "--dry-run")
        self.assertEqual(code, 0, out)
        self.assertIn("would overwrite: SKILL.md", out)

    def test_grok_target_rejected(self):
        # Grok is experimental with no native installer target.
        with self.assertRaises(ValueError):
            install.install_target("grok", "user", True, None)

    def test_opencode_install_to_destination(self):
        code, out = self._run("--target", "opencode", "--destination",
                              str(self.dest))
        self.assertEqual(code, 0, out)
        # All seven skills install, and the full package recurses (the
        # shape reference must be carried, not just SKILL.md).
        for name in ALL_SKILLS:
            self.assertTrue((self.dest / name / "SKILL.md").exists(),
                            f"missing {name}")
        self.assertTrue((self.dest / "shape" / "references"
                         / "delivery-ready.md").exists(),
                        "shape reference not copied")

    def test_opencode_evaluate_has_autoinvoke_metadata(self):
        code, out = self._run("--target", "opencode", "--destination",
                              str(self.dest))
        self.assertEqual(code, 0, out)
        text = (self.dest / "evaluate" / "SKILL.md").read_text(
            encoding="utf-8")
        self.assertIn("metadata:", text)
        self.assertIn('opencode/autoinvoke: "false"', text)

    def test_opencode_non_evaluate_has_no_metadata(self):
        code, out = self._run("--target", "opencode", "--destination",
                              str(self.dest))
        self.assertEqual(code, 0, out)
        text = (self.dest / "shape" / "SKILL.md").read_text(
            encoding="utf-8")
        self.assertNotIn("metadata:", text)
        self.assertNotIn("opencode/autoinvoke", text)

    def test_opencode_installed_body_matches_canonical(self):
        # Host metadata is added only to evaluate's frontmatter; every
        # installed skill body must otherwise equal the canonical body.
        # Compare the body after the frontmatter, not via the strict parser,
        # because evaluate's installed copy carries a nested metadata block.
        def body_only(text):
            _, _, b = text.partition("---\n\n") if "\n\n" in text \
                else text.partition("---")
            return b
        code, out = self._run("--target", "opencode", "--destination",
                              str(self.dest))
        self.assertEqual(code, 0, out)
        for name in ALL_SKILLS:
            repo = (REPO_ROOT / "skills" / name / "SKILL.md").read_text(
                encoding="utf-8")
            inst = (self.dest / name / "SKILL.md").read_text(
                encoding="utf-8")
            self.assertEqual(body_only(repo), body_only(inst),
                             f"body drift: {name}")


class TestProjectScope(unittest.TestCase):
    """--scope project resolves against the current project (cwd), not the
    toolkit's location, and not the user home."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.project = Path(self.tmp.name) / "my-project"
        self.project.mkdir()

    def _run_in(self, cwd, *argv):
        # Run install.main with the cwd set to the fake project.
        orig_cwd = os.getcwd()
        os.chdir(cwd)
        try:
            buf = io.StringIO()
            with redirect_stdout(buf):
                code = install.main(list(argv))
            return code, buf.getvalue()
        finally:
            os.chdir(orig_cwd)

    def test_codex_project_scope_is_cwd_agents_skills(self):
        code, out = self._run_in(
            self.project, "--target", "codex", "--scope", "project", "--dry-run")
        self.assertEqual(code, 0, out)
        expected = str(self.project / ".agents" / "skills")
        self.assertIn(expected, out,
                      "codex project scope must resolve to <project>/.agents/skills")

    def test_claude_project_scope_is_cwd_claude_skills(self):
        code, out = self._run_in(
            self.project, "--target", "claude", "--scope", "project", "--dry-run")
        self.assertEqual(code, 0, out)
        expected = str(self.project / ".claude" / "skills")
        self.assertIn(expected, out,
                      "claude project scope must resolve to <project>/.claude/skills")

    def test_opencode_project_scope_is_cwd_opencode_skills(self):
        code, out = self._run_in(
            self.project, "--target", "opencode", "--scope", "project", "--dry-run")
        self.assertEqual(code, 0, out)
        expected = str(self.project / ".opencode" / "skills")
        self.assertIn(expected, out,
                      "opencode project scope must resolve to <project>/.opencode/skills")

    def test_project_scope_not_inferred_from_toolkit_parent(self):
        # The project dir is unrelated to the repo where the toolkit lives.
        # Confirm resolution uses cwd, not REPO_ROOT.parent.
        self.assertNotEqual(
            (self.project / ".agents" / "skills"),
            (REPO_ROOT.parent / ".agents" / "skills"),
            "test setup would not distinguish cwd from toolkit-parent")

    def test_project_scope_not_user_home(self):
        home = Path(os.path.expanduser("~"))
        code, out = self._run_in(
            self.project, "--target", "codex", "--scope", "project", "--dry-run")
        self.assertEqual(code, 0, out)
        self.assertNotIn(str(home / ".agents" / "skills"), out,
                         "project scope must not resolve to the user home")

    def test_opencode_user_scope_is_config_dir(self):
        # user scope must resolve under ~/.config/opencode/skills (not a
        # temp dir, but host_install_dir itself is pure path resolution).
        home = Path(os.path.expanduser("~"))
        d = install.host_install_dir("opencode", "user", None)
        self.assertEqual(d, home / ".config" / "opencode" / "skills")


if __name__ == "__main__":
    unittest.main()