# CLI JSON Contract

`bin/tutor` is the stable boundary used by hooks, skills, tests, and contributors. Commands write JSON to stdout for machine-readable operations and exit non-zero only for actionable failures.

## Global Rules

- Output JSON is UTF-8, schema-validated, and deterministic for identical input/state.
- Errors use `{ "error": { "code": "...", "message": "...", "repair_hint": "..." } }`.
- Commands that mutate state perform exactly one transaction and return the committed record id or summary.
- Commands must not read or write data outside platformdirs-resolved config/data/state paths unless an explicit test path is provided.

## Commands

### `tutor doctor --json`

Checks runtime, plugin registration, data paths, migrations, schema health, and defined setup failure fixtures.

**Output**: `DoctorReport` with per-area status for Python runtime, `bin/tutor` executability, plugin manifest, hooks, skills, agent file, config/data/state path permissions, profile/preferences YAML schema validation, SQLite connectivity, migration checksum/order, package data inclusion, and whether learner data changed (`false` unless an explicit repair command is added later).

### `tutor setup read --json`

Loads current profile/preferences or defaults.

**Output**: `SetupState`.

### `tutor setup write --json <payload>`

Validates and writes profile/preferences YAML without touching learning history.

**Input**: `LearnerProfile` plus `LearnerPreferences`.

**Output**: `SetupWriteResult`.

### `tutor boot-context --json`

Builds session-start learner context from local state.

**Output**: `BootContext`.

### `tutor render boot-context --json <payload>`

Renders a validated `BootContext` as markdown-style host text.

**Output**: `{ "markdown": "..." }`.

### `tutor vocab start --json`

Returns due queue and optional starter-content request metadata. Starter-content candidates accepted by the core must declare target language, level target, prompt, accepted-answer forms, learner-constraint fit, weak-pattern or interest rationale, and normalized duplicate key before queueing.

**Output**: `VocabularySessionPlan`.

### `tutor vocab answer --json <payload>`

Records one vocabulary answer, evaluates against accepted answers, applies SM-2 exactly once, and returns feedback.

**Input**: `VocabularyAnswerInput`.

**Output**: `VocabularyAnswerResult` containing `FeedbackEnvelope`, `AnswerEvent`, and `VocabularyReview`.

### `tutor writing prompt --json`

Returns a writing prompt or prompt choices with explicit fit metadata for target language, level target, interests, and learner constraints. If no candidate satisfies those rules, the response must allow learner-provided passage entry without pretending a prompt was selected.

**Output**: `WritingPromptResult`.

### `tutor writing record --json <payload>`

Validates judge output, records answer/mistakes, and returns the validated or downgraded feedback.

**Input**: `WritingRecordInput` containing learner answer and candidate `FeedbackEnvelope`.

**Output**: `WritingRecordResult`.

### `tutor render feedback --json <payload>`

Renders a validated feedback envelope.

**Output**: `{ "markdown": "...", "ascii_markdown": "..." }`.

### `tutor progress --json`

Returns streak, due counts, weak patterns, item maturity, latest recap, month-to-date estimated USD cost, and cost status (`available`, `partial`, or `unavailable`).

**Output**: `ProgressReport`.

### `tutor session-end --json`

Handles SessionEnd analysis input and persists validated summary/cost/metrics. Cost input comes from host-provided usage metadata for evaluator/analyzer calls: operation, model, non-negative token counts, optional estimated USD cost, pricing source, and source event id. It is safe to run asynchronously and must not block host shutdown on non-critical analyzer failure. If analysis is interrupted or rejected, persisted lifecycle events remain intact and the result status is `pending`.

**Output**: `SessionEndResult`.

## Contract Tests

- Invalid YAML returns repair-oriented error and does not mutate SQLite.
- Vocabulary answer comparison applies transliteration tolerance only when enabled in preferences.
- Duplicate `vocab answer` calls with same idempotency key do not double-apply SRS.
- Same DB/profile state produces byte-identical `boot-context` JSON and rendered markdown.
- Unsupported evaluator tags are rejected or downgraded before persistence.
- Starter vocabulary content missing required declarations or conflicting with profile constraints is rejected before queueing.
- Doctor reports actionable failures for missing plugin files, invalid YAML, migration drift, unreadable data paths, and corrupt local databases without mutating learner data.
- Plugin and CLI discovery expose setup, vocabulary, writing, and progress as distinct learner intents.
