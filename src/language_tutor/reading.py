"""Reading comprehension and transcript-drill orchestration.

Transcript drills are a text-only `tutor-reading` submode (mode=transcript), not a
separate skill and not an audio feature. Both reading and transcript validate generated
candidates through the shared text-modality contracts and persist as the same skill.
"""

from __future__ import annotations

from typing import Any

from language_tutor.dal.repositories import TutorRepository
from language_tutor.errors import TutorError
from language_tutor.schemas import (
    LearnerProfile,
    TextExerciseCandidate,
    TextExerciseMode,
    TextModalityRecordInput,
    TextModalityResult,
    ValidatedTextExercise,
)
from language_tutor.text_modalities import record_text_modality, validate_candidate

_TRANSCRIPT_MODES: frozenset[str] = frozenset(
    {"transcript_reconstruction", "transcript_correction", "transcript_comprehension"}
)


def start_reading(payload: dict[str, Any], profile: LearnerProfile) -> ValidatedTextExercise:
    """Validate a reading or transcript candidate into a presentable exercise."""
    candidate_data = payload.get("candidate")
    if not isinstance(candidate_data, dict):
        raise TutorError(
            "invalid_text_exercise",
            "Reading start payload requires a candidate object.",
            'Pass {"mode":"comprehension","candidate":{...}}.',
        )
    candidate = TextExerciseCandidate.model_validate(candidate_data)
    repair_attempts_used = int(payload.get("repair_attempts_used", 0))
    mode = str(payload.get("mode", "comprehension"))

    if mode == "transcript":
        forced_mode: TextExerciseMode = (
            candidate.mode if candidate.mode in _TRANSCRIPT_MODES else "transcript_reconstruction"
        )
        return validate_candidate(
            candidate,
            target_language=profile.target_language,
            level_target=profile.level_target,
            forced_modality="transcript",
            forced_mode=forced_mode,
            repair_attempts_used=repair_attempts_used,
        )
    return validate_candidate(
        candidate,
        target_language=profile.target_language,
        level_target=profile.level_target,
        forced_modality="reading",
        forced_mode="comprehension",
        repair_attempts_used=repair_attempts_used,
    )


def record_reading(repo: TutorRepository, record_input: TextModalityRecordInput) -> TextModalityResult:
    """Persist a reading or transcript attempt and wrap the unchanged FeedbackEnvelope."""
    return record_text_modality(repo, record_input)
