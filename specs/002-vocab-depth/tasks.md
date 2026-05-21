# Tasks: Vocab Depth

**Input**: Design documents from `/specs/002-vocab-depth/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Tests**: Required. The feature specification and constitution require unit, contract, golden, integration, and migration coverage for changed vocabulary contracts, persistence, rendering, and CLI behavior.

**Organization**: Tasks are grouped by independently testable user story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel because it touches a different file and has no dependency on incomplete tasks.
- **[Story]**: User story label for story phases only.
- Every task includes exact file paths.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Add Phase 2 fixtures and seed inputs used across stories.

- [ ] T001 Create canonical Phase 2 seed JSON fixture with standard, duplicate-update, cloze, and invalid entries in tests/fixtures/vocabulary/phase2_seed.json
- [ ] T002 [P] Create malformed and empty JSON import fixtures for repair-path coverage in tests/fixtures/vocabulary/phase2_invalid.json
- [ ] T003 [P] Create large review-history fixture helper data for 500-attempt history tests in tests/fixtures/vocabulary/phase2_history.json

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Shared schema, migration, normalization, and persistence surfaces that all user stories depend on.

**CRITICAL**: No user story work can begin until this phase is complete.

- [ ] T004 [P] Add failing migration tests for `002_vocab_depth.sql` card metadata backfill, dedupe uniqueness, and review preservation in tests/migration/test_migrations.py
- [ ] T005 [P] Add failing schema tests for foundational Phase 2 vocabulary contract defaults, existing vocabulary schema compatibility, and schema export registry wiring in tests/unit/test_schemas.py
- [ ] T006 Create SQLite migration for card type, notes, stored additive source values, and recalculated dedupe keys in migrations/002_vocab_depth.sql
- [ ] T007 Update migration loader expectations for the new Phase 2 migration file in src/language_tutor/dal/migrations.py
- [ ] T008 Define shared vocabulary normalization, tag normalization, and duplicate identity helpers in src/language_tutor/vocab.py
- [ ] T009 Extend `VocabularyItem` with `card_type`, notes, stored additive source values, and Phase 2 defaults in src/language_tutor/schemas.py
- [ ] T010 Update repository row mapping and default seed rows for Phase 2 vocabulary columns in src/language_tutor/dal/repositories.py
- [ ] T011 Add regression tests for existing unfiltered vocabulary start/answer behavior before Phase 2 changes in tests/adapter_contract/test_vocab_cli.py and tests/integration/test_vocabulary_flow.py

**Checkpoint**: Foundation ready; user story implementation can proceed.

---

## Phase 3: User Story 1 - Build a Personal Vocabulary Deck (Priority: P1) MVP

**Goal**: Learner can add cards manually, import local JSON seed lists idempotently, and preserve review history across duplicates and metadata updates.

**Independent Test**: On an empty profile, add one card, import `tests/fixtures/vocabulary/phase2_seed.json`, re-import it, and verify expected cards exist once with preserved review history and accurate created/updated/skipped/invalid counts.

### Tests for User Story 1

- [ ] T012 [P] [US1] Add CLI and schema contract tests for `vocab add --json`, `vocab import --json`, duplicate rejection, empty tag/source metadata repair hints, and card/import JSON schema mirrors in tests/adapter_contract/test_vocab_cli.py and tests/unit/test_schemas.py
- [ ] T013 [P] [US1] Add repository unit tests for duplicate identity, additive metadata merge, accepted-answer union, empty tag/source metadata validation, and per-entry import atomicity in tests/unit/test_repositories.py
- [ ] T014 [P] [US1] Add integration test for manual add, seed import, idempotent re-import, and review-history preservation in tests/integration/test_vocabulary_flow.py
- [ ] T015 [P] [US1] Add golden tests for deterministic import summary rendering and duplicate-repair text in tests/golden/test_vocab_feedback.py

### Implementation for User Story 1

- [ ] T016 [US1] Add `VocabularyCardDefinition`, `VocabularyCardAddResult`, `SeedImportRequest`, and `SeedImportResult` contracts in src/language_tutor/schemas.py
- [ ] T017 [US1] Implement card validation, empty tag/source metadata rejection, and manual-card creation service using shared duplicate identity in src/language_tutor/vocab.py
- [ ] T018 [US1] Implement JSON seed-list parsing, per-entry validation, and import orchestration with repair details in src/language_tutor/vocab.py
- [ ] T019 [US1] Implement repository methods for manual insert, duplicate lookup, import upsert, and additive metadata merge in src/language_tutor/dal/repositories.py
- [ ] T020 [US1] Add `tutor vocab add --json` and `tutor vocab import --json` CLI commands with existing error-envelope behavior in src/language_tutor/cli.py
- [ ] T021 [US1] Register and generate schema mirrors for card definitions and import summaries in src/language_tutor/schemas.py, schemas/vocabulary_card_definition.schema.json, and schemas/vocabulary_import_summary.schema.json

**Checkpoint**: User Story 1 works independently and is the MVP.

---

## Phase 4: User Story 2 - Run Focused Tag Drills (Priority: P1)

**Goal**: Learner can start vocabulary drills filtered by one or more tags while due-first ordering and normal answer recording continue to work.

**Independent Test**: Create cards with multiple tags, start a drill for one tag, answer due and new cards, and verify every shown card matches the requested tag and records normal review results.

### Tests for User Story 2

- [ ] T022 [P] [US2] Add schema tests for `VocabularyDrillRequest`, normalized tag filters, empty filter rejection, and session-plan JSON schema mirror export in tests/unit/test_schemas.py
- [ ] T023 [P] [US2] Add repository unit tests for inclusive tag filtering, due-first ordering, and empty-state counts in tests/unit/test_repositories.py
- [ ] T024 [P] [US2] Add CLI contract tests for `vocab start --json` tag payloads and empty-state reasons in tests/adapter_contract/test_vocab_cli.py
- [ ] T025 [P] [US2] Add integration test for filtered drill selection and answer review persistence in tests/integration/test_vocabulary_flow.py

### Implementation for User Story 2

- [ ] T026 [US2] Add `VocabularyDrillRequest` and filtered session-plan fields to vocabulary contracts in src/language_tutor/schemas.py
- [ ] T027 [US2] Implement normalized tag-filter query support and matching/due counts in src/language_tutor/dal/repositories.py
- [ ] T028 [US2] Update `start_vocab` to accept drill requests, preserve due-first ordering, and return `no_matching_cards` versus `matching_cards_not_due` in src/language_tutor/vocab.py
- [ ] T029 [US2] Parse optional payload for `tutor vocab start --json` without changing unfiltered behavior in src/language_tutor/cli.py
- [ ] T030 [US2] Register and generate session-plan schema mirror with filter fields in src/language_tutor/schemas.py and schemas/vocabulary_session_plan.schema.json

**Checkpoint**: User Story 2 works independently after foundational tasks.

---

## Phase 5: User Story 3 - Practice Cloze Cards (Priority: P1)

**Goal**: Learner can create, import, drill, answer, and receive feedback for cloze cards using the same SRS and review path as standard vocabulary cards.

**Independent Test**: Add a cloze card manually and through JSON, drill it, answer correctly and incorrectly, and verify hidden prompt, reveal text, accepted answer, feedback, and review state.

### Tests for User Story 3

- [ ] T031 [P] [US3] Add schema tests for cloze card type, exactly one `{{answer}}` marker, missing-marker rejection, multi-marker rejection, and accepted-answer requirements in tests/unit/test_schemas.py
- [ ] T032 [P] [US3] Add golden tests for cloze drill prompt hiding and feedback reveal text in tests/golden/test_vocab_feedback.py
- [ ] T033 [P] [US3] Add CLI contract tests for cloze add, cloze import, invalid marker counts, and answer reveal in tests/adapter_contract/test_vocab_cli.py
- [ ] T034 [P] [US3] Add integration test for cloze add/import/start/answer/review flow in tests/integration/test_vocabulary_flow.py

### Implementation for User Story 3

- [ ] T035 [US3] Extend vocabulary contracts with `card_type="cloze"` validation and legacy `standard` defaults in src/language_tutor/schemas.py
- [ ] T036 [US3] Implement cloze prompt hiding, full-sentence reveal, and accepted-answer selection helpers in src/language_tutor/vocab.py
- [ ] T037 [US3] Persist and hydrate `card_type` for standard and cloze cards in src/language_tutor/dal/repositories.py
- [ ] T038 [US3] Add cloze reveal details to vocabulary answer feedback without changing SM-2 scheduling in src/language_tutor/feedback.py
- [ ] T039 [US3] Update `tutor-vocab` skill guidance for cloze add, import, start, and answer workflows in skills/tutor-vocab/SKILL.md
- [ ] T040 [US3] Update `tutor-vocab` helper script for cloze-aware command routing in skills/tutor-vocab/scripts/run.py

**Checkpoint**: User Story 3 works independently after foundational tasks.

---

## Phase 6: User Story 4 - Inspect Per-Card Review History (Priority: P2)

**Goal**: Learner can inspect chronological review attempts, outcomes, reviewed times, and current due status for one vocabulary card.

**Independent Test**: Review one card several times with different outcomes, open history, and verify attempts, answer details, timing, previous/next state, and due status match recorded practice.

### Tests for User Story 4

- [ ] T041 [P] [US4] Add CLI and schema contract tests for `vocab history --json`, missing-card errors, new-card history, complete 500-attempt JSON output under 2 seconds, and review-history JSON schema mirror export in tests/adapter_contract/test_vocab_cli.py and tests/unit/test_schemas.py
- [ ] T042 [P] [US4] Add repository unit tests for chronological review joins, current due status, and new-card empty attempts in tests/unit/test_repositories.py
- [ ] T043 [P] [US4] Add golden tests for readable review-history rendering that summarizes long histories while preserving complete attempt detail in JSON in tests/golden/test_vocab_feedback.py
- [ ] T044 [P] [US4] Add integration test for multiple review attempts and history audit output in tests/integration/test_vocabulary_flow.py

### Implementation for User Story 4

- [ ] T045 [US4] Add `VocabularyReviewHistoryRequest`, `VocabularyReviewHistory`, and attempt summary contracts in src/language_tutor/schemas.py
- [ ] T046 [US4] Implement repository review-history query joining `vocabulary_reviews` and `answer_events` in src/language_tutor/dal/repositories.py
- [ ] T047 [US4] Implement review-history service and due-status calculation in src/language_tutor/vocab.py
- [ ] T048 [US4] Add deterministic review-history text rendering in src/language_tutor/feedback.py
- [ ] T049 [US4] Add `tutor vocab history --json` CLI command with `vocab_card_not_found` repair errors in src/language_tutor/cli.py
- [ ] T050 [US4] Register and generate review-history schema mirror in src/language_tutor/schemas.py and schemas/vocabulary_review_history.schema.json
- [ ] T051 [US4] Update `tutor-vocab` skill guidance for per-card history inspection in skills/tutor-vocab/SKILL.md

**Checkpoint**: User Story 4 works independently after foundational tasks.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Verify no regressions, update user-facing docs, and enforce architecture gates.

- [ ] T052 [P] Update vocabulary feature documentation for manual add, imports, tag filters, cloze cards, and history in docs/FEATURES.md
- [ ] T053 [P] Update implementation notes and local-first data ownership details for Phase 2 vocabulary in docs/ARCHITECTURE.md
- [ ] T054 [P] Update known pitfalls for duplicate identity, JSON import repair, tag normalization, and cloze marker validation in docs/PITFALLS.md
- [ ] T055 Run quickstart verification commands and record any deviations in specs/002-vocab-depth/quickstart.md
- [ ] T056 Run full verification gates listed in specs/002-vocab-depth/plan.md, including existing unfiltered vocabulary regression tests, and fix failures in src/language_tutor/, tests/, skills/tutor-vocab/, migrations/, schemas/, or docs/
- [ ] T057 Perform constitution compliance review for SOLID/DRY/KISS/YAGNI/SoC/Demeter across src/language_tutor/, tests/, docs/, specs/002-vocab-depth/spec.md, specs/002-vocab-depth/plan.md, and specs/002-vocab-depth/tasks.md before implementation is considered complete

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies.
- **Foundational (Phase 2)**: Depends on Setup; blocks every user story.
- **US1 (Phase 3)**: Depends on Foundational; MVP.
- **US2 (Phase 4)**: Depends on Foundational; can run after or alongside US1 once shared contracts exist.
- **US3 (Phase 5)**: Depends on Foundational and the US1 add/import contract and service path; only cloze-specific schema/rendering prework can run before the US1 service baseline exists.
- **US4 (Phase 6)**: Depends on Foundational and benefits from US1/US3 test data but remains independently testable with direct fixtures.
- **Polish (Phase 7)**: Depends on completed target stories.

### User Story Dependencies

- **US1 (P1)**: No story dependency; provides MVP card creation/import path.
- **US2 (P1)**: No story dependency after Foundational; uses tag metadata created by fixtures or US1.
- **US3 (P1)**: Depends on the US1 add/import contract and service path because cloze cards reuse the standard manual-add, seed-import, and review flow.
- **US4 (P2)**: No required story dependency after Foundational; review attempts can be created directly in tests.

### Within Each User Story

- Tests first; verify failing tests before implementation.
- Contracts before repository/core implementation.
- Repository behavior before CLI integration.
- Rendering before golden snapshot acceptance.
- Each story must pass its own unit, contract, golden, and integration tests before moving on.

---

## Parallel Opportunities

- Setup fixture tasks T002 and T003 can run in parallel after T001 is defined.
- Foundational tests T004 and T005 can run in parallel.
- Story test tasks marked `[P]` can run in parallel because they target different test files.
- After Phase 2, US1 and US2 can be staffed in parallel if shared schema changes are coordinated; US3 can parallelize only cloze-specific tests/rendering until the US1 add/import service path exists.
- Documentation polish tasks T052, T053, and T054 can run in parallel.

---

## Parallel Example: User Story 1

```bash
Task: "T012 [US1] Add CLI/schema contract tests in tests/adapter_contract/test_vocab_cli.py and tests/unit/test_schemas.py"
Task: "T013 [US1] Add repository unit tests in tests/unit/test_repositories.py"
Task: "T014 [US1] Add integration tests in tests/integration/test_vocabulary_flow.py"
Task: "T015 [US1] Add golden tests in tests/golden/test_vocab_feedback.py"
```

## Parallel Example: User Story 2

```bash
Task: "T022 [US2] Add schema and session-plan mirror tests in tests/unit/test_schemas.py"
Task: "T023 [US2] Add repository tests in tests/unit/test_repositories.py"
Task: "T024 [US2] Add CLI contract tests in tests/adapter_contract/test_vocab_cli.py"
Task: "T025 [US2] Add integration tests in tests/integration/test_vocabulary_flow.py"
```

## Parallel Example: User Story 3

```bash
Task: "T031 [US3] Add cloze schema tests in tests/unit/test_schemas.py"
Task: "T032 [US3] Add cloze golden tests in tests/golden/test_vocab_feedback.py"
Task: "T033 [US3] Add cloze CLI contract tests in tests/adapter_contract/test_vocab_cli.py"
Task: "T034 [US3] Add cloze integration tests in tests/integration/test_vocabulary_flow.py"
```

## Parallel Example: User Story 4

```bash
Task: "T041 [US4] Add history CLI/schema contract tests in tests/adapter_contract/test_vocab_cli.py and tests/unit/test_schemas.py"
Task: "T042 [US4] Add history repository tests in tests/unit/test_repositories.py"
Task: "T043 [US4] Add history golden tests in tests/golden/test_vocab_feedback.py"
Task: "T044 [US4] Add history integration tests in tests/integration/test_vocabulary_flow.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1 setup fixtures.
2. Complete Phase 2 foundational schema, migration, and repository baseline.
3. Complete Phase 3 US1 tests and implementation.
4. Stop and validate manual add plus idempotent seed import independently.

### Incremental Delivery

1. Deliver US1 for deck ownership.
2. Deliver US2 for focused tag drills.
3. Deliver US3 for cloze practice.
4. Deliver US4 for history inspection.
5. Run Phase 7 verification and documentation updates.

### Verification Gates

```bash
rtk pytest tests/unit/test_schemas.py tests/unit/test_repositories.py tests/unit/test_srs.py
rtk pytest tests/golden/test_vocab_feedback.py
rtk pytest tests/adapter_contract/test_vocab_cli.py
rtk pytest tests/integration/test_vocabulary_flow.py
rtk pytest tests/migration/test_migrations.py
rtk pyright
rtk ruff check .
```

The adapter-contract and integration gates include existing unfiltered
vocabulary regression cases; do not narrow them to Phase 2-only tests.

---

## Notes

- `[P]` tasks use different files and have no dependency on incomplete tasks in the same phase.
- `VocabularyCardDefinition`, duplicate identity, tag normalization, and cloze validation must remain single-source helpers.
- Seed JSON is import-only; SQLite remains canonical after import.
- Host adapters, writing feedback, progress dashboards, cloud behavior, audio, gamification, and scheduler algorithm changes remain out of scope.
