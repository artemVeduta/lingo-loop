from __future__ import annotations

import pytest

from language_tutor.dal.repositories import TutorRepository
from language_tutor.dal.sqlite_store import connect
from language_tutor.errors import TutorError
from language_tutor.reading import record_reading, start_reading
from language_tutor.schemas import LearnerProfile, TextModalityRecordInput
from tests.fixtures.text_modalities.builders import (
    feedback,
    reading_candidate,
    record_payload,
    transcript_candidate,
)

PROFILE = LearnerProfile(native_language="en", target_language="Ukrainian", level_target="A2")


def test_start_reading_validates_comprehension() -> None:
    exercise = start_reading({"mode": "comprehension", "candidate": reading_candidate()}, PROFILE)
    assert exercise.modality == "reading"
    assert exercise.mode == "comprehension"
    assert exercise.exercise_id.startswith("reading_")


def test_start_reading_rejects_missing_candidate() -> None:
    with pytest.raises(TutorError) as exc:
        start_reading({"mode": "comprehension"}, PROFILE)
    assert exc.value.code == "invalid_text_exercise"


def test_start_reading_forces_reading_modality() -> None:
    with pytest.raises(TutorError):
        start_reading(
            {"mode": "comprehension", "candidate": reading_candidate(modality="lesson")}, PROFILE
        )


def test_start_transcript_is_reading_submode() -> None:
    exercise = start_reading({"mode": "transcript", "candidate": transcript_candidate()}, PROFILE)
    assert exercise.modality == "transcript"
    assert exercise.mode == "transcript_reconstruction"
    assert exercise.exercise_id.startswith("transcript_")


def test_transcript_rejects_audio_claims() -> None:
    with pytest.raises(TutorError) as exc:
        start_reading(
            {
                "mode": "transcript",
                "candidate": transcript_candidate(instructions="Listen to the audio and transcribe."),
            },
            PROFILE,
        )
    assert exc.value.code == "invalid_text_exercise"


def test_transcript_records_as_reading_skill(tmp_path) -> None:  # type: ignore[no-untyped-def]
    conn = connect(tmp_path / "db.sqlite3")
    try:
        repo = TutorRepository(conn)
        record = TextModalityRecordInput.model_validate(
            record_payload("transcript_abc", modality="transcript")
        )
        result = record_reading(repo, record)
        conn.commit()
        assert result.modality == "transcript"
        assert result.answer_event is not None
        assert result.answer_event.skill == "reading"  # transcript stored as reading
    finally:
        conn.close()


def test_record_reading_persists_answer_and_safe_mistakes(tmp_path) -> None:  # type: ignore[no-untyped-def]
    conn = connect(tmp_path / "db.sqlite3")
    try:
        repo = TutorRepository(conn)
        record = TextModalityRecordInput.model_validate(record_payload("reading_abc"))
        result = record_reading(repo, record)
        conn.commit()
        assert result.modality == "reading"
        assert result.answer_event is not None
        assert result.answer_event.skill == "reading"
        assert result.persisted_mistakes == 1
        assert result.feedback.verdict == "partial"
    finally:
        conn.close()


def test_record_reading_empty_response_persists_no_mistakes(tmp_path) -> None:  # type: ignore[no-untyped-def]
    conn = connect(tmp_path / "db.sqlite3")
    try:
        repo = TutorRepository(conn)
        record = TextModalityRecordInput.model_validate(
            record_payload("reading_empty", response_status="empty", learner_response="")
        )
        result = record_reading(repo, record)
        conn.commit()
        assert result.response_status == "empty"
        assert result.persisted_mistakes == 0
        assert result.answer_event is not None
    finally:
        conn.close()


def test_record_reading_refused_persists_nothing(tmp_path) -> None:  # type: ignore[no-untyped-def]
    conn = connect(tmp_path / "db.sqlite3")
    try:
        repo = TutorRepository(conn)
        record = TextModalityRecordInput.model_validate(
            record_payload("reading_refused", response_status="refused")
        )
        result = record_reading(repo, record)
        conn.commit()
        assert result.answer_event is None
        assert result.persisted_mistakes == 0
        count = conn.execute("SELECT COUNT(*) AS c FROM answer_events").fetchone()
        assert int(count["c"]) == 0
    finally:
        conn.close()


def test_record_reading_rejects_over_budget_feedback(tmp_path) -> None:  # type: ignore[no-untyped-def]
    conn = connect(tmp_path / "db.sqlite3")
    try:
        repo = TutorRepository(conn)
        record = TextModalityRecordInput.model_validate(
            record_payload("reading_long", candidate_feedback=feedback(explanation="x" * 1000))
        )
        with pytest.raises(TutorError) as exc:
            record_reading(repo, record)
        assert exc.value.code == "text_feedback_too_long"
    finally:
        conn.close()
