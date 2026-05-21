# Research: Vocab Depth

## Decision: Keep Phase 2 inside the existing `tutor vocab` surface

**Rationale**: Manual add, seed import, filtered drills, cloze review, and history are all vocabulary workflows. Extending the existing CLI group and `tutor-vocab` skill keeps user intent coherent and preserves the current host-independent boundary.

**Alternatives considered**: A new `tutor-deck` command was rejected because it would split one responsibility across two user-facing surfaces. A new host skill was rejected because there is no host-specific behavior in Phase 2.

## Decision: Use stdlib JSON for seed import

**Rationale**: Seed lists need safe local parsing, validation, and helpful errors. JSON keeps import files human-editable enough for Phase 2 while avoiding a conflict with the constitution rule that YAML contains only profile and preference fields. No new dependency is required.

**Alternatives considered**: YAML was rejected because the constitution restricts YAML to profile and preference ownership. PyYAML was rejected as redundant.

## Decision: Define duplicate identity as card type plus normalized content

**Rationale**: The spec requires duplicate identity from card type, normalized target or hidden answer, and normalized prompt or context, excluding metadata. A shared normalizer keeps manual add, seed import, repository uniqueness, and tests aligned.

**Alternatives considered**: Including tags, notes, source, accepted-answer variants, or import file path was rejected because those fields are mutable metadata. Keeping the Phase 1 `target_language:lemma/prompt` key was rejected because it does not distinguish cloze cards and does not match the clarified identity rule.

## Decision: Apply seed imports with entry-level transactions

**Rationale**: Per-entry atomicity satisfies the spec: valid entries persist, invalid entries do not block unrelated valid entries, and interrupted entries leave no partial card state. The repository should validate one card, upsert or merge it inside one transaction, then return an entry result.

**Alternatives considered**: One transaction for the entire file was rejected because one malformed entry would block unrelated valid cards. Non-transactional row-by-row writes were rejected because interrupted entries could leave partial metadata or orphaned history.

## Decision: Store tags on the card contract and normalize through one helper

**Rationale**: Existing cards already carry `tags_json`. Phase 2 needs inclusive tag filtering, tag normalization, and clear empty-state reporting. A single normalization helper plus repository filtering is sufficient for the local single-learner scope.

**Alternatives considered**: A separate tag table was rejected for Phase 2 because it duplicates the tag source of truth and adds migration/query complexity before scale demands it. Free-form unnormalized tags were rejected because case, spacing, and punctuation variants must match consistently.

## Decision: Model cloze as a vocabulary card type, not a new exercise subsystem

**Rationale**: Cloze cards share accepted-answer comparison, feedback, SM-2 scheduling, and review recording with standard vocabulary cards. The only new behavior is validation and rendering of a prompt containing exactly one `{{answer}}` marker.

**Alternatives considered**: A separate cloze table or skill was rejected as over-engineering. Treating cloze as a special prompt string without `card_type` was rejected because duplicate identity and renderer behavior need an explicit contract.

## Decision: Build review history from existing reviews and answer events

**Rationale**: `vocabulary_reviews` already records each attempt, verdict, quality, previous state, next state, and time. Joining to `answer_events` provides learner answer and feedback context. A new audit log would duplicate history.

**Alternatives considered**: Persisting a denormalized history snapshot was rejected because it creates drift risk. Showing only aggregate counts was rejected because the spec requires chronological attempt detail.

## Decision: Export new JSON schema mirrors for changed vocabulary contracts

**Rationale**: The constitution requires Pydantic models and JSON schema mirrors for changed contract surfaces. New schemas should cover card definitions, import summaries, session plans with filters, and review history.

**Alternatives considered**: Document-only contracts were rejected because CLI, skill, and tests need machine-checkable boundaries.
