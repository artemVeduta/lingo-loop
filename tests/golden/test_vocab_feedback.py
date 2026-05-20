from __future__ import annotations

from language_tutor.feedback import render_feedback, vocabulary_feedback


def test_vocab_feedback_markdown() -> None:
    feedback = vocabulary_feedback("privit", ["привіт", "privit"], transliteration_tolerance=True)
    assert "Verdict: correct" in render_feedback(feedback)
