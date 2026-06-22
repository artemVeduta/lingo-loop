"""Book-reading companion handlers (pure functions; CLI layer calls these)."""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any

from language_tutor.dal.book_repository import BookRepository
from language_tutor.dal.repositories import TutorRepository
from language_tutor.dal.sqlite_store import transaction
from language_tutor.errors import TutorError
from language_tutor.schemas import BookList, BookLog, BookLogEntry, BookLookupResult, BookSession
from language_tutor.vocab import find_or_create_vocab_card_for_book, normalize_text


def start_book(
    repo: BookRepository,
    *,
    session_id: str,
    title: str,
    author: str | None,
    now: datetime,
) -> BookSession:
    if not title.strip():
        raise TutorError(
            "invalid_book_start",
            "A title is required to start a reading session.",
            "Pass a non-empty title.",
        )
    return repo.start_book_session(
        session_id=session_id,
        title=title,
        title_norm=normalize_text(title),
        author=author,
        now=now,
    )


def record_book(
    *,
    book_repo: BookRepository,
    tutor_repo: TutorRepository,
    book_session_id: str,
    kind: str,
    content: str,
    context: str | None,
    explanation: dict[str, Any],
    target_language: str,
    now: datetime,
) -> BookLookupResult:
    if not content.strip():
        raise TutorError(
            "invalid_book_record",
            "content is required.",
            "Pass a non-empty word/sentence/passage/question.",
        )

    session = book_repo.get_book_session(book_session_id)
    if session is None:
        raise KeyError(book_session_id)
    if session.status != "open":
        raise TutorError(
            "book_session_closed",
            "This reading session is closed.",
            "Call `tutor book start` for a new session or `tutor book resume` to continue an open one.",
        )

    explanation_json = json.dumps(explanation, ensure_ascii=False)
    book_source = session.title if session.author is None else f"{session.title} — {session.author}"

    if kind == "word":
        content_norm = normalize_text(content)
        with transaction(book_repo.conn):
            existing = book_repo.find_word_lookup(book_session_id, content_norm)
            if existing is not None:
                # Per-book word dedup: return the stored row, no SRS re-feed.
                stored = json.loads(book_repo.read_explanation_json(existing.lookup_id))
                return existing.model_copy(update={"rendered": render_lookup(kind, content, stored)})
            vocab_item_id = _maybe_feed_srs(
                tutor_repo,
                content=content,
                explanation=explanation,
                book_source=book_source,
                target_language=target_language,
            )
            result = book_repo.record_lookup_in_tx(
                book_session_id=book_session_id,
                kind=kind,
                content=content,
                content_norm=content_norm,
                context=context,
                explanation_json=explanation_json,
                vocab_item_id=vocab_item_id,
                now=now,
            )
    else:
        result = book_repo.record_lookup(
            book_session_id=book_session_id,
            kind=kind,
            content=content,
            content_norm=None,
            context=context,
            explanation_json=explanation_json,
            vocab_item_id=None,
            now=now,
        )
    return result.model_copy(update={"rendered": render_lookup(kind, content, explanation)})


def _maybe_feed_srs(
    tutor_repo: TutorRepository,
    *,
    content: str,
    explanation: dict[str, Any],
    book_source: str,
    target_language: str,
) -> str | None:
    """Feed the global SRS card for a usable word translation; return its id (or None).

    A translation is usable when present and not an echo of the word itself.
    """
    translation = str(explanation.get("translation", "")).strip()
    if not translation or normalize_text(translation) == normalize_text(content):
        return None
    gloss = explanation.get("gloss")
    gloss_str = str(gloss).strip() if gloss else None
    _status, vocab_item_id = find_or_create_vocab_card_for_book(
        tutor_repo,
        word=content,
        translation=translation,
        gloss=gloss_str,
        book_source=book_source,
        target_language=target_language,
    )
    return vocab_item_id


def resume_book(repo: BookRepository, *, title: str) -> BookSession | None:
    return repo.get_open_book_session_by_title(normalize_text(title))


def log_book(repo: BookRepository, *, book_session_id: str) -> BookLog:
    entries = [
        BookLogEntry(
            lookup_id=row.lookup_id,
            kind=row.kind,
            content=row.content,
            created_at=row.created_at,
            rendered=render_lookup(row.kind, row.content, row.explanation),
        )
        for row in repo.read_lookups(book_session_id)
    ]
    full_rendered = "\n".join(
        f"{n}. [{entry.kind}] {entry.rendered}" for n, entry in enumerate(entries, start=1)
    )
    return BookLog(book_session_id=book_session_id, lookups=entries, rendered=full_rendered)


def list_book(repo: BookRepository) -> BookList:
    return repo.list_book_sessions()


def close_book(repo: BookRepository, *, book_session_id: str, now: datetime) -> BookSession:
    return repo.close_book_session(book_session_id, now=now)


def render_lookup(kind: str, content: str, explanation: dict[str, Any]) -> str:
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
    raise TutorError("invalid_book_record", f"Unknown kind: {kind}", "Use word/sentence/passage/question.")
