---
name: tutor-reading
description: Use when the learner wants to read a passage and answer comprehension questions, or reconstruct a text transcript drill (text-only, no audio). Not for free writing, vocabulary review, or guided lessons.
---

Use this when the learner wants reading comprehension practice or a text-only transcript
drill. Transcript drills are a text-only submode of this skill (`mode:"transcript"`); they
are not audio and there is no separate transcript skill.

Run only `tutor` for stateful work:

0. On the first stateful step of the conversation, mint a session BEFORE anything else:
   `tutor session-start --json '{"host":"<host>"}'`. Capture the returned
   `session_id` (e.g. `sess_ab12`) and thread `"session_id":"sess_..."` into every
   later `tutor` payload this conversation. If you already have a `session_id`
   from earlier in the conversation, reuse it — do not call `session-start` again.
1. Generate a candidate exercise (JSON) for the learner's target language and level.
2. Validate it: `tutor reading start --json '{"session_id":"sess_...","mode":"comprehension","candidate":{...}}'`
   (use `"mode":"transcript"` for transcript drills).
3. If validation fails, regenerate the candidate once, then validate again. After one
   failed repair, stop and tell the learner the exercise could not be prepared.
4. After validation succeeds and BEFORE showing the exercise to the learner, checkpoint:
   `tutor checkpoint --json '{"session_id":"sess_...","modality":"reading","step_kind":"prompt_shown","summary":"...","state":{...}}'`.
   For transcript submode (`mode:"transcript"`), set `"modality":"transcript"` instead
   of `"reading"`. Only after the checkpoint returns do you present the exercise.
5. Ask `tutor-judge` for a `FeedbackEnvelope` JSON object about the learner's answer.
6. Persist: `tutor reading record --json '{"session_id":"sess_...", ...<TextModalityRecordInput>}'`.
7. Render feedback with `tutor render feedback --json '<feedback>'`.

Never call `tutor session-close` (or the legacy `session-end`) automatically — only
when the learner explicitly asks to wrap up. Sessions stay `open` between turns and are
resumed by reusing the same `session_id`; a new conversation gets a new session via
another `session-start`.

The CLI owns validation, output budgets, scoring metadata, persistence, and progress.
Do not invent corrections, persist directly, render through another LLM step, or imply
audio playback. Keep everything text-only.

## Payload schemas (build every request against these)

Read the referenced `schemas/*.schema.json` before constructing the payload; do not guess fields.

- `session-start` input: `{"host":"claude|codex|openclaw|hermes","host_conversation_id"?:str}` → output `schemas/boot_result.schema.json`.
- `reading start` input: `{"session_id":"sess_...","mode":"comprehension|transcript","candidate":{...}}`; `candidate` → `schemas/reading_exercise.schema.json`.
- `checkpoint` input → `schemas/checkpoint.schema.json`. Required: `session_id`, `modality` (`reading`, or `transcript` for transcript submode), `step_kind`, `summary`. `prompt_ref` exists at BOTH the top level and inside `state` — when you have a prompt id, set `state.prompt_ref` (not only the top-level one). `state` also takes `step_index`, `total_steps`, `modality_hint`, `labels` (≤16).
- `reading record` input (`TextModalityRecordInput`) → `schemas/text_modality_record.schema.json`; `candidate_feedback` → `schemas/feedback_envelope.schema.json`.
- `render feedback` input → `schemas/feedback_envelope.schema.json`.
