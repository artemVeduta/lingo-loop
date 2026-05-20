from __future__ import annotations

import json
from pathlib import Path


def test_semantic_fixture_count() -> None:
    cases = json.loads(Path("tests/fixtures/evaluator_slavic/cases.json").read_text())
    assert len(cases) >= 20
