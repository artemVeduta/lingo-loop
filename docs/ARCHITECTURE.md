# Architecture

This is the module-level expansion of the high-level diagram in the README. For maintainer-facing internals see `docs/internal/ARCHITECTURE.md`.

## Overview

```
┌──────────────┐       ┌────────────────┐       ┌─────────────────────────┐
│  AI Host     │──────▶│  Tutor skill   │──────▶│  tutor CLI              │
│  (Claude/    │       │  (markdown +   │       │  (Python, src/          │
│  Codex/      │       │  prompts under │       │   language_tutor/)      │
│  Hermes/     │       │  skills/...)   │       │                         │
│  OpenClaw)   │       └────────────────┘       └─────────────────────────┘
└──────────────┘                                          │
                                                          │ reads / writes
                                ┌─────────────────────────┼─────────────────────────┐
                                ▼                         ▼                         ▼
                         ┌──────────────┐         ┌──────────────┐         ┌──────────────┐
                         │  profile +   │         │  learning    │         │  data/       │
                         │  preferences │         │  history     │         │  defaults/   │
                         │  YAML        │         │  SQLite      │         │  (read-only) │
                         │  ~/.config/  │         │  ~/.local/   │         │  packaged    │
                         │  language-   │         │  state/      │         │  fixtures    │
                         │  tutor/      │         │  language-   │         │              │
                         │              │         │  tutor/      │         │              │
                         └──────────────┘         └──────────────┘         └──────────────┘

    All state is local. The only network traffic is the host's own LLM API call,
    using the host's own credentials. The tutor CLI opens no sockets.
```

## Layers

### 1. Host integration (`.claude-plugin/`, `.codex-plugin/`, `hermes-profile/`, `openclaw-plugin/`)
Thin packaging glue. Each host gets a manifest declaring metadata (name, version, MIT license) and pointing at the shared skill markdown. No business logic lives here.

### 2. Skills (`skills/tutor-{lesson,reading,vocab,writing,progress,setup}/`)
Markdown prompt definitions that the host loads. Each skill knows how to invoke the `tutor` CLI with the right subcommand and how to render the JSON response back to the learner.

### 3. CLI entry point (`src/language_tutor/cli.py`)
Single CLI exposed as `tutor` (entry point declared in `pyproject.toml`). Subcommands include `doctor`, `setup write`, `session-start`, and the modality commands (reading, lesson, vocab, writing, progress). All commands accept `--json` for structured output that skills can parse.

### 4. Core domain (`src/language_tutor/`)
- **`boot_context.py`** — builds the per-session boot block (profile, due reviews, weak patterns, latest recap, local status) returned by `tutor session-start`.
- **`setup.py`** — reads/writes profile + preferences YAML through the DAL.
- **`schemas.py`** — pydantic models that define every wire/disk shape: `LearnerProfile`, `LearnerPreferences`, `BootContext`, `FeedbackEnvelope`, etc.
- **`progress.py`, `vocab.py`, `feedback.py`, `lessons.py`, `reading.py`, `writing.py`** — modality-specific logic.
- **`srs.py`** — spaced-repetition scheduling.
- **`evaluators.py`, `text_modalities.py`** — input validation and modality routing.
- **`health.py`** — backs `tutor doctor`.

### 5. Data access layer (`src/language_tutor/dal/`)
- **`paths.py`** — resolves config/data/state directories via `platformdirs` (`APP_NAME = "language-tutor"`). Honors `LANGUAGE_TUTOR_HOME` for overrides.
- **`yaml_store.py`** — load/dump pydantic models to YAML (via `ruamel.yaml`).
- **`sqlite_store.py`** — opens the SQLite connection and provides a transaction context manager.
- **`migrations.py`** — applies forward-only SQL migrations from `migrations/` at the repo root.
- **`repositories.py`** — `TutorRepository`: typed read/write surface over SQLite for sessions, vocab, mistakes, SRS, summaries.
- **`defaults/`** — read-only seed data packaged with the wheel.

### 6. Adapters (`src/language_tutor/adapters/`)
Host-specific output shapers (e.g. trimming/formatting for hosts with stricter token budgets). Pure functions; no I/O.

## Boot sequence

1. Learner sends the first tutor-related message to the host.
2. Host loads the matching skill markdown and runs `tutor session-start --json`.
3. CLI resolves paths (`platformdirs` or `LANGUAGE_TUTOR_HOME`), loads profile + preferences YAML, opens SQLite, applies pending migrations.
4. `build_boot_context()` assembles six sections from the repository (due review count, weak tag signals, latest recap).
5. CLI prints `BootContext` as JSON; skill renders it into the host's message stream.

## Data shapes (canonical)

All wire/disk shapes are pydantic models in `schemas.py`. The two user-editable files:

- `LearnerProfile` — see [configuration](configuration.md#profileyaml).
- `LearnerPreferences` — see [configuration](configuration.md#preferencesyaml).

The SQLite database is implementation detail; tables evolve via `migrations/` and should not be hand-edited.

## Test layout

`tests/` mirrors `src/language_tutor/`. Coverage gate is configured in `pyproject.toml` (`--cov-fail-under`). See `CONTRIBUTING.md` for running tests.

## What is *not* in this picture

- No background daemon. The CLI is a request/response process; the host owns the session loop.
- No remote sync. Multi-device usage means manually copying `~/.config/language-tutor/` and `~/.local/state/language-tutor/`.
- No telemetry. See [privacy](privacy.md).
