"""Semantic-eval fixture validation for text-modality feedback.

Per contracts/semantic-eval.md each modality needs >=3 representative fixtures, each run
5 live evaluations (schema-valid 5/5, expected verdict >=4/5, required tags across the
run set, zero unsafe definitive corrections). This repo has no live judge harness in CI,
so these tests deterministically validate that the fixtures are well-formed and
contract-compliant; the 5-live-run execution is the documented manual gate in
quickstart.md. Reading fixtures land in T042, lesson in T058, transcript in T071.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from language_tutor.schemas import TextExerciseCandidate, Verdict

FIXTURE_DIR = Path("tests/fixtures/text_modalities")
_VALID_VERDICTS = {verdict.value for verdict in Verdict}


def _load(name: str) -> list[dict[str, object]]:
    data = json.loads((FIXTURE_DIR / name).read_text(encoding="utf-8"))
    return list(data["fixtures"])


@pytest.mark.parametrize("filename", ["reading.json", "lesson.json", "transcript.json"])
def test_modality_has_at_least_three_fixtures(filename: str) -> None:
    assert len(_load(filename)) >= 3


@pytest.mark.parametrize("filename", ["reading.json", "lesson.json", "transcript.json"])
def test_fixtures_are_contract_compliant(filename: str) -> None:
    for fixture in _load(filename):
        assert fixture["id"]
        # Candidate must be a valid TextExerciseCandidate.
        TextExerciseCandidate.model_validate(fixture["candidate"])
        assert isinstance(fixture["learner_response"], str)
        assert fixture["expected_verdict"] in _VALID_VERDICTS
        assert isinstance(fixture["required_tags"], list)
        assert fixture["unsafe_definitive_correction"]
