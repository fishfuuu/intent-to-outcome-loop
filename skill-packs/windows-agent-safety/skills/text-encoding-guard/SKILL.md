---
name: "text-encoding-guard"
description: "Read-only guard for text file encoding integrity. Inspects raw bytes (UTF-8, BOM, UTF-16, GBK/GB18030, Big5, mojibake, U+FFFD, question-mark replacement, CRLF/LF/mixed newlines, trailing newline, bidi and zero-width controls, NUL bytes) and reports deterministic, machine-verifiable JSON; compare reports encoding, BOM, newline, U+FFFD, CJK and mojibake drift between an edit and its inspect baseline. Never writes files, never converts encoding, and never auto-selects an ambiguous legacy encoding. Use before and after editing files that contain Chinese, Japanese, Korean, or other non-ASCII text, PowerShell-written files, or files that have shown mojibake, U+FFFD, question-mark replacement, or newline anomalies."
---

# text-encoding-guard

## Purpose

Verify that editing did not corrupt a text file's encoding, BOM, newline
style, trailing newline, or Unicode integrity. The guard is **read-only**:
it never writes, never converts encoding, and never auto-selects a legacy
encoding when the bytes are ambiguous.

## Use when

- Editing code or documents that contain Chinese, Japanese, Korean, or other
  non-ASCII text.
- Writing files from Windows PowerShell, or after batch replace, format, or
  generator runs that could rewrite non-ASCII files.
- The user reports mojibake, U+FFFD, question-mark replacement, or newline
  anomalies, or suspects UTF-8 / BOM / UTF-16 / GBK / GB18030 issues.

## Do not use when

- The file is already correct and the goal is to fix it. This skill only
  diagnoses; it never converts or repairs.
- The path is a directory or a stream, not a file.

## How to run

```text
python text_encoding_guard.py inspect [--encoding NAME] <path>...
python text_encoding_guard.py compare --before <inspect.json> <path>...
```

- `inspect` reads raw bytes, never the platform default encoding, and never
  modifies the file. Output is canonical JSON (UTF-8, LF, no BOM, sorted
  keys) with `write_authorized` always `"NO"`.
- `compare` reads an earlier `inspect` output as the baseline and reports
  drift (encoding, BOM, newline, trailing newline, new U+FFFD, CJK replaced
  by question marks, new mojibake, new dangerous Unicode) while allowing
  normal content changes. It also never writes.

## Statuses

`SAFE_UTF8`, `SAFE_UTF8_BOM`, `SAFE_UTF16_LE`, `SAFE_UTF16_BE`,
`EXPLICIT_LEGACY_ENCODING_REQUIRED`, `VALIDATED_LEGACY_ENCODING`,
`POSSIBLE_MOJIBAKE`, `AMBIGUOUS_TEXT_ENCODING`, `BINARY_OR_UNSUPPORTED`,
`IO_ERROR`.

## Fail-closed rules

- ASCII is safe UTF-8; UTF-8 is only ever accepted after a strict decode.
- UTF-8 / UTF-16 BOMs are recognized explicitly; a BOM-less UTF-16 file is
  never guessed.
- A legacy file (GBK/GB18030, Big5, Shift-JIS, EUC-JP) is never auto-chosen:
  one candidate family yields `EXPLICIT_LEGACY_ENCODING_REQUIRED`, several
  yield `AMBIGUOUS_TEXT_ENCODING`. An explicit `--encoding` with a strict
  decode success yields `VALIDATED_LEGACY_ENCODING`; a failed decode stays
  fail-closed as `BINARY_OR_UNSUPPORTED`.
- Latin-1 is never used as a decode-everything fallback, and decoding never
  uses `errors="replace"` to mask failures.
- NUL-heavy bytes without a BOM are `BINARY_OR_UNSUPPORTED`, never assumed
  to be UTF-16.
- Nothing is ever converted to UTF-8 and mojibake is never auto-reversed.

## Safety rules for the agent

- `write_authorized` is always `"NO"`. A clean report is not permission to
  overwrite a file whose encoding is in doubt.
- On `AMBIGUOUS_TEXT_ENCODING`, `POSSIBLE_MOJIBAKE`, or a compare drift of
  type `ENCODING_DRIFT` / `NEW_MOJIBAKE` / `NEW_DANGEROUS_UNICODE`, stop and
  ask the operator; do not re-save the file.
- Findings report position, code point, type, and short redacted evidence
  only; whole file content and secrets are never emitted.

## Stop conditions

- The file cannot be read or decoded: report the status and stop.
- The encoding is ambiguous or a compare shows encoding/mojibake drift: stop
  before any further write.
- The user redirects or the target changes: re-run `inspect` first.
