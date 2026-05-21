# Implementation Plan: Richer Feedback & Progress

**Branch**: `004-richer-feedback-progress` | **Date**: 2026-05-21 | **Spec**: `specs/004-richer-feedback-progress/spec.md`

**Input**: Feature specification from `specs/004-richer-feedback-progress/spec.md`

**Note**: This file is the `/speckit-plan` output. Phase 2 task generation is intentionally deferred to `/speckit-tasks`.

## Summary

Extend the existing local progress surface into a deterministic text-only report with per-tag mastery, recent-session recap trends, ASCII sparklines, and markdown/JSON exports. The implementation keeps aggregation in the Python core, persistence reads in narrow SQLite repository methods, rendering in markdown/text renderers, and schemas as the single source of truth. No host adapter, GUI, web view, dashboard, charting library, cloud sync, new exercise modality, or scheduling algorithm is introduced.

## Technical Context

**Language/Version**: Python 3.12+ with the existing synchronous core.

**Primary Dependencies**: Existing runtime dependencies only: Click for `bin/tutor`, Pydantic v2 for contracts and schema export, ruamel.yaml for preferences/profile, platformdirs for local paths, and stdlib `sqlite3`/`json`/`datetime`/`math`/`textwrap` for local aggregation and deterministic text rendering. Dev tooling remains pytest, syrupy, freezegun, pytest-cov, pyright, ruff, hatchling, uv, and pre-commit.

**Storage**: SQLite remains the canonical transactional/derived store for answer events, vocabulary reviews, mistake events, session summaries, costs, and vocabulary items. YAML remains human-editable profile/preferences only. Progress reports are derived artifacts emitted on demand, not persisted as a new source of truth. A small migration for read-performance indexes is planned; no data-shape migration is required.

**Testing**: pytest for unit, contract, integration, migration, and performance tests; syrupy for deterministic markdown/ASCII golden tests; freezegun or injected clocks for generated-at, recency, streak, and trend fixtures; pyright and ruff for type/lint gates.

**Target Platform**: macOS and Linux local plugin runtime. Host-independent CLI behavior only; no Claude-specific or other host adapter changes.

**Project Type**: Local Python package plus Claude Code plugin surface. This feature changes Python core/DAL/renderers/contracts/schema mirrors and the existing `tutor-progress` user surface only if invocation wording must describe new outputs.

**Performance Goals**: Default progress view and export complete in under 5 seconds on a fixture representing one year of daily completed sessions with dense reviews and mistakes. Per-tag mastery uses the most recent 30 completed valid sessions; recaps use a requested last-N valid completed-session window from 1 to 30, default 10. Rendering targets terminal-printable markdown for a 100-column terminal with deterministic wrapping for long tags, hints, and learner-safe summaries.

**Constraints**: Output stays text/markdown only. ASCII trend characters are exactly `.:-=+*#%@`, one character per valid session plus min/max labels. Trend direction uses earlier-half vs later-half averages, ignores the middle value for odd windows, treats relative changes under 10% as steady, treats both-zero averages as steady, and treats a zero-to-nonzero average as beyond the 10% threshold. Duplicate session records count each `session_id` once, preferring the latest valid analyzed record and reporting skipped duplicates. Exports exclude raw learner answers, full feedback prose, complete event logs, host metadata, GUI/web/dashboard surfaces, and graphical charts.

**Scale/Scope**: Single local learner, one progress request at a time, local one-year daily history fixture, active mastery window of 30 completed valid sessions, recap window of 1-30 completed valid sessions, and the existing normalized tag vocabulary shared across mistakes, reviews, weak patterns, and progress targeting.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Layered boundaries**: PASS. Affected layers are progress aggregation, narrow repository reads, Pydantic progress/export schemas, JSON schema mirrors, deterministic markdown/text renderers, `tutor progress` CLI JSON, optional `render progress-report`, migration indexes, tests, and the existing `tutor-progress` skill surface only if invocation text changes. Host adapters remain out of scope. Cross-layer calls stay CLI -> core -> repository and CLI/core -> renderer.
- **Contracts and abstractions**: PASS. New data crosses boundaries through Pydantic models, JSON schema mirrors, documented CLI JSON, renderer contracts, and narrow repository read methods. No catch-all dictionaries or concrete DAL internals leak into skills or renderers.
- **Deterministic tests**: PASS. Required coverage includes unit tests for mastery scoring, stale evidence, tie ordering, trend labels, sparkline buckets, duplicate/invalid skip counts, privacy filtering, and no-data behavior; golden tests for progress markdown and ASCII trends; contract tests for JSON export, markdown export, CLI request validation, and schema export; integration tests for empty, partial, dense one-year, and older-state histories; migration tests for read indexes; performance verification for one year of daily history.
- **Skill creation gate**: PASS. No new skill is created. If `skills/tutor-progress/SKILL.md` is edited, implementation tasks must use a subagent for the skill family, read the local `writing-skills` helper, apply the active spec's references, record RED/GREEN/REFACTOR pressure evidence, and require activation/description trigger review plus main-agent review of changed files.
- **Local-first data ownership**: PASS. SQLite owns sessions, reviews, mistakes, costs, due counts, and derived aggregation inputs. YAML remains profile/preferences only. Reports are generated from local state and emitted to stdout; no cloud, telemetry, remote state, or host-owned learner data is introduced.
- **Scope discipline**: PASS. Work is limited to roadmap Phase 4 richer feedback and progress. Graphical dashboards, GUI/web views, chart libraries, raw event exports, host adapter work, new modalities, new scheduling algorithms, gamification, cloud sync, multi-user behavior, and unrelated evaluator changes are excluded.
- **DRY and composition**: PASS. Tag normalization, severity weights, trend direction, sparkline buckets, skip reasons, report guardrails, and markdown/JSON export facts are single-source helpers or schemas composed by progress aggregation and renderers. No inheritance hierarchy, service locator, or global mutable state is introduced.

## Project Structure

### Documentation (this feature)

```text
specs/004-richer-feedback-progress/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── progress-cli.md
│   ├── progress-json-report.md
│   └── progress-markdown-report.md
└── tasks.md              # Generated by /speckit-tasks
```

### Source Code (repository root)

```text
skills/
└── tutor-progress/
    ├── SKILL.md                    # edit only if invocation text must change
    └── scripts/
        └── run.py                  # if present/needed by existing pattern

src/language_tutor/
├── cli.py                          # progress request parsing and render command wiring
├── progress.py                     # aggregation, scoring, recap, skipped-data accounting
├── progress_rendering.py           # planned markdown/table/sparkline renderer
├── schemas.py                      # progress request/report/export contracts
└── dal/
    └── repositories.py             # narrow progress read methods

migrations/
├── 001_initial.sql
├── 002_vocab_depth.sql
└── 003_progress_indexes.sql        # planned read-performance indexes

schemas/
├── progress_report.schema.json     # planned
├── progress_request.schema.json    # planned if exported separately
└── progress_markdown_export.schema.json  # planned if exported separately

tests/
├── adapter_contract/
│   ├── test_cli_json_contract.py
│   └── test_progress_cli.py
├── golden/
│   ├── test_progress_rendering.py
│   └── snapshots/
├── integration/
│   └── test_progress_flow.py
├── migration/
│   └── test_migrations.py
├── performance/
│   └── test_progress_performance.py
└── unit/
    ├── test_progress.py
    ├── test_repositories.py
    └── test_schemas.py
```

**Structure Decision**: Extend the existing single Python package. Keep progress scoring and recap aggregation in `progress.py`, deterministic markdown/table rendering in a small renderer module, and raw storage access behind `TutorRepository` methods. Use Pydantic schemas as the JSON report source of truth and render markdown from the validated report model. Add read indexes only where they support the one-year-history performance gate. A new analytics package, charting dependency, persisted report table, host adapter, or alternate scheduler is rejected because Phase 4 is a local text/report surface over existing state.

## Phase 0: Research

**Output**: `specs/004-richer-feedback-progress/research.md`

All technical-context unknowns are resolved:

- Keep existing dependencies. Python/Pydantic/stdlib are sufficient for scoring, trend math, schema export, and ASCII rendering; no chart, table, markdown, or analytics dependency is needed.
- Use existing SQLite state as the source of truth: `session_summaries`, `answer_events`, `mistake_events`, `vocabulary_reviews`, `vocabulary_items`, and `cost_events`. Add only read indexes for session/window queries.
- Define `ProgressReportRequest` with `window_size` 1-30 and optional `generated_at`; CLI defaults `generated_at` from current UTC and tests inject/freeze time.
- Expand `ProgressReport` into a full report contract with generated-at, report window, progress snapshot, per-tag mastery list, recent recap, due-review summary, skipped-data notices, and scope guardrails.
- Compute mastery from aggregated safe evidence only: correctness/review outcomes 45%, mistake severity 30%, recency 15%, and evidence confidence 10%. Component scores are normalized to 0-100 before weighting; correctness/review maps correct or quality 4-5 to 100, partial or quality 3 to 60, and negative outcomes or quality 0-2 to 0; severity is `100 - average_penalty` with `none=0`, `low=25`, `medium=60`, `high=100`; recency decays linearly across the 30-session mastery window and is 0 for stale tags; confidence averages explicit confidence values with sparse evidence capped by `min(1, evidence_count / 5)`. No raw answers, span text, or full feedback prose appear in the report.
- Reuse `normalize_tag` and weak-tag semantics from Phase 3 so targeting and progress identify the same tags.
- Deduplicate session summaries by `session_id`, preferring the latest valid analyzed row; skipped duplicate, invalid, interrupted, missing-analysis, and stale counts are reported through `SkippedDataNotice`. Current SQLite storage has `session_summaries.session_id UNIQUE` and `INSERT OR REPLACE`, so duplicate-summary skip counts are normally zero unless a legacy/import path or pure canonicalizer input exposes duplicates.
- Trend labels compare the first `floor(n/2)` and last `floor(n/2)` averages within the selected valid session window, ignoring the middle value only for direction when `n` is odd. Higher-is-better and lower-is-better metrics use explicit polarity; under 10% relative change is steady, both-zero averages are steady, and zero-to-nonzero averages use the polarity-adjusted delta direction.
- ASCII sparklines scale each metric independently across the selected valid sessions into `.:-=+*#%@`; constant series use the middle bucket and still show min/max labels.
- JSON export is the canonical machine contract. Markdown export is rendered from the same validated `ProgressReport`, which keeps markdown/JSON core facts equivalent.

## Phase 1: Design And Contracts

**Output**:

- `specs/004-richer-feedback-progress/data-model.md`
- `specs/004-richer-feedback-progress/contracts/progress-cli.md`
- `specs/004-richer-feedback-progress/contracts/progress-json-report.md`
- `specs/004-richer-feedback-progress/contracts/progress-markdown-report.md`
- `specs/004-richer-feedback-progress/quickstart.md`
- `AGENTS.md` Speckit plan reference

Design decisions:

- `ProgressReportRequest` is a Pydantic request model accepted by `tutor progress --json [payload]`. Omitting the payload preserves the current no-argument progress behavior while returning the richer report shape.
- `ProgressReport` replaces the narrow current report as the canonical JSON export. It contains required `generated_at`, report window, snapshot, tag mastery rows, recent recap, due-review summary, skipped-data notices, and guardrails.
- `TagMastery` rows are derived, not stored. They include normalized tag, score, band, evidence count, last-seen age, stale flag, trend direction, next-practice hint, and signal breakdown. Sorting is lowest score first, worsening trend first, most recent evidence first, then normalized tag.
- `RecentSessionRecap` is derived from the selected last-N completed valid sessions. It includes actual count, date range, practice totals, review totals, severity totals, weak-tag changes, learner-safe latest summary, trend metrics, and skipped-data counts.
- `TextTrend` is a validated model containing metric name, polarity, values count, direction, sparkline, min label, and max label. The renderer prints only ASCII trend characters and plain labels.
- `SkippedDataNotice` centralizes skip reasons and counts. Duplicate sessions, invalid/incomplete sessions, missing analysis, stale tag evidence, and optional unavailable fields are reported without leaking raw records.
- `ProgressMarkdownExport` is a renderer output model containing generated-at, report window, content type, and markdown string. It is rendered from `ProgressReport`; it does not own aggregation logic.
- Repository additions are narrow read methods: valid recent session summaries, progress evidence for session IDs, due-review summary, per-tag aggregate evidence counts, month cost, and answer dates. They return typed rows or Pydantic input models without scoring. Due-review summary must distinguish reviewable due cards from new-card availability if existing `due_count()` semantics include new cards.
- Migration `003_progress_indexes.sql` adds indexes for bounded progress reads, likely on session summary creation/session IDs, mistake session/time, vocabulary review session/time, and vocabulary item tags/state as implementation proves useful.
- A `skills/tutor-progress/SKILL.md` update is planned because markdown/JSON export options change the learner-facing progress invocation surface. The constitution skill gate applies: subagent baseline, local writing-skills helper, required external skill-authoring references, pressure verification, activation/description trigger review, and main-agent review of changed files.

## Post-Design Constitution Check

- **Layered boundaries**: PASS. Design keeps host adapters untouched and separates CLI request parsing, core aggregation, repository reads, schema contracts, and markdown rendering.
- **Contracts and abstractions**: PASS. Data model and contract docs define Pydantic/JSON/markdown surfaces before implementation tasks. Repository additions are narrow data reads and do not own scoring or rendering.
- **Deterministic tests**: PASS. Quickstart and contracts identify unit, golden, contract, integration, migration, and performance gates for changed behavior.
- **Skill creation gate**: PASS. No skill creation is planned. Any `SKILL.md` edit is explicitly gated by subagent, local writing-skills evidence, activation/description trigger review, and main-agent review of changed files.
- **Local-first data ownership**: PASS. Reports are derived from local SQLite state and emitted on demand. YAML remains human-editable preferences/profile only.
- **Scope discipline**: PASS. Design excludes dashboards, GUI/web views, chart libraries, new hosts, new modalities, new scheduler behavior, cloud sync, gamification, and raw event exports.
- **DRY and composition**: PASS. Shared tag normalization, scoring weights, trend polarity, sparkline buckets, skip reasons, and export guardrails prevent duplicated rules and remain composed through explicit collaborators.

## Verification Gates

```bash
rtk uv run pytest tests/unit/test_progress.py tests/unit/test_schemas.py tests/unit/test_repositories.py
rtk uv run pytest tests/golden/test_progress_rendering.py
rtk uv run pytest tests/adapter_contract/test_progress_cli.py tests/adapter_contract/test_cli_json_contract.py
rtk uv run pytest tests/integration/test_progress_flow.py
rtk uv run pytest tests/migration/test_migrations.py
rtk uv run pytest tests/performance/test_progress_performance.py
rtk uv run pyright
rtk uv run ruff check .
```

The performance gate MUST include a fixture representing one year of daily completed sessions and verify default progress generation plus JSON/markdown export under 5 seconds. Golden and contract gates MUST verify byte-stable output when `generated_at` is injected.

## Complexity Tracking

No constitution violations. No complexity exceptions required.
