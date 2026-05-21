from __future__ import annotations

from language_tutor.feedback import render_feedback
from language_tutor.reading import start_reading
from language_tutor.schemas import FeedbackEnvelope, LearnerProfile
from language_tutor.text_modalities import (
    RENDERED_EXERCISE_BUDGET,
    RENDERED_FEEDBACK_BUDGET,
    render_exercise,
)
from tests.fixtures.text_modalities.builders import (
    lesson_candidate,
    reading_candidate,
    transcript_candidate,
)

PROFILE = LearnerProfile(native_language="en", target_language="Ukrainian", level_target="A2")


def test_reading_exercise_render_is_within_budget_and_deterministic() -> None:
    exercise = start_reading({"mode": "comprehension", "candidate": reading_candidate()}, PROFILE)
    rendered = render_exercise(exercise)
    assert len(rendered) <= RENDERED_EXERCISE_BUDGET
    assert exercise.rendered_char_count == len(rendered)
    assert render_exercise(exercise) == rendered
    assert "Questions:" in rendered
    assert "1. Що купила Марія?" in rendered


def test_lesson_exercise_render_is_within_budget() -> None:
    from language_tutor.lessons import start_lesson

    exercise = start_lesson({"candidate": lesson_candidate()}, PROFILE)
    rendered = render_exercise(exercise)
    assert len(rendered) <= RENDERED_EXERCISE_BUDGET
    assert exercise.mode == "lesson"


def test_transcript_render_is_text_only_and_within_budget() -> None:
    exercise = start_reading({"mode": "transcript", "candidate": transcript_candidate()}, PROFILE)
    rendered = render_exercise(exercise)
    assert len(rendered) <= RENDERED_EXERCISE_BUDGET
    assert exercise.modality == "transcript"
    lowered = rendered.lower()
    assert "audio" not in lowered
    assert "listen" not in lowered
    assert "play" not in lowered


def test_feedback_render_is_within_budget() -> None:
    feedback = FeedbackEnvelope(
        explanation="Use the accusative case.", next_drill_hint="Decline one noun."
    )
    rendered = render_feedback(feedback)
    assert len(rendered) <= RENDERED_FEEDBACK_BUDGET
    assert "Verdict" in rendered
