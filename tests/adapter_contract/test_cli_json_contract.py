from __future__ import annotations

import json
from datetime import UTC, datetime

from language_tutor.dal.paths import resolve_paths
from language_tutor.dal.repositories import TutorRepository
from language_tutor.dal.sqlite_store import connect
from language_tutor.progress_rendering import render_progress_markdown
from language_tutor.schemas import (
    ProgressReport,
    TextModalityResult,
    ValidatedTextExercise,
    export_json_schemas,
)
from tests.conftest import invoke_json
from tests.fixtures.progress.phase4_scenarios import seed_mixed_history
from tests.fixtures.text_modalities.builders import (
    lesson_candidate,
    reading_candidate,
    record_payload,
    transcript_candidate,
)


def test_cli_error_envelope(runner) -> None:  # type: ignore[no-untyped-def]
    result = runner.invoke(
        __import__("language_tutor.cli").cli.main, ["setup", "write", "--json", "{bad"]
    )
    assert result.exit_code == 1
    assert '"error"' in result.output


def test_doctor_json(runner) -> None:  # type: ignore[no-untyped-def]
    data = invoke_json(runner, ["doctor", "--json"])
    assert "checks" in data


def test_boot_context_reports_safe_weak_tag_summary(runner) -> None:  # type: ignore[no-untyped-def]
    invoke_json(
        runner,
        [
            "setup",
            "write",
            "--json",
            '{"profile":{"native_language":"en","target_language":"uk"},"preferences":{}}',
        ],
    )
    conn = connect(resolve_paths().database_path)
    try:
        for session_id, day in (("s1", 20), ("s2", 21)):
            conn.execute(
                """
                INSERT INTO session_summaries(
                  id, session_id, summary_for_user, summary_for_next_boot,
                  weak_tags_json, next_focus, cost_snapshot_json, created_at
                ) VALUES (?, ?, 'u', 'b', '[]', 'focus', '{}', ?)
                """,
                (f"summary_{session_id}", session_id, datetime(2026, 5, day, tzinfo=UTC).isoformat()),
            )
            conn.execute(
                """
                INSERT INTO mistake_events(
                  id, session_id, skill, severity, tag, explanation, confidence, created_at
                ) VALUES (?, ?, 'writing', 'low', 'case', 'private prose', 'high', ?)
                """,
                (f"mistake_{session_id}", session_id, datetime(2026, 5, day, tzinfo=UTC).isoformat()),
            )
        conn.commit()
    finally:
        conn.close()

    context = invoke_json(runner, ["boot-context", "--json"])
    weak_section = next(section for section in context["sections"] if section["title"] == "Weak Patterns")  # type: ignore[index]
    assert len(weak_section["lines"]) == 1  # type: ignore[index]
    assert "case" in weak_section["lines"][0]  # type: ignore[index]
    assert "private prose" not in json.dumps(context)


def test_vocab_start_json_selection_reason_invariants(runner) -> None:  # type: ignore[no-untyped-def]
    invoke_json(
        runner,
        [
            "setup",
            "write",
            "--json",
            '{"profile":{"native_language":"en","target_language":"uk"},"preferences":{"session_length":2}}',
        ],
    )
    plan = invoke_json(runner, ["vocab", "start", "--json"])
    item_ids = {item["id"] for item in plan["items"]}  # type: ignore[index]
    reason_ids = {reason["item_id"] for reason in plan["selection_reasons"]}  # type: ignore[index]
    assert reason_ids == item_ids
    assert len(plan["active_weak_tags"]) <= 5  # type: ignore[arg-type]
    assert "learner_answer" not in json.dumps(plan)


def test_progress_schema_mirrors_export(tmp_path) -> None:  # type: ignore[no-untyped-def]
    export_json_schemas(tmp_path)
    assert (tmp_path / "progress_request.schema.json").exists()
    assert (tmp_path / "progress_report.schema.json").exists()
    assert (tmp_path / "progress_markdown_export.schema.json").exists()


def test_reading_json_round_trip_and_schema_mirrors(runner, tmp_path) -> None:  # type: ignore[no-untyped-def]
    invoke_json(
        runner,
        [
            "setup",
            "write",
            "--json",
            '{"profile":{"native_language":"en","target_language":"Ukrainian","level_target":"A2"}}',
        ],
    )
    exercise_json = invoke_json(
        runner,
        ["reading", "start", "--json", json.dumps({"mode": "comprehension", "candidate": reading_candidate()})],
    )
    exercise = ValidatedTextExercise.model_validate(exercise_json)
    assert (
        ValidatedTextExercise.model_validate_json(exercise.model_dump_json()).exercise_id
        == exercise.exercise_id
    )
    result_json = invoke_json(
        runner, ["reading", "record", "--json", json.dumps(record_payload(exercise.exercise_id))]
    )
    result = TextModalityResult.model_validate(result_json)
    assert TextModalityResult.model_validate_json(result.model_dump_json()).feedback.verdict == "partial"
    export_json_schemas(tmp_path)
    assert (tmp_path / "reading_exercise.schema.json").exists()
    assert (tmp_path / "reading_result.schema.json").exists()


def test_lesson_json_round_trip_and_schema_mirrors(runner, tmp_path) -> None:  # type: ignore[no-untyped-def]
    invoke_json(
        runner,
        [
            "setup",
            "write",
            "--json",
            '{"profile":{"native_language":"en","target_language":"Ukrainian","level_target":"A2"}}',
        ],
    )
    exercise_json = invoke_json(
        runner, ["lesson", "start", "--json", json.dumps({"candidate": lesson_candidate()})]
    )
    exercise = ValidatedTextExercise.model_validate(exercise_json)
    assert exercise.modality == "lesson"
    result_json = invoke_json(
        runner,
        ["lesson", "record", "--json", json.dumps(record_payload(exercise.exercise_id, modality="lesson"))],
    )
    result = TextModalityResult.model_validate(result_json)
    assert result.answer_event is not None and result.answer_event.skill == "lesson"
    export_json_schemas(tmp_path)
    assert (tmp_path / "lesson_exercise.schema.json").exists()
    assert (tmp_path / "lesson_result.schema.json").exists()


def test_transcript_json_round_trip_stores_reading_skill(runner, tmp_path) -> None:  # type: ignore[no-untyped-def]
    invoke_json(
        runner,
        [
            "setup",
            "write",
            "--json",
            '{"profile":{"native_language":"en","target_language":"Ukrainian","level_target":"A2"}}',
        ],
    )
    exercise_json = invoke_json(
        runner,
        ["reading", "start", "--json", json.dumps({"mode": "transcript", "candidate": transcript_candidate()})],
    )
    exercise = ValidatedTextExercise.model_validate(exercise_json)
    assert exercise.modality == "transcript"
    result_json = invoke_json(
        runner,
        ["reading", "record", "--json", json.dumps(record_payload(exercise.exercise_id, modality="transcript"))],
    )
    result = TextModalityResult.model_validate(result_json)
    assert result.modality == "transcript"
    assert result.answer_event is not None and result.answer_event.skill == "reading"
    export_json_schemas(tmp_path)
    assert (tmp_path / "transcript_drill.schema.json").exists()


def test_progress_json_round_trip_and_markdown_equivalence(runner) -> None:  # type: ignore[no-untyped-def]
    conn = connect(resolve_paths().database_path)
    try:
        seed_mixed_history(TutorRepository(conn), 4)
    finally:
        conn.close()
    payload = '{"window_size":4,"generated_at":"2026-05-21T12:00:00Z"}'
    report_json = invoke_json(runner, ["progress", "--json", payload])
    report = ProgressReport.model_validate(report_json)
    assert ProgressReport.model_validate_json(report.model_dump_json()).generated_at == report.generated_at
    markdown = render_progress_markdown(report).markdown
    assert report.tag_mastery[0].tag in markdown
    assert str(report.report_window.actual_session_count) in markdown
    assert "private answer" not in markdown
