# Lingo Loop Skill Hub Install Design (Four Providers)

Date: 2026-05-31
Status: Approved design (rev. 2026-05-31 — Claude/Codex switched from
plugin-bundled skills to the provider personal skills hub; the Claude/Codex
plugin path is dropped)

Revision note: validation against the four provider docs
(hermes-agent.nousresearch.com/docs, docs.openclaw.ai,
code.claude.com/docs, developers.openai.com/codex) confirmed that Claude
(`~/.claude/skills/<name>/SKILL.md`) and Codex (`~/.codex/skills/<name>/SKILL.md`)
both auto-discover a **personal skills hub** with no plugin and no marketplace
registration — the same flat file-drop model Hermes and OpenClaw already use. A
marketplace plugin would surface the skill markdown but cannot install the
`tutor` Python engine the skills shell out to, so click-install never yields a
working tutor. The Claude/Codex plugin is therefore dropped; all four providers
now share one uniform skills hub destination `<root>/skills/`.

This spec supersedes, for the upstream `lingo-loop` repo, both:

- `docs/internal/superpowers/plans/2026-05-31-lingo-loop-skill-hub-design.md` (base:
  unified Hermes + OpenClaw skill-hub install)
- `docs/internal/superpowers/plans/2026-05-31-old-lingo-loop-hermes-skill-hub-design.md`
  (`HERMES_HOME` path-resolver clarification, verified against the live Hermes
  container)

It extends that work to **all four supported providers** — Hermes, OpenClaw,
Claude, and Codex — and pins the implementation to the repo's existing
`BaseProviderInstaller` subclass pattern.

## Scope

- **This repo only** (`/Users/artem.veduta/python/language-tutor`): canonical
  skill source, the four provider installers, packaging, and tests.
- **No homelab changes.** Homelab pin bumps, Dockerfiles, entrypoints, compose,
  and Telegram quick-commands are handled separately by the owner and are out of
  scope here.

## Goal

Make every supported provider surface the seven tutor skills (six flows plus
`tutor-judge`) in its skill hub, materialized by `tutor init --provider <p>`
from one shared asset tree shipped in the wheel.

The six flows the learner sees: setup, vocab, writing, reading, lesson,
progress; plus the `tutor-judge` grader.

## Core Decisions

1. **One skills source, copied verbatim per provider.** The repo `skills/` tree
   is the single source of truth. The wheel ships it once under
   `_assets/skills/`. Each provider installer copies that same tree, byte for
   byte, into a provider-resolved destination. **No per-provider frontmatter
   rendering** and **no build-time generator.** Frontmatter stays plain
   `name` + `description`, the common denominator every provider's `SKILL.md`
   accepts (all four follow the Agent Skills open standard).

2. **Flat layout everywhere.** No Hermes category subfolders, no OpenClaw
   `metadata.openclaw.{category,requires.bins,cliHelp}` block. The base doc's
   per-provider enrichment is intentionally dropped in favor of a single flat
   tree. Per-provider richness is sacrificed for one source of truth.

3. **`tutor-judge` becomes a skill.** It is currently an *agent*
   (`agents/tutor-judge.md`, referenced as `judge_agent` in
   `adapters/claude.py`). It is converted to `skills/tutor-judge/SKILL.md` and
   ships in the same flat tree as the six flows. Judge is a stateless grader the
   flows invoke; a `SKILL.md` serves identically.

4. **Base installer + thin per-provider subclasses.** `BaseProviderInstaller`
   keeps its verbatim byte-copy + byte-level drift model. It is extended to
   handle a **list of managed areas** instead of one. Each concrete installer
   (`HermesInstaller`, `OpenClawInstaller`, `ClaudeInstaller`, `CodexInstaller`)
   stays thin: it declares its areas and overrides only its root resolver. This
   is the "basic installer extended by per-provider logic" — plain subclassing.

5. **Claude and Codex install into the personal skills hub — no plugin.** Both
   providers auto-discover flat `SKILL.md` under their personal hub
   (`<CLAUDE_CONFIG_DIR|~/.claude>/skills/`,
   `<CODEX_HOME|~/.codex>/skills/`), enabled by default, with no plugin manifest
   and no marketplace registration. The Claude/Codex plugin path is dropped: the
   manifests carried only metadata (no commands, no hooks), so the plugin was a
   pure skill-wrapper that the personal hub replaces more reliably. A marketplace
   plugin is explicitly rejected — it ships skill markdown but not the `tutor`
   Python engine the skills depend on, so click-install yields a non-working
   tutor. This makes all four providers a single model: `tutor init` drops the
   flat skill tree into `<root>/skills/`.

6. **Hermes keeps the profile and adds skills.** The three profile files stay a
   managed area; the skills hub is added as a second managed area. Hermes paths
   resolve from `HERMES_HOME` first (the old-doc root-cause fix).

## Canonical Skill Source

`skills/` in the repo is the one source of truth. Changes:

- Move `agents/tutor-judge.md` → `skills/tutor-judge/SKILL.md`. Remove the
  standalone agents asset.
- Rewrite all skill bodies and helper scripts: replace source-relative
  `bin/tutor` with the installed console script `tutor`. Helper scripts resolve
  the binary via `os.environ.get("LANGUAGE_TUTOR_TUTOR_BIN", "tutor")`, matching
  the OpenClaw plugin convention.
- Frontmatter is plain `name` + `description` only.

The seven skills (the shared file list every installer's skills area copies):

```
tutor-setup/SKILL.md
tutor-vocab/SKILL.md
tutor-vocab/scripts/run.py
tutor-writing/SKILL.md
tutor-writing/scripts/run.py
tutor-reading/SKILL.md
tutor-lesson/SKILL.md
tutor-progress/SKILL.md
tutor-progress/scripts/run.py
tutor-judge/SKILL.md
```

Packaging: `pyproject.toml` `force-include` maps repo `skills/` →
`language_tutor/_assets/skills/`. The `agents/tutor-judge.md` force-include entry
is removed; `tutor-judge/SKILL.md` is added under the skills mappings. Editable
installs resolve assets from the repo `skills/`; wheel installs from
`_assets/skills/`.

Code references to update when judge moves and the Claude/Codex plugin is dropped:

- `src/language_tutor/package_assets.py` — drop `agents/tutor-judge.md`, add the
  judge skill path; drop the `.claude-plugin/plugin.json` and
  `.codex-plugin/plugin.json` `force-include` entries.
- `src/language_tutor/adapters/claude.py` — `plugin_root_components` no longer
  describes a plugin. Repoint it at the skills hub (`"judge_skill":
  "skills/tutor-judge/SKILL.md"`, the six flow skills, no `"manifest"`), or
  remove it if nothing consumes the plugin manifest path anymore.
- Delete the now-unused `.claude-plugin/plugin.json` and
  `.codex-plugin/plugin.json` manifests from the repo (don't ship dead files).
- `src/language_tutor/installer/providers/claude.py` and `codex.py` — drop the
  plugin registration area; declare a single skills area rooted at
  `<config_root>/skills`.

## Installer Architecture

### Managed areas

`ProviderProfile` gains a list of managed areas. Each area is a small spec:

```python
@dataclass(frozen=True)
class ManagedArea:
    bundled_assets_root_rel: str   # host-package dir in _assets (or "skills")
    managed_dir_rel: str           # destination, relative to the resolved root
    files: tuple[str, ...]         # explicit per-file list
```

`ProviderProfile` carries `areas: tuple[ManagedArea, ...]` (plus the existing
`host`, `cli_name`, `config_root_rel`, `next_command`). The area count varies by
provider:

- a **skills area** (every provider) — bundled root `skills` (the shared
  `_assets/skills/` tree), the seven-file list above, destination
  `<config_root>/skills` for all four,
- a **registration area** (Hermes and OpenClaw only) — Hermes profile files,
  OpenClaw plugin/channel files (per-provider, as today). Claude and Codex have
  **no** registration area; they ship the skills area alone.

### Base behavior (unchanged per-file logic, now per-area)

`detect` / `plan` / `apply` / `verify` iterate every area and run the existing
per-file verbatim-copy + byte-compare logic against it. Aggregate rules:

- `INSTALLED` only if every area is fully installed and drift-free.
- `AVAILABLE` only if every file in every area is absent.
- `NEEDS_REPAIR` if any area has a missing or content-divergent file; the repair
  plan emits one `WRITE_FILE` action per divergent file across all areas.
- `BLOCKED` keeps its current meaning (CLI missing, config root absent, or a
  bundled asset missing from the wheel — reported by exact relative path).

No rendering, no string composition: drift detection stays a byte comparison
between the bundled file and the on-disk file, so it is deterministic and cannot
produce spurious repair loops.

### Root resolvers — the per-subclass "specific logic"

`config_root()` is the only path method a subclass overrides. The base default
is `fs.home() / config_root_rel`. Area destinations are
`config_root() / area.managed_dir_rel`.

| Provider | `config_root()` resolution |
|---|---|
| Base | `fs.home() / config_root_rel` |
| Hermes | `HERMES_HOME` (expanded) if set, else `fs.home() / ".hermes"` |
| Codex | `CODEX_HOME` (expanded) if set, else `fs.home() / ".codex"` |
| Claude | `CLAUDE_CONFIG_DIR` (expanded) if set, else `fs.home() / ".claude"` |
| OpenClaw | `fs.home() / ".openclaw"` |

The Hermes resolver is the old-doc root-cause fix: the resolver must read
`HERMES_HOME` and never `fs.home()` alone. The same `*_HOME`-first pattern is
applied to Codex for parity (container/CLI portability).

### Per-provider areas

| Provider | registration area dest | skills area dest |
|---|---|---|
| Claude | — (none) | `<root>/skills/` |
| Codex | — (none) | `<root>/skills/` |
| OpenClaw | `<root>/plugins/lingo-loop/<7 plugin files>` | `<root>/skills/` |
| Hermes | `<root>/profiles/lingo-loop/<3 profile files>` | `<root>/skills/` |

- Claude: skills go to the personal hub `<CLAUDE_CONFIG_DIR|~/.claude>/skills/`,
  auto-discovered and enabled by default, live-watched (a brand-new top-level
  skills dir created mid-session needs one restart). No plugin.
- Codex: skills go to the personal hub `<CODEX_HOME|~/.codex>/skills/`,
  auto-discovered globally across projects. Codex loads skills at startup, so
  the post-init step is "restart Codex". No plugin, no marketplace.
- OpenClaw: existing seven plugin/channel files stay; skills go to the
  auto-discovered managed hub `<root>/skills/` (flat, alongside `gws-*`), which
  outranks plugin-bundled skills in OpenClaw's precedence order.
- Hermes: existing three profile files stay (`distribution.yaml`,
  `config.yaml`, `SOUL.md`); skills go to `<HERMES_HOME>/skills/`.

### Hermes profile caveat (carried from old doc)

The old doc verified, on the live `hermes-language-tutor` container, that the
profile path was inert: the container runs flat-home (`HERMES_HOME=/opt/data`,
profile mode off, only `◆default` registered), so files written under
`profiles/lingo-loop/` are not read by the gateway. This design **keeps** the
profile area by explicit choice. The `HERMES_HOME`-first resolver at least roots
the profile correctly (`<HERMES_HOME>/profiles/lingo-loop`) for hosts that do use
profile mode (e.g. a laptop CLI). The skills area is what makes the flows
discoverable on the live container, and it lands in `<HERMES_HOME>/skills`
regardless of profile mode.

## Installer Behavior and Safety

- Copy bundled files verbatim into the resolved destinations; repair only
  missing or content-divergent files.
- Never touch learner state, secrets, memories, sessions, plugin registries, or
  unrelated skills (`gws-*`, other Hermes skills). Overwrite empty placeholder
  files (e.g. a `.gitkeep`) with the real skill content when present.
- Missing bundled asset → `BLOCKED` with the exact relative path and a repair
  hint (packaging defect).
- `tutor doctor --json` validates that all bundled assets for the requested
  provider are present, plus migrations / writable state / config schema,
  without creating a learner session.
- Missing `tutor` binary or missing provider CLI / config root blocks install
  with the existing status model.
- Secrets remain outside package assets and provider init flows.

## Portable Install

The same instruction installs on any host where the `tutor` console script and
the target provider share a config root:

```bash
pip install lingo-loop        # or pipx / uv tool install
tutor init --provider <hermes|openclaw|claude|codex> --yes
```

The only per-host difference is the resolved root (e.g. `HERMES_HOME=/opt/data`
→ `/opt/data/skills` in a container vs `~/.hermes/skills` on a laptop). No
provider-native whole-agent distribution command (`hermes profile install …`,
nor a Claude/Codex marketplace plugin) is required; this design ships skills to
`<root>/skills/` for all four providers, plus — for Hermes and OpenClaw only —
the existing profile/plugin registration files.

## Skill Command Contract

Installed skill markdown describes `tutor <flow> --json` commands, never
source-relative `bin/tutor`. Helper scripts resolve the binary via
`os.environ.get("LANGUAGE_TUTOR_TUTOR_BIN", "tutor")`. The agent calls boot
context (`session-start`) on the first stateful tutor message and reads learner
state from `LANGUAGE_TUTOR_HOME`.

## Testing

Shared:

- One canonical `skills/` tree feeds every provider's skills area; markdown and
  helper scripts use `tutor` / `LANGUAGE_TUTOR_TUTOR_BIN`, not `bin/tutor`.
- `tutor-judge` exists as `skills/tutor-judge/SKILL.md`; no `agents/` asset
  remains; `package_assets.py` and `adapters/claude.py` reference the skill, not
  the old agent path.
- Single-file drift repairs only the divergent file (any area).
- Missing packaged assets are reported by exact relative path.
- Aggregate status: a provider is `INSTALLED` only when every area is clean;
  `NEEDS_REPAIR` when any area diverges.
- Full suite green before release.

Per provider:

- Hermes and OpenClaw profiles declare both areas (registration + skills);
  Claude and Codex declare a single skills area. Every profile lists exactly the
  seven skill files for its skills area.
- `tutor init --provider <p> --yes` writes the declared areas and the seven
  skills into the resolved destination; second init is idempotent.
- Claude/Codex write skills to `<config_root>/skills` and create no plugin
  manifest; `.claude-plugin`/`.codex-plugin` are not referenced by packaging.
- The installer does not delete or modify unrelated skills (`gws-*`) or the
  registration files of other providers.

Resolver tests:

- Hermes: with `HERMES_HOME` set, the resolved root (and therefore both areas)
  is `<HERMES_HOME>/…`; unset, it falls back to `~/.hermes`. The resolver never
  uses `fs.home()` when `HERMES_HOME` is present.
- Codex: same `CODEX_HOME` set/unset assertions against `~/.codex`.
- Claude: `CLAUDE_CONFIG_DIR` set/unset against `~/.claude`.

## Release Blockers

Verify before tagging the release:

1. **Plain-flat hub discovery per provider.** Confirm each provider discovers a
   flat `<root>/skills/<name>/SKILL.md` carrying only `name` + `description` (no
   Hermes category dir, no OpenClaw metadata block). OpenClaw auto-discovery of
   the `gws-*` managed hub is the precedent; confirm the equivalent for Hermes
   (`$HERMES_HOME/skills`), Claude (`~/.claude/skills`, live-watched), and Codex
   (`~/.codex/skills`, restart to reload). Codex gotcha: the entry file must be
   named exactly `SKILL.md` — `SKILL.MD` is silently skipped (codex#20637); the
   shared tree already uses `SKILL.md`, so assert it in packaging tests.
2. **Skills enabled by default per provider.** Hermes, OpenClaw, Claude, and
   Codex all enable discovered hub skills by default. OpenClaw adds a per-agent
   allowlist (`agents.defaults.skills`, `agents.list[].skills`) that can hide
   skills regardless of discovery — confirm the tutor skills are not excluded.
   Any enable/allowlist step is a homelab concern and out of scope here, but the
   finding is recorded for the homelab work.

## Non-Goals

- No homelab changes (Dockerfiles, compose, entrypoints, pins, Telegram
  quick-commands).
- No per-provider frontmatter rendering or build-time skill generator.
- No Hermes category subfolders or OpenClaw `metadata.openclaw` block.
- No plugin-bundled or marketplace install for Claude/Codex (personal skills
  hub only). The `.claude-plugin/plugin.json` and `.codex-plugin/plugin.json`
  manifests are removed.
- No data migration of learner state between providers.
- No new tutor flows beyond the six existing flows plus `tutor-judge`.
- No behavior change to unrelated agents or `gws-*` skills.
</content>
</invoke>
