from __future__ import annotations

from pydantic import ValidationError

from language_tutor.feedback import sanitize_feedback
from language_tutor.schemas import Confidence, FeedbackEnvelope, Severity, Verdict


def validate_evaluator_output(candidate: object) -> FeedbackEnvelope:
    try:
        feedback = FeedbackEnvelope.model_validate(candidate)
    except ValidationError:
        return safe_fallback()
    return sanitize_feedback(feedback)


def safe_fallback() -> FeedbackEnvelope:
    return FeedbackEnvelope(
        verdict=Verdict.NEEDS_REVIEW,
        corrected_answer="",
        severity=Severity.LOW,
        confidence=Confidence.LOW,
        explanation="Feedback could not be validated safely.",
        next_drill_hint="Try one shorter sentence and request review again.",
    )
