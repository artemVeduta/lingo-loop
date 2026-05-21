# Feature Specification: Vocab Depth

**Feature Branch**: `002-vocab-depth`

**Created**: 2026-05-21

**Status**: Draft

**Input**: User description: "Phase 2 from docs/ROADMAP.md: Vocab Depth. Deepen the existing SRS loop with manual card add, seed-word lists, per-card review history, tag-filtered drills, and cloze card type. No host dependency."

## Clarifications

### Session 2026-05-21

- Q: What should define stable duplicate identity for vocabulary cards across manual add and seed import? → A: Card type, normalized target or hidden answer, and normalized prompt or context; metadata excluded.
- Q: Which local seed-word list format should be canonical for Phase 2 imports? → A: JSON `.json` file containing a list of card objects.
- Q: How should seed-list cloze cards mark the hidden answer in sentence context? → A: Sentence contains exactly one `{{answer}}` marker.
- Q: When a seed import matches an existing card, how should mutable metadata updates behave? → A: Merge additive metadata; never remove existing values.
- Q: What atomicity should seed imports guarantee when a file is partially invalid or interrupted? → A: Per-entry atomic: valid entries persist; invalid or interrupted entries do not.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Build a Personal Vocabulary Deck (Priority: P1)

A learner can add individual vocabulary cards during daily study and import a local seed-word list to start or expand a personal deck without creating duplicates or losing prior review history.

**Why this priority**: Phase 2 must let the learner build and own a useful deck instead of relying only on generated or pre-existing vocabulary.

**Independent Test**: Can be tested on a learner profile with no vocabulary by adding one card manually, importing a seed list, rerunning the same import, and confirming the deck contains the expected cards exactly once with review history preserved.

**Acceptance Scenarios**:

1. **Given** a learner wants to save a target-language word, **When** they provide the required card fields and optional tags, **Then** the tutor adds a drillable card and confirms what was saved.
2. **Given** a local seed-word list contains valid cards, **When** the learner imports it, **Then** the tutor creates missing cards, reports created/skipped/updated/error counts, and makes imported cards available for drills.
3. **Given** the same seed-word list is imported again, **When** no card content changed, **Then** the tutor creates no duplicates and does not reset review history.
4. **Given** a seed-word list changes a card already known to the tutor, **When** the learner imports it again, **Then** the tutor merges additive user-visible metadata without creating a second card, deleting existing metadata, or deleting review attempts.

---

### User Story 2 - Run Focused Tag Drills (Priority: P1)

A learner can drill only the cards that match a chosen tag, while the tutor still respects due-first practice and normal answer feedback.

**Why this priority**: Focused drills make the existing SRS loop more useful for weak topics, custom decks, and exam-focused study.

**Independent Test**: Can be tested by creating cards with multiple tags, starting a drill for one tag, answering due and new cards, and confirming every shown card matches the requested tag and records a normal review result.

**Acceptance Scenarios**:

1. **Given** cards exist with tags for topic, source, or weak area, **When** the learner starts a drill for one tag, **Then** only eligible cards with that tag are shown.
2. **Given** both due and not-yet-due cards match the tag, **When** the learner starts a tag-filtered drill, **Then** due matching cards appear before optional new matching cards.
3. **Given** no due cards match the chosen tag, **When** the learner starts a filtered drill, **Then** the tutor clearly explains whether matching cards exist but are not due, or whether no cards use that tag.
4. **Given** a learner answers a filtered drill prompt, **When** the tutor records the result, **Then** the same feedback, review scheduling, and history rules apply as in unfiltered vocabulary practice.

---

### User Story 3 - Practice Cloze Cards (Priority: P1)

A learner can create and review cloze cards where the target word or phrase is hidden inside sentence context, then receive the same correction and scheduling behavior as other vocabulary cards.

**Why this priority**: Cloze practice deepens recall from isolated word lookup into usage in context, which is central to "Vocab Depth."

**Independent Test**: Can be tested by adding cloze cards manually and through a seed list, drilling them, answering correctly and incorrectly, and confirming the hidden answer, context, feedback, and review history behave consistently.

**Acceptance Scenarios**:

1. **Given** a learner adds a cloze card with a sentence and hidden answer, **When** the card is saved, **Then** future drills show the sentence context with the answer omitted.
2. **Given** a cloze card is due, **When** the learner answers it, **Then** the tutor reveals the full sentence, accepted answer, verdict, and next review outcome.
3. **Given** a seed-word list includes cloze cards, **When** the learner imports it, **Then** valid cloze cards are imported and invalid cloze entries are reported without blocking unrelated valid cards.

---

### User Story 4 - Inspect Per-Card Review History (Priority: P2)

A learner can inspect the complete review history for a vocabulary card to understand how often it was missed, when it was last reviewed, and when it is expected again.

**Why this priority**: Review history builds trust in the scheduler and helps the learner diagnose persistent memory problems without adding dashboards.

**Independent Test**: Can be tested by reviewing one card several times with different outcomes, opening its history, and confirming attempts, outcomes, timing, and next due status match recorded practice.

**Acceptance Scenarios**:

1. **Given** a card has prior reviews, **When** the learner opens that card's history, **Then** the tutor shows each review attempt in order with answer outcome, reviewed time, and resulting review status.
2. **Given** a card has never been reviewed, **When** the learner opens its history, **Then** the tutor shows that it is new and indicates whether it is eligible for practice.
3. **Given** a card has many review attempts, **When** the learner opens its history, **Then** JSON output includes every attempt in chronological order and rendered text remains readable by summarizing long histories while preserving access to complete JSON detail.

### Edge Cases

- Manual card add is missing required target term, prompt, accepted answer, or cloze blank.
- Manual add or seed import repeats an existing card with different capitalization, whitespace, punctuation, or tag order.
- Seed-word list is malformed, partially valid, empty, or contains unsupported card types.
- Seed import is interrupted before all entries are processed; entries already committed as valid persist, while the interrupted entry leaves no partial card state.
- A tag filter matches cards that are not due today.
- A tag name differs only by case, spacing, or punctuation.
- A cloze prompt contains no `{{answer}}` marker, more than one `{{answer}}` marker, or no accepted answer.
- A card has multiple accepted answers, transliteration variants, or homographs.
- A learner deletes or edits the original seed-word list after import.
- Existing vocabulary data was created before Phase 2 and has no tags or card type metadata.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST allow a learner to manually add a vocabulary card with target-language content, a prompt, at least one accepted answer, optional notes, optional source metadata, optional tags, and a card type.
- **FR-002**: System MUST validate manual card input before saving and show repair-oriented feedback for missing required fields, empty accepted-answer lists, unsupported card types, invalid cloze marker counts, or empty tag/source metadata.
- **FR-003**: System MUST assign each card a stable duplicate identity from card type, normalized target-language content or hidden answer, and normalized prompt or sentence context; notes, source, tags, and accepted-answer variants MUST NOT affect duplicate identity.
- **FR-004**: System MUST reject duplicate manual cards by default and explain which existing card already matches.
- **FR-005**: System MUST import learner-provided seed-word lists from a canonical human-editable JSON `.json` file containing a list of card objects.
- **FR-006**: System MUST make seed-list import idempotent: repeating the same import MUST NOT duplicate cards, reset review state, or create extra review history.
- **FR-007**: System MUST report seed-list import results with counts for created, updated, skipped, and invalid entries, plus enough detail for the learner to repair invalid entries.
- **FR-008**: System MUST allow imported cards to carry the same user-visible fields as manually added cards, including tags and card type.
- **FR-009**: System MUST preserve existing review history whenever an imported or manually added card matches an existing card.
- **FR-009a**: System MUST merge additive mutable metadata for matching imported cards, including notes, source values, tags, and accepted answers, and MUST NOT remove existing metadata values during import.
- **FR-010**: System MUST allow learners to start a vocabulary drill filtered by one or more card tags.
- **FR-011**: System MUST ensure tag-filtered drills show only cards matching the selected tag filter.
- **FR-012**: System MUST keep existing due-first vocabulary behavior inside tag-filtered drills.
- **FR-013**: System MUST clearly distinguish "no cards match this tag" from "matching cards exist but none are due."
- **FR-014**: System MUST support a cloze card type where the learner sees sentence context with the answer hidden and submits the missing target word or phrase.
- **FR-015**: System MUST validate cloze cards for a visible context containing exactly one `{{answer}}` marker and at least one accepted answer.
- **FR-016**: System MUST apply the same answer feedback, review scheduling, and review recording rules to cloze cards as to other vocabulary cards.
- **FR-017**: System MUST show the complete sentence context and accepted answer after a cloze answer is graded.
- **FR-018**: System MUST provide a per-card review history view showing prior attempts, outcomes, reviewed times, and current due status.
- **FR-019**: System MUST show useful review-history output for both new cards with no attempts and cards with many attempts; JSON output MUST remain complete, while rendered text MAY summarize long histories for readability.
- **FR-020**: System MUST keep all Phase 2 vocabulary workflows local-first and host-independent.
- **FR-021**: System MUST avoid changing writing feedback, progress dashboards, host adapters, cloud sync, gamification, audio, or any scheduling algorithm beyond using the existing vocabulary review behavior for new card sources and card types.
- **FR-022**: System MUST process seed imports with per-entry atomicity so each valid entry persists after a successful entry-level validation/update transaction, while failed validation, partial import errors, or interrupted entries do not leave incomplete cards, duplicate cards, or orphaned review history.

### Requirement Details

- Manual add and seed import MUST share the same card field names and optionality: `card_type` defaults to `standard`; `target`, `prompt`, and non-empty `accepted_answers` are required; `hint`, `notes`, `source`, and `tags` are optional; unknown fields are rejected with a repair hint.
- Repair-oriented feedback MUST include a stable error code, human-readable message, repair hint, and field or entry index when the issue is field-specific or seed-entry-specific.
- Import statuses are defined as follows: `created` means a new duplicate identity was stored; `updated` means an existing card received at least one additive metadata or accepted-answer value; `skipped` means the matching card already contained all supplied additive values; `invalid` means the entry failed validation and made no state change.
- Duplicate normalization MUST apply Unicode NFKC, `casefold`, trim and collapse whitespace, normalize apostrophe variants (`'`, `’`, `‘`, `ʼ`, `＇`) to ASCII `'`, and trim leading/trailing Unicode punctuation characters. Internal punctuation is preserved so distinct homographs or prompt contexts are not over-merged.
- Tag normalization MUST use the shared normalization helper, reject empty normalized tags, collapse duplicate selected filters, and treat multiple selected tags as inclusive OR.
- Seed files are import inputs only. Editing or deleting a seed file after import MUST NOT mutate stored tutor state.
- Seed import exception and recovery flows MUST distinguish malformed JSON, non-list top-level JSON, empty lists, unsupported fields, invalid entries, interrupted entries, and unreadable or non-`.json` paths.
- Existing Phase 1 vocabulary rows MUST migrate to `standard` card type with empty additive metadata, recalculated duplicate identity, and preserved review rows and answer events.
- Review history ordering MUST be chronological by `reviewed_at`, then stable review id for timestamp ties. Missing answer-event links MUST render the attempt with unavailable answer detail instead of hiding the review.
- Review history JSON MUST remain complete for 500 attempts and the rendered text MAY summarize long histories while preserving newest and oldest context.
- Existing unfiltered `vocab start` and `vocab answer` workflows are baseline regression requirements for Phase 2 and MUST stay covered by adapter-contract and integration tests.

### Key Entities *(include if feature involves data)*

- **Vocabulary Card**: A learner-owned drill unit with target-language content, prompt, accepted answers, optional notes/source metadata/tags, card type, duplicate identity, and review state. Input uses singular `source`; stored cards keep normalized additive source values.
- **Seed Word List**: A learner-provided JSON `.json` local import source containing one or more vocabulary card definitions as a list of card objects. It is not the canonical learning record after import.
- **Card Tag**: A learner-visible label used to group cards for focused drills and review.
- **Cloze Card**: A vocabulary card whose prompt hides a target word or phrase inside sentence context defined by exactly one `{{answer}}` marker.
- **Review Attempt**: A recorded learner answer for one card, including outcome, time reviewed, and resulting review state.
- **Review History**: The chronological audit trail of review attempts for one vocabulary card.
- **Drill Filter**: The learner's selected constraint for a practice session, such as one or more tags.

## Constitution Alignment *(mandatory)*

- **Affected Layers**: User-facing vocabulary skill, vocabulary core, SRS selection boundary, local data repositories, migrations, contract schemas, and deterministic text renderers. Host adapters remain out of scope except for continuing to invoke the existing tutor command surface.
- **Data Ownership**: Human-editable profile and preferences remain separate from learning history. Seed-word lists are import inputs only, not canonical tutor state. Vocabulary cards, review attempts, scheduling state, import outcomes, and card history belong to local transactional learning state.
- **Contract Surfaces**: Card definition contract, seed-list import contract, card duplicate identity rules, drill-filter contract, cloze-card contract, review-history contract, command result JSON, schema mirrors, and local state migration.
- **Required Validation**: Unit tests for card validation, duplicate identity, tag filtering, cloze validation, and review-history ordering; golden tests for drill prompts, import summaries, cloze feedback, and review-history text; contract tests for command inputs/outputs; integration tests for manual add, idempotent import, filtered drills, cloze review, and review history; migration tests for existing vocabulary data.
- **Scope Guardrails**: Phase 2 deepens vocabulary only. It does not add new hosts, new learning modalities, dashboards, gamification, cloud sync, multi-user support, audio, writing evaluator changes, bundled curricula, or a new scheduling algorithm.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A learner can manually add a valid vocabulary card and start drilling it in under 2 minutes.
- **SC-002**: Re-importing an unchanged seed-word list produces zero duplicate cards and preserves review history in 100% of acceptance fixtures.
- **SC-003**: Tag-filtered drills show only cards matching the selected tag filter in 100% of deterministic drill-selection fixtures.
- **SC-004**: Cloze cards produce the same visible feedback, review recording, and next-review decision as standard vocabulary cards in 100% of cloze review fixtures.
- **SC-005**: Per-card review history JSON opens in under 2 seconds for a card with 500 recorded attempts and contains every attempt in chronological order.
- **SC-006**: Import summaries identify created, updated, skipped, and invalid entries with 100% accurate counts in seed-list fixtures.
- **SC-007**: A learner can build and drill a custom Slavic vocabulary deck end-to-end, using manual add, seed import, tags, cloze cards, and review history, in under 10 minutes.
- **SC-008**: Existing vocabulary practice without tags or cloze cards continues to complete with no user-visible behavior regression in existing acceptance tests.

## Assumptions

- Phase 1 vocabulary practice, review scheduling, local storage, and tutor command surface already exist and remain the baseline.
- The learner is a single local user who can provide or edit seed-word lists on disk.
- Seed-word lists may be human-editable local JSON files, but the canonical tutor record after import is the local learning state, not the source file.
- Tags are learner-visible labels supplied during manual add or seed import; weak-pattern targeting remains a later phase.
- Tag filtering is inclusive: a card matches when it has at least one selected tag.
- Cloze cards hide one intended answer per card in Phase 2.
- Existing vocabulary cards without explicit card type are treated as standard recall cards.
- No host-specific behavior is needed for Phase 2.
