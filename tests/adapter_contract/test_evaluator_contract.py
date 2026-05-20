from __future__ import annotations

from language_tutor.schemas import FeedbackEnvelope


def test_feedback_envelope_contract_requires_hint() -> None:
    feedback = FeedbackEnvelope(explanation="Ok", next_drill_hint="Try again.")
    assert feedback.next_drill_hint == "Try again."
