from __future__ import annotations

from datetime import UTC, datetime

from language_tutor.schemas import Verdict, VocabularyItemState
from language_tutor.srs import quality_for_verdict, schedule_review


def test_sm2_correct_advances_schedule() -> None:
    now = datetime(2026, 5, 20, tzinfo=UTC)
    next_state = schedule_review(VocabularyItemState(due_at=now), Verdict.CORRECT, now)
    assert next_state.repetition_count == 1
    assert next_state.interval_days == 1
    assert quality_for_verdict(Verdict.CORRECT) == 5
