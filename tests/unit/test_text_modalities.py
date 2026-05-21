from __future__ import annotations

import pytest

from language_tutor.errors import TutorError
from language_tutor.schemas import (
    Confidence,
    ErrorSpan,
    ErrorTag,
    FeedbackEnvelope,
    Severity,
    TextExerciseCandidate,
    Verdict,
)
from language_tutor.text_modalities import (
    MAX_REPAIR_ATTEMPTS,
    RENDERED_EXERCISE_BUDGET,
    RENDERED_FEEDBACK_BUDGET,
    STORED_SKILL,
    ensure_feedback_budget,
    render_exercise,
    safe_mistake_spans,
    validate_candidate,
)


def _candidate(**overrides: object) -> TextExerciseCandidate:
    base: dict[str, object] = {
        "modality": "reading",
        "target_language": "Ukrainian",
        "level_target": "A2",
        "focus": "case",
        "instructions": "Read the passage and answer briefly.",
        "content": "Марія купила книгу в магазині.",
        "questions": ["Що купила Марія?"],
        "answer_key": ["книгу"],
        "rubric": ["Mentions the correct object in the accusative case."],
        "tags": ["case"],
    }
    base.update(overrides)
    return TextExerciseCandidate.model_validate(base)


def test_valid_candidate_produces_validated_exercise() -> None:
    exercise = validate_candidate(
        _candidate(), target_language="Ukrainian", level_target="A2"
    )
    assert exercise.modality == "reading"
    assert exercise.mode == "comprehension"
    assert exercise.exercise_id.startswith("reading_")
    assert exercise.rendered_char_count <= RENDERED_EXERCISE_BUDGET
    assert exercise.rendered_char_count == len(render_exercise(exercise))
    assert exercise.scope_guardrails == [
        "text_only",
        "terminal_readable",
        "feedback_envelope_unchanged",
        "no_new_persistence",
    ]
    assert exercise.tags == ["case"]


def test_candidate_requires_answer_key_or_rubric() -> None:
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        _candidate(answer_key=[], rubric=[])


def test_language_mismatch_is_rejected() -> None:
    with pytest.raises(TutorError) as exc:
        validate_candidate(_candidate(), target_language="Polish", level_target="A2")
    assert exc.value.code == "invalid_text_exercise"


def test_level_mismatch_is_rejected() -> None:
    with pytest.raises(TutorError) as exc:
        validate_candidate(_candidate(), target_language="Ukrainian", level_target="B2")
    assert exc.value.code == "invalid_text_exercise"


def test_over_budget_exercise_is_rejected() -> None:
    with pytest.raises(TutorError) as exc:
        validate_candidate(
            _candidate(content="х" * (RENDERED_EXERCISE_BUDGET + 50)),
            target_language="Ukrainian",
            level_target="A2",
        )
    assert exc.value.code == "text_exercise_too_long"


def test_audio_scope_claim_is_rejected() -> None:
    with pytest.raises(TutorError) as exc:
        validate_candidate(
            _candidate(instructions="Press play and listen to the recording."),
            target_language="Ukrainian",
            level_target="A2",
        )
    assert exc.value.code == "invalid_text_exercise"


def test_forced_modality_mismatch_rejected() -> None:
    with pytest.raises(TutorError):
        validate_candidate(
            _candidate(modality="lesson"),
            target_language="Ukrainian",
            level_target="A2",
            forced_modality="reading",
        )


def test_transcript_stored_as_reading() -> None:
    assert STORED_SKILL["transcript"] == "reading"
    assert STORED_SKILL["reading"] == "reading"
    assert STORED_SKILL["lesson"] == "lesson"
    exercise = validate_candidate(
        _candidate(modality="transcript", mode="transcript_reconstruction"),
        target_language="Ukrainian",
        level_target="A2",
    )
    assert exercise.exercise_id.startswith("transcript_")


def test_repair_attempts_threshold() -> None:
    assert MAX_REPAIR_ATTEMPTS == 1
    exercise = validate_candidate(
        _candidate(), target_language="Ukrainian", level_target="A2", repair_attempts_used=1
    )
    assert exercise.repair_attempts_used == 1


def test_feedback_budget_guard() -> None:
    ensure_feedback_budget("ok")
    with pytest.raises(TutorError) as exc:
        ensure_feedback_budget("x" * (RENDERED_FEEDBACK_BUDGET + 1))
    assert exc.value.code == "text_feedback_too_long"


def _feedback(spans: list[ErrorSpan], confidence: Confidence = Confidence.MEDIUM) -> FeedbackEnvelope:
    return FeedbackEnvelope(
        verdict=Verdict.PARTIAL,
        severity=Severity.LOW,
        confidence=confidence,
        error_spans=spans,
        explanation="ok",
        next_drill_hint="practice",
    )


def test_safe_mistake_spans_drops_low_confidence_high_severity() -> None:
    spans = [
        ErrorSpan(text="a", tag=ErrorTag.CASE, severity=Severity.HIGH),
        ErrorSpan(text="b", tag=ErrorTag.CASE, severity=Severity.LOW),
    ]
    kept = safe_mistake_spans(_feedback(spans, Confidence.LOW), "completed")
    assert [span.text for span in kept] == ["b"]


@pytest.mark.parametrize("status", ["empty", "abandoned", "refused"])
def test_no_mistakes_for_non_answering_statuses(status: str) -> None:
    spans = [ErrorSpan(text="a", tag=ErrorTag.CASE, severity=Severity.LOW)]
    assert safe_mistake_spans(_feedback(spans), status) == []  # type: ignore[arg-type]
