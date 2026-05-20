from __future__ import annotations

from tests.conftest import invoke_json


def test_first_session_flow(runner) -> None:  # type: ignore[no-untyped-def]
    invoke_json(
        runner,
        [
            "setup",
            "write",
            "--json",
            '{"profile":{"native_language":"en","target_language":"uk"},"preferences":{}}',
        ],
    )
    context = invoke_json(runner, ["boot-context", "--json"])
    rendered = invoke_json(
        runner, ["render", "boot-context", "--json", __import__("json").dumps(context)]
    )
    assert "First session guidance" in rendered["markdown"]
    assert len(rendered["markdown"]) <= 6000
