from __future__ import annotations

from tests.conftest import invoke_json


def test_vocab_start_answer_idempotent(runner) -> None:  # type: ignore[no-untyped-def]
    invoke_json(
        runner,
        [
            "setup",
            "write",
            "--json",
            '{"profile":{"native_language":"en","target_language":"uk"},"preferences":{"transliteration_tolerance":true}}',
        ],
    )
    plan = invoke_json(runner, ["vocab", "start", "--json"])
    item_id = plan["items"][0]["id"]  # type: ignore[index]
    payload = f'{{"item_id":"{item_id}","answer":"privit","idempotency_key":"same"}}'
    first = invoke_json(runner, ["vocab", "answer", "--json", payload])
    second = invoke_json(runner, ["vocab", "answer", "--json", payload])
    assert first["review"]["id"] == second["review"]["id"]
    assert second["duplicate"] is True
