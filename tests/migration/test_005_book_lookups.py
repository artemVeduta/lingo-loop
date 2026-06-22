from __future__ import annotations

import contextlib
import sqlite3
from pathlib import Path

from language_tutor.dal.sqlite_store import connect
from language_tutor.package_assets import REQUIRED_MIGRATION_FILES

MIGRATION_PATH = Path(__file__).resolve().parents[2] / "migrations" / "005_book_lookups.sql"


def test_005_creates_book_tables_and_expands_checkpoints(tmp_path) -> None:  # type: ignore[no-untyped-def]
    conn = connect(tmp_path / "db.sqlite3")
    try:
        tables = {
            row["name"]
            for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
        }
        assert {"book_sessions", "book_lookups"} <= tables

        session_cols = {
            row["name"] for row in conn.execute("PRAGMA table_info(book_sessions)").fetchall()
        }
        assert {
            "book_session_id",
            "session_id",
            "title",
            "title_norm",
            "author",
            "status",
            "started_at",
            "closed_at",
        } <= session_cols

        lookup_cols = {
            row["name"] for row in conn.execute("PRAGMA table_info(book_lookups)").fetchall()
        }
        assert {
            "lookup_id",
            "book_session_id",
            "kind",
            "content",
            "content_norm",
            "context",
            "explanation_json",
            "vocab_item_id",
            "created_at",
        } <= lookup_cols

        indexes = {
            row["name"]
            for row in conn.execute("SELECT name FROM sqlite_master WHERE type='index'")
        }
        assert {
            "idx_book_sessions_session",
            "idx_book_sessions_open_per_session",
            "idx_book_sessions_title_norm",
            "idx_book_lookups_session",
            "idx_book_lookups_word",
            "idx_checkpoints_session",
            "idx_checkpoints_created",
        } <= indexes

        # New modality + step_kind accepted by the rebuilt checkpoints CHECKs.
        conn.execute(
            "INSERT INTO sessions (id, host, status, started_at, last_seen_at) "
            "VALUES ('sess_t1', 'claude', 'open', '2026-06-22T00:00:00', '2026-06-22T00:00:00')"
        )
        conn.execute(
            "INSERT INTO checkpoints (id, session_id, modality, step_kind, state_json, summary, created_at) "
            "VALUES ('ckpt_b1', 'sess_t1', 'book', 'answer_recorded', '{}', 'lookup', '2026-06-22T00:00:00')"
        )
        conn.rollback()
    finally:
        conn.close()


def test_005_is_sequential_version_five(tmp_path) -> None:  # type: ignore[no-untyped-def]
    conn = connect(tmp_path / "db.sqlite3")
    try:
        versions = [
            int(row["version"])
            for row in conn.execute("SELECT version FROM migration_records ORDER BY version")
        ]
        assert versions == [1, 2, 3, 4, 5]
        names = {
            str(row["name"])
            for row in conn.execute("SELECT name FROM migration_records WHERE version = 5")
        }
        assert names == {"book_lookups"}
    finally:
        conn.close()


def test_005_is_idempotent_when_reapplied(tmp_path) -> None:  # type: ignore[no-untyped-def]
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


def test_005_rebuild_is_atomic_on_mid_rebuild_failure(tmp_path) -> None:  # type: ignore[no-untyped-def]
    # Apply all migrations, seed a checkpoint row, then run a poisoned rebuild
    # that fails mid-script. The BEGIN/COMMIT-wrapped rebuild must roll back,
    # leaving the original checkpoints (rows + schema) intact.
    conn = connect(tmp_path / "db.sqlite3")
    try:
        conn.execute(
            "INSERT INTO sessions (id, host, status, started_at, last_seen_at) "
            "VALUES ('sess_a', 'claude', 'open', '2026-06-22T00:00:00', '2026-06-22T00:00:00')"
        )
        conn.execute(
            "INSERT INTO checkpoints (id, session_id, modality, step_kind, state_json, summary, created_at) "
            "VALUES ('ckpt_orig', 'sess_a', 'reading', 'prompt_shown', '{}', 'orig', '2026-06-22T00:00:00')"
        )
        conn.commit()
    finally:
        conn.close()

    # Build a poisoned 005 script: keep the BEGIN ... DROP TABLE checkpoints,
    # then inject a broken statement before COMMIT.
    sql = MIGRATION_PATH.read_text(encoding="utf-8")
    drop_pos = sql.index("DROP TABLE checkpoints;")
    poisoned = sql[: drop_pos + len("DROP TABLE checkpoints;")] + "\nSELECT no_such_function_x();\n"
    conn = connect(tmp_path / "db.sqlite3", migrate=False)
    try:
        with contextlib.suppress(sqlite3.OperationalError):
            conn.executescript(poisoned)
        conn.rollback()
    finally:
        conn.close()

    # Reopen on a fresh connection (migration_records has no version 5 entry because
    # the poisoned run never completed). Verify the original row survived and the
    # real 005 applies cleanly.
    conn = connect(tmp_path / "db.sqlite3")
    try:
        row = conn.execute(
            "SELECT id, summary FROM checkpoints WHERE id = 'ckpt_orig'"
        ).fetchone()
        assert row is not None
        assert row["summary"] == "orig"
        versions = [
            int(row["version"])
            for row in conn.execute("SELECT version FROM migration_records ORDER BY version")
        ]
        assert versions == [1, 2, 3, 4, 5]
    finally:
        conn.close()


def test_005_registered_in_required_migration_files() -> None:  # type: ignore[no-untyped-def]
    assert "migrations/005_book_lookups.sql" in REQUIRED_MIGRATION_FILES
