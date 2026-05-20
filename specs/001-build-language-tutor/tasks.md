# Tasks: language-tutor v1

**Input**: Design documents from `/specs/001-build-language-tutor/`

**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, `quickstart.md`, and `contracts/`

**Tests**: Required by the feature specification and constitution. Contract, schema, migration, rendering, SRS, boot-context, and evaluator semantic tasks appear before implementation tasks.

**Organization**: Tasks are grouped by independently testable user story. User stories can start only after shared Setup and Foundational phases are complete.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel because it touches different files and has no dependency on incomplete tasks.
- **[Story]**: User story label for traceability. Setup, Foundational, and Polish tasks intentionally have no story label.
- Every task includes at least one exact repository path.

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Establish project, plugin, CLI, default data, and test skeletons.

- [ ] T001 Define Python package metadata, dependencies, scripts, and tool configuration in `pyproject.toml`
- [ ] T002 Create base package skeleton in `src/language_tutor/__init__.py`
- [ ] T003 [P] Configure strict type checking in `pyrightconfig.json`
- [ ] T004 [P] Create Claude plugin manifest skeleton in `.claude-plugin/plugin.json`
- [ ] T005 [P] Create executable CLI wrapper skeleton in `bin/tutor`
- [ ] T006 [P] Create Claude hook registry and hook documentation skeletons in `hooks/hooks.json` and `hooks/README.md`
- [ ] T007 [P] Create editable default profile and preference templates with documented v1 defaults in `data/defaults/profile.yaml` and `data/defaults/preferences.yaml`
- [ ] T008 [P] Create test directory scaffolding in `tests/unit/`, `tests/golden/`, `tests/contract/`, `tests/adapter_contract/`, `tests/integration/`, `tests/migration/`, and `tests/fixtures/`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Build contracts, data boundaries, migrations, repositories, adapter protocols, and CLI JSON plumbing used by all stories.

**Critical**: No user story work can begin until this phase is complete.

### Tests for Foundational Contracts

- [ ] T009 [P] Write failing schema and JSON schema export tests in `tests/unit/test_schemas.py`
- [ ] T010 [P] Write failing CLI JSON error-envelope contract tests in `tests/adapter_contract/test_cli_json_contract.py`
- [ ] T011 [P] Write failing platform path resolution tests in `tests/unit/test_paths.py`
- [ ] T012 [P] Write failing initial SQLite migration tests in `tests/migration/test_migrations.py`
- [ ] T013 [P] Write failing repository transaction tests in `tests/unit/test_repositories.py`

### Implementation for Foundational Contracts

- [ ] T014 Implement Pydantic v2 contracts, closed enums, and schema export helpers in `src/language_tutor/schemas.py`
- [ ] T015 Implement repair-oriented error codes and JSON error envelopes in `src/language_tutor/errors.py`
- [ ] T016 Implement narrow adapter and repository Protocols in `src/language_tutor/adapters/base.py`
- [ ] T017 Implement Claude adapter boundary helpers without persistence logic in `src/language_tutor/adapters/claude.py`
- [ ] T018 Implement macOS/Linux platform path resolution with test overrides in `src/language_tutor/dal/paths.py`
- [ ] T019 Create initial SQLite tables, constraints, indexes, and migration marker in `migrations/001_initial.sql`
- [ ] T020 Implement ordered SQLite migration runner with checksum validation in `src/language_tutor/dal/migrations.py`
- [ ] T021 Implement SQLite connection, transaction, and idempotency primitives in `src/language_tutor/dal/sqlite_store.py`
- [ ] T022 Implement repository methods for lifecycle, answers, vocabulary, mistakes, summaries, metrics, and costs in `src/language_tutor/dal/repositories.py`
- [ ] T023 Generate JSON Schema mirrors in `schemas/boot_context.schema.json`, `schemas/feedback_envelope.schema.json`, `schemas/session_analysis.schema.json`, and `schemas/answer_event.schema.json`
- [ ] T024 Implement Click CLI root, JSON parsing, JSON output, and error handling in `src/language_tutor/cli.py`
- [ ] T025 Wire `bin/tutor` to invoke `language_tutor.cli` without host-specific imports in `bin/tutor`

**Checkpoint**: Foundation ready. Story work can now proceed in priority order or in parallel by story.

---

## Phase 3: User Story 1 - Start a First Learning Session (Priority: P1) MVP

**Goal**: A learner can run setup, store local profile/preferences, and receive deterministic first-session context without remote storage.

**Independent Test**: On a fresh test path, run setup read/write with only native and target language, then boot context and render boot context. Verify defaults apply, profile/preferences YAML changes, SQLite history remains untouched, boot context stays within 6,000 rendered characters, and the setup-to-context path stays under 60 seconds with model calls stubbed.

### Tests for User Story 1

- [ ] T026 [P] [US1] Write failing setup CLI contract tests in `tests/adapter_contract/test_setup_cli.py`
- [ ] T027 [P] [US1] Write failing YAML validation and round-trip tests in `tests/unit/test_yaml_store.py`
- [ ] T028 [P] [US1] Write failing no-history and history-rich boot-context golden tests with eight-section ordering, due review, weak-pattern, latest-recap, cost/status, first-session guidance, and 6,000-character budget assertions in `tests/golden/test_boot_context.py`
- [ ] T029 [P] [US1] Write failing fresh setup, setup-rerun history-preservation, and first-session integration tests, including the under-60-second setup-to-context budget with model calls stubbed, in `tests/integration/test_first_session.py`

### Implementation for User Story 1

- [ ] T030 [US1] Implement comment-preserving profile and preference YAML store in `src/language_tutor/dal/yaml_store.py`
- [ ] T031 [US1] Implement setup read/write service with required native/target language fields and defaults for level, interests, constraints, feedback verbosity, review intensity, transliteration tolerance, session length, ASCII fallback, and streak grace in `src/language_tutor/setup.py`
- [ ] T032 [US1] Implement deterministic boot-context builder for no-history, existing-profile, and populated-history states with due review, weak-pattern, latest-recap, and cost/status sections in `src/language_tutor/boot_context.py`
- [ ] T033 [US1] Implement bounded boot-context markdown renderer with a 6,000-character cap in `src/language_tutor/boot_context.py`
- [ ] T034 [US1] Add `setup read` and `setup write` CLI commands in `src/language_tutor/cli.py`
- [ ] T035 [US1] Add `boot-context` and `render boot-context` CLI commands in `src/language_tutor/cli.py`
- [ ] T036 [US1] Implement session-start hook that calls the CLI boundary in `hooks/session-start.sh`
- [ ] T037 [US1] Create setup skill orchestration that shells out only to `bin/tutor` in `skills/tutor-setup/SKILL.md`
- [ ] T038 [US1] Add first-session profile, preference, and storage fixtures in `tests/fixtures/first_session/`
- [ ] T039 [US1] Document setup skill and session-start hook discovery paths without adding plugin logic in `hooks/README.md`

**Checkpoint**: User Story 1 is independently usable and testable.

---

## Phase 4: User Story 2 - Practice Vocabulary With Review Scheduling (Priority: P1)

**Goal**: A learner can practice due vocabulary, receive immediate correction, record one review event, and update next-review timing exactly once.

**Independent Test**: Seed due vocabulary and preferences, run vocab start, answer correct/partial/missed/unanswered prompts, then verify queue sizing from session length/review intensity, transliteration tolerance behavior, feedback, answer events, review events, future due times, duplicate answer idempotency, and duplicate vocabulary item handling.

### Tests for User Story 2

- [ ] T040 [P] [US2] Write failing SM-2 scheduling, queue-sizing, unanswered, mixed-language, and severity-quality mapping tests in `tests/unit/test_srs.py`
- [ ] T041 [P] [US2] Write failing vocabulary CLI, transliteration tolerance, and idempotency contract tests in `tests/adapter_contract/test_vocab_cli.py`
- [ ] T042 [P] [US2] Write failing vocabulary practice integration tests, including session length/review intensity queue sizing, duplicate item handling by normalized target-language lemma/prompt key, and interrupted-session exact-once answer/review persistence, in `tests/integration/test_vocabulary_flow.py`
- [ ] T043 [P] [US2] Write failing vocabulary feedback golden tests in `tests/golden/test_vocab_feedback.py`

### Implementation for User Story 2

- [ ] T044 [US2] Implement deterministic SM-2 scheduler and verdict-to-quality mapping in `src/language_tutor/srs.py`
- [ ] T045 [US2] Implement accepted-answer comparator with blank, "I don't know", mixed-language, transliteration preference handling, and vocabulary feedback envelope builder in `src/language_tutor/feedback.py`
- [ ] T046 [US2] Implement due queue selection using session length/review intensity, starter-content planning, and duplicate vocabulary item handling in `src/language_tutor/vocab.py`
- [ ] T047 [US2] Implement idempotent and interruption-safe vocabulary answer and review persistence in `src/language_tutor/dal/repositories.py`
- [ ] T048 [US2] Add `vocab start` CLI command in `src/language_tutor/cli.py`
- [ ] T049 [US2] Add `vocab answer` CLI command with idempotency key handling in `src/language_tutor/cli.py`
- [ ] T050 [US2] Add vocabulary seed, transliteration, duplicate-item, and answer fixtures in `tests/fixtures/vocabulary/`
- [ ] T051 [US2] Create vocabulary skill orchestration that shells out only to `bin/tutor` in `skills/tutor-vocab/SKILL.md`
- [ ] T052 [US2] Add vocabulary skill helper script that shells out only to `bin/tutor` in `skills/tutor-vocab/scripts/run.py`

**Checkpoint**: User Story 2 is independently usable and testable.

---

## Phase 5: User Story 3 - Improve Free Writing With Structured Feedback (Priority: P1)

**Goal**: A learner can submit free writing and receive validated localized feedback with controlled tags, severity, spans, corrected text, and safe fallback behavior.

**Independent Test**: Submit at least 20 accepted writing fixtures with known grammar, vocabulary, punctuation, and Slavic morphology issues; verify evaluator JSON validation, retry/downgrade behavior, feedback-verbosity-shaped explanations, rendered feedback, mistake persistence, and unchanged vocabulary schedules.

### Tests for User Story 3

- [ ] T053 [P] [US3] Write failing evaluator JSON contract tests, including feedback verbosity-derived detail budget, in `tests/adapter_contract/test_evaluator_contract.py`
- [ ] T054 [P] [US3] Write failing malformed, unsupported-tag, contradictory, missing-confidence, invalid-confidence, and low-confidence evaluator tests in `tests/unit/test_evaluators.py`
- [ ] T055 [P] [US3] Write failing feedback rendering and ASCII fallback golden tests in `tests/golden/test_feedback_rendering.py`
- [ ] T056 [P] [US3] Write failing writing prompt and record integration tests in `tests/integration/test_writing_flow.py`
- [ ] T057 [P] [US3] Add at least 20 accepted semantic evaluator fixture cases and a failing threshold harness that enforces SC-004 95% feedback completeness and SC-005 90% Slavic verdict/tag pass rates in `tests/fixtures/evaluator_slavic/` and `tests/adapter_contract/test_evaluator_semantic_thresholds.py`

### Implementation for User Story 3

- [ ] T058 [US3] Implement evaluator output validation, confidence enum handling (`high`, `medium`, `low`), retry decision, safe downgrade, and controlled-tag handling in `src/language_tutor/evaluators.py`
- [ ] T059 [US3] Implement writing prompt generation and writing record service in `src/language_tutor/writing.py`
- [ ] T060 [US3] Implement deterministic feedback markdown renderer with ASCII fallback in `src/language_tutor/feedback.py`
- [ ] T061 [US3] Implement mistake-event persistence without vocabulary SRS mutation in `src/language_tutor/dal/repositories.py`
- [ ] T062 [US3] Add `writing prompt` and `writing record` CLI commands in `src/language_tutor/cli.py`
- [ ] T063 [US3] Add `render feedback` CLI command in `src/language_tutor/cli.py`
- [ ] T064 [US3] Create stateless tutor judge agent contract prompt that consumes allowed tags from input without duplicating the controlled vocabulary in `agents/tutor-judge.md`
- [ ] T065 [US3] Create writing skill orchestration that calls `tutor-judge` then `bin/tutor` in `skills/tutor-writing/SKILL.md`
- [ ] T066 [US3] Add writing skill helper script that invokes `tutor-judge` and validates through `bin/tutor` in `skills/tutor-writing/scripts/run.py`

**Checkpoint**: User Story 3 is independently usable and testable.

---

## Phase 6: User Story 4 - Review Progress and Next Focus (Priority: P2)

**Goal**: A learner can view compact progress and receive an end-of-session recap with streak, due counts, weak patterns, maturity, cost, and next focus.

**Independent Test**: Seed empty history and one-year daily history cases, run progress and session-end, then verify streak grace, due counts, weak tags, recap, item maturity, month-to-date cost, progress under 5 seconds, and pending summary status when session analysis is interrupted.

### Tests for User Story 4

- [ ] T067 [P] [US4] Write failing progress aggregation unit tests in `tests/unit/test_progress.py`
- [ ] T068 [P] [US4] Write failing empty-history and history-rich progress integration tests, including the under-5-second one-year fixture budget, in `tests/integration/test_progress_flow.py`
- [ ] T069 [P] [US4] Write failing session-end CLI contract tests, including interrupted-analysis pending status, in `tests/adapter_contract/test_session_end_cli.py`
- [ ] T070 [P] [US4] Write failing progress and session-summary golden tests in `tests/golden/test_progress_rendering.py`

### Implementation for User Story 4

- [ ] T071 [US4] Implement streak, due count, item maturity, weak-pattern, recap, and cost aggregation in `src/language_tutor/progress.py`
- [ ] T072 [US4] Implement session analysis validation, interrupted-analysis pending status, summary creation, and next-focus selection in `src/language_tutor/lifecycle.py`
- [ ] T073 [US4] Implement session summary, skill metric, and cost repository queries in `src/language_tutor/dal/repositories.py`
- [ ] T074 [US4] Add `progress` CLI command in `src/language_tutor/cli.py`
- [ ] T075 [US4] Add `session-end` CLI command in `src/language_tutor/cli.py`
- [ ] T076 [US4] Implement non-blocking session-end hook wrapper that preserves persisted events when analysis remains pending in `hooks/session-end.sh`
- [ ] T077 [US4] Create progress skill orchestration that shells out only to `bin/tutor` in `skills/tutor-progress/SKILL.md`
- [ ] T078 [US4] Add empty-history and one-year progress fixtures in `tests/fixtures/progress/`
- [ ] T079 [US4] Add progress skill helper script that shells out only to `bin/tutor` in `skills/tutor-progress/scripts/run.py`

**Checkpoint**: User Story 4 is independently usable and testable.

---

## Phase 7: User Story 5 - Trust Local, Portable Tutor Behavior (Priority: P2)

**Goal**: A learner or contributor can verify install health, inspect local data ownership, and trust deterministic local-only behavior on macOS and Linux.

**Independent Test**: Run doctor on macOS/Linux fixture paths, corrupt profile/history/schema inputs, and a 30-consecutive-day local-session fixture; verify actionable errors, no remote/account requirements, separate YAML/SQLite ownership, plugin discovery, history preservation, and stable rerendering.

### Tests for User Story 5

- [ ] T080 [P] [US5] Write failing doctor CLI contract tests in `tests/adapter_contract/test_doctor_cli.py`
- [ ] T081 [P] [US5] Write failing plugin surface contract tests in `tests/adapter_contract/test_plugin_surface.py`
- [ ] T082 [P] [US5] Write failing local data ownership integration tests, including 30 consecutive local sessions without account, telemetry, cloud storage, or manual state repair, in `tests/integration/test_local_data_ownership.py`
- [ ] T083 [P] [US5] Write failing deterministic rerender golden tests in `tests/golden/test_deterministic_rerender.py`

### Implementation for User Story 5

- [ ] T084 [US5] Implement runtime, data path, stored data, migration, schema, and plugin file health checks in `src/language_tutor/health.py`
- [ ] T085 [US5] Add `doctor --json` CLI command with repair-oriented failure output in `src/language_tutor/cli.py`
- [ ] T086 [US5] Complete Claude hook registry for plugin discovery in `hooks/hooks.json`
- [ ] T087 [US5] Complete Claude plugin metadata only in `.claude-plugin/plugin.json` and keep component discovery in root-level `skills/`, `hooks/`, `agents/`, and `bin/`
- [ ] T088 [US5] Document local data ownership, install checks, and no-telemetry behavior in `README.md`
- [ ] T089 [US5] Add macOS, Linux, corrupt-profile, and corrupt-database fixture cases in `tests/fixtures/doctor/`
- [ ] T090 [US5] Include plugin files, defaults, migrations, and schemas in package build data in `pyproject.toml`

**Checkpoint**: User Story 5 is independently usable and testable.

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Final verification, docs, coverage, and governance review after selected stories are complete.

- [ ] T091 [P] Reconcile contributor quickstart commands with implemented CLI behavior in `specs/001-build-language-tutor/quickstart.md`
- [ ] T092 [P] Add pytest coverage configuration and thresholds in `pyproject.toml`
- [ ] T093 [P] Add user-facing install and usage examples in `README.md`
- [ ] T094 Run full pytest verification for deterministic suites in `tests/`
- [ ] T095 Run strict type verification using `pyrightconfig.json`
- [ ] T096 Run lint verification using `pyproject.toml`
- [ ] T097 Perform SOLID, DRY, KISS, YAGNI, SoC, composition, and Demeter review against `.specify/memory/constitution.md`
- [ ] T098 Validate quickstart smoke flow from `specs/001-build-language-tutor/quickstart.md`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 Setup**: No dependencies.
- **Phase 2 Foundational**: Depends on Phase 1 and blocks every user story.
- **Phase 3 US1**: Depends on Phase 2.
- **Phase 4 US2**: Depends on Phase 2. Can run alongside US1 after foundation, but MVP delivery should validate US1 first.
- **Phase 5 US3**: Depends on Phase 2. Can run alongside US1 and US2 after foundation.
- **Phase 6 US4**: Depends on Phase 2 and benefits from US2/US3 data, but must handle empty history independently.
- **Phase 7 US5**: Depends on Phase 2 and validates all plugin/data ownership surfaces.
- **Phase 8 Polish**: Depends on all selected story phases.

### User Story Dependency Graph

```text
Setup -> Foundational -> US1
                       -> US2
                       -> US3
                       -> US4
                       -> US5

Recommended MVP path: Setup -> Foundational -> US1
Recommended P1 path:  Setup -> Foundational -> US1 -> US2 -> US3
Recommended v1 path:  Setup -> Foundational -> US1 -> US2 -> US3 -> US4 -> US5 -> Polish
```

### Within Each User Story

- Write required tests first and confirm they fail for the expected reason.
- Implement schemas/contracts before services that depend on them.
- Implement migrations before repository behavior.
- Implement repository behavior before CLI commands that mutate state.
- Implement CLI commands before hooks and skills that shell out to `bin/tutor`.
- Complete each story checkpoint before moving to the next priority when working sequentially.

---

## Parallel Opportunities

- Phase 1 tasks T003-T008 can run in parallel after T001/T002 ownership is clear.
- Phase 2 test tasks T009-T013 can run in parallel before implementation.
- US1 tests T026-T029 can run in parallel.
- US2 tests T040-T043 can run in parallel.
- US3 tests T053-T057 can run in parallel.
- US4 tests T067-T070 can run in parallel.
- US5 tests T080-T083 can run in parallel.
- After Phase 2, US1, US2, and US3 can be staffed in parallel if shared edits to `src/language_tutor/cli.py`, `src/language_tutor/feedback.py`, and `src/language_tutor/dal/repositories.py` are coordinated.

### Parallel Example: User Story 1

```bash
Task: "T026 [US1] Write failing setup CLI contract tests in tests/adapter_contract/test_setup_cli.py"
Task: "T027 [US1] Write failing YAML validation and round-trip tests in tests/unit/test_yaml_store.py"
Task: "T028 [US1] Write failing no-history and history-rich boot-context golden tests with eight-section ordering, due review, weak-pattern, latest-recap, cost/status, first-session guidance, and 6,000-character budget assertions in tests/golden/test_boot_context.py"
Task: "T029 [US1] Write failing fresh setup, setup-rerun history-preservation, and first-session integration tests, including the under-60-second setup-to-context budget with model calls stubbed, in tests/integration/test_first_session.py"
```

### Parallel Example: User Story 2

```bash
Task: "T040 [US2] Write failing SM-2 scheduling, queue-sizing, unanswered, mixed-language, and severity-quality mapping tests in tests/unit/test_srs.py"
Task: "T041 [US2] Write failing vocabulary CLI and idempotency contract tests in tests/adapter_contract/test_vocab_cli.py"
Task: "T042 [US2] Write failing vocabulary practice integration tests, including session length/review intensity queue sizing, duplicate item handling by normalized target-language lemma/prompt key, and interrupted-session exact-once answer/review persistence, in tests/integration/test_vocabulary_flow.py"
Task: "T043 [US2] Write failing vocabulary feedback golden tests in tests/golden/test_vocab_feedback.py"
```

### Parallel Example: User Story 3

```bash
Task: "T053 [US3] Write failing evaluator JSON contract tests, including feedback verbosity-derived detail budget, in tests/adapter_contract/test_evaluator_contract.py"
Task: "T054 [US3] Write failing malformed, unsupported-tag, contradictory, missing-confidence, invalid-confidence, and low-confidence evaluator tests in tests/unit/test_evaluators.py"
Task: "T055 [US3] Write failing feedback rendering and ASCII fallback golden tests in tests/golden/test_feedback_rendering.py"
Task: "T057 [US3] Add at least 20 accepted semantic evaluator fixture cases and a failing threshold harness that enforces SC-004 95% feedback completeness and SC-005 90% Slavic verdict/tag pass rates in tests/fixtures/evaluator_slavic/ and tests/adapter_contract/test_evaluator_semantic_thresholds.py"
```

### Parallel Example: User Story 4

```bash
Task: "T067 [US4] Write failing progress aggregation unit tests in tests/unit/test_progress.py"
Task: "T068 [US4] Write failing empty-history and history-rich progress integration tests, including the under-5-second one-year fixture budget, in tests/integration/test_progress_flow.py"
Task: "T069 [US4] Write failing session-end CLI contract tests, including interrupted-analysis pending status, in tests/adapter_contract/test_session_end_cli.py"
Task: "T070 [US4] Write failing progress and session-summary golden tests in tests/golden/test_progress_rendering.py"
```

### Parallel Example: User Story 5

```bash
Task: "T080 [US5] Write failing doctor CLI contract tests in tests/adapter_contract/test_doctor_cli.py"
Task: "T081 [US5] Write failing plugin surface contract tests in tests/adapter_contract/test_plugin_surface.py"
Task: "T082 [US5] Write failing local data ownership integration tests, including 30 consecutive local sessions without account, telemetry, cloud storage, or manual state repair, in tests/integration/test_local_data_ownership.py"
Task: "T083 [US5] Write failing deterministic rerender golden tests in tests/golden/test_deterministic_rerender.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1 Setup.
2. Complete Phase 2 Foundational.
3. Complete Phase 3 User Story 1.
4. Stop and validate setup, boot context, and session-start hook independently.

### Incremental Delivery

1. Deliver US1 to establish local profile/preferences and first-session context.
2. Deliver US2 to add vocabulary retention loop.
3. Deliver US3 to add structured writing feedback.
4. Deliver US4 to add progress and end-of-session recap.
5. Deliver US5 to harden health checks, plugin packaging, and local ownership guarantees.

### Parallel Team Strategy

1. Complete Setup and Foundational phases together.
2. Assign US1, US2, and US3 to separate implementers after Phase 2.
3. Coordinate edits to shared files: `src/language_tutor/cli.py`, `src/language_tutor/dal/repositories.py`, `src/language_tutor/feedback.py`, and `.claude-plugin/plugin.json`.
4. Add US4 and US5 once enough shared behavior exists to validate progress and health.

---

## Notes

- `[P]` marks tasks that can run concurrently with other marked tasks in the same phase.
- `[US#]` labels map tasks to user stories in `specs/001-build-language-tutor/spec.md`.
- Tests are mandatory here because the spec and constitution require contract, deterministic, migration, rendering, SRS, and semantic evaluator verification.
- Skills and hooks remain orchestration-only. They must shell out to `bin/tutor` and must not access YAML, SQLite, SRS, or rendering logic directly.
