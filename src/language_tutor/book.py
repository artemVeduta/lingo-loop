"""Book-reading companion handlers (pure functions; CLI layer calls these)."""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any

from language_tutor.dal.book_repository import BookRepository
from language_tutor.dal.repositories import TutorRepository
from language_tutor.dal.sqlite_store import transaction
from language_tutor.errors import TutorError
from language_tutor.schemas import BookList, BookLog, BookLookupResult, BookSession
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
    _validate_explanation_shape(kind, explanation)

    session = book_repo.get_book_session(book_session_id)
    if session is None:
        raise KeyError(book_session_id)
    if session.status != "open":
        raise TutorError(
            "book_session_closed",
            "This reading session is closed.",
            "Call `tutor book start` for a new session or `tutor book resume` to continue an open one.",
        )

    content_norm = normalize_text(content) if kind == "word" else None
    book_source = session.title if session.author is None else f"{session.title} — {session.author}"

    if kind == "word":
        # Per-book word dedup: return existing row, no SRS re-feed.
        existing = book_repo._find_word_lookup(book_session_id, content_norm)  # type: ignore[attr-defined]
        if existing is not None:
            return BookLookupResult(
                lookup_id=existing.lookup_id,
                vocab_item_id=existing.vocab_item_id,
                deduped=True,
                created_at=existing.created_at,
                rendered=existing.rendered,
            )

        translation = str(explanation.get("translation", "")).strip()
        gloss = explanation.get("gloss")
        gloss_str = str(gloss).strip() if gloss else None
        usable = bool(translation) and normalize_text(translation) != normalize_text(content)

        if usable:
            with transaction(book_repo.conn):
                _status, vocab_item_id = find_or_create_vocab_card_for_book(
                    tutor_repo,
                    word=content,
                    translation=translation,
                    gloss=gloss_str,
                    book_source=book_source,
                    target_language=target_language,
                )
                result = book_repo._record_lookup_inner(
                    book_session_id=book_session_id,
                    kind=kind,
                    content=content,
                    content_norm=content_norm,
                    context=context,
                    explanation_json=json.dumps(explanation, ensure_ascii=False),
                    vocab_item_id=vocab_item_id,
                    now=now,
                )
        else:
            result = book_repo.record_lookup(
                book_session_id=book_session_id,
                kind=kind,
                content=content,
                content_norm=content_norm,
                context=context,
                explanation_json=json.dumps(explanation, ensure_ascii=False),
                vocab_item_id=None,
                now=now,
            )
        return BookLookupResult(
            lookup_id=result.lookup_id,
            vocab_item_id=result.vocab_item_id,
            deduped=False,
            created_at=result.created_at,
            rendered=render_lookup(kind, content, explanation),
        )

    result = book_repo.record_lookup(
        book_session_id=book_session_id,
        kind=kind,
        content=content,
        content_norm=None,
        context=context,
        explanation_json=json.dumps(explanation, ensure_ascii=False),
        vocab_item_id=None,
        now=now,
    )
    return BookLookupResult(
        lookup_id=result.lookup_id,
        vocab_item_id=result.vocab_item_id,
        deduped=False,
        created_at=result.created_at,
        rendered=render_lookup(kind, content, explanation),
    )


def resume_book(repo: BookRepository, *, title: str) -> BookSession | None:
    return repo.get_open_book_session_by_title(normalize_text(title))


def log_book(repo: BookRepository, *, book_session_id: str) -> BookLog:
    log = repo.get_lookups(book_session_id)
    entries = []
    for _n, entry in enumerate(log.lookups, start=1):
        explanation = json.loads(_read_explanation(repo, entry.lookup_id))
        rendered = render_lookup(entry.kind, entry.content, explanation)
        entries.append(entry.model_copy(update={"rendered": rendered}))
    full_rendered = "\n".join(
        f"{n}. [{entry.kind}] {entry.rendered}" for n, entry in enumerate(entries, start=1)
    )
    return log.model_copy(update={"lookups": entries, "rendered": full_rendered})


def list_book(repo: BookRepository) -> BookList:
    return repo.list_book_sessions()


def close_book(repo: BookRepository, *, book_session_id: str, now: datetime) -> BookSession:
    return repo.close_book_session(book_session_id, now=now)


def _validate_explanation_shape(kind: str, explanation: dict[str, Any]) -> None:
    if kind == "word":
        if "translation" not in explanation:
            raise TutorError(
                "invalid_book_record",
                "word explanation requires a 'translation' field (may be empty).",
                "Pass {\"translation\": \"...\", \"gloss\"?: \"...\"}.",
            )
    elif kind in ("sentence", "passage"):
        if "translation" not in explanation:
            raise TutorError(
                "invalid_book_record",
                f"{kind} explanation requires a 'translation' field.",
                "Pass {\"translation\": \"...\"}.",
            )
    elif kind == "question" and "answer" not in explanation:
        raise TutorError(
            "invalid_book_record",
            "question explanation requires an 'answer' field.",
            "Pass {\"answer\": \"...\"}.",
        )


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


def _read_explanation(repo: BookRepository, lookup_id: str) -> str:
    row = repo.conn.execute(
        "SELECT explanation_json FROM book_lookups WHERE lookup_id = ?", (lookup_id,)
    ).fetchone()
    return str(row["explanation_json"]) if row is not None else "{}"
