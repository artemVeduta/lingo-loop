from __future__ import annotations

from language_tutor.evaluators import validate_evaluator_output


def test_invalid_evaluator_output_downgrades() -> None:
    feedback = validate_evaluator_output({"bad": "shape"})
    assert feedback.confidence == "low"
    assert feedback.next_drill_hint
