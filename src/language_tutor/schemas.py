from __future__ import annotations

import json
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from typing import Any, Literal, cast

from pydantic import BaseModel, ConfigDict, Field, computed_field, field_validator, model_validator


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
    cloze_sentence: str | None = None
    accepted_answer: str | None = None
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
    card_type: Literal["standard", "cloze"] = "standard"
    target_language: str
    prompt: str
    lemma: str | None = None
    accepted_answers: list[str]
    hint: str | None = None
    notes: list[str] = Field(default_factory=list)
    sources: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    state: VocabularyItemState = Field(default_factory=VocabularyItemState)


class WeakTagSourceCounts(TutorModel):
    mistake_events: int = Field(default=0, ge=0)
    low_quality_reviews: int = Field(default=0, ge=0)


class WeakTagSignal(TutorModel):
    tag: str
    session_count: int = Field(ge=2)
    latest_seen_at: datetime
    priority_rank: int = Field(ge=1)
    source_counts: WeakTagSourceCounts = Field(default_factory=WeakTagSourceCounts)


class SelectionReason(TutorModel):
    item_id: str
    rank: int = Field(ge=1)
    bucket: Literal["overdue_due", "due_today", "new_fill"]
    reasons: list[
        Literal[
            "overdue",
            "due",
            "weak_tag_match",
            "explicit_filter_match",
            "reserved_non_weak_due",
            "new_card_fill",
        ]
    ]
    matched_weak_tags: list[str] = Field(default_factory=list)
    due_at: datetime | None = None


class SelectionPolicy(TutorModel):
    due_first: bool = True
    weak_tag_limit: int = 5
    recent_session_limit: int = 10
    reserved_non_weak_due_slot: bool = False
    intensity: ReviewIntensity = ReviewIntensity.NORMAL


def empty_weak_tag_signals() -> list[WeakTagSignal]:
    return []


def empty_selection_reasons() -> list[SelectionReason]:
    return []


class VocabularySessionPlan(TutorModel):
    items: list[VocabularyItem]
    requested_count: int
    effective_count: int | None = None
    starter_content_required: bool = False
    filter: list[str] = Field(default_factory=list)
    matching_count: int | None = None
    due_matching_count: int | None = None
    empty_reason: Literal["no_matching_cards", "matching_cards_not_due"] | None = None
    active_weak_tags: list[WeakTagSignal] = Field(default_factory=empty_weak_tag_signals)
    selection_reasons: list[SelectionReason] = Field(default_factory=empty_selection_reasons)
    selection_policy: SelectionPolicy = Field(default_factory=SelectionPolicy)


def _clean_string(value: str, field_name: str) -> str:
    value = value.strip()
    if not value:
        raise ValueError(f"{field_name} must not be empty")
    return value


def _clean_string_list(values: list[str], field_name: str) -> list[str]:
    cleaned: list[str] = []
    seen: set[str] = set()
    for value in values:
        text = _clean_string(value, field_name)
        key = text.casefold()
        if key not in seen:
            cleaned.append(text)
            seen.add(key)
    if not cleaned:
        raise ValueError(f"{field_name} must contain at least one value")
    return cleaned


class VocabularyCardDefinition(TutorModel):
    card_type: Literal["standard", "cloze"] = "standard"
    target: str
    prompt: str
    accepted_answers: list[str]
    hint: str | None = None
    notes: str | list[str] | None = None
    source: str | list[str] | None = None
    tags: list[str] = Field(default_factory=list)

    @field_validator("target", "prompt")
    @classmethod
    def required_text(cls, value: str) -> str:
        return _clean_string(value, "field")

    @field_validator("accepted_answers")
    @classmethod
    def required_answers(cls, value: list[str]) -> list[str]:
        return _clean_string_list(value, "accepted_answers")

    @field_validator("tags")
    @classmethod
    def valid_tags(cls, value: list[str]) -> list[str]:
        if not value:
            return []
        return _clean_string_list(value, "tags")

    @field_validator("notes", "source")
    @classmethod
    def valid_metadata(cls, value: str | list[str] | None) -> str | list[str] | None:
        if value is None:
            return None
        if isinstance(value, str):
            return _clean_string(value, "metadata")
        return _clean_string_list(value, "metadata")

    @model_validator(mode="after")
    def valid_cloze(self) -> VocabularyCardDefinition:
        marker_count = self.prompt.count("{{answer}}")
        if self.card_type == "cloze" and marker_count != 1:
            raise ValueError("cloze prompt must contain exactly one {{answer}} marker")
        return self

    def notes_list(self) -> list[str]:
        if self.notes is None:
            return []
        return [self.notes] if isinstance(self.notes, str) else list(self.notes)

    def sources_list(self) -> list[str]:
        if self.source is None:
            return []
        return [self.source] if isinstance(self.source, str) else list(self.source)


class VocabularyCardAddResult(TutorModel):
    status: Literal["created", "duplicate"]
    item_id: str
    duplicate: bool = False
    message: str
    repair_hint: str | None = None


class SeedImportRequest(TutorModel):
    path: str

    @field_validator("path")
    @classmethod
    def valid_path(cls, value: str) -> str:
        return _clean_string(value, "path")


class SeedImportEntryResult(TutorModel):
    index: int = Field(ge=0)
    status: Literal["created", "updated", "skipped", "invalid"]
    item_id: str | None = None
    code: str | None = None
    message: str | None = None
    repair_hint: str | None = None


def empty_seed_import_entries() -> list[SeedImportEntryResult]:
    return []


class SeedImportResult(TutorModel):
    path: str
    created_count: int = 0
    updated_count: int = 0
    skipped_count: int = 0
    invalid_count: int = 0
    entries: list[SeedImportEntryResult] = Field(default_factory=empty_seed_import_entries)


class VocabularyDrillRequest(TutorModel):
    tags: list[str] | None = None
    requested_count: int | None = Field(default=None, ge=1, le=100)

    @field_validator("tags")
    @classmethod
    def valid_filter_tags(cls, value: list[str] | None) -> list[str] | None:
        if value is None:
            return None
        return _clean_string_list(value, "tags")


class VocabularyAnswerInput(TutorModel):
    item_id: str
    answer: str
    idempotency_key: str
    session_id: str = "default"


class AnswerEvent(TutorModel):
    id: str
    session_id: str
    skill: Literal["vocab", "writing", "reading", "lesson"]
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


class VocabularyReviewHistoryRequest(TutorModel):
    item_id: str

    @field_validator("item_id")
    @classmethod
    def valid_item_id(cls, value: str) -> str:
        return _clean_string(value, "item_id")


class VocabularyReviewAttempt(TutorModel):
    id: str
    session_id: str
    answer_event_id: str | None = None
    learner_answer: str | None = None
    answer_detail_available: bool = True
    verdict: Verdict
    quality: int = Field(ge=0, le=5)
    previous_state: VocabularyItemState
    next_state: VocabularyItemState
    reviewed_at: datetime


def empty_review_attempts() -> list[VocabularyReviewAttempt]:
    return []


class VocabularyReviewHistory(TutorModel):
    item: VocabularyItem
    current_state: VocabularyItemState
    due_status: Literal["new", "due", "not_due"]
    attempts: list[VocabularyReviewAttempt] = Field(default_factory=empty_review_attempts)


class WeakTagSourceEvent(TutorModel):
    session_id: str
    tag: str
    source: Literal["mistake_events", "low_quality_reviews"]
    observed_at: datetime


class VocabularySelectionSource(TutorModel):
    item: VocabularyItem
    created_at: datetime


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


# --- Text modalities (Phase 5) ---

TextModality = Literal["reading", "lesson", "transcript"]
StoredSkill = Literal["vocab", "writing", "reading", "lesson"]
TextResponseStatus = Literal[
    "completed", "empty", "abandoned", "off_topic", "mixed_language", "refused"
]
TextExerciseMode = Literal[
    "comprehension",
    "lesson",
    "transcript_reconstruction",
    "transcript_correction",
    "transcript_comprehension",
]

EXERCISE_SCOPE_GUARDRAILS: list[str] = [
    "text_only",
    "terminal_readable",
    "feedback_envelope_unchanged",
    "no_new_persistence",
]
RESULT_SCOPE_GUARDRAILS: list[str] = [
    "text_only",
    "no_raw_private_export",
    "no_host_specific_behavior",
]


def _exercise_guardrails() -> list[str]:
    return list(EXERCISE_SCOPE_GUARDRAILS)


def _result_guardrails() -> list[str]:
    return list(RESULT_SCOPE_GUARDRAILS)


class TextExerciseCandidate(TutorModel):
    """Common input envelope for generated reading/lesson/transcript candidates."""

    modality: TextModality
    mode: TextExerciseMode | None = None
    target_language: str
    level_target: str
    focus: str = ""
    instructions: str
    content: str
    questions: list[str] = Field(default_factory=list[str])
    answer_key: list[str] = Field(default_factory=list[str])
    rubric: list[str] = Field(default_factory=list[str])
    tags: list[str] = Field(default_factory=list[str])

    @field_validator("target_language", "level_target", "instructions", "content")
    @classmethod
    def required_text(cls, value: str) -> str:
        return _clean_string(value, "field")

    @field_validator("questions", "tags")
    @classmethod
    def required_lists(cls, value: list[str]) -> list[str]:
        return _clean_string_list(value, "field")

    @model_validator(mode="after")
    def needs_answer_key_or_rubric(self) -> TextExerciseCandidate:
        if not self.answer_key and not self.rubric:
            raise ValueError("candidate must include answer_key or rubric")
        return self


class ValidatedTextExercise(TutorModel):
    """Validated exercise derived from a candidate; safe to present in the terminal."""

    schema_version: int = 1
    exercise_id: str
    modality: TextModality
    mode: TextExerciseMode
    target_language: str
    level_target: str
    focus: str = ""
    instructions: str
    content: str
    questions: list[str]
    answer_key_summary: str
    rubric_summary: str
    tags: list[str]
    rendered_char_count: int = Field(ge=0)
    repair_attempts_used: int = Field(default=0, ge=0)
    scope_guardrails: list[str] = Field(default_factory=_exercise_guardrails)


class TextModalityRecordInput(TutorModel):
    """CLI input for completed or attempted text-modality responses."""

    exercise_id: str
    modality: TextModality
    session_id: str = "default"
    idempotency_key: str | None = None
    learner_response: str = ""
    response_status: TextResponseStatus = "completed"
    candidate_feedback: FeedbackEnvelope
    score_metadata: dict[str, Any] = Field(default_factory=dict[str, Any])
    exercise_summary: str = ""


class TextModalityResult(TutorModel):
    """Canonical result wrapper for reading/lesson/transcript record commands."""

    schema_version: int = 1
    modality: TextModality
    exercise_id: str
    session_id: str
    response_status: TextResponseStatus
    feedback: FeedbackEnvelope
    score_metadata: dict[str, Any] = Field(default_factory=dict[str, Any])
    answer_event: AnswerEvent | None = None
    persisted_mistakes: int = Field(default=0, ge=0)
    scope_guardrails: list[str] = Field(default_factory=_result_guardrails)


class ProgressReportRequest(TutorModel):
    window_size: int = Field(default=10, ge=1, le=30)
    generated_at: datetime | None = None
    format: Literal["json", "markdown"] = "json"

    @field_validator("generated_at")
    @classmethod
    def normalize_generated_at(cls, value: datetime | None) -> datetime | None:
        if value is None:
            return None
        if value.tzinfo is None:
            value = value.replace(tzinfo=UTC)
        return value.astimezone(UTC).replace(microsecond=0)


class ReportWindow(TutorModel):
    requested_session_count: int = Field(ge=1, le=30)
    actual_session_count: int = Field(ge=0)
    mastery_session_count: int = Field(ge=0, le=30)
    start_date: str | None = None
    end_date: str | None = None
    active_mastery_window: str = "last_30_completed_sessions"

    @model_validator(mode="after")
    def valid_counts(self) -> ReportWindow:
        if self.actual_session_count > self.requested_session_count:
            raise ValueError("actual_session_count cannot exceed requested_session_count")
        return self


class ProgressSnapshot(TutorModel):
    streak_days: int = Field(ge=0)
    due_count: int = Field(ge=0)
    maturity: dict[str, int] = Field(default_factory=dict[str, int])
    top_weak_patterns: list[str] = Field(default_factory=list[str])
    month_to_date_estimated_usd: float | None = Field(default=None, ge=0)
    cost_status: Literal["available", "partial", "unavailable"]
    next_action: str


class TagMasteryBreakdown(TutorModel):
    correctness: int = Field(ge=0, le=100)
    severity: int = Field(ge=0, le=100)
    recency: int = Field(ge=0, le=100)
    confidence: int = Field(ge=0, le=100)


class TagMastery(TutorModel):
    tag: str
    score: int = Field(ge=0, le=100)
    band: Literal["emerging", "developing", "steady", "strong"]
    evidence_count: int = Field(ge=0)
    last_seen_at: datetime | None = None
    last_seen_age_days: int | None = Field(default=None, ge=0)
    stale: bool = False
    trend: Literal["improving", "steady", "worsening", "insufficient_data"]
    next_practice_hint: str
    score_breakdown: TagMasteryBreakdown


class TextTrend(TutorModel):
    metric: str
    label: str
    polarity: Literal["higher_is_better", "lower_is_better"]
    direction: Literal["improving", "steady", "worsening", "insufficient_data"]
    sparkline: str
    min_label: str
    max_label: str
    values_count: int = Field(ge=0)

    @field_validator("sparkline")
    @classmethod
    def valid_sparkline(cls, value: str) -> str:
        invalid = set(value) - set(".:-=+*#%@")
        if invalid:
            raise ValueError("sparkline contains invalid characters")
        return value

    @model_validator(mode="after")
    def valid_length(self) -> TextTrend:
        if len(self.sparkline) != self.values_count:
            raise ValueError("sparkline length must match values_count")
        return self


class ProgressDateRange(TutorModel):
    start_date: str | None = None
    end_date: str | None = None


class PracticeTotals(TutorModel):
    answers: int = Field(default=0, ge=0)
    vocabulary_reviews: int = Field(default=0, ge=0)
    writing_answers: int = Field(default=0, ge=0)
    reading_answers: int = Field(default=0, ge=0)
    lesson_answers: int = Field(default=0, ge=0)
    transcript_drills: int = Field(default=0, ge=0)


class DueReviewCompletion(TutorModel):
    completed: int = Field(default=0, ge=0)
    current_due_count: int = Field(default=0, ge=0)


class MistakeSeverityTotals(TutorModel):
    low: int = Field(default=0, ge=0)
    medium: int = Field(default=0, ge=0)
    high: int = Field(default=0, ge=0)


class WeakTagChanges(TutorModel):
    new: list[str] = Field(default_factory=list[str])
    repeated: list[str] = Field(default_factory=list[str])
    resolved: list[str] = Field(default_factory=list[str])


class SkippedDataNotice(TutorModel):
    reason: Literal[
        "duplicate_session",
        "invalid_session",
        "interrupted_session",
        "missing_analysis",
        "stale_tag_evidence",
        "unavailable_optional_field",
    ]
    count: int = Field(ge=0)
    scope: Literal["mastery", "recap", "export", "snapshot"]
    message: str


class RecentSessionRecap(TutorModel):
    actual_session_count: int = Field(ge=0)
    date_range: ProgressDateRange = Field(default_factory=ProgressDateRange)
    practice_totals: PracticeTotals = Field(default_factory=PracticeTotals)
    due_review_completion: DueReviewCompletion = Field(default_factory=DueReviewCompletion)
    mistake_severity_totals: MistakeSeverityTotals = Field(default_factory=MistakeSeverityTotals)
    weak_tag_changes: WeakTagChanges = Field(default_factory=WeakTagChanges)
    latest_session_summary: str | None = None
    trends: list[TextTrend] = Field(default_factory=list[TextTrend])
    skipped_data: list[SkippedDataNotice] = Field(default_factory=list[SkippedDataNotice])


class DueReviewSummary(TutorModel):
    due_count: int = Field(ge=0)
    completed_in_window: int = Field(ge=0)
    low_quality_in_window: int = Field(ge=0)
    maturity: dict[str, int] = Field(default_factory=dict[str, int])


class ProgressReport(TutorModel):
    schema_version: int = 1
    generated_at: datetime
    report_window: ReportWindow
    snapshot: ProgressSnapshot
    tag_mastery: list[TagMastery] = Field(default_factory=list[TagMastery])
    recent_recap: RecentSessionRecap
    due_review_summary: DueReviewSummary
    skipped_data: list[SkippedDataNotice] = Field(default_factory=list[SkippedDataNotice])
    scope_guardrails: list[str] = Field(
        default_factory=lambda: [
            "text_markdown_only",
            "aggregate_metrics_only",
            "no_raw_answers",
            "no_host_metadata",
        ]
    )

    @model_validator(mode="before")
    @classmethod
    def drop_legacy_computed_input(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data
        cleaned = cast(dict[str, Any], data).copy()
        for key in (
            "streak_days",
            "due_count",
            "weak_patterns",
            "maturity",
            "latest_recap",
            "month_to_date_estimated_usd",
            "cost_status",
            "next_action",
        ):
            cleaned.pop(key, None)
        return cleaned

    @computed_field  # type: ignore[prop-decorator]
    @property
    def streak_days(self) -> int:
        return self.snapshot.streak_days

    @computed_field  # type: ignore[prop-decorator]
    @property
    def due_count(self) -> int:
        return self.snapshot.due_count

    @computed_field  # type: ignore[prop-decorator]
    @property
    def weak_patterns(self) -> list[str]:
        return self.snapshot.top_weak_patterns

    @computed_field  # type: ignore[prop-decorator]
    @property
    def maturity(self) -> dict[str, int]:
        return self.snapshot.maturity

    @computed_field  # type: ignore[prop-decorator]
    @property
    def latest_recap(self) -> str | None:
        return self.recent_recap.latest_session_summary

    @computed_field  # type: ignore[prop-decorator]
    @property
    def month_to_date_estimated_usd(self) -> float | None:
        return self.snapshot.month_to_date_estimated_usd

    @computed_field  # type: ignore[prop-decorator]
    @property
    def cost_status(self) -> Literal["available", "partial", "unavailable"]:
        return self.snapshot.cost_status

    @computed_field  # type: ignore[prop-decorator]
    @property
    def next_action(self) -> str:
        return self.snapshot.next_action


class ProgressMarkdownExport(TutorModel):
    content_type: Literal["text/markdown"] = "text/markdown"
    generated_at: datetime
    report_window: ReportWindow
    markdown: str


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
        "vocabulary_card_definition.schema.json": VocabularyCardDefinition,
        "vocabulary_import_summary.schema.json": SeedImportResult,
        "vocabulary_session_plan.schema.json": VocabularySessionPlan,
        "weak_tag_signal.schema.json": WeakTagSignal,
        "selection_reason.schema.json": SelectionReason,
        "vocabulary_review_history.schema.json": VocabularyReviewHistory,
        "progress_request.schema.json": ProgressReportRequest,
        "progress_report.schema.json": ProgressReport,
        "progress_markdown_export.schema.json": ProgressMarkdownExport,
        "text_modality_result.schema.json": TextModalityResult,
        "text_modality_record.schema.json": TextModalityRecordInput,
        "reading_exercise.schema.json": ValidatedTextExercise,
        "reading_result.schema.json": TextModalityResult,
        "lesson_exercise.schema.json": ValidatedTextExercise,
        "lesson_result.schema.json": TextModalityResult,
        "transcript_drill.schema.json": ValidatedTextExercise,
    }
    for filename, model in mapping.items():
        (output_dir / filename).write_text(
            json.dumps(model.model_json_schema(), ensure_ascii=False, indent=2, sort_keys=True),
            encoding="utf-8",
        )
