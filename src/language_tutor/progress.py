from __future__ import annotations

from datetime import UTC, date, datetime, timedelta

from language_tutor.dal.repositories import TutorRepository
from language_tutor.schemas import LearnerPreferences, ProgressReport


def compute_streak(dates: list[str], grace_days: int) -> int:
    seen = {date.fromisoformat(value) for value in dates}
    if not seen:
        return 0
    cursor = datetime.now(UTC).date()
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


def progress_report(repo: TutorRepository, preferences: LearnerPreferences) -> ProgressReport:
    now = datetime.now(UTC)
    month_prefix = now.strftime("%Y-%m-01")
    cost, cost_status = repo.month_cost(month_prefix)
    due = repo.due_count(now)
    weak = repo.weak_tags()
    return ProgressReport(
        streak_days=compute_streak(repo.answer_dates(), preferences.streak_grace_days),
        due_count=due,
        weak_patterns=weak,
        maturity=repo.maturity_counts(),
        latest_recap=repo.latest_summary(),
        month_to_date_estimated_usd=cost,
        cost_status=cost_status,  # type: ignore[arg-type]
        next_action="Review due vocabulary." if due else "Add or practice starter vocabulary.",
    )
