# CLI Contract: `tutor book`

Six subcommands under the `tutor book` group. Implemented in `src/language_tutor/book.py`;
the `@main.group()` and subcommand functions live in `src/language_tutor/cli.py`.
Every command takes `--json '<payload>'` and returns JSON; errors use the repo's
existing `{"error": {...}}` envelope. JSON shapes: [book-json.md](book-json.md);
schema mirrors: `book_*.schema.json` in this directory.

The skill mints a tutor `session_id` via `tutor session-start` first, then threads both
`session_id` (for `tutor checkpoint`) and `book_session_id` (for `book record`/`log`/
`close`) through the conversation. See the design doc "Data flow" section.

## `book start`

Create a per-book reading session linked to the current tutor session.

### Invocation

```bash
tutor book start --json '{"session_id":"sess_...","title":"<title>","author":"<author>"}'
```

### Input

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `session_id` | string (`sess_...`) | yes | the active tutor session; must exist and be `open`. |
| `title` | string | yes | non-empty; stored as given, normalized (`normalize_text`) into `title_norm` for idempotency/resume. |
| `author` | string | no | set on first `book start` only; ignored on idempotent re-start. |

### Output

Conforms to `book_session.schema.json`:

```json
{ "book_session_id": "book_...", "session_id": "sess_...", "title": "...",
  "author": "...", "status": "open", "started_at": "...", "closed_at": null }
```

### Behavior

1. Validate `session_id` exists and is `open`; validate `title` non-empty.
2. Compute `title_norm = normalize_text(title)`. If an OPEN `book_sessions` row with
   the same `(session_id, title_norm)` already exists, return it unchanged (idempotent;
   a new `author` is ignored).
3. Otherwise mint `book_session_id`, INSERT the row (`status=open`,
   `started_at=now`), durably commit, and return it.

### Errors

- `session_not_open` — `session_id` does not exist or is not `open`.
- `invalid_book_title` — `title` empty after normalization.
- Pydantic / JSON-schema validation envelope on malformed input.

## `book record`

Persist a lookup with an agent-generated explanation. The lookup is ALWAYS persisted
(the reading log is the primary value); words additionally feed the SRS deck on a
usable, non-echo translation.

### Invocation

```bash
tutor book record --json '{"book_session_id":"book_...","kind":"word","content":"esquivo","context":"...","explanation":{"translation":"...","gloss":"..."}}'
```

### Input

Conforms to `book_record.schema.json`:

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `book_session_id` | string (`book_...`) | yes | must exist and be `open`. |
| `kind` | enum(word, sentence, passage, question) | yes | the lookup kind. |
| `content` | string | yes | non-empty; the original text the learner asked about. |
| `context` | string | no | optional surrounding text. |
| `explanation` | object | yes | shape must match `kind` (see [book-json.md](book-json.md)). |

### Output

Conforms to `book_lookup_result.schema.json`:

```json
{ "lookup_id": "lookup_...", "vocab_item_id": "vocab_...", "deduped": false,
  "created_at": "...", "rendered": "**esquivo** — shy (translation: reclusive)" }
```

`vocab_item_id` is present only when an SRS card was fed (word + usable, non-echo
translation). `deduped:true` means this normalized word already had a lookup row in
this book (existing row returned, no SRS re-feed). `rendered` is a deterministic
per-kind markdown string the agent displays directly.

### Behavior

1. Validate `book_session_id` exists and is `open`; reject `closed` with
   `book_session_closed` (no lookup persisted, no SRS feed).
2. Validate `kind`/`content`/`explanation` shape per kind.
3. For `kind:"word"`: compute `content_norm`. If a lookup row with this
   `(book_session_id, content_norm)` already exists, return it (`deduped:true`, no
   SRS re-feed).
4. For `kind:"word"` with a usable, non-echo translation, find-or-create the SRS card
   via the nestable `_import_vocabulary_item_inner` (global dedup by
   `standard:<word>:<word>`, word set as `lemma`, tagged `["from-book"]`, card
   `source` = `(title, author)`). The find-or-create + lookup insert run in ONE
   transaction. A missing/echo translation logs the word with `vocab_item_id` NULL
   and no SRS feed.
5. For `kind` ∈ sentence/passage/question: INSERT the lookup (no dedup, no SRS).
6. Render the per-kind `rendered` markdown, commit, and return the result.

### Errors

- `book_session_closed` — the book session is `closed` (recoverable: offer
  `book start` for a new session or `book resume` to continue an open one).
- `invalid_book_record` — bad `kind`, empty `content`, or `explanation` shape does
  not match `kind`.
- `book_session_not_found` — `book_session_id` does not exist.
- Pydantic / JSON-schema validation envelope on malformed input.

## `book resume`

Find the most recent OPEN book session by normalized title (for resuming in a new
conversation). Works regardless of the originating tutor session's status — book
sessions are scoped to the learner, not to the tutor session.

### Invocation

```bash
tutor book resume --json '{"title":"<title>"}'
```

### Input

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `title` | string | yes | normalized via `normalize_text` for the lookup. |

### Output

Conforms to `book_session.schema.json` (the matched OPEN book session).

### Behavior

1. Compute `title_norm`; find the most recent OPEN `book_sessions` row for this
   `title_norm`. Tiebreak: `started_at DESC, book_session_id DESC`.
2. Return the matched row.

### Errors

- `no_open_book_session` — no OPEN session for the normalized title (message names
  the title and points to `tutor book start`).
- `invalid_book_title` — `title` empty after normalization.
- Pydantic validation envelope on malformed input.

## `book log`

Return all lookups for a book session, ordered by `created_at` ascending (for review).

### Invocation

```bash
tutor book log --json '{"book_session_id":"book_..."}'
```

### Input

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `book_session_id` | string (`book_...`) | yes | must exist (open or closed). |

### Output

Conforms to `book_log.schema.json`:

```json
{ "book_session_id": "book_...", "lookups": [
  { "lookup_id": "lookup_...", "kind": "word", "content": "...",
    "created_at": "...", "rendered": "..." } ],
  "rendered": "1. [word] **esquivo** — shy (translation: reclusive)\n2. ..." }
```

`lookups[]` is ordered by `created_at` ascending; each entry carries its own
`rendered` field. The top-level `rendered` is a deterministic numbered list the agent
displays directly.

### Behavior

1. Validate `book_session_id` exists.
2. Read all `book_lookups` for the session, ordered by `created_at` ascending.
3. Render the per-lookup markdown + the numbered list, and return both.

### Errors

- `book_session_not_found` — `book_session_id` does not exist.
- Pydantic validation envelope on malformed input.

## `book list`

Return all book sessions (OPEN first, then CLOSED), newest first, each with
`lookup_count`. The skill calls this before `resume` to propose books the learner has
already started.

### Invocation

```bash
tutor book list --json '{}'
```

### Input

No required fields. (An empty `{}` payload is the normal input.)

### Output

Conforms to `book_list.schema.json`:

```json
{ "sessions": [
  { "book_session_id": "book_...", "session_id": "sess_...", "title": "...",
    "author": "...", "status": "open", "started_at": "...", "closed_at": null,
    "lookup_count": 7 } ] }
```

`sessions[]` is ordered OPEN first, then CLOSED, newest first by
`started_at DESC, book_session_id DESC`.

### Behavior

1. Read all `book_sessions` rows with their `lookup_count` (count of `book_lookups`
   per session).
2. Order OPEN first, then CLOSED, newest first within each status.
3. Return the list (empty `sessions: []` if no book sessions exist).

### Errors

- None beyond malformed-input / pydantic validation (always returns a list).

## `book close`

Mark a reading session `closed`. Only on explicit learner request — the skill never
calls this automatically (mirrors the `session-close` guardrail). Closing a book
session does NOT close the parent tutor session, and closing a tutor session does NOT
close linked book sessions.

### Invocation

```bash
tutor book close --json '{"book_session_id":"book_..."}'
```

### Input

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `book_session_id` | string (`book_...`) | yes | the book session to close. |

### Output

Conforms to `book_session.schema.json` with `status:"closed"` and `closed_at` set.

### Behavior

1. Validate `book_session_id` exists.
2. Reject an already-closed session with `book_session_already_closed`.
3. Set `status=closed`, `closed_at=now`, durably commit, and return the row.

### Errors

- `book_session_not_found` — `book_session_id` does not exist.
- `book_session_already_closed` — the session is already `closed`.
- Pydantic validation envelope on malformed input.

## CLI Error Rules (all subcommands)

- Invalid JSON returns `invalid_json`.
- Pydantic / JSON-schema validation failure returns the standard `{"error": {...}}`
  envelope with the field-specific reason.
- Click usage errors surface via the existing click error contract.
- The skill MUST recover from `book_session_closed` by offering `book start` /
  `book resume`, not by surfacing the raw error to the learner
  (see [skill-pressure-scenarios.md](../skill-pressure-scenarios.md) scenario 6).
