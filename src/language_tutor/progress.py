from __future__ import annotations

from collections import defaultdict
from collections.abc import Sequence
from datetime import UTC, date, datetime, timedelta
from statistics import mean

from language_tutor.dal.repositories import (
    ProgressAnswerTotalsRow,
    ProgressMasteryEvidenceRow,
    ProgressMistakeSeverityTotalsRow,
    ProgressReviewTotalsRow,
    ProgressSessionRow,
    TutorRepository,
)
from language_tutor.schemas import (
    DueReviewCompletion,
    DueReviewSummary,
    LearnerPreferences,
    MistakeSeverityTotals,
    PracticeTotals,
    ProgressDateRange,
    ProgressReport,
    ProgressReportRequest,
    ProgressSnapshot,
    RecentSessionRecap,
    ReportWindow,
    SkippedDataNotice,
    TagMastery,
    TagMasteryBreakdown,
    TextTrend,
    WeakTagChanges,
)
from language_tutor.vocab import derive_active_weak_tag_signals

SPARKLINE_BUCKETS = ".:-=+*#%@"
SEVERITY_PENALTY = {"none": 0, "low": 25, "medium": 60, "high": 100}
CONFIDENCE_SCORE = {"high": 100, "medium": 70, "low": 40}


def compute_streak(dates: list[str], grace_days: int, today: date | None = None) -> int:
    seen = {date.fromisoformat(value) for value in dates}
    if not seen:
        return 0
    cursor = today or datetime.now(UTC).date()
    streak = 0
    missed = 0
    while missed <= grace_days:
        if cursor in seen:
            streak += 1
        else:
            missed += 1
        cursor -= timedelta(days=1)
        if cursor < min(seen):
            break
    return streak


def clamp_score(value: float) -> int:
    return max(0, min(100, round(value)))


def mastery_band(score: int) -> str:
    if score < 50:
        return "emerging"
    if score < 75:
        return "developing"
    if score < 90:
        return "steady"
    return "strong"


def trend_direction(
    values: list[float], *, polarity: str = "higher_is_better"
) -> str:
    if len(values) < 2:
        return "insufficient_data"
    half = len(values) // 2
    earlier = mean(values[:half])
    later = mean(values[-half:])
    if earlier == 0 and later == 0:
        return "steady"
    change = 1.0 if earlier == 0 else (later - earlier) / abs(earlier)
    if abs(change) < 0.10:
        return "steady"
    rising = change > 0
    if polarity == "lower_is_better":
        rising = not rising
    return "improving" if rising else "worsening"


def sparkline(values: list[float]) -> str:
    if not values:
        return ""
    low = min(values)
    high = max(values)
    if low == high:
        return SPARKLINE_BUCKETS[len(SPARKLINE_BUCKETS) // 2] * len(values)
    span = high - low
    last_bucket = len(SPARKLINE_BUCKETS) - 1
    return "".join(
        SPARKLINE_BUCKETS[round(((value - low) / span) * last_bucket)]
        for value in values
    )


def text_trend(metric: str, label: str, values: list[float], polarity: str) -> TextTrend:
    if values:
        min_label = f"min {min(values):g}"
        max_label = f"max {max(values):g}"
    else:
        min_label = "min unavailable"
        max_label = "max unavailable"
    return TextTrend(
        metric=metric,
        label=label,
        polarity=polarity,  # type: ignore[arg-type]
        direction=trend_direction(values, polarity=polarity),  # type: ignore[arg-type]
        sparkline=sparkline(values),
        min_label=min_label,
        max_label=max_label,
        values_count=len(values),
    )


def _review_signal(evidence: ProgressMasteryEvidenceRow) -> int | None:
    if evidence.review_quality is not None:
        if evidence.review_quality >= 4:
            return 100
        if evidence.review_quality == 3:
            return 60
        return 0
    if evidence.verdict in {"correct"}:
        return 100
    if evidence.verdict in {"partial"}:
        return 60
    if evidence.verdict in {"needs_review", "missed", "unanswered"}:
        return 0
    return None


def _mastery_hint(tag: str, band: str, stale: bool) -> str:
    if stale:
        return f"Refresh {tag} with a short review."
    if band == "emerging":
        return f"Practice focused {tag} drills."
    if band == "developing":
        return f"Revisit {tag} in mixed practice."
    if band == "steady":
        return f"Keep {tag} active with normal review."
    return f"Maintain {tag} with light review."


def _score_tag(
    tag: str,
    evidence: list[ProgressMasteryEvidenceRow],
    active_session_rank: dict[str, int],
    generated_at: datetime,
) -> TagMastery:
    active = [row for row in evidence if row.session_id in active_session_rank]
    stale = bool(evidence) and not active
    scoring_rows = active or evidence
    review_values = [
        value for value in (_review_signal(row) for row in scoring_rows) if value is not None
    ]
    correctness = clamp_score(mean(review_values)) if review_values else 50
    severity_rows = [row for row in active if row.severity]
    if severity_rows:
        severity = clamp_score(
            100 - mean(SEVERITY_PENALTY.get(str(row.severity), 60) for row in severity_rows)
        )
    else:
        severity = 50 if stale else 100
    if active:
        denominator = max(1, len(active_session_rank) - 1)
        recency = max(
            clamp_score(100 * (denominator - active_session_rank[row.session_id]) / denominator)
            for row in active
        )
    else:
        recency = 0
    confidence_values = [
        CONFIDENCE_SCORE.get(str(row.confidence), 70)
        for row in scoring_rows
    ]
    raw_confidence = mean(confidence_values) if confidence_values else 70
    confidence = clamp_score(raw_confidence * min(1.0, len(scoring_rows) / 5))
    score = clamp_score(correctness * 0.45 + severity * 0.30 + recency * 0.15 + confidence * 0.10)
    band = mastery_band(score)
    latest = max((row.observed_at for row in scoring_rows), default=None)
    session_values: dict[str, list[float]] = defaultdict(list)
    for row in active:
        signal = _review_signal(row)
        if signal is not None:
            session_values[row.session_id].append(signal)
        if row.severity:
            session_values[row.session_id].append(100 - SEVERITY_PENALTY.get(str(row.severity), 60))
    ordered_values = [
        mean(session_values[session_id])
        for session_id, _rank in sorted(active_session_rank.items(), key=lambda item: item[1], reverse=True)
        if session_id in session_values
    ]
    return TagMastery(
        tag=tag,
        score=score,
        band=band,  # type: ignore[arg-type]
        evidence_count=len(scoring_rows),
        last_seen_at=latest,
        last_seen_age_days=(generated_at.date() - latest.date()).days if latest else None,
        stale=stale,
        trend=trend_direction(ordered_values),  # type: ignore[arg-type]
        next_practice_hint=_mastery_hint(tag, band, stale),
        score_breakdown=TagMasteryBreakdown(
            correctness=correctness,
            severity=severity,
            recency=recency,
            confidence=confidence,
        ),
    )


def tag_mastery_rows(
    evidence_rows: list[ProgressMasteryEvidenceRow],
    active_sessions: list[ProgressSessionRow],
    generated_at: datetime,
) -> list[TagMastery]:
    active_session_rank = {
        session.session_id: index for index, session in enumerate(active_sessions)
    }
    grouped: dict[str, list[ProgressMasteryEvidenceRow]] = defaultdict(list)
    for row in evidence_rows:
        grouped[row.tag].append(row)
    mastery = [
        _score_tag(tag, rows, active_session_rank, generated_at)
        for tag, rows in grouped.items()
    ]
    trend_order = {"worsening": 0, "steady": 1, "improving": 2, "insufficient_data": 3}
    mastery.sort(
        key=lambda row: (
            row.score,
            trend_order[row.trend],
            -(row.last_seen_at.timestamp() if row.last_seen_at else 0),
            row.tag,
        )
    )
    return mastery


ProgressTotalsRow = (
    ProgressAnswerTotalsRow | ProgressReviewTotalsRow | ProgressMistakeSeverityTotalsRow
)


def _by_session(rows: Sequence[ProgressTotalsRow]) -> dict[str, ProgressTotalsRow]:
    return {row.session_id: row for row in rows}


def recent_recap(
    sessions: list[ProgressSessionRow],
    answers: list[ProgressAnswerTotalsRow],
    reviews: list[ProgressReviewTotalsRow],
    mistakes: list[ProgressMistakeSeverityTotalsRow],
    due_count: int,
) -> RecentSessionRecap:
    ordered = list(reversed(sessions))
    answer_by_session = _by_session(answers)
    review_by_session = _by_session(reviews)
    mistake_by_session = _by_session(mistakes)
    total_answers = 0
    total_vocab = 0
    total_writing = 0
    total_reading = 0
    total_lesson = 0
    total_transcript = 0
    total_reviews = 0
    low_quality = 0
    severity_totals = {"low": 0, "medium": 0, "high": 0}
    answer_series: list[float] = []
    review_series: list[float] = []
    severity_series: list[float] = []
    for session in ordered:
        answer_row = answer_by_session.get(session.session_id)
        review_row = review_by_session.get(session.session_id)
        mistake_row = mistake_by_session.get(session.session_id)
        answers_count = answer_row.answers if isinstance(answer_row, ProgressAnswerTotalsRow) else 0
        vocab_count = (
            answer_row.vocabulary_answers if isinstance(answer_row, ProgressAnswerTotalsRow) else 0
        )
        writing_count = (
            answer_row.writing_answers if isinstance(answer_row, ProgressAnswerTotalsRow) else 0
        )
        reading_count = (
            answer_row.reading_answers if isinstance(answer_row, ProgressAnswerTotalsRow) else 0
        )
        lesson_count = (
            answer_row.lesson_answers if isinstance(answer_row, ProgressAnswerTotalsRow) else 0
        )
        transcript_count = (
            answer_row.transcript_drills if isinstance(answer_row, ProgressAnswerTotalsRow) else 0
        )
        review_count = review_row.completed if isinstance(review_row, ProgressReviewTotalsRow) else 0
        low_quality += review_row.low_quality if isinstance(review_row, ProgressReviewTotalsRow) else 0
        low = mistake_row.low if isinstance(mistake_row, ProgressMistakeSeverityTotalsRow) else 0
        medium = mistake_row.medium if isinstance(mistake_row, ProgressMistakeSeverityTotalsRow) else 0
        high = mistake_row.high if isinstance(mistake_row, ProgressMistakeSeverityTotalsRow) else 0
        total_answers += answers_count
        total_vocab += vocab_count
        total_writing += writing_count
        total_reading += reading_count
        total_lesson += lesson_count
        total_transcript += transcript_count
        total_reviews += review_count
        severity_totals["low"] += low
        severity_totals["medium"] += medium
        severity_totals["high"] += high
        answer_series.append(float(answers_count))
        review_series.append(float(review_count))
        severity_series.append(float(low + medium * 2 + high * 3))
    latest_tags: set[str] = set(ordered[-1].weak_tags) if ordered else set()
    prior_tags: set[str] = set()
    for session in ordered[:-1]:
        prior_tags.update(session.weak_tags)
    changes = WeakTagChanges(
        new=sorted(latest_tags - prior_tags),
        repeated=sorted(latest_tags & prior_tags),
        resolved=sorted(prior_tags - latest_tags),
    )
    latest_summary = ordered[-1].summary_for_next_boot if ordered else None
    return RecentSessionRecap(
        actual_session_count=len(ordered),
        date_range=ProgressDateRange(
            start_date=ordered[0].created_at.date().isoformat() if ordered else None,
            end_date=ordered[-1].created_at.date().isoformat() if ordered else None,
        ),
        practice_totals=PracticeTotals(
            answers=total_answers,
            vocabulary_reviews=total_reviews or total_vocab,
            writing_answers=total_writing,
            reading_answers=total_reading,
            lesson_answers=total_lesson,
            transcript_drills=total_transcript,
        ),
        due_review_completion=DueReviewCompletion(
            completed=total_reviews,
            current_due_count=due_count,
        ),
        mistake_severity_totals=MistakeSeverityTotals(**severity_totals),
        weak_tag_changes=changes,
        latest_session_summary=latest_summary,
        trends=[
            text_trend("answer_volume", "Answer volume", answer_series, "higher_is_better"),
            text_trend("review_completion", "Review completion", review_series, "higher_is_better"),
            text_trend("mistake_severity", "Mistake severity", severity_series, "lower_is_better"),
        ],
        skipped_data=[
            SkippedDataNotice(
                reason="unavailable_optional_field",
                count=1,
                scope="recap",
                message="Optional session summary unavailable."
            )
        ] if ordered and latest_summary is None else [],
    )


def progress_report(
    repo: TutorRepository,
    preferences: LearnerPreferences,
    request: ProgressReportRequest | None = None,
    *,
    generated_at: datetime | None = None,
) -> ProgressReport:
    request = request or ProgressReportRequest()
    now = (generated_at or request.generated_at or datetime.now(UTC)).astimezone(UTC).replace(microsecond=0)
    month_prefix = now.strftime("%Y-%m-01")
    cost, cost_status = repo.month_cost(month_prefix)
    due = repo.due_count(now)
    historical_sessions = repo.recent_progress_sessions(365)
    mastery_sessions = historical_sessions[:30]
    recap_sessions = historical_sessions[: request.window_size]
    recap_ids = [session.session_id for session in recap_sessions]
    mastery_ids = [session.session_id for session in historical_sessions]
    weak = [signal.tag for signal in derive_active_weak_tag_signals(repo)]
    mastery = tag_mastery_rows(repo.progress_mastery_evidence(mastery_ids), mastery_sessions, now)
    recap = recent_recap(
        recap_sessions,
        repo.progress_answer_totals(recap_ids),
        repo.progress_review_totals(recap_ids),
        repo.progress_mistake_severity_totals(recap_ids),
        due,
    )
    report_window = ReportWindow(
        requested_session_count=request.window_size,
        actual_session_count=len(recap_sessions),
        mastery_session_count=len(mastery_sessions),
        start_date=recap.date_range.start_date,
        end_date=recap.date_range.end_date,
    )
    maturity = repo.maturity_counts()
    no_history = not recap_sessions and not mastery
    return ProgressReport(
        generated_at=now,
        report_window=report_window,
        snapshot=ProgressSnapshot(
            streak_days=compute_streak(repo.answer_dates(), preferences.streak_grace_days, now.date()),
            due_count=due,
            maturity=maturity,
            top_weak_patterns=weak,
            month_to_date_estimated_usd=cost,
            cost_status=cost_status,  # type: ignore[arg-type]
            next_action=(
                "Start vocabulary or writing practice."
                if no_history
                else ("Review due vocabulary." if due else "Continue mixed practice.")
            ),
        ),
        tag_mastery=mastery,
        recent_recap=recap,
        due_review_summary=DueReviewSummary(
            due_count=due,
            completed_in_window=recap.due_review_completion.completed,
            low_quality_in_window=sum(row.low_quality for row in repo.progress_review_totals(recap_ids)),
            maturity=maturity,
        ),
        skipped_data=recap.skipped_data,
    )
