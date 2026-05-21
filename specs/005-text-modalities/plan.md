# Implementation Plan: Text Modalities + Skill Authoring

**Branch**: `005-text-modalities` | **Date**: 2026-05-21 | **Spec**: `specs/005-text-modalities/spec.md`

**Input**: Feature specification from `specs/005-text-modalities/spec.md`

**Note**: This file is the `/speckit-plan` output. Phase 2 task generation is intentionally deferred to `/speckit-tasks`.

## Summary

Add Phase 5 text-only practice by first auditing the full project skill suite, then adding reading comprehension, guided micro-lessons, and transcript drills as host-independent CLI/skill flows. The implementation keeps generated teaching content provisional until validated by Python contracts, embeds the existing `FeedbackEnvelope` unchanged inside modality-specific result wrappers, records safe mistake events through existing SQLite tables, and exposes completed attempts to existing progress/session analysis without a new persistence path. Audio, images, dashboards, host adapters, new schedulers, and new storage are explicitly excluded.

## Technical Context

**Language/Version**: Python 3.12+ with the existing synchronous core.

**Primary Dependencies**: Existing runtime dependencies only: Click for `bin/tutor`, Pydantic v2 for contracts and schema export, ruamel.yaml for profile/preferences, platformdirs for local paths, and stdlib `sqlite3`/`json`/`datetime`/`hashlib`/`textwrap` for local state, deterministic IDs, validation, and rendering guards. Dev tooling remains pytest, syrupy, freezegun, pytest-cov, pyright, ruff, hatchling, uv, and pre-commit. Skill-authoring work depends on the existing local helper at `/Users/artem.veduta/.claude/plugins/cache/claude-plugins-official/superpowers/5.1.0/skills/writing-skills` plus the active external skill-authoring references named by the constitution.

**Storage**: Existing SQLite remains the canonical transactional/derived store for `answer_events`, `mistake_events`, `session_summaries`, `vocabulary_reviews`, cost events, and progress inputs. YAML remains human-editable profile/preferences only. Reading, lesson, and transcript attempts are stored as existing answer/mistake/session signals with expanded validated skill values and prompt references; exercise bodies, answer keys, and audit evidence are not added as new runtime persistence. Skill inventory and rewrite evidence are repository design artifacts under `specs/005-text-modalities/`, not learner state.

**Testing**: pytest for unit, contract, integration, migration, and CLI tests; syrupy for deterministic terminal rendering/golden output; freezegun or injected clocks for timestamps and deterministic IDs; pyright and ruff for static gates. Semantic evals are required for reading, lesson, and transcript feedback: 3 fixtures per modality, 5 live runs per fixture, schema-valid 5/5, expected verdict/rubric 4/5, required tags preserved across the run set, and zero unsafe definitive corrections.

**Target Platform**: macOS and Linux local plugin runtime. Host-independent text CLI and skill surfaces only; no Claude-specific adapter changes and no new host capabilities.

**Project Type**: Local Python package plus skill-driven CLI surface. This feature changes Python core/contracts/renderers/DAL repository methods, CLI command groups, JSON schema mirrors, project skills, and feature evidence docs.

**Performance Goals**: Generated exercise rendering must stay at or below 1200 rendered characters. Generated feedback rendering must stay at or below 900 rendered characters. Validation should be bounded by candidate payload size and suitable for terminal use; no unbounded prompt/rubric traversal. Existing progress generation keeps the Phase 4 under-5-second one-year fixture gate after adding text-modality signals.

**Constraints**: `FeedbackEnvelope` remains unchanged. Reading, lesson, and transcript feedback is embedded in modality-specific wrappers. Invalid generated exercises get one repair/regeneration attempt before a clear learner-facing refusal. Transcript practice is a `tutor-reading` text-only submode, not an audio feature and not a third skill. No audio playback, speech recognition, image modality, GUI/web/dashboard surface, host adapter, host-capability abstraction, cloud sync, multi-user behavior, gamification, bundled curriculum, FSRS, or new scheduling algorithm is introduced.

**Scale/Scope**: Single local learner, two new learner-facing skills (`tutor-reading`, `tutor-lesson`), transcript drill as reading submode, one exercise attempt at a time, existing local state only. Existing inventory currently covers 4 tutor skills under `skills/` and 9 Speckit skills under `.agents/skills/`; implementation must inventory all existing skills exactly once before accepting new skills, then re-run coherence after adding the new skills.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Layered boundaries**: PASS. Affected layers are skills, CLI command surfaces, Pydantic contracts/schema mirrors, text exercise validation/orchestration, feedback rendering guards, evaluator/judge contract docs, repository write helpers for existing answer/mistake tables, session analysis/progress signal ingestion, and tests. Host adapters remain out of scope. Cross-layer calls stay skill -> CLI, CLI -> core, core -> repository/renderer.
- **Contracts and abstractions**: PASS. New data crosses boundaries through Pydantic models, JSON schema mirrors, documented CLI JSON, and narrow repository helpers. `FeedbackEnvelope` is embedded unchanged; no catch-all dictionary or concrete DAL detail leaks into skills or renderers.
- **Deterministic tests**: PASS. Required coverage includes unit tests for generated exercise validation, size budgets, answer/rubric shape, one-repair refusal, safe response classification, mistake-event mapping, and progress signal aggregation; golden tests for reading/lesson/transcript terminal rendering; contract tests for CLI JSON, result wrappers, schema export, and feedback embedding; integration tests for completed, abandoned, empty, off-topic, mixed-language, invalid-generation, and transcript flows; semantic-eval suites for all three feedback paths.
- **Skill creation gate**: PASS. The feature changes project skills. Implementation must inventory all `SKILL.md` files, then use a subagent per skill or coherent skill family for every creation/rewrite. Each subagent must read the local `writing-skills` helper, apply the external references required by the active spec, report changed files, and produce RED/GREEN/REFACTOR pressure evidence. Main agent review of every reported changed file is required before acceptance.
- **Local-first data ownership**: PASS. SQLite owns completed attempts, feedback-derived answer events, mistake events, session summaries, and progress inputs. YAML remains profile/preferences only. No cloud, telemetry, remote state, host-owned learner data, or new runtime persistence is introduced.
- **Scope discipline**: PASS. Work is limited to roadmap Phase 5 text modalities and skill-suite quality. The plan rejects audio, image, dashboards, host-capability abstraction, new hosts, new persistence, new scheduler behavior, gamification, bundled curriculum, cloud sync, multi-user behavior, and unrelated progress redesign.
- **DRY and composition**: PASS. Shared output budgets, validation guards, modality names, feedback wrapper rules, mistake mapping, tag normalization, and rendering guardrails are single-source helpers/contracts. Behavior is composed through small core functions and repository helpers, not inheritance, service locators, or global mutable state.

## Project Structure

### Documentation (this feature)

```text
specs/005-text-modalities/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── skill-suite-audit.md
│   ├── text-modality-cli.md
│   ├── text-modality-json.md
│   └── semantic-eval.md
├── skill-inventory.md              # planned implementation evidence
├── skill-rewrite-evidence.md        # planned only if rewrites occur
├── skill-suite-coherence-audit.md   # planned implementation evidence
└── tasks.md                         # Generated by /speckit-tasks
```

### Source Code (repository root)

```text
skills/
├── tutor-reading/
│   ├── SKILL.md
│   └── scripts/
│       └── run.py                   # if existing skill script pattern needs it
├── tutor-lesson/
│   ├── SKILL.md
│   └── scripts/
│       └── run.py                   # if existing skill script pattern needs it
├── tutor-setup/
├── tutor-vocab/
├── tutor-writing/
└── tutor-progress/

.agents/skills/
└── speckit-*/SKILL.md               # inventory only unless audit finds drift

src/language_tutor/
├── cli.py                           # reading/lesson command groups and render wiring
├── feedback.py                      # existing sanitize/render helpers; budget checks reuse renderer
├── reading.py                       # reading comprehension and transcript drill orchestration
├── lessons.py                       # guided micro-lesson orchestration
├── text_modalities.py               # shared size, repair/refusal, wrapper, and safe-signal helpers
├── progress.py                      # include text-modality answer totals and safe mistake signals
├── progress_rendering.py            # render added text-modality progress fields if contract expands
├── schemas.py                       # Pydantic contracts and schema export mapping
└── dal/
    └── repositories.py              # narrow helpers over existing answer_events/mistake_events

schemas/
├── reading_exercise.schema.json
├── reading_result.schema.json
├── lesson_exercise.schema.json
├── lesson_result.schema.json
├── transcript_drill.schema.json
├── text_modality_result.schema.json
├── text_modality_record.schema.json
├── progress_report.schema.json      # updated if practice totals expand
└── answer_event.schema.json         # updated skill values

tests/
├── adapter_contract/
│   ├── test_reading_cli.py
│   ├── test_lesson_cli.py
│   ├── test_cli_json_contract.py
│   └── test_evaluator_semantic_thresholds.py
├── fixtures/
│   └── text_modalities/
├── golden/
│   ├── test_text_modality_rendering.py
│   └── snapshots/
├── integration/
│   └── test_text_modality_flow.py
├── migration/
│   └── test_migrations.py
├── semantic/
│   └── test_text_modality_feedback.py
└── unit/
    ├── test_text_modalities.py
    ├── test_reading.py
    ├── test_lessons.py
    ├── test_repositories.py
    ├── test_progress.py
    └── test_schemas.py
```

**Structure Decision**: Extend the existing single Python package and skill layout. Keep reading comprehension and transcript submodes in `reading.py`, micro-lessons in `lessons.py`, and shared validation/result-wrapper logic in `text_modalities.py`. Use `schemas.py` as the Pydantic and JSON-schema source of truth, repository helpers only for existing local tables, and skills as thin orchestration over CLI commands plus LLM candidate generation. A new service package, persisted exercise table, host adapter, dashboard, content curriculum bundle, or separate transcript skill is rejected because Phase 5 can be implemented through existing text contracts and local signals.

## Phase 0: Research

**Output**: `specs/005-text-modalities/research.md`

All technical-context unknowns are resolved:

- Skill inventory is a deterministic repository artifact, not runtime data. The inventory lists every `SKILL.md` under `skills/` and `.agents/skills/` once with path, purpose, trigger scope, progressive disclosure status, CLI/contract convention status, compliance decision, and required evidence.
- Skill creation/rewrite evidence uses the local `writing-skills` helper that exists at `/Users/artem.veduta/.claude/plugins/cache/claude-plugins-official/superpowers/5.1.0/skills/writing-skills`, plus the active external references required by the constitution. If any required reference is unavailable during implementation, the affected rewrite is blocked or explicitly documented as blocked.
- Reading, lesson, and transcript generated content is host-provided candidate JSON that must pass CLI/core validation before use. The CLI does not trust generated prose directly; it validates modality, level fit, answerability/rubric presence, learner-facing instructions, scope guardrails, and rendered character budgets.
- Feedback remains a `FeedbackEnvelope` generated by the judge/evaluator path and then validated/sanitized by the CLI before persistence. Result wrappers add modality metadata, scoring metadata, response summary, and exercise/rubric references without modifying `FeedbackEnvelope`.
- Existing SQLite tables are sufficient. `answer_events.skill` and Pydantic literals expand to include `reading` and `lesson`; transcript uses skill `reading` plus result modality `transcript`. `mistake_events.skill` stores the same values. No new runtime table is planned.
- Progress visibility is achieved by extending existing practice totals and using existing `mistake_events` and `session_summaries`. Safe mistake events from reading, lesson, and transcript attempts enter the same progress mastery evidence as writing mistakes.
- Invalid generated exercises retry/repair once. After the second failure, the CLI returns a validated refusal result with no answer event, no mistake event, and a clear learner-facing repair hint.
- Empty, abandoned, off-topic, or mixed-language responses are represented as explicit record outcomes. They may produce feedback and answer events when learner-safe, but must not emit taggable mistake events unless validated feedback contains safe, confidence-compatible spans.

## Phase 1: Design And Contracts

**Output**:

- `specs/005-text-modalities/data-model.md`
- `specs/005-text-modalities/contracts/skill-suite-audit.md`
- `specs/005-text-modalities/contracts/text-modality-cli.md`
- `specs/005-text-modalities/contracts/text-modality-json.md`
- `specs/005-text-modalities/contracts/semantic-eval.md`
- `specs/005-text-modalities/quickstart.md`
- `AGENTS.md` Speckit plan reference

Design decisions:

- `SkillInventoryRecord`, `SkillRewriteEvidence`, and `SkillSuiteCoherenceAudit` are planning/evidence artifacts. They do not enter runtime storage and are reviewed before new skills are accepted.
- `TextExerciseCandidate` is the common candidate envelope for generated reading, lesson, and transcript content. It carries modality, learner fit, rendered instructions, prompt material, answer key or rubric summary, tags, and source kind.
- `ReadingExercise`, `MicroLesson`, and `TranscriptDrill` are validated exercise models derived from candidate JSON. Reading owns transcript as `mode:"transcript"` so the learner-facing skill remains `tutor-reading`.
- `TextModalityRecordInput` accepts exercise metadata, learner response summary/raw response as currently required by existing answer event behavior, candidate `FeedbackEnvelope`, scoring metadata, session ID, and optional idempotency key.
- `TextModalityResult` is the canonical result wrapper for reading/lesson/transcript attempts. It embeds `FeedbackEnvelope`, reports persisted answer/mistake counts, preserves modality metadata, and includes scope guardrails. It never changes `FeedbackEnvelope`.
- `AnswerEvent.skill` expands from `vocab|writing` to `vocab|writing|reading|lesson`. Transcript drills use `reading` for `AnswerEvent.skill` and `transcript` for result modality. Progress and contract tests must prove existing vocab/writing consumers still substitute.
- Repository additions are narrow: validate idempotency, record a text-modality answer in `answer_events`, and insert safe mistake events using the existing `mistake_events` schema. Repository code does not generate exercises, score pedagogy, or render output.
- CLI additions follow current conventions: `bin/tutor reading start --json '<payload>'`, `bin/tutor reading record --json '<payload>'`, `bin/tutor lesson start --json '<payload>'`, and `bin/tutor lesson record --json '<payload>'`. `reading start` accepts `mode:"comprehension"` or `mode:"transcript"`.
- Rendering uses existing feedback rendering plus modality-specific deterministic wrappers. Golden tests enforce exercise output <= 1200 rendered chars and feedback output <= 900 rendered chars.
- Skill scripts remain optional. If existing script conventions help keep skills thin, use `scripts/run.py`; otherwise skills may call `bin/tutor` directly like current tutor skills.

## Post-Design Constitution Check

- **Layered boundaries**: PASS. Design keeps host adapters untouched and separates skill orchestration, CLI validation, core text-modality logic, repository persistence, progress aggregation, and deterministic rendering.
- **Contracts and abstractions**: PASS. Data model and contract docs define Pydantic/JSON/CLI surfaces before implementation. Existing storage is reached only through narrow repository helpers.
- **Deterministic tests**: PASS. Quickstart and contracts identify unit, golden, contract, integration, migration/no-migration, progress, skill-pressure, and semantic-eval gates.
- **Skill creation gate**: PASS. Skill inventory, helper use, external references, subagent pressure evidence, activation/description review, and main-agent changed-file review are explicit preconditions before skill changes are accepted.
- **Local-first data ownership**: PASS. Attempts and safe signals use existing local SQLite tables; YAML stays profile/preferences; evidence docs live in the repo, not learner state.
- **Scope discipline**: PASS. Design excludes audio, image, GUI/web/dashboard, new hosts, host capability abstraction, new persistence, new scheduler behavior, gamification, bundled curriculum, cloud sync, and multi-user behavior.
- **DRY and composition**: PASS. Shared validation budgets, modality literals, wrapper contracts, safe mistake mapping, rendering guards, and progress signal mapping are single-source helpers/contracts composed by reading, lessons, CLI, and repository code.

## Verification Gates

```bash
rtk uv run pytest tests/unit/test_text_modalities.py tests/unit/test_reading.py tests/unit/test_lessons.py tests/unit/test_schemas.py tests/unit/test_repositories.py
rtk uv run pytest tests/golden/test_text_modality_rendering.py tests/golden/test_feedback_rendering.py tests/golden/test_progress_rendering.py
rtk uv run pytest tests/adapter_contract/test_reading_cli.py tests/adapter_contract/test_lesson_cli.py tests/adapter_contract/test_cli_json_contract.py tests/adapter_contract/test_evaluator_contract.py
rtk uv run pytest tests/integration/test_text_modality_flow.py tests/integration/test_progress_flow.py tests/integration/test_local_data_ownership.py
rtk uv run pytest tests/migration/test_migrations.py
rtk uv run pytest tests/adapter_contract/test_evaluator_semantic_thresholds.py tests/semantic/test_text_modality_feedback.py
rtk uv run pyright
rtk uv run ruff check .
```

Skill-specific implementation gates:

```bash
rtk rg --files skills .agents/skills
rtk uv run pytest tests/adapter_contract/test_plugin_surface.py
```

The semantic-eval gate MUST run 5 live evaluations per fixture across at least 3 reading, 3 lesson, and 3 transcript fixtures. Each fixture must produce schema-valid feedback in 5/5 runs, expected verdict/rubric outcome in at least 4/5 runs, required tags somewhere in the run set, and no unsafe definitive correction.

## Complexity Tracking

No constitution violations. No complexity exceptions required.
