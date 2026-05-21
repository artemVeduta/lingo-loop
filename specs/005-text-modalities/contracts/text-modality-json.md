# Contract: Text Modality JSON

## Shared Literals

```json
{
  "text_modality": ["reading", "lesson", "transcript"],
  "stored_skill": ["vocab", "writing", "reading", "lesson"],
  "response_status": ["completed", "empty", "abandoned", "off_topic", "mixed_language", "refused"]
}
```

Transcript drills are stored as `skill=reading` and represented as `modality=transcript`.

## TextExerciseCandidate

Required fields:

- `modality`
- `target_language`
- `level_target`
- `instructions`
- `content`
- `questions`
- `answer_key` or `rubric`
- `tags`

Validation:

- Rendered exercise output <= 1200 characters.
- Target language and level match learner setup.
- Tags normalize through the same tag rules used by vocabulary/progress.
- No audio, image, dashboard, web, cloud, host-adapter, or scheduling claims.

## Validated Exercise Output

Required fields:

- `schema_version`
- `exercise_id`
- `modality`
- `mode`
- `target_language`
- `level_target`
- `focus`
- `instructions`
- `content`
- `questions`
- `answer_key_summary`
- `rubric_summary`
- `tags`
- `rendered_char_count`
- `repair_attempts_used`
- `scope_guardrails`

Guardrails must include:

- `text_only`
- `terminal_readable`
- `feedback_envelope_unchanged`
- `no_new_persistence`

## TextModalityRecordInput

Required fields:

- `exercise_id`
- `modality`
- `learner_response`
- `response_status`
- `candidate_feedback`
- `score_metadata`
- `exercise_summary`

Optional fields:

- `session_id`, default `default`.
- `idempotency_key`.

Validation:

- `candidate_feedback` must validate as existing `FeedbackEnvelope`.
- Rendered feedback <= 900 characters.
- `score_metadata` must contain only JSON scalar/list/object values needed for current modality scoring.
- Empty and abandoned responses cannot create mistake events.

## TextModalityResult

Required fields:

- `schema_version`
- `modality`
- `exercise_id`
- `session_id`
- `response_status`
- `feedback`
- `score_metadata`
- `persisted_mistakes`
- `scope_guardrails`

Nullable fields:

- `answer_event`: null when nothing is persisted.

Rules:

- `feedback` is the unchanged existing `FeedbackEnvelope`.
- `persisted_mistakes` counts only safe mistake spans inserted into `mistake_events`.
- Existing `AnswerEvent` schema remains substitutable after adding `reading` and `lesson` skill values.
- Result wrappers must not include raw private learner data in progress/export surfaces.

## Progress Extension

If implementation exposes text-modality counts in progress:

- Add `reading_answers`.
- Add `lesson_answers`.
- Add `transcript_drills`.

Rules:

- Existing fields remain stable.
- Output remains aggregate-only.
- Progress is derived from existing local SQLite state.
