from __future__ import annotations

from language_tutor.dal.repositories import TutorRepository
from language_tutor.feedback import sanitize_feedback
from language_tutor.schemas import (
    LearnerProfile,
    WritingPromptResult,
    WritingRecordInput,
    WritingRecordResult,
)


def writing_prompt(profile: LearnerProfile) -> WritingPromptResult:
    interest = profile.interests[0] if profile.interests else "daily life"
    prompt = f"Write three {profile.target_language} sentences about {interest}."
    return WritingPromptResult(
        prompt_id=f"prompt-{profile.target_language}-{profile.level_target}",
        prompt=prompt,
        fit={
            "target_language": profile.target_language,
            "level_target": profile.level_target,
            "interest": interest,
            "constraints": profile.constraints,
        },
    )


def record_writing(repo: TutorRepository, payload: WritingRecordInput) -> WritingRecordResult:
    feedback = sanitize_feedback(payload.candidate_feedback)
    event, mistake_count = repo.record_writing_answer(
        payload.session_id, payload.prompt_id, payload.learner_answer, feedback
    )
    return WritingRecordResult(
        feedback=feedback, answer_event=event, persisted_mistakes=mistake_count
    )
