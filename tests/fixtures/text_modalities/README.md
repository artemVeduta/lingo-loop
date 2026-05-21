# Text Modality Fixtures

Deterministic and semantic-eval fixtures for Phase 5 text modalities.

| File | Purpose | Used by |
|------|---------|---------|
| `skill_pressure.json` | Skill trigger-boundary pressure scenarios (existing + new skills) | T018, T033, T049 |
| `reading.json` | 3 representative reading comprehension semantic-eval fixtures | T032, T042 |
| `lesson.json` | 3 representative micro-lesson semantic-eval fixtures | T048, T058 |
| `transcript.json` | 3 representative transcript drill semantic-eval fixtures | T065, T071 |

## Semantic-eval fixture shape

Each semantic-eval fixture defines (per `contracts/semantic-eval.md`):

- `id`: stable fixture id.
- `candidate`: `TextExerciseCandidate` JSON.
- `learner_response`: learner answer text.
- `expected_verdict`: expected `FeedbackEnvelope.verdict` (or rubric outcome).
- `required_tags`: tags that must appear across the 5-run set.
- `unsafe_definitive_correction`: condition that must never occur.

## Run policy

5 live evaluations per fixture. Schema-valid 5/5, expected verdict ≥4/5, required tags
present across the run set, zero unsafe definitive corrections.
