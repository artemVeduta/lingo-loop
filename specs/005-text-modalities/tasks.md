# Tasks: Text Modalities + Skill Authoring

**Input**: Design documents from `/specs/005-text-modalities/`

**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, `contracts/`, `quickstart.md`

**Tests**: Required by the feature specification and constitution. Contract, schema, persistence, rendering, progress, migration, skill-pressure, and semantic-eval tests must be written before implementation for their affected surface.

**Organization**: Tasks are grouped by independently testable user story. Phase 2 contains only shared blockers needed by multiple text-modality stories.

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Prepare evidence and fixture locations without changing runtime behavior.

- [X] T001 Create Phase 5 evidence artifact skeletons in specs/005-text-modalities/skill-inventory.md, specs/005-text-modalities/skill-rewrite-evidence.md, and specs/005-text-modalities/skill-suite-coherence-audit.md
- [X] T002 [P] Create text-modality fixture index in tests/fixtures/text_modalities/README.md
- [X] T003 [P] Record the required local writing-skills helper path, external reference checklist, and blocked-rewrite decision rule for unavailable helper/reference inputs in specs/005-text-modalities/skill-rewrite-evidence.md

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Shared contracts, validators, persistence helpers, and progress fields required by reading, lesson, and transcript stories.

**Critical**: No text-modality user story implementation starts until this phase is complete.

### Tests for Shared Foundation

- [X] T004 [P] Add shared text exercise validation, render-budget, repair/refusal, and result-wrapper unit tests in tests/unit/test_text_modalities.py
- [X] T005 [P] Add schema literal and JSON-schema export tests for text modality models, AnswerEvent skills, and progress totals in tests/unit/test_schemas.py
- [X] T006 [P] Add repository tests for idempotent text-modality answer recording and safe mistake-event insertion in tests/unit/test_repositories.py
- [X] T007 [P] Add progress aggregation tests for reading_answers, lesson_answers, and transcript_drills totals in tests/unit/test_progress.py
- [X] T008 [P] Add migration/local-data ownership tests proving existing SQLite tables accept reading and lesson skill values without a new runtime table in tests/migration/test_migrations.py

### Implementation for Shared Foundation

- [X] T009 Update shared Pydantic contracts for TextExerciseCandidate, TextModalityRecordInput, TextModalityResult, stored skill literals, response statuses, and progress totals in src/language_tutor/schemas.py
- [X] T010 Implement shared text exercise validation, rendered output budgets, one-repair refusal helpers, scope guardrails, and safe mistake filtering in src/language_tutor/text_modalities.py
- [X] T011 Update schema export mapping for text-modality schema mirrors in src/language_tutor/schemas.py
- [X] T012 Add generated schema mirrors for text modality contracts in schemas/text_modality_result.schema.json and schemas/text_modality_record.schema.json
- [X] T013 Refactor mistake insertion so repository helpers can persist safe mistake events for writing, reading, lesson, and transcript-as-reading without hardcoded writing skill in src/language_tutor/dal/repositories.py
- [X] T014 Add narrow repository helper for text-modality answer event recording with optional idempotency key in src/language_tutor/dal/repositories.py
- [X] T015 Extend progress input rows, totals, and aggregate output for reading, lesson, and transcript attempts in src/language_tutor/progress.py
- [X] T016 Update progress rendering for any new aggregate-only practice totals while preserving raw-answer privacy in src/language_tutor/progress_rendering.py

**Checkpoint**: Shared foundation validates candidate exercises, result wrappers, safe persistence, and aggregate progress without delivering a learner-facing modality.

---

## Phase 3: User Story 1 - Verify Skill Suite Coherence (Priority: P1) MVP

**Goal**: Inventory every project skill, identify trigger or convention drift, and produce required rewrite evidence before new skills are accepted.

**Independent Test**: Scan `skills/` and `.agents/skills/`, confirm every `SKILL.md` appears exactly once in the inventory, and verify any rewrite has helper use, subagent pressure evidence, and main-agent changed-file review.

### Tests for User Story 1

- [X] T017 [P] [US1] Add skill inventory artifact validation tests for required columns and exact SKILL.md coverage in tests/adapter_contract/test_plugin_surface.py
- [X] T018 [P] [US1] Add baseline skill pressure scenarios for existing tutor and Speckit trigger boundaries in tests/fixtures/text_modalities/skill_pressure.json
- [X] T019 [P] [US1] Add audit artifact structure tests for rewrite evidence, unavailable helper/reference blocked decisions, and coherence audit decisions in tests/unit/test_skill_suite_audit_artifacts.py

### Implementation for User Story 1

- [X] T020 [US1] Populate the complete SKILL.md inventory from skills/ and .agents/skills/ in specs/005-text-modalities/skill-inventory.md
- [X] T021 [US1] Dispatch subagent baseline pressure review for existing skills and record RED evidence in specs/005-text-modalities/skill-rewrite-evidence.md
- [X] T022 [US1] Rewrite any non-compliant existing tutor skill through its assigned subagent using the local writing-skills helper in skills/tutor-setup/SKILL.md, skills/tutor-vocab/SKILL.md, skills/tutor-writing/SKILL.md, and skills/tutor-progress/SKILL.md
- [X] T023 [US1] Rewrite any non-compliant active Speckit skill through its assigned subagent using the local writing-skills helper in .agents/skills/speckit-analyze/SKILL.md, .agents/skills/speckit-checklist/SKILL.md, .agents/skills/speckit-clarify/SKILL.md, .agents/skills/speckit-constitution/SKILL.md, .agents/skills/speckit-implement/SKILL.md, .agents/skills/speckit-plan/SKILL.md, .agents/skills/speckit-specify/SKILL.md, .agents/skills/speckit-tasks/SKILL.md, and .agents/skills/speckit-taskstoissues/SKILL.md
- [X] T024 [US1] Record GREEN and REFACTOR pressure evidence, changed files, and main-agent review for every created or rewritten skill in specs/005-text-modalities/skill-rewrite-evidence.md
- [X] T025 [US1] Update plugin surface expectations for reviewed skill names, descriptions, and trigger boundaries in tests/adapter_contract/test_plugin_surface.py
- [X] T026 [US1] Write the pre-new-skill coherence decision with unresolved overlaps, blockers, and allowed next steps in specs/005-text-modalities/skill-suite-coherence-audit.md

**Checkpoint**: Skill suite is inventoried and any required rewrite evidence exists before `tutor-reading` or `tutor-lesson` is accepted.

---

## Phase 4: User Story 2 - Practice Reading Comprehension (Priority: P2)

**Goal**: Let a learner validate a generated reading passage, answer comprehension questions, receive `FeedbackEnvelope` feedback, and persist safe learning signals.

**Independent Test**: Start reading practice, submit correct and incorrect answers, confirm validated exercise output, feedback wrapper, answer event, safe mistake events, and progress visibility with no new storage path.

### Tests for User Story 2

- [X] T027 [P] [US2] Add reading exercise validation and orchestration unit tests in tests/unit/test_reading.py
- [X] T028 [P] [US2] Add reading start and record CLI contract tests for success and invalid-candidate errors in tests/adapter_contract/test_reading_cli.py
- [X] T029 [P] [US2] Add reading JSON round-trip and schema mirror assertions in tests/adapter_contract/test_cli_json_contract.py
- [X] T030 [P] [US2] Add reading terminal rendering golden tests for 1200-character exercise and 900-character feedback budgets in tests/golden/test_text_modality_rendering.py
- [X] T031 [P] [US2] Add reading completed, invalid-generation, empty, abandoned, off-topic, and mixed-language integration tests in tests/integration/test_text_modality_flow.py
- [X] T032 [P] [US2] Add three representative reading semantic-eval fixtures in tests/fixtures/text_modalities/reading.json
- [X] T033 [P] [US2] Add tutor-reading skill pressure baseline scenarios before skill creation in tests/fixtures/text_modalities/skill_pressure.json

### Implementation for User Story 2

- [X] T034 [US2] Implement reading comprehension start and record orchestration in src/language_tutor/reading.py
- [X] T035 [US2] Add `reading start` and `reading record` Click commands with documented error envelopes in src/language_tutor/cli.py
- [X] T036 [US2] Wire reading answer persistence and safe mistake counts through text-modality repository helpers in src/language_tutor/dal/repositories.py
- [X] T037 [US2] Make completed reading attempts visible to aggregate progress and session analysis inputs in src/language_tutor/progress.py
- [X] T038 [US2] Export reading exercise and reading result schemas in schemas/reading_exercise.schema.json and schemas/reading_result.schema.json
- [X] T039 [US2] Create the tutor-reading skill through an assigned subagent using the local writing-skills helper in skills/tutor-reading/SKILL.md
- [X] T040 [US2] Add a tutor-reading script only if it matches the existing thin skill-script pattern in skills/tutor-reading/scripts/run.py
- [X] T041 [US2] Record tutor-reading RED/GREEN/REFACTOR evidence and main-agent changed-file review in specs/005-text-modalities/skill-rewrite-evidence.md
- [X] T042 [US2] Add reading semantic-eval threshold assertions for 5 live runs per fixture in tests/semantic/test_text_modality_feedback.py and tests/adapter_contract/test_evaluator_semantic_thresholds.py

**Checkpoint**: Reading comprehension is independently usable from CLI and skill surfaces.

---

## Phase 5: User Story 3 - Complete Guided Micro-Lessons (Priority: P2)

**Goal**: Let a learner request one focused micro-lesson for a weak tag or chosen topic, complete practice, receive `FeedbackEnvelope` feedback, and persist safe learning signals.

**Independent Test**: Start a weak-tag or selected-topic lesson, complete the practice step, confirm focus is bounded, feedback is wrapped, and progress receives safe lesson signals.

### Tests for User Story 3

- [X] T043 [P] [US3] Add micro-lesson validation, focus-selection, and orchestration unit tests in tests/unit/test_lessons.py
- [X] T044 [P] [US3] Add lesson start and record CLI contract tests for weak-tag and selected-topic flows in tests/adapter_contract/test_lesson_cli.py
- [X] T045 [P] [US3] Add lesson JSON round-trip and schema mirror assertions in tests/adapter_contract/test_cli_json_contract.py
- [X] T046 [P] [US3] Add lesson terminal rendering golden tests for bounded lesson output and feedback budgets in tests/golden/test_text_modality_rendering.py
- [X] T047 [P] [US3] Add lesson completed, no-weak-tag fallback, invalid-generation, and abandoned-response integration tests in tests/integration/test_text_modality_flow.py
- [X] T048 [P] [US3] Add three representative lesson semantic-eval fixtures in tests/fixtures/text_modalities/lesson.json
- [X] T049 [P] [US3] Add tutor-lesson skill pressure baseline scenarios before skill creation in tests/fixtures/text_modalities/skill_pressure.json

### Implementation for User Story 3

- [X] T050 [US3] Implement guided micro-lesson start and record orchestration in src/language_tutor/lessons.py
- [X] T051 [US3] Add `lesson start` and `lesson record` Click commands with documented error envelopes in src/language_tutor/cli.py
- [X] T052 [US3] Wire lesson answer persistence and safe mistake counts through text-modality repository helpers in src/language_tutor/dal/repositories.py
- [X] T053 [US3] Make completed lesson attempts visible to aggregate progress and session analysis inputs in src/language_tutor/progress.py
- [X] T054 [US3] Export lesson exercise and lesson result schemas in schemas/lesson_exercise.schema.json and schemas/lesson_result.schema.json
- [X] T055 [US3] Create the tutor-lesson skill through an assigned subagent using the local writing-skills helper in skills/tutor-lesson/SKILL.md
- [X] T056 [US3] Add a tutor-lesson script only if it matches the existing thin skill-script pattern in skills/tutor-lesson/scripts/run.py
- [X] T057 [US3] Record tutor-lesson RED/GREEN/REFACTOR evidence and main-agent changed-file review in specs/005-text-modalities/skill-rewrite-evidence.md
- [X] T058 [US3] Add lesson semantic-eval threshold assertions for 5 live runs per fixture in tests/semantic/test_text_modality_feedback.py and tests/adapter_contract/test_evaluator_semantic_thresholds.py

**Checkpoint**: Guided micro-lessons are independently usable from CLI and skill surfaces.

---

## Phase 6: User Story 4 - Run Text-Based Transcript Drills (Priority: P3)

**Goal**: Provide transcript drills as a text-only `tutor-reading` submode with no audio, no new skill, and safe progress signals.

**Independent Test**: Start a transcript drill through reading mode, submit reconstruction/correction/comprehension response, confirm feedback compares intended meaning, stores `skill=reading` with `modality=transcript`, and never implies audio support.

### Tests for User Story 4

- [X] T059 [P] [US4] Add transcript drill validation and reading-submode unit tests in tests/unit/test_reading.py
- [X] T060 [P] [US4] Add transcript start and record CLI contract tests under the reading command group in tests/adapter_contract/test_reading_cli.py
- [X] T061 [P] [US4] Add transcript JSON round-trip and stored skill assertions in tests/adapter_contract/test_cli_json_contract.py
- [X] T062 [P] [US4] Add transcript terminal rendering golden tests with explicit text-only guardrails in tests/golden/test_text_modality_rendering.py
- [X] T063 [P] [US4] Add transcript completed, empty, off-topic, and no-audio-scope integration tests in tests/integration/test_text_modality_flow.py
- [X] T064 [P] [US4] Add local data ownership regression tests proving transcript drills use `skill=reading` and no new table in tests/integration/test_local_data_ownership.py
- [X] T065 [P] [US4] Add three representative transcript semantic-eval fixtures in tests/fixtures/text_modalities/transcript.json

### Implementation for User Story 4

- [X] T066 [US4] Implement transcript drill validation and start/record orchestration as a reading submode in src/language_tutor/reading.py
- [X] T067 [US4] Wire `mode=transcript` through `reading start` and `reading record` while storing answer events as `skill=reading` in src/language_tutor/cli.py
- [X] T068 [US4] Export transcript drill schema in schemas/transcript_drill.schema.json
- [X] T069 [US4] Update tutor-reading for transcript submode through its assigned subagent using the local writing-skills helper in skills/tutor-reading/SKILL.md
- [X] T070 [US4] Record transcript-submode pressure evidence and main-agent changed-file review in specs/005-text-modalities/skill-rewrite-evidence.md
- [X] T071 [US4] Add transcript semantic-eval threshold assertions for 5 live runs per fixture in tests/semantic/test_text_modality_feedback.py and tests/adapter_contract/test_evaluator_semantic_thresholds.py

**Checkpoint**: Transcript drills work as text-only reading submode and are independently testable.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Finish docs, schema mirrors, final audit, dogfood evidence, and verification gates.

- [X] T072 [P] Update architecture and feature documentation for text-only reading, lesson, transcript scope, and no new persistence in docs/ARCHITECTURE.md and docs/FEATURES.md
- [X] T073 [P] Update project pitfalls and roadmap notes for Phase 5 scope guardrails in docs/PITFALLS.md and docs/ROADMAP.md
- [X] T074 [P] Regenerate and verify JSON schema mirrors in schemas/text_modality_result.schema.json, schemas/text_modality_record.schema.json, schemas/reading_exercise.schema.json, schemas/reading_result.schema.json, schemas/lesson_exercise.schema.json, schemas/lesson_result.schema.json, and schemas/transcript_drill.schema.json
- [X] T075 Complete final skill-suite coherence audit after tutor-reading and tutor-lesson are added in specs/005-text-modalities/skill-suite-coherence-audit.md
- [X] T076 Record dogfood session evidence for tutor-reading, tutor-lesson, and transcript drill in specs/005-text-modalities/quickstart.md
- [X] T077 [P] Run unit verification gate for tests/unit/test_text_modalities.py, tests/unit/test_schemas.py, tests/unit/test_repositories.py, tests/unit/test_progress.py, tests/unit/test_reading.py, and tests/unit/test_lessons.py
- [X] T078 [P] Run golden, adapter-contract, integration, migration, semantic-eval, pyright, and ruff gates covering tests/golden/test_text_modality_rendering.py, tests/golden/test_feedback_rendering.py, tests/golden/test_progress_rendering.py, tests/adapter_contract/test_reading_cli.py, tests/adapter_contract/test_lesson_cli.py, tests/adapter_contract/test_cli_json_contract.py, tests/adapter_contract/test_evaluator_contract.py, tests/adapter_contract/test_evaluator_semantic_thresholds.py, tests/integration/test_text_modality_flow.py, tests/integration/test_progress_flow.py, tests/integration/test_local_data_ownership.py, tests/migration/test_migrations.py, tests/semantic/test_text_modality_feedback.py, pyright, and ruff
- [X] T079 Review SOLID, DRY, KISS, YAGNI, SoC, composition, Demeter, local-first data ownership, and scope guardrails in specs/005-text-modalities/skill-suite-coherence-audit.md

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies.
- **Foundational (Phase 2)**: Depends on Setup and blocks all text-modality stories.
- **US1 (Phase 3)**: Depends on Foundational and blocks new skill acceptance.
- **US2 and US3 (Phases 4-5)**: Depend on Foundational and US1. They can proceed in parallel after skill-suite gate passes because they use separate core modules and skill files.
- **US4 (Phase 6)**: Depends on US2 because transcript is a `tutor-reading` submode.
- **Polish (Phase 7)**: Depends on selected story scope completion.

### User Story Dependencies

- **US1 (P1)**: First MVP increment. No dependency on text modality implementation.
- **US2 (P2)**: Requires shared text-modality foundation and accepted skill-suite audit.
- **US3 (P2)**: Requires shared text-modality foundation and accepted skill-suite audit.
- **US4 (P3)**: Requires reading command group and `tutor-reading` skill from US2.

### Within Each User Story

- Tests and pressure baselines must be written before implementation.
- Skill pressure RED evidence must exist before editing any `SKILL.md`.
- Pydantic/JSON contracts before CLI and repository integration.
- Core orchestration before CLI wiring.
- Persistence helpers before progress aggregation.
- Skill changed-file review before story checkpoint acceptance.
- Semantic-eval fixtures before live threshold assertions.

---

## Parallel Execution Examples

### User Story 1

```bash
# Parallel after Phase 2:
Task: "T017 Add skill inventory artifact validation tests in tests/adapter_contract/test_plugin_surface.py"
Task: "T018 Add baseline skill pressure scenarios in tests/fixtures/text_modalities/skill_pressure.json"
Task: "T019 Add audit artifact structure tests in tests/unit/test_skill_suite_audit_artifacts.py"
```

### User Story 2

```bash
# Parallel before reading implementation:
Task: "T027 Add reading unit tests in tests/unit/test_reading.py"
Task: "T028 Add reading CLI contract tests in tests/adapter_contract/test_reading_cli.py"
Task: "T030 Add reading golden tests in tests/golden/test_text_modality_rendering.py"
Task: "T032 Add reading semantic fixtures in tests/fixtures/text_modalities/reading.json"
```

### User Story 3

```bash
# Parallel before lesson implementation:
Task: "T043 Add lesson unit tests in tests/unit/test_lessons.py"
Task: "T044 Add lesson CLI contract tests in tests/adapter_contract/test_lesson_cli.py"
Task: "T046 Add lesson golden tests in tests/golden/test_text_modality_rendering.py"
Task: "T048 Add lesson semantic fixtures in tests/fixtures/text_modalities/lesson.json"
```

### User Story 4

```bash
# Parallel before transcript implementation:
Task: "T059 Add transcript unit tests in tests/unit/test_reading.py"
Task: "T060 Add transcript CLI contract tests in tests/adapter_contract/test_reading_cli.py"
Task: "T064 Add local data ownership regression tests in tests/integration/test_local_data_ownership.py"
Task: "T065 Add transcript semantic fixtures in tests/fixtures/text_modalities/transcript.json"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1 setup.
2. Complete Phase 2 shared foundation.
3. Complete Phase 3 skill-suite inventory and coherence gate.
4. Stop and validate that every existing `SKILL.md` is inventoried exactly once and any rewrite has required evidence.

### Incremental Delivery

1. Deliver reading comprehension (US2) after MVP gate.
2. Deliver guided micro-lessons (US3) in parallel with or after US2.
3. Deliver transcript drills (US4) after `tutor-reading` exists.
4. Finish final coherence audit, dogfood evidence, and full verification gates.

### Suggested MVP Scope

MVP is US1 plus the shared foundation needed to prove the skill-suite gate. This satisfies the highest-priority requirement and prevents new skills from being accepted before existing skill boundaries are known.
