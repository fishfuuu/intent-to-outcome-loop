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

Both hosts support `--scope project` and `--dry-run`. See the README
for full install instructions.

## Experimentally compatible (v0.4)

| Host | Status | What works | What does not |
| --- | --- | --- | --- |
| OpenCode | Experimental | Reads the canonical `SKILL.md` files directly. | v0.4 does not yet generate adapter metadata for OpenCode. Copy skills manually. |
| Grok | Experimental | Reads the canonical `SKILL.md` files directly. | v0.4 does not yet generate adapter metadata for Grok. Copy skills manually. |

OpenCode and Grok can read the skills as plain markdown. The
`evaluate` skill is *intended* to be user-only everywhere, but v0.4 has
not yet generated the per-host adapter metadata that would enforce that
on OpenCode and Grok. On those hosts, treat "user-only" as a convention
the operator must respect until a future version adds the metadata.

## Coordinate persistence across hosts

The Codex and Claude installed copies read the same `coordinate` skill
instructions, including the default (in-conversation packet) and
persistence (save one Handoff Markdown) modes.

- Whether a handoff file is actually saved depends on the current host's
  file-write permission and the path the user specified.
- `coordinate` does not bypass host permissions. If the host will not
  allow the write, `coordinate` reports that and writes nothing.
- `evaluate` remains user-only on every host (see above).

This repo does not claim that OpenCode, Grok, or any other host not
listed above is fully compatible. They can read the canonical skills as
plain markdown, but their handling of `coordinate` persistence and the
`evaluate` user-only policy is unverified.

## Why canonical frontmatter stays generic

The repository ships one canonical `SKILL.md` per skill. Host-specific
frontmatter (for example Claude's `disable-model-invocation`) is added
only to the installed copy, by `install.py`. This keeps the canonical
files portable and lets the validator prove the source of truth is
host-neutral. See [concepts.md](concepts.md) for the skill model.