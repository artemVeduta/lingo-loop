# Data Model: language-tutor v1

## Ownership Rules

YAML owns only user-editable profile and preference fields. SQLite owns transactional and derived learner state. The same field must not be stored in both places unless the plan names a one-way cache, and v1 has no planned caches.

## YAML Entities

### LearnerProfile

Human-editable language-learning identity.

**Fields**: `schema_version`, `native_language`, `target_language`, `level_target`, `interests`, `constraints`, `created_at`, `updated_at`.

**Validation**: `native_language` and `target_language` are required; `level_target` defaults to a documented beginner-safe value; interests and constraints default to empty lists; unknown fields warn or fail according to schema policy.

**Relationships**: Read by boot context, setup, vocab prompt generation, writing prompt generation, evaluator instructions, and renderer localization.

### LearnerPreferences

Human-editable session and feedback choices.

**Fields**: `schema_version`, `session_length`, `review_intensity`, `feedback_verbosity`, `transliteration_tolerance`, `ascii_fallback`, `streak_grace_days`, `updated_at`.

**Validation**: Numeric values are bounded; enum values are closed; transliteration tolerance defaults to false for Cyrillic target languages unless edited.

**Relationships**: Read by session planning, vocab queue sizing, vocab answer comparison, feedback rendering, progress, and boot context.

## SQLite Entities

### LifecycleEvent

Append-only record of canonical tutor lifecycle events.

**Fields**: `id`, `session_id`, `event_type`, `payload_json`, `occurred_at`, `source`.

**Validation**: `event_type` is a closed enum; payload validates against the event contract before insert.

**Relationships**: Links setup, boot, answer, feedback, analysis, persistence, and session-end events.

### VocabularyItem

Target-language recall unit.

**Fields**: `id`, `target_language`, `prompt`, `lemma`, `accepted_answers_json`, `hint`, `tags_json`, `state`, `ease_factor`, `repetition_count`, `interval_days`, `due_at`, `created_at`, `updated_at`.

**Validation**: Accepted answers are non-empty; `ease_factor >= 1.3`; interval and repetition count are non-negative; dedupe key uses target language plus normalized lemma/prompt where available.

**State transitions**: `new -> learning -> review -> mature`; `review|mature -> relearning` on lapse.

### VocabularyReview

Recorded answer attempt and SRS decision for one vocabulary item.

**Fields**: `id`, `session_id`, `vocabulary_item_id`, `answer_event_id`, `verdict`, `quality`, `previous_state_json`, `next_state_json`, `reviewed_at`.

**Validation**: One review per graded answer event; quality is 0-5; next state is produced by the SM-2 function exactly once.

**Relationships**: Belongs to one `VocabularyItem` and one `AnswerEvent`.

### AnswerEvent

Append-only record that the learner answered an exercise.

**Fields**: `id`, `session_id`, `skill`, `prompt_ref`, `learner_answer`, `outcome`, `feedback_envelope_json`, `recorded_at`.

**Validation**: `skill` is closed (`vocab`, `writing` for v1); `feedback_envelope_json` validates before persistence when present.

**Relationships**: Parent for vocabulary reviews and mistake events.

### MistakeEvent

Structured record of a writing or vocabulary issue.

**Fields**: `id`, `session_id`, `answer_event_id`, `skill`, `span_start`, `span_end`, `span_text`, `severity`, `tag`, `explanation`, `confidence`, `created_at`.

**Validation**: Span bounds must be valid when exact spans are available; `tag` must be in the frozen `ErrorTag` vocabulary; `confidence` is a closed enum (`high`, `medium`, `low`); low confidence cannot render as a definitive high-severity correction.

**Relationships**: Aggregated into weak-pattern summaries and progress; writing mistake events do not mutate vocabulary schedules by default.

### SessionSummary

End-of-session recap and next-session handoff.

**Fields**: `id`, `session_id`, `summary_for_user`, `summary_for_next_boot`, `weak_tags_json`, `next_focus`, `cost_snapshot_json`, `created_at`.

**Validation**: Summary text is bounded; `summary_for_next_boot` fits the 6,000-character boot-context budget; weak tags are controlled vocabulary values.

**Relationships**: Read by boot context and progress.

### SessionAnalysis

Validated analyzer output before summary persistence.

**Fields**: `session_id`, `severity_counts_json`, `new_tags_json`, `repeated_tags_json`, `resolved_tags_json`, `next_focus`, `summary_for_next_boot`, `confidence`, `created_at`.

**Validation**: Analyzer JSON is rejected before persistence when malformed, contradictory, over budget, or unsupported by known events.

**Relationships**: Produces `SessionSummary` and skill metrics.

### SkillMetric

Aggregated learning and operational metric.

**Fields**: `id`, `metric_date`, `metric_name`, `metric_value`, `dimensions_json`, `created_at`.

**Validation**: Metric names are closed for v1: streak, due count, item maturity, weak pattern count, token usage, month-to-date estimated USD cost, and cost status (`available`, `partial`, `unavailable`).

**Relationships**: Read by progress and boot-context status.

### CostEvent

Append-only model-cost record for host-provided evaluator or analyzer calls.

**Fields**: `id`, `session_id`, `operation`, `model`, `input_tokens`, `output_tokens`, `cache_read_tokens`, `estimated_cost_usd`, `pricing_source`, `source_event_id`, `created_at`.

**Validation**: Token counts are non-negative; `operation` is closed for v1 (`writing_evaluator`, `session_analyzer`); `estimated_cost_usd` is optional and must be non-negative when present; `pricing_source` records `host_usage_metadata`, `local_pricing_table`, or `unavailable`; missing cost estimates are reported as unavailable instead of inferred.

**Relationships**: Aggregated into month-to-date progress.

### MigrationRecord

Applied SQLite migration marker.

**Fields**: `version`, `name`, `checksum`, `applied_at`.

**Validation**: Versions apply once and in order.

## Contract Entities

### BootContext

Concise session-start state derived from profile, preferences, due reviews, weak patterns, latest recap, and status metrics.

**Validation**: Deterministic ordering, 6,000 rendered-character maximum, no raw event dump, stable output for identical state.

### FeedbackEnvelope

Structured correction package for vocab and writing.

**Fields**: verdict, corrected answer, error spans, severity, controlled tags, confidence (`high`, `medium`, `low`), native-language explanation, optional next-drill hint, optional SRS update.

**Validation**: Tags are controlled; explanations use learner native language; target-language forms remain in target language; unsupported or contradictory output is retried or downgraded before rendering/persistence.

### ErrorTag

Frozen v1 controlled vocabulary.

**Initial groups**: case, aspect, agreement, animacy, verbs of motion, punctuation, interference, vocabulary, spelling, word order, uncategorized.

**Validation**: Unknown tags coerce to `UNCATEGORIZED` only through explicit evaluator fallback logic and are logged.
