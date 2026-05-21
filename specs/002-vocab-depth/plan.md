# Implementation Plan: Vocab Depth

**Branch**: `002-vocab-depth` | **Date**: 2026-05-21 | **Spec**: `specs/002-vocab-depth/spec.md`

**Input**: Feature specification from `specs/002-vocab-depth/spec.md`

**Note**: This file is the `/speckit-plan` output. Phase 2 task generation is intentionally left to `/speckit-tasks`.

## Summary

Deepen the existing local vocabulary SRS loop with manual card creation, idempotent local JSON seed imports, tag-filtered drills, cloze cards, and per-card review history. The implementation extends the current `VocabularyItem`/`VocabularyReview` contracts, `tutor vocab` CLI group, SQLite repository, deterministic vocabulary renderers, JSON schema mirrors, and `tutor-vocab` skill instructions without changing host adapters, writing feedback, progress dashboards, cloud behavior, or the SM-2 scheduling algorithm.

## Technical Context

**Language/Version**: Python 3.12+ with the existing synchronous core.

**Primary Dependencies**: Existing runtime dependencies only: Click for `bin/tutor`, Pydantic v2 for contracts and schema export, platformdirs for local paths, and stdlib `json` plus `sqlite3` for import parsing and transactional state. Dev tooling remains pytest, syrupy, freezegun, pytest-cov, pyright, ruff, hatchling, uv, and pre-commit.

**Storage**: SQLite remains the canonical transactional learning state. The seed JSON file is an import source only and is not canonical after import. Existing profile/preferences YAML ownership is unchanged.

**Testing**: pytest for unit, contract, integration, and migration tests; syrupy for deterministic vocabulary prompt/import/history/cloze rendering snapshots; freezegun for due-first and review-history time fixtures; pyright and ruff for type/lint gates.

**Target Platform**: macOS and Linux local Claude Code plugin runtime. Host-independent CLI behavior only; no new host adapter work.

**Project Type**: Local Python package plus Claude Code plugin surface. This feature changes Python core/DAL/renderers/contracts and one existing skill surface.

**Performance Goals**: Manual add to drillable card in under 2 minutes; review history response under 2 seconds for 500 attempts; import summary counts accurate for deterministic seed fixtures; tag-filtered queue preserves due-first ordering for 100% of selection fixtures.

**Constraints**: No host dependency, no cloud sync, no dashboards, no bundled curriculum, no new scheduling algorithm, no ORM, no async storage, no new modality, and no speculative adapter abstractions. Each seed entry uses its own validation/update transaction.

**Scale/Scope**: Single local learner, locally managed decks, local seed files, low-thousands vocabulary cards, one hidden answer per cloze card, and complete review history for each card.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Layered boundaries**: PASS. Affected layers are `skills/tutor-vocab`, `src/language_tutor/cli.py`, vocabulary core, deterministic feedback/rendering helpers, Pydantic schemas, DAL repositories, SQL migrations, JSON schema mirrors, and tests. Host adapters remain out of scope.
- **Contracts and abstractions**: PASS. New data crosses boundaries through Pydantic models, JSON schema mirrors, documented CLI JSON, and SQL migration shape. Repositories expose narrow methods for add/import/filter/history; skills call only `bin/tutor`.
- **Deterministic tests**: PASS. Required coverage includes unit tests for card validation, duplicate identity, metadata merge, tag normalization, cloze validation, and history ordering; golden tests for prompts, import summaries, cloze feedback, and history text; contract tests for CLI JSON and seed JSON; integration tests for manual add, idempotent import, tag drills, cloze review, and history; migration tests for existing rows.
- **Local-first data ownership**: PASS. Seed JSON is a human-editable import input only. SQLite owns cards, dedupe keys, review attempts, scheduling state, import outcomes, and history. Existing profile/preferences YAML ownership is unchanged.
- **Scope discipline**: PASS. Work is limited to roadmap Phase 2 vocabulary depth. Writing feedback, progress dashboards, host adapters, audio, cloud sync, gamification, bundled curricula, and scheduler algorithm changes are excluded.
- **DRY and composition**: PASS. Duplicate identity, tag normalization, card validation, and cloze rendering are single-source helpers used by CLI, repositories, renderers, and tests. Behavior is composed through explicit CLI/core/repository collaborators, not inheritance or globals.

## Project Structure

### Documentation (this feature)

```text
specs/002-vocab-depth/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── cli-json.md
│   ├── seed-list-json.md
│   └── vocabulary-card.md
└── tasks.md              # Created later by /speckit-tasks
```

### Source Code (repository root)

```text
skills/
└── tutor-vocab/
    ├── SKILL.md
    └── scripts/
        └── run.py

src/language_tutor/
├── cli.py
├── feedback.py
├── schemas.py
├── srs.py
├── vocab.py
└── dal/
    ├── migrations.py
    ├── repositories.py
    └── sqlite_store.py

migrations/
├── 001_initial.sql
└── 002_vocab_depth.sql

schemas/
├── answer_event.schema.json
├── boot_context.schema.json
├── feedback_envelope.schema.json
├── session_analysis.schema.json
├── vocabulary_card_definition.schema.json
├── vocabulary_import_summary.schema.json
├── vocabulary_review_history.schema.json
└── vocabulary_session_plan.schema.json

tests/
├── adapter_contract/
│   └── test_vocab_cli.py
├── fixtures/
│   └── vocabulary/
├── golden/
│   └── test_vocab_feedback.py
├── integration/
│   └── test_vocabulary_flow.py
├── migration/
│   └── test_migrations.py
└── unit/
    ├── test_repositories.py
    ├── test_schemas.py
    └── test_srs.py
```

**Structure Decision**: Extend the existing single package and `tutor vocab` CLI group. A separate deck package, new tag repository package, new host adapter, or new scheduling package is rejected because Phase 2 adds vocabulary depth inside the existing local SRS boundary.

## Phase 0: Research

**Output**: `specs/002-vocab-depth/research.md`

All technical-context unknowns are resolved:

- Runtime/dependencies: keep Python 3.12+ and existing dependencies; use stdlib `json` parsing for seed lists.
- Duplicate identity: stable identity is card type plus normalized target/hidden answer plus normalized prompt/context; metadata is excluded.
- Seed import: validate each JSON object into a Pydantic card definition, then apply one entry-level SQLite transaction.
- Tag filtering: keep tags on the card contract and normalize through one helper; do not add a separate tag index table until scale requires it.
- Cloze cards: represent cloze as a card type using exactly one `{{answer}}` marker in `prompt` and the hidden answer as target content.
- Review history: derive from existing `vocabulary_reviews` and `answer_events`; no second audit log is needed.

## Phase 1: Design And Contracts

**Output**:

- `specs/002-vocab-depth/data-model.md`
- `specs/002-vocab-depth/contracts/cli-json.md`
- `specs/002-vocab-depth/contracts/seed-list-json.md`
- `specs/002-vocab-depth/contracts/vocabulary-card.md`
- `specs/002-vocab-depth/quickstart.md`
- `AGENTS.md` Speckit plan reference

Design decisions:

- `VocabularyCardDefinition` is the shared input contract for manual add and seed import.
- `VocabularyItem` remains the canonical stored card model and gains explicit card type, additive metadata, and Phase 2 duplicate identity support while preserving existing review state.
- Seed import result models report created, updated, skipped, and invalid entries with repair-oriented details.
- `VocabularyDrillRequest` adds optional inclusive tag filters to `vocab start`; empty requests preserve current unfiltered behavior.
- `VocabularyReviewHistory` reads the chronological `VocabularyReview` trail and current due state for one card.
- Cloze review uses the same answer comparison, `FeedbackEnvelope`, SM-2 scheduling, and review recording path as standard vocabulary review.

## Post-Design Constitution Check

- **Layered boundaries**: PASS. Contracts keep skill orchestration, CLI parsing, core validation/selection, DAL persistence, and rendering separate.
- **Contracts and abstractions**: PASS. Data model and contract docs define Pydantic/JSON/SQL surfaces before implementation tasks.
- **Deterministic tests**: PASS. Quickstart and contracts identify unit, golden, contract, integration, and migration gates for changed behavior.
- **Local-first data ownership**: PASS. Seed JSON remains input only; SQLite remains canonical for cards, review history, and scheduling.
- **Scope discipline**: PASS. Design excludes host work, writing/progress changes, cloud features, dashboards, and scheduler replacement.
- **DRY and composition**: PASS. Shared normalization, duplicate identity, validation, and renderer helpers are planned as single-source collaborators.

## Verification Gates

```bash
rtk pytest tests/unit/test_schemas.py tests/unit/test_repositories.py tests/unit/test_srs.py
rtk pytest tests/golden/test_vocab_feedback.py
rtk pytest tests/adapter_contract/test_vocab_cli.py
rtk pytest tests/integration/test_vocabulary_flow.py
rtk pytest tests/migration/test_migrations.py
rtk pyright
rtk ruff check .
```

The adapter-contract and integration gates MUST keep existing unfiltered
vocabulary start/answer regression cases in scope; do not narrow these commands
to Phase 2-only tests.

## Complexity Tracking

No constitution violations. No complexity exceptions required.
