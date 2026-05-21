from __future__ import annotations

import json
from pathlib import Path

import pytest

TEXT_MODALITY_DIR = Path("tests/fixtures/text_modalities")
REQUIRED_RUNS_PER_FIXTURE = 5


def test_semantic_fixture_count() -> None:
    cases = json.loads(Path("tests/fixtures/evaluator_slavic/cases.json").read_text())
    assert len(cases) >= 20


@pytest.mark.parametrize("filename", ["reading.json", "lesson.json", "transcript.json"])
def test_text_modality_semantic_threshold_metadata(filename: str) -> None:
    data = json.loads((TEXT_MODALITY_DIR / filename).read_text())
    fixtures = data["fixtures"]
    # Contract: at least 3 fixtures per modality, each defining run-set threshold inputs.
    assert len(fixtures) >= 3
    assert REQUIRED_RUNS_PER_FIXTURE == 5
    for fixture in fixtures:
        assert "expected_verdict" in fixture
        assert "required_tags" in fixture
        assert "unsafe_definitive_correction" in fixture
