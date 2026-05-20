from __future__ import annotations

from datetime import UTC, datetime

from language_tutor.progress import compute_streak


def test_streak_with_today() -> None:
    today = datetime.now(UTC).date().isoformat()
    assert compute_streak([today], grace_days=0) == 1
