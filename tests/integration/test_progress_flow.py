from __future__ import annotations

from tests.conftest import invoke_json


def test_empty_progress(runner) -> None:  # type: ignore[no-untyped-def]
    result = invoke_json(runner, ["progress", "--json"])
    assert result["cost_status"] == "unavailable"
    assert "next_action" in result
