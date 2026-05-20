from __future__ import annotations

from tests.conftest import invoke_json


def test_setup_write_and_read(runner) -> None:  # type: ignore[no-untyped-def]
    invoke_json(
        runner,
        [
            "setup",
            "write",
            "--json",
            '{"profile":{"native_language":"en","target_language":"uk"},"preferences":{}}',
        ],
    )
    state = invoke_json(runner, ["setup", "read", "--json"])
    assert state["profile"]["target_language"] == "uk"
    assert state["preferences"]["session_length"] == 10
