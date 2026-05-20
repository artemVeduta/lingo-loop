from __future__ import annotations

from tests.conftest import invoke_json


def test_progress_json_stable_shape(runner) -> None:  # type: ignore[no-untyped-def]
    result = invoke_json(runner, ["progress", "--json"])
    assert set(result) >= {"streak_days", "due_count", "weak_patterns", "maturity"}
