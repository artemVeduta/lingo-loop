from __future__ import annotations

import sqlite3
from pathlib import Path

from language_tutor.dal.sqlite_store import connect


def test_initial_migration_creates_tables(tmp_path) -> None:  # type: ignore[no-untyped-def]
    conn = connect(tmp_path / "db.sqlite3")
    try:
        tables = {
            row["name"] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
        }
        assert {"vocabulary_items", "answer_events", "migration_records"} <= tables
    finally:
        conn.close()


def test_vocab_depth_migration_backfills_metadata_and_preserves_reviews(tmp_path) -> None:  # type: ignore[no-untyped-def]
    db_path = tmp_path / "legacy.sqlite3"
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        initial_sql = Path(__file__).resolve().parents[2] / "migrations" / "001_initial.sql"
        conn.executescript(initial_sql.read_text(encoding="utf-8"))
        conn.execute(
            """
            INSERT INTO vocabulary_items(
              id, target_language, prompt, lemma, accepted_answers_json, hint, tags_json,
              state, ease_factor, repetition_count, interval_days, due_at, created_at,
              updated_at, dedupe_key
            ) VALUES (
              'vocab_1', 'uk', 'hello', 'привіт', '["привіт"]', NULL, '[]',
              'new', 2.5, 0, 0, '2026-05-21T00:00:00+00:00',
              '2026-05-21T00:00:00+00:00', '2026-05-21T00:00:00+00:00', 'uk:привіт'
            )
            """
        )
        conn.execute(
            """
            INSERT INTO answer_events(
              id, idempotency_key, session_id, skill, prompt_ref, learner_answer,
              outcome, feedback_envelope_json, recorded_at
            ) VALUES (
              'ans_1', 'k1', 's1', 'vocab', 'vocab_1', 'привіт', 'correct', NULL,
              '2026-05-21T00:00:00+00:00'
            )
            """
        )
        state_json = '{"state":"new","ease_factor":2.5,"repetition_count":0,"interval_days":0,"due_at":"2026-05-21T00:00:00Z"}'
        conn.execute(
            """
            INSERT INTO vocabulary_reviews(
              id, session_id, vocabulary_item_id, answer_event_id, verdict, quality,
              previous_state_json, next_state_json, reviewed_at
            ) VALUES ('rev_1', 's1', 'vocab_1', 'ans_1', 'correct', 5, ?, ?, ?)
            """,
            (state_json, state_json, "2026-05-21T00:00:00+00:00"),
        )
        conn.execute(
            """
            INSERT INTO mistake_events(
              id, session_id, answer_event_id, skill, severity, tag, explanation, confidence, created_at
            ) VALUES ('mistake_1', 's1', 'ans_1', 'vocab', 'low', 'case', '', 'high', ?)
            """,
            ("2026-05-21T00:00:00+00:00",),
        )
        conn.execute(
            """
            INSERT INTO session_summaries(
              id, session_id, summary_for_user, summary_for_next_boot,
              weak_tags_json, next_focus, cost_snapshot_json, created_at
            ) VALUES ('summary_1', 's1', 'u', 'b', '["case"]', 'review', '{}', ?)
            """,
            ("2026-05-21T00:00:00+00:00",),
        )
        conn.commit()
    finally:
        conn.close()

    migrated = connect(db_path)
    try:
        row = migrated.execute("SELECT * FROM vocabulary_items WHERE id = 'vocab_1'").fetchone()
        review_count = migrated.execute("SELECT COUNT(*) AS count FROM vocabulary_reviews").fetchone()
        mistake_count = migrated.execute("SELECT COUNT(*) AS count FROM mistake_events").fetchone()
        summary_count = migrated.execute("SELECT COUNT(*) AS count FROM session_summaries").fetchone()
        migration_count = migrated.execute("SELECT COUNT(*) AS count FROM migration_records").fetchone()
        assert row["card_type"] == "standard"
        assert row["notes_json"] == "[]"
        assert row["sources_json"] == "[]"
        assert str(row["dedupe_key"]).startswith("standard:")
        assert int(review_count["count"]) == 1
        assert int(mistake_count["count"]) == 1
        assert int(summary_count["count"]) == 1
        assert int(migration_count["count"]) == 3
    finally:
        migrated.close()


def test_existing_tables_accept_reading_and_lesson_skills_without_new_table(tmp_path) -> None:  # type: ignore[no-untyped-def]
    conn = connect(tmp_path / "db.sqlite3")
    try:
        before = {
            row["name"] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
        }
        for event_id, skill, prompt_ref in (
            ("ans_read", "reading", "reading_x"),
            ("ans_lesson", "lesson", "lesson_x"),
            ("ans_transcript", "reading", "transcript_x"),
        ):
            conn.execute(
                """
                INSERT INTO answer_events(id, session_id, skill, prompt_ref, learner_answer, outcome, recorded_at)
                VALUES (?, 's1', ?, ?, 'a', 'partial', '2026-05-21T00:00:00+00:00')
                """,
                (event_id, skill, prompt_ref),
            )
            conn.execute(
                """
                INSERT INTO mistake_events(id, session_id, answer_event_id, skill, severity, tag, explanation, confidence, created_at)
                VALUES (?, 's1', ?, ?, 'low', 'case', '', 'medium', '2026-05-21T00:00:00+00:00')
                """,
                (f"m_{event_id}", event_id, skill),
            )
        conn.commit()
        after = {
            row["name"] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
        }
        skills = {
            str(row["skill"]) for row in conn.execute("SELECT DISTINCT skill FROM answer_events")
        }
        assert after == before  # no new runtime table introduced
        assert {"reading", "lesson"} <= skills
    finally:
        conn.close()


def test_progress_index_migration_order_and_indexes(tmp_path) -> None:  # type: ignore[no-untyped-def]
    conn = connect(tmp_path / "db.sqlite3")
    try:
        versions = [
            int(row["version"])
            for row in conn.execute("SELECT version FROM migration_records ORDER BY version")
        ]
        indexes = {
            row["name"] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='index'")
        }
        assert versions == [1, 2, 3]
        assert {
            "idx_progress_sessions_created",
            "idx_progress_reviews_session_time",
            "idx_progress_mistakes_session_time",
            "idx_progress_answers_session_skill_time",
            "idx_progress_vocab_due_state",
        } <= indexes
    finally:
        conn.close()
