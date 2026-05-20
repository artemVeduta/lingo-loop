# Implementation Plan: language-tutor v1

**Branch**: `001-build-language-tutor` | **Date**: 2026-05-20 | **Spec**: `specs/001-build-language-tutor/spec.md`

**Input**: Feature specification from `specs/001-build-language-tutor/spec.md`

**Note**: This file is the `/speckit-plan` output. Phase 2 task generation is intentionally left to `/speckit-tasks`.

## Summary

Build a local-first Claude Code language-tutor plugin with a synchronous Python 3.12+ core. The tutor exposes setup, vocabulary practice, writing feedback, progress, boot-context, session-end, and doctor commands through one `bin/tutor` CLI; Claude plugin hooks and skills only orchestrate. Human-editable learner profile and preferences live in YAML, while answer events, mistake events, SRS state, reviews, summaries, metrics, migrations, and costs live in SQLite. Pydantic contracts, deterministic renderers, SM-2 scheduling, and golden/contract/integration/semantic tests protect the core behavior.

## Technical Context

**Language/Version**: Python 3.12+ with a synchronous core.

**Primary Dependencies**: Pydantic v2 for contracts and schema export; `ruamel.yaml` for comment-preserving setup/edit YAML; Click for the `bin/tutor` CLI; platformdirs for macOS/Linux paths; stdlib `sqlite3` for local transactional state. Dev dependencies are pytest, syrupy, freezegun, pytest-cov, pyright, ruff, hatchling, uv, and pre-commit.

**Storage**: YAML owns profile and preferences only. SQLite owns transactional and derived state only. Migrations are plain numbered SQL applied by an in-tree runner.

**Testing**: pytest for all tiers; syrupy for deterministic markdown/boot-context snapshots; freezegun for time-dependent SRS tests; pyright strict for types; ruff for lint/format. Semantic evaluator fixtures cover LLM-backed writing quality with explicit SC-004/SC-005 threshold gates separately from deterministic tests.

**Target Platform**: macOS and Linux, running as a Claude Code plugin. Windows and additional hosts are out of scope for v1.

**Project Type**: Local Python package plus Claude Code plugin surface: manifest, hooks, skills, subagent, `bin/tutor`, schemas, migrations, and tests.

**Performance Goals**: Setup to first usable context in under 60 seconds; boot context no more than 8 ordered sections and 6,000 rendered characters; progress view under 5 seconds with one year of daily history; deterministic renderers byte-identical for identical input.

**Constraints**: No cloud sync, telemetry, auth, multi-user, remote storage, async core, ORM, MCP server, speculative host adapters, FSRS, bundled curricula, rich dashboards, games, XP, speaking/listening/reading modes, or extra host manifests in v1. Every state mutation persists immediately through one repository transaction. Definitive high-severity evaluator corrections require `confidence == "high"`. Shell verification in this repository uses the `rtk` command prefix.

**Scale/Scope**: Single local learner, local data paths, setup/vocabulary/writing/progress/session lifecycle/doctor workflows, Slavic-aware evaluator fixtures, and marketplace-ready plugin packaging.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Layered boundaries**: PASS. Affected layers are plugin surface, host adapter, core, DAL, renderer, skills, hooks, agent, packaging, schemas, and tests. Plugin components invoke only the CLI; adapter normalizes host events; core owns pedagogy and validation; DAL owns files and transactions; renderers are pure.
- **Contracts and abstractions**: PASS. Boundary data uses Pydantic models, JSON Schema mirrors, documented CLI JSON, SQL migrations, and a narrow Claude adapter Protocol. No catch-all dictionaries or DAL details cross module boundaries.
- **Deterministic tests**: PASS. Plan requires unit tests for SM-2, severity mappings, schema validation, path rules, and YAML validation; golden tests for boot context and feedback markdown; contract tests for CLI/plugin/adapter JSON; integration tests for setup, vocab, writing, progress, lifecycle, and migration flows; semantic fixtures with threshold gates for evaluator quality.
- **Local-first data ownership**: PASS. YAML is limited to human-editable profile/preferences; SQLite holds answer events, mistake events, SRS rows, reviews, summaries, metrics, costs, and migrations. Paths use platformdirs/XDG conventions.
- **Scope discipline**: PASS. v1 ships Claude Code only with setup, vocab, writing, progress, session hooks, doctor, local storage, and packaging. Deferred hosts, modalities, FSRS, cloud, dashboards, and gamification remain excluded.
- **DRY and composition**: PASS. Pydantic schemas, controlled tags, severity maps, path rules, prompt rubrics, migrations, and renderer mappings stay single-source. Behavior is composed through injected collaborators and repositories, not inheritance or globals.

## Project Structure

### Documentation (this feature)

```text
specs/001-build-language-tutor/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── cli-json.md
│   ├── evaluator.md
│   └── plugin-surface.md
└── tasks.md              # Created later by /speckit-tasks
```

### Source Code (repository root)

```text
.claude-plugin/
└── plugin.json

hooks/
├── hooks.json
├── session-start.sh
├── session-end.sh
└── README.md

skills/
├── tutor-setup/
│   ├── SKILL.md
│   └── scripts/
├── tutor-vocab/
│   ├── SKILL.md
│   └── scripts/
├── tutor-writing/
│   ├── SKILL.md
│   └── scripts/
└── tutor-progress/
    ├── SKILL.md
    └── scripts/

agents/
└── tutor-judge.md

bin/
└── tutor

src/
└── language_tutor/
    ├── __init__.py
    ├── cli.py
    ├── schemas.py
    ├── setup.py
    ├── lifecycle.py
    ├── boot_context.py
    ├── feedback.py
    ├── vocab.py
    ├── srs.py
    ├── session.py
    ├── evaluators.py
    ├── writing.py
    ├── progress.py
    ├── health.py
    ├── errors.py
    ├── adapters/
    │   ├── __init__.py
    │   ├── base.py
    │   └── claude.py
    └── dal/
        ├── __init__.py
        ├── paths.py
        ├── yaml_store.py
        ├── sqlite_store.py
        ├── migrations.py
        └── repositories.py

migrations/
└── 001_initial.sql

schemas/
├── boot_context.schema.json
├── feedback_envelope.schema.json
├── session_analysis.schema.json
└── answer_event.schema.json

data/defaults/
├── profile.yaml
└── preferences.yaml

tests/
├── unit/
├── golden/
├── contract/
├── adapter_contract/
├── integration/
├── migration/
└── fixtures/

pyproject.toml
pyrightconfig.json
README.md
LICENSE
```

**Structure Decision**: Use one installable package under `src/language_tutor/` and enforce layer boundaries through modules, contracts, repositories, and tests. Separate packages for core/DAL/adapters are rejected for v1 because there is only one host adapter and one local runtime. Rendering and session analysis are Python modules/CLI commands, not separate LLM-invoked skills.

## Phase 0: Research

**Output**: `specs/001-build-language-tutor/research.md`

All technical-context unknowns are resolved:

- Runtime: Python 3.12+ synchronous package.
- CLI boundary: one Click-powered `bin/tutor` with JSON input/output.
- Contracts: Pydantic v2 as source of truth plus JSON Schema mirrors.
- Persistence: `ruamel.yaml` for editable config; stdlib `sqlite3` for transactional state.
- Paths: platformdirs for macOS/Linux.
- SRS: in-tree SM-2 with explicit quality mapping.
- Evaluation: `tutor-judge` only for writing; structured validation, retry, fallback, and semantic fixtures with SC-004/SC-005 threshold checks.
- Rendering: deterministic Python markdown renderer with emoji and ASCII fallback.
- Distribution: Claude plugin manifest, hooks, skills, agent, doctor command, and install checks.

## Phase 1: Design And Contracts

**Output**:

- `specs/001-build-language-tutor/data-model.md`
- `specs/001-build-language-tutor/contracts/cli-json.md`
- `specs/001-build-language-tutor/contracts/evaluator.md`
- `specs/001-build-language-tutor/contracts/plugin-surface.md`
- `specs/001-build-language-tutor/quickstart.md`
- `AGENTS.md` Speckit plan reference

Design decisions:

- Data model separates YAML entities (`LearnerProfile`, `LearnerPreferences`) from SQLite entities (`LifecycleEvent`, `VocabularyItem`, `VocabularyReview`, `AnswerEvent`, `MistakeEvent`, `SessionSummary`, `SessionAnalysis`, `SkillMetric`, `CostEvent`, `MigrationRecord`).
- Contract entities are `BootContext`, `FeedbackEnvelope`, and frozen `ErrorTag` vocabulary.
- CLI contract is the stable boundary for hooks, skills, tests, and contributors.
- Evaluator contract is stateless and validates/downgrades before persistence or rendering.
- Plugin surface contract forbids persistence, SM-2 math, tag duplication, and renderer logic inside `SKILL.md`.

## Post-Design Constitution Check

- **Layered boundaries**: PASS. Phase 1 contracts keep plugin, adapter, core, DAL, renderer, and agent responsibilities separate.
- **Contracts and abstractions**: PASS. Data model and contracts define explicit Pydantic/JSON/SQL surfaces before tasks or implementation.
- **Deterministic tests**: PASS. Quickstart and contracts identify required unit, golden, contract, adapter, integration, migration, and semantic gates.
- **Local-first data ownership**: PASS. Ownership rules are documented in data model and CLI contract.
- **Scope discipline**: PASS. Design excludes v2 hosts/modalities and anti-features named in the spec.
- **DRY and composition**: PASS. Shared schemas/tags/maps remain centralized; behavior is assembled through CLI/core/DAL collaborators.

## Complexity Tracking

No constitution violations. No complexity exceptions required.
