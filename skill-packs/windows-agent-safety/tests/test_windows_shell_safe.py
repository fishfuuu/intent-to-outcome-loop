"""Behavior tests for windows-shell-safe (analyzer + context collector).

These are behavior tests, not keyword-existence tests. They load the real
analyzer, run real payloads, and assert on output structure, severities, stop
completeness, determinism, secret/machine-path redaction, and no-launch / no
write behavior. The collector is exercised by actually running it under
Windows PowerShell 5.1 (and PowerShell 7 when present, explicitly skipped
otherwise).
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

PACK_ROOT = Path(__file__).resolve().parents[1]
SKILL = PACK_ROOT / "skills" / "windows-shell-safe"
IMPLEMENTATION = SKILL / "scripts" / "windows_shell_safe.py"
COLLECTOR = SKILL / "scripts" / "collect_windows_context.ps1"
FIXTURES = Path(__file__).resolve().parent / "fixtures" / "windows-shell-safe"
INPUTS = FIXTURES / "wss_synthetic_inputs.json"
SECRETS = FIXTURES / "wss_synthetic_secrets.json"

REQUIRED_FIELDS = [
    "shell_family",
    "shell_executable",
    "shell_version",
    "host_process",
    "execution_mode",
    "detection_confidence",
    "command_classification",
    "risk_level",
    "findings",
    "target_identity",
    "recursive_preview_status",
    "safe_command_form",
    "equivalence_level",
    "execution_authorized",
    "stop_reasons",
]

FINDING_REGISTRY_ORDER = [
    "DIALECT_COMMAND_MISMATCH",
    "OPERATOR_UNSUPPORTED_BY_VERSION",
    "EXECUTABLE_NOT_FOUND",
    "WINDOWSAPPS_STUB_DETECTED",
    "SHELL_EVIDENCE_CONFLICT",
    "SHELL_DETECTION_CONFIDENCE_LOW",
    "COMMAND_IDENTITY_AMBIGUOUS",
    "DYNAMIC_COMMAND_IDENTITY",
    "UNTERMINATED_QUOTE",
    "ARGUMENT_BOUNDARY_EQUIVALENCE_NOT_PROVEN",
    "SENSITIVE_VALUE_REDACTED",
    "DESTRUCTIVE_CONTEXT_INCOMPLETE",
    "TARGET_OUTSIDE_ALLOWED_ROOT",
    "PROTECTED_ROOT_TARGET",
    "REPARSE_POINT_DESTRUCTIVE_TARGET",
    "TARGET_IDENTITY_UNAVAILABLE",
    "UNSUPPORTED_FILESYSTEM_PREVIEW",
    "RECURSIVE_PREVIEW_INCOMPLETE",
    "TARGET_CHANGED_DURING_PREVIEW",
    "DUPLICATE_INVENTORY_ENTRY",
    "NESTED_REINTERPRETATION_RISK",
    "SAFE_FORM_NOT_AVAILABLE",
    "SEMANTIC_EQUIVALENCE_NOT_PROVEN",
    "SENSITIVE_OUTPUT_SUPPRESSED",
    "UNKNOWN_SYNTAX",
    "BASH_BUILTIN_IN_POWERSHELL",
    "BASH_HEREDOC_IN_NON_BASH_SHELL",
    "POWERSHELL_COLON_VARIABLE_AMBIGUITY",
    "NESTED_QUOTES_NATIVE_ARGV",
    "TARGET_NOT_FOUND",
    "TARGET_EVIDENCE_MISMATCH",
    "TARGET_COMMAND_BINDING_UNPROVEN",
    "REGISTRY_OPERATION",
    "PRIVILEGE_ELEVATION_OPERATION",
    "NETWORK_DOWNLOAD_INSTALL_OPERATION",
    "OPAQUE_EXECUTOR_PAYLOAD",
]
FINDING_REGISTRY_INDEX = {code: i for i, code in enumerate(FINDING_REGISTRY_ORDER)}

STOP_CODES = {
    "EXECUTABLE_NOT_FOUND",
    "SHELL_EVIDENCE_CONFLICT",
    "COMMAND_IDENTITY_AMBIGUOUS",
    "UNTERMINATED_QUOTE",
    "DESTRUCTIVE_CONTEXT_INCOMPLETE",
    "TARGET_OUTSIDE_ALLOWED_ROOT",
    "PROTECTED_ROOT_TARGET",
    "REPARSE_POINT_DESTRUCTIVE_TARGET",
    "TARGET_IDENTITY_UNAVAILABLE",
    "UNSUPPORTED_FILESYSTEM_PREVIEW",
    "RECURSIVE_PREVIEW_INCOMPLETE",
    "TARGET_CHANGED_DURING_PREVIEW",
    "DUPLICATE_INVENTORY_ENTRY",
    "TARGET_NOT_FOUND",
    "TARGET_EVIDENCE_MISMATCH",
    "TARGET_COMMAND_BINDING_UNPROVEN",
    "OPAQUE_EXECUTOR_PAYLOAD",
    "UNKNOWN_SYNTAX",
}

# New scenario table for the v0.2 pack (beyond the migrated WSS-01..WSS-20).
NEW_SCENARIOS = {
    "WSS-21": {
        "shell": {"family": "POWERSHELL_7_PLUS", "confidence": "CONFIRMED"},
        "command": "cat <<EOF\nhello\nEOF",
        "expected": ["BASH_HEREDOC_IN_NON_BASH_SHELL"],
        "not_expected": ["EXECUTABLE_NOT_FOUND"],
    },
    "WSS-22": {
        "shell": {"family": "WINDOWS_POWERSHELL_5_1", "confidence": "CONFIRMED"},
        "command": "Write-Output one || Write-Output two",
        "expected": ["OPERATOR_UNSUPPORTED_BY_VERSION"],
    },
    "WSS-23": {
        "shell": {"family": "POWERSHELL_7_PLUS", "confidence": "CONFIRMED"},
        "command": "git push origin $branch:",
        "expected": ["POWERSHELL_COLON_VARIABLE_AMBIGUITY"],
    },
    "WSS-24": {
        "shell": {"family": "POWERSHELL_7_PLUS", "confidence": "CONFIRMED"},
        "command": "curl -X POST --data \"{\\\"a\\\":\\\"b\\\"}\" https://synthetic.invalid",
        "expected": ["NESTED_QUOTES_NATIVE_ARGV"],
    },
    "WSS-25": {
        "shell": {"family": "POWERSHELL_7_PLUS", "confidence": "CONFIRMED"},
        "command": "export FOO=bar",
        "expected": ["BASH_BUILTIN_IN_POWERSHELL"],
    },
    "WSS-26": {
        "shell": {"family": "CMD", "confidence": "CONFIRMED"},
        "command": "Remove-Item C:\\Synthetic\\one.txt",
        "expected": ["DIALECT_COMMAND_MISMATCH"],
    },
}

# Negative scenarios: behaviors that must NOT trigger a given finding.
NEGATIVE_CASES = [
    ("git-rev-path", "git show HEAD:README.md",
     "POWERSHELL_COLON_VARIABLE_AMBIGUITY"),
    ("colon-safe-form", "Write-Output ${file}:",
     "POWERSHELL_COLON_VARIABLE_AMBIGUITY"),
    ("env-colon-path", "Write-Output $env:PATH",
     "POWERSHELL_COLON_VARIABLE_AMBIGUITY"),
    ("heredoc-in-bash", "cat <<EOF\nhello\nEOF",
     "BASH_HEREDOC_IN_NON_BASH_SHELL"),
    ("heredoc-quoted", "bash -c \"cat <<EOF\"",
     "BASH_HEREDOC_IN_NON_BASH_SHELL"),
    ("ps7-double-ampersand", "Get-ChildItem . && Write-Output ok",
     "OPERATOR_UNSUPPORTED_BY_VERSION"),
]


def _load_module():
    assert IMPLEMENTATION.is_file(), f"implementation missing: {IMPLEMENTATION}"
    spec = importlib.util.spec_from_file_location("wss_impl", IMPLEMENTATION)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _tree_snapshot(root: Path) -> tuple[str, ...]:
    return tuple(sorted(str(p.relative_to(root)) for p in root.rglob("*")))


class WindowsShellSafeScenarioTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.module = _load_module()
        cls.inputs = json.loads(INPUTS.read_text(encoding="utf-8"))
        cls.secrets = json.loads(SECRETS.read_text(encoding="utf-8"))

    def _assert_output_contract(self, result: dict) -> None:
        self.assertEqual(list(result.keys()), REQUIRED_FIELDS)
        self.assertEqual(result["execution_authorized"], "NO")
        self.assertIsInstance(result["findings"], list)
        self.assertIsInstance(result["stop_reasons"], list)
        self.assertIn(result["recursive_preview_status"],
                      {"OBSERVED_COMPLETE", "INCOMPLETE", "NOT_APPLICABLE"})
        self.assertIn(result["detection_confidence"],
                      {"CONFIRMED", "HIGH", "MEDIUM", "LOW", "CONFLICTED", "UNKNOWN"})
        self.assertIsInstance(result["target_identity"], (dict, type(None)))
        finding_keys = {"code", "severity", "token_range", "evidence",
                        "affected_semantic_element", "remediation"}
        for finding in result["findings"]:
            self.assertEqual(set(finding), finding_keys)
            self.assertIn(finding["severity"], {"LOW", "MEDIUM", "HIGH", "STOP"})
            self.assertIsInstance(finding["evidence"], str)
            self.assertIsInstance(finding["remediation"], str)
            self.assertIn(finding["code"], FINDING_REGISTRY_INDEX)
        codes = [f["code"] for f in result["findings"]]
        self.assertEqual(len(codes), len(set(codes)))
        self.assertEqual(codes, sorted(codes, key=FINDING_REGISTRY_INDEX.__getitem__))
        stop_from_findings = {f["code"] for f in result["findings"]
                              if f["severity"] == "STOP"}
        self.assertEqual(stop_from_findings, set(result["stop_reasons"]))
        self.assertEqual(result["stop_reasons"],
                         [f["code"] for f in result["findings"]
                          if f["severity"] == "STOP"])
        if stop_from_findings:
            self.assertEqual(result["risk_level"], "STOP")
        serialized = json.dumps(result, ensure_ascii=False)
        for secret in self.secrets.values():
            self.assertNotIn(secret, serialized)

    def _analyze(self, payload: dict) -> dict:
        with tempfile.TemporaryDirectory(prefix="wss-test-") as tmp:
            temp_path = Path(tmp)
            before = _tree_snapshot(temp_path)
            with patch.object(subprocess, "run", side_effect=AssertionError("shell launch forbidden")), \
                 patch.object(subprocess, "Popen", side_effect=AssertionError("shell launch forbidden")), \
                 patch.object(subprocess, "call", side_effect=AssertionError("shell launch forbidden")), \
                 patch.object(subprocess, "check_call", side_effect=AssertionError("shell launch forbidden")), \
                 patch.object(subprocess, "check_output", side_effect=AssertionError("shell launch forbidden")), \
                 patch.object(os, "system", side_effect=AssertionError("shell launch forbidden")), \
                 patch.object(os, "popen", side_effect=AssertionError("shell launch forbidden")):
                result = self.module.analyze(payload)
            self.assertEqual(before, _tree_snapshot(temp_path))
        self._assert_output_contract(result)
        return result

    def _assert_scenario(self, scenario_id: str, payload: dict) -> None:
        result = self._analyze(payload)
        expected = set(payload.get("expected", []))
        not_expected = set(payload.get("not_expected", []))
        codes = {f["code"] for f in result["findings"]}
        observed = codes | set(result["command_classification"].get("secondary", []))
        observed.add(result["command_classification"].get("primary"))
        observed.add(result["equivalence_level"])
        self.assertTrue(expected.issubset(observed), scenario_id)
        self.assertTrue(not_expected.isdisjoint(observed),
                        f"{scenario_id}: unexpected findings {not_expected & observed}")
        for code in expected & STOP_CODES:
            self.assertIn(code, result["stop_reasons"])
            self.assertEqual(result["risk_level"], "STOP")
            self.assertEqual(result["safe_command_form"], "NOT_AVAILABLE")
        if "RECURSIVE_PREVIEW_INCOMPLETE" in expected:
            self.assertEqual(result["recursive_preview_status"], "INCOMPLETE")

    def _scenario(self, scenario_id: str) -> dict:
        if scenario_id in self.inputs:
            return dict(self.inputs[scenario_id])
        return dict(NEW_SCENARIOS[scenario_id])

    def test_migrated_scenarios(self) -> None:
        for scenario_id in sorted(self.inputs):
            if scenario_id == "WSS-18":
                continue  # covered by the determinism/identity tests
            self._assert_scenario(scenario_id, self._scenario(scenario_id))

    def test_new_scenarios(self) -> None:
        for scenario_id in sorted(NEW_SCENARIOS):
            self._assert_scenario(scenario_id, self._scenario(scenario_id))

    def test_negative_scenarios(self) -> None:
        ps7 = {"family": "POWERSHELL_7_PLUS", "confidence": "CONFIRMED"}
        bash = {"family": "GIT_BASH", "confidence": "CONFIRMED"}
        for label, command, forbidden in NEGATIVE_CASES:
            family = bash if label == "heredoc-in-bash" else ps7
            result = self._analyze({"shell": family, "command": command})
            codes = {f["code"] for f in result["findings"]}
            self.assertNotIn(forbidden, codes, f"{label}: {forbidden} must not fire")
            if forbidden == "BASH_HEREDOC_IN_NON_BASH_SHELL" and label == "heredoc-quoted":
                self.assertIn("NESTED_REINTERPRETATION_RISK", codes)

    def test_wss_17_sensitive_argument_withheld(self) -> None:
        result = self._analyze(self._scenario("WSS-17"))
        self.assertEqual(result["safe_command_form"], "NOT_AVAILABLE")
        self.assertIn("SENSITIVE_VALUE_REDACTED",
                      [f["code"] for f in result["findings"]])

    def test_wss_04_primary_native(self) -> None:
        result = self._analyze(self._scenario("WSS-04"))
        self.assertEqual(result["command_classification"]["primary"], "NATIVE_EXECUTABLE")


class WindowsShellSafeRmRfTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.module = _load_module()

    SYNTH_CWD = r"C:\Synthetic"
    SYNTH_ROOT = r"C:\Synthetic"
    SYNTH_TARGET = r"C:\Synthetic\t"

    RECURSIVE_CASES = [
        ("T1", "rm -rf t"),
        ("T2", "rm -fr t"),
        ("T3", "rm -rfi t"),
        ("T4", "rm -rfv t"),
        ("T5", "rm --recursive t"),
        ("T6", "rm --recursive --force t"),
        ("T7", "rm -r -f t"),
        ("T8", "rm -f -r t"),
        ("T10", "rm -r t"),
        ("T12", "rm -Rf t"),
    ]
    CONTROL_CASES = [("T9", "rm -f t")]

    def _payload(self, command: str, *, destructive: bool) -> dict:
        payload = {
            "shell": {"family": "GIT_BASH", "version": "5.2", "confidence": "CONFIRMED"},
            "command": command,
            "working_directory": self.SYNTH_CWD,
            "allowed_root": self.SYNTH_ROOT,
            "target": self.SYNTH_TARGET,
        }
        if destructive:
            payload["destructive"] = True
        return payload

    def test_recursive_classification_dual_site(self) -> None:
        for case_id, command in self.RECURSIVE_CASES:
            r_a = self.module.analyze(self._payload(command, destructive=False))
            self.assertEqual(r_a["execution_authorized"], "NO")
            self.assertIn("DESTRUCTIVE_FILESYSTEM_OPERATION",
                          r_a["command_classification"]["secondary"], case_id)
            r_b = self.module.analyze(self._payload(command, destructive=True))
            self.assertIn("TARGET_IDENTITY_UNAVAILABLE",
                          [f["code"] for f in r_b["findings"]], case_id)
            self.assertEqual(r_b["risk_level"], "STOP")

    def test_non_recursive_rm_f_is_destructive(self) -> None:
        # Requirement B: rm -f is destructive even when non-recursive.
        for case_id, command in self.CONTROL_CASES:
            r_a = self.module.analyze(self._payload(command, destructive=False))
            self.assertIn("DESTRUCTIVE_FILESYSTEM_OPERATION",
                          r_a["command_classification"]["secondary"], case_id)
            self.assertEqual(r_a["execution_authorized"], "NO")

    def test_readonly_command_not_destructive(self) -> None:
        # A genuinely read-only command is never classified destructive.
        result = self.module.analyze(self._payload("ls -la t", destructive=False))
        self.assertNotIn("DESTRUCTIVE_FILESYSTEM_OPERATION",
                         result["command_classification"]["secondary"])
        self.assertEqual(result["execution_authorized"], "NO")

    def test_execution_authorized_always_no(self) -> None:
        for case_id, command in self.RECURSIVE_CASES + self.CONTROL_CASES:
            for destructive in (False, True):
                result = self.module.analyze(self._payload(command, destructive=destructive))
                self.assertEqual(result["execution_authorized"], "NO",
                                 f"{case_id} destructive={destructive}")


class WindowsShellSafeDeterminismTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.module = _load_module()
        cls.inputs = json.loads(INPUTS.read_text(encoding="utf-8"))

    def test_same_input_byte_identical(self) -> None:
        payload = dict(self.inputs["WSS-03"])
        first = self.module.analyze(payload)
        second = self.module.analyze(payload)
        text = self.module.canonical_json_dumps(first)
        self.assertEqual(text, self.module.canonical_json_dumps(second))
        self.assertFalse(text.startswith("\ufeff"))
        self.assertNotIn("\r\n", text)
        self.assertEqual(list(first.keys()), REQUIRED_FIELDS)

    def test_wss_18_inventory_digest_deterministic(self) -> None:
        data = self.inputs["WSS-18"]
        first = self.module.inventory_digest(data["inventory"], data["display_paths"])
        second = self.module.inventory_digest(list(reversed(data["inventory"])),
                                              data["alternate_display_paths"])
        self.assertEqual(first, data["expected_digest"])
        self.assertEqual(first, second)

    def test_wss_18_identity_change_stops(self) -> None:
        data = self.inputs["WSS-18"]
        payload = dict(data["analysis_template"])
        payload["inventory"] = data["inventory"]
        payload["preview_before"] = data["target_identity_a"]
        payload["preview_after"] = data["target_identity_b"]
        result = self.module.analyze(payload)
        codes = {f["code"] for f in result["findings"]}
        self.assertIn(data["expected_identity_change_code"], codes)
        self.assertIn(data["expected_identity_change_code"], result["stop_reasons"])
        self.assertEqual(result["risk_level"], "STOP")
        self.assertEqual(result["safe_command_form"], "NOT_AVAILABLE")

    def test_wss_18_conflicting_inventory_exact_stop(self) -> None:
        data = self.inputs["WSS-18"]
        payload = dict(data["analysis_template"])
        payload["inventory"] = data["conflicting_inventory"]
        # Provide identity snapshots so the isolated duplicate-inventory stop
        # is the only stop reason (the unified identity check is satisfied).
        payload["preview_before"] = data["target_identity_a"]
        payload["preview_after"] = data["target_identity_b"]
        result = self.module.analyze(payload)
        self.assertEqual(result["stop_reasons"], ["DUPLICATE_INVENTORY_ENTRY"])
        self.assertEqual(result["risk_level"], "STOP")
        self.assertEqual(result["safe_command_form"], "NOT_AVAILABLE")

    def test_wss_18_duplicate_and_unavailable_size_contract(self) -> None:
        fixture = [
            {"path_utf16le_hex": "4100", "type": "F", "size_state": "UNAVAILABLE", "size": None},
            {"path_utf16le_hex": "4100", "type": "F", "size_state": "UNAVAILABLE", "size": None},
        ]
        self.assertEqual(self.module.inventory_digest(fixture),
                         self.module.inventory_digest([fixture[0]]))


class WindowsShellSafeCliTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.secrets = json.loads(SECRETS.read_text(encoding="utf-8"))
        cls.inputs = json.loads(INPUTS.read_text(encoding="utf-8"))

    def _run_cli(self, payload_text: str, *args) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(IMPLEMENTATION), *args],
            input=payload_text, text=True, capture_output=True, check=False, timeout=60,
        )

    def test_cli_stdin_stdout_contract(self) -> None:
        proc = self._run_cli(json.dumps(self.inputs["WSS-03"]))
        self.assertEqual(proc.returncode, 0, proc.stderr)
        result = json.loads(proc.stdout)
        self.assertEqual(result["execution_authorized"], "NO")

    def test_cli_malformed_json_exit_2_redacted(self) -> None:
        secret = self.secrets["token"]
        bad = '{"command": "' + secret + '", broken'
        proc = self._run_cli(bad)
        self.assertEqual(proc.returncode, 2)
        self.assertNotIn(secret, proc.stdout)
        self.assertNotIn(secret, proc.stderr)

    def test_cli_output_flag_rejected_and_no_write(self) -> None:
        """The analyzer is read-only: --output is rejected and no file is written."""
        with tempfile.TemporaryDirectory(prefix="wss-cli-") as tmp:
            out = Path(tmp) / "result.json"
            proc = self._run_cli(json.dumps(self.inputs["WSS-03"]), "--output", str(out))
            self.assertNotEqual(proc.returncode, 0)
            self.assertFalse(out.exists(), "the CLI must never write a report file")
            self.assertIn("usage", proc.stderr.lower())

    def test_cli_utf8_stdout_under_ascii_ioencoding(self) -> None:
        """stdout is explicit UTF-8 bytes, independent of the process encoding."""
        with tempfile.TemporaryDirectory(prefix="wss-utf8-") as tmp:
            payload_file = Path(tmp) / "payload.json"
            payload_file.write_text(json.dumps({
                "shell": {"family": "POWERSHELL_7_PLUS", "confidence": "CONFIRMED"},
                "command": "Get-Item 'C:\\Synthetic\\中文\\文件.txt'",
            }), encoding="utf-8")
            env = dict(os.environ)
            env["PYTHONIOENCODING"] = "ascii"
            env["PYTHONUTF8"] = "0"
            proc = subprocess.run(
                [sys.executable, str(IMPLEMENTATION), "--input", str(payload_file)],
                capture_output=True, check=False, env=env, timeout=60,
            )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        text = proc.stdout.decode("utf-8")
        self.assertNotIn("\ufeff", text)
        self.assertNotIn("\r\n", text)
        result = json.loads(text)
        self.assertEqual(result["execution_authorized"], "NO")
        self.assertIn("中文", text)  # the UTF-8 bytes carry the non-ASCII command

    def test_cli_conservative_identity_exit_1(self) -> None:
        proc = self._run_cli(json.dumps(self.inputs["WSS-16"]))
        self.assertEqual(proc.returncode, 1)
        result = json.loads(proc.stdout)
        self.assertEqual(result["execution_authorized"], "NO")

    def test_cli_secret_free_on_sensitive_input(self) -> None:
        secret = self.secrets["token"]
        payload = dict(self.inputs["WSS-17"])
        payload["command"] = payload["command"].replace("SYNTHETIC_TOKEN_DO_NOT_USE", secret)
        proc = self._run_cli(json.dumps(payload))
        self.assertEqual(proc.returncode, 0)
        self.assertNotIn(secret, proc.stdout)
        self.assertNotIn(secret, proc.stderr)

    def test_cli_context_file_flag(self) -> None:
        context = {
            "environment": {"ps_edition": "Desktop", "ps_version": "5.1.26100.9168"},
            "executable": {}, "target": {},
        }
        payload = {"shell": {"family": "UNKNOWN", "confidence": "UNKNOWN"},
                   "command": "Get-ChildItem ."}
        with tempfile.TemporaryDirectory(prefix="wss-ctx-") as tmp:
            ctx_file = Path(tmp) / "context.json"
            ctx_file.write_text(json.dumps(context), encoding="utf-8")
            proc = self._run_cli(json.dumps(payload), "--context", str(ctx_file))
        self.assertEqual(proc.returncode, 0, proc.stderr)
        result = json.loads(proc.stdout)
        self.assertEqual(result["shell_family"], "WINDOWS_POWERSHELL_5_1")
        self.assertEqual(result["detection_confidence"], "CONFIRMED")

    def test_cli_context_file_in_payload(self) -> None:
        context = {
            "environment": {"ps_edition": "Core", "ps_version": "7.4.6"},
            "executable": {}, "target": {},
        }
        with tempfile.TemporaryDirectory(prefix="wss-ctx-") as tmp:
            ctx_file = Path(tmp) / "context.json"
            ctx_file.write_text(json.dumps(context), encoding="utf-8")
            payload = {"shell": {"family": "UNKNOWN", "confidence": "UNKNOWN"},
                       "command": "Get-ChildItem .", "context_file": str(ctx_file)}
            proc = self._run_cli(json.dumps(payload))
        self.assertEqual(proc.returncode, 0, proc.stderr)
        result = json.loads(proc.stdout)
        self.assertEqual(result["shell_family"], "POWERSHELL_7_PLUS")


class WindowsShellSafeContextTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.module = _load_module()

    def _analyze(self, payload: dict) -> dict:
        with patch.object(subprocess, "run", side_effect=AssertionError("shell launch forbidden")), \
             patch.object(subprocess, "Popen", side_effect=AssertionError("shell launch forbidden")), \
             patch.object(subprocess, "call", side_effect=AssertionError("shell launch forbidden")), \
             patch.object(subprocess, "check_call", side_effect=AssertionError("shell launch forbidden")), \
             patch.object(subprocess, "check_output", side_effect=AssertionError("shell launch forbidden")), \
             patch.object(os, "system", side_effect=AssertionError("shell launch forbidden")), \
             patch.object(os, "popen", side_effect=AssertionError("shell launch forbidden")):
            return self.module.analyze(payload)

    def test_context_confirms_shell_identity(self) -> None:
        context = {
            "environment": {
                "ps_edition": "Desktop",
                "ps_version": "5.1.26100.9168",
                "current_process_path": r"C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe",
                "host_name": "ConsoleHost",
            },
            "executable": {}, "target": {},
        }
        payload = {"shell": {"family": "UNKNOWN", "confidence": "UNKNOWN"},
                   "command": "Get-ChildItem .", "context": context}
        result = self._analyze(payload)
        self.assertEqual(result["shell_family"], "WINDOWS_POWERSHELL_5_1")
        self.assertEqual(result["detection_confidence"], "CONFIRMED")
        self.assertEqual(result["host_process"], "ConsoleHost")
        self.assertIn("powershell.exe", result["shell_executable"])

    def test_context_machine_path_sanitization(self) -> None:
        user_path = ("C:" + r"\Users" + r"\Administrator" +
                     r"\AppData\Local\Microsoft\WindowsApps\bash.exe")
        context = {
            "environment": {"ps_edition": "Core", "ps_version": "7.4.6"},
            "executable": {
                "requested": "bash", "found": True, "command_type": "Application",
                "resolved_path": user_path, "in_windows_apps": True,
            },
            "target": {},
        }
        payload = {"shell": {"family": "GIT_BASH", "confidence": "CONFIRMED"},
                   "command": "bash -c echo", "context": context}
        result = self._analyze(payload)
        # GIT_BASH is the command's shell; the collector's PowerShell host
        # is not a contradiction, so the family is preserved.
        self.assertEqual(result["shell_family"], "GIT_BASH")
        codes = {f["code"] for f in result["findings"]}
        self.assertIn("WINDOWSAPPS_STUB_DETECTED", codes)
        self.assertIn("<USER>", result["shell_executable"])
        self.assertTrue(result["shell_executable"].endswith("bash.exe"))
        self.assertEqual(result["shell_executable"],
                         user_path.replace("Administrator", "<USER>"))
        serialized = json.dumps(result, ensure_ascii=False)
        self.assertIn("Administrator", user_path)  # the fixture really contains it
        self.assertNotIn("Administrator", serialized)

    def test_context_executable_not_found_stops(self) -> None:
        context = {"environment": {},
                   "executable": {"requested": "git", "found": False, "resolved_path": ""},
                   "target": {}}
        payload = {"shell": {"family": "POWERSHELL_7_PLUS", "confidence": "CONFIRMED"},
                   "command": "git pull", "executable": {"resolved": False},
                   "context": context}
        result = self._analyze(payload)
        self.assertIn("EXECUTABLE_NOT_FOUND", result["stop_reasons"])
        self.assertEqual(result["risk_level"], "STOP")

    def test_context_target_not_found_stops(self) -> None:
        context = {"environment": {}, "executable": {},
                   "target": {"requested": r"C:\Synthetic\repo\missing",
                              "full_path": r"C:\Synthetic\repo\missing",
                              "exists": False, "error": ""}}
        payload = {
            "shell": {"family": "POWERSHELL_7_PLUS", "confidence": "CONFIRMED"},
            "command": "Remove-Item -LiteralPath C:\\Synthetic\\repo\\missing",
            "working_directory": r"C:\Synthetic\repo",
            "allowed_root": r"C:\Synthetic\repo",
            "target": r"C:\Synthetic\repo\missing",
            "destructive": True,
            "context": context,
        }
        result = self._analyze(payload)
        self.assertIn("TARGET_NOT_FOUND", result["stop_reasons"])
        self.assertEqual(result["risk_level"], "STOP")
        self.assertEqual(result["safe_command_form"], "NOT_AVAILABLE")

    def test_context_target_reparse_stops(self) -> None:
        context = {"environment": {}, "executable": {},
                   "target": {"requested": r"C:\Synthetic\repo\link",
                              "full_path": r"C:\Synthetic\repo\link",
                              "exists": True, "is_reparse_point": True,
                              "link_type": "Junction", "error": ""}}
        payload = {
            "shell": {"family": "POWERSHELL_7_PLUS", "confidence": "CONFIRMED"},
            "command": "Remove-Item -Recurse -LiteralPath C:\\Synthetic\\repo\\link",
            "working_directory": r"C:\Synthetic\repo",
            "allowed_root": r"C:\Synthetic\repo",
            "target": r"C:\Synthetic\repo\link",
            "destructive": True,
            "context": context,
        }
        result = self._analyze(payload)
        self.assertIn("REPARSE_POINT_DESTRUCTIVE_TARGET", result["stop_reasons"])
        self.assertEqual(result["risk_level"], "STOP")

    def test_context_target_unresolved_stops(self) -> None:
        context = {"environment": {}, "executable": {},
                   "target": {"requested": r"C:\Synthetic\bad<>",
                              "full_path": r"C:\Synthetic\bad<>",
                              "exists": False,
                              "error": "target resolution failed: invalid chars"}}
        payload = {
            "shell": {"family": "POWERSHELL_7_PLUS", "confidence": "CONFIRMED"},
            "command": "Remove-Item -LiteralPath C:\\Synthetic\\bad<>",
            "working_directory": r"C:\Synthetic",
            "allowed_root": r"C:\Synthetic",
            "target": r"C:\Synthetic\bad<>",
            "destructive": True,
            "context": context,
        }
        result = self._analyze(payload)
        self.assertIn("TARGET_IDENTITY_UNAVAILABLE", result["stop_reasons"])
        self.assertEqual(result["risk_level"], "STOP")

    def test_context_shell_conflict_stops(self) -> None:
        context = {"environment": {"ps_edition": "Desktop", "ps_version": "5.1"},
                   "executable": {}, "target": {}}
        payload = {"shell": {"family": "POWERSHELL_7_PLUS", "confidence": "CONFIRMED"},
                   "command": "Get-ChildItem .", "context": context}
        result = self._analyze(payload)
        self.assertIn("SHELL_EVIDENCE_CONFLICT", result["stop_reasons"])
        self.assertEqual(result["shell_family"], "UNKNOWN")


class WindowsShellSafeFailClosedTests(unittest.TestCase):
    """Auto-detection and fail-closed destructive/high-impact behavior.

    These call the real analyzer with no-launch patches and assert on
    structure and behavior, not keywords.
    """

    @classmethod
    def setUpClass(cls) -> None:
        cls.module = _load_module()

    def _analyze(self, payload: dict) -> dict:
        with patch.object(subprocess, "run", side_effect=AssertionError("shell launch forbidden")), \
             patch.object(subprocess, "Popen", side_effect=AssertionError("shell launch forbidden")), \
             patch.object(subprocess, "call", side_effect=AssertionError("shell launch forbidden")), \
             patch.object(subprocess, "check_call", side_effect=AssertionError("shell launch forbidden")), \
             patch.object(subprocess, "check_output", side_effect=AssertionError("shell launch forbidden")), \
             patch.object(os, "system", side_effect=AssertionError("shell launch forbidden")), \
             patch.object(os, "popen", side_effect=AssertionError("shell launch forbidden")):
            return self.module.analyze(payload)

    def test_A_remove_item_recurse_auto_stops(self) -> None:
        """Remove-Item -Recurse without a destructive flag must STOP."""
        result = self._analyze({
            "shell": {"family": "POWERSHELL_7_PLUS", "confidence": "CONFIRMED"},
            "command": "Remove-Item -Recurse C:\\Windows",
            "working_directory": "C:\\repo",
            "allowed_root": "C:\\repo",
            "target": "C:\\Windows",
        })
        self.assertEqual(result["execution_authorized"], "NO")
        self.assertEqual(result["risk_level"], "STOP")
        self.assertEqual(result["safe_command_form"], "NOT_AVAILABLE")
        self.assertIn("TARGET_OUTSIDE_ALLOWED_ROOT", result["stop_reasons"])
        self.assertIn("TARGET_IDENTITY_UNAVAILABLE", result["stop_reasons"])
        self.assertIn("DESTRUCTIVE_FILESYSTEM_OPERATION",
                      result["command_classification"]["secondary"])

    def test_B_rm_f_nonrecursive_auto_destructive(self) -> None:
        """rm -f is destructive even when non-recursive."""
        result = self._analyze({
            "shell": {"family": "GIT_BASH", "confidence": "CONFIRMED"},
            "command": "rm -f t",
            "working_directory": "C:\\repo",
            "allowed_root": "C:\\repo",
            "target": "C:\\repo\\t",
        })
        self.assertIn("DESTRUCTIVE_FILESYSTEM_OPERATION",
                      result["command_classification"]["secondary"])
        self.assertEqual(result["risk_level"], "STOP")
        self.assertIn("TARGET_IDENTITY_UNAVAILABLE", result["stop_reasons"])
        self.assertEqual(result["safe_command_form"], "NOT_AVAILABLE")

    def test_C_path_escape_out_of_bounds(self) -> None:
        """C:\safe\..\Windows must not be treated as inside C:\safe."""
        self.assertFalse(self.module._component_contained(r"C:\safe\..\Windows", r"C:\safe"))
        self.assertTrue(self.module._component_contained(r"C:\safe\sub", r"C:\safe"))
        self.assertFalse(self.module._component_contained(r"D:\safe\x", r"C:\safe"))
        self.assertFalse(self.module._component_contained(r"C:\safe2", r"C:\safe"))
        result = self._analyze({
            "shell": {"family": "POWERSHELL_7_PLUS", "confidence": "CONFIRMED"},
            "command": "Remove-Item -LiteralPath C:\\safe\\..\\Windows",
            "working_directory": "C:\\safe",
            "allowed_root": "C:\\safe",
            "target": "C:\\safe\\..\\Windows",
        })
        self.assertEqual(result["risk_level"], "STOP")
        self.assertIn("TARGET_OUTSIDE_ALLOWED_ROOT", result["stop_reasons"])
        self.assertEqual(result["safe_command_form"], "NOT_AVAILABLE")

    def test_D_nonrecursive_destructive_requires_identity(self) -> None:
        """A non-recursive delete without target identity must STOP."""
        result = self._analyze({
            "shell": {"family": "POWERSHELL_7_PLUS", "confidence": "CONFIRMED"},
            "command": "Remove-Item -LiteralPath C:\\repo\\target",
            "working_directory": "C:\\repo",
            "allowed_root": "C:\\repo",
            "target": "C:\\repo\\target",
        })
        self.assertIn("TARGET_IDENTITY_UNAVAILABLE", result["stop_reasons"])
        self.assertEqual(result["risk_level"], "STOP")
        self.assertEqual(result["safe_command_form"], "NOT_AVAILABLE")

    def test_E_high_impact_never_low(self) -> None:
        """registry delete, elevation, and install must not return LOW."""
        cases = [
            ({"family": "POWERSHELL_7_PLUS", "confidence": "CONFIRMED"},
             "winget install synthetic-package", "NETWORK_DOWNLOAD_INSTALL_OPERATION"),
            ({"family": "CMD", "confidence": "CONFIRMED"},
             "reg delete HKCU\\Software\\Synthetic /f", "REGISTRY_OPERATION"),
            ({"family": "POWERSHELL_7_PLUS", "confidence": "CONFIRMED"},
             "Start-Process -Verb RunAs notepad", "PRIVILEGE_ELEVATION_OPERATION"),
        ]
        for shell, command, code in cases:
            with self.subTest(command=command):
                result = self._analyze({"shell": shell, "command": command})
                self.assertNotEqual(result["risk_level"], "LOW", command)
                self.assertIn(code, [f["code"] for f in result["findings"]], command)
                self.assertEqual(result["safe_command_form"], "NOT_AVAILABLE", command)
                self.assertEqual(result["execution_authorized"], "NO", command)

    def test_nested_and_piped_destructive_enter_protection(self) -> None:
        """Destructive words at command position (leading space, after an
        operator, or inside a nested-shell payload) enter the protection
        branch and STOP when evidence is insufficient."""
        cases = [
            ({"family": "POWERSHELL_7_PLUS", "confidence": "CONFIRMED"},
             "   Remove-Item -Recurse C:\\Windows"),
            ({"family": "POWERSHELL_7_PLUS", "confidence": "CONFIRMED"},
             "Write-Output x | Remove-Item C:\\Windows"),
            ({"family": "POWERSHELL_7_PLUS", "confidence": "CONFIRMED"},
             "echo x && rm -f target"),
            ({"family": "CMD", "confidence": "CONFIRMED"},
             "cmd /c del C:\\temp\\x"),
            ({"family": "POWERSHELL_7_PLUS", "confidence": "CONFIRMED"},
             "powershell -Command \"Remove-Item C:\\temp\\x\""),
            ({"family": "POWERSHELL_7_PLUS", "confidence": "CONFIRMED"},
             "pwsh -Command 'Remove-Item C:\\temp\\x'"),
        ]
        for shell, command in cases:
            with self.subTest(command=command):
                result = self._analyze({
                    "shell": shell,
                    "command": command,
                    "working_directory": "C:\\repo",
                    "allowed_root": "C:\\repo",
                    "target": "C:\\repo\\target",
                })
                self.assertIn("DESTRUCTIVE_FILESYSTEM_OPERATION",
                              result["command_classification"]["secondary"], command)
                self.assertEqual(result["risk_level"], "STOP", command)
                self.assertEqual(result["safe_command_form"], "NOT_AVAILABLE", command)
                self.assertEqual(result["execution_authorized"], "NO", command)

    def test_readonly_text_and_path_not_destructive(self) -> None:
        """Quoted text and path components must never be misjudged destructive."""
        cases = [
            ({"family": "POWERSHELL_7_PLUS", "confidence": "CONFIRMED"},
             "Write-Output 'Remove-Item is a cmdlet'"),
            ({"family": "POWERSHELL_7_PLUS", "confidence": "CONFIRMED"},
             "Get-Content C:\\example\\del\\file"),
        ]
        for shell, command in cases:
            with self.subTest(command=command):
                result = self._analyze({"shell": shell, "command": command,
                                        "working_directory": "C:\\repo",
                                        "allowed_root": "C:\\repo",
                                        "target": "C:\\repo\\target"})
                self.assertNotIn("DESTRUCTIVE_FILESYSTEM_OPERATION",
                                 result["command_classification"]["secondary"], command)
                self.assertNotIn("TARGET_IDENTITY_UNAVAILABLE", result["stop_reasons"], command)

    def test_executor_with_preceding_switches_still_detected(self) -> None:
        """Executor switches before the payload flag (-NoProfile,
        -ExecutionPolicy Bypass, /d, /s, --noprofile, quoted executable path)
        must not lose the executor state: the payload is still analyzed."""
        cases = [
            ({"family": "POWERSHELL_7_PLUS", "confidence": "CONFIRMED"},
             'powershell -NoProfile -Command "Remove-Item C:\\Windows\\x"'),
            ({"family": "POWERSHELL_7_PLUS", "confidence": "CONFIRMED"},
             'pwsh -NoProfile -ExecutionPolicy Bypass -Command "Remove-Item C:\\Windows\\x"'),
            ({"family": "CMD", "confidence": "CONFIRMED"},
             "cmd /d /s /c del C:\\Windows\\x"),
            ({"family": "GIT_BASH", "confidence": "CONFIRMED"},
             'bash --noprofile -c "rm -f target"'),
            ({"family": "POWERSHELL_7_PLUS", "confidence": "CONFIRMED"},
             '"C:\\Program Files\\PowerShell\\7\\pwsh.exe" -NoProfile -Command "Remove-Item C:\\Windows\\x"'),
        ]
        for shell, command in cases:
            with self.subTest(command=command):
                result = self._analyze({
                    "shell": shell, "command": command,
                    "working_directory": "C:\\repo", "allowed_root": "C:\\repo",
                    "target": "C:\\repo\\target",
                })
                self.assertIn("DESTRUCTIVE_FILESYSTEM_OPERATION",
                              result["command_classification"]["secondary"], command)
                self.assertEqual(result["risk_level"], "STOP", command)
                self.assertEqual(result["safe_command_form"], "NOT_AVAILABLE", command)
                self.assertEqual(result["execution_authorized"], "NO", command)

    def test_executor_mention_in_string_not_destructive(self) -> None:
        """Quoted text that merely mentions an executor payload is not a
        destructive command."""
        result = self._analyze({
            "shell": {"family": "POWERSHELL_7_PLUS", "confidence": "CONFIRMED"},
            "command": "Write-Output 'powershell -NoProfile -Command Remove-Item C:\\Windows\\x'",
            "working_directory": "C:\\repo", "allowed_root": "C:\\repo",
            "target": "C:\\repo\\target",
        })
        self.assertNotIn("DESTRUCTIVE_FILESYSTEM_OPERATION",
                         result["command_classification"]["secondary"])
        self.assertNotIn("TARGET_IDENTITY_UNAVAILABLE", result["stop_reasons"])

    def test_opaque_encoded_payload_stops(self) -> None:
        """PowerShell -EncodedCommand carrying a destructive command must
        STOP, never return LOW; the Base64 payload is not decoded."""
        base64 = ("UgBlAG0AbwB2AGUALQBJAHQAZQBtACAALQBMAGkAdABlAHIAYQBsAFAAYQB0AGgA"
                  "IABDADoAXABXAGkAbgBkAG8AdwBzAFwAeAAuAHQAeAB0AA==")
        result = self._analyze({
            "shell": {"family": "POWERSHELL_7_PLUS", "confidence": "CONFIRMED"},
            "executable": {"resolved": True},
            "command": "powershell -EncodedCommand " + base64,
        })
        self.assertEqual(result["stop_reasons"], ["OPAQUE_EXECUTOR_PAYLOAD"])
        self.assertEqual(result["risk_level"], "STOP")
        self.assertEqual(result["safe_command_form"], "NOT_AVAILABLE")
        self.assertEqual(result["execution_authorized"], "NO")
        self.assertEqual(result["execution_mode"], "DIRECT")  # no -NoExit

    def test_opaque_file_payload_stops(self) -> None:
        """PowerShell -File runs an uninspectable script file -> STOP."""
        result = self._analyze({
            "shell": {"family": "POWERSHELL_7_PLUS", "confidence": "CONFIRMED"},
            "executable": {"resolved": True},
            "command": "powershell -File C:\\scripts\\unknown.ps1",
        })
        self.assertEqual(result["stop_reasons"], ["OPAQUE_EXECUTOR_PAYLOAD"])
        self.assertEqual(result["risk_level"], "STOP")
        self.assertEqual(result["safe_command_form"], "NOT_AVAILABLE")
        self.assertEqual(result["execution_authorized"], "NO")
        self.assertEqual(result["execution_mode"], "DIRECT")  # no -NoExit

    def test_interactive_executor_stops(self) -> None:
        """An executor with no transparent payload enters an uninspectable
        interactive shell -> STOP, execution_mode INTERACTIVE."""
        result = self._analyze({
            "shell": {"family": "POWERSHELL_7_PLUS", "confidence": "CONFIRMED"},
            "executable": {"resolved": True},
            "command": "powershell -NoProfile",
        })
        self.assertEqual(result["stop_reasons"], ["OPAQUE_EXECUTOR_PAYLOAD"])
        self.assertEqual(result["risk_level"], "STOP")
        self.assertEqual(result["safe_command_form"], "NOT_AVAILABLE")
        self.assertEqual(result["execution_authorized"], "NO")
        self.assertEqual(result["execution_mode"], "INTERACTIVE")

    def test_persistent_interactive_executor_stops(self) -> None:
        """-NoExit and cmd /k run the payload then stay interactive: the
        payload is still checked, but the session must STOP."""
        cases = [
            ({"family": "POWERSHELL_7_PLUS", "confidence": "CONFIRMED"},
             'powershell -NoExit -Command "Write-Output ok"'),
            ({"family": "CMD", "confidence": "CONFIRMED"},
             "cmd /k echo ok"),
        ]
        for shell, command in cases:
            with self.subTest(command=command):
                result = self._analyze({
                    "shell": shell, "executable": {"resolved": True}, "command": command,
                })
                self.assertEqual(result["stop_reasons"], ["OPAQUE_EXECUTOR_PAYLOAD"], command)
                self.assertEqual(result["risk_level"], "STOP", command)
                self.assertEqual(result["safe_command_form"], "NOT_AVAILABLE", command)
                self.assertEqual(result["execution_authorized"], "NO", command)
                self.assertEqual(result["execution_mode"], "INTERACTIVE", command)

    def test_uninspectable_transparent_payload_stops(self) -> None:
        """-Command -, variable payloads, and PowerShell script blocks cannot
        be statically inspected and must STOP as opaque."""
        cases = [
            ({"family": "POWERSHELL_7_PLUS", "confidence": "CONFIRMED"},
             "powershell -Command -"),
            ({"family": "CMD", "confidence": "CONFIRMED"},
             "cmd /c %PAYLOAD%"),
            ({"family": "GIT_BASH", "confidence": "CONFIRMED"},
             "bash -c $PAYLOAD"),
            ({"family": "CMD", "confidence": "CONFIRMED"},
             'cmd /c powershell -Command "& { Remove-Item C:/Windows/x }"'),
        ]
        for shell, command in cases:
            with self.subTest(command=command):
                result = self._analyze({
                    "shell": shell, "executable": {"resolved": True}, "command": command,
                })
                self.assertEqual(result["stop_reasons"], ["OPAQUE_EXECUTOR_PAYLOAD"], command)
                self.assertEqual(result["risk_level"], "STOP", command)
                self.assertEqual(result["safe_command_form"], "NOT_AVAILABLE", command)
                self.assertEqual(result["execution_authorized"], "NO", command)

    def test_dynamic_command_position_stops(self) -> None:
        """A dynamic command identity inside a transparent payload (& $x,
        iex / Invoke-Expression, call %x%, !x!, eval $x, after an operator)
        must STOP as opaque and propagate through nested executors."""
        cases = [
            ({"family": "POWERSHELL_7_PLUS", "confidence": "CONFIRMED"},
             'powershell -Command "& $PAYLOAD"'),
            ({"family": "POWERSHELL_7_PLUS", "confidence": "CONFIRMED"},
             'powershell -Command "Write-Output ok; & $PAYLOAD"'),
            ({"family": "POWERSHELL_7_PLUS", "confidence": "CONFIRMED"},
             'powershell -Command "Invoke-Expression $PAYLOAD"'),
            ({"family": "POWERSHELL_7_PLUS", "confidence": "CONFIRMED"},
             'powershell -Command "iex $PAYLOAD"'),
            ({"family": "CMD", "confidence": "CONFIRMED"},
             "cmd /c !PAYLOAD!"),
            ({"family": "CMD", "confidence": "CONFIRMED"},
             'cmd /c "call %PAYLOAD%"'),
            ({"family": "GIT_BASH", "confidence": "CONFIRMED"},
             'bash -c "eval $PAYLOAD"'),
            ({"family": "CMD", "confidence": "CONFIRMED"},
             'cmd /c powershell -Command "& $PAYLOAD"'),
        ]
        for shell, command in cases:
            with self.subTest(command=command):
                result = self._analyze({
                    "shell": shell,
                    "executable": {"identity": "NATIVE_EXECUTABLE", "resolved": True},
                    "command": command,
                })
                self.assertEqual(result["stop_reasons"], ["OPAQUE_EXECUTOR_PAYLOAD"], command)
                self.assertEqual(result["risk_level"], "STOP", command)
                self.assertEqual(result["safe_command_form"], "NOT_AVAILABLE", command)
                self.assertEqual(result["execution_authorized"], "NO", command)

    def test_dynamic_data_not_opaque(self) -> None:
        """A variable in plain argument position is data, not a dynamic
        command."""
        cases = [
            ({"family": "GIT_BASH", "confidence": "CONFIRMED"},
             'bash -c "echo $HOME"'),
            ({"family": "POWERSHELL_7_PLUS", "confidence": "CONFIRMED"},
             'powershell -Command "Write-Output $env:TEMP"'),
            ({"family": "CMD", "confidence": "CONFIRMED"},
             'cmd /c "echo %TEMP%"'),
        ]
        for shell, command in cases:
            with self.subTest(command=command):
                result = self._analyze({
                    "shell": shell,
                    "executable": {"identity": "NATIVE_EXECUTABLE", "resolved": True},
                    "command": command,
                })
                self.assertNotIn("OPAQUE_EXECUTOR_PAYLOAD", result["stop_reasons"], command)
                self.assertEqual(result["execution_authorized"], "NO", command)

    def test_brace_script_block_stops(self) -> None:
        """A real PowerShell script block ({ ... } outside literals) is an
        unparsable payload and must STOP, including nested in cmd /c."""
        cases = [
            ({"family": "POWERSHELL_7_PLUS", "confidence": "CONFIRMED"},
             'powershell -Command "& { Remove-Item C:/Windows/x }"'),
            ({"family": "CMD", "confidence": "CONFIRMED"},
             'cmd /c powershell -Command "& { Remove-Item C:/Windows/x }"'),
        ]
        for shell, command in cases:
            with self.subTest(command=command):
                result = self._analyze({
                    "shell": shell,
                    "executable": {"identity": "NATIVE_EXECUTABLE", "resolved": True},
                    "command": command,
                })
                self.assertEqual(result["stop_reasons"], ["OPAQUE_EXECUTOR_PAYLOAD"], command)
                self.assertEqual(result["risk_level"], "STOP", command)
                self.assertEqual(result["safe_command_form"], "NOT_AVAILABLE", command)
                self.assertEqual(result["execution_authorized"], "NO", command)

    def test_brace_in_literal_or_non_powershell_not_opaque(self) -> None:
        """Braces inside string literals (PowerShell) or in CMD/Bash payloads
        are text, not structural script blocks."""
        cases = [
            ({"family": "POWERSHELL_7_PLUS", "confidence": "CONFIRMED"},
             'powershell -Command "Write-Output \'{literal}\'"'),
            ({"family": "CMD", "confidence": "CONFIRMED"},
             'cmd /c "echo {ok}"'),
            ({"family": "GIT_BASH", "confidence": "CONFIRMED"},
             'bash -c "echo {a,b}"'),
        ]
        for shell, command in cases:
            with self.subTest(command=command):
                result = self._analyze({
                    "shell": shell,
                    "executable": {"identity": "NATIVE_EXECUTABLE", "resolved": True},
                    "command": command,
                })
                self.assertNotIn("OPAQUE_EXECUTOR_PAYLOAD", result["stop_reasons"], command)

    def test_persistent_with_opaque_payload_interactive(self) -> None:
        """-NoExit / cmd /k keep the session interactive even when the payload
        is opaque (file/encoded) or nested; execution_mode must be
        INTERACTIVE independently of the opaque reason."""
        base64 = ("UgBlAG0AbwB2AGUALQBJAHQAZQBtACAALQBMAGkAdABlAHIAYQBsAFAAYQB0AGgA"
                  "IABDADoAXABXAGkAbgBkAG8AdwBzAFwAeAAuAHQAeAB0AA==")
        cases = [
            ({"family": "POWERSHELL_7_PLUS", "confidence": "CONFIRMED"},
             'powershell -NoExit -Command "Write-Output ok"'),
            ({"family": "POWERSHELL_7_PLUS", "confidence": "CONFIRMED"},
             "powershell -NoExit -File C:\\scripts\\x.ps1"),
            ({"family": "POWERSHELL_7_PLUS", "confidence": "CONFIRMED"},
             "powershell -NoExit -EncodedCommand " + base64),
            ({"family": "CMD", "confidence": "CONFIRMED"},
             "cmd /k echo ok"),
            ({"family": "CMD", "confidence": "CONFIRMED"},
             'cmd /c powershell -NoExit -File C:\\scripts\\x.ps1'),
        ]
        for shell, command in cases:
            with self.subTest(command=command):
                result = self._analyze({
                    "shell": shell,
                    "executable": {"identity": "NATIVE_EXECUTABLE", "resolved": True},
                    "command": command,
                })
                self.assertEqual(result["execution_mode"], "INTERACTIVE", command)
                self.assertEqual(result["risk_level"], "STOP", command)
                self.assertIn("OPAQUE_EXECUTOR_PAYLOAD", result["stop_reasons"], command)
                self.assertEqual(result["safe_command_form"], "NOT_AVAILABLE", command)
                self.assertEqual(result["execution_authorized"], "NO", command)

    def test_quoted_dynamic_command_position_stops(self) -> None:
        """A quoted dynamic token at command position (after & or an operator)
        is a dynamic command identity and must STOP."""
        cases = [
            ({"family": "POWERSHELL_7_PLUS", "confidence": "CONFIRMED"},
             'powershell -Command \'& "$PAYLOAD"\''),
            ({"family": "POWERSHELL_7_PLUS", "confidence": "CONFIRMED"},
             'powershell -Command \'Write-Output ok; & "$PAYLOAD"\''),
        ]
        for shell, command in cases:
            with self.subTest(command=command):
                result = self._analyze({
                    "shell": shell,
                    "executable": {"identity": "NATIVE_EXECUTABLE", "resolved": True},
                    "command": command,
                })
                self.assertEqual(result["stop_reasons"], ["OPAQUE_EXECUTOR_PAYLOAD"], command)
                self.assertEqual(result["risk_level"], "STOP", command)
                self.assertEqual(result["safe_command_form"], "NOT_AVAILABLE", command)
                self.assertEqual(result["execution_authorized"], "NO", command)

    def test_quoted_evaluator_argument_stops(self) -> None:
        """Evaluator state persists across quoted args and evaluator switches
        (Invoke-Expression -Command $x); a dynamic argument must STOP."""
        cases = [
            ({"family": "POWERSHELL_7_PLUS", "confidence": "CONFIRMED"},
             'powershell -Command \'Invoke-Expression "$PAYLOAD"\''),
            ({"family": "POWERSHELL_7_PLUS", "confidence": "CONFIRMED"},
             'powershell -Command \'iex "$PAYLOAD"\''),
            ({"family": "POWERSHELL_7_PLUS", "confidence": "CONFIRMED"},
             'powershell -Command "Invoke-Expression -Command $PAYLOAD"'),
            ({"family": "GIT_BASH", "confidence": "CONFIRMED"},
             'bash -c \'eval "$PAYLOAD"\''),
            ({"family": "CMD", "confidence": "CONFIRMED"},
             'cmd /c \'call "%PAYLOAD%"\''),
        ]
        for shell, command in cases:
            with self.subTest(command=command):
                result = self._analyze({
                    "shell": shell,
                    "executable": {"identity": "NATIVE_EXECUTABLE", "resolved": True},
                    "command": command,
                })
                self.assertEqual(result["stop_reasons"], ["OPAQUE_EXECUTOR_PAYLOAD"], command)
                self.assertEqual(result["risk_level"], "STOP", command)
                self.assertEqual(result["safe_command_form"], "NOT_AVAILABLE", command)
                self.assertEqual(result["execution_authorized"], "NO", command)

    def test_quoted_data_not_dynamic(self) -> None:
        """A quoted variable in plain argument position is data, not a dynamic
        command, even when it mentions $ or %."""
        cases = [
            ({"family": "POWERSHELL_7_PLUS", "confidence": "CONFIRMED"},
             'powershell -Command \'Write-Output "$PAYLOAD"\''),
            ({"family": "POWERSHELL_7_PLUS", "confidence": "CONFIRMED"},
             'powershell -Command \'Write-Output "$env:TEMP"\''),
            ({"family": "GIT_BASH", "confidence": "CONFIRMED"},
             'bash -c \'echo "$HOME"\''),
            ({"family": "CMD", "confidence": "CONFIRMED"},
             'cmd /c \'echo "%TEMP%"\'')
        ]
        for shell, command in cases:
            with self.subTest(command=command):
                result = self._analyze({
                    "shell": shell,
                    "executable": {"identity": "NATIVE_EXECUTABLE", "resolved": True},
                    "command": command,
                })
                self.assertNotIn("OPAQUE_EXECUTOR_PAYLOAD", result["stop_reasons"], command)
                self.assertEqual(result["execution_authorized"], "NO", command)

    def test_unquoted_script_block_stops(self) -> None:
        """An unquoted PowerShell script block payload must STOP with the
        correct PowerShell executor context (direct and nested under cmd /c)."""
        cases = [
            ({"family": "POWERSHELL_7_PLUS", "confidence": "CONFIRMED"},
             "powershell -Command { Remove-Item C:/Windows/x }"),
            ({"family": "CMD", "confidence": "CONFIRMED"},
             "cmd /c powershell -Command { Remove-Item C:/Windows/x }"),
        ]
        for shell, command in cases:
            with self.subTest(command=command):
                result = self._analyze({
                    "shell": shell,
                    "executable": {"identity": "NATIVE_EXECUTABLE", "resolved": True},
                    "command": command,
                })
                self.assertEqual(result["stop_reasons"], ["OPAQUE_EXECUTOR_PAYLOAD"], command)
                self.assertEqual(result["risk_level"], "STOP", command)
                self.assertEqual(result["safe_command_form"], "NOT_AVAILABLE", command)
                self.assertEqual(result["execution_authorized"], "NO", command)

    def test_transparent_executor_payloads_not_opaque(self) -> None:
        """-Command, cmd /c, and bash -c stay transparent and must not
        regress (still detected as destructive, never OPAQUE)."""
        cases = [
            ({"family": "POWERSHELL_7_PLUS", "confidence": "CONFIRMED"},
             'powershell -Command "Remove-Item C:\\Windows\\x"'),
            ({"family": "CMD", "confidence": "CONFIRMED"},
             "cmd /c del C:\\Windows\\x"),
            ({"family": "GIT_BASH", "confidence": "CONFIRMED"},
             'bash -c "rm -f target"'),
        ]
        for shell, command in cases:
            with self.subTest(command=command):
                result = self._analyze({
                    "shell": shell, "executable": {"resolved": True}, "command": command,
                    "working_directory": "C:\\repo", "allowed_root": "C:\\repo",
                    "target": "C:\\repo\\target",
                })
                self.assertNotIn("OPAQUE_EXECUTOR_PAYLOAD", result["stop_reasons"], command)
                self.assertIn("DESTRUCTIVE_FILESYSTEM_OPERATION",
                              result["command_classification"]["secondary"], command)
                self.assertEqual(result["risk_level"], "STOP", command)
                self.assertEqual(result["safe_command_form"], "NOT_AVAILABLE", command)
                self.assertEqual(result["execution_authorized"], "NO", command)

    def test_opaque_mention_in_string_not_misjudged(self) -> None:
        """Quoted text that merely mentions -EncodedCommand is not opaque."""
        result = self._analyze({
            "shell": {"family": "POWERSHELL_7_PLUS", "confidence": "CONFIRMED"},
            "command": "Write-Output 'powershell -EncodedCommand abc'",
        })
        self.assertNotIn("OPAQUE_EXECUTOR_PAYLOAD", result["stop_reasons"])
        self.assertEqual(result["risk_level"], "LOW")

    def test_multi_operand_destructive_unproven(self) -> None:
        """Two static targets while the evidence supports only one -> STOP."""
        result = self._analyze({
            "shell": {"family": "GIT_BASH", "confidence": "CONFIRMED"},
            "command": "rm C:/safe/ok.txt C:/Windows/x.txt",
            "working_directory": "C:\\safe", "allowed_root": "C:\\safe",
            "target": "C:\\safe\\ok.txt",
        })
        self.assertIn("TARGET_COMMAND_BINDING_UNPROVEN", result["stop_reasons"])
        self.assertEqual(result["risk_level"], "STOP")
        self.assertEqual(result["safe_command_form"], "NOT_AVAILABLE")

    def test_two_destructive_commands_unproven(self) -> None:
        """Two separate delete commands -> STOP, not first-site binding."""
        result = self._analyze({
            "shell": {"family": "GIT_BASH", "confidence": "CONFIRMED"},
            "command": "rm C:/safe/ok.txt ; rm C:/Windows/x.txt",
            "working_directory": "C:\\safe", "allowed_root": "C:\\safe",
            "target": "C:\\safe\\ok.txt",
        })
        self.assertIn("TARGET_COMMAND_BINDING_UNPROVEN", result["stop_reasons"])
        self.assertEqual(result["risk_level"], "STOP")

    def test_mixed_static_dynamic_operand_unproven(self) -> None:
        """A static plus a dynamic target cannot be bound -> STOP."""
        result = self._analyze({
            "shell": {"family": "POWERSHELL_7_PLUS", "confidence": "CONFIRMED"},
            "command": "Remove-Item safe.txt,$dynamicTarget",
            "working_directory": "C:\\safe", "allowed_root": "C:\\safe",
            "target": "C:\\safe\\safe.txt",
        })
        self.assertIn("TARGET_COMMAND_BINDING_UNPROVEN", result["stop_reasons"])
        self.assertEqual(result["risk_level"], "STOP")

    def test_malformed_identity_pair_not_valid(self) -> None:
        """preview_before/after carrying only unrelated fields are not a valid
        identity snapshot pair -> TARGET_IDENTITY_UNAVAILABLE."""
        result = self._analyze({
            "shell": {"family": "POWERSHELL_7_PLUS", "confidence": "CONFIRMED"},
            "command": "Remove-Item -LiteralPath C:\\safe\\target.txt",
            "working_directory": "C:\\safe", "allowed_root": "C:\\safe",
            "target": "C:\\safe\\target.txt",
            "preview_before": {"x": 1},
            "preview_after": {"x": 1},
        })
        self.assertIn("TARGET_IDENTITY_UNAVAILABLE", result["stop_reasons"])
        self.assertEqual(result["risk_level"], "STOP")
        self.assertNotIn("TARGET_CHANGED_DURING_PREVIEW", result["stop_reasons"])

    def test_single_static_target_full_evidence_no_stop(self) -> None:
        """A single static target with complete consistent evidence keeps
        HIGH (never LOW) and has no STOP findings."""
        result = self._analyze({
            "shell": {"family": "POWERSHELL_7_PLUS", "confidence": "CONFIRMED"},
            "command": "Remove-Item -LiteralPath C:\\safe\\target.txt",
            "working_directory": "C:\\safe", "allowed_root": "C:\\safe",
            "target": "C:\\safe\\target.txt",
            "preview_before": {"volume_serial": "SYNTH-VOL", "file_id_128": "SYNTH-ID"},
            "preview_after": {"volume_serial": "SYNTH-VOL", "file_id_128": "SYNTH-ID"},
            "context": {
                "environment": {}, "executable": {},
                "target": {
                    "requested": "C:\\safe\\target.txt", "full_path": "C:\\safe\\target.txt",
                    "exists": True, "is_reparse_point": False, "error": "",
                },
            },
        })
        self.assertEqual(result["stop_reasons"], [])
        self.assertEqual(result["risk_level"], "HIGH")
        self.assertEqual(result["safe_command_form"], "NOT_AVAILABLE")
        self.assertEqual(result["execution_authorized"], "NO")

    def test_TARGET_EVIDENCE_MISMATCH_command_vs_evidence(self) -> None:
        """Command deletes C:\\Windows\\System32\\x.txt while payload/context
        point at C:\\safe\\ok.txt: must STOP with TARGET_EVIDENCE_MISMATCH."""
        result = self._analyze({
            "shell": {"family": "POWERSHELL_7_PLUS", "confidence": "CONFIRMED"},
            "command": "Remove-Item C:\\Windows\\System32\\x.txt",
            "working_directory": "C:\\safe",
            "allowed_root": "C:\\safe",
            "target": "C:\\safe\\ok.txt",
            "context": {
                "environment": {}, "executable": {},
                "target": {
                    "requested": "C:\\safe\\ok.txt", "full_path": "C:\\safe\\ok.txt",
                    "exists": True, "is_reparse_point": False, "error": "",
                },
            },
        })
        self.assertIn("TARGET_EVIDENCE_MISMATCH", result["stop_reasons"])
        self.assertEqual(result["risk_level"], "STOP")
        self.assertEqual(result["safe_command_form"], "NOT_AVAILABLE")
        self.assertEqual(result["execution_authorized"], "NO")

    def test_TARGET_EVIDENCE_MISMATCH_context_requested_vs_full(self) -> None:
        """Collector requested and resolved full path disagree: must STOP."""
        result = self._analyze({
            "shell": {"family": "POWERSHELL_7_PLUS", "confidence": "CONFIRMED"},
            "command": "Remove-Item C:\\safe\\a.txt",
            "working_directory": "C:\\safe",
            "allowed_root": "C:\\safe",
            "target": "C:\\safe\\a.txt",
            "context": {
                "environment": {}, "executable": {},
                "target": {
                    "requested": "C:\\safe\\a.txt", "full_path": "C:\\Windows\\b.txt",
                    "exists": True, "is_reparse_point": False, "error": "",
                },
            },
        })
        self.assertIn("TARGET_EVIDENCE_MISMATCH", result["stop_reasons"])
        self.assertEqual(result["risk_level"], "STOP")

    def test_TARGET_COMMAND_BINDING_UNPROVEN_dynamic_target(self) -> None:
        """A dynamic command target cannot be proven against the evidence."""
        result = self._analyze({
            "shell": {"family": "POWERSHELL_7_PLUS", "confidence": "CONFIRMED"},
            "command": "Remove-Item $path",
            "working_directory": "C:\\safe",
            "allowed_root": "C:\\safe",
            "target": "C:\\safe\\ok.txt",
        })
        self.assertIn("TARGET_COMMAND_BINDING_UNPROVEN", result["stop_reasons"])
        self.assertEqual(result["risk_level"], "STOP")
        self.assertEqual(result["safe_command_form"], "NOT_AVAILABLE")

    def test_single_static_target_full_evidence_no_stop(self) -> None:
        """A single static target with complete consistent evidence keeps
        HIGH (never LOW) and has no STOP findings."""
        result = self._analyze({
            "shell": {"family": "POWERSHELL_7_PLUS", "confidence": "CONFIRMED"},
            "command": "Remove-Item -LiteralPath C:\\safe\\target.txt",
            "working_directory": "C:\\safe",
            "allowed_root": "C:\\safe",
            "target": "C:\\safe\\target.txt",
            "preview_before": {"volume_serial": "SYNTH-VOL", "file_id_128": "SYNTH-ID"},
            "preview_after": {"volume_serial": "SYNTH-VOL", "file_id_128": "SYNTH-ID"},
            "context": {
                "environment": {}, "executable": {},
                "target": {
                    "requested": "C:\\safe\\target.txt", "full_path": "C:\\safe\\target.txt",
                    "exists": True, "is_reparse_point": False, "error": "",
                },
            },
        })
        self.assertEqual(result["stop_reasons"], [])
        self.assertEqual(result["risk_level"], "HIGH")
        self.assertEqual(result["safe_command_form"], "NOT_AVAILABLE")
        self.assertEqual(result["execution_authorized"], "NO")


class CollectWindowsContextTests(unittest.TestCase):
    POWERSHELL = None
    PWSH_PATH = None
    PWSH_SKIP_REASON = None

    @classmethod
    def setUpClass(cls) -> None:
        for cand in (r"C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe",
                     shutil.which("powershell")):
            if cand and Path(cand).exists():
                cls.POWERSHELL = str(cand)
                break
        cls.PWSH_PATH, cls.PWSH_SKIP_REASON = cls._probe_pwsh()

    @classmethod
    def _probe_pwsh(cls) -> tuple[str | None, str | None]:
        """Distinguish: not installed / installed but runtime unavailable for
        the collector / healthy.

        A `shutil.which` hit is not enough: the runtime must actually run the
        collector smoke. A failed smoke is reported with its real reason and
        the full PS7 tests are skipped; only a successful smoke runs them, so
        the probe result and the smoke result can never disagree.
        """
        candidates = [shutil.which("pwsh")]
        candidates += [r"C:\Program Files\PowerShell\7\pwsh.exe",
                       r"C:\Program Files\PowerShell\7-preview\pwsh.exe",
                       str(Path.home() / "AppData" / "Local" / "Programs" / "PowerShell" / "7" / "pwsh.exe")]
        # A bundled pwsh in a user-level runtime cache (e.g. codex-runtimes)
        # is found generically -- no machine-specific absolute path is pinned.
        candidates += [str(p) for p in Path.home().glob(
            ".cache/*/*/dependencies/native/powershell/pwsh.exe")]
        path = next((p for p in candidates if p and Path(p).exists()), None)
        if not path:
            return None, ("PowerShell 7 is not installed (no pwsh on PATH, standard, "
                          "or bundled locations)")
        try:
            with tempfile.TemporaryDirectory(prefix="wss-pwsh-probe-") as tmp:
                probe = subprocess.run(
                    [path, "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass",
                     "-File", str(COLLECTOR), "-Executable", "cmd.exe", "-Target", str(tmp)],
                    capture_output=True, check=False, timeout=60,
                )
        except Exception as exc:  # noqa: BLE001
            return path, f"pwsh exists at {path} but failed to start: {type(exc).__name__}: {exc}"
        if probe.returncode != 0:
            reason = probe.stderr.decode("utf-8", "replace").strip()[:200] or "unknown error"
            reason = re.sub(r"\x1b\[[0-9;]*m", "", reason)
            return path, (f"pwsh is installed at {path} but its runtime is unavailable for "
                          f"the collector (exit {probe.returncode}): {reason}")
        try:
            json.loads(probe.stdout.decode("utf-8"))
        except Exception as exc:  # noqa: BLE001
            return path, (f"pwsh is installed at {path} but the collector output was not "
                          f"valid JSON: {type(exc).__name__}: {exc}")
        return path, None

    def _run(self, exe: str, *args) -> subprocess.CompletedProcess[bytes]:
        return subprocess.run(
            [exe, "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass",
             "-File", str(COLLECTOR), *args],
            capture_output=True, check=False, timeout=90,
        )

    def _assert_schema(self, data: dict) -> None:
        self.assertEqual(data["schema"], "windows-context-v1")
        self.assertEqual(data["collector_version"], "0.2.0")
        for block in ("environment", "executable", "target"):
            self.assertIsInstance(data.get(block), dict)
        env = data["environment"]
        for key in ("ps_edition", "ps_version", "current_process_path",
                    "host_name", "working_directory", "windows_apps_dir"):
            self.assertIn(key, env)
        for key in ("requested", "found", "resolved_path", "in_windows_apps"):
            self.assertIn(key, data["executable"])
        self.assertNotIn("definition", data["executable"],
                         "the collector must never emit command definitions")
        for key in ("requested", "full_path", "exists", "is_reparse_point",
                    "link_type", "error"):
            self.assertIn(key, data["target"])

    def test_windows_powershell_51_smoke(self) -> None:
        if not self.POWERSHELL:
            self.skipTest("Windows PowerShell 5.1 is not available on this host")
        with tempfile.TemporaryDirectory(prefix="wss-collect-") as tmp:
            target = Path(tmp)
            before = _tree_snapshot(target)
            proc = self._run(self.POWERSHELL, "-Executable", "cmd.exe", "-Target", str(target))
        self.assertEqual(proc.returncode, 0, proc.stderr.decode("utf-8", "replace"))
        text = proc.stdout.decode("utf-8")
        data = json.loads(text)
        self._assert_schema(data)
        self.assertEqual(data["environment"]["ps_edition"], "Desktop")
        self.assertTrue(data["environment"]["working_directory"])
        self.assertTrue(data["executable"]["found"])
        self.assertTrue(str(data["executable"]["resolved_path"]).lower().endswith("cmd.exe"))
        self.assertTrue(data["target"]["exists"])
        self.assertEqual(data["target"]["item_type"], "Directory")
        self.assertFalse(data["target"]["is_reparse_point"])
        self.assertEqual(_tree_snapshot(target), before)
        self.assertNotIn(b"\r\n", proc.stdout)

    def test_windows_powershell_51_missing_executable(self) -> None:
        if not self.POWERSHELL:
            self.skipTest("Windows PowerShell 5.1 is not available on this host")
        proc = self._run(self.POWERSHELL, "-Executable", "definitely-not-a-real-exe-xyz-123")
        self.assertEqual(proc.returncode, 0, proc.stderr.decode("utf-8", "replace"))
        data = json.loads(proc.stdout.decode("utf-8"))
        self.assertFalse(data["executable"]["found"])
        self.assertEqual(data["executable"]["requested"], "definitely-not-a-real-exe-xyz-123")

    def test_windows_powershell_51_utf8_cjk_roundtrip(self) -> None:
        if not self.POWERSHELL:
            self.skipTest("Windows PowerShell 5.1 is not available on this host")
        with tempfile.TemporaryDirectory(prefix="wss-utf8-") as tmp:
            chinese_dir = Path(tmp) / "中文目录"
            chinese_dir.mkdir()
            chinese_file = chinese_dir / "测试文件.txt"
            chinese_file.write_bytes("内容".encode("utf-8"))
            proc = self._run(self.POWERSHELL, "-Target", str(chinese_file))
        self.assertEqual(proc.returncode, 0, proc.stderr.decode("utf-8", "replace"))
        data = json.loads(proc.stdout.decode("utf-8"))
        self.assertTrue(data["target"]["exists"])
        self.assertEqual(data["target"]["item_type"], "File")
        self.assertIn("中文目录", data["target"]["full_path"])
        self.assertIn("测试文件.txt", data["target"]["full_path"])

    def test_powershell_7_smoke(self) -> None:
        if self.PWSH_SKIP_REASON:
            self.skipTest(self.PWSH_SKIP_REASON)
        with tempfile.TemporaryDirectory(prefix="wss-collect7-") as tmp:
            proc = self._run(self.PWSH_PATH, "-Executable", "cmd.exe", "-Target", str(tmp))
        self.assertEqual(proc.returncode, 0, proc.stderr.decode("utf-8", "replace"))
        data = json.loads(proc.stdout.decode("utf-8"))
        self._assert_schema(data)
        self.assertEqual(data["environment"]["ps_edition"], "Core")

    def test_collector_source_has_no_mutating_operations(self) -> None:
        text = COLLECTOR.read_text(encoding="utf-8")
        forbidden = [
            "Set-Content", "Add-Content", "Out-File", "Clear-Content",
            "Remove-Item", "New-Item", "Set-Item", "Rename-Item", "Copy-Item",
            "Move-Item", "Set-ItemProperty", "New-ItemProperty", "Remove-ItemProperty",
            "New-PSDrive", "Start-Process", "Invoke-WebRequest", "Invoke-RestMethod",
            "Invoke-Expression", "Test-NetConnection", "Set-Location",
        ]
        hits = [token for token in forbidden if token in text]
        self.assertEqual(hits, [], f"collector must stay read-only; found {hits}")

    def test_collector_never_executes_analyzed_executable(self) -> None:
        """A sentinel executable must be resolved, never launched."""
        if not self.POWERSHELL:
            self.skipTest("Windows PowerShell 5.1 is not available on this host")
        with tempfile.TemporaryDirectory(prefix="wss-sentinel-") as tmp:
            sentinel = Path(tmp) / "sentinel.cmd"
            marker = Path(tmp) / "executed.marker"
            sentinel.write_text(
                'echo executed > "' + str(marker) + '"\r\n', encoding="utf-8"
            )
            proc = self._run(self.POWERSHELL, "-Executable", str(sentinel))
            self.assertEqual(proc.returncode, 0, proc.stderr.decode("utf-8", "replace"))
            data = json.loads(proc.stdout.decode("utf-8"))
            self.assertTrue(data["executable"]["found"])
            self.assertFalse(
                marker.exists(),
                "collector must resolve but never launch the analyzed executable",
            )

    def test_collector_does_not_emit_definition_or_secret(self) -> None:
        """A synthetic secret inside a script/function definition must never
        appear in the collector JSON (the Definition field is not collected)."""
        if not self.POWERSHELL:
            self.skipTest("Windows PowerShell 5.1 is not available on this host")
        secret = "SYNTHETIC_SECRET_FROM_DEFINITION_9Z"
        with tempfile.TemporaryDirectory(prefix="wss-def-") as tmp:
            script = Path(tmp) / "secret.ps1"
            script.write_text(
                'function Internal-Run { Write-Output "' + secret + '" }\n',
                encoding="utf-8",
            )
            proc = self._run(self.POWERSHELL, "-Executable", str(script))
            self.assertEqual(proc.returncode, 0, proc.stderr.decode("utf-8", "replace"))
            stdout = proc.stdout.decode("utf-8")
            data = json.loads(stdout)
            self.assertTrue(data["executable"]["found"])
            self.assertEqual(data["executable"]["command_type"], "ExternalScript")
            self.assertNotIn("definition", data["executable"])
            self.assertNotIn(secret, stdout)


if __name__ == "__main__":
    unittest.main()
