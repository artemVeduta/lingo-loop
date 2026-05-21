from __future__ import annotations

import json

from tests.conftest import invoke_json
from tests.fixtures.text_modalities.builders import lesson_candidate, record_payload

SETUP = (
    '{"profile":{"native_language":"en","target_language":"Ukrainian","level_target":"A2"}}'
)


def _setup(runner) -> None:  # type: ignore[no-untyped-def]
    invoke_json(runner, ["setup", "write", "--json", SETUP])


def test_lesson_start_weak_tag_focus(runner) -> None:  # type: ignore[no-untyped-def]
    _setup(runner)
    payload = json.dumps({"candidate": lesson_candidate(focus="case")})
    exercise = invoke_json(runner, ["lesson", "start", "--json", payload])
    assert exercise["modality"] == "lesson"
    assert exercise["focus"] == "case"
    assert exercise["rendered_char_count"] <= 1200


def test_lesson_start_selected_topic_flow(runner) -> None:  # type: ignore[no-untyped-def]
    _setup(runner)
    payload = json.dumps({"candidate": lesson_candidate(focus="verbs_of_motion")})
    exercise = invoke_json(runner, ["lesson", "start", "--json", payload])
    assert exercise["focus"] == "verbs_of_motion"


def test_lesson_start_invalid_candidate(runner) -> None:  # type: ignore[no-untyped-def]
    _setup(runner)
    payload = json.dumps({"candidate": lesson_candidate(level_target="C2")})
    result = runner.invoke(__import__("language_tutor.cli").cli.main, ["lesson", "start", "--json", payload])
    assert result.exit_code == 1
    assert json.loads(result.output)["error"]["code"] == "invalid_text_exercise"


def test_lesson_record_returns_result(runner) -> None:  # type: ignore[no-untyped-def]
    _setup(runner)
    start = invoke_json(runner, ["lesson", "start", "--json", json.dumps({"candidate": lesson_candidate()})])
    record = json.dumps(record_payload(start["exercise_id"], modality="lesson"))
    result = invoke_json(runner, ["lesson", "record", "--json", record])
    assert result["answer_event"]["skill"] == "lesson"
    assert result["persisted_mistakes"] == 1
