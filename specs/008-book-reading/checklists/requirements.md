# Specification Quality Checklist: tutor-book (Book-Reading Companion)

**Purpose**: Acceptance checklist for the 008 feature — one bullet per success criterion
from the design doc plus the contract-test gates.
**Created**: 2026-06-22
**Feature**: [spec.md](../spec.md)
**Design**: [docs/superpowers/specs/2026-06-22-tutor-book-reading-design.md](../../docs/superpowers/specs/2026-06-22-tutor-book-reading-design.md)

## Success Criteria (from design doc)

- [ ] SC-1: A book session row + its lookups survive an abrupt CLI close (incremental
  persistence via `book record`; no shutdown hook needed).
- [ ] SC-2: Looking up the same word in N different books creates exactly ONE SRS vocab
  card (global dedup by `standard:<word>:<word>`, word set as `lemma`); each subsequent
  book is merged into the card via `import_vocabulary_item`.
- [ ] SC-3: `book log` returns lookups ordered by `created_at` ascending, stable across
  calls.
- [ ] SC-4: `book resume` finds an open book session by normalized title even after the
  originating tutor session is closed (book sessions are independent of tutor sessions).
- [ ] SC-5: `book record` on a `closed` book session is rejected with
  `book_session_closed`; no lookup is persisted.
- [ ] SC-6: A `word` lookup with a missing or echoed translation is still logged (lookup
  row persists, `vocab_item_id` NULL) and creates no SRS card.

## Contract-Test Gates

- [ ] `tests/installer/test_skill_payload_contract.py` — the 5 skill-payload contract
  tests pass (canonical `skills/` tree matches `SKILL_FILES`, `tutor-book` frontmatter
  is exactly `{name, description}`, body uses console `tutor` not `bin/tutor`).
- [ ] `tests/unit/test_skill_suite_audit_artifacts.py` — the skill-suite audit artifact
  tests pass with the inventory bumped to 8 tutor skills and the `tutor-book` row added.
- [ ] `tests/migration/test_005_book_lookups.py` — 005 applies cleanly on top of 004;
  the `checkpoints` rebuild preserves schema/rows/indexes, accepts the new `book`
  modality + `answer_recorded` step_kind, and an injected mid-rebuild failure rolls back
  atomically.
- [ ] `tests/unit/test_book.py`, `tests/integration/test_book_flow.py`,
  `tests/golden/test_book_rendering.py` — the book CLI/core/DAL/rendering contract
  tests pass (Package B scope).

## Notes

- The success criteria are technology-agnostic outcomes; the contract-test gates name
  the concrete test files that enforce them.
- The 7 skill-pressure scenarios ([skill-pressure-scenarios.md](../skill-pressure-scenarios.md))
  are the RED→GREEN evidence for the `tutor-book` SKILL.md authoring gate
  (constitution VIII); they are reviewed alongside this checklist, not as success
  criteria themselves.
