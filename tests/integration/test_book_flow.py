from __future__ import annotations

import json

from tests.conftest import invoke_json
from tests.fixtures.book.builders import book_record_payload

SETUP = (
    '{"profile":{"native_language":"en","target_language":"Spanish","level_target":"A2"}}'
)


def _setup(runner) -> None:  # type: ignore[no-untyped-def]
    invoke_json(runner, ["setup", "write", "--json", SETUP])


def _start_session(runner) -> str:  # type: ignore[no-untyped-def]
    boot = invoke_json(runner, ["session-start", "--json", '{"host":"claude"}'])
    return str(boot["session_id"])


def _start_book(runner, session_id: str, title: str = "Esquivo") -> str:  # type: ignore[no-untyped-def]
    result = invoke_json(
        runner,
        ["book", "start", "--json", json.dumps({"session_id": session_id, "title": title, "author": "Cela"})],
    )
    return str(result["book_session_id"])


def test_book_start_record_log_close_flow(runner) -> None:  # type: ignore[no-untyped-def]
    _setup(runner)
    session_id = _start_session(runner)
    book_id = _start_book(runner, session_id, title="Esquivo")
    result = invoke_json(runner, ["book", "record", "--json", json.dumps(book_record_payload(book_id))])
    assert result["deduped"] is False
    assert result["vocab_item_id"].startswith("vocab_")
    assert "esquivo" in result["rendered"]
    log = invoke_json(runner, ["book", "log", "--json", json.dumps({"book_session_id": book_id})])
    assert len(log["lookups"]) == 1
    assert log["rendered"].startswith("1. [word]")
    closed = invoke_json(runner, ["book", "close", "--json", json.dumps({"book_session_id": book_id})])
    assert closed["status"] == "closed"


def test_book_record_on_closed_returns_error_envelope(runner) -> None:  # type: ignore[no-untyped-def]
    _setup(runner)
    session_id = _start_session(runner)
    book_id = _start_book(runner, session_id)
    invoke_json(runner, ["book", "close", "--json", json.dumps({"book_session_id": book_id})])
    result = runner.invoke(
        __import__("language_tutor.cli").cli.main,
        ["book", "record", "--json", json.dumps(book_record_payload(book_id))],
    )
    assert result.exit_code == 1
    assert json.loads(result.output)["error"]["code"] == "book_session_closed"


def test_book_resume_finds_open_session(runner) -> None:  # type: ignore[no-untyped-def]
    _setup(runner)
    session_id = _start_session(runner)
    _start_book(runner, session_id, title="Esquivo")
    resumed = invoke_json(runner, ["book", "resume", "--json", json.dumps({"title": "Esquivo"})])
    assert resumed["title"] == "Esquivo"
    assert resumed["status"] == "open"


def test_book_list_returns_open_first(runner) -> None:  # type: ignore[no-untyped-def]
    _setup(runner)
    session_id = _start_session(runner)
    a = _start_book(runner, session_id, title="A")
    _start_book(runner, session_id, title="B")
    invoke_json(runner, ["book", "close", "--json", json.dumps({"book_session_id": a})])
    result = invoke_json(runner, ["book", "list", "--json", "{}"])
    assert [s["status"] for s in result["sessions"]] == ["open", "closed"]


def test_book_record_word_echo_translation_logs_without_card(runner) -> None:  # type: ignore[no-untyped-def]
    _setup(runner)
    session_id = _start_session(runner)
    book_id = _start_book(runner, session_id)
    result = invoke_json(
        runner,
        ["book", "record", "--json", json.dumps(book_record_payload(book_id, content="hello", explanation={"translation": "hello"}))],
    )
    assert result["vocab_item_id"] is None
    assert result["rendered"] == "**hello**"
