from __future__ import annotations

import json

from tests.conftest import invoke_json
from tests.fixtures.text_modalities.builders import (
    reading_candidate,
    record_payload,
    transcript_candidate,
)

SETUP = (
    '{"profile":{"native_language":"en","target_language":"Ukrainian","level_target":"A2"}}'
)


def _setup(runner) -> None:  # type: ignore[no-untyped-def]
    invoke_json(runner, ["setup", "write", "--json", SETUP])


def test_reading_start_success(runner) -> None:  # type: ignore[no-untyped-def]
    _setup(runner)
    payload = json.dumps({"mode": "comprehension", "candidate": reading_candidate()})
    exercise = invoke_json(runner, ["reading", "start", "--json", payload])
    assert exercise["modality"] == "reading"
    assert exercise["rendered_char_count"] <= 1200
    assert "text_only" in exercise["scope_guardrails"]


def test_reading_start_invalid_candidate_returns_error(runner) -> None:  # type: ignore[no-untyped-def]
    _setup(runner)
    payload = json.dumps(
        {"mode": "comprehension", "candidate": reading_candidate(target_language="Polish")}
    )
    result = runner.invoke(__import__("language_tutor.cli").cli.main, ["reading", "start", "--json", payload])
    assert result.exit_code == 1
    body = json.loads(result.output)
    assert body["error"]["code"] == "invalid_text_exercise"


def test_reading_start_over_budget_returns_error(runner) -> None:  # type: ignore[no-untyped-def]
    _setup(runner)
    payload = json.dumps(
        {"mode": "comprehension", "candidate": reading_candidate(content="х" * 1300)}
    )
    result = runner.invoke(__import__("language_tutor.cli").cli.main, ["reading", "start", "--json", payload])
    assert result.exit_code == 1
    body = json.loads(result.output)
    assert body["error"]["code"] == "text_exercise_too_long"


def test_reading_record_returns_text_modality_result(runner) -> None:  # type: ignore[no-untyped-def]
    _setup(runner)
    start = invoke_json(
        runner,
        ["reading", "start", "--json", json.dumps({"mode": "comprehension", "candidate": reading_candidate()})],
    )
    record = json.dumps(record_payload(start["exercise_id"]))
    result = invoke_json(runner, ["reading", "record", "--json", record])
    assert result["schema_version"] == 1
    assert result["answer_event"]["skill"] == "reading"
    assert result["persisted_mistakes"] == 1
    assert result["feedback"]["verdict"] == "partial"


def test_transcript_start_stays_text_only(runner) -> None:  # type: ignore[no-untyped-def]
    _setup(runner)
    payload = json.dumps({"mode": "transcript", "candidate": transcript_candidate()})
    exercise = invoke_json(runner, ["reading", "start", "--json", payload])
    assert exercise["modality"] == "transcript"
    assert exercise["exercise_id"].startswith("transcript_")
    serialized = json.dumps(exercise).lower()
    assert "audio" not in serialized
    assert "play" not in serialized
