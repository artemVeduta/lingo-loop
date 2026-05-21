from __future__ import annotations

from datetime import UTC, datetime, timedelta

from language_tutor.dal.repositories import TutorRepository, new_id
from language_tutor.dal.sqlite_store import connect
from language_tutor.feedback import vocabulary_feedback
from language_tutor.schemas import (
    Confidence,
    ErrorSpan,
    ErrorTag,
    FeedbackEnvelope,
    Severity,
    Verdict,
    VocabularyItem,
)
from language_tutor.srs import quality_for_verdict, schedule_review
from tests.fixtures.progress.phase4_scenarios import seed_mixed_history


def test_vocab_answer_idempotency(tmp_path) -> None:  # type: ignore[no-untyped-def]
    conn = connect(tmp_path / "db.sqlite3")
    try:
        repo = TutorRepository(conn)
        item = VocabularyItem(
            id=new_id("vocab"),
            target_language="uk",
            prompt="hello",
            lemma="привіт",
            accepted_answers=["привіт"],
        )
        repo.upsert_vocabulary_item(item)
        conn.commit()
        feedback = vocabulary_feedback("привіт", ["привіт"])
        next_state = schedule_review(item.state, feedback.verdict)
        first = repo.record_vocab_answer(
            item=item,
            session_id="s1",
            answer="привіт",
            idempotency_key="k1",
            feedback=feedback,
            previous_state=item.state,
            next_state=next_state,
            quality=quality_for_verdict(feedback.verdict),
        )
        second = repo.record_vocab_answer(
            item=item,
            session_id="s1",
            answer="привіт",
            idempotency_key="k1",
            feedback=feedback,
            previous_state=item.state,
            next_state=next_state,
            quality=quality_for_verdict(feedback.verdict),
        )
        assert first.review.id == second.review.id
        assert second.duplicate is True
    finally:
        conn.close()


def test_import_merges_additive_metadata_without_review_reset(tmp_path) -> None:  # type: ignore[no-untyped-def]
    conn = connect(tmp_path / "db.sqlite3")
    try:
        repo = TutorRepository(conn)
        item = VocabularyItem(
            id=new_id("vocab"),
            target_language="uk",
            prompt="hello",
            lemma="привіт",
            accepted_answers=["привіт"],
            tags=["greetings"],
            sources=["manual"],
        )
        repo.insert_vocabulary_item(item)
        conn.commit()
        feedback = vocabulary_feedback("привіт", ["привіт"])
        next_state = schedule_review(item.state, feedback.verdict)
        repo.record_vocab_answer(
            item=item,
            session_id="s1",
            answer="привіт",
            idempotency_key="merge-k1",
            feedback=feedback,
            previous_state=item.state,
            next_state=next_state,
            quality=quality_for_verdict(feedback.verdict),
        )
        duplicate = item.model_copy(
            update={
                "id": new_id("vocab"),
                "accepted_answers": ["привіт", "privit"],
                "tags": ["daily"],
                "notes": ["informal"],
                "sources": ["seed"],
            }
        )
        status, item_id = repo.import_vocabulary_item(duplicate)
        stored = repo.get_vocabulary_item(item_id)
        review_count = conn.execute("SELECT COUNT(*) AS count FROM vocabulary_reviews").fetchone()
        assert status == "updated"
        assert stored.accepted_answers == ["привіт", "privit"]
        assert stored.tags == ["greetings", "daily"]
        assert stored.notes == ["informal"]
        assert stored.sources == ["manual", "seed"]
        assert int(review_count["count"]) == 1
        assert stored.state.state == next_state.state
    finally:
        conn.close()


def test_tag_filter_is_inclusive_and_reports_not_due_count(tmp_path) -> None:  # type: ignore[no-untyped-def]
    conn = connect(tmp_path / "db.sqlite3")
    try:
        repo = TutorRepository(conn)
        due = VocabularyItem(
            id=new_id("vocab"),
            target_language="uk",
            prompt="hello",
            lemma="привіт",
            accepted_answers=["привіт"],
            tags=["Greetings"],
        )
        not_due = VocabularyItem(
            id=new_id("vocab"),
            target_language="uk",
            prompt="thanks",
            lemma="дякую",
            accepted_answers=["дякую"],
            tags=["thanks"],
            state=due.state.model_copy(
                update={"due_at": datetime.now(UTC) + timedelta(days=1)}
            ),
        )
        repo.insert_vocabulary_item(due)
        repo.insert_vocabulary_item(not_due)
        conn.commit()
        items, matching_count, due_matching_count = repo.due_vocabulary_by_tags(
            10, datetime.now(UTC), ["greetings", "thanks"]
        )
        assert [item.id for item in items] == [due.id]
        assert matching_count == 2
        assert due_matching_count == 1
    finally:
        conn.close()


def test_review_history_orders_attempts_and_keeps_new_status(tmp_path) -> None:  # type: ignore[no-untyped-def]
    conn = connect(tmp_path / "db.sqlite3")
    try:
        repo = TutorRepository(conn)
        item = VocabularyItem(
            id=new_id("vocab"),
            target_language="uk",
            prompt="hello",
            lemma="привіт",
            accepted_answers=["привіт"],
        )
        repo.insert_vocabulary_item(item)
        conn.commit()
        assert repo.vocabulary_review_history(item.id, datetime.now(UTC)).due_status == "new"
        feedback = vocabulary_feedback("wrong", ["привіт"])
        next_state = schedule_review(item.state, feedback.verdict)
        repo.record_vocab_answer(
            item=item,
            session_id="s1",
            answer="wrong",
            idempotency_key="hist-k1",
            feedback=feedback,
            previous_state=item.state,
            next_state=next_state,
            quality=quality_for_verdict(feedback.verdict),
        )
        history = repo.vocabulary_review_history(item.id, datetime.now(UTC))
        assert len(history.attempts) == 1
        assert history.attempts[0].learner_answer == "wrong"
        assert history.attempts[0].answer_detail_available is True
    finally:
        conn.close()


def test_recent_analyzed_sessions_and_weak_sources_are_bounded(tmp_path) -> None:  # type: ignore[no-untyped-def]
    conn = connect(tmp_path / "db.sqlite3")
    try:
        repo = TutorRepository(conn)
        for index in range(12):
            conn.execute(
                """
                INSERT INTO session_summaries(
                  id, session_id, summary_for_user, summary_for_next_boot,
                  weak_tags_json, next_focus, cost_snapshot_json, created_at
                ) VALUES (?, ?, 'u', 'b', '[]', 'focus', '{}', ?)
                """,
                (
                    f"summary_{index}",
                    f"s{index}",
                    (datetime(2026, 5, 1, tzinfo=UTC) + timedelta(days=index)).isoformat(),
                ),
            )
        conn.execute(
            """
            INSERT INTO mistake_events(
              id, session_id, skill, severity, tag, explanation, confidence, created_at
            ) VALUES ('m1', 's11', 'writing', 'low', 'case', '', 'high', ?)
            """,
            (datetime(2026, 5, 21, tzinfo=UTC).isoformat(),),
        )
        conn.commit()
        session_ids = repo.recent_analyzed_session_ids(10)
        events = repo.weak_tag_source_events(session_ids)
        assert session_ids[0] == "s11"
        assert len(session_ids) == 10
        assert [(event.session_id, event.tag, event.source) for event in events] == [
            ("s11", "case", "mistake_events")
        ]
    finally:
        conn.close()


def test_vocabulary_selection_candidates_include_ordering_and_filter_boundary(tmp_path) -> None:  # type: ignore[no-untyped-def]
    conn = connect(tmp_path / "db.sqlite3")
    try:
        repo = TutorRepository(conn)
        first = VocabularyItem(
            id="vocab_case",
            target_language="uk",
            prompt="book",
            accepted_answers=["книга"],
            tags=["Case"],
        )
        second = VocabularyItem(
            id="vocab_aspect",
            target_language="uk",
            prompt="read",
            accepted_answers=["читати"],
            tags=["aspect"],
        )
        repo.insert_vocabulary_item(first)
        repo.insert_vocabulary_item(second)
        conn.execute(
            "UPDATE vocabulary_items SET created_at = ? WHERE id = ?",
            (datetime(2026, 5, 20, tzinfo=UTC).isoformat(), first.id),
        )
        conn.execute(
            "UPDATE vocabulary_items SET created_at = ? WHERE id = ?",
            (datetime(2026, 5, 21, tzinfo=UTC).isoformat(), second.id),
        )
        conn.commit()
        candidates = repo.vocabulary_selection_candidates(["case"])
        assert [candidate.item.id for candidate in candidates] == ["vocab_case"]
        assert candidates[0].created_at == datetime(2026, 5, 20, tzinfo=UTC)
    finally:
        conn.close()


def _text_feedback() -> FeedbackEnvelope:
    return FeedbackEnvelope(
        verdict=Verdict.PARTIAL,
        severity=Severity.LOW,
        confidence=Confidence.MEDIUM,
        error_spans=[
            ErrorSpan(text="книга", tag=ErrorTag.CASE, severity=Severity.LOW, explanation="case"),
        ],
        explanation="Close.",
        next_drill_hint="Practice the accusative case.",
    )


def test_text_modality_answer_records_event_and_safe_mistakes(tmp_path) -> None:  # type: ignore[no-untyped-def]
    conn = connect(tmp_path / "db.sqlite3")
    try:
        repo = TutorRepository(conn)
        feedback = _text_feedback()
        event, persisted = repo.record_text_modality_answer(
            skill="reading",
            session_id="s1",
            prompt_ref="reading_abc",
            learner_answer="книга",
            outcome="partial",
            feedback=feedback,
            safe_spans=feedback.error_spans,
        )
        conn.commit()
        assert event.skill == "reading"
        assert persisted == 1
        mistake = conn.execute("SELECT skill FROM mistake_events").fetchone()
        assert mistake["skill"] == "reading"
        answer = conn.execute("SELECT skill FROM answer_events").fetchone()
        assert answer["skill"] == "reading"
    finally:
        conn.close()


def test_text_modality_answer_is_idempotent(tmp_path) -> None:  # type: ignore[no-untyped-def]
    conn = connect(tmp_path / "db.sqlite3")
    try:
        repo = TutorRepository(conn)
        feedback = _text_feedback()
        first, first_count = repo.record_text_modality_answer(
            skill="lesson",
            session_id="s1",
            prompt_ref="lesson_abc",
            learner_answer="йду",
            outcome="partial",
            feedback=feedback,
            safe_spans=feedback.error_spans,
            idempotency_key="key-1",
        )
        conn.commit()
        second, second_count = repo.record_text_modality_answer(
            skill="lesson",
            session_id="s1",
            prompt_ref="lesson_abc",
            learner_answer="йду",
            outcome="partial",
            feedback=feedback,
            safe_spans=feedback.error_spans,
            idempotency_key="key-1",
        )
        conn.commit()
        assert first.id == second.id
        assert second_count == first_count == 1
        answer_count = conn.execute("SELECT COUNT(*) AS c FROM answer_events").fetchone()
        mistake_count = conn.execute("SELECT COUNT(*) AS c FROM mistake_events").fetchone()
        assert int(answer_count["c"]) == 1
        assert int(mistake_count["c"]) == 1
    finally:
        conn.close()


def test_text_modality_answer_without_safe_spans_persists_no_mistakes(tmp_path) -> None:  # type: ignore[no-untyped-def]
    conn = connect(tmp_path / "db.sqlite3")
    try:
        repo = TutorRepository(conn)
        feedback = _text_feedback()
        _event, persisted = repo.record_text_modality_answer(
            skill="reading",
            session_id="s1",
            prompt_ref="reading_empty",
            learner_answer="",
            outcome="empty",
            feedback=feedback,
            safe_spans=[],
        )
        conn.commit()
        assert persisted == 0
        mistake_count = conn.execute("SELECT COUNT(*) AS c FROM mistake_events").fetchone()
        assert int(mistake_count["c"]) == 0
    finally:
        conn.close()


def test_progress_repository_reads_are_bounded_and_aggregate_safe(tmp_path) -> None:  # type: ignore[no-untyped-def]
    conn = connect(tmp_path / "db.sqlite3")
    try:
        repo = TutorRepository(conn)
        seed_mixed_history(repo, 12)
        sessions = repo.recent_progress_sessions(5)
        session_ids = [session.session_id for session in sessions]
        evidence = repo.progress_mastery_evidence(session_ids)
        answers = repo.progress_answer_totals(session_ids)
        reviews = repo.progress_review_totals(session_ids)
        mistakes = repo.progress_mistake_severity_totals(session_ids)
        assert len(sessions) == 5
        assert {row.session_id for row in answers} <= set(session_ids)
        assert {row.session_id for row in reviews} <= set(session_ids)
        assert {row.session_id for row in mistakes} <= set(session_ids)
        serialized = "".join(str(row) for row in evidence)
        assert "private answer" not in serialized
        assert "private span" not in serialized
        assert "private prose" not in serialized
    finally:
        conn.close()
