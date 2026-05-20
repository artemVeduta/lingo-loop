from __future__ import annotations

import json
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


def utc_now() -> datetime:
    return datetime.now(UTC).replace(microsecond=0)


class TutorModel(BaseModel):
    model_config = ConfigDict(extra="forbid", use_enum_values=True)


class ReviewIntensity(StrEnum):
    LIGHT = "light"
    NORMAL = "normal"
    HEAVY = "heavy"


class FeedbackVerbosity(StrEnum):
    CONCISE = "concise"
    STANDARD = "standard"
    DETAILED = "detailed"


class Confidence(StrEnum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class Severity(StrEnum):
    NONE = "none"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class Verdict(StrEnum):
    CORRECT = "correct"
    PARTIAL = "partial"
    MISSED = "missed"
    UNANSWERED = "unanswered"
    NEEDS_REVIEW = "needs_review"


class ErrorTag(StrEnum):
    CASE = "case"
    ASPECT = "aspect"
    AGREEMENT = "agreement"
    ANIMACY = "animacy"
    VERBS_OF_MOTION = "verbs_of_motion"
    PUNCTUATION = "punctuation"
    INTERFERENCE = "interference"
    VOCABULARY = "vocabulary"
    SPELLING = "spelling"
    WORD_ORDER = "word_order"
    UNCATEGORIZED = "uncategorized"


class LearnerProfile(TutorModel):
    schema_version: int = 1
    native_language: str
    target_language: str
    level_target: str = "A1"
    interests: list[str] = Field(default_factory=list)
    constraints: list[str] = Field(default_factory=list)
    created_at: datetime | None = None
    updated_at: datetime | None = None

    @field_validator("native_language", "target_language", "level_target")
    @classmethod
    def non_empty(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("must not be empty")
        return value


class LearnerPreferences(TutorModel):
    schema_version: int = 1
    session_length: int = Field(default=10, ge=1, le=60)
    review_intensity: ReviewIntensity = ReviewIntensity.NORMAL
    feedback_verbosity: FeedbackVerbosity = FeedbackVerbosity.CONCISE
    transliteration_tolerance: bool = False
    ascii_fallback: bool = False
    streak_grace_days: int = Field(default=1, ge=0, le=14)
    updated_at: datetime | None = None


class SetupState(TutorModel):
    profile: LearnerProfile
    preferences: LearnerPreferences
    profile_path: str
    preferences_path: str


class SetupWriteResult(TutorModel):
    profile_path: str
    preferences_path: str
    history_touched: bool = False


class ErrorEnvelope(TutorModel):
    error: dict[str, str]


class ErrorSpan(TutorModel):
    start: int | None = None
    end: int | None = None
    text: str = ""
    tag: ErrorTag = ErrorTag.UNCATEGORIZED
    severity: Severity = Severity.LOW
    explanation: str = ""


def empty_error_spans() -> list[ErrorSpan]:
    return []


class FeedbackEnvelope(TutorModel):
    verdict: Verdict = Verdict.NEEDS_REVIEW
    corrected_answer: str = ""
    severity: Severity = Severity.LOW
    confidence: Confidence = Confidence.LOW
    error_spans: list[ErrorSpan] = Field(default_factory=empty_error_spans)
    explanation: str = ""
    next_drill_hint: str = ""
    srs_update: dict[str, Any] | None = None


class BootSection(TutorModel):
    title: str
    lines: list[str] = Field(default_factory=list)


class BootContext(TutorModel):
    profile: LearnerProfile
    preferences: LearnerPreferences
    sections: list[BootSection]
    generated_at: datetime = Field(default_factory=utc_now)
    max_rendered_chars: int = 6000


class VocabularyItemState(TutorModel):
    state: Literal["new", "learning", "review", "mature", "relearning"] = "new"
    ease_factor: float = Field(default=2.5, ge=1.3)
    repetition_count: int = Field(default=0, ge=0)
    interval_days: int = Field(default=0, ge=0)
    due_at: datetime = Field(default_factory=utc_now)


class VocabularyItem(TutorModel):
    id: str
    target_language: str
    prompt: str
    lemma: str | None = None
    accepted_answers: list[str]
    hint: str | None = None
    tags: list[str] = Field(default_factory=list)
    state: VocabularyItemState = Field(default_factory=VocabularyItemState)


class VocabularySessionPlan(TutorModel):
    items: list[VocabularyItem]
    requested_count: int
    starter_content_required: bool = False


class VocabularyAnswerInput(TutorModel):
    item_id: str
    answer: str
    idempotency_key: str
    session_id: str = "default"


class AnswerEvent(TutorModel):
    id: str
    session_id: str
    skill: Literal["vocab", "writing"]
    prompt_ref: str
    learner_answer: str
    outcome: str
    feedback_envelope: FeedbackEnvelope | None = None
    recorded_at: datetime = Field(default_factory=utc_now)


class VocabularyReview(TutorModel):
    id: str
    session_id: str
    vocabulary_item_id: str
    answer_event_id: str
    verdict: Verdict
    quality: int = Field(ge=0, le=5)
    previous_state: VocabularyItemState
    next_state: VocabularyItemState
    reviewed_at: datetime = Field(default_factory=utc_now)


class VocabularyAnswerResult(TutorModel):
    feedback: FeedbackEnvelope
    answer_event: AnswerEvent
    review: VocabularyReview
    duplicate: bool = False


class WritingPromptResult(TutorModel):
    prompt_id: str
    prompt: str
    fit: dict[str, Any]
    learner_provided_allowed: bool = True


class WritingRecordInput(TutorModel):
    prompt_id: str
    learner_answer: str
    candidate_feedback: FeedbackEnvelope
    session_id: str = "default"


class WritingRecordResult(TutorModel):
    feedback: FeedbackEnvelope
    answer_event: AnswerEvent
    persisted_mistakes: int


class ProgressReport(TutorModel):
    streak_days: int
    due_count: int
    weak_patterns: list[str]
    maturity: dict[str, int]
    latest_recap: str | None
    month_to_date_estimated_usd: float | None
    cost_status: Literal["available", "partial", "unavailable"]
    next_action: str


class SessionAnalysis(TutorModel):
    severity_counts: dict[str, int] = Field(default_factory=dict)
    new_tags: list[ErrorTag] = Field(default_factory=list[ErrorTag])
    repeated_tags: list[ErrorTag] = Field(default_factory=list[ErrorTag])
    resolved_tags: list[ErrorTag] = Field(default_factory=list[ErrorTag])
    next_focus: str = "review_due_items"
    summary_for_next_boot: str = ""
    confidence: Confidence = Confidence.LOW


class CostEventInput(TutorModel):
    operation: Literal["writing_evaluator", "session_analyzer"]
    model: str
    input_tokens: int = Field(ge=0)
    output_tokens: int = Field(ge=0)
    cache_read_tokens: int = Field(default=0, ge=0)
    estimated_cost_usd: float | None = Field(default=None, ge=0)
    pricing_source: Literal["host_usage_metadata", "local_pricing_table", "unavailable"]
    source_event_id: str | None = None


class SessionEndInput(TutorModel):
    session_id: str = "default"
    analysis: SessionAnalysis | None = None
    costs: list[CostEventInput] = Field(default_factory=list[CostEventInput])


class SessionEndResult(TutorModel):
    session_id: str
    status: Literal["complete", "pending"]
    summary_id: str | None = None
    next_focus: str | None = None


class DoctorCheck(TutorModel):
    name: str
    status: Literal["ok", "fail"]
    repair_hint: str = ""


class DoctorReport(TutorModel):
    checks: list[DoctorCheck]
    learner_data_changed: bool = False


def export_json_schemas(output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    mapping: dict[str, type[BaseModel]] = {
        "boot_context.schema.json": BootContext,
        "feedback_envelope.schema.json": FeedbackEnvelope,
        "session_analysis.schema.json": SessionAnalysis,
        "answer_event.schema.json": AnswerEvent,
    }
    for filename, model in mapping.items():
        (output_dir / filename).write_text(
            json.dumps(model.model_json_schema(), ensure_ascii=False, indent=2, sort_keys=True),
            encoding="utf-8",
        )
