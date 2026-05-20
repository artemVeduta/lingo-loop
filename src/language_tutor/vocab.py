from __future__ import annotations

from datetime import UTC, datetime

from language_tutor.dal.repositories import TutorRepository
from language_tutor.feedback import vocabulary_feedback
from language_tutor.schemas import (
    LearnerPreferences,
    VocabularyAnswerInput,
    VocabularyAnswerResult,
    VocabularySessionPlan,
)
from language_tutor.srs import quality_for_verdict, schedule_review


def queue_size(preferences: LearnerPreferences) -> int:
    multiplier = {"light": 0.5, "normal": 1.0, "heavy": 1.5}[str(preferences.review_intensity)]
    return max(1, round(preferences.session_length * multiplier))


def start_vocab(
    repo: TutorRepository, target_language: str, preferences: LearnerPreferences
) -> VocabularySessionPlan:
    limit = queue_size(preferences)
    items = repo.due_vocabulary(limit, datetime.now(UTC))
    if not items:
        repo.seed_default_vocabulary(target_language)
        items = repo.due_vocabulary(limit, datetime.now(UTC))
    return VocabularySessionPlan(
        items=items, requested_count=limit, starter_content_required=not bool(items)
    )


def answer_vocab(
    repo: TutorRepository, payload: VocabularyAnswerInput, preferences: LearnerPreferences
) -> VocabularyAnswerResult:
    item = repo.get_vocabulary_item(payload.item_id)
    feedback = vocabulary_feedback(
        payload.answer, item.accepted_answers, preferences.transliteration_tolerance
    )
    next_state = schedule_review(item.state, feedback.verdict)
    quality = quality_for_verdict(feedback.verdict)
    return repo.record_vocab_answer(
        item=item,
        session_id=payload.session_id,
        answer=payload.answer,
        idempotency_key=payload.idempotency_key,
        feedback=feedback,
        previous_state=item.state,
        next_state=next_state,
        quality=quality,
    )
