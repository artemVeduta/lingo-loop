# Contract: Text Modality Semantic Eval

## Scope

Semantic evals cover feedback quality for:

- Reading comprehension.
- Guided micro-lessons.
- Transcript drills.

## Fixtures

Minimum fixture set:

- 3 representative reading fixtures.
- 3 representative lesson fixtures.
- 3 representative transcript fixtures.

Each fixture must define:

- Candidate exercise or lesson.
- Learner response.
- Expected verdict or rubric outcome.
- Required tags.
- Unsafe definitive correction conditions.

## Run Count

Each fixture must run 5 live evaluations.

## Acceptance Threshold

For each fixture:

- Feedback schema-valid: 5/5.
- Expected verdict or rubric outcome: at least 4/5.
- Required tags present across the 5-run set.
- Unsafe definitive corrections: 0.

## Failure Handling

Any fixture below threshold fails the semantic-eval gate. The implementation may adjust prompts, validators, or evaluator instructions, but must keep `FeedbackEnvelope` unchanged and must not add modality-specific feedback models.
