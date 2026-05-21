# Contract: Text Modality CLI

## Reading Start

Command:

```bash
rtk bin/tutor reading start --json '<payload>'
```

Payload:

```json
{
  "mode": "comprehension",
  "candidate": {
    "modality": "reading",
    "target_language": "Ukrainian",
    "level_target": "A2",
    "focus": "case",
    "instructions": "Answer the questions in short phrases.",
    "content": "...",
    "questions": ["..."],
    "answer_key": ["..."],
    "rubric": ["..."],
    "tags": ["case"]
  }
}
```

Success output: validated reading exercise JSON.

Failure output: standard error envelope with a repair hint. Invalid candidates may be retried once by the skill before refusal.

## Reading Transcript Start

Command:

```bash
rtk bin/tutor reading start --json '<payload>'
```

Payload difference:

```json
{
  "mode": "transcript",
  "candidate": {
    "modality": "transcript",
    "mode": "transcript_reconstruction"
  }
}
```

Success output: validated transcript drill JSON. Output must remain text-only and must not imply audio support.

## Reading Record

Command:

```bash
rtk bin/tutor reading record --json '<payload>'
```

Payload:

```json
{
  "exercise_id": "reading_...",
  "modality": "reading",
  "session_id": "default",
  "idempotency_key": "optional-client-key",
  "learner_response": "...",
  "response_status": "completed",
  "candidate_feedback": {
    "verdict": "partial",
    "corrected_answer": "",
    "severity": "low",
    "confidence": "medium",
    "error_spans": [],
    "explanation": "...",
    "next_drill_hint": "..."
  },
  "score_metadata": {
    "questions_total": 3,
    "questions_correct": 2
  },
  "exercise_summary": "Short learner-safe summary."
}
```

Success output: `TextModalityResult`.

Persistence:

- Stores an `answer_events` row with `skill=reading`.
- Stores safe mistake events from the embedded feedback.
- Transcript uses `skill=reading` and `modality=transcript`.

## Lesson Start

Command:

```bash
rtk bin/tutor lesson start --json '<payload>'
```

Payload:

```json
{
  "candidate": {
    "modality": "lesson",
    "target_language": "Ukrainian",
    "level_target": "A2",
    "focus": "verbs_of_motion",
    "instructions": "Read the explanation, then complete the practice step.",
    "content": "...",
    "questions": ["..."],
    "answer_key": ["..."],
    "rubric": ["..."],
    "tags": ["verbs_of_motion"]
  }
}
```

Success output: validated micro-lesson JSON.

## Lesson Record

Command:

```bash
rtk bin/tutor lesson record --json '<payload>'
```

Payload follows `TextModalityRecordInput` with `modality=lesson`.

Persistence:

- Stores an `answer_events` row with `skill=lesson`.
- Stores safe mistake events from embedded feedback.

## CLI Error Rules

- Invalid JSON returns `invalid_json`.
- Invalid candidate returns `invalid_text_exercise`.
- Over-budget exercise returns `text_exercise_too_long`.
- Over-budget feedback returns `text_feedback_too_long`.
- Invalid record payload returns `invalid_text_modality_record`.
- Refusal after one failed repair records no answer event and no mistake events.
