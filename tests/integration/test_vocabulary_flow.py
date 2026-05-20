from __future__ import annotations

from tests.conftest import invoke_json


def test_vocabulary_flow(runner) -> None:  # type: ignore[no-untyped-def]
    invoke_json(
        runner,
        [
            "setup",
            "write",
            "--json",
            '{"profile":{"native_language":"en","target_language":"uk"},"preferences":{"session_length":2,"review_intensity":"normal","transliteration_tolerance":true}}',
        ],
    )
    plan = invoke_json(runner, ["vocab", "start", "--json"])
    assert plan["requested_count"] == 2
    item_id = plan["items"][0]["id"]  # type: ignore[index]
    answer = invoke_json(
        runner,
        [
            "vocab",
            "answer",
            "--json",
            f'{{"item_id":"{item_id}","answer":"privit","idempotency_key":"k"}}',
        ],
    )
    assert answer["feedback"]["verdict"] == "correct"
