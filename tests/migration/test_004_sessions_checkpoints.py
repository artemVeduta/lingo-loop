from __future__ import annotations

from language_tutor.dal.sqlite_store import connect


def test_004_creates_sessions_and_checkpoints_tables(tmp_path) -> None:  # type: ignore[no-untyped-def]
    conn = connect(tmp_path / "db.sqlite3")
    try:
        tables = {
            row["name"] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
        }
        assert {"sessions", "checkpoints"} <= tables

        session_cols = {
            row["name"] for row in conn.execute("PRAGMA table_info(sessions)").fetchall()
        }
        assert {
            "id",
            "host",
            "host_conversation_id",
            "status",
            "started_at",
            "last_seen_at",
            "closed_at",
        } <= session_cols

        checkpoint_cols = {
            row["name"] for row in conn.execute("PRAGMA table_info(checkpoints)").fetchall()
        }
        assert {
            "id",
            "session_id",
            "modality",
            "step_kind",
            "prompt_ref",
            "state_json",
            "summary",
            "created_at",
        } <= checkpoint_cols

        indexes = {
            row["name"] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='index'")
        }
        assert {
            "idx_sessions_last_seen",
            "idx_sessions_status",
            "idx_checkpoints_session",
            "idx_checkpoints_created",
        } <= indexes
    finally:
        conn.close()


def test_004_is_idempotent_when_reapplied(tmp_path) -> None:  # type: ignore[no-untyped-def]
    db_path = tmp_path / "db.sqlite3"
    first = connect(db_path)
    first.close()
    second = connect(db_path)
    try:
        versions = [
            int(row["version"])
            for row in second.execute("SELECT version FROM migration_records ORDER BY version")
        ]
        assert versions == [1, 2, 3, 4, 5]
    finally:
        second.close()


def test_004_is_sequential_version_four(tmp_path) -> None:  # type: ignore[no-untyped-def]
    conn = connect(tmp_path / "db.sqlite3")
    try:
        versions = [
            int(row["version"])
            for row in conn.execute("SELECT version FROM migration_records ORDER BY version")
        ]
        assert versions == [1, 2, 3, 4, 5]
        names = {
            str(row["name"])
            for row in conn.execute("SELECT name FROM migration_records WHERE version = 4")
        }
        assert names == {"sessions_checkpoints"}
    finally:
        conn.close()
