# Skill Pressure Scenarios (T011)

Pressure scenarios for the writing-skills helper RED→GREEN cycle. Each scenario
describes one rule the `tutor-book` `SKILL.md` must teach a future agent. Baseline
(RED): verify these all FAIL without the `tutor-book` skill (an agent asked to "help
me read my book" has no skill to route to — it refuses or misuses `tutor-reading`,
which generates passages instead of looking up the learner's own text). After the
`SKILL.md` is authored (GREEN), verify they all PASS. Source: design doc
[docs/superpowers/specs/2026-06-22-tutor-book-reading-design.md](../../docs/superpowers/specs/2026-06-22-tutor-book-reading-design.md)
"Skill pressure scenarios" section.

## Scenario 1 — Pasting a whole chapter as a "passage" (design scenario 1)

> Setup: the learner pastes a whole chapter (thousands of words) and asks the agent to
> explain it as `kind:"passage"`.
> PASS condition: the skill does NOT pass the whole chapter verbatim into
> `tutor book record --json '{"...","kind":"passage","content":"<whole chapter>"}'`.
> It either routes to a length-bounded explanation (asks the learner to pick the
> sentence/paragraph they don't understand) or splits the request into sentence-level
> lookups. The CLI owns validation/budgets; the skill respects them.
> FAIL (RED) condition: the agent forwards the unbounded chapter as one `passage`
> `content`, or tries to summarize the whole chapter itself instead of routing to a
> bounded lookup.

## Scenario 2 — Own-book text vs tutor-generated passage discriminator (design scenario 2)

> Setup: the learner is reading their own book and asks "what does this sentence mean?"
> (text in front of them), then separately asks "what's the main idea of this chapter?"
> (open-ended comprehension/analysis).
> PASS condition: the on-the-spot meaning lookup ("what does this sentence mean?") stays
> in `tutor-book` (a `kind:"sentence"`/`passage`/`question` `tutor book record` call);
> the open-ended comprehension/analysis ("main idea of this chapter?") routes to
> `tutor-reading`, not `tutor-book`.
> FAIL (RED) condition: the agent routes the open-ended comprehension question to
> `tutor-book` (misusing `kind:"question"` for analysis the CLI cannot validate), OR
> routes the on-the-spot lookup to `tutor-reading` (which generates a passage instead
> of explaining the learner's own text).

## Scenario 3 — Looking up the same word twice (SC-2)

> Setup: within one book session the learner looks up "esquivo" twice.
> PASS condition: the second `tutor book record` for the same normalized word returns
> `deduped:true` with the existing `lookup_id`/`created_at`/`rendered` and NO SRS
> re-feed (the card already has this book as a source). Across N different books, the
> same word creates exactly ONE SRS card (global dedup by `standard:<word>:<word>`).
> FAIL (RED) condition: the agent re-generates a fresh explanation and forces a new
> lookup row, or the skill implies a second SRS card would be created for the same
> word.

## Scenario 4 — No automatic `book close` (design scenario 4, mirrors FR-007)

> Setup: ordinary book-reading flow with no explicit "close this book" request; the
> learner says "I'm done, wrap up" meaning only that they are stopping for now.
> PASS condition: the agent does NOT call `tutor book close` (or `tutor session-close`)
> automatically at the end of the flow. Book sessions stay `open` between turns and are
> resumed by reusing the same `book_session_id`.
> FAIL (RED) condition: the agent calls `tutor book close` after the last lookup, or
> treats "I'm done for today" as a close request.

## Scenario 5 — Content language does not match the setup profile (design scenario 5)

> Setup: the learner's setup `target_language` is Ukrainian, but they paste a Spanish
> sentence and ask for a lookup.
> PASS condition: the skill rejects the content and asks the learner to paste content
> in their target language (Ukrainian), rather than recording a mismatched-language
> lookup.
> FAIL (RED) condition: the agent records the Spanish lookup as if it were Ukrainian
> target-language content, polluting the per-book log and the SRS deck.

## Scenario 6 — Lookup on a `closed` book session recovers, does not surface the raw error (SC-5)

> Setup: the learner's current book session is `closed` (closed earlier) and they type a
> word to look up. `tutor book record` returns `book_session_closed`.
> PASS condition: the agent RECOVERS — it does not surface the raw `book_session_closed`
> error to the learner. It offers to `tutor book start` a new session for the same book
> or `tutor book resume` to continue an open one, then proceeds once the learner picks.
> FAIL (RED) condition: the agent surfaces the raw `{"error":{"code":"book_session_closed"}}`
> envelope to the learner, or gives up instead of offering recovery.

## Scenario 7 — Two open book sessions with the same title; "resume my book" disambiguates (design scenario 7)

> Setup: the learner has two OPEN book sessions with the same title (a re-read or two
> editions) and says "resume my book".
> PASS condition: the agent calls `tutor book list --json '{}'` first and disambiguates
> by `author` / `started_at` (presenting both to the learner to pick), rather than
> letting `tutor book resume` silently pick the most-recent by tiebreak.
> FAIL (RED) condition: the agent calls `tutor book resume` directly and silently
> resumes one of the two sessions without surfacing the ambiguity to the learner.

## Per-command summary

| `tutor book` subcommand | When the skill calls it |
|---|---|
| `book start` | Once at the start of a new book-reading conversation (after `session-start`), to mint the `book_session_id`. Idempotent within the tutor session for an open book of the same title. |
| `book record` | Once per learner lookup (word/sentence/passage/question), after the agent generates the explanation. Always followed by a `checkpoint` (`modality:"book"`, `step_kind:"answer_recorded"`) and a display of the returned `rendered` field. |
| `book log` | When the learner asks "what have I looked up?" — returns the ordered lookup history. |
| `book list` | When the learner wants to resume or asks "what books am I reading?" — and ALWAYS before `book resume` when more than one open session may share a title (disambiguation, scenario 7). |
| `book resume` | In a new conversation, after `session-start` (and usually after `book list`), to continue an open book session by title. |
| `book close` | ONLY on an explicit learner request to close this book (scenario 4). Never automatic. Does not close the parent tutor session. |
