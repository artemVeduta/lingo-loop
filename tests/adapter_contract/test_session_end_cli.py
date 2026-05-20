from __future__ import annotations

from tests.conftest import invoke_json


def test_session_end_pending_when_no_analysis(runner) -> None:  # type: ignore[no-untyped-def]
    result = invoke_json(runner, ["session-end", "--json", '{"session_id":"s1"}'])
    assert result["status"] == "pending"
