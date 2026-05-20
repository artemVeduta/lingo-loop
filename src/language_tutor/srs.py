from __future__ import annotations

from datetime import UTC, datetime, timedelta

from language_tutor.schemas import Verdict, VocabularyItemState

QUALITY_BY_VERDICT: dict[Verdict | str, int] = {
    Verdict.CORRECT: 5,
    Verdict.PARTIAL: 3,
    Verdict.MISSED: 1,
    Verdict.UNANSWERED: 0,
}


def quality_for_verdict(verdict: Verdict | str) -> int:
    return QUALITY_BY_VERDICT[verdict]


def schedule_review(
    previous: VocabularyItemState, verdict: Verdict | str, now: datetime | None = None
) -> VocabularyItemState:
    current = now or datetime.now(UTC).replace(microsecond=0)
    quality = quality_for_verdict(verdict)
    ease = max(1.3, previous.ease_factor + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02)))
    if quality < 3:
        repetition = 0
        interval = 1
        state = "relearning" if previous.repetition_count else "learning"
    else:
        repetition = previous.repetition_count + 1
        if repetition == 1:
            interval = 1
            state = "learning"
        elif repetition == 2:
            interval = 6
            state = "review"
        else:
            interval = max(1, round(previous.interval_days * ease))
            state = "mature" if interval >= 21 else "review"
    return VocabularyItemState(
        state=state,
        ease_factor=round(ease, 2),
        repetition_count=repetition,
        interval_days=interval,
        due_at=current + timedelta(days=interval),
    )
