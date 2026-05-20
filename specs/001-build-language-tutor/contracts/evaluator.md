# Evaluator Contract

The evaluator is a stateless `tutor-judge` subagent used for free-writing feedback. It does not read local files, query SQLite, or persist state.

## Input

```json
{
  "profile": {
    "native_language": "en",
    "target_language": "uk",
    "level_target": "A2",
    "interests": ["daily life"]
  },
  "preferences": {
    "feedback_verbosity": "concise",
    "transliteration_tolerance": false
  },
  "prompt": "Write three sentences about your morning.",
  "learner_answer": "...",
  "allowed_error_tags": ["CASE_GENITIVE", "ASPECT_PERFECTIVE_NEEDED", "UNCATEGORIZED"],
  "feedback_detail": "concise",
  "max_feedback_items": 3
}
```

## Output

Output must be a `FeedbackEnvelope` JSON object. Freeform prose outside the JSON object is invalid.

Required fields:

- `verdict`
- `corrected_answer`
- `severity`
- `confidence` (`high`, `medium`, or `low`)
- `error_spans`
- `explanation`
- `next_drill_hint`

## Validation Rules

- `error_spans[].tag` must be in the controlled vocabulary.
- `confidence` must be one of `high`, `medium`, or `low`; missing or invalid confidence is treated as `low`.
- `explanation` and `next_drill_hint` render in the learner native language.
- `feedback_detail` is derived from learner feedback verbosity and controls explanation length, not required fields.
- `corrected_answer` and span text remain in the target language.
- Low confidence feedback renders as tentative and cannot be persisted as a definitive high-severity correction. Definitive high-severity corrections require `confidence == "high"`.
- Malformed, contradictory, or unsupported output retries once with a stricter prompt. Second failure downgrades to a safe fallback and records no definitive correction.
- Writing feedback creates `MistakeEvent` rows only; it does not update vocabulary SRS schedules by default.

## Semantic Fixture Gates

- The accepted writing fixture set contains at least 20 non-empty, schema-valid submissions.
- Slavic fixtures cover case, aspect, gender/agreement, animacy, verbs of motion, punctuation, and Russian/Ukrainian interference.
- Known-correct sentences must not receive definitive high-severity corrections.
- Expected core tags must be present for at least the threshold defined in the feature success criteria.
