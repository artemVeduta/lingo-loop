from __future__ import annotations

from language_tutor.feedback import render_feedback
from language_tutor.schemas import FeedbackEnvelope


def test_feedback_renderer_has_ascii_fallback() -> None:
    feedback = FeedbackEnvelope(explanation="Use case.", next_drill_hint="Decline one noun.")
    assert "[!] Verdict" in render_feedback(feedback, ascii_fallback=True)
