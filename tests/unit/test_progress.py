from __future__ import annotations

from datetime import UTC, datetime

from language_tutor.dal.repositories import TutorRepository
from language_tutor.dal.sqlite_store import connect
from language_tutor.progress import (
    compute_streak,
    progress_report,
    sparkline,
    tag_mastery_rows,
    text_trend,
)
from language_tutor.schemas import LearnerPreferences, ProgressReportRequest
from tests.fixtures.progress.phase4_scenarios import BASE_TIME, seed_mixed_history


def test_streak_with_today() -> None:
    today = datetime.now(UTC).date().isoformat()
    assert compute_streak([today], grace_days=0) == 1


def test_progress_request_validates_window_and_utc() -> None:
    request = ProgressReportRequest.model_validate(
        {"window_size": 30, "generated_at": "2026-05-21T12:00:00+02:00"}
    )
    assert request.generated_at == datetime(2026, 5, 21, 10, tzinfo=UTC)


def test_text_trend_direction_and_sparkline() -> None:
    trend = text_trend("accuracy", "Accuracy", [1, 2, 3, 4, 5], "higher_is_better")
    assert trend.direction == "improving"
    assert trend.sparkline == ".-+#@"
    assert sparkline([7, 7, 7]) == "+++"
    lower = text_trend("mistakes", "Mistakes", [5, 4, 3, 2, 1], "lower_is_better")
    assert lower.direction == "improving"


def test_mastery_rows_are_sorted_and_private_text_is_absent(tmp_path) -> None:  # type: ignore[no-untyped-def]
    conn = connect(tmp_path / "db.sqlite3")
    try:
        repo = TutorRepository(conn)
        seed_mixed_history(repo, 6)
        sessions = repo.recent_progress_sessions(30)
        mastery = tag_mastery_rows(
            repo.progress_mastery_evidence([session.session_id for session in sessions]),
            sessions,
            BASE_TIME,
        )
        assert [row.score for row in mastery] == sorted(row.score for row in mastery)
        serialized = "".join(row.model_dump_json() for row in mastery)
        assert "private answer" not in serialized
        assert "private span" not in serialized
        assert "private prose" not in serialized
    finally:
        conn.close()


def _insert_answer(conn, event_id: str, session_id: str, skill: str, prompt_ref: str) -> None:  # type: ignore[no-untyped-def]
    conn.execute(
        """
        INSERT INTO answer_events(id, session_id, skill, prompt_ref, learner_answer, outcome, recorded_at)
        VALUES (?, ?, ?, ?, 'a', 'partial', ?)
        """,
        (event_id, session_id, skill, prompt_ref, datetime(2026, 5, 21, tzinfo=UTC).isoformat()),
    )


def test_text_modality_answer_totals_separate_reading_lesson_transcript(tmp_path) -> None:  # type: ignore[no-untyped-def]
    conn = connect(tmp_path / "db.sqlite3")
    try:
        repo = TutorRepository(conn)
        _insert_answer(conn, "a1", "s1", "reading", "reading_aaa")
        _insert_answer(conn, "a2", "s1", "reading", "reading_bbb")
        _insert_answer(conn, "a3", "s1", "lesson", "lesson_ccc")
        _insert_answer(conn, "a4", "s1", "reading", "transcript_ddd")
        _insert_answer(conn, "a5", "s1", "writing", "prompt_x")
        conn.commit()
        totals = repo.progress_answer_totals(["s1"])[0]
        assert totals.reading_answers == 2
        assert totals.lesson_answers == 1
        assert totals.transcript_drills == 1
        assert totals.writing_answers == 1
        assert totals.answers == 5
    finally:
        conn.close()


def test_progress_report_contains_recap_and_due_summary(tmp_path) -> None:  # type: ignore[no-untyped-def]
    conn = connect(tmp_path / "db.sqlite3")
    try:
        repo = TutorRepository(conn)
        seed_mixed_history(repo, 5)
        report = progress_report(
            repo,
            LearnerPreferences(),
            ProgressReportRequest(generated_at=BASE_TIME, window_size=5),
        )
        assert report.report_window.actual_session_count == 5
        assert report.recent_recap.practice_totals.answers > 0
        assert report.due_review_summary.completed_in_window > 0
        assert report.scope_guardrails == [
            "text_markdown_only",
            "aggregate_metrics_only",
            "no_raw_answers",
            "no_host_metadata",
        ]
    finally:
        conn.close()
