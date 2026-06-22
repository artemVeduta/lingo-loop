from __future__ import annotations

from datetime import UTC, datetime

import pytest

from language_tutor.book import (
    close_book,
    list_book,
    log_book,
    record_book,
    resume_book,
    start_book,
)
from language_tutor.dal.book_repository import BookRepository
from language_tutor.dal.repositories import TutorRepository
from language_tutor.dal.sqlite_store import connect
from language_tutor.errors import TutorError


def _now() -> datetime:
    return datetime(2026, 6, 22, 12, 0, 0, tzinfo=UTC)


def _seed(conn, session_id: str = "sess_seed") -> None:  # type: ignore[no-untyped-def]
    conn.execute(
        "INSERT INTO sessions (id, host, status, started_at, last_seen_at) "
        "VALUES (?, 'claude', 'open', ?, ?)",
        (session_id, _now().isoformat(), _now().isoformat()),
    )
    conn.commit()


def _repos(conn):  # type: ignore[no-untyped-def]
    return BookRepository(conn), TutorRepository(conn)


def test_start_book_returns_session(tmp_path) -> None:  # type: ignore[no-untyped-def]
    conn = connect(tmp_path / "db.sqlite3")
    try:
        _seed(conn)
        book_repo, _ = _repos(conn)
        session = start_book(book_repo, session_id="sess_seed", title="Esquivo", author="Cela", now=_now())
        assert session.title == "Esquivo"
        assert session.author == "Cela"
    finally:
        conn.close()


def test_record_word_feeds_srs_on_usable_translation(tmp_path) -> None:  # type: ignore[no-untyped-def]
    conn = connect(tmp_path / "db.sqlite3")
    try:
        _seed(conn)
        book_repo, tutor_repo = _repos(conn)
        session = start_book(book_repo, session_id="sess_seed", title="Bk", author=None, now=_now())
        result = record_book(
            book_repo=book_repo,
            tutor_repo=tutor_repo,
            book_session_id=session.book_session_id,
            kind="word",
            content="esquivo",
            context=None,
            explanation={"translation": "evasive", "gloss": "adjective"},
            target_language="es",
            now=_now(),
        )
        assert result.deduped is False
        assert result.vocab_item_id is not None
        assert result.vocab_item_id.startswith("vocab_")
        assert "evasive" in result.rendered
        assert "esquivo" in result.rendered
    finally:
        conn.close()


def test_record_word_skips_srs_on_echo_translation(tmp_path) -> None:  # type: ignore[no-untyped-def]
    conn = connect(tmp_path / "db.sqlite3")
    try:
        _seed(conn)
        book_repo, tutor_repo = _repos(conn)
        session = start_book(book_repo, session_id="sess_seed", title="Bk", author=None, now=_now())
        result = record_book(
            book_repo=book_repo, tutor_repo=tutor_repo,
            book_session_id=session.book_session_id, kind="word", content="hello",
            context=None, explanation={"translation": "hello"}, target_language="en", now=_now(),
        )
        assert result.vocab_item_id is None
        assert "hello" in result.rendered
    finally:
        conn.close()


def test_record_word_skips_srs_on_missing_translation(tmp_path) -> None:  # type: ignore[no-untyped-def]
    conn = connect(tmp_path / "db.sqlite3")
    try:
        _seed(conn)
        book_repo, tutor_repo = _repos(conn)
        session = start_book(book_repo, session_id="sess_seed", title="Bk", author=None, now=_now())
        result = record_book(
            book_repo=book_repo, tutor_repo=tutor_repo,
            book_session_id=session.book_session_id, kind="word", content="x",
            context=None, explanation={"translation": ""}, target_language="en", now=_now(),
        )
        assert result.vocab_item_id is None
        assert result.rendered == "**x**"
    finally:
        conn.close()


def test_record_word_logs_when_translation_field_absent(tmp_path) -> None:  # type: ignore[no-untyped-def]
    conn = connect(tmp_path / "db.sqlite3")
    try:
        _seed(conn)
        book_repo, tutor_repo = _repos(conn)
        session = start_book(book_repo, session_id="sess_seed", title="Bk", author=None, now=_now())
        result = record_book(
            book_repo=book_repo, tutor_repo=tutor_repo,
            book_session_id=session.book_session_id, kind="word", content="x",
            context=None, explanation={"gloss": "unknown word"}, target_language="en", now=_now(),
        )
        assert result.vocab_item_id is None
        assert result.rendered == "**x** — unknown word"
    finally:
        conn.close()


def test_record_word_dedup_returns_existing_no_srs_refeed(tmp_path) -> None:  # type: ignore[no-untyped-def]
    conn = connect(tmp_path / "db.sqlite3")
    try:
        _seed(conn)
        book_repo, tutor_repo = _repos(conn)
        session = start_book(book_repo, session_id="sess_seed", title="Bk", author=None, now=_now())
        first = record_book(
            book_repo=book_repo, tutor_repo=tutor_repo,
            book_session_id=session.book_session_id, kind="word", content="esquivo",
            context=None, explanation={"translation": "evasive"}, target_language="es", now=_now(),
        )
        second = record_book(
            book_repo=book_repo, tutor_repo=tutor_repo,
            book_session_id=session.book_session_id, kind="word", content="Esquivo",
            context=None, explanation={"translation": "evasive"}, target_language="es", now=_now(),
        )
        assert second.deduped is True
        assert second.lookup_id == first.lookup_id
        assert second.vocab_item_id == first.vocab_item_id
    finally:
        conn.close()


def test_record_sentence_passage_question_shapes(tmp_path) -> None:  # type: ignore[no-untyped-def]
    conn = connect(tmp_path / "db.sqlite3")
    try:
        _seed(conn)
        book_repo, tutor_repo = _repos(conn)
        session = start_book(book_repo, session_id="sess_seed", title="Bk", author=None, now=_now())
        s = record_book(
            book_repo=book_repo, tutor_repo=tutor_repo,
            book_session_id=session.book_session_id, kind="sentence", content="Hola mundo",
            context=None, explanation={"translation": "Hello world"}, target_language="es", now=_now(),
        )
        assert s.rendered == "> Hola mundo\n\nHello world"
        p = record_book(
            book_repo=book_repo, tutor_repo=tutor_repo,
            book_session_id=session.book_session_id, kind="passage", content="Long passage",
            context=None, explanation={"translation": "Translation"}, target_language="es", now=_now(),
        )
        assert p.rendered == "> Long passage\n\nTranslation"
        p_explanation = record_book(
            book_repo=book_repo, tutor_repo=tutor_repo,
            book_session_id=session.book_session_id, kind="passage", content="Another passage",
            context=None, explanation={"explanation": "Meaning in context"}, target_language="es", now=_now(),
        )
        assert p_explanation.rendered == "> Another passage\n\nMeaning in context"
        q = record_book(
            book_repo=book_repo, tutor_repo=tutor_repo,
            book_session_id=session.book_session_id, kind="question", content="Why?",
            context=None, explanation={"answer": "Because."}, target_language="es", now=_now(),
        )
        assert q.rendered == "Q: Why?\nA: Because."
    finally:
        conn.close()


def test_record_rejects_closed_session(tmp_path) -> None:  # type: ignore[no-untyped-def]
    conn = connect(tmp_path / "db.sqlite3")
    try:
        _seed(conn)
        book_repo, tutor_repo = _repos(conn)
        session = start_book(book_repo, session_id="sess_seed", title="Bk", author=None, now=_now())
        close_book(book_repo, book_session_id=session.book_session_id, now=_now())
        with pytest.raises(TutorError) as exc:
            record_book(
                book_repo=book_repo, tutor_repo=tutor_repo,
                book_session_id=session.book_session_id, kind="word", content="x",
                context=None, explanation={"translation": "y"}, target_language="en", now=_now(),
            )
        assert exc.value.code == "book_session_closed"
    finally:
        conn.close()


def test_resume_finds_open_by_title(tmp_path) -> None:  # type: ignore[no-untyped-def]
    conn = connect(tmp_path / "db.sqlite3")
    try:
        _seed(conn)
        book_repo, _ = _repos(conn)
        start_book(book_repo, session_id="sess_seed", title="Esquivo", author=None, now=_now())
        resumed = resume_book(book_repo, title="Esquivo")
        assert resumed is not None
        assert resumed.title == "Esquivo"
    finally:
        conn.close()


def test_resume_missing_title_returns_none(tmp_path) -> None:  # type: ignore[no-untyped-def]
    conn = connect(tmp_path / "db.sqlite3")
    try:
        _seed(conn)
        book_repo, _ = _repos(conn)
        assert resume_book(book_repo, title="Nope") is None
    finally:
        conn.close()


def test_log_returns_rendered_numbered_list(tmp_path) -> None:  # type: ignore[no-untyped-def]
    conn = connect(tmp_path / "db.sqlite3")
    try:
        _seed(conn)
        book_repo, tutor_repo = _repos(conn)
        session = start_book(book_repo, session_id="sess_seed", title="Bk", author=None, now=_now())
        record_book(
            book_repo=book_repo, tutor_repo=tutor_repo,
            book_session_id=session.book_session_id, kind="word", content="esquivo",
            context=None, explanation={"translation": "evasive"}, target_language="es",
            now=datetime(2026, 6, 22, 12, 0, 0, tzinfo=UTC),
        )
        record_book(
            book_repo=book_repo, tutor_repo=tutor_repo,
            book_session_id=session.book_session_id, kind="question", content="Why?",
            context=None, explanation={"answer": "Because."}, target_language="es",
            now=datetime(2026, 6, 22, 12, 1, 0, tzinfo=UTC),
        )
        log = log_book(book_repo, book_session_id=session.book_session_id)
        assert len(log.lookups) == 2
        assert log.lookups[0].content == "esquivo"
        assert log.rendered.startswith("1. [word]")
        assert "2. [question]" in log.rendered
    finally:
        conn.close()


def test_log_rejects_unknown_book_session(tmp_path) -> None:  # type: ignore[no-untyped-def]
    conn = connect(tmp_path / "db.sqlite3")
    try:
        book_repo, _ = _repos(conn)
        with pytest.raises(KeyError):
            log_book(book_repo, book_session_id="book_missing")
    finally:
        conn.close()


def test_list_returns_sessions_open_first(tmp_path) -> None:  # type: ignore[no-untyped-def]
    conn = connect(tmp_path / "db.sqlite3")
    try:
        _seed(conn)
        book_repo, _ = _repos(conn)
        a = start_book(book_repo, session_id="sess_seed", title="A", author=None, now=_now())
        start_book(book_repo, session_id="sess_seed", title="B", author=None, now=_now())
        close_book(book_repo, book_session_id=a.book_session_id, now=_now())
        result = list_book(book_repo)
        assert [s.status for s in result.sessions] == ["open", "closed"]
    finally:
        conn.close()


def test_global_card_dedup_across_books(tmp_path) -> None:  # type: ignore[no-untyped-def]
    conn = connect(tmp_path / "db.sqlite3")
    try:
        _seed(conn, "sess_one")
        _seed(conn, "sess_two")
        book_repo, tutor_repo = _repos(conn)
        b1 = start_book(book_repo, session_id="sess_one", title="Book One", author=None, now=_now())
        b2 = start_book(book_repo, session_id="sess_two", title="Book Two", author=None, now=_now())
        first = record_book(
            book_repo=book_repo, tutor_repo=tutor_repo,
            book_session_id=b1.book_session_id, kind="word", content="esquivo",
            context=None, explanation={"translation": "evasive"}, target_language="es", now=_now(),
        )
        second = record_book(
            book_repo=book_repo, tutor_repo=tutor_repo,
            book_session_id=b2.book_session_id, kind="word", content="esquivo",
            context=None, explanation={"translation": "evasive"}, target_language="es", now=_now(),
        )
        # Per-book lookup dedup is independent (different book_session_id) -> not deduped.
        assert second.deduped is False
        # Global SRS card dedup -> same vocab card.
        assert second.vocab_item_id == first.vocab_item_id
    finally:
        conn.close()
