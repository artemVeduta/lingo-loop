"""Persistence for the book-reading companion (book_sessions + book_lookups)."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from typing import Any

from language_tutor.dal.sqlite_store import transaction
from language_tutor.errors import TutorError
from language_tutor.schemas import (
    BookList,
    BookListEntry,
    BookLog,
    BookLogEntry,
    BookLookupResult,
    BookSession,
)
from language_tutor.vocab import normalize_text


class BookRepository:
    """Owns the ``book_sessions`` and ``book_lookups`` tables.

    Shares one ``conn`` with ``TutorRepository`` so the SRS card write and the
    lookup insert can run in a single caller-managed transaction (see
    ``book.record_book``). App-layer existence checks supplement the DDL FKs
    (``PRAGMA foreign_keys = ON``), mirroring ``record_checkpoint``.
    """

    def __init__(self, conn: sqlite3.Connection) -> None:
        self.conn = conn

    def start_book_session(
        self,
        *,
        session_id: str,
        title: str,
        title_norm: str,
        author: str | None,
        now: datetime,
    ) -> BookSession:
        with transaction(self.conn):
            row = self.conn.execute(
                "SELECT id, status FROM sessions WHERE id = ?", (session_id,)
            ).fetchone()
            if row is None:
                raise KeyError(session_id)
            if row["status"] != "open":
                raise TutorError(
                    "session_not_open",
                    f"Session {session_id} is not open.",
                    "Call session-start first and use an open session_id.",
                )
            existing = self.conn.execute(
                "SELECT * FROM book_sessions WHERE session_id = ? AND title_norm = ? AND status = 'open'",
                (session_id, title_norm),
            ).fetchone()
            if existing is not None:
                return self._row_to_session(existing)
            book_session_id = f"book_{_uuid_hex()}"
            self.conn.execute(
                """
                INSERT INTO book_sessions (
                    book_session_id, session_id, title, title_norm, author, status, started_at, closed_at
                ) VALUES (?, ?, ?, ?, ?, 'open', ?, NULL)
                """,
                (book_session_id, session_id, title, title_norm, author, now.isoformat()),
            )
            row = self.conn.execute(
                "SELECT * FROM book_sessions WHERE book_session_id = ?", (book_session_id,)
            ).fetchone()
            return self._row_to_session(row)

    def get_open_book_session_by_title(self, title_norm: str) -> BookSession | None:
        row = self.conn.execute(
            "SELECT * FROM book_sessions WHERE title_norm = ? AND status = 'open' "
            "ORDER BY started_at DESC, book_session_id DESC LIMIT 1",
            (title_norm,),
        ).fetchone()
        return self._row_to_session(row) if row is not None else None

    def get_book_session(self, book_session_id: str) -> BookSession | None:
        row = self.conn.execute(
            "SELECT * FROM book_sessions WHERE book_session_id = ?", (book_session_id,)
        ).fetchone()
        return self._row_to_session(row) if row is not None else None

    def list_book_sessions(self) -> BookList:
        rows = self.conn.execute(
            "SELECT bs.*, COUNT(bl.lookup_id) AS lookup_count "
            "FROM book_sessions bs "
            "LEFT JOIN book_lookups bl ON bl.book_session_id = bs.book_session_id "
            "GROUP BY bs.book_session_id "
            "ORDER BY CASE bs.status WHEN 'open' THEN 0 ELSE 1 END, bs.started_at DESC, bs.book_session_id DESC"
        ).fetchall()
        sessions = [self._row_to_list_entry(row) for row in rows]
        return BookList(sessions=sessions)

    def record_lookup(
        self,
        *,
        book_session_id: str,
        kind: str,
        content: str,
        content_norm: str | None,
        context: str | None,
        explanation_json: str,
        vocab_item_id: str | None,
        now: datetime,
    ) -> BookLookupResult:
        with transaction(self.conn):
            return self._record_lookup_inner(
                book_session_id=book_session_id,
                kind=kind,
                content=content,
                content_norm=content_norm,
                context=context,
                explanation_json=explanation_json,
                vocab_item_id=vocab_item_id,
                now=now,
            )

    def _record_lookup_inner(
        self,
        *,
        book_session_id: str,
        kind: str,
        content: str,
        content_norm: str | None,
        context: str | None,
        explanation_json: str,
        vocab_item_id: str | None,
        now: datetime,
    ) -> BookLookupResult:
        session_row = self.conn.execute(
            "SELECT status FROM book_sessions WHERE book_session_id = ?", (book_session_id,)
        ).fetchone()
        if session_row is None:
            raise KeyError(book_session_id)
        if session_row["status"] != "open":
            raise TutorError(
                "book_session_closed",
                "This reading session is closed.",
                "Call `tutor book start` for a new session or `tutor book resume` to continue an open one.",
            )
        if kind == "word" and content_norm is not None:
            existing = self.conn.execute(
                "SELECT * FROM book_lookups WHERE book_session_id = ? AND kind = 'word' AND content_norm = ?",
                (book_session_id, content_norm),
            ).fetchone()
            if existing is not None:
                return self._row_to_lookup_result(existing).model_copy(update={"deduped": True})
        lookup_id = f"lookup_{_uuid_hex()}"
        self.conn.execute(
            """
            INSERT INTO book_lookups (
                lookup_id, book_session_id, kind, content, content_norm, context,
                explanation_json, vocab_item_id, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                lookup_id, book_session_id, kind, content, content_norm, context,
                explanation_json, vocab_item_id, now.isoformat(),
            ),
        )
        row = self.conn.execute(
            "SELECT * FROM book_lookups WHERE lookup_id = ?", (lookup_id,)
        ).fetchone()
        return self._row_to_lookup_result(row)

    def _find_word_lookup(self, book_session_id: str, content_norm: str) -> BookLookupResult | None:
        row = self.conn.execute(
            "SELECT * FROM book_lookups WHERE book_session_id = ? AND kind = 'word' AND content_norm = ?",
            (book_session_id, content_norm),
        ).fetchone()
        if row is None:
            return None
        # Rendering for the deduped row: re-read the explanation blob.
        explanation = json.loads(str(row["explanation_json"]))
        rendered = _render_lookup(str(row["kind"]), str(row["content"]), explanation)
        return BookLookupResult(
            lookup_id=str(row["lookup_id"]),
            vocab_item_id=str(row["vocab_item_id"]) if row["vocab_item_id"] is not None else None,
            deduped=True,
            created_at=_parse_iso(row["created_at"]),
            rendered=rendered,
        )

    def get_lookups(self, book_session_id: str) -> BookLog:
        session_row = self.conn.execute(
            "SELECT 1 FROM book_sessions WHERE book_session_id = ?", (book_session_id,)
        ).fetchone()
        if session_row is None:
            raise KeyError(book_session_id)
        rows = self.conn.execute(
            "SELECT * FROM book_lookups WHERE book_session_id = ? ORDER BY created_at ASC, lookup_id ASC",
            (book_session_id,),
        ).fetchall()
        entries = [
            BookLogEntry(
                lookup_id=str(row["lookup_id"]),
                kind=str(row["kind"]),  # type: ignore[arg-type]
                content=str(row["content"]),
                created_at=_parse_iso(row["created_at"]),
                rendered="",
            )
            for row in rows
        ]
        return BookLog(book_session_id=book_session_id, lookups=entries, rendered="")

    def close_book_session(self, book_session_id: str, *, now: datetime) -> BookSession:
        with transaction(self.conn):
            row = self.conn.execute(
                "SELECT * FROM book_sessions WHERE book_session_id = ?", (book_session_id,)
            ).fetchone()
            if row is None:
                raise KeyError(book_session_id)
            if row["status"] == "closed":
                raise TutorError(
                    "book_session_already_closed",
                    "This reading session is already closed.",
                    "Start a new session with `tutor book start`.",
                )
            self.conn.execute(
                "UPDATE book_sessions SET status = 'closed', closed_at = ? WHERE book_session_id = ?",
                (now.isoformat(), book_session_id),
            )
            row = self.conn.execute(
                "SELECT * FROM book_sessions WHERE book_session_id = ?", (book_session_id,)
            ).fetchone()
            return self._row_to_session(row)

    def _row_to_session(self, row: sqlite3.Row) -> BookSession:
        return BookSession(
            book_session_id=str(row["book_session_id"]),
            session_id=str(row["session_id"]),
            title=str(row["title"]),
            author=str(row["author"]) if row["author"] is not None else None,
            status=str(row["status"]),  # type: ignore[arg-type]
            started_at=_parse_iso(row["started_at"]),
            closed_at=_parse_iso(row["closed_at"]) if row["closed_at"] is not None else None,
        )

    def _row_to_list_entry(self, row: sqlite3.Row) -> BookListEntry:
        return BookListEntry(
            book_session_id=str(row["book_session_id"]),
            session_id=str(row["session_id"]),
            title=str(row["title"]),
            author=str(row["author"]) if row["author"] is not None else None,
            status=str(row["status"]),  # type: ignore[arg-type]
            started_at=_parse_iso(row["started_at"]),
            closed_at=_parse_iso(row["closed_at"]) if row["closed_at"] is not None else None,
            lookup_count=int(row["lookup_count"]),
        )

    def _row_to_lookup_result(self, row: sqlite3.Row) -> BookLookupResult:
        return BookLookupResult(
            lookup_id=str(row["lookup_id"]),
            vocab_item_id=str(row["vocab_item_id"]) if row["vocab_item_id"] is not None else None,
            deduped=False,
            created_at=_parse_iso(row["created_at"]),
            rendered="",
        )


def _uuid_hex() -> str:
    import uuid

    return uuid.uuid4().hex


def _parse_iso(value: str) -> datetime:
    return datetime.fromisoformat(str(value))


def _render_lookup(kind: str, content: str, explanation: dict[str, Any]) -> str:
    if kind == "word":
        translation = str(explanation.get("translation", "")).strip()
        gloss = explanation.get("gloss")
        gloss_str = str(gloss).strip() if gloss else None
        rendered = f"**{content}**"
        if gloss_str:
            rendered += f" — {gloss_str}"
        if translation and normalize_text(translation) != normalize_text(content):
            rendered += f" (translation: {translation})"
        return rendered
    if kind == "sentence":
        return f"> {content}\n\n{explanation.get('translation', '')}"
    if kind == "passage":
        body = explanation.get("translation") or explanation.get("explanation", "")
        return f"> {content}\n\n{body}"
    if kind == "question":
        return f"Q: {content}\nA: {explanation.get('answer', '')}"
    return ""
