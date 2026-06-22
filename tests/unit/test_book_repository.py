from __future__ import annotations

from datetime import UTC, datetime

import pytest

from language_tutor.dal.book_repository import BookRepository
from language_tutor.dal.repositories import TutorRepository
from language_tutor.dal.sqlite_store import connect
from language_tutor.errors import TutorError
from language_tutor.schemas import VocabularyItem
from language_tutor.vocab import normalize_text


def _now() -> datetime:
    return datetime(2026, 6, 22, 12, 0, 0, tzinfo=UTC)


def _seed_session(conn, session_id: str = "sess_seed") -> None:  # type: ignore[no-untyped-def]
    conn.execute(
        "INSERT INTO sessions (id, host, status, started_at, last_seen_at) "
        "VALUES (?, 'claude', 'open', ?, ?)",
        (session_id, _now().isoformat(), _now().isoformat()),
    )
    conn.commit()


def _seed_vocab(conn, vocab_id: str = "vocab_1") -> None:  # type: ignore[no-untyped-def]
    TutorRepository(conn).insert_vocabulary_item(
        VocabularyItem(
            id=vocab_id,
            target_language="uk",
            prompt="p",
            accepted_answers=["a"],
        )
    )
    conn.commit()


def test_start_creates_open_session(tmp_path) -> None:  # type: ignore[no-untyped-def]
    conn = connect(tmp_path / "db.sqlite3")
    try:
        _seed_session(conn)
        repo = BookRepository(conn)
        session = repo.start_book_session(
            session_id="sess_seed",
            title="The City of Dreaming Books",
            title_norm=normalize_text("The City of Dreaming Books"),
            author="Walter Moers",
            now=_now(),
        )
        assert session.book_session_id.startswith("book_")
        assert session.status == "open"
        assert session.title == "The City of Dreaming Books"
        assert session.author == "Walter Moers"
        assert session.closed_at is None
    finally:
        conn.close()


def test_start_is_idempotent_within_session_for_open_title(tmp_path) -> None:  # type: ignore[no-untyped-def]
    conn = connect(tmp_path / "db.sqlite3")
    try:
        _seed_session(conn)
        repo = BookRepository(conn)
        first = repo.start_book_session(
            session_id="sess_seed", title="Esquivo", title_norm=normalize_text("Esquivo"), author=None, now=_now()
        )
        second = repo.start_book_session(
            session_id="sess_seed", title="Esquivo", title_norm=normalize_text("Esquivo"), author="New Author", now=_now()
        )
        assert first.book_session_id == second.book_session_id
        # Author set on first start only; idempotent re-start ignores new author.
        assert second.author is None
    finally:
        conn.close()


def test_start_rejects_missing_session(tmp_path) -> None:  # type: ignore[no-untyped-def]
    conn = connect(tmp_path / "db.sqlite3")
    try:
        repo = BookRepository(conn)
        with pytest.raises(KeyError):
            repo.start_book_session(
                session_id="sess_missing", title="X", title_norm="x", author=None, now=_now()
            )
    finally:
        conn.close()


def test_start_rejects_closed_tutor_session(tmp_path) -> None:  # type: ignore[no-untyped-def]
    conn = connect(tmp_path / "db.sqlite3")
    try:
        conn.execute(
            "INSERT INTO sessions (id, host, status, started_at, last_seen_at, closed_at) "
            "VALUES ('sess_closed', 'claude', 'closed', ?, ?, ?)",
            (_now().isoformat(), _now().isoformat(), _now().isoformat()),
        )
        conn.commit()
        repo = BookRepository(conn)
        with pytest.raises(TutorError) as exc:
            repo.start_book_session(
                session_id="sess_closed", title="X", title_norm="x", author=None, now=_now()
            )
        assert exc.value.code == "session_not_open"
    finally:
        conn.close()


def test_resume_finds_most_recent_open_by_title(tmp_path) -> None:  # type: ignore[no-untyped-def]
    conn = connect(tmp_path / "db.sqlite3")
    try:
        _seed_session(conn)
        repo = BookRepository(conn)
        older = repo.start_book_session(
            session_id="sess_seed", title="Reread", title_norm=normalize_text("Reread"), author=None, now=_now()
        )
        # Simulate a second open book session for the same title (different tutor session).
        conn.execute(
            "INSERT INTO sessions (id, host, status, started_at, last_seen_at) "
            "VALUES ('sess_two', 'claude', 'open', ?, ?)",
            (_now().isoformat(), _now().isoformat()),
        )
        conn.commit()
        newer = repo.start_book_session(
            session_id="sess_two", title="Reread", title_norm=normalize_text("Reread"), author=None, now=_now()
        )
        # Insert with explicit started_at ordering: newer has later started_at.
        conn.execute(
            "UPDATE book_sessions SET started_at = ? WHERE book_session_id = ?",
            (_now().isoformat(), newer.book_session_id),
        )
        conn.execute(
            "UPDATE book_sessions SET started_at = ? WHERE book_session_id = ?",
            ("2026-01-01T00:00:00+00:00", older.book_session_id),
        )
        conn.commit()
        resumed = repo.get_open_book_session_by_title(normalize_text("Reread"))
        assert resumed is not None
        assert resumed.book_session_id == newer.book_session_id
    finally:
        conn.close()


def test_record_lookup_inserts_and_dedupes_words(tmp_path) -> None:  # type: ignore[no-untyped-def]
    conn = connect(tmp_path / "db.sqlite3")
    try:
        _seed_session(conn)
        _seed_vocab(conn)
        repo = BookRepository(conn)
        session = repo.start_book_session(
            session_id="sess_seed", title="Bk", title_norm="bk", author=None, now=_now()
        )
        first = repo.record_lookup(
            book_session_id=session.book_session_id,
            kind="word",
            content="esquivo",
            content_norm=normalize_text("esquivo"),
            context=None,
            explanation_json='{"translation":"evasive"}',
            vocab_item_id="vocab_1",
            now=_now(),
        )
        assert first.deduped is False
        assert first.lookup_id.startswith("lookup_")
        second = repo.record_lookup(
            book_session_id=session.book_session_id,
            kind="word",
            content="Esquivo",
            content_norm=normalize_text("Esquivo"),
            context=None,
            explanation_json='{"translation":"evasive"}',
            vocab_item_id="vocab_1",
            now=_now(),
        )
        assert second.deduped is True
        assert second.lookup_id == first.lookup_id
    finally:
        conn.close()


def test_record_lookup_rejects_closed_session(tmp_path) -> None:  # type: ignore[no-untyped-def]
    conn = connect(tmp_path / "db.sqlite3")
    try:
        _seed_session(conn)
        repo = BookRepository(conn)
        session = repo.start_book_session(
            session_id="sess_seed", title="Bk", title_norm="bk", author=None, now=_now()
        )
        repo.close_book_session(session.book_session_id, now=_now())
        with pytest.raises(TutorError) as exc:
            repo.record_lookup(
                book_session_id=session.book_session_id,
                kind="word",
                content="x",
                content_norm="x",
                context=None,
                explanation_json='{"translation":"y"}',
                vocab_item_id=None,
                now=_now(),
            )
        assert exc.value.code == "book_session_closed"
    finally:
        conn.close()


def test_close_marks_closed_and_rejects_already_closed(tmp_path) -> None:  # type: ignore[no-untyped-def]
    conn = connect(tmp_path / "db.sqlite3")
    try:
        _seed_session(conn)
        repo = BookRepository(conn)
        session = repo.start_book_session(
            session_id="sess_seed", title="Bk", title_norm="bk", author=None, now=_now()
        )
        closed = repo.close_book_session(session.book_session_id, now=_now())
        assert closed.status == "closed"
        assert closed.closed_at is not None
        with pytest.raises(TutorError) as exc:
            repo.close_book_session(session.book_session_id, now=_now())
        assert exc.value.code == "book_session_already_closed"
    finally:
        conn.close()


def test_list_orders_open_first_then_closed(tmp_path) -> None:  # type: ignore[no-untyped-def]
    conn = connect(tmp_path / "db.sqlite3")
    try:
        _seed_session(conn)
        repo = BookRepository(conn)
        a = repo.start_book_session(
            session_id="sess_seed", title="A", title_norm="a", author=None, now=_now()
        )
        b = repo.start_book_session(
            session_id="sess_seed", title="B", title_norm="b", author=None, now=_now()
        )
        repo.close_book_session(a.book_session_id, now=_now())
        sessions = repo.list_book_sessions()
        # Open (B) first, then closed (A).
        assert sessions.sessions[0].book_session_id == b.book_session_id
        assert sessions.sessions[0].status == "open"
        assert sessions.sessions[1].book_session_id == a.book_session_id
        assert sessions.sessions[1].status == "closed"
        assert sessions.sessions[0].lookup_count == 0
    finally:
        conn.close()


def test_get_lookups_orders_by_created_at_ascending(tmp_path) -> None:  # type: ignore[no-untyped-def]
    conn = connect(tmp_path / "db.sqlite3")
    try:
        _seed_session(conn)
        repo = BookRepository(conn)
        session = repo.start_book_session(
            session_id="sess_seed", title="Bk", title_norm="bk", author=None, now=_now()
        )
        repo.record_lookup(
            book_session_id=session.book_session_id, kind="sentence", content="one",
            content_norm=None, context=None, explanation_json='{"translation":"1"}',
            vocab_item_id=None, now=datetime(2026, 6, 22, 12, 1, 0, tzinfo=UTC),
        )
        repo.record_lookup(
            book_session_id=session.book_session_id, kind="sentence", content="two",
            content_norm=None, context=None, explanation_json='{"translation":"2"}',
            vocab_item_id=None, now=datetime(2026, 6, 22, 12, 0, 0, tzinfo=UTC),
        )
        lookups = repo.get_lookups(session.book_session_id)
        assert [lk.content for lk in lookups.lookups] == ["two", "one"]
    finally:
        conn.close()
