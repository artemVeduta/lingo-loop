# Data Model: Vocab Depth

## Ownership Rules

Seed JSON files are local import inputs only. SQLite owns vocabulary cards, duplicate identity, review state, review attempts, import outcomes, and history after import. Profile and preference YAML ownership is unchanged.

## Contract Entities

### VocabularyCardDefinition

Shared input model for manual card add and each seed-list entry.

**Fields**: `card_type`, `target`, `prompt`, `accepted_answers`, `hint`, `notes`, `source`, `tags`.

**Validation**:

- `card_type` is `standard` or `cloze`; default may be `standard`.
- `target` is required and non-empty.
- `prompt` is required and non-empty.
- `accepted_answers` is a non-empty list; normalized duplicates are removed.
- `notes`, `source`, and `tags` are optional user-visible metadata and never affect duplicate identity.
- Unknown fields fail validation with a repair hint.

**Relationships**: Parsed by `tutor vocab add` and seed import, converted to a stored `VocabularyItem`, and mirrored as JSON Schema.

### VocabularyDuplicateIdentity

Stable identity used for duplicate detection and idempotent import.

**Fields**: `card_type`, `normalized_target_or_answer`, `normalized_prompt_or_context`, `dedupe_key`.

**Validation**:

- Normalization uses one shared helper: Unicode NFKC, `casefold`, trimmed/collapsed whitespace, normalized apostrophe variants, and trimmed boundary punctuation.
- Apostrophe variants are `'`, `’`, `‘`, `ʼ`, and `＇`; boundary punctuation means leading/trailing characters whose Unicode category starts with `P`; internal punctuation remains significant.
- Metadata fields are excluded.
- Accepted-answer variants are excluded except for the canonical hidden answer or target content.

**Relationships**: Stored as the unique `dedupe_key` for `VocabularyItem`.

### VocabularyDrillRequest

Optional request model for starting vocabulary practice.

**Fields**: `tags`, `requested_count`.

**Validation**:

- `tags` is optional; when present, at least one normalized tag is required.
- Tag filtering is inclusive: a card matches when it has at least one selected tag.
- Empty arrays, empty normalized values, and unsupported payload fields are rejected; duplicate filters collapse by normalized key.
- `requested_count` defaults to the existing preference-derived queue size and remains bounded by preferences.

**Relationships**: Input to `tutor vocab start`; produces a `VocabularySessionPlan`.

### SeedImportRequest

CLI request to import a local seed JSON file.

**Fields**: `path`.

**Validation**:

- Path must point to a readable `.json` file.
- File must contain a JSON list of card objects.
- The import source is not persisted as canonical learning state.

**Relationships**: Input to `tutor vocab import`.

### SeedImportResult

Summary of one import run.

**Fields**: `path`, `created_count`, `updated_count`, `skipped_count`, `invalid_count`, `entries`.

**Validation**:

- Counts equal the number of entry results by status.
- Entry details include index, status, item id when available, and repair hint for invalid entries.
- Results are deterministic for identical file content and existing state.

**Relationships**: Returned by `tutor vocab import` and rendered by `tutor-vocab`.

### VocabularyReviewHistory

Chronological review audit for one card.

**Fields**: `item`, `current_state`, `due_status`, `attempts`.

**Validation**:

- Attempts are ordered by `reviewed_at`, oldest first.
- Attempts with identical `reviewed_at` are ordered by stable review id.
- New cards return an empty `attempts` list and a clear due/new status.
- Cards with many attempts remain bounded in render output while JSON remains complete and chronologically ordered.
- Missing answer-event links are represented as unavailable answer detail rather than dropping the review attempt.

**Relationships**: Built from `vocabulary_items`, `vocabulary_reviews`, and `answer_events`.

## SQLite Entities

### VocabularyItem

Canonical stored vocabulary card. Phase 2 extends the existing Phase 1 table/model.

**Fields**: `id`, `card_type`, `target_language`, `prompt`, `lemma`, `accepted_answers_json`, `hint`, `notes_json`, `sources_json`, `tags_json`, `state`, `ease_factor`, `repetition_count`, `interval_days`, `due_at`, `created_at`, `updated_at`, `dedupe_key`.

**Validation**:

- `card_type` is `standard` or `cloze`; existing rows backfill to `standard`.
- `lemma` continues to hold the target-language content for standard cards and the hidden answer for cloze cards to avoid a broad storage rename in Phase 2.
- `dedupe_key` is unique and generated from `VocabularyDuplicateIdentity`.
- Tags, notes, sources, and accepted answers are stored as normalized JSON arrays with stable ordering.

**State transitions**: Existing SM-2 state transitions remain unchanged: `new -> learning -> review -> mature`, and `review|mature -> relearning` on lapse.

### CardTag

Learner-visible label stored on `VocabularyItem.tags_json`.

**Fields**: display text and normalized key.

**Validation**:

- Empty tags are rejected.
- Case, spacing, and boundary punctuation differences normalize to the same key.
- Display ordering is deterministic.

**Relationships**: Used by `VocabularyDrillRequest`, import metadata merge, and rendered card/history output.

### ClozeCard

Specialized vocabulary card type represented by `VocabularyItem.card_type == "cloze"`.

**Fields**: `prompt` as the sentence context with one `{{answer}}` marker, `lemma` as hidden answer, `accepted_answers_json` as accepted hidden-answer variants.

**Validation**:

- Prompt contains exactly one `{{answer}}` marker.
- Hidden answer is non-empty.
- At least one accepted answer is present.
- Drill prompt hides the answer; feedback reveals the full sentence and accepted answer.

**Relationships**: Uses the same answer comparison, feedback envelope, review record, and SM-2 schedule as standard cards.

### VocabularyReview

Existing review attempt record.

**Fields**: `id`, `session_id`, `vocabulary_item_id`, `answer_event_id`, `verdict`, `quality`, `previous_state_json`, `next_state_json`, `reviewed_at`.

**Validation**: One review per graded answer event; quality remains 0-5; next state is produced by existing scheduling logic exactly once.

**Relationships**: Read by `VocabularyReviewHistory`.

### AnswerEvent

Existing learner answer event.

**Phase 2 change**: Vocabulary answers for standard and cloze cards continue to use `skill == "vocab"` and `prompt_ref == VocabularyItem.id`.

## Migration Notes

`002_vocab_depth.sql` should add the new card metadata columns and backfill existing vocabulary rows:

- `card_type` default `standard`
- `notes_json` default `[]`
- `sources_json` default `[]`
- recalculated `dedupe_key` for the Phase 2 identity rule

The migration must preserve existing review rows and answer events. Migration tests must verify Phase 1 vocabulary practice still starts, answers, and records reviews after migration.
