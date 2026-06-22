# tutor-book: Book-Reading Companion — Design

- **Date:** 2026-06-22
- **Status:** Approved (brainstorming complete; ready for implementation plan)
- **Skill placement:** `skills/tutor-book/SKILL.md` (runtime learner-facing skill, peer of `tutor-reading` / `tutor-vocab` / `tutor-writing` / `tutor-lesson`)
- **CLI placement:** new `tutor book` command group in `src/language_tutor/book.py`, registered in `src/language_tutor/cli.py`

## Goal

A book-reading companion mode for lingo-loop. While the learner reads a book in their target language, they run the `tutor-book` skill to enter a per-book reading session. Within the session they type anything they don't understand — a **word**, a **sentence**, a **passage**, or a **question** — and the agent explains it. Every lookup is persisted to a per-book reading log; looked-up **words** are additionally added to the vocabulary spaced-repetition deck so they reappear for review.

## Non-goals (YAGNI)

- No book file ingestion or parsing (the learner types/pastes what they want explained).
- No page/position tracking.
- No automatic unknown-word extraction from pasted passages.
- No pronunciation/IPA, etymology, or full linguistic profile.
- No comprehension Q&A on generated passages (that is `tutor-reading`).
- No standalone vocab drill loop (that is `tutor-vocab`).

## Architecture & skill surface

### New skill: `skills/tutor-book/SKILL.md`

- `name: tutor-book`
- `description: Use when the learner is reading a book in their target language and wants to look up words, sentences, or passages they don't understand, or ask questions about the text. Looked-up words are saved and added to vocabulary spaced-repetition review. Not for comprehension Q&A on generated passages (use tutor-reading) or standalone vocab drills (use tutor-vocab).`
- Thin orchestrator that runs only `tutor` for stateful work (per the constitution). Ships with a `scripts/run.py` shim identical to the other tutor skills (forwards to the `tutor` binary via `LANGUAGE_TUTOR_TUTOR_BIN`, default `tutor`).

### New CLI command group (`tutor book`)

Implemented in `src/language_tutor/book.py`; registered in `src/language_tutor/cli.py`.

| Command | Purpose |
|---|---|
| `tutor book start` | Create a per-book reading session (title + optional author), linked to the current tutor session. Idempotent: if an open session for this title already exists, returns it. |
| `tutor book record` | Persist a lookup (`kind` ∈ word/sentence/passage/question) with an agent-generated explanation. For `kind:"word"`, also find-or-create an SRS vocab card (deduped globally by target word) and link it. |
| `tutor book resume` | Find an open reading session by title (for resuming in a new conversation). |
| `tutor book log` | Return all lookups for a book session, ordered by `created_at` (for review). |
| `tutor book close` | Mark a reading session `closed`. Only on explicit learner request — the skill never calls it automatically (mirrors the `session-close` guardrail). |

### How it fits

`tutor-book` is a peer modality of `tutor-reading` / `tutor-vocab` / `tutor-writing` / `tutor-lesson`. It reuses:

- `tutor session-start` / `tutor checkpoint` — session lifecycle and per-step persistence
- `srs.py` — the SM-2 spaced-repetition engine (no duplication)
- The vocab module (`vocab.py`) — called **internally** by `tutor book record` to find-or-create cards (DRY; not via the `tutor vocab add` CLI command)

The skill never embeds pedagogy, persistence, rendering, or scoring — all of that lives in validated Python contracts, per the constitution.

### Naming

`tutor-reading` is already taken (comprehension Q&A + transcript drills), so this skill is `tutor-book` — avoids collision and reads naturally as "book-reading companion."

## Data model & persistence

### New migration: `migrations/005_book_lookups.sql`

```sql
CREATE TABLE book_sessions (
  book_session_id  TEXT PRIMARY KEY,                 -- "book_..."
  session_id       TEXT NOT NULL,                    -- links to tutor session (sess_...)
  title            TEXT NOT NULL,
  author           TEXT,
  status           TEXT NOT NULL DEFAULT 'open',     -- 'open' | 'closed'
  started_at       TEXT NOT NULL,                    -- ISO 8601
  closed_at        TEXT
);

CREATE TABLE book_lookups (
  lookup_id        TEXT PRIMARY KEY,                 -- "lookup_..."
  book_session_id  TEXT NOT NULL,
  kind             TEXT NOT NULL,                    -- 'word'|'sentence'|'passage'|'question'
  content          TEXT NOT NULL,                    -- the word/sentence/passage/question
  context          TEXT,                             -- optional surrounding text (words)
  explanation_json TEXT NOT NULL,                    -- JSON blob: {translation, gloss, answer, ...}
  vocab_item_id    TEXT,                             -- linked SRS card (words only)
  created_at       TEXT NOT NULL                     -- ISO 8601
);

CREATE INDEX idx_book_lookups_session ON book_lookups(book_session_id);
CREATE UNIQUE INDEX idx_book_lookups_word ON book_lookups(book_session_id, content) WHERE kind='word';
```

Referential integrity to `sessions(session_id)` and `vocab_items(item_id)` is enforced at the application layer (the repo's existing repositories follow this pattern; SQLite foreign keys are enabled per-connection).

### Dedup strategy

- **Lookups:** deduped per book for words (the unique index on `(book_session_id, content) WHERE kind='word'`). Re-looking-up the same word in the same book returns the existing row. Sentence/passage/question lookups are never deduped (you may ask different questions about the same sentence).
- **SRS cards:** deduped **globally** by target word across the whole vocab deck. Re-reading a word in a second book links to the existing card and adds this book as a `source`, rather than creating a duplicate card.

### SRS feeding (words only)

`tutor book record` with `kind:"word"` calls the vocab module internally to find-or-create a card:

- `target` = the word
- `accepted_answers` = the translation
- `hint` / `notes` = the short gloss
- `tags` = `["from-book", <title-slug>]`
- `sources` += this book (title, author)

Returns `vocab_item_id` so the `book_lookups` row links to the card. The find-or-create + lookup insert run in a single transaction; on failure both roll back.

### Explanation shape per kind

The explanation is **agent-generated** (LLM step) and passed into `tutor book record`. The CLI validates the shape against the kind:

- `word`: `{"translation": "<native-lang>", "gloss": "<short gloss>"}`
- `sentence` / `passage`: `{"translation": "..."}` (or explanation)
- `question`: `{"answer": "..."}`

Rationale: the CLI is deterministic (no LLM access), so it cannot generate explanations. It validates shape + persists + feeds SRS. This matches the repo pattern (agent generates content, CLI validates + persists).

### Rendering

Rendering belongs in the CLI (per the constitution), so `tutor book record` returns a pre-rendered `rendered` markdown field alongside the structured result. The agent displays `rendered` directly — no separate `tutor render book-explanation` command needed (KISS; the explanation is just translation + gloss). `tutor book log` likewise includes a `rendered` field per lookup so the agent displays the review list without formatting it.

### New JSON schemas (under `schemas/`)

- `book_session.schema.json` — book session object (id, title, author, status, started_at, closed_at)
- `book_lookup_input.schema.json` — `tutor book record` input (book_session_id, kind, content, context?, explanation)
- `book_lookup_result.schema.json` — `tutor book record` output (lookup_id, vocab_item_id?, deduped, created_at, `rendered`)
- `book_log.schema.json` — `tutor book log` output (ordered list of lookups, each with `rendered`)

Referenced by the skill ("do not guess fields"); validated by pydantic models in `src/language_tutor/schemas.py`.

## Data flow

### Start (first message of a reading conversation)

1. `tutor session-start --json '{"host":"<host>"}'` → `session_id`
2. `tutor book start --json '{"session_id":"sess_...","title":"...","author":"..."}'` → `book_session_id` (idempotent on open title)
3. `tutor checkpoint --json '{"session_id":"...","modality":"book","step_kind":"prompt_shown","summary":"Started reading <title>","state":{"book_session_id":"...","title":"..."}}'`
4. Tell the learner the reading session is ready.

### Lookup loop (each learner input)

1. Learner types a word / sentence / passage / question (optionally with context).
2. Agent generates the explanation (translation + gloss for words; translation for sentence/passage; answer for questions).
3. `tutor book record --json '{"book_session_id":"...","kind":"word","content":"esquivo","context":"...","explanation":{"translation":"...","gloss":"..."}}'` → `{lookup_id, vocab_item_id?, deduped, created_at, rendered}`
4. `tutor checkpoint --json '{"session_id":"...","modality":"book","step_kind":"answer_recorded","summary":"Looked up 'esquivo'","state":{"book_session_id":"...","lookup_id":"...","kind":"word"}}'`
5. Display the `rendered` markdown returned by `tutor book record` to the learner.

### Resume (new conversation, same book)

1. `tutor session-start --json '{"host":"..."}'` → new `session_id`
2. `tutor book resume --json '{"title":"..."}'` → finds the most recent open book session for this title → `book_session_id`
3. Continue the lookup loop (new `session_id` for checkpoints, same `book_session_id` for records).

### Review log (learner asks "what have I looked up?")

- `tutor book log --json '{"book_session_id":"..."}'` → all lookups ordered by `created_at`; agent renders the list.

### Close (only on explicit learner request)

- `tutor book close --json '{"book_session_id":"..."}'` → `status='closed'`. The skill never calls this automatically.

## Error handling

Deterministic JSON error envelopes matching the repo's existing `{"error": {...}}` contract:

- **`book start`**: title required non-empty; `session_id` must exist and be `open`; idempotent on re-start for the same open title (returns existing).
- **`book record`**: `kind` ∈ {word, sentence, passage, question}; `content` non-empty; explanation fields must match the kind (word requires `translation` + `gloss`); word dedup returns the existing row; SRS card find-or-create + lookup insert are one transaction — on failure both roll back.
- **`book resume`**: no open session for title → `"no open reading session for '<title>'; start one with tutor book start"`.
- **`book log` / `book close`**: `book_session_id` must exist; `close` rejects an already-closed session.
- **All commands**: pydantic + JSON-schema validation; click usage errors; same error envelope shape as existing commands.

## Testing

Follows the repo's spec-driven contract pattern (peer to `specs/005-text-modalities/`):

- **New spec:** `specs/008-book-reading/` with `contracts/` (CLI JSON contracts, migration contracts, schema contracts).
- **Unit tests:** `tests/book/test_record.py`, `test_start.py`, `test_resume.py`, `test_log.py`, `test_close.py`, `test_srs_feeding.py`.
- **DAL tests:** new `BookSessionRepository` + `BookLookupRepository` in `src/language_tutor/dal/`.
- **Migration test:** `005_book_lookups` applies cleanly on top of `004_sessions_checkpoints` and rolls back on error.
- **Skill-suite audit:** `specs/005-text-modalities/skill-inventory.md` + `contracts/skill-suite-audit.md` updated to register `tutor-book`.
- **Constitution gate:** `SKILL.md` creation requires subagent + RED/GREEN/REFACTOR pressure evidence via the local `writing-skills` helper (per `docs/internal/constitution.md:189-194`).

## Implementation note

The user requested parallel agents for the implementation. The work decomposes into independent units (CLI command group, migration + DAL, schemas, skill markdown, tests, spec/contracts) that can be dispatched to parallel subagents once the implementation plan is written.
