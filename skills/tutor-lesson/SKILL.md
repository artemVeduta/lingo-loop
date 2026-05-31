---
name: tutor-lesson
description: Use when the learner wants a guided micro-lesson on one weak tag or one chosen topic (one explanation plus one practice step). Not for reading comprehension, free writing, vocabulary review, or progress reports.
---

Use this when the learner wants a short guided lesson on one weak area or a topic they
pick. A micro-lesson covers exactly one bounded topic plus a single practice step.

Run only `tutor` for stateful work:

1. If this conversation has no `session_id` yet, call
   `tutor session-start --json '{"host":"<host>"}'` first and capture the returned
   `session_id` (e.g. `sess_ab12`). Thread that same `session_id` into every later
   `tutor` payload this conversation. Never use `"default"`. Never call
   `session-close` or `session-end` automatically — only on explicit learner request.
2. Pick one focus: a learner-chosen topic, or a weak tag from
   `tutor progress --json '{"session_id":"sess_..."}'`.
3. Generate a candidate lesson (JSON) for the learner's target language and level with one
   explanation and one practice step. The `candidate` object must match this schema:

   ```json
   {
     "modality": "lesson",
     "target_language": "<lang>",
     "level_target": "<CEFR level>",
     "focus": "<optional weak tag or topic>",
     "instructions": "<what the learner should do>",
     "content": "<the explanation>",
     "questions": ["<practice prompt>"],
     "answer_key": ["<expected answer>"],
     "rubric": [],
     "tags": ["<topic tag>"]
   }
   ```

   Required: `modality`, `target_language`, `level_target`, `instructions`, `content`,
   and at least one of `answer_key` or `rubric`. `focus` defaults to `""`; `questions`,
   `rubric`, `tags` default to `[]`.
4. Validate it: `tutor lesson start --json '{"session_id":"sess_...","candidate":{...}}'`.
5. If validation fails, regenerate the candidate once, then validate again. After one
   failed repair, stop and tell the learner the lesson could not be prepared.
6. Before showing the lesson to the learner, checkpoint it:
   `tutor checkpoint --json '{"session_id":"sess_...","modality":"lesson","step_kind":"prompt_shown","prompt_ref":"<id>","state":{"step_index":0,"total_steps":2},"summary":"<short>"}'`.
7. Ask `tutor-judge` for a `FeedbackEnvelope` JSON object about the practice answer.
8. Persist: `tutor lesson record --json '<TextModalityRecordInput with "session_id":"sess_...">'`.
9. Render feedback with `tutor render feedback --json '<feedback>'`.

The CLI owns validation, output budgets, scoring metadata, persistence, and progress.
Do not invent corrections, persist directly, render through another LLM step, or expand
the lesson beyond one bounded topic.

## Payload schemas (build every request against these)

Read the referenced `schemas/*.schema.json` before constructing the payload; do not guess fields.

- `session-start` input: `{"host":"claude|codex|openclaw|hermes","host_conversation_id"?:str}` → output `schemas/boot_result.schema.json`.
- `progress` input → `schemas/progress_request.schema.json`.
- `lesson start` input: `{"session_id":"sess_...","candidate":{...}}`; `candidate` → `schemas/lesson_exercise.schema.json` (also inlined in step 3).
- `checkpoint` input → `schemas/checkpoint.schema.json`. Required: `session_id`, `modality`, `step_kind`, `summary`. `prompt_ref` exists at BOTH the top level and inside `state` — when you have a prompt id, set `state.prompt_ref` (not only the top-level one). `state` also takes `step_index`, `total_steps`, `modality_hint`, `labels` (≤16).
- `lesson record` input (`TextModalityRecordInput`) → `schemas/text_modality_record.schema.json`; `candidate_feedback` → `schemas/feedback_envelope.schema.json`.
- `render feedback` input → `schemas/feedback_envelope.schema.json`.
