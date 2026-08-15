"""text-encoding-guard -- read-only text encoding integrity diagnostics.

Never writes files, never converts encoding, never decodes with a lossy
fallback (no errors="replace", no latin1 blanket decode), and never guesses
an encoding when the bytes are ambiguous. It inspects raw bytes first and
reports deterministic, machine-verifiable JSON.

Two subcommands:

    inspect  <path>...            diagnose current file state
    compare  --before <file.json> <path>...
                                  compare current files against inspect output

Inspect never auto-selects a legacy encoding; a file that is not valid UTF-8
and not BOM-identified is reported as EXPLICIT_LEGACY_ENCODING_REQUIRED
(single candidate family) or AMBIGUOUS_TEXT_ENCODING (multiple candidate
families) or BINARY_OR_UNSUPPORTED (nothing decodes). Only an explicit
--encoding validates a legacy file: a strict decode success yields
VALIDATED_LEGACY_ENCODING, and a failed decode stays fail-closed as
BINARY_OR_UNSUPPORTED.
"""

from __future__ import annotations

import codecs
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Statuses
# ---------------------------------------------------------------------------

STATUS_SAFE_UTF8 = "SAFE_UTF8"
STATUS_SAFE_UTF8_BOM = "SAFE_UTF8_BOM"
STATUS_SAFE_UTF16_LE = "SAFE_UTF16_LE"
STATUS_SAFE_UTF16_BE = "SAFE_UTF16_BE"
STATUS_EXPLICIT_LEGACY = "EXPLICIT_LEGACY_ENCODING_REQUIRED"
STATUS_VALIDATED_LEGACY = "VALIDATED_LEGACY_ENCODING"
STATUS_POSSIBLE_MOJIBAKE = "POSSIBLE_MOJIBAKE"
STATUS_AMBIGUOUS = "AMBIGUOUS_TEXT_ENCODING"
STATUS_BINARY = "BINARY_OR_UNSUPPORTED"
STATUS_IO_ERROR = "IO_ERROR"

# Legacy encoding families. GBK and GB18030 are one family (GB18030 is a
# superset of GBK), so a GB-valid file is not reported as ambiguous between
# them. Each family's primary codec is used for a strict-decode probe.
LEGACY_FAMILIES = [
    ("gb", ("gb18030", "gbk")),
    ("big5", ("big5",)),
    ("shift_jis", ("shift_jis",)),
    ("euc_jp", ("euc_jp",)),
]
_FAMILY_LABEL = {"gb": "gb18030/gbk", "big5": "big5", "shift_jis": "shift_jis", "euc_jp": "euc_jp"}
_FAMILY_PRIMARY = {"gb": "gb18030", "big5": "big5", "shift_jis": "shift_jis", "euc_jp": "euc_jp"}

# CJK / CJK-extended / kana / hangul / hangul-jamo / bopomofo ranges used for
# the CJK drift signal in compare.
_CJK_RANGES = (
    (0x3400, 0x4DBF),
    (0x4E00, 0x9FFF),
    (0xF900, 0xFAFF),
    (0x3040, 0x30FF),
    (0x31F0, 0x31FF),
    (0xAC00, 0xD7AF),
    (0x1100, 0x11FF),
)

# Dangerous Unicode categories: bidi controls, zero-width/format controls,
# Unicode tag characters, and C0 (except tab/LF/CR) / C1 control characters.
_DANGER_RANGES = (
    ("BIDI_CONTROL", "bidi-control", "HIGH", (0x202A, 0x202E), (0x2066, 0x2069), (0x200E, 0x200F), (0x061C, 0x061C)),
    ("ZERO_WIDTH_FORMAT", "zero-width-format", "MEDIUM", (0x200B, 0x200D), (0xFEFF, 0xFEFF), (0x2060, 0x2060), (0x00AD, 0x00AD)),
    ("TAG_CHARACTER", "unicode-tag", "MEDIUM", (0xE0000, 0xE007F)),
    ("CONTROL_CHARACTER", "control-character", "MEDIUM",
     (0x0000, 0x0008), (0x000B, 0x000C), (0x000E, 0x001F), (0x007F, 0x009F)),
)

# Latin-1-supplement runs are the classic double-encoding artifact
# (UTF-8 bytes decoded as Latin-1/GBK, then re-encoded as UTF-8).
_MOJIBAKE_PATTERN = re.compile(r"[À-ÿ]{2,}")

# Compare drift finding codes, in a fixed report order.
_CHANGE_ORDER = [
    "ENCODING_DRIFT",
    "BOM_DRIFT",
    "NEWLINE_DRIFT",
    "TRAILING_NEWLINE_DRIFT",
    "NEW_U_FFFD",
    "CJK_QUESTION_REPLACEMENT",
    "NEW_MOJIBAKE",
    "NEW_DANGEROUS_UNICODE",
    "NO_BASELINE",
]

_DANGER_CODES = {"BIDI_CONTROL", "ZERO_WIDTH_FORMAT", "TAG_CHARACTER", "CONTROL_CHARACTER"}

_CAP_LEN = 120


def _cap(text: str) -> str:
    return text if len(text) <= _CAP_LEN else text[:_CAP_LEN] + "..."


def _finding(code: str, severity: str, *, offset=None, byte_offset=None,
             codepoint=None, ftype: str = "", evidence: str = "") -> dict[str, Any]:
    return {
        "code": code,
        "severity": severity,
        "offset": offset,
        "byte_offset": byte_offset,
        "codepoint": codepoint,
        "type": ftype,
        "evidence": _cap(evidence),
    }


def _detect_bom(raw: bytes) -> str:
    if raw.startswith(b"\xef\xbb\xbf"):
        return "utf-8"
    if raw.startswith(b"\xff\xfe"):
        return "utf-16-le"
    if raw.startswith(b"\xfe\xff"):
        return "utf-16-be"
    return "none"


def _strict_decodes(raw: bytes, codec: str) -> bool:
    try:
        raw.decode(codec)
        return True
    except (UnicodeDecodeError, LookupError):
        return False


def _resolve_legacy(
    raw: bytes, explicit: str | None, findings: list[dict[str, Any]]
) -> tuple[str, str, list[str], str | None]:
    """Return (status, encoding_label, candidates, decoded_text_or_None)."""
    if explicit:
        try:
            codecs.lookup(explicit)
        except LookupError:
            findings.append(_finding(
                "ENCODING_MISMATCH", "HIGH", ftype="encoding",
                evidence=f"unknown encoding name: {explicit}",
            ))
            return STATUS_BINARY, "binary/unsupported", [], None
        try:
            text = raw.decode(explicit)
        except UnicodeDecodeError:
            findings.append(_finding(
                "ENCODING_MISMATCH", "HIGH", ftype="encoding",
                evidence=f"bytes are not valid {explicit}",
            ))
            return STATUS_BINARY, "binary/unsupported", [], None
        findings.append(_finding(
            "LEGACY_ENCODING_VALIDATED", "LOW", ftype="encoding",
            evidence=f"decoded as {explicit}",
        ))
        return STATUS_VALIDATED_LEGACY, explicit, [explicit], text

    decodable = [fam for fam, codecs_list in LEGACY_FAMILIES
                 if _strict_decodes(raw, codecs_list[0])]
    if not decodable:
        findings.append(_finding(
            "BINARY_FILE", "MEDIUM", ftype="binary",
            evidence="not valid UTF-8 and matches no known legacy encoding",
        ))
        return STATUS_BINARY, "binary/unsupported", [], None
    if len(decodable) == 1:
        fam = decodable[0]
        label = _FAMILY_LABEL[fam]
        findings.append(_finding(
            "LEGACY_ENCODING_REQUIRED", "MEDIUM", ftype="encoding",
            evidence=f"explicit encoding required; candidate family: {label}",
        ))
        text = raw.decode(_FAMILY_PRIMARY[fam])
        return STATUS_EXPLICIT_LEGACY, label, [label], text
    labels = sorted(_FAMILY_LABEL[f] for f in decodable)
    findings.append(_finding(
        "AMBIGUOUS_ENCODING", "HIGH", ftype="encoding",
        evidence=f"multiple encodings decode; candidates: {', '.join(labels)}",
    ))
    return STATUS_AMBIGUOUS, "ambiguous", labels, None


def _count_cjk(text: str) -> int:
    n = 0
    for ch in text:
        o = ord(ch)
        for lo, hi in _CJK_RANGES:
            if lo <= o <= hi:
                n += 1
                break
    return n


def _newline_analysis(text: str) -> tuple[str, bool]:
    crlf = text.count("\r\n")
    lf_only = text.count("\n") - crlf
    cr_only = text.count("\r") - crlf
    total = crlf + lf_only + cr_only
    if total == 0:
        style = "NONE"
    elif crlf > 0 and lf_only == 0 and cr_only == 0:
        style = "CRLF"
    elif crlf == 0 and lf_only > 0 and cr_only == 0:
        style = "LF"
    elif crlf == 0 and lf_only == 0 and cr_only > 0:
        style = "CR"
    else:
        style = "MIXED"
    trailing = text.endswith(("\n", "\r"))
    return style, trailing


def _scan_content(text: str) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    stats = {
        "char_count": len(text),
        "cjk_count": _count_cjk(text),
        "question_count": text.count("?"),
        "fffd_count": text.count("�"),
        "non_ascii_count": sum(1 for ch in text if ord(ch) > 127),
        "nul_byte_count": 0,  # filled by the byte-level caller
    }

    fffd_count = stats["fffd_count"]
    if fffd_count:
        pos = text.find("�")
        findings.append(_finding(
            "U_FFFD_FOUND", "MEDIUM", offset=pos, codepoint="U+FFFD",
            ftype="replacement-character",
            evidence=f"{fffd_count} replacement character(s); first at offset {pos}",
        ))

    mojibake = _MOJIBAKE_PATTERN.findall(text)
    if mojibake:
        m = _MOJIBAKE_PATTERN.search(text)
        findings.append(_finding(
            "MOJIBAKE_TRACES", "MEDIUM", offset=m.start(), ftype="mojibake",
            evidence=f"{len(mojibake)} double-encoding artifact(s); first at offset {m.start()}",
        ))

    _scan_dangerous(text, findings)
    _scan_question_marks(text, findings)
    return findings, stats


def _scan_dangerous(text: str, findings: list[dict[str, Any]]) -> None:
    for code, ftype, sev, *ranges in _DANGER_RANGES:
        hits: list[int] = []
        for idx, ch in enumerate(text):
            o = ord(ch)
            if any(lo <= o <= hi for lo, hi in ranges):
                hits.append(idx)
                if len(hits) >= 10:
                    break
        if hits:
            first = hits[0]
            findings.append(_finding(
                code, sev, offset=first,
                codepoint=f"U+{ord(text[first]):04X}", ftype=ftype,
                evidence=f"{len(hits)}+ {ftype} character(s); first at offset {first}",
            ))


def _scan_question_marks(text: str, findings: list[dict[str, Any]]) -> None:
    total = len(text)
    if total <= 40:
        return
    q = text.count("?")
    if q == 0:
        return
    max_run = max((len(m) for m in re.findall(r"\?+", text)), default=0)
    if q / total >= 0.03 and max_run >= 2:
        findings.append(_finding(
            "SUSPICIOUS_QUESTION_MARKS", "LOW", ftype="question-marks",
            evidence=f"question density {q}/{total} chars; longest run {max_run}",
        ))


def inspect_file(path_str: str, explicit_encoding: str | None = None) -> dict[str, Any]:
    """Diagnose one file. Read-only and deterministic."""
    findings: list[dict[str, Any]] = []
    try:
        raw = Path(path_str).read_bytes()
    except OSError as exc:
        findings.append(_finding(
            "IO_ERROR", "HIGH", ftype="io",
            evidence=f"{type(exc).__name__}: {_cap(str(exc))}",
        ))
        return {
            "path": path_str,
            "status": STATUS_IO_ERROR,
            "encoding": None,
            "encoding_evidence": {
                "bom": None,
                "strict_decode": None,
                "candidates": [],
                "explicit_encoding_requested": explicit_encoding,
                "notes": ["file could not be read"],
            },
            "bom": None,
            "newline_style": None,
            "trailing_newline": None,
            "byte_sha256": None,
            "decoded_text_sha256": None,
            "statistics": None,
            "findings": findings,
            "write_authorized": "NO",
        }

    byte_sha = hashlib.sha256(raw).hexdigest()
    nul_count = raw.count(b"\x00")
    bom = _detect_bom(raw)

    text: str | None = None
    status: str | None = None
    encoding_label: str | None = None
    strict_decode: bool | None = None
    candidates: list[str] = []
    notes: list[str] = []

    if bom == "utf-8":
        try:
            text = raw[3:].decode("utf-8")
        except UnicodeDecodeError:
            status = STATUS_BINARY
            encoding_label = "binary/unsupported"
            findings.append(_finding(
                "ENCODING_MISMATCH", "HIGH", ftype="encoding",
                evidence="UTF-8 BOM present but bytes are not valid UTF-8",
            ))
        else:
            status = STATUS_SAFE_UTF8_BOM
            encoding_label = "utf-8"
            strict_decode = True
    elif bom == "utf-16-le":
        try:
            text = raw[2:].decode("utf-16-le")
        except UnicodeDecodeError:
            status = STATUS_BINARY
            encoding_label = "binary/unsupported"
            findings.append(_finding(
                "ENCODING_MISMATCH", "HIGH", ftype="encoding",
                evidence="UTF-16 LE BOM present but bytes are not valid UTF-16 LE",
            ))
        else:
            status = STATUS_SAFE_UTF16_LE
            encoding_label = "utf-16-le"
            strict_decode = True
    elif bom == "utf-16-be":
        try:
            text = raw[2:].decode("utf-16-be")
        except UnicodeDecodeError:
            status = STATUS_BINARY
            encoding_label = "binary/unsupported"
            findings.append(_finding(
                "ENCODING_MISMATCH", "HIGH", ftype="encoding",
                evidence="UTF-16 BE BOM present but bytes are not valid UTF-16 BE",
            ))
        else:
            status = STATUS_SAFE_UTF16_BE
            encoding_label = "utf-16-be"
            strict_decode = True
    else:
        if nul_count:
            status = STATUS_BINARY
            encoding_label = "binary/unsupported"
            strict_decode = False
            notes.append("NUL bytes present without a BOM; encoding not determinable without guessing")
            findings.append(_finding(
                "NUL_BYTES", "HIGH", byte_offset=raw.find(b"\x00"), ftype="nul-bytes",
                evidence=f"{nul_count} NUL byte(s)",
            ))
            findings.append(_finding(
                "BINARY_FILE", "MEDIUM", ftype="binary",
                evidence="NUL bytes without a BOM",
            ))
        else:
            try:
                text = raw.decode("utf-8")
            except UnicodeDecodeError:
                strict_decode = False
                status, encoding_label, candidates, text = _resolve_legacy(
                    raw, explicit_encoding, findings
                )
            else:
                strict_decode = True
                status = STATUS_SAFE_UTF8
                encoding_label = "utf-8"

    if text is not None:
        content_findings, stats = _scan_content(text)
        stats["nul_byte_count"] = nul_count
        findings.extend(content_findings)
        if status == STATUS_SAFE_UTF8 and any(
            f["code"] == "MOJIBAKE_TRACES" for f in content_findings
        ):
            status = STATUS_POSSIBLE_MOJIBAKE
        decoded_sha = hashlib.sha256(text.encode("utf-8")).hexdigest()
        newline_style, trailing = _newline_analysis(text)
    else:
        stats = {
            "char_count": None,
            "cjk_count": 0,
            "question_count": 0,
            "fffd_count": 0,
            "non_ascii_count": 0,
            "nul_byte_count": nul_count,
        }
        decoded_sha = None
        newline_style = None
        trailing = None

    return {
        "path": path_str,
        "status": status,
        "encoding": encoding_label,
        "encoding_evidence": {
            "bom": bom,
            "strict_decode": strict_decode,
            "candidates": candidates,
            "explicit_encoding_requested": explicit_encoding,
            "notes": notes,
        },
        "bom": bom,
        "newline_style": newline_style,
        "trailing_newline": trailing,
        "byte_sha256": byte_sha,
        "decoded_text_sha256": decoded_sha,
        "statistics": stats,
        "findings": findings,
        "write_authorized": "NO",
    }


def _has_code(findings: list[dict[str, Any]], code: str) -> bool:
    return any(f.get("code") == code for f in findings)


def _baseline_subset(b: dict[str, Any] | None) -> dict[str, Any] | None:
    if not b:
        return None
    stats = b.get("statistics") or {}
    return {
        "path": b.get("path"),
        "status": b.get("status"),
        "encoding": b.get("encoding"),
        "bom": b.get("bom"),
        "newline_style": b.get("newline_style"),
        "trailing_newline": b.get("trailing_newline"),
        "byte_sha256": b.get("byte_sha256"),
        "decoded_text_sha256": b.get("decoded_text_sha256"),
        "statistics": {k: stats.get(k) for k in ("cjk_count", "question_count", "fffd_count")},
        "finding_codes": sorted({f.get("code") for f in b.get("findings", [])}),
    }


def _change_finding(code: str, b: dict[str, Any] | None, c: dict[str, Any]) -> dict[str, Any]:
    base_stats = (b or {}).get("statistics") or {}
    cur_stats = c.get("statistics") or {}
    severity = "MEDIUM"
    evidence = code
    if code == "ENCODING_DRIFT":
        severity, evidence = "HIGH", f"{b.get('encoding') or '?'} -> {c.get('encoding') or '?'}"
    elif code == "BOM_DRIFT":
        evidence = f"{b.get('bom') or 'none'} -> {c.get('bom') or 'none'}"
    elif code == "NEWLINE_DRIFT":
        evidence = f"{b.get('newline_style')} -> {c.get('newline_style')}"
    elif code == "TRAILING_NEWLINE_DRIFT":
        evidence = f"trailing newline {b.get('trailing_newline')} -> {c.get('trailing_newline')}"
    elif code == "NEW_U_FFFD":
        evidence = f"U+FFFD {base_stats.get('fffd_count', 0) or 0} -> {cur_stats.get('fffd_count', 0) or 0}"
    elif code == "CJK_QUESTION_REPLACEMENT":
        evidence = (
            f"CJK {base_stats.get('cjk_count', 0) or 0} -> {cur_stats.get('cjk_count', 0) or 0}, "
            f"? {base_stats.get('question_count', 0) or 0} -> {cur_stats.get('question_count', 0) or 0}"
        )
    elif code == "NEW_MOJIBAKE":
        severity, evidence = "HIGH", "mojibake traces newly present"
    elif code == "NEW_DANGEROUS_UNICODE":
        severity, evidence = "HIGH", "new dangerous unicode characters present"
    elif code == "NO_BASELINE":
        evidence = "no inspect baseline found for this path"
    return _finding(code, severity, ftype="compare-drift", evidence=evidence)


def compare_file(
    path_str: str, baseline: dict[str, Any] | None, explicit_encoding: str | None = None
) -> dict[str, Any]:
    """Compare one file against its inspect baseline. Read-only."""
    current = inspect_file(path_str, explicit_encoding)
    findings = list(current["findings"])
    changes: set[str] = set()

    if baseline is None:
        changes.add("NO_BASELINE")
    else:
        if baseline.get("encoding") != current.get("encoding"):
            changes.add("ENCODING_DRIFT")
        if baseline.get("bom") != current.get("bom"):
            changes.add("BOM_DRIFT")

        # Newline / trailing-newline drift is only meaningful when both sides
        # decode (an AMBIGUOUS or BINARY current file has no determinable
        # newline style; the encoding drift already covers that change).
        base_nl = baseline.get("newline_style")
        cur_nl = current.get("newline_style")
        if base_nl is not None and cur_nl is not None and base_nl != cur_nl:
            changes.add("NEWLINE_DRIFT")
        base_trailing = baseline.get("trailing_newline")
        cur_trailing = current.get("trailing_newline")
        if (base_trailing is not None and cur_trailing is not None
                and base_trailing != cur_trailing):
            changes.add("TRAILING_NEWLINE_DRIFT")

        base_stats = baseline.get("statistics") or {}
        cur_stats = current.get("statistics") or {}
        base_fffd = base_stats.get("fffd_count", 0) or 0
        cur_fffd = cur_stats.get("fffd_count", 0) or 0
        if cur_fffd > base_fffd:
            changes.add("NEW_U_FFFD")

        base_cjk = base_stats.get("cjk_count", 0) or 0
        cur_cjk = cur_stats.get("cjk_count", 0) or 0
        base_q = base_stats.get("question_count", 0) or 0
        cur_q = cur_stats.get("question_count", 0) or 0
        if cur_cjk < base_cjk and cur_q > base_q:
            changes.add("CJK_QUESTION_REPLACEMENT")

        base_moj = _has_code(baseline.get("findings", []), "MOJIBAKE_TRACES")
        cur_moj = _has_code(current.get("findings", []), "MOJIBAKE_TRACES")
        if cur_moj and not base_moj:
            changes.add("NEW_MOJIBAKE")

        base_danger = {code for code in _DANGER_CODES
                       if _has_code(baseline.get("findings", []), code)}
        cur_danger = {code for code in _DANGER_CODES
                      if _has_code(current.get("findings", []), code)}
        if cur_danger - base_danger:
            changes.add("NEW_DANGEROUS_UNICODE")

    ordered_changes = [code for code in _CHANGE_ORDER if code in changes]
    for code in ordered_changes:
        findings.append(_change_finding(code, baseline, current))

    return {
        "path": path_str,
        "status": current["status"],
        "encoding": current["encoding"],
        "bom": current["bom"],
        "newline_style": current["newline_style"],
        "trailing_newline": current["trailing_newline"],
        "byte_sha256": current["byte_sha256"],
        "decoded_text_sha256": current["decoded_text_sha256"],
        "statistics": current["statistics"],
        "changes": ordered_changes,
        "findings": findings,
        "baseline": _baseline_subset(baseline),
        "write_authorized": "NO",
    }


def canonical_json_dumps(obj: Any) -> str:
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"


def _emit_stdout(text: str) -> None:
    """Write UTF-8 (LF, no BOM) bytes to stdout regardless of the process
    encoding / console codepage. Falls back to the text layer when stdout
    has no binary buffer (e.g. an in-process StringIO)."""
    data = text.encode("utf-8")
    buffer = getattr(sys.stdout, "buffer", None)
    if buffer is not None:
        buffer.write(data)
        buffer.flush()
    else:
        sys.stdout.write(text)


def _usage() -> None:
    print(
        "usage:\n"
        "  text_encoding_guard.py inspect [--encoding NAME] <path>...\n"
        "  text_encoding_guard.py compare --before <inspect.json> [--encoding NAME] <path>...",
        file=sys.stderr,
    )


def _cli(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv:
        _usage()
        return 2
    sub = argv[0]

    if sub == "inspect":
        explicit: str | None = None
        paths: list[str] = []
        i = 1
        while i < len(argv):
            if argv[i] == "--encoding" and i + 1 < len(argv):
                explicit = argv[i + 1]
                i += 2
            elif argv[i].startswith("-"):
                _usage()
                return 2
            else:
                paths.append(argv[i])
                i += 1
        if not paths:
            _usage()
            return 2
        if explicit:
            try:
                codecs.lookup(explicit)
            except LookupError:
                print(f"error: unknown encoding: {explicit}", file=sys.stderr)
                return 2
        _emit_stdout(canonical_json_dumps([inspect_file(p, explicit) for p in paths]))
        return 0

    if sub == "compare":
        explicit = None
        before_path: str | None = None
        paths = []
        i = 1
        while i < len(argv):
            if argv[i] == "--before" and i + 1 < len(argv):
                before_path = argv[i + 1]
                i += 2
            elif argv[i] == "--encoding" and i + 1 < len(argv):
                explicit = argv[i + 1]
                i += 2
            elif argv[i].startswith("-"):
                _usage()
                return 2
            else:
                paths.append(argv[i])
                i += 1
        if not before_path or not paths:
            _usage()
            return 2
        if explicit:
            try:
                codecs.lookup(explicit)
            except LookupError:
                print(f"error: unknown encoding: {explicit}", file=sys.stderr)
                return 2
        try:
            before_obj = json.loads(Path(before_path).read_text(encoding="utf-8"))
        except Exception as exc:  # noqa: BLE001
            print(f"error: before file could not be read: {_cap(str(exc))}", file=sys.stderr)
            return 4
        if isinstance(before_obj, dict):
            baselines = [before_obj]
        elif isinstance(before_obj, list):
            baselines = before_obj
        else:
            print("error: before file must be a JSON object or array", file=sys.stderr)
            return 4
        base_by_path: dict[str, dict[str, Any]] = {}
        for b in baselines:
            if isinstance(b, dict) and b.get("path"):
                base_by_path[str(b["path"])] = b
        results = [compare_file(p, base_by_path.get(p), explicit) for p in paths]
        _emit_stdout(canonical_json_dumps(results))
        return 0

    _usage()
    return 2


if __name__ == "__main__":
    raise SystemExit(_cli())
