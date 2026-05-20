from __future__ import annotations

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
