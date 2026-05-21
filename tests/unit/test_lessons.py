from __future__ import annotations

import pytest

from language_tutor.dal.repositories import TutorRepository
from language_tutor.dal.sqlite_store import connect
from language_tutor.errors import TutorError
from language_tutor.lessons import record_lesson, start_lesson
from language_tutor.schemas import LearnerProfile, TextModalityRecordInput
from tests.fixtures.text_modalities.builders import lesson_candidate, record_payload

PROFILE = LearnerProfile(native_language="en", target_language="Ukrainian", level_target="A2")


def test_start_lesson_validates_single_topic() -> None:
    exercise = start_lesson({"candidate": lesson_candidate()}, PROFILE)
    assert exercise.modality == "lesson"
    assert exercise.mode == "lesson"
    assert exercise.focus == "verbs_of_motion"
    assert exercise.exercise_id.startswith("lesson_")


def test_start_lesson_requires_candidate() -> None:
    with pytest.raises(TutorError) as exc:
        start_lesson({}, PROFILE)
    assert exc.value.code == "invalid_text_exercise"


def test_start_lesson_forces_lesson_modality() -> None:
    with pytest.raises(TutorError):
        start_lesson({"candidate": lesson_candidate(modality="reading")}, PROFILE)


def test_record_lesson_persists_with_lesson_skill(tmp_path) -> None:  # type: ignore[no-untyped-def]
    conn = connect(tmp_path / "db.sqlite3")
    try:
        repo = TutorRepository(conn)
        record = TextModalityRecordInput.model_validate(
            record_payload("lesson_abc", modality="lesson")
        )
        result = record_lesson(repo, record)
        conn.commit()
        assert result.modality == "lesson"
        assert result.answer_event is not None
        assert result.answer_event.skill == "lesson"
        assert result.persisted_mistakes == 1
    finally:
        conn.close()
