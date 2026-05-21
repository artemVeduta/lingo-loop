"""Guided micro-lesson orchestration.

A micro-lesson is one focused, bounded topic (a weak tag, a common error, or a
learner-selected topic) plus a single practice step. Generated candidates are validated
through the shared text-modality contracts; feedback is the unchanged FeedbackEnvelope.
"""

from __future__ import annotations

from typing import Any

from language_tutor.dal.repositories import TutorRepository
from language_tutor.errors import TutorError
from language_tutor.schemas import (
    LearnerProfile,
    TextExerciseCandidate,
    TextModalityRecordInput,
    TextModalityResult,
    ValidatedTextExercise,
)
from language_tutor.text_modalities import record_text_modality, validate_candidate


def start_lesson(payload: dict[str, Any], profile: LearnerProfile) -> ValidatedTextExercise:
    """Validate a micro-lesson candidate into a presentable, bounded lesson."""
    candidate_data = payload.get("candidate")
    if not isinstance(candidate_data, dict):
        raise TutorError(
            "invalid_text_exercise",
            "Lesson start payload requires a candidate object.",
            'Pass {"candidate":{...}}.',
        )
    candidate = TextExerciseCandidate.model_validate(candidate_data)
    repair_attempts_used = int(payload.get("repair_attempts_used", 0))
    return validate_candidate(
        candidate,
        target_language=profile.target_language,
        level_target=profile.level_target,
        forced_modality="lesson",
        forced_mode="lesson",
        repair_attempts_used=repair_attempts_used,
    )


def record_lesson(repo: TutorRepository, record_input: TextModalityRecordInput) -> TextModalityResult:
    """Persist a lesson attempt and wrap the unchanged FeedbackEnvelope."""
    return record_text_modality(repo, record_input)
