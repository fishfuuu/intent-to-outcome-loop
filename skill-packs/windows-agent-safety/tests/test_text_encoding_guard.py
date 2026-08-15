"""Behavior tests for text-encoding-guard (inspect + compare).

All encoding-sensitive fixtures are generated at runtime in temporary
directories so that no non-UTF-8 or mojibake bytes are committed to the
repository. Tests exercise real behavior: write bytes, run inspect/compare,
and assert on status, findings, hashes, and the absence of writes.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

PACK_ROOT = Path(__file__).resolve().parents[1]
SKILL = PACK_ROOT / "skills" / "text-encoding-guard"
IMPLEMENTATION = SKILL / "scripts" / "text_encoding_guard.py"

# (label, bytes, expected_status, expected_findings)
# Note: common GB18030 Chinese text also strict-decodes as Shift-JIS/EUC-JP,
# so without an explicit --encoding it is correctly fail-closed AMBIGUOUS.
# The single-family legacy case (a GB18030 4-byte character) proves the
# EXPLICIT_LEGACY_ENCODING_REQUIRED path.
SIMPLE_CASES = [
    ("ascii", b"hello world\n", "SAFE_UTF8", []),
    ("utf8_chinese", "中文内容\n第二行\n".encode("utf-8"), "SAFE_UTF8", []),
    ("utf8_bom", b"\xef\xbb\xbf" + "中文内容\n".encode("utf-8"), "SAFE_UTF8_BOM", []),
    ("utf16_le_bom", b"\xff\xfe" + "中文内容\n".encode("utf-16-le"), "SAFE_UTF16_LE", []),
    ("utf16_be_bom", b"\xfe\xff" + "中文内容\n".encode("utf-16-be"), "SAFE_UTF16_BE", []),
    ("gb18030_chinese", "中文内容\n".encode("gb18030"),
     "AMBIGUOUS_TEXT_ENCODING", ["AMBIGUOUS_ENCODING"]),
    ("gb18030_4byte_char", "𠀀中文\n".encode("gb18030"),
     "EXPLICIT_LEGACY_ENCODING_REQUIRED", ["LEGACY_ENCODING_REQUIRED"]),
    ("ambiguous_encoding", b"\xa1\x41\xa1\x42",
     "AMBIGUOUS_TEXT_ENCODING", ["AMBIGUOUS_ENCODING"]),
    ("invalid_utf8", b"\xff\xff\xff", "BINARY_OR_UNSUPPORTED", ["BINARY_FILE"]),
    ("binary_nul", b"abc\x00\x00def", "BINARY_OR_UNSUPPORTED", ["NUL_BYTES", "BINARY_FILE"]),
    ("mojibake", "ÖÐÎÄ 中文\n".encode("utf-8"), "POSSIBLE_MOJIBAKE", ["MOJIBAKE_TRACES"]),
    ("u_fffd", "ok � broken\n".encode("utf-8"), "SAFE_UTF8", ["U_FFFD_FOUND"]),
    ("bidi", "abc‮def\n".encode("utf-8"), "SAFE_UTF8", ["BIDI_CONTROL"]),
    ("zero_width", "a​b\n".encode("utf-8"), "SAFE_UTF8", ["ZERO_WIDTH_FORMAT"]),
    ("tag_char", "x\U000e0001y\n".encode("utf-8"), "SAFE_UTF8", ["TAG_CHARACTER"]),
    ("c1_control", "ab\n".encode("utf-8"), "SAFE_UTF8", ["CONTROL_CHARACTER"]),
]

# Longer ASCII file whose CJK characters were replaced by question marks.
QUESTION_MARK_FIXTURE = (
    b"# config: name=?? count=??\n"
    b"# note: status ?? unknown\n"
    b"# remark: value ?? replaced\n"
    b"# extra: ?? ?? ??\n"
    b"# end: ?? confirmed\n"
    b"# padding line to exceed the short-file guard\n"
)


def _load_module():
    assert IMPLEMENTATION.is_file(), f"implementation missing: {IMPLEMENTATION}"
    spec = importlib.util.spec_from_file_location("teg_impl", IMPLEMENTATION)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _run_cli(args, input_text=None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(IMPLEMENTATION), *args],
        input=input_text, text=True, capture_output=True, check=False, timeout=60,
    )


class TextEncodingGuardInspectTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.module = _load_module()

    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory(prefix="teg-inspect-")
        self.root = Path(self.tmp.name)

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def _write(self, name: str, data: bytes) -> Path:
        p = self.root / name
        p.write_bytes(data)
        return p

    def _inspect(self, path: Path, encoding: str | None = None) -> dict:
        before = _sha256_bytes(path.read_bytes())
        result = self.module.inspect_file(str(path), encoding)
        after = _sha256_bytes(path.read_bytes())
        self.assertEqual(before, after, "inspect must not modify the file")
        self.assertEqual(result["write_authorized"], "NO")
        return result

    def test_simple_fixture_table(self) -> None:
        for label, data, expected_status, expected_findings in SIMPLE_CASES:
            with self.subTest(label=label):
                path = self._write(label + ".bin", data)
                result = self._inspect(path)
                self.assertEqual(result["status"], expected_status, label)
                codes = [f["code"] for f in result["findings"]]
                for code in expected_findings:
                    self.assertIn(code, codes, label)
                self.assertEqual(result["byte_sha256"],
                                 _sha256_bytes(data), label)

    def test_ascii_is_safe_utf8(self) -> None:
        result = self._inspect(self._write("ascii.txt", b"hello\n"))
        self.assertEqual(result["status"], "SAFE_UTF8")
        self.assertEqual(result["encoding"], "utf-8")
        self.assertEqual(result["bom"], "none")
        self.assertEqual(result["newline_style"], "LF")
        self.assertTrue(result["trailing_newline"])

    def test_utf8_chinese_statistics(self) -> None:
        data = "中文内容\n".encode("utf-8")
        result = self._inspect(self._write("zh.txt", data))
        self.assertEqual(result["status"], "SAFE_UTF8")
        self.assertGreater(result["statistics"]["cjk_count"], 0)
        self.assertEqual(result["decoded_text_sha256"],
                         hashlib.sha256("中文内容\n".encode("utf-8")).hexdigest())

    def test_newline_styles(self) -> None:
        crlf = self._write("crlf.txt", b"a\r\nb\r\n")
        lf = self._write("lf.txt", b"a\nb\n")
        mixed = self._write("mixed.txt", b"a\r\nb\nc\r\n")
        cr = self._write("cr.txt", b"a\rb\r")
        self.assertEqual(self._inspect(crlf)["newline_style"], "CRLF")
        self.assertEqual(self._inspect(lf)["newline_style"], "LF")
        self.assertEqual(self._inspect(mixed)["newline_style"], "MIXED")
        self.assertEqual(self._inspect(cr)["newline_style"], "CR")

    def test_trailing_newline_detection(self) -> None:
        with_nl = self._write("nl.txt", b"a\n")
        without_nl = self._write("nonl.txt", b"a")
        self.assertTrue(self._inspect(with_nl)["trailing_newline"])
        self.assertFalse(self._inspect(without_nl)["trailing_newline"])

    def test_single_candidate_legacy_requires_explicit_and_never_converts(self) -> None:
        data = "𠀀中文\n".encode("gb18030")  # a GB18030 4-byte char keeps it single-family
        self.assertTrue(self.module._strict_decodes(data, "gb18030"))
        self.assertFalse(self.module._strict_decodes(data, "big5"))
        self.assertFalse(self.module._strict_decodes(data, "shift_jis"))
        path = self._write("gb.txt", data)
        result = self._inspect(path)
        self.assertEqual(result["status"], "EXPLICIT_LEGACY_ENCODING_REQUIRED")
        self.assertEqual(result["encoding_evidence"]["candidates"], ["gb18030/gbk"])
        self.assertEqual(result["encoding"], "gb18030/gbk")
        self.assertEqual(result["decoded_text_sha256"],
                         hashlib.sha256("𠀀中文\n".encode("utf-8")).hexdigest())
        self.assertEqual(_sha256_bytes(path.read_bytes()),
                         _sha256_bytes(data), "no conversion must occur")

    def test_gb18030_chinese_fails_closed_without_explicit_encoding(self) -> None:
        data = "中文内容\n".encode("gb18030")
        self.assertFalse(self.module._strict_decodes(data, "utf-8"))
        result = self._inspect(self._write("gbc.txt", data))
        self.assertEqual(result["status"], "AMBIGUOUS_TEXT_ENCODING")

    def test_gb18030_explicit_encoding_validates(self) -> None:
        path = self._write("gb2.txt", "中文内容\n".encode("gb18030"))
        result = self._inspect(path, "gb18030")
        self.assertEqual(result["status"], "VALIDATED_LEGACY_ENCODING")
        self.assertIn("LEGACY_ENCODING_VALIDATED",
                      [f["code"] for f in result["findings"]])
        self.assertEqual(result["encoding_evidence"]["candidates"], ["gb18030"])
        self.assertEqual(result["encoding"], "gb18030")

    def test_utf8_wins_over_explicit_legacy_encoding(self) -> None:
        path = self._write("u8.txt", "中文内容\n".encode("utf-8"))
        result = self._inspect(path, "gb18030")
        self.assertEqual(result["status"], "SAFE_UTF8")

    def test_explicit_encoding_mismatch_fails_closed(self) -> None:
        path = self._write("mismatch.txt", b"\xff\xff\xff")
        result = self._inspect(path, "gb18030")
        self.assertEqual(result["status"], "BINARY_OR_UNSUPPORTED")
        self.assertIn("ENCODING_MISMATCH", [f["code"] for f in result["findings"]])

    def test_ambiguous_encoding_fails_closed(self) -> None:
        data = b"\xa1\x41\xa1\x42"
        self.assertTrue(self.module._strict_decodes(data, "gb18030"))
        self.assertTrue(self.module._strict_decodes(data, "big5"))
        result = self._inspect(self._write("ambig.bin", data))
        self.assertEqual(result["status"], "AMBIGUOUS_TEXT_ENCODING")
        self.assertIsNone(result["decoded_text_sha256"])
        self.assertGreaterEqual(len(result["encoding_evidence"]["candidates"]), 2)

    def test_question_mark_replacement_signal(self) -> None:
        path = self._write("qm.txt", QUESTION_MARK_FIXTURE)
        result = self._inspect(path)
        codes = [f["code"] for f in result["findings"]]
        self.assertIn("SUSPICIOUS_QUESTION_MARKS", codes)

    def test_normal_question_marks_not_suspicious(self) -> None:
        data = (
            b"question one: which value should we use here?\n"
            b"answer: it depends on the caller and the context.\n"
        ) * 20  # isolated single question marks at low density
        path = self._write("norm.txt", data)
        result = self._inspect(path)
        codes = [f["code"] for f in result["findings"]]
        self.assertNotIn("SUSPICIOUS_QUESTION_MARKS", codes)

    def test_io_error_for_missing_file(self) -> None:
        result = self.module.inspect_file(str(self.root / "nope.txt"))
        self.assertEqual(result["status"], "IO_ERROR")
        self.assertEqual(result["write_authorized"], "NO")
        self.assertIsNone(result["byte_sha256"])

    def test_chinese_filename_and_directory(self) -> None:
        chinese_dir = self.root / "中文目录"
        chinese_dir.mkdir()
        chinese_file = chinese_dir / "测试文件.txt"
        chinese_file.write_bytes("内容\n".encode("utf-8"))
        result = self._inspect(chinese_file)
        self.assertEqual(result["status"], "SAFE_UTF8")
        self.assertIn("中文目录", result["path"])
        self.assertIn("测试文件.txt", result["path"])

    def test_secret_content_not_leaked(self) -> None:
        secret = "SYNTHETIC_SECRET_XK7_9"
        path = self._write("secret.txt", f"token = {secret}\n".encode("utf-8"))
        result = self._inspect(path)
        serialized = json.dumps(result, ensure_ascii=False)
        self.assertNotIn(secret, serialized)

    def test_determinism(self) -> None:
        path = self._write("det.txt", "中文 内容\n第二行\r\n".encode("utf-8"))
        first = self.module.canonical_json_dumps(self._inspect(path))
        second = self.module.canonical_json_dumps(self._inspect(path))
        self.assertEqual(first, second)
        self.assertFalse(first.startswith("﻿"))
        self.assertNotIn("\r\n", first)

    def test_finding_shape(self) -> None:
        path = self._write("shape.txt", "a‮\x85\n".encode("utf-8"))
        result = self._inspect(path)
        for finding in result["findings"]:
            self.assertEqual(
                set(finding),
                {"code", "severity", "offset", "byte_offset", "codepoint",
                 "type", "evidence"},
            )
            self.assertIn(finding["severity"], {"LOW", "MEDIUM", "HIGH", "STOP"})


class TextEncodingGuardCompareTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.module = _load_module()

    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory(prefix="teg-compare-")
        self.root = Path(self.tmp.name)

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def _write(self, name: str, data: bytes) -> Path:
        p = self.root / name
        p.write_bytes(data)
        return p

    def _compare(self, path: Path, baseline: dict) -> dict:
        before = _sha256_bytes(path.read_bytes())
        result = self.module.compare_file(str(path), baseline)
        after = _sha256_bytes(path.read_bytes())
        self.assertEqual(before, after, "compare must not modify the file")
        self.assertEqual(result["write_authorized"], "NO")
        return result

    def test_normal_content_change_allowed(self) -> None:
        path = self._write("ok.txt", "中文第一行\n".encode("utf-8"))
        baseline = self.module.inspect_file(str(path))
        path.write_bytes("中文第一行已更新\n".encode("utf-8"))
        result = self._compare(path, baseline)
        self.assertEqual(result["changes"], [])

    def test_encoding_drift(self) -> None:
        path = self._write("drift.txt", "中文\n".encode("utf-8"))
        baseline = self.module.inspect_file(str(path))
        path.write_bytes("中文\n".encode("gb18030"))
        result = self._compare(path, baseline)
        self.assertIn("ENCODING_DRIFT", result["changes"])

    def test_bom_drift(self) -> None:
        path = self._write("bom.txt", "中文\n".encode("utf-8"))
        baseline = self.module.inspect_file(str(path))
        path.write_bytes(b"\xef\xbb\xbf" + "中文\n".encode("utf-8"))
        result = self._compare(path, baseline)
        self.assertIn("BOM_DRIFT", result["changes"])
        self.assertNotIn("ENCODING_DRIFT", result["changes"])

    def test_newline_and_trailing_drift(self) -> None:
        path = self._write("nl2.txt", "a\nb\n".encode("utf-8"))
        baseline = self.module.inspect_file(str(path))
        path.write_bytes("a\r\nb\r\n".encode("utf-8"))
        result = self._compare(path, baseline)
        self.assertIn("NEWLINE_DRIFT", result["changes"])
        path.write_bytes("a\r\nb".encode("utf-8"))
        result2 = self._compare(path, baseline)
        self.assertIn("TRAILING_NEWLINE_DRIFT", result2["changes"])

    def test_new_u_fffd(self) -> None:
        path = self._write("fffd.txt", "中文\n".encode("utf-8"))
        baseline = self.module.inspect_file(str(path))
        path.write_bytes("中文 �\n".encode("utf-8"))
        result = self._compare(path, baseline)
        self.assertIn("NEW_U_FFFD", result["changes"])

    def test_cjk_question_replacement(self) -> None:
        path = self._write("cjk.txt", "姓名: 张三\n年龄: 25\n".encode("utf-8"))
        baseline = self.module.inspect_file(str(path))
        path.write_bytes("姓名: ??\n年龄: ??\n".encode("utf-8"))
        result = self._compare(path, baseline)
        self.assertIn("CJK_QUESTION_REPLACEMENT", result["changes"])

    def test_new_mojibake(self) -> None:
        path = self._write("moj.txt", "中文\n".encode("utf-8"))
        baseline = self.module.inspect_file(str(path))
        path.write_bytes("ÖÐÎÄ\n".encode("utf-8"))
        result = self._compare(path, baseline)
        self.assertIn("NEW_MOJIBAKE", result["changes"])

    def test_new_dangerous_unicode(self) -> None:
        path = self._write("danger.txt", "safe\n".encode("utf-8"))
        baseline = self.module.inspect_file(str(path))
        path.write_bytes("safe ‮\n".encode("utf-8"))
        result = self._compare(path, baseline)
        self.assertIn("NEW_DANGEROUS_UNICODE", result["changes"])

    def test_no_baseline(self) -> None:
        path = self._write("nobase.txt", b"a\n")
        result = self.module.compare_file(str(path), None)
        self.assertIn("NO_BASELINE", result["changes"])
        self.assertEqual(result["status"], "SAFE_UTF8")

    def test_compare_output_contains_baseline_and_current(self) -> None:
        path = self._write("out.txt", "a\n".encode("utf-8"))
        baseline = self.module.inspect_file(str(path))
        path.write_bytes("b\r\n".encode("utf-8"))
        result = self._compare(path, baseline)
        self.assertIsInstance(result["baseline"], dict)
        self.assertEqual(result["baseline"]["byte_sha256"], baseline["byte_sha256"])
        self.assertEqual(result["byte_sha256"], _sha256_bytes(path.read_bytes()))


class TextEncodingGuardCliTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.module = _load_module()

    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory(prefix="teg-cli-")
        self.root = Path(self.tmp.name)

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_inspect_cli_array_output(self) -> None:
        a = self.root / "a.txt"
        a.write_bytes("中文\n".encode("utf-8"))
        b = self.root / "b.txt"
        b.write_bytes("中文\n".encode("gb18030"))
        proc = _run_cli(["inspect", str(a), str(b)])
        self.assertEqual(proc.returncode, 0, proc.stderr)
        results = json.loads(proc.stdout)
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]["status"], "SAFE_UTF8")
        self.assertEqual(results[1]["status"], "AMBIGUOUS_TEXT_ENCODING")
        for r in results:
            self.assertEqual(r["write_authorized"], "NO")

    def test_inspect_cli_explicit_encoding(self) -> None:
        path = self.root / "gb.txt"
        path.write_bytes("中文\n".encode("gb18030"))
        proc = _run_cli(["inspect", "--encoding", "gb18030", str(path)])
        self.assertEqual(proc.returncode, 0, proc.stderr)
        result = json.loads(proc.stdout)[0]
        self.assertEqual(result["status"], "VALIDATED_LEGACY_ENCODING")
        self.assertIn("LEGACY_ENCODING_VALIDATED",
                      [f["code"] for f in result["findings"]])

    def test_inspect_cli_utf8_stdout_under_ascii_ioencoding(self) -> None:
        """stdout is explicit UTF-8 bytes, independent of the process encoding."""
        chinese_dir = self.root / "中文目录"
        chinese_dir.mkdir()
        f = chinese_dir / "文件.txt"
        f.write_bytes("中文内容\n".encode("utf-8"))
        env = dict(os.environ)
        env["PYTHONIOENCODING"] = "ascii"
        env["PYTHONUTF8"] = "0"
        proc = subprocess.run(
            [sys.executable, str(IMPLEMENTATION), "inspect", str(f)],
            capture_output=True, check=False, env=env, timeout=60,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        text = proc.stdout.decode("utf-8")
        self.assertNotIn("﻿", text)
        self.assertNotIn("\r\n", text)
        results = json.loads(text)
        self.assertEqual(results[0]["status"], "SAFE_UTF8")
        self.assertIn("中文目录", results[0]["path"])

    def test_inspect_cli_unknown_encoding_exit_2(self) -> None:
        path = self.root / "a.txt"
        path.write_bytes(b"a\n")
        proc = _run_cli(["inspect", "--encoding", "no-such-codec", str(path)])
        self.assertEqual(proc.returncode, 2)

    def test_compare_cli_unknown_encoding_exit_2(self) -> None:
        """compare must reject an unknown --encoding up front (same as inspect),
        even when the current file is valid UTF-8."""
        path = self.root / "ok.txt"
        path.write_bytes("合法 UTF-8 内容\n".encode("utf-8"))
        before_file = self.root / "before.json"
        before_file.write_text(json.dumps(self.module.inspect_file(str(path))),
                               encoding="utf-8")
        proc = _run_cli(
            ["compare", "--before", str(before_file), "--encoding", "no-such-codec", str(path)]
        )
        self.assertEqual(proc.returncode, 2)
        self.assertIn("unknown encoding", proc.stderr.lower())
        self.assertEqual(proc.stdout, "")  # no comparison JSON is emitted

    def test_inspect_cli_does_not_write(self) -> None:
        path = self.root / "keep.txt"
        path.write_bytes("中文\n".encode("utf-8"))
        before = _sha256_bytes(path.read_bytes())
        proc = _run_cli(["inspect", str(path)])
        self.assertEqual(proc.returncode, 0)
        self.assertEqual(_sha256_bytes(path.read_bytes()), before)

    def test_compare_cli_with_before_file(self) -> None:
        path = self.root / "cmp.txt"
        path.write_bytes("第一行\n".encode("utf-8"))
        before_file = self.root / "before.json"
        before_file.write_text(json.dumps(self.module.inspect_file(str(path))),
                               encoding="utf-8")
        path.write_bytes("第一行\n第二行\n".encode("utf-8"))
        proc = _run_cli(["compare", "--before", str(before_file), str(path)])
        self.assertEqual(proc.returncode, 0, proc.stderr)
        result = json.loads(proc.stdout)[0]
        self.assertEqual(result["changes"], [])
        self.assertEqual(result["write_authorized"], "NO")

    def test_compare_cli_missing_before_file_exit_4(self) -> None:
        path = self.root / "a.txt"
        path.write_bytes(b"a\n")
        proc = _run_cli(["compare", "--before", str(self.root / "missing.json"), str(path)])
        self.assertEqual(proc.returncode, 4)

    def test_no_subcommand_exit_2(self) -> None:
        proc = _run_cli([])
        self.assertEqual(proc.returncode, 2)


if __name__ == "__main__":
    unittest.main()
