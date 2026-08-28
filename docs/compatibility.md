# Host compatibility

Intent to Outcome Loop is vendor-neutral. The canonical `SKILL.md`
files use only generic frontmatter (`name`, `description`) so any host
can read them. Host-specific behavior is layered on top, never baked
into the canonical files.

## Officially supported (v0.4)

| Host | Install | Notes |
| --- | --- | --- |
| OpenAI Codex | `python scripts/install.py --target codex --scope user` | The `evaluate` user-only policy lives in `skills/evaluate/agents/openai.yaml`. |
| Claude Code | `python scripts/install.py --target claude --scope user` | The installer adds `disable-model-invocation: true` to the installed copy of `evaluate` so it cannot auto-invoke. |
| Pi | `python scripts/install.py --target pi --scope user` | Pi officially discovers `~/.agents/skills` and project `.agents/skills`. The Pi target shares that canonical installed view with Codex, avoiding duplicate skill names. |

All three hosts support `--scope project` and `--dry-run`. See the README
for full install instructions.

Pi supports the Agent Skills format used by the canonical files, including
recursive discovery of directories containing `SKILL.md`. Although Pi also
supports `disable-model-invocation`, the installer does not inject Pi-only
frontmatter into the shared Codex/Pi directory. Pi therefore treats
`evaluate` as user-only by instruction rather than by host-enforced hiding;
users should invoke it explicitly with `/skill:evaluate`. See the
[official Pi Skills documentation](https://pi.dev/docs/latest/skills).

## Experimentally compatible (v0.4)

| Host | Status | What works | What does not |
| --- | --- | --- | --- |
| OpenCode | Experimental | Native installer target `--target opencode` (user `~/.config/opencode/skills`, project `<cwd>/.opencode/skills`). Reads the canonical `SKILL.md` files; full package (references, supporting files) is copied. V2 suppresses `evaluate` auto-invocation via `metadata.opencode/autoinvoke`. | Stable/V1 has no per-skill auto-invocation suppression, so `evaluate` user-only is not enforced there. Real OpenCode runtime pilot pending. |
| Antigravity | Experimental | Native installer target `--target antigravity` (user `~/.gemini/config/skills`, project `<cwd>/.agents/skills`). Reads the canonical `SKILL.md` files; full package (references, supporting files) is copied — no manual copy needed. | Antigravity exposes skills through model-driven discovery with no per-skill auto-invocation suppression, so `evaluate` user-only is a convention, not host-enforced behavior. Real runtime pilot pending. |
| Grok | Experimental | Reads the canonical `SKILL.md` files directly. | No native installer target. v0.4 does not yet generate adapter metadata for Grok. Copy skills manually. |

OpenCode, Antigravity, and Grok can read the skills as plain markdown.
The `evaluate` skill is *intended* to be user-only everywhere. For OpenCode,
the installer emits `metadata.opencode/autoinvoke: "false"` on the
installed `evaluate` copy: OpenCode V2 honors it and hides the skill from
model-facing discovery while still allowing explicit invocation.
OpenCode stable/V1 accepts the `metadata` frontmatter but has no
equivalent auto-invocation enforcement, so on stable/V1 treat "user-only"
as a convention the operator must respect. Antigravity's router discovers
skills by matching the prompt against the `description` field and has no
per-skill auto-invocation suppression, so on Antigravity `evaluate` is
intended to be user-only but that is a convention rather than
host-enforced behavior. Grok has no adapter metadata; on Grok treat
"user-only" as a convention too, until a future version adds the
metadata.

## Coordinate persistence across hosts

The Codex, Claude, and Pi installed copies read the same `coordinate` skill
instructions, including the default (in-conversation packet) and
persistence (save one Handoff Markdown) modes.

- Whether a handoff file is actually saved depends on the current host's
  file-write permission and the path the user specified.
- `coordinate` does not bypass host permissions. If the host will not
  allow the write, `coordinate` reports that and writes nothing.
- `evaluate` remains user-only on every host (see above).

This repo does not claim that OpenCode, Antigravity, Grok, or any other
host not listed above is fully compatible. They can read the canonical
skills as plain markdown, but their handling of `coordinate` persistence
and the `evaluate` user-only policy is unverified.

## Why canonical frontmatter stays generic

The repository ships one canonical `SKILL.md` per skill. Host-specific
frontmatter (for example Claude's `disable-model-invocation`) is added
only to the installed copy, by `install.py`. This keeps the canonical
files portable and lets the validator prove the source of truth is
host-neutral. See [concepts.md](concepts.md) for the skill model.
