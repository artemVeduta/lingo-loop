"""Shared validation, budgets, repair/refusal, and safe-signal helpers for text modalities.

This module is the single source of truth for the rules every text modality
(reading, lesson, transcript) shares. Reading and lesson orchestration compose these
helpers; they do not re-implement budgets, guardrails, or mistake filtering.
"""

from __future__ import annotations

import hashlib
from typing import Literal, cast

from language_tutor.dal.repositories import TutorRepository
from language_tutor.errors import TutorError
from language_tutor.feedback import render_feedback, sanitize_feedback
from language_tutor.schemas import (
    AnswerEvent,
    Confidence,
    ErrorSpan,
    FeedbackEnvelope,
    Severity,
    StoredSkill,
    TextExerciseCandidate,
    TextExerciseMode,
    TextModality,
    TextModalityRecordInput,
    TextModalityResult,
    TextResponseStatus,
    ValidatedTextExercise,
)
from language_tutor.vocab import normalize_tag

RENDERED_EXERCISE_BUDGET = 1200
RENDERED_FEEDBACK_BUDGET = 900
MAX_REPAIR_ATTEMPTS = 1

# Default mode per modality when the candidate omits an explicit mode.
DEFAULT_MODE: dict[TextModality, TextExerciseMode] = {
    "reading": "comprehension",
    "lesson": "lesson",
    "transcript": "transcript_reconstruction",
}

# Stored answer_events.skill per modality. Transcript persists as reading.
STORED_SKILL: dict[TextModality, StoredSkill] = {
    "reading": "reading",
    "lesson": "lesson",
    "transcript": "reading",
}

# Audio/host/scope claims that must never appear in a text-only exercise.
_FORBIDDEN_SCOPE_TERMS = (
    "play the audio",
    "play audio",
    "audio clip",
    "audio file",
    "press play",
    "listen to the recording",
    "listen to the audio",
    "speech recognition",
    "microphone",
    "record your voice",
    "voice recording",
    "sound file",
    "image below",
    "see the picture",
    "dashboard",
    "open the web",
    "cloud sync",
    "schedule a reminder",
)

# Statuses that never produce taggable mistake events.
_NO_MISTAKE_STATUSES: frozenset[TextResponseStatus] = frozenset(
    {"empty", "abandoned", "refused"}
)


def render_exercise(exercise: ValidatedTextExercise) -> str:
    """Deterministic terminal rendering of a validated exercise."""
    lines = [
        f"Modality: {exercise.modality} ({exercise.mode})",
        f"Target: {exercise.target_language} {exercise.level_target}",
        f"Focus: {exercise.focus or 'general'}",
        "",
        f"Instructions: {exercise.instructions}",
        "",
        exercise.content,
        "",
        "Questions:",
    ]
    lines.extend(f"{index}. {question}" for index, question in enumerate(exercise.questions, 1))
    return "\n".join(lines)


def _rendered_char_count(
    modality: TextModality,
    mode: TextExerciseMode,
    target_language: str,
    level_target: str,
    focus: str,
    instructions: str,
    content: str,
    questions: list[str],
) -> int:
    probe = ValidatedTextExercise(
        exercise_id="probe",
        modality=modality,
        mode=mode,
        target_language=target_language,
        level_target=level_target,
        focus=focus,
        instructions=instructions,
        content=content,
        questions=questions,
        answer_key_summary="",
        rubric_summary="",
        tags=[],
        rendered_char_count=0,
    )
    return len(render_exercise(probe))


def deterministic_exercise_id(modality: TextModality, content: str, questions: list[str]) -> str:
    digest = hashlib.sha256(
        (content + " ".join(questions)).encode("utf-8")
    ).hexdigest()[:12]
    return f"{modality}_{digest}"


def _summarize(values: list[str]) -> str:
    return "; ".join(values)


def validate_candidate(
    candidate: TextExerciseCandidate,
    *,
    target_language: str,
    level_target: str,
    forced_modality: TextModality | None = None,
    forced_mode: TextExerciseMode | None = None,
    repair_attempts_used: int = 0,
) -> ValidatedTextExercise:
    """Validate a generated candidate into a presentable exercise.

    Raises TutorError with a learner-facing repair hint on any rule violation.
    """
    modality = forced_modality or candidate.modality
    if forced_modality and candidate.modality != forced_modality:
        raise TutorError(
            "invalid_text_exercise",
            f"Candidate modality must be {forced_modality}.",
            f"Set candidate.modality to {forced_modality}.",
        )
    mode = forced_mode or candidate.mode or DEFAULT_MODE[modality]

    if normalize_tag(candidate.target_language) != normalize_tag(target_language):
        raise TutorError(
            "invalid_text_exercise",
            "Candidate target language does not match learner setup.",
            f"Generate the exercise in {target_language}.",
        )
    if normalize_tag(candidate.level_target) != normalize_tag(level_target):
        raise TutorError(
            "invalid_text_exercise",
            "Candidate level does not match learner setup.",
            f"Generate the exercise at level {level_target}.",
        )

    _reject_out_of_scope(candidate)

    rendered = _rendered_char_count(
        modality,
        mode,
        candidate.target_language,
        candidate.level_target,
        candidate.focus,
        candidate.instructions,
        candidate.content,
        candidate.questions,
    )
    if rendered > RENDERED_EXERCISE_BUDGET:
        raise TutorError(
            "text_exercise_too_long",
            f"Rendered exercise is {rendered} characters (max {RENDERED_EXERCISE_BUDGET}).",
            "Shorten the passage, questions, or instructions and regenerate.",
        )

    return ValidatedTextExercise(
        exercise_id=deterministic_exercise_id(modality, candidate.content, candidate.questions),
        modality=modality,
        mode=mode,
        target_language=candidate.target_language,
        level_target=candidate.level_target,
        focus=candidate.focus,
        instructions=candidate.instructions,
        content=candidate.content,
        questions=candidate.questions,
        answer_key_summary=_summarize(candidate.answer_key),
        rubric_summary=_summarize(candidate.rubric),
        tags=[normalize_tag(tag) for tag in candidate.tags],
        rendered_char_count=rendered,
        repair_attempts_used=repair_attempts_used,
    )


def _reject_out_of_scope(candidate: TextExerciseCandidate) -> None:
    haystack = " ".join(
        [candidate.instructions, candidate.content, *candidate.questions]
    ).casefold()
    for term in _FORBIDDEN_SCOPE_TERMS:
        if term in haystack:
            raise TutorError(
                "invalid_text_exercise",
                "Candidate implies audio, image, or host-specific behavior.",
                "Keep the exercise text-only with no audio, image, or host claims.",
            )


def ensure_feedback_budget(feedback_render: str) -> None:
    """Raise if rendered feedback exceeds the terminal budget."""
    if len(feedback_render) > RENDERED_FEEDBACK_BUDGET:
        raise TutorError(
            "text_feedback_too_long",
            f"Rendered feedback is {len(feedback_render)} characters "
            f"(max {RENDERED_FEEDBACK_BUDGET}).",
            "Shorten the explanation or correction and regenerate feedback.",
        )


def safe_mistake_spans(
    feedback: FeedbackEnvelope, response_status: TextResponseStatus
) -> list[ErrorSpan]:
    """Return only the error spans that may be persisted as mistake events.

    Empty, abandoned, and refused responses never emit mistakes. Low-confidence
    high-severity spans are dropped (mirrors writing persistence).
    """
    if response_status in _NO_MISTAKE_STATUSES:
        return []
    spans: list[ErrorSpan] = []
    for span in feedback.error_spans:
        if feedback.confidence == Confidence.LOW and span.severity == Severity.HIGH:
            continue
        spans.append(span)
    return spans


def record_text_modality(
    repo: TutorRepository, record_input: TextModalityRecordInput
) -> TextModalityResult:
    """Shared record path for reading, lesson, and transcript attempts.

    Sanitizes feedback, enforces the feedback budget, persists a safe answer event plus
    safe mistake events, and wraps the unchanged FeedbackEnvelope in a TextModalityResult.
    """
    feedback = sanitize_feedback(record_input.candidate_feedback)
    ensure_feedback_budget(render_feedback(feedback))
    status = record_input.response_status

    answer_event: AnswerEvent | None = None
    persisted = 0
    if status != "refused":
        spans = safe_mistake_spans(feedback, status)
        skill = cast(Literal["reading", "lesson"], STORED_SKILL[record_input.modality])
        outcome = str(feedback.verdict) if status == "completed" else status
        event, persisted = repo.record_text_modality_answer(
            skill=skill,
            session_id=record_input.session_id,
            prompt_ref=record_input.exercise_id,
            learner_answer=record_input.learner_response,
            outcome=outcome,
            feedback=feedback,
            safe_spans=spans,
            idempotency_key=record_input.idempotency_key,
        )
        answer_event = event

    return TextModalityResult(
        modality=record_input.modality,
        exercise_id=record_input.exercise_id,
        session_id=record_input.session_id,
        response_status=status,
        feedback=feedback,
        score_metadata=record_input.score_metadata,
        answer_event=answer_event,
        persisted_mistakes=persisted,
    )
