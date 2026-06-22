# tutor-book: Book-Reading Companion — Design

- **Date:** 2026-06-22
- **Status:** Approved (brainstorming complete; ready for implementation plan)
- **Revision:** 2026-06-22 — review pass resolved 10 unresolved questions (checkpoint schema, vocab find-or-create, idempotency scope, nested transaction, success criteria, rendering template, schema inventory, closed-session behavior, title normalization, skill pressure scenarios) and added the `tutor book list` command.
- **Revision:** 2026-06-22 (verification pass) — parallel sub-agent audit against the live codebase corrected nine inaccurate claims: real identifiers (`vocabulary_items(id)`, `sessions(id)`, `VocabularyItem.lemma` not `target`, required `id`); real referential-integrity pattern (DDL `REFERENCES` + `PRAGMA foreign_keys=ON`, not app-layer-only); `target_language` resolution is a `cli.py` pattern passed into vocab functions; SRS card built via the existing `VocabularyCardDefinition` → `item_from_definition` path (DRY); schema/test naming aligned to real repo conventions (`_record`/`_result`, by-layer `tests/`); migration rebuild completeness + `REQUIRED_MIGRATION_FILES` registration; constitution citation fixed to Principle VIII (`:133-148`); `rendered` field acknowledged as a deliberate divergence from the `render`-subcommand pattern (following the `progress` inline-markdown precedent).
- **Skill placement:** `skills/tutor-book/SKILL.md` (runtime learner-facing skill, peer of `tutor-reading` / `tutor-vocab` / `tutor-writing` / `tutor-lesson`)
- **CLI placement:** pure handlers in `src/language_tutor/book.py`; the `@main.group()` and its subcommand functions live in `src/language_tutor/cli.py` and import those handlers — the repo convention (e.g. `reading` is registered in `cli.py:849` importing `start_reading`/`record_reading` from `reading.py`). Do **not** put `@main.group()` in `book.py`.

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
- Thin orchestrator that runs only `tutor` for stateful work (per the constitution). Ships with a `scripts/run.py` shim identical to the `tutor-vocab` / `tutor-writing` / `tutor-progress` shims (`tutor-reading` ships none) — forwards to the `tutor` binary via `LANGUAGE_TUTOR_TUTOR_BIN`, default `tutor`.

### New CLI command group (`tutor book`)

Implemented in `src/language_tutor/book.py`; registered in `src/language_tutor/cli.py`.

| Command | Purpose |
|---|---|
| `tutor book start` | Create a per-book reading session (title + optional author), linked to the current tutor session. Idempotent within the current tutor session: if an OPEN `book_sessions` row with the same `(session_id, normalized_title)` already exists, returns it. Across tutor sessions, a new `book start` for an already-open title creates a new book session linked to the new session (use `book resume` to continue an existing one). |
| `tutor book record` | Persist a lookup (`kind` ∈ word/sentence/passage/question) with an agent-generated explanation. For `kind:"word"`, also find-or-create an SRS vocab card (deduped globally by the item dedup key `standard:<word>:<word>`, word set as `lemma` — see Dedup strategy) and link it. Rejects `closed` book sessions with `book_session_closed`. |
| `tutor book resume` | Find the most recent OPEN book session by normalized title (for resuming in a new conversation). Tiebreak: `started_at DESC, book_session_id DESC`. Works regardless of the originating tutor session's status — book sessions are scoped to the learner, not to the tutor session. |
| `tutor book list` | Return all book sessions (OPEN first, then CLOSED), newest first by `started_at DESC, book_session_id DESC`, each with `lookup_count`. The skill calls this before `resume` to propose books the learner has already started. |
| `tutor book log` | Return all lookups for a book session, ordered by `created_at` ascending (for review). |
| `tutor book close` | Mark a reading session `closed`. Only on explicit learner request — the skill never calls it automatically (mirrors the `session-close` guardrail). Closing a book session does NOT close the parent tutor session, and closing a tutor session does NOT close linked book sessions. |

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
  session_id       TEXT NOT NULL REFERENCES sessions(id),  -- links to tutor session
  title            TEXT NOT NULL,
  title_norm       TEXT NOT NULL,                    -- normalize_text(title) for idempotency/resume
  author           TEXT,
  status           TEXT NOT NULL DEFAULT 'open',     -- 'open' | 'closed'
  started_at       TEXT NOT NULL,                    -- ISO 8601
  closed_at        TEXT
);

CREATE INDEX idx_book_sessions_session ON book_sessions(session_id);
CREATE UNIQUE INDEX idx_book_sessions_open_per_session
  ON book_sessions(session_id, title_norm) WHERE status='open';
CREATE INDEX idx_book_sessions_title_norm ON book_sessions(title_norm, started_at DESC);

CREATE TABLE book_lookups (
  lookup_id        TEXT PRIMARY KEY,                 -- "lookup_..."
  book_session_id  TEXT NOT NULL REFERENCES book_sessions(book_session_id),
  kind             TEXT NOT NULL,                    -- 'word'|'sentence'|'passage'|'question'
  content          TEXT NOT NULL,                    -- the word/sentence/passage/question (original, displayed)
  content_norm     TEXT,                             -- normalize_text(content); populated for kind='word' (dedup key)
  context          TEXT,                             -- optional surrounding text (words)
  explanation_json TEXT NOT NULL,                    -- JSON blob: {translation, gloss, answer, ...}
  vocab_item_id    TEXT REFERENCES vocabulary_items(id),  -- linked SRS card (words only)
  created_at       TEXT NOT NULL                     -- ISO 8601
);

CREATE INDEX idx_book_lookups_session ON book_lookups(book_session_id);
-- Word dedup uses the SAME normalization as the SRS card dedup, so "Esquivo" and
-- "esquivo" are one lookup AND one card. content_norm = normalize_text(content).
CREATE UNIQUE INDEX idx_book_lookups_word ON book_lookups(book_session_id, content_norm) WHERE kind='word';
```

The migration also extends the `checkpoints` table CHECK constraints to accept the new modality and step_kind. SQLite cannot `ALTER CHECK`, so the migration rebuilds `checkpoints` (CREATE new with expanded CHECKs, `INSERT INTO ... SELECT ...` from old, DROP old, RENAME new). The rebuilt `checkpoints.modality` CHECK adds `'book'`; the rebuilt `checkpoints.step_kind` CHECK adds `'answer_recorded'`. The rebuild MUST re-declare the full original definition, not just the CHECKs: `id TEXT PRIMARY KEY`, `session_id TEXT NOT NULL REFERENCES sessions(id)`, the `NOT NULL`s on `state_json`/`summary`/`created_at`, and it MUST recreate **both** indexes exactly — `idx_checkpoints_session ON checkpoints(session_id, created_at)` and `idx_checkpoints_created ON checkpoints(created_at)` (`migrations/004_sessions_checkpoints.sql:26-27`). This is the first table-rebuild migration in the repo (002 only `ALTER TABLE ... ADD COLUMN`), so there is no in-repo template to copy.

Atomicity caveat: the runner applies each migration with `conn.executescript(...)` and commits once after the whole loop (`dal/migrations.py:84,94`). `executescript` implicitly commits any pending transaction before running and does **not** roll back partial statements on failure, so a `DROP`/`RENAME` rebuild that fails mid-script could leave `checkpoints` half-destroyed. The 005 script MUST therefore wrap the rebuild in an explicit `BEGIN; ... COMMIT;` inside the SQL so the drop+recreate+copy is one atomic unit. The migration test asserts that an injected mid-rebuild failure leaves the original `checkpoints` (rows + schema) intact.

Registration: `005_book_lookups.sql` MUST be appended to `REQUIRED_MIGRATION_FILES` in `src/language_tutor/package_assets.py:9-14`, or `load_migrations` raises `missing_migrations` when run from the installed package. The runner enforces strict no-gap ordering (`dal/migrations.py:66-73`), so the file must be exactly `005_...`, immediately following `004`.

Referential integrity uses real DDL foreign keys, matching every existing table (`vocabulary_items.id`, `sessions.id`, the `REFERENCES` clauses in `001_initial.sql` / `004_sessions_checkpoints.sql`): `book_sessions.session_id → sessions(id)`, `book_lookups.book_session_id → book_sessions(book_session_id)`, `book_lookups.vocab_item_id → vocabulary_items(id)`. These are enforced at runtime because `connect()` sets `PRAGMA foreign_keys = ON` per connection (`dal/sqlite_store.py:15`). As the existing `record_checkpoint` does (`repositories.py:732-736`), the book repositories ALSO perform an app-layer existence check before insert to return a friendly error envelope rather than a raw FK violation — belt-and-suspenders on top of the DDL FK, not a substitute for it. (Note: the real vocab table is `vocabulary_items` with PK `id` — **not** `vocab_items(item_id)`; the `book_lookups.vocab_item_id` column name is fine but links to `vocabulary_items.id`.)

Python enum changes accompany the migration: `CheckpointModality.BOOK = "book"` and `CheckpointStepKind.ANSWER_RECORDED = "answer_recorded"` in `src/language_tutor/schemas.py`.

### Dedup strategy

- **Lookups:** deduped per book for words (the unique index on `(book_session_id, content_norm) WHERE kind='word'`, where `content_norm = normalize_text(content)` — the same normalization the SRS card uses, so the two dedup levels never disagree). Re-looking-up the same word in the same book returns the existing row. Sentence/passage/question lookups are never deduped (you may ask different questions about the same sentence).

There are **two independent dedup levels**, and they must not be confused:
  - **Per-book lookup dedup** (above) → drives the `deduped` flag in the `book record` result. `deduped:true` means *this normalized word already had a lookup row in this book*.
  - **Global SRS card dedup** (below) → an internal detail of `import_vocabulary_item` (`"created"`/`"updated"`/`"skipped"`). The card may be deduped globally (the word exists from another book) while the lookup is brand-new in this book — in that case `deduped:false` (new lookup) even though no new card was created.
- **SRS cards:** deduped **globally** by target word across the whole vocab deck. The repo's dedup key for a stored item is `dedupe_key_for_item` (`vocab.py:80-81`), which feeds `item.lemma or item.prompt` (not `target` — `VocabularyItem` has no `target` field) into `dedupe_key` (`f"{card_type}:{normalize_text(target)}:{normalize_text(prompt)}"`, `vocab.py:77`). So the card MUST be built with `card_type="standard"` and **`lemma`=word** (with `prompt`=word) to collapse to `standard:<word>:<word>` — one card per word regardless of how many books look it up. Re-reading a word in a second book links to the existing card and merges this book into the card (via `repo.import_vocabulary_item`, the only existing function that merges on a duplicate — it merges `accepted_answers`, `notes`, `sources`, and `tags`, `repositories.py:163-168`; `add_vocab_card` rejects duplicates, `upsert_vocabulary_item` silently returns the existing id without merging).

### SRS feeding (words only)

`tutor book record` with `kind:"word"` calls a new `vocab.py` helper, `find_or_create_vocab_card_for_book`. To stay DRY, the helper does **not** hand-build a `VocabularyItem` (that model has no `target` field, requires an `id`, and takes list-typed `accepted_answers`/`notes` — easy to get wrong). Instead it composes a `VocabularyCardDefinition` and reuses the existing `item_from_definition(definition, target_language, item_id)` constructor (`vocab.py:318-332`), which already maps `definition.target → lemma`, sets `id`, and calls `notes_list()`/`sources_list()`. The definition is:

- `card_type` = `"standard"`
- `target` = the word (→ `VocabularyItem.lemma`, the dedup key component — see Dedup strategy)
- `prompt` = the word
- `accepted_answers` = `[translation]` (a non-empty list; required — guard against an empty translation)
- `hint` = the short gloss; `notes` = `[gloss]`
- `tags` = `["from-book", <title-slug>]`, where `<title-slug>` is the book's `title_norm` with internal whitespace replaced by hyphens (reuse the already-computed `title_norm`; do not add a second normalization path)
- `sources` = `[this book (title, author)]`

`target_language` is a **parameter** the helper receives — it is NOT resolved inside `vocab.py`. Every existing vocab function (`start_vocab`, `add_vocab_card`, `import_seed_list`) takes `target_language: str`, and the value is resolved at the `cli.py` layer via `read_setup(resolve_paths()).profile.target_language` (`cli.py:383,409,435`). The new `tutor book` command in `cli.py` resolves it the same way and passes it into the `book.py` handler, which passes it to the helper. (The previous draft's claim that this chain lives in `reading.py`/`lessons.py` was wrong — those modules receive a `profile` parameter.)

The helper generates the card `id` (`repo.create_id(...)`, as `add_vocab_card` does) and calls the nestable `_import_vocabulary_item_inner` (below), returning the `(status, vocab_item_id)` tuple. The `status` (`"created"`/`"updated"`/`"skipped"`) is the *SRS card* outcome and stays internal — it does **not** set the result's `deduped` flag. The `deduped` flag is set purely from the per-book word-lookup check: `deduped:true` iff a row with this `content_norm` already exists in this book. The SRS card may be globally deduped (the word came from another book) while the lookup is still new in this book → `deduped:false`. Either way `book.py` links the returned `vocab_item_id` onto the `book_lookups` row.

The find-or-create + lookup insert run in a **single transaction** opened by `book.py`. To make this safe, `repo.import_vocabulary_item` is refactored to be **nestable**: extract its body into a `_import_vocabulary_item_inner` method that assumes the caller manages the transaction and returns the same `tuple[Literal["created","updated","skipped"], str]`, and have `import_vocabulary_item` wrap it in `with transaction(self.conn):` (preserving the existing public contract — it currently opens its own transaction at `repositories.py:155`). `book.py` calls `_import_vocabulary_item_inner` inside its own outer `with transaction(conn):` (the `transaction` helper uses bare `BEGIN`, which fails if a transaction is already open — `dal/sqlite_store.py:24`). On failure both the vocab card write and the lookup insert roll back together.

### Explanation shape per kind

The explanation is **agent-generated** (LLM step) and passed into `tutor book record`. The CLI validates the shape against the kind:

- `word`: `{"translation": "<native-lang>", "gloss": "<short gloss>"}`
- `sentence` / `passage`: `{"translation": "..."}` (or explanation)
- `question`: `{"answer": "..."}`

Rationale: the CLI is deterministic (no LLM access), so it cannot generate explanations. It validates shape + persists + feeds SRS. This matches the repo pattern (agent generates content, CLI validates + persists).

### Rendering

Rendering belongs in the CLI (per the constitution), so `tutor book record` returns a pre-rendered `rendered` markdown field alongside the structured result. The agent displays `rendered` directly — no separate `tutor render book-explanation` command needed (KISS; the explanation is just translation + gloss). `tutor book log` likewise includes a `rendered` field per lookup so the agent displays the review list without formatting it.

**Deliberate divergence (acknowledged):** no existing record/result model carries a `rendered` field — the canonical pattern is a two-step `record` then `tutor render feedback` (as `tutor-reading` does, since its output is a structured `FeedbackEnvelope`). This design instead follows the `progress` command's inline-markdown precedent (`cli.py:569-571`), which emits rendered markdown directly. The trade-off is intentional: a book explanation is a trivial deterministic template, not a `FeedbackEnvelope`, so building a separate `render` subcommand + its schema would be over-engineering (YAGNI). The `rendered` field is therefore a new, narrowly-scoped result field justified by KISS — implementers should know they are introducing it, not matching an existing result-model field.

The `rendered` template is deterministic and per-kind:

- `word`: `**{content}** — {gloss} (translation: {translation})`
- `sentence`: `> {content}\n\n{translation}`
- `passage`: `> {content}\n\n{translation}` (falls back to `{explanation}` if `translation` is absent — the explanation shape allows either)
- `question`: `Q: {content}\nA: {answer}`

For `tutor book log`, each lookup is rendered as a numbered list item: `{n}. [{kind}] ` followed by the per-kind template above. The list is ordered by `created_at` ascending.

### New JSON schemas (under `schemas/`)

Naming follows the **real** repo convention — there is no `*_input.schema.json` suffix anywhere in `schemas/`. The repo splits input/output by semantic name (`text_modality_record` input vs `text_modality_result` output; `progress_request` vs `progress_report`; `init_request` vs `init_result`), and it does **not** create a JSON-schema file for every trivial input — several inputs are validated by a pydantic `...Input` model only (`VocabularyAnswerInput`, `WritingRecordInput`, `TextModalityRecordInput` have no matching `*.schema.json`).

So:

**Pydantic input models** (in `src/language_tutor/schemas.py`, peer to `TextModalityRecordInput`) validate every command input: `BookStartInput {session_id, title, author?}`, `BookRecordInput {book_session_id, kind, content, context?, explanation}`, `BookResumeInput {title}`, `BookLogInput {book_session_id}`, `BookCloseInput {book_session_id}`, `BookListInput {}`.

**JSON-schema files** are created only for the rich payloads the skill must not mis-field (the skill references them as "do not guess fields"):

- `book_record.schema.json` — `tutor book record` input (matches `text_modality_record` naming): `{book_session_id, kind, content, context?, explanation}`, with the per-kind `explanation` shape. This is the one input complex enough to warrant a schema file.
- `book_session.schema.json` — book session object (book_session_id, session_id, title, author, status, started_at, closed_at); output of `start`, `resume`, and `close`.
- `book_lookup_result.schema.json` — `tutor book record` output: `{lookup_id, vocab_item_id?, deduped, created_at, rendered}`.
- `book_log.schema.json` — `tutor book log` output: ordered list of lookups, each with `rendered`.
- `book_list.schema.json` — `tutor book list` output: ordered list of book sessions (open first), each with `lookup_count`.

The trivial inputs (`start`/`resume`/`log`/`close`/`list`) rely on their pydantic models, matching how peer commands handle simple inputs (no redundant schema file — KISS/YAGNI).

## Data flow

### Start (first message of a reading conversation)

1. `tutor session-start --json '{"host":"<host>"}'` → `session_id`
2. `tutor book start --json '{"session_id":"sess_...","title":"...","author":"..."}'` → `book_session_id` (idempotent on `(session_id, normalized_title)` within OPEN sessions)
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
2. (Optional, to propose books) `tutor book list --json '{}'` → all book sessions (open first, with `lookup_count`); agent presents them so the learner can pick.
3. `tutor book resume --json '{"title":"..."}'` → finds the most recent open book session for this title → `book_session_id` (tiebreak: `started_at DESC, book_session_id DESC`)
4. Continue the lookup loop (new `session_id` for checkpoints, same `book_session_id` for records).

### List (learner asks "what books am I reading?" or wants to resume)

- `tutor book list --json '{}'` → all book sessions (open first, then closed), each with `book_session_id`, `title`, `author`, `status`, `started_at`, `closed_at`, `lookup_count`; agent presents the list and, on a pick, calls `book resume` (open) or `book log` (closed, for review).

### Review log (learner asks "what have I looked up?")

- `tutor book log --json '{"book_session_id":"..."}'` → all lookups ordered by `created_at` ascending; agent renders the list.

### Close (only on explicit learner request)

- `tutor book close --json '{"book_session_id":"..."}'` → `status='closed'`. The skill never calls this automatically.

## Error handling

Deterministic JSON error envelopes matching the repo's existing `{"error": {...}}` contract:

- **`book start`**: title required non-empty; `session_id` must exist and be `open`; idempotent on re-start for the same `(session_id, normalized_title)` among OPEN book sessions (returns existing). Title normalization uses `normalize_text()` (`vocab.py:62` — NFKC + casefold + whitespace collapse + punctuation strip); the original title is stored and displayed, `title_norm` is the lookup key. Author is set on first `book start` only; on idempotent re-start the new `author` is ignored (existing session returned unchanged).
- **`book record`**: `kind` ∈ {word, sentence, passage, question}; `content` non-empty; explanation fields must match the kind (word requires `translation` + `gloss`); word dedup returns the existing row (`deduped:true`, existing `lookup_id`, existing `vocab_item_id`, existing `created_at`, existing `rendered`, no SRS re-feed — the card already has this book as a source); SRS card find-or-create + lookup insert are one transaction — on failure both roll back. Rejects a `closed` book session with `book_session_closed` ("This reading session is closed; start a new one with `tutor book start` or resume it first." / "Call `tutor book start` for a new session or `tutor book resume` to continue an open one."); no lookup persisted, no SRS feed.
- **`book resume`**: no open session for normalized title → `"no open reading session for '<title>'; start one with tutor book start"`.
- **`book log` / `book close`**: `book_session_id` must exist; `close` rejects an already-closed session.
- **`book list`**: no required input; always returns a list (empty if no book sessions exist).
- **All commands**: pydantic + JSON-schema validation; click usage errors; same error envelope shape as existing commands.

## Success criteria

1. A book session row + its lookups survive an abrupt CLI close (incremental persistence via `book record`; no shutdown hook needed — per constitution principle IX).
2. Looking up the same word in N different books creates exactly ONE SRS vocab card (global dedup by the item dedup key `standard:<word>:<word>`, where the word is set as `lemma`); each subsequent book is merged into the card via `import_vocabulary_item` (merges `sources`, plus `accepted_answers`/`notes`/`tags`).
3. `book log` returns lookups ordered by `created_at` ascending, stable across calls.
4. `book resume` finds an open book session by normalized title even after the originating tutor session is closed (book sessions are independent of tutor sessions).
5. `book record` on a `closed` book session is rejected with `book_session_closed`; no lookup is persisted.

## Testing

Follows the repo's spec-driven contract pattern (peer to `specs/005-text-modalities/`):

- **New spec:** `specs/008-book-reading/` with `contracts/` (CLI JSON contracts as Markdown + the `book_*.schema.json` files, mirroring how `specs/007-hookfree-incremental-lifecycle/contracts/` mixes Markdown contracts and `*.schema.json`) and `skill-pressure-scenarios.md` (peer to `specs/007-hookfree-incremental-lifecycle/skill-pressure-scenarios.md`).
- **Tests follow the repo's by-layer layout, not a per-feature `tests/book/` dir (which does not exist as a convention):**
  - `tests/unit/test_book.py` — `start`, `record`, `resume`, `log`, `list`, `close`, SRS feeding, rendering (peer to `tests/unit/test_text_modalities.py`).
  - `tests/integration/test_book_flow.py` — full start → lookup-loop → resume → log journey across CLI/core/DAL (peer to `tests/integration/test_text_modality_flow.py`).
  - `tests/golden/test_book_rendering.py` — the deterministic per-kind `rendered` templates (peer to `tests/golden/test_text_modality_rendering.py`).
  - `tests/migration/test_005_book_lookups.py` — see Migration test below.
- **DAL:** the repo has a single `TutorRepository(conn)` (`repositories.py:96-98`), not per-entity repositories. Per the constitution's single-responsibility principle (and the user's SOLID standard), book persistence goes in **new** `BookSessionRepository(conn)` + `BookLookupRepository(conn)` classes that follow the existing `__init__(self, conn)` connection convention, rather than growing the ~40 KB `TutorRepository` god-class. Tests cover `title_norm` idempotency and the resume tiebreak (`started_at DESC, book_session_id DESC`).
- **Migration test** (`tests/migration/test_005_book_lookups.py`, peer to `tests/migration/test_004_sessions_checkpoints.py`): `005_book_lookups` applies cleanly on top of `004_sessions_checkpoints`; the `checkpoints` rebuild preserves PK/NOT NULL/`REFERENCES sessions(id)`/both indexes, existing rows survive, new `'book'` modality and `'answer_recorded'` step_kind are accepted, old values still accepted; an injected mid-rebuild failure rolls back atomically leaving the original `checkpoints` intact; and `005` is registered in `REQUIRED_MIGRATION_FILES`.
- **Vocab refactor test:** `_import_vocabulary_item_inner` (the extracted no-transaction body) produces the same find-or-create-with-merge behavior as the original `import_vocabulary_item` when wrapped in an outer transaction, and composes with `book.py`'s outer `with transaction(conn):`.
- **Skill-suite audit:** the per-skill row is added to `specs/005-text-modalities/skill-inventory.md` (the inventory artifact). That file also asserts fixed counts — "7 tutor skills … 16 total" — which MUST be bumped to **8 tutor skills / 17 total**, not just appended to. `contracts/skill-suite-audit.md` is the *process* contract (audit rules), not a per-skill registry, so "register in skill-suite-audit.md" was imprecise — it is re-run, not edited with a skill row.
- **Skill pressure scenarios** (`specs/008-book-reading/skill-pressure-scenarios.md`) — written in the `specs/007-…/skill-pressure-scenarios.md` format (numbered scenarios, each with `Setup:` / `PASS condition:` / `FAIL (RED) condition:` and FR cross-references), not loose prose:
  1. Learner pastes a whole chapter as a "passage" — skill routes to a length-bounded explanation or asks the learner to pick a sentence.
  2. Learner asks a comprehension question ("what's the main idea of this chapter?") — skill routes to `tutor-reading`, not `tutor-book`.
  3. Learner looks up the same word twice — dedup, no duplicate SRS card.
  4. Learner says "I'm done, wrap up" — agent must NOT call `book close` automatically (mirrors the `session-close` guardrail).
  5. Learner pastes content in a language that doesn't match their setup profile — skill rejects and asks for content in the target language.
- **Constitution gate:** `SKILL.md` creation requires a subagent per skill plus documented RED/GREEN/REFACTOR pressure evidence, with the subagent prompt explicitly reading the local `writing-skills` helper and reporting changed files — per **Principle VIII "Skill Creation as Tested Contract" (`docs/internal/constitution.md:133-148`)**, reinforced by the Development Workflow bullets at `:205-208` and `:211-212`. (The earlier `:189-194` citation was wrong — those lines cover frontmatter naming and progressive disclosure.) Note: the helper path the constitution pins (`…/superpowers/5.1.0/skills/writing-skills`) is still present on disk but `6.0.3` is now installed alongside it; if `5.1.0` is later pruned the pinned path breaks — a constitution-level fragility this design inherits but does not fix.

## Implementation note

The user requested parallel agents for the implementation. The work decomposes into independent units (CLI command group, migration + DAL, schemas, skill markdown, tests, spec/contracts) that can be dispatched to parallel subagents once the implementation plan is written. One cross-cutting prerequisite: the `import_vocabulary_item` → `_import_vocabulary_item_inner` extraction (Q4) must land before the `book.py` SRS-feeding path can be wired up.
