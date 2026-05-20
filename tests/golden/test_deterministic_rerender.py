from __future__ import annotations

import json

from tests.conftest import invoke_json


def test_render_boot_context_deterministic(runner) -> None:  # type: ignore[no-untyped-def]
    context = invoke_json(runner, ["boot-context", "--json"])
    payload = json.dumps(context, sort_keys=True)
    first = invoke_json(runner, ["render", "boot-context", "--json", payload])
    second = invoke_json(runner, ["render", "boot-context", "--json", payload])
    assert first == second
