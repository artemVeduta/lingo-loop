# CLI JSON Contract: Vocab Depth

`bin/tutor` remains the stable host-independent boundary. All commands output UTF-8 JSON and use the existing error envelope:

```json
{"error":{"code":"...","message":"...","repair_hint":"..."}}
```

## Existing Command Extension

### `tutor vocab start --json [payload]`

Starts a vocabulary queue. Without payload, behavior matches Phase 1. With payload, applies an inclusive tag filter.

**Input**: optional `VocabularyDrillRequest`.

```json
{"tags":["exam verbs","weak spelling"],"requested_count":10}
```

**Output**: `VocabularySessionPlan`.

Additional Phase 2 fields may include `filter`, `matching_count`, `due_matching_count`, and an empty-state reason of `no_matching_cards` or `matching_cards_not_due`.

**Rules**:

- Every returned item must match at least one requested tag when tags are supplied.
- Due matching cards appear before optional new matching cards.
- Empty results distinguish no matching cards from matching cards not due.
- Empty tag arrays are rejected. Duplicate filters and normalized tag collisions collapse to one filter. Multiple tags use inclusive OR matching.

### `tutor vocab answer --json <payload>`

Records one standard or cloze answer through the existing answer path.

**Input**: `VocabularyAnswerInput`.

**Output**: `VocabularyAnswerResult`.

**Rules**:

- Standard and cloze cards use the same `FeedbackEnvelope`, SM-2 scheduling, idempotency, and review persistence.
- Cloze feedback reveals the complete sentence and accepted answer after grading.

## New Commands

### `tutor vocab add --json <payload>`

Adds one manual vocabulary card.

**Input**: `VocabularyCardDefinition`.

```json
{
  "card_type": "standard",
  "target": "privit",
  "prompt": "hello",
  "accepted_answers": ["privit"],
  "tags": ["greetings"],
  "notes": ["informal greeting"],
  "source": "manual"
}
```

**Output**: `VocabularyCardAddResult`.

```json
{
  "status": "created",
  "item_id": "vocab_...",
  "duplicate": false,
  "message": "Card created."
}
```

**Rules**:

- Duplicate manual cards are rejected by default with the existing matching card id.
- Manual add does not create review history.
- Required-field errors include repair hints.

### `tutor vocab import --json <payload>`

Imports one local seed JSON file.

**Input**: `SeedImportRequest`.

```json
{"path":"data/seeds/uk-basic.json"}
```

**Output**: `SeedImportResult`.

```json
{
  "path": "data/seeds/uk-basic.json",
  "created_count": 2,
  "updated_count": 1,
  "skipped_count": 4,
  "invalid_count": 1,
  "entries": [
    {"index": 0, "status": "created", "item_id": "vocab_..."},
    {"index": 1, "status": "invalid", "repair_hint": "prompt is required"}
  ]
}
```

**Rules**:

- Each valid entry is committed independently.
- Invalid entries do not block unrelated valid entries.
- Matching entries merge additive metadata and accepted answers.
- Matching entries never reset review state or create review history.

### `tutor vocab history --json <payload>`

Shows review history for one card.

**Input**:

```json
{"item_id":"vocab_..."}
```

**Output**: `VocabularyReviewHistory`.

**Rules**:

- Attempts are chronological.
- Timestamp ties are ordered by stable review id.
- New cards return an empty history with current eligibility.
- Missing cards return a repair-oriented `vocab_card_not_found` error.
- Missing answer-event detail does not hide the review attempt; the attempt marks answer detail as unavailable.

## Contract Tests

- Manual add rejects missing target, prompt, accepted answers, unsupported card type, and invalid cloze marker count.
- Duplicate manual add returns the matching item id and does not mutate review history.
- Seed import reports accurate created, updated, skipped, and invalid counts.
- Re-importing the same seed file creates zero duplicates and preserves review state.
- Tag-filtered start returns only matching cards and preserves due-first ordering.
- Cloze answer output reveals complete sentence after grading.
- History output is chronological and complete for a 500-attempt fixture.
- Existing unfiltered `vocab start` and `vocab answer` contract cases remain in scope as regression coverage.
