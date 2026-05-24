# Stack Research

**Domain:** AI language tutor delivered as a Claude Code plugin, with a portable Python core
**Researched:** 2026-05-19
**Confidence:** HIGH (verified against official Claude Code docs, PyPI releases, official library repos)

## Executive Recommendation

Single-language, fully synchronous Python core (Python 3.12+), distributed as a Claude Code plugin where each skill is a `SKILL.md` that invokes a small Python CLI bundled in `bin/` via dynamic-context shell injection. No async, no ORM, no FastAPI. Stdlib `sqlite3` + `ruamel.yaml` + Pydantic v2 + pytest+syrupy. Type-check with pyright in strict mode. Build with hatchling.

This stack optimizes for: zero runtime cost beyond Claude itself, deterministic golden testing, human-editable YAML, transactional SQLite, and the smallest dependency surface a marketplace plugin can ship.

---

## Recommended Stack

### Core Technologies

| Technology | Version | Purpose | Why Recommended |
|---|---|---|---|
| **Python** | **3.12 minimum**, target 3.13 | Runtime for shared core + adapters + DAL | 3.12 is the current oldest non-EOL version most user systems already have (EOL Oct 2028). 3.13 is the recommended target through 2026. Picking 3.12 minimum avoids forcing learners to upgrade Python while giving the core: PEP 695 type aliases, `tomllib`, better error messages, and stable `sqlite3` extensions. Do **not** require 3.13 — many macOS/Linux distros still ship 3.12. |
| **`sqlite3` (stdlib)** | bundled | Transactional store: answer_events, mistake_events, srs_items, srs_reviews, session_summaries, skill_metrics | Zero install. SQLite 3.45+ ships in Python 3.12 stdlib. Workload is single-writer, single-user, append-heavy — no concurrency story is needed and no ORM features (relationships, lazy loading, cross-DB portability) are needed. Adding SQLAlchemy/SQLModel here would buy nothing real and cost ~30 MB + boot time. |
| **`ruamel.yaml`** | **^0.18** | Profile + preferences YAML I/O with comment preservation | The YAML files are human-edited. PyYAML drops comments and reorders keys on round-trip. ruamel.yaml round-trip preserves comments, key order, and indentation 1:1 — required behavior for a config the learner is supposed to maintain by hand. Use `YAML(typ='safe')` for boot-time reads where comments are not needed, and `YAML(typ='rt')` only for the setup/edit flow. |
| **Pydantic v2** | **^2.13** (current 2.13.4, May 2026) | Schema validation for `BootContext`, `FeedbackEnvelope`, `SessionAnalysis`, `AnswerEvent`, lifecycle events | Defines core contracts as Python types, gets free JSON Schema export via `model_json_schema()` to satisfy the `schemas/*.schema.json` artifact requirement from `docs/design.md`, validates LLM-as-judge JSON output on the hot path. 5–50x faster than v1 / Marshmallow. Native discriminated unions for severity / lifecycle event types. |

### Supporting Libraries

| Library | Version | Purpose | When to Use |
|---|---|---|---|
| **`pydantic`** | ^2.13 | All inter-layer contracts | Always — boot context, feedback envelope, session analysis, answer events |
| **`ruamel.yaml`** | ^0.18 | YAML profile/preferences | DAL `yaml_store.py` |
| **`click`** | ^8.1 | CLI entrypoint for each skill (`tutor-vocab`, `tutor-writing`, etc.) | The plugin invokes `bin/tutor` via `!\`...\`` shell injection from SKILL.md. Click gives subcommands, typed args, and `--help` cheaply. **Not** Typer — Typer adds a dependency on the Rich/Pydantic stack we already have but pulls more transitive deps without benefit at this scale. |
| **`platformdirs`** | ^4.3 | Locate XDG data dir for SQLite + YAML (`~/.local/share/language-tutor/`, `~/Library/Application Support/language-tutor/`) | DAL bootstrap. Avoids ad-hoc `os.path.expanduser` and gets macOS+Linux right out of the box. |
| **No SRS library** | — | SM-2 implemented in-tree (`core/language_tutor/srs.py`, ~80 lines) | The SM-2 algorithm is ~5 fields and a single function. `anki-sm-2` exists (open-spaced-repetition/anki-sm-2) but is AGPL-3.0 — viral copyleft is incompatible with an OSS plugin most users would want to fork or relicense. `py-fsrs` is FSRS not SM-2 and the project has explicitly scoped FSRS out. **Write SM-2 yourself**: 6-field card state + a `review(card, quality, now) -> card` function. Golden-test it. Total cost is lower than integrating any library. |
| **`pytest`** | ^8.3 | Test runner | All test tiers (unit, integration, golden, adapter contract) |
| **`syrupy`** | ^4.7 | Snapshot/golden testing for `FeedbackEnvelope` markdown + boot context format | The design doc mandates golden tests for feedback markdown + severity rendering. Syrupy is the idiomatic pytest snapshot plugin (`assert rendered == snapshot`), zero-dep, supports custom serializers if Amber's default isn't right for raw markdown. Update snapshots with `pytest --snapshot-update`. |
| **`pytest-cov`** | ^6.0 | Coverage reporting | CI gate |
| **`freezegun`** | ^1.5 | Deterministic time in SRS tests (intervals, due-date math) | SRS math depends on `now()`. Without freezing time, golden tests are flaky. |

### Development Tools

| Tool | Purpose | Notes |
|---|---|---|
| **`hatchling`** | Build backend in `pyproject.toml` | PyPA-maintained, zero-config for pure-Python, supports `[tool.hatch.build.targets.wheel]` for the `core/`, `adapters/`, `dal/` layout. `uv_build` is the new default for `uv init` projects, but hatchling is still the safer pick when packaging a multi-package monorepo (`core/`, `adapters/`, `dal/` each in their own `src/`). Revisit `uv_build` if/when the project consolidates to one package. |
| **`uv`** | ^0.5 | Dep management, lockfile, virtualenv | 10–100x faster than pip; produces a reproducible `uv.lock`. The plugin install flow can rely on `uv tool install` or `uv run` if Python invocation from hooks needs isolation. Do not require uv as a runtime dependency for end users — keep `pip install -e .` working. |
| **`pyright`** | latest | Static type checker | Strict mode (`"strict"`). 2–5x faster than mypy, 98% spec conformance, no plugin sprawl (we don't use Django/SQLAlchemy stubs). Add a `pyrightconfig.json` with `strict: ["core/", "adapters/", "dal/"]`. Do **not** also run mypy — pick one type checker, save CI time. |
| **`ruff`** | ^0.8 | Linter + formatter (replaces black, isort, flake8) | One tool, one config block in `pyproject.toml`, ~100x faster than the trio. Enable `E,F,I,UP,B,SIM,RUF` rule sets. |
| **`pre-commit`** | ^4.0 | Git hook runner | Wire ruff + pyright + `claude plugin validate` into pre-commit so the plugin manifest doesn't drift. |

### What we are NOT using (and why)

| Library | Reason |
|---|---|
| **SQLAlchemy / SQLModel** | ORM overhead for a single-user, single-writer SQLite with ~6 tables. Stdlib `sqlite3` + a thin repository pattern is simpler and faster. SQLModel would also drag in async machinery we don't need. |
| **`aiosqlite`** | Async SQLite buys nothing here. The lifecycle is event-at-a-time, driven by a synchronous plugin hook. No concurrent learners, no event loop, no network I/O on the hot path. Async would add cognitive cost and color the entire core with `async def`. |
| **Alembic / yoyo-migrations** | Migration tooling for a v1 with 6 tables is overkill. Use plain numbered SQL files in `data/migrations/*.sql` and a `schema_migrations(version INT PRIMARY KEY, applied_at TEXT)` table read at boot. This is what `docs/design.md` already implies. Revisit if the schema reaches double-digit migrations. |
| **PyYAML** | Drops comments and reorders keys. The whole point of `profile.yaml` is that the learner edits it. |
| **Typer** | Click already does what we need; Typer adds a layer without benefit at this scale. |
| **`anki-sm-2`** | AGPL-3.0 — incompatible with permissive OSS plugin distribution. The algorithm is small enough to own. |
| **`py-fsrs`** | Wrong algorithm. Project decision is SM-2 for v1 (`docs/design.md` §Out of Scope). |
| **`anki` (full Anki Python)** | Ships a Qt UI, sync server client, and a card model far beyond what's needed. |
| **`jsonschema`** | Pydantic v2 emits JSON Schema for free via `model_json_schema()` and validates 3.5x faster than `jsonschema` while keeping the schema as Python types (single source of truth). |
| **`dataclasses` + `TypedDict`** | No runtime validation. We need to validate LLM-as-judge JSON output at the boundary — dataclasses can't do that without a third library. |
| **`mypy`** | Slower than pyright, more plugin-dependent. Pick one. |
| **FastAPI / any web framework** | No HTTP server. Plugin runs as subprocess invoked by Claude. |
| **`rich` / `textual`** | The renderer outputs markdown that Claude (or another host) displays. No terminal UI library is needed. Stdlib f-strings + a 30-line `feedback_renderer.py` covers the severity-emoji + markdown layout requirement. |
| **Markdown rendering library** (`markdown-it-py`, `mistune`) | We *emit* markdown for the host to display, we don't *parse* it. f-strings suffice. |

---

## Async or sync?

**Sync.** Justification:

1. The plugin lifecycle is one synchronous event per turn (`SessionStart` → exercise → `AnswerReceived` → feedback → ...). There is no concurrency.
2. SQLite writes are local and microsecond-scale. Async gains zero throughput here.
3. The Claude API call inside the evaluator is synchronous per turn from the tutor's perspective — Claude itself drives the loop; our core just returns structured output.
4. Async colors every function. Forcing `async def` through `core/` for no gain is the textbook anti-pattern.

If a future host adapter needs concurrency (unlikely), wrap the sync core in a thread or process. Don't async-ify the core.

---

## Claude Code plugin manifest format (verified against official docs, 2026)

### `.claude-plugin/plugin.json`

Only `.claude-plugin/plugin.json` lives in `.claude-plugin/`. Everything else (`skills/`, `hooks/`, `agents/`, `bin/`) lives at the **plugin root**, not inside `.claude-plugin/`. This is the most common mistake per the official docs.

```json
{
  "name": "language-tutor",
  "description": "Daily AI language tutor with SRS-driven vocab + writing practice and host-identical feedback. Profile lives in YAML, learner history in SQLite, all local.",
  "version": "0.1.0",
  "author": { "name": "Artem Veduta" },
  "homepage": "https://github.com/<owner>/language-tutor",
  "repository": "https://github.com/<owner>/language-tutor",
  "license": "MIT"
}
```

`version` is optional but **set it** — if omitted, Claude treats every git commit as a new version, breaking user pinning.

### `skills/<name>/SKILL.md` frontmatter

The full schema for SKILL.md frontmatter (verified at `code.claude.com/docs/en/skills`):

```yaml
---
name: tutor-vocab          # optional, defaults to directory name; lowercase + hyphens, max 64 chars
description: Use when the learner wants vocabulary practice, due SRS reviews, word recall drills, or lexical correction.
disable-model-invocation: false   # default false; set true for skills that should only be triggered manually (e.g. tutor-setup)
allowed-tools: Bash(tutor *)      # pre-approves the bin/tutor CLI so users aren't prompted per-call
argument-hint: "[count]"
---

## Run a vocab session

!`${CLAUDE_SKILL_DIR}/../../bin/tutor vocab start --count ${1:-10}`

[Skill prompt body that interprets the JSON the CLI emits and renders the FeedbackEnvelope per turn]
```

Key fields the design relies on:

- **`description`** — drives Claude's auto-invocation; cap is 1,536 chars combined with `when_to_use`.
- **`allowed-tools`** — pre-approves `Bash(tutor *)` so the learner isn't prompted on every turn.
- **`disable-model-invocation: true`** — set on `tutor-setup` (don't let Claude unilaterally rewrite profile.yaml).
- **`${CLAUDE_SKILL_DIR}`** — resolves to the skill's own dir so the bash injection path is stable across personal/project/plugin installs.
- **`!\`...\`` injection** — runs *before* Claude sees the skill content. This is how the Python core feeds JSON state into the prompt deterministically.

### `hooks/hooks.json`

Hooks live in `hooks/hooks.json` (not in `.claude-plugin/`). The shape matches `.claude/settings.json`:

```json
{
  "hooks": {
    "SessionStart": [
      {
        "hooks": [
          { "type": "command", "command": "tutor boot-context" }
        ]
      }
    ],
    "SessionEnd": [
      {
        "hooks": [
          { "type": "command", "command": "tutor session-end" }
        ]
      }
    ]
  }
}
```

Hooks receive JSON on stdin (session info, tool input, tool response) and communicate via exit codes (0 = ok, 2 = block) and stdout/stderr.

Available lifecycle hooks (verified): `SessionStart`, `SessionEnd`, `UserPromptSubmit`, `PreToolUse`, `PostToolUse`, `Stop`, `StopFailure`, plus skill-scoped `hooks` field. Map our canonical lifecycle as follows:

| Canonical event | Claude hook |
|---|---|
| `SessionStart`, `BootContextRequested`, `BootContextLoaded` | `SessionStart` hook → `tutor boot-context` emits JSON for the boot prompt |
| `ExercisePresented` → `AnswerReceived` → `FeedbackRendered` | Inside skill body (Claude orchestrates per turn, calling `tutor` CLI subcommands) |
| `SessionAnalysisRequested`, `SessionAnalyzed`, `StatePersisted`, `SessionEnd` | `SessionEnd` hook → `tutor session-end` runs analyzer + persists |

### Plugin → Python core invocation (CLI / entrypoints)

**Decision: subprocess via a single `bin/tutor` CLI.** Reasoning:

1. **Subprocess (Click CLI in `bin/tutor`)** ✅ chosen — stable, language-agnostic, every host adapter can call it identically, fits the "host adapter translates, core decides" rule. JSON in / JSON out.
2. **Python module import** ❌ — plugin hosts don't share a Python runtime with our core; would require the user to install our package globally and pin a Python version.
3. **MCP server** ❌ — overkill for a synchronous local CLI. MCP shines for tool servers shared across sessions. Reconsider if/when we want the tutor's data queryable by other Claude tools mid-session.

`bin/tutor` is added to PATH automatically by Claude Code when the plugin is enabled (per the official `bin/` convention). It dispatches to subcommands: `tutor boot-context`, `tutor vocab next`, `tutor vocab answer`, `tutor writing evaluate`, `tutor session-end`. Each subcommand reads JSON from stdin or args and writes a validated Pydantic model as JSON to stdout.

---

## Installation

`pyproject.toml`:

```toml
[build-system]
requires = ["hatchling>=1.27"]
build-backend = "hatchling.build"

[project]
name = "language-tutor"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = [
  "pydantic>=2.13,<3",
  "ruamel.yaml>=0.18,<1",
  "click>=8.1,<9",
  "platformdirs>=4.3,<5",
]

[project.optional-dependencies]
dev = [
  "pytest>=8.3",
  "pytest-cov>=6.0",
  "syrupy>=4.7",
  "freezegun>=1.5",
  "pyright>=1.1.400",
  "ruff>=0.8",
  "pre-commit>=4.0",
]

[project.scripts]
tutor = "language_tutor.cli:main"
```

Install for development:

```bash
uv venv && uv pip install -e ".[dev]"
```

Plugin users do not install the Python package directly — the plugin marketplace bundles `bin/tutor` as an executable shim that resolves the bundled Python source.

---

## Alternatives Considered

| Recommended | Alternative | When to Use Alternative |
|---|---|---|
| stdlib `sqlite3` | SQLModel | If we add a second persistence layer or another author wants type-safe queries badly — but not for v1's 6-table schema. |
| ruamel.yaml | PyYAML (`safe_load` only) | If we ever stop allowing humans to edit YAML directly and the files become machine-only. |
| Pydantic v2 | `attrs` + `jsonschema` | If we want runtime-free dataclasses and validate at boundaries only — but loses single-source-of-truth schemas. |
| In-tree SM-2 | `py-fsrs` | If the project later upgrades to FSRS (currently scoped out). |
| hatchling | `uv_build` | When the repo collapses to a single package and we want the fastest possible builds. |
| pyright | mypy | If we add a heavy SQLAlchemy or Django plugin ecosystem (unlikely). |
| sync | async | Never, in this codebase, unless a host adapter spawns concurrent sessions. |
| subprocess CLI | MCP server | If another Claude tool needs to query learner state mid-session without going through skills. |

---

## What NOT to Use

| Avoid | Why | Use Instead |
|---|---|---|
| `anki-sm-2` | AGPL-3.0 — viral copyleft incompatible with permissive marketplace distribution | In-tree SM-2 implementation (~80 lines) |
| `py-fsrs` | Wrong algorithm; FSRS explicitly out of v1 scope | In-tree SM-2 |
| PyYAML for round-tripped configs | Drops comments + reorders keys | `ruamel.yaml` with `typ='rt'` |
| `jsonschema` (Python lib) for contract validation | 3.5x slower than Pydantic v2 + duplicates the source of truth | Pydantic v2 with `model_json_schema()` |
| `aiosqlite` | Async coloring for zero benefit | Stdlib `sqlite3` |
| SQLAlchemy / SQLModel | ORM features unused, install cost + boot time, async machinery | Stdlib `sqlite3` + a thin repository pattern |
| Typer | Adds deps without benefit over Click at this scale | `click` |
| Custom markdown parser | We emit markdown, we don't parse it | f-strings + a tiny `severity → emoji` map |
| `rich` for renderer | Host (Claude) displays the markdown | Plain markdown strings |
| mypy + pyright together | Doubles CI time, conflicting strictness | Pick pyright |

---

## Stack Patterns by Variant

**If the tutor later needs to expose live state to other Claude tools mid-session:**
- Add an MCP server (`.mcp.json` in plugin root) as a *second* entrypoint that wraps the same Python core.
- The CLI remains canonical for skill-driven turns; MCP is read-mostly.

**If we add a second host adapter (Codex, OpenClaw, Hermess) in v2:**
- The Python core stays identical.
- New adapter is a new directory under `adapters/` + new `<host>-plugin/` manifest dir at repo root.
- `bin/tutor` is shared. Host adapter only translates lifecycle events.

**If the SRS algorithm is later swapped to FSRS:**
- Replace `core/language_tutor/srs.py` only.
- Add `py-fsrs` dependency.
- `srs_items` schema may need new columns (stability, difficulty) — bump migration version.

---

## Version Compatibility Matrix

| Package | Version | Compatible With | Notes |
|---|---|---|---|
| Python | 3.12, 3.13, 3.14 | All deps below | 3.12 minimum, 3.13 recommended |
| pydantic | 2.13.x | Python 3.9–3.14 | 2.13 added 3.14 support; pydantic-core merged into main repo |
| ruamel.yaml | 0.18.x | Python 3.7+ | Stable round-trip API |
| click | 8.1.x | Python 3.8+ | Long-stable |
| pytest | 8.3.x | Python 3.9+ | Required by syrupy 4.x |
| syrupy | 4.7+ | pytest 7.x+ | Use AmberSnapshotSerializer for FeedbackEnvelope, raw serializer for markdown |
| pyright | 1.1.400+ | Pydantic v2 has first-class pyright support | Use `strict` mode |
| hatchling | 1.27+ | PEP 517 | Default in PyPA guide |

---

## Sources

- **Claude Code Plugins (official)** — [code.claude.com/docs/en/plugins](https://code.claude.com/docs/en/plugins) — verified plugin.json schema, directory layout, marketplace, --plugin-dir testing. HIGH.
- **Claude Code Plugins Reference (official)** — [code.claude.com/docs/en/plugins-reference](https://code.claude.com/docs/en/plugins-reference) — verified components, hooks, monitors, LSP, settings. HIGH.
- **Claude Code Skills (official)** — [code.claude.com/docs/en/skills](https://code.claude.com/docs/en/skills) — verified SKILL.md frontmatter (all fields), `${CLAUDE_SKILL_DIR}` substitution, `!\`...\`` shell injection, `allowed-tools` semantics. HIGH.
- **Claude Code Hooks (official)** — [code.claude.com/docs/en/hooks](https://code.claude.com/docs/en/hooks) — verified SessionStart/SessionEnd/PreToolUse/PostToolUse, hooks.json shape, stdin/exit-code protocol. HIGH.
- **Python Developer Guide** — [devguide.python.org/versions](https://devguide.python.org/versions/) — verified support windows for 3.12 (EOL 2028), 3.13 (EOL 2029), 3.14 (Oct 2025 release). HIGH.
- **Pydantic v2.13 release** — [pydantic.dev/articles/pydantic-v2-12-release](https://pydantic.dev/articles/pydantic-v2-12-release), [pypi.org/project/pydantic](https://pypi.org/project/pydantic/) — verified 2.13.4 latest (May 2026), Python 3.14 support. HIGH.
- **ruamel.yaml** — [pypi.org/project/ruamel.yaml](https://pypi.org/project/ruamel.yaml/), [yaml.dev/doc/ruamel.yaml](https://yaml.dev/doc/ruamel.yaml/detail/) — verified round-trip comment preservation. HIGH.
- **syrupy** — [github.com/syrupy-project/syrupy](https://github.com/syrupy-project/syrupy) — verified pytest plugin, Amber serializer, snapshot lifecycle. HIGH.
- **py-fsrs** — [github.com/open-spaced-repetition/py-fsrs](https://github.com/open-spaced-repetition/py-fsrs) — verified algorithm is FSRS not SM-2; project ships 6.3.1 (Mar 2026). HIGH.
- **anki-sm-2** — [github.com/open-spaced-repetition/anki-sm-2](https://github.com/open-spaced-repetition/anki-sm-2) — verified AGPL-3.0 license, v0.2.0 (Dec 2024). HIGH.
- **Python Build Backends 2026** — [packaging.python.org/en/latest/guides/writing-pyproject-toml](https://packaging.python.org/en/latest/guides/writing-pyproject-toml/), [docs.astral.sh/uv/concepts/build-backend](https://docs.astral.sh/uv/concepts/build-backend/) — verified hatchling as PyPA default, uv_build as new uv default. HIGH.
- **pyright vs mypy 2026** — [github.com/microsoft/pyright/blob/main/docs/mypy-comparison.md](https://github.com/microsoft/pyright/blob/main/docs/mypy-comparison.md), [danilchenko.dev/posts/ty-vs-mypy-vs-pyright](https://www.danilchenko.dev/posts/ty-vs-mypy-vs-pyright/) — verified pyright speed + spec conformance. MEDIUM (training-supplemented). |
- **pytest plugin downloads** — [docs.pytest.org/en/stable/reference/plugin_list.html](https://docs.pytest.org/en/stable/reference/plugin_list.html) — verified pytest-cov, pytest-asyncio, pytest-mock as top plugins. HIGH.

---
*Stack research for: AI language tutor delivered as a Claude Code plugin with portable Python core*
*Researched: 2026-05-19*

## Phase 6 Addendum — Host Tooling (2026-05-22)

Host-specific verification uses official host tools where available:

- **Hermes**: `hermes profile install|info|update|delete` (git-backed profile distribution).
- **OpenClaw**: Node >=22, TypeScript ESM, `pnpm`, ClawHub (`clawhub package publish --dry-run`).
- **Claude**: `claude plugin validate --strict`, `claude --plugin-dir`, `/reload-plugins`.
- **Codex**: local/repo marketplace install + restart (no standalone validator documented).

No new Python runtime dependency is added for the host-capability layer; it builds
on existing Pydantic v2 + Click + stdlib.
