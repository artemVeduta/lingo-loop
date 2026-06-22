from __future__ import annotations

from typing import Any


def book_record_payload(book_session_id: str, kind: str = "word", **overrides: Any) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "book_session_id": book_session_id,
        "kind": kind,
        "content": "esquivo",
        "context": None,
        "explanation": {"translation": "evasive", "gloss": "adjective"},
    }
    if kind == "sentence" or kind == "passage":
        payload["content"] = "Hola mundo."
        payload["explanation"] = {"translation": "Hello world."}
    elif kind == "question":
        payload["content"] = "Why?"
        payload["explanation"] = {"answer": "Because."}
    payload.update(overrides)
    return payload
