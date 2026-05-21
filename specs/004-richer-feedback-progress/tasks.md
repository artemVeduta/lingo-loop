# Tasks: Richer Feedback & Progress

**Input**: Design documents from `/specs/004-richer-feedback-progress/`

**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, `contracts/`,
`quickstart.md`, `.specify/memory/constitution.md`, `docs/ROADMAP.md`, and
`specs/003-smarter-engine/plan.md`

**Tests**: Required by the feature specification and constitution. Write failing tests
before implementation for schemas, repository reads, aggregation, rendering, CLI JSON,
migrations, privacy, and performance.

**Organization**: Tasks are grouped by independently testable user story. The
`tutor-progress` skill update is included in US3 because new markdown/JSON export
invocation text changes the learner-facing progress surface; skill work must use a
subagent and the local writing-skills helper.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel with other marked tasks in the same phase because it
  touches different files and does not depend on incomplete work
- **[Story]**: User story label for story phases only
- **Paths**: Every task names the exact file path it changes or verifies

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Create shared test/evidence scaffolding without implementing behavior.

- [ ] T001 Create Phase 4 fixture builder helpers for no-data, one-session, tied-tag, stale-tag, skipped-session, long-text, and one-year histories in `tests/fixtures/progress/phase4_scenarios.py`
- [ ] T002 [P] Create renderer module skeleton with public markdown export function placeholders in `src/language_tutor/progress_rendering.py`
- [ ] T003 [P] Document the affected `skills/tutor-progress/SKILL.md` inventory, local writing-skills helper path, and required external skill-authoring references in `specs/004-richer-feedback-progress/skill-pressure-evidence.md`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Define shared contracts, schema mirrors, repository read boundaries, and
read-performance migration before user-story behavior.

**Critical**: No user story implementation starts until this phase is complete.

- [ ] T004 [P] Add failing schema tests for `ProgressReportRequest`, `ReportWindow`, `ProgressSnapshot`, `TagMastery`, `TextTrend`, `SkippedDataNotice`, `DueReviewSummary`, `ProgressReport`, and `ProgressMarkdownExport` in `tests/unit/test_schemas.py`
- [ ] T005 [P] Add failing JSON schema export assertions for progress schema mirror filenames in `tests/adapter_contract/test_cli_json_contract.py`
- [ ] T006 [P] Add failing migration order and progress-index assertions for `003_progress_indexes.sql` in `tests/migration/test_migrations.py`
- [ ] T007 [P] Add failing repository boundary tests for progress session windows, due-review summary reads, cost fallback reads, optional summary/tag-evidence fallback reads, and aggregate-only evidence reads in `tests/unit/test_repositories.py`
- [ ] T008 Implement Phase 4 Pydantic models and validators in `src/language_tutor/schemas.py`
- [ ] T009 Update `export_json_schemas()` to include Phase 4 progress schema mirrors in `src/language_tutor/schemas.py`
- [ ] T010 Add generated schema mirrors for progress request, progress report, and markdown export in `schemas/progress_request.schema.json`, `schemas/progress_report.schema.json`, and `schemas/progress_markdown_export.schema.json`
- [ ] T011 Add read-performance indexes for bounded progress reads in `migrations/003_progress_indexes.sql`
- [ ] T012 Implement narrow progress repository read methods returning typed aggregate-safe rows in `src/language_tutor/dal/repositories.py`
- [ ] T013 Update `progress_report()` to accept `ProgressReportRequest`, injected `generated_at`, and repository read collaborators in `src/language_tutor/progress.py`

**Checkpoint**: Contracts, schema mirrors, migration, and repository read boundaries exist. User stories can start.

---

## Phase 3: User Story 1 - Review Per-Tag Mastery (Priority: P1) MVP

**Goal**: Learner sees normalized tags ranked by mastery score, band, evidence count,
recency, trend, stale state, and next-practice hint.

**Independent Test**: Seed completed sessions, vocabulary reviews, and writing mistakes
across several tags; `tutor progress --json` returns deterministic `tag_mastery` rows
without raw learner answers or full feedback prose.

### Tests for User Story 1

- [ ] T014 [P] [US1] Add failing unit tests for mastery component normalization formulas, weighting, band mapping, stale evidence, invalid/duplicate/unanalyzed evidence exclusion, shared `normalize_tag` identity, tie ordering, and next-practice hints in `tests/unit/test_progress.py`
- [ ] T015 [P] [US1] Add failing repository tests for vocabulary-review, mistake-event, and session-summary mastery evidence rows that preserve normalized tag identity across sources in `tests/unit/test_repositories.py`
- [ ] T016 [P] [US1] Add failing CLI contract tests for `tag_mastery` JSON shape and no-data mastery output in `tests/adapter_contract/test_progress_cli.py`
- [ ] T017 [P] [US1] Add failing integration tests for no-history, mixed-tag history with shared normalized tag identity, stale-tag history, skipped-record mastery exclusion, and deterministic tied-tag ordering in `tests/integration/test_progress_flow.py`

### Implementation for User Story 1

- [ ] T018 [P] [US1] Implement mastery component scoring, score clamping, band mapping, deterministic ordering, stale detection, and hint generation in `src/language_tutor/progress.py`
- [ ] T019 [P] [US1] Implement aggregate-only mastery evidence reads for vocabulary reviews, mistake events, and safe session-summary weak tags in `src/language_tutor/dal/repositories.py`
- [ ] T020 [US1] Integrate `tag_mastery`, preserved snapshot fields, and no-data next action into `ProgressReport` generation in `src/language_tutor/progress.py`
- [ ] T021 [US1] Wire `tutor progress --json [payload]` to emit the richer `ProgressReport` while preserving existing no-payload behavior in `src/language_tutor/cli.py`

**Checkpoint**: User Story 1 works independently as the MVP progress report.

---

## Phase 4: User Story 2 - Understand Recent Trend And Recap (Priority: P2)

**Goal**: Learner sees last-N completed-session recap totals, skipped-data notices,
trend directions, and ASCII sparklines.

**Independent Test**: Seed fixed completed-session windows for 1, 5, 10, and 30
sessions; repeated progress generation with the same `generated_at` returns byte-stable
recap totals, direction labels, and sparkline strings.

### Tests for User Story 2

- [ ] T022 [P] [US2] Add failing unit tests for trend direction polarity, odd-window middle-value handling, zero-baseline direction handling, under-10-percent steady threshold, insufficient-data handling, sparkline buckets, constant series, and min/max labels in `tests/unit/test_progress.py`
- [ ] T023 [US2] Add failing unit tests for duplicate-session canonicalization, invalid/interrupted/missing-analysis skip counts, and recap window bounds in `tests/unit/test_progress.py`
- [ ] T024 [P] [US2] Add failing repository tests for recent valid sessions, answer/review totals, severity totals, weak-tag changes, and current due-review summary in `tests/unit/test_repositories.py`
- [ ] T025 [P] [US2] Add failing integration tests for recap windows 1, 5, 10, 30, fewer-than-requested sessions, skipped-data notices, older-state missing summaries, and missing optional tag evidence in `tests/integration/test_progress_flow.py`
- [ ] T026 [P] [US2] Add failing CLI request-validation tests for `window_size` 0, `window_size` 31, bad JSON, unsupported format, and deterministic `generated_at` in `tests/adapter_contract/test_progress_cli.py`

### Implementation for User Story 2

- [ ] T027 [P] [US2] Implement `TextTrend` value bucketing, sparkline generation, min/max labeling, and polarity-aware direction helpers in `src/language_tutor/progress.py`
- [ ] T028 [US2] Implement canonical completed-session window selection and skipped-data notice aggregation in `src/language_tutor/progress.py`
- [ ] T029 [P] [US2] Implement repository reads for recent session summaries, answer totals, review totals, mistake severity totals, weak-tag changes, and current due-review summary in `src/language_tutor/dal/repositories.py`
- [ ] T030 [US2] Integrate `RecentSessionRecap`, `DueReviewSummary`, report window counts, and skipped-data notices into `ProgressReport` generation in `src/language_tutor/progress.py`
- [ ] T031 [US2] Add progress payload parsing, request validation, deterministic UTC defaulting, and structured progress error mapping in `src/language_tutor/cli.py`

**Checkpoint**: User Story 2 works independently from the richer JSON report.

---

## Phase 5: User Story 3 - Export A Shareable Progress Report (Priority: P2)

**Goal**: Learner exports the same progress facts as validated JSON and
terminal-printable markdown, with no raw learner data or graphical surface.

**Independent Test**: Generate JSON and markdown reports from the same fixture,
validate JSON round-trip, compare equivalent core facts, and confirm markdown is
ASCII-safe for trends and byte-stable for a fixed `generated_at`.

### Tests for User Story 3

- [ ] T032 [P] [US3] Add failing golden tests for no-data markdown, non-empty markdown, top-three weakest-tag visibility in the first progress section within 30 nonblank lines, tied mastery ordering, stale tags, trend labels, skipped notices, 100-column wrapping, essential-field non-truncation, and long tag/hint/summary truncation rules in `tests/golden/test_progress_rendering.py`
- [ ] T033 [P] [US3] Add failing CLI contract tests for `tutor render progress-report --json <payload>` and `tutor progress --json '{"format":"markdown"}'` in `tests/adapter_contract/test_progress_cli.py`
- [ ] T034 [P] [US3] Add failing JSON round-trip and markdown/JSON core-fact equivalence tests in `tests/adapter_contract/test_cli_json_contract.py`
- [ ] T035 [P] [US3] Add failing privacy and scope tests proving exports omit raw answers, span text, full feedback prose, event logs, host metadata, GUI, web, SVG, Mermaid, and graphical chart language in `tests/integration/test_progress_flow.py`
- [ ] T036 [P] [US3] Run a subagent baseline against current `skills/tutor-progress/SKILL.md` using scenarios for markdown export, JSON export, and privacy guardrails; record RED evidence in `specs/004-richer-feedback-progress/skill-pressure-evidence.md`

### Implementation for User Story 3

- [ ] T037 [P] [US3] Implement deterministic markdown rendering from validated `ProgressReport` in `src/language_tutor/progress_rendering.py`
- [ ] T038 [US3] Add `render progress-report` CLI command that validates `ProgressReport` input and emits `ProgressMarkdownExport` in `src/language_tutor/cli.py`
- [ ] T039 [US3] Add direct markdown export support for `ProgressReportRequest.format == "markdown"` through `tutor progress --json` in `src/language_tutor/cli.py`
- [ ] T040 [US3] Update `skills/tutor-progress/SKILL.md` through the assigned subagent after it reads the local writing-skills helper and required skill-authoring references
- [ ] T041 [US3] Run subagent pressure verification for updated `skills/tutor-progress/SKILL.md`, perform activation/description trigger review, perform main-agent integration review of subagent-reported changed files, and record GREEN/REFACTOR evidence, changed files, closed loopholes, and remaining gaps in `specs/004-richer-feedback-progress/skill-pressure-evidence.md`

**Checkpoint**: User Story 3 exports validated JSON and markdown and the skill surface routes export requests.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Performance, documentation, privacy hardening, and final verification across all
stories.

- [ ] T042 [P] Add one-year daily dense-history performance test for default JSON progress and markdown export under 5 seconds in `tests/performance/test_progress_performance.py`
- [ ] T043 [P] Add committed one-year progress fixture data used by performance and integration tests in `tests/fixtures/progress/one_year.json`
- [ ] T044 [P] Add export determinism fixture data for no-data, tied mastery, stale tags, skipped records, and long text in `tests/fixtures/progress/empty.json`
- [ ] T045 [P] Update feature documentation for text-only progress reports and export commands in `docs/FEATURES.md`
- [ ] T046 [P] Update Phase 4 exit-gate status notes only after all gates pass in `docs/ROADMAP.md`
- [ ] T047 Refresh command examples and expected outputs after implementation in `specs/004-richer-feedback-progress/quickstart.md`
- [ ] T048 Run unit, golden, adapter-contract, integration, migration, and performance gates listed in `specs/004-richer-feedback-progress/quickstart.md`
- [ ] T049 Run `rtk uv run pyright` and `rtk uv run ruff check .` using configuration in `pyproject.toml`
- [ ] T050 [P] Perform constitution compliance review for SOLID, DRY, KISS, YAGNI, SoC, composition, Demeter, local-first ownership, scope guardrails, and skill-gate evidence in `specs/004-richer-feedback-progress/tasks.md`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies.
- **Foundational (Phase 2)**: Depends on Setup; blocks all user stories.
- **User Story 1 (Phase 3)**: Depends on Foundational; MVP scope.
- **User Story 2 (Phase 4)**: Depends on Foundational and can run after US1 contracts are stable; must remain independently testable.
- **User Story 3 (Phase 5)**: Depends on canonical `ProgressReport` facts from US1 and US2.
- **Polish (Phase 6)**: Depends on selected user stories being complete.

### User Story Dependencies

- **US1 Review Per-Tag Mastery**: Starts after Phase 2; no dependency on US2 or US3.
- **US2 Recent Trend And Recap**: Starts after Phase 2; uses the same request/report contracts as US1.
- **US3 Shareable Progress Report**: Starts after US1/US2 report facts exist; markdown renders from the validated `ProgressReport`.

### Within Each User Story

- Tests must be written and fail before implementation.
- Repository reads must return aggregate-safe typed data before core aggregation uses them.
- Core aggregation must produce a validated `ProgressReport` before renderer work.
- Markdown must render from `ProgressReport`; it must not recompute facts.
- Skill pressure baseline must run before editing `skills/tutor-progress/SKILL.md`.
- Skill pressure verification must pass before the skill change is considered complete.

---

## Parallel Opportunities

- T001, T002, and T003 can run in parallel after repository checkout.
- T004, T005, T006, and T007 can run in parallel because they touch separate test files.
- In US1, T014, T015, T016, and T017 can run in parallel; T018 and T019 can run in parallel after those tests exist.
- In US2, T022, T024, T025, and T026 can run in parallel; T023 follows T022 because both edit `tests/unit/test_progress.py`; T027 and T029 can run in parallel after tests exist.
- In US3, T032, T033, T034, T035, and T036 can run in parallel; T037 can run while the skill subagent prepares T040.
- T042, T043, T044, T045, and T050 can run in parallel once all story behavior is complete; T050 must also confirm T041 recorded activation/description and main-agent skill reviews.

## Parallel Example: User Story 1

```bash
Task: "T014 [P] [US1] Add failing unit tests for mastery scoring in tests/unit/test_progress.py"
Task: "T015 [P] [US1] Add failing repository tests for mastery evidence in tests/unit/test_repositories.py"
Task: "T016 [P] [US1] Add failing CLI contract tests for tag_mastery in tests/adapter_contract/test_progress_cli.py"
Task: "T017 [P] [US1] Add failing integration tests for mixed-tag history in tests/integration/test_progress_flow.py"
```

## Parallel Example: User Story 2

```bash
Task: "T022 [P] [US2] Add failing unit tests for trend direction and sparklines in tests/unit/test_progress.py"
Task: "T024 [P] [US2] Add failing repository tests for recap reads in tests/unit/test_repositories.py"
Task: "T025 [P] [US2] Add failing integration tests for recap windows in tests/integration/test_progress_flow.py"
Task: "T026 [P] [US2] Add failing CLI request-validation tests in tests/adapter_contract/test_progress_cli.py"
```

## Parallel Example: User Story 3

```bash
Task: "T032 [P] [US3] Add failing golden tests for progress markdown in tests/golden/test_progress_rendering.py"
Task: "T033 [P] [US3] Add failing CLI contract tests for report rendering in tests/adapter_contract/test_progress_cli.py"
Task: "T034 [P] [US3] Add failing JSON round-trip tests in tests/adapter_contract/test_cli_json_contract.py"
Task: "T036 [P] [US3] Run subagent baseline for skills/tutor-progress/SKILL.md"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1 setup scaffolding.
2. Complete Phase 2 contracts, schema mirrors, migration, and repository read boundaries.
3. Complete Phase 3 per-tag mastery tests and implementation.
4. Validate US1 independently with `rtk uv run pytest tests/unit/test_progress.py tests/unit/test_repositories.py tests/adapter_contract/test_progress_cli.py tests/integration/test_progress_flow.py`.
5. Stop if MVP is the only desired delivery slice.

### Incremental Delivery

1. Add US1 per-tag mastery and preserve existing progress snapshot fields.
2. Add US2 recap/trend/skipped-data support through the same `ProgressReport`.
3. Add US3 markdown rendering, JSON round-trip validation, direct export support, and skill routing.
4. Run Phase 6 performance, docs, privacy, type, lint, and quickstart gates.

### Parallel Team Strategy

1. One developer owns schema/repository foundation.
2. One developer owns core mastery and recap aggregation.
3. One developer owns renderer/CLI export once the `ProgressReport` shape stabilizes.
4. One subagent owns `skills/tutor-progress/SKILL.md` update and pressure evidence; main agent reviews activation/description triggers and reported changed files before merge.

## Notes

- Keep SQLite as source of truth; reports are derived artifacts only.
- Keep markdown and JSON facts equivalent by rendering markdown from validated `ProgressReport`.
- Do not add runtime dependencies, charting libraries, GUI/web views, host adapters, scheduling algorithms, cloud sync, telemetry, or raw event-log exports.
- Avoid raw learner answers, mistake span text, full feedback prose, complete event logs, host metadata, and local filesystem paths in exported reports.
- Use `normalize_tag` from `src/language_tutor/vocab.py` for all tag identity.
- Current `session_summaries.session_id` is unique; duplicate-session tests should cover canonicalizer inputs even when current SQLite storage collapses duplicates.
- Commit after each task or logical group.
