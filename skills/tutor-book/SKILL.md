---
name: tutor-book
description: Use when the learner has their OWN book or text in front of them and wants on-the-spot lookups of words, sentences, or passages they don't understand, or to ask about the text they are reading. Looked-up words are saved and added to vocabulary spaced-repetition review. tutor-reading is for comprehension Q&A on tutor-generated passages; tutor-vocab is for standalone vocab drills.
---

Use this when the learner is reading their own book (or any external text) and wants
help with something they don't understand in front of them — a word, a sentence, a
passage, or a question about the text. The learner types/pastes the text; this skill
does not ingest book files or generate passages.

Run only `tutor` for stateful work:

0. On the first stateful step of the conversation, mint a session BEFORE anything else:
   `tutor session-start --json '{"host":"<host>"}'`. Capture the returned
   `session_id` (e.g. `sess_ab12`) and thread `"session_id":"sess_..."` into every
   later `tutor` payload this conversation. If you already have a `session_id`
   from earlier in the conversation, reuse it — do not call `session-start` again.
1. Start a per-book reading session linked to the tutor session:
   `tutor book start --json '{"session_id":"sess_...","title":"<title>","author":"<author>"}'`
   (`author` is optional). Capture the returned `book_session_id` (e.g. `book_cd34`)
   and thread `"book_session_id":"book_..."` into every `tutor book record` /
   `tutor book log` / `tutor book close` payload this conversation. `book start` is
   idempotent within the current tutor session for an open book of the same title —
   re-calling it returns the existing book session.
2. BEFORE telling the learner the reading session is ready, checkpoint:
   `tutor checkpoint --json '{"session_id":"sess_...","modality":"book","step_kind":"prompt_shown","summary":"Started reading <title>","state":{"book_session_id":"book_...","title":"<title>"}}'`.
   Only after the checkpoint returns do you tell the learner the session is ready.
3. Lookup loop — for each thing the learner does not understand:
    a. The learner types a `word`, `sentence`, `passage`, or `question` (optionally
       with surrounding `context`). You generate the explanation:
      If the learner pastes a whole chapter or an overly long excerpt, do not try to
      process it as one lookup; ask them to choose a sentence/short passage or give a
      bounded summary of the specific excerpt they selected. If the pasted content is
      not in the learner's configured target language, reject it and ask for target-
      language text before calling `tutor book record`.
       - `word`: `{"translation":"<native-lang>","gloss"?:"<short gloss>"}` —
         `translation` may be absent/empty (the word is still logged; it just feeds no
         SRS card). A translation that is just the word echoed back is treated as
        absent for SRS purposes.
      - `sentence` / `passage`: `{"translation":"..."}` (or explanation).
      - `question`: `{"answer":"..."}`.
   b. Persist + render:
      `tutor book record --json '{"book_session_id":"book_...","kind":"word","content":"<text>","context":"<optional>","explanation":{...}}'`.
      The result is `{lookup_id, vocab_item_id?, deduped, created_at, rendered}`. The
      lookup is always persisted; `deduped:true` means this normalized word already had
      a lookup row in this book (no duplicate SRS card).
    c. Checkpoint the recorded answer:
       `tutor checkpoint --json '{"session_id":"sess_...","modality":"book","step_kind":"answer_recorded","summary":"Looked up <text>","state":{"book_session_id":"book_...","lookup_id":"lookup_...","kind":"word"}}'`.
    d. Display the `rendered` markdown field returned by `tutor book record` to the
       learner. Do not reformat it yourself — the CLI owns rendering.
      If `tutor book record` returns `book_session_closed`, do not show the raw error.
      Tell the learner the reading session is closed and offer to start a new session
      with `tutor book start` or resume an open one with `tutor book list` / `tutor book resume`.
4. Review log — when the learner asks "what have I looked up?":
   `tutor book log --json '{"book_session_id":"book_..."}'` returns all lookups ordered
   by `created_at` ascending, each with its own `rendered` field. Display the
   `rendered` field; do not reformat.
5. Resume in a new conversation — when the learner comes back to continue a book:
   `tutor session-start` (new `session_id`) → optionally `tutor book list --json '{}'`
   to propose open books (open first, each with `lookup_count`; disambiguate by
   `author` / `started_at` when two open sessions share a title) →
   `tutor book resume --json '{"title":"<title>"}'` finds the most recent open book
   session for the title and returns its `book_session_id`. Reuse that
   `book_session_id` for `tutor book record` / `tutor book log`; use the new
   `session_id` for `tutor checkpoint`.
6. `tutor book close --json '{"book_session_id":"book_..."}'` marks a reading session
   `closed`. NEVER call it automatically — only when the learner explicitly asks to
   wrap up this book. Closing a book session does NOT close the parent tutor session,
   and closing a tutor session does NOT close linked book sessions.

Never call `tutor session-close` (or the legacy `session-end`) automatically either —
only when the learner explicitly asks to wrap up the whole tutor session. Sessions stay
`open` between turns and are resumed by reusing the same id; a new conversation gets a
new session via another `session-start`.

The CLI owns validation, persistence, SRS card find-or-create, rendering, and
dedup. Do not invent explanations and persist them directly, render through another
LLM step, build SRS cards yourself, or imply book-file ingestion, page tracking, or
automatic unknown-word extraction.

## Discriminator vs `tutor-reading`

- `tutor-book`: the learner has their OWN book/text in front of them and wants an
  on-the-spot meaning lookup of text they are reading (word/sentence/passage), or a
  direct question about that text (`kind:"question"`/`passage`). The text is the
  learner's; this skill explains it and logs the lookup.
- `tutor-reading`: the tutor generates a passage and the learner answers
  comprehension questions (or reconstructs a transcript). The text is tutor-generated.
- Open-ended comprehension/analysis ("what's the main idea of this chapter?") routes
  to `tutor-reading`, not `tutor-book`. On-the-spot "what does this sentence mean?"
  of text in front of the learner stays in `tutor-book`.

## Payload schemas (build every request against these)

Read the referenced `schemas/*.schema.json` before constructing the payload; do not guess fields.

- `session-start` input: `{"host":"claude|codex|openclaw|hermes","host_conversation_id"?:str}` → output `schemas/boot_result.schema.json`.
- `book start` input: `{"session_id":"sess_...","title":str,"author"?:str}` → output `schemas/book_session.schema.json`.
- `checkpoint` input → `schemas/checkpoint.schema.json`. Required: `session_id`, `modality` (`book` for this skill), `step_kind`, `summary`. For this skill: `step_kind` is `prompt_shown` (step 2) or `answer_recorded` (step 3c). `state` also takes `book_session_id`, `lookup_id`, `kind`, `title`, `step_index`, `total_steps`, `labels` (≤16).
- `book record` input (`BookRecordInput`) → `schemas/book_record.schema.json`; `kind` ∈ `word|sentence|passage|question`; `explanation` shape per kind (see step 3a). Output → `schemas/book_lookup_result.schema.json` (`lookup_id`, `deduped`, `created_at`, `rendered`, optional `vocab_item_id`).
- `book log` input: `{"book_session_id":"book_..."}` → output `schemas/book_log.schema.json` (ordered `lookups[]`, each with `rendered`, plus a top-level `rendered` numbered list).
- `book list` input: `{}` → output `schemas/book_list.schema.json` (`sessions[]` open first, each with `lookup_count`).
- `book resume` input: `{"title":str}` → output `schemas/book_session.schema.json`.
- `book close` input: `{"book_session_id":"book_..."}` → output `schemas/book_session.schema.json` (`status:"closed"`).
