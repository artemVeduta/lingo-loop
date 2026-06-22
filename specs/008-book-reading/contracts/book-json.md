# Contract: Book Reading JSON

JSON shapes for the `tutor book` command group. Schema mirrors live alongside this
file as `book_*.schema.json` (frozen copies of the canonical `schemas/` files emitted
by `export_json_schemas` from the backing pydantic models in `src/language_tutor/schemas.py`).

## Shared Literals

```json
{
  "kind": ["word", "sentence", "passage", "question"],
  "status": ["open", "closed"]
}
```

- `kind` is the lookup kind passed to `book record` and stored on every `book_lookups`
  row.
- `status` is the book-session lifecycle status. `stale`/`abandoned` are NOT book
  statuses (they are read-time labels on tutor sessions only, per 007).

## BookRecordInput

`tutor book record` input. Schema: [book_record.schema.json](book_record.schema.json).

Required fields:

- `book_session_id` (`book_...`)
- `kind` (enum)
- `content` (non-empty string; the original text the learner asked about)
- `explanation` (object; shape must match `kind` — see below)

Optional fields:

- `context` (string | null; surrounding text, mainly for words)

Validation:

- `book_session_id` must exist and be `open` (else `book_session_closed` /
  `book_session_not_found`).
- `explanation` shape must match `kind` (else `invalid_book_record`).

### Per-kind `explanation` shape

- `word`: `{"translation": "<native-lang>", "gloss"?:"<short gloss>"}`. `translation`
  may be absent/empty — the word is still logged; it just feeds no SRS card. A
  `translation` equal to the word (after `normalize_text`) is treated as absent for
  SRS purposes (the "echoed source word" guard).
- `sentence` / `passage`: `{"translation": "..."}` (or an explanation string).
- `question`: `{"answer": "..."}`.

Rationale: the CLI is deterministic (no LLM access), so it cannot generate
explanations. It validates shape + persists + feeds SRS. The agent generates the
content; the CLI validates and persists (the repo pattern).

## BookSession

Output of `book start`, `book resume`, and `book close`. Schema:
[book_session.schema.json](book_session.schema.json).

Required fields:

- `book_session_id` (`^book_[A-Za-z0-9]+$`)
- `session_id` (`^sess_[A-Za-z0-9]+$`) — the parent tutor session
- `title` (original, as given)
- `started_at` (ISO 8601)

Optional / default fields:

- `author` (string | null; default null)
- `status` (enum, default `"open"`)
- `closed_at` (ISO 8601 | null; default null; set only by `book close`)

Rules:

- `book_session_id` is CLI-minted and immutable.
- `status` becomes `closed` only via an explicit `book close`.
- Closing a book session does NOT close the parent tutor session, and closing a tutor
  session does NOT close linked book sessions.

## BookLookupResult

Output of `tutor book record`. Schema:
[book_lookup_result.schema.json](book_lookup_result.schema.json).

Required fields:

- `lookup_id` (`^lookup_[A-Za-z0-9]+$`)
- `deduped` (boolean) — `true` iff this normalized word already had a lookup row in
  this book (per-book word-lookup dedup via `content_norm`). For
  sentence/passage/question this is always `false` (no dedup).
- `created_at` (ISO 8601)
- `rendered` (string) — deterministic per-kind markdown the agent displays directly.

Optional field:

- `vocab_item_id` (string | null; default null) — present only when an SRS card was
  fed (word + usable, non-echo translation). NULL when the word was logged without a
  card (missing/echo translation, or non-word kinds).

Rules:

- `deduped` reflects ONLY the per-book word-lookup check. The SRS card may be
  globally deduped (the word came from another book) while the lookup is brand-new in
  this book → `deduped:false` even though no new card was created. The two dedup
  levels are independent and must not be confused.
- The lookup is ALWAYS persisted (the reading log is the primary value). SRS feeding
  is conditional; logging is not.
- `rendered` is a deliberate, narrowly-scoped result field (ratified in the design
  doc), not a reuse of an existing embedded-rendered pattern. It keeps rendering in
  the CLI layer (constitution-aligned).

### Per-kind `rendered` template

- `word`: `**{content}** — {gloss} (translation: {translation})` when both present;
  drop the `— {gloss}` segment when no gloss and the `(translation: …)` segment when
  no translation (a logged-but-not-carded word still renders as `**{content}**`).
- `sentence`: `> {content}\n\n{translation}`
- `passage`: `> {content}\n\n{translation}` (falls back to `{explanation}` if
  `translation` is absent)
- `question`: `Q: {content}\nA: {answer}`

## BookLog

Output of `tutor book log`. Schema: [book_log.schema.json](book_log.schema.json).

Required fields:

- `book_session_id` (`^book_[A-Za-z0-9]+$`)
- `lookups` (array of `BookLogEntry`, ordered by `created_at` ascending)
- `rendered` (string) — deterministic numbered list the agent displays directly.

`BookLogEntry` required fields:

- `lookup_id`, `kind`, `content`, `created_at`, `rendered`

Rules:

- `lookups[]` is ordered by `created_at` ascending, stable across calls.
- The top-level `rendered` is `{n}. [{kind}] ` followed by the per-kind template
  above, one line per lookup.

## BookList

Output of `tutor book list`. Schema: [book_list.schema.json](book_list.schema.json).

Required fields:

- `sessions` (array of `BookListEntry`, ordered OPEN first then CLOSED, newest first
  by `started_at DESC, book_session_id DESC`)

`BookListEntry` required fields:

- `book_session_id`, `session_id`, `title`, `status`, `started_at`, `lookup_count`

`BookListEntry` optional fields:

- `author` (string | null), `closed_at` (ISO 8601 | null)

Rules:

- Always returns a list (empty `sessions: []` if no book sessions exist).
- `lookup_count` is the count of `book_lookups` for the session (minimum 0).
- The skill calls `book list` before `book resume` to propose books and disambiguate
  when two open sessions share a title (by `author` / `started_at`).
