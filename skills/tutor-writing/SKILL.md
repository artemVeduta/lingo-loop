---
name: tutor-writing
description: Free writing prompt and structured feedback orchestration.
---

Use this when learner wants free writing or structured correction.

Flow:

1. If this conversation has no `session_id` yet, FIRST run `tutor session-start --json '{"host":"<host>"}'` and capture `session_id` from the response. Do this before any other `tutor` call. No SessionStart hooks — session-start is the boot path.
2. Get prompt with `tutor writing prompt --json`.
3. IMMEDIATELY, before showing the prompt to the learner, call `tutor checkpoint --json '{"session_id":"sess_...","modality":"writing","step_kind":"prompt_shown","prompt_ref":"<prompt_id>","summary":"<short>"}'`.
4. Ask `tutor-judge` for a `FeedbackEnvelope` JSON object.
5. Persist validated feedback with `tutor writing record --json '<payload>'`. The payload MUST include `"session_id":"sess_..."` (never `"default"`).
6. Render with `tutor render feedback --json '<feedback>'`.

Do not persist directly or render through another LLM step. Do NOT call `tutor session-close` or `session-end` automatically — only when the learner explicitly ends the session.

## Payload schemas (build every request against these)

Read the referenced `schemas/*.schema.json` before constructing the payload; do not guess fields.

- `session-start` input: `{"host":"claude|codex|openclaw|hermes","host_conversation_id"?:str}` → output `schemas/boot_result.schema.json`.
- `writing prompt`: no input → output fields `prompt_id`, `prompt`, `fit`, `learner_provided_allowed`.
- `checkpoint` input → `schemas/checkpoint.schema.json`. Required: `session_id`, `modality` (`writing`), `step_kind` (`prompt_shown`), `summary`. `prompt_ref` exists at BOTH the top level and inside `state` — set `state.prompt_ref` to the prompt id, not only the top-level field. `state` also takes `step_index`, `total_steps`, `modality_hint`, `labels` (≤16).
- `writing record` input (`WritingRecordInput`): `{"session_id":"sess_...","prompt_id":str,"learner_answer":str,"candidate_feedback":{...}}`; `candidate_feedback` → `schemas/feedback_envelope.schema.json`.
- `render feedback` input → `schemas/feedback_envelope.schema.json`.
