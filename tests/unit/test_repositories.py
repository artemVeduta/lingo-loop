from __future__ import annotations

from language_tutor.dal.repositories import TutorRepository, new_id
from language_tutor.dal.sqlite_store import connect
from language_tutor.feedback import vocabulary_feedback
from language_tutor.schemas import VocabularyItem
from language_tutor.srs import quality_for_verdict, schedule_review


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
