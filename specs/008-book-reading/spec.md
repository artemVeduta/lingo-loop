# Feature Specification: tutor-book (Book-Reading Companion)

**Feature Branch**: `vedutaartem20/dig-11-add-tutor-book`

**Created**: 2026-06-22

**Status**: Draft

**Input**: Approved design at
[docs/superpowers/specs/2026-06-22-tutor-book-reading-design.md](../../docs/superpowers/specs/2026-06-22-tutor-book-reading-design.md).
This spec is the concise feature spine; the design doc is the single source of truth
for architecture, data model, error codes, and skill-pressure scenarios — referenced,
not duplicated here.

## Goal

A book-reading companion mode for lingo-loop. While the learner reads a book in their
target language, they run the `tutor-book` skill to enter a per-book reading session.
Within the session they type anything they don't understand — a **word**, a
**sentence**, a **passage**, or a **question** — and the agent explains it. Every lookup
is persisted to a per-book reading log; looked-up **words** are additionally added to
the vocabulary spaced-repetition deck so they reappear for review.

## Non-goals (YAGNI)

- No book file ingestion or parsing (the learner types/pastes what they want explained).
- No page/position tracking.
- No automatic unknown-word extraction from pasted passages.
- No pronunciation/IPA, etymology, or full linguistic profile.
- No comprehension Q&A on generated passages (that is `tutor-reading`).
- No standalone vocab drill loop (that is `tutor-vocab`).

## CLI Commands (6)

Implemented in `src/language_tutor/book.py`; the `@main.group()` and subcommand functions
live in `src/language_tutor/cli.py` (the repo convention — see design doc "CLI placement").
Full input/output/error contracts: [contracts/book-cli.md](contracts/book-cli.md);
JSON shapes: [contracts/book-json.md](contracts/book-json.md).

| Command | Purpose |
|---|---|
| `tutor book start` | Create a per-book reading session (title + optional author), linked to the current tutor session. Idempotent within the current tutor session on `(session_id, normalized_title)` among OPEN sessions. |
| `tutor book record` | Persist a lookup (`kind` ∈ word/sentence/passage/question) with an agent-generated explanation. Always persisted; words additionally feed the SRS deck on a usable, non-echo translation. Rejects `closed` book sessions with `book_session_closed`. |
| `tutor book resume` | Find the most recent OPEN book session by normalized title (for resuming in a new conversation). Tiebreak: `started_at DESC, book_session_id DESC`. Independent of the originating tutor session's status. |
| `tutor book log` | Return all lookups for a book session, ordered by `created_at` ascending (for review). |
| `tutor book list` | Return all book sessions (OPEN first, then CLOSED), newest first, each with `lookup_count`. Called before `resume` to propose books the learner has already started. |
| `tutor book close` | Mark a reading session `closed`. Only on explicit learner request — the skill never calls it automatically (mirrors the `session-close` guardrail). |

## Data Model

New migration `migrations/005_book_lookups.sql` adds two tables and rebuilds
`checkpoints` to accept the new `modality='book'` and `step_kind='answer_recorded'`
values. See the design doc "Data model & persistence" for the full DDL, FK delete
semantics, the `checkpoints` rebuild ordering + atomicity gate, and the dedup
strategy (per-book word-lookup dedup via `content_norm` + global SRS card dedup via
the item dedup key `standard:<word>:<word>`).

- **BookSession**: `book_session_id` (PK, `book_...`), `session_id` (FK → sessions),
  `title`, `title_norm`, `author?`, `status` (`open`|`closed`), `started_at`,
  `closed_at?`. Output schema: `schemas/book_session.schema.json` (`BookSession` in
  `src/language_tutor/schemas.py`).
- **BookLookup**: `lookup_id` (PK, `lookup_...`), `book_session_id` (FK → book_sessions),
  `kind`, `content`, `content_norm?` (word dedup key), `context?`, `explanation_json`,
  `vocab_item_id?` (FK → vocabulary_items `ON DELETE SET NULL`), `created_at`. Input
  schema: `schemas/book_record.schema.json` (`BookRecordInput`); output:
  `schemas/book_lookup_result.schema.json` (`BookLookupResult`) — both in
  `src/language_tutor/schemas.py`.

Referential integrity uses real DDL `REFERENCES` (enforced at runtime via
`PRAGMA foreign_keys=ON`), with belt-and-suspenders app-layer existence checks that
map to friendly CLI-boundary errors.

## Success Criteria

1. A book session row + its lookups survive an abrupt CLI close (incremental
   persistence via `book record`; no shutdown hook needed — constitution principle IX).
2. Looking up the same word in N different books creates exactly ONE SRS vocab card
   (global dedup by `standard:<word>:<word>`, word set as `lemma`); each subsequent
   book is merged into the card via `import_vocabulary_item`.
3. `book log` returns lookups ordered by `created_at` ascending, stable across calls.
4. `book resume` finds an open book session by normalized title even after the
   originating tutor session is closed (book sessions are independent of tutor sessions).
5. `book record` on a `closed` book session is rejected with `book_session_closed`;
   no lookup is persisted.
6. A `word` lookup with a missing or echoed translation is still logged (lookup row
   persists, `vocab_item_id` NULL) and creates no SRS card.

## Constitution Alignment

- **Affected Layers**: core (`book.py` handlers), CLI (`cli.py` `book` group), DAL
  (new `BookRepository` + `vocab.py` nestable-transaction refactor), schemas (pydantic
  `Book*Input`/`BookSession`/`BookLookupResult`/`BookLog`/`BookList` + 5 generated
  `book_*.schema.json`), migration (`005_book_lookups.sql` + `checkpoints` rebuild),
  skills (`skills/tutor-book/SKILL.md`). No renderer-pedagogy change; pedagogy stays
  host-blind.
- **Data Ownership**: SQLite state — new `book_sessions` + `book_lookups` tables; no
  new YAML config. User-owned data MUST NOT be packaged.
- **Contract Surfaces**: Pydantic models + JSON-Schema mirrors for the 5 book payloads;
  CLI JSON contracts for the 6 commands; SQL migration; the new `book` checkpoint
  modality and `answer_recorded` step_kind.
- **Required Validation**: Unit (`tests/unit/test_book.py`), integration
  (`tests/integration/test_book_flow.py`), golden rendering
  (`tests/golden/test_book_rendering.py`), migration
  (`tests/migration/test_005_book_lookups.py`), skill-payload contract
  (`tests/installer/test_skill_payload_contract.py`), skill-suite audit artifacts
  (`tests/unit/test_skill_suite_audit_artifacts.py`).
- **Skill Creation**: One new skill `tutor-book`, authored by a dedicated subagent per
  constitution Principle VIII (read the local `writing-skills` helper, produce
  RED/GREEN/REFACTOR pressure evidence, report changed files). Evidence:
  [skill-rewrite-evidence.md](skill-rewrite-evidence.md).
- **Scope Guardrails**: No book-file ingestion; no page tracking; no automatic
  unknown-word extraction; no automatic book close; no comprehension Q&A on generated
  passages (own-book text only — the `tutor-book` vs `tutor-reading` discriminator).

## Assumptions

- The `tutor session-start` / `tutor checkpoint` lifecycle from `007-hookfree-incremental-lifecycle`
  is already in place and reused unchanged (this feature adds the `book` modality and
  `answer_recorded` step_kind to the `checkpoints` CHECK constraints only).
- The vocab module's `import_vocabulary_item` is refactored to a nestable
  `_import_vocabulary_item_inner` so `book record` can run the find-or-create card +
  lookup insert in one shared transaction.
- The `rendered` field on `BookLookupResult` / `BookLog` is a deliberate, narrowly-scoped
  new result field (ratified in the design doc's orchestrated review), not a reuse of
  an existing embedded-rendered pattern — justified by KISS/YAGNI for a trivial
  deterministic explanation template.
- The skill-inventory total in `specs/005-text-modalities/skill-inventory.md` is already
  stale (the 9-speckit count undercounts). This feature bumps the tutor sub-count
  7 → 8 only and does NOT reconcile the broader drift (out of scope per design doc).
