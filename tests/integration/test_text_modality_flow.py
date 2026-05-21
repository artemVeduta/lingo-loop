from __future__ import annotations

import json

from tests.conftest import invoke_json
from tests.fixtures.text_modalities.builders import (
    feedback,
    lesson_candidate,
    reading_candidate,
    record_payload,
    transcript_candidate,
)

SETUP = (
    '{"profile":{"native_language":"en","target_language":"Ukrainian","level_target":"A2"}}'
)


def _setup(runner) -> None:  # type: ignore[no-untyped-def]
    invoke_json(runner, ["setup", "write", "--json", SETUP])


def _start_reading(runner) -> str:  # type: ignore[no-untyped-def]
    exercise = invoke_json(
        runner,
        ["reading", "start", "--json", json.dumps({"mode": "comprehension", "candidate": reading_candidate()})],
    )
    return str(exercise["exercise_id"])


def test_completed_reading_flow_persists_and_shows_in_progress(runner) -> None:  # type: ignore[no-untyped-def]
    _setup(runner)
    exercise_id = _start_reading(runner)
    result = invoke_json(runner, ["reading", "record", "--json", json.dumps(record_payload(exercise_id))])
    assert result["answer_event"]["skill"] == "reading"
    report = invoke_json(runner, ["progress", "--json", '{"window_size":10}'])
    # Reading mistakes feed mastery evidence (aggregate, no raw answers).
    assert "книга" not in json.dumps(report)


def test_invalid_generation_returns_error_envelope(runner) -> None:  # type: ignore[no-untyped-def]
    _setup(runner)
    payload = json.dumps(
        {"mode": "comprehension", "candidate": reading_candidate(instructions="Press play and listen to the audio.")}
    )
    result = runner.invoke(__import__("language_tutor.cli").cli.main, ["reading", "start", "--json", payload])
    assert result.exit_code == 1
    assert json.loads(result.output)["error"]["code"] == "invalid_text_exercise"


def test_empty_and_abandoned_record_no_mistakes(runner) -> None:  # type: ignore[no-untyped-def]
    _setup(runner)
    exercise_id = _start_reading(runner)
    for status in ("empty", "abandoned"):
        result = invoke_json(
            runner,
            [
                "reading",
                "record",
                "--json",
                json.dumps(
                    record_payload(
                        exercise_id,
                        response_status=status,
                        learner_response="",
                        idempotency_key=f"key-{status}",
                    )
                ),
            ],
        )
        assert result["response_status"] == status
        assert result["persisted_mistakes"] == 0


def test_completed_lesson_flow_persists_lesson_skill(runner) -> None:  # type: ignore[no-untyped-def]
    _setup(runner)
    exercise = invoke_json(runner, ["lesson", "start", "--json", json.dumps({"candidate": lesson_candidate()})])
    result = invoke_json(
        runner,
        ["lesson", "record", "--json", json.dumps(record_payload(exercise["exercise_id"], modality="lesson"))],
    )
    assert result["answer_event"]["skill"] == "lesson"
    assert result["modality"] == "lesson"


def test_lesson_invalid_generation_returns_error(runner) -> None:  # type: ignore[no-untyped-def]
    _setup(runner)
    payload = json.dumps({"candidate": lesson_candidate(target_language="Polish")})
    result = runner.invoke(__import__("language_tutor.cli").cli.main, ["lesson", "start", "--json", payload])
    assert result.exit_code == 1
    assert json.loads(result.output)["error"]["code"] == "invalid_text_exercise"


def test_lesson_abandoned_records_no_mistakes(runner) -> None:  # type: ignore[no-untyped-def]
    _setup(runner)
    exercise = invoke_json(runner, ["lesson", "start", "--json", json.dumps({"candidate": lesson_candidate()})])
    result = invoke_json(
        runner,
        [
            "lesson",
            "record",
            "--json",
            json.dumps(
                record_payload(
                    exercise["exercise_id"], modality="lesson", response_status="abandoned", learner_response=""
                )
            ),
        ],
    )
    assert result["response_status"] == "abandoned"
    assert result["persisted_mistakes"] == 0


def test_transcript_completed_and_empty_flow(runner) -> None:  # type: ignore[no-untyped-def]
    _setup(runner)
    exercise = invoke_json(
        runner, ["reading", "start", "--json", json.dumps({"mode": "transcript", "candidate": transcript_candidate()})]
    )
    assert exercise["modality"] == "transcript"
    completed = invoke_json(
        runner,
        ["reading", "record", "--json", json.dumps(record_payload(exercise["exercise_id"], modality="transcript"))],
    )
    assert completed["answer_event"]["skill"] == "reading"
    empty = invoke_json(
        runner,
        [
            "reading",
            "record",
            "--json",
            json.dumps(
                record_payload(
                    exercise["exercise_id"],
                    modality="transcript",
                    response_status="empty",
                    learner_response="",
                    idempotency_key="transcript-empty",
                )
            ),
        ],
    )
    assert empty["persisted_mistakes"] == 0


def test_transcript_no_audio_scope_rejected(runner) -> None:  # type: ignore[no-untyped-def]
    _setup(runner)
    payload = json.dumps(
        {"mode": "transcript", "candidate": transcript_candidate(content="Press play to hear the audio clip.")}
    )
    result = runner.invoke(__import__("language_tutor.cli").cli.main, ["reading", "start", "--json", payload])
    assert result.exit_code == 1
    assert json.loads(result.output)["error"]["code"] == "invalid_text_exercise"


def test_off_topic_and_mixed_language_record_safe_signals(runner) -> None:  # type: ignore[no-untyped-def]
    _setup(runner)
    exercise_id = _start_reading(runner)
    for status in ("off_topic", "mixed_language"):
        result = invoke_json(
            runner,
            [
                "reading",
                "record",
                "--json",
                json.dumps(
                    record_payload(
                        exercise_id,
                        response_status=status,
                        candidate_feedback=feedback(),
                        idempotency_key=f"key-{status}",
                    )
                ),
            ],
        )
        assert result["response_status"] == status
        # Safe spans (low severity, medium confidence) are persisted.
        assert result["persisted_mistakes"] == 1
