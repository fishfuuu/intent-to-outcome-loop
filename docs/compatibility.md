# Host compatibility

Coding Agent Delivery is vendor-neutral. The canonical `SKILL.md`
files use only generic frontmatter (`name`, `description`) so any host
can read them. Host-specific behavior is layered on top, never baked
into the canonical files.

## Officially supported (v0.2)

| Host | Install | Notes |
| --- | --- | --- |
| OpenAI Codex | `python scripts/install.py --target codex --scope user` | The `evaluate` user-only policy lives in `skills/evaluate/agents/openai.yaml`. |
| Claude Code | `python scripts/install.py --target claude --scope user` | The installer adds `disable-model-invocation: true` to the installed copy of `evaluate` so it cannot auto-invoke. |

Both hosts support `--scope project` and `--dry-run`. See the README
for full install instructions.

## Experimentally compatible (v0.2)

| Host | Status | What works | What does not |
| --- | --- | --- | --- |
| OpenCode | Experimental | Reads the canonical `SKILL.md` files directly. | v0.2 does not yet generate adapter metadata for OpenCode. Copy skills manually. |
| Grok | Experimental | Reads the canonical `SKILL.md` files directly. | v0.2 does not yet generate adapter metadata for Grok. Copy skills manually. |

OpenCode and Grok can read the skills as plain markdown. The
`evaluate` skill is *intended* to be user-only everywhere, but v0.2 has
not yet generated the per-host adapter metadata that would enforce that
on OpenCode and Grok. On those hosts, treat "user-only" as a convention
the operator must respect until a future version adds the metadata.

## Why canonical frontmatter stays generic

The repository ships one canonical `SKILL.md` per skill. Host-specific
frontmatter (for example Claude's `disable-model-invocation`) is added
only to the installed copy, by `install.py`. This keeps the canonical
files portable and lets the validator prove the source of truth is
host-neutral. See [concepts.md](concepts.md) for the skill model.