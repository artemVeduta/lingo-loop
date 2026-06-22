from __future__ import annotations

import json
import re
from datetime import UTC, datetime
from pathlib import Path

import pytest

from language_tutor.schemas import (
    BootContext,
    BootResult,
    BootSection,
    Checkpoint,
    CheckpointModality,
    CheckpointStepKind,
    HostId,
    LearnerPreferences,
    LearnerProfile,
    PriorSessionEntry,
    SafeStepState,
    Session,
    SessionLabel,
    SessionStatus,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
SCHEMA_DIR = REPO_ROOT / "schemas"


def _load_schema(filename: str) -> dict[str, object]:
    return json.loads((SCHEMA_DIR / filename).read_text(encoding="utf-8"))


def _profile() -> LearnerProfile:
    return LearnerProfile(native_language="en", target_language="uk")


def _preferences() -> LearnerPreferences:
    return LearnerPreferences()


def _now() -> datetime:
    return datetime(2026, 5, 22, 12, 0, 0, tzinfo=UTC)


def test_session_schema_mirror_has_required_fields() -> None:
    schema = _load_schema("session.schema.json")
    required = set(schema["required"])  # type: ignore[arg-type]
    assert required == {"id", "host", "status", "started_at", "last_seen_at"}
    props = schema["properties"]  # type: ignore[index]
    defs = schema["$defs"]  # type: ignore[index]
    assert props["status"]["$ref"] == "#/$defs/SessionStatus"  # type: ignore[index]
    assert props["host"]["$ref"] == "#/$defs/HostId"  # type: ignore[index]
    assert defs["SessionStatus"]["enum"] == ["open", "closed"]  # type: ignore[index]
    assert set(defs["HostId"]["enum"]) == {"claude", "codex", "openclaw", "hermes"}  # type: ignore[index]


def test_session_open_validates_against_pydantic_and_mirror() -> None:
    session = Session(
        id="sess_abc123",
        host=HostId.CLAUDE,
        host_conversation_id=None,
        status=SessionStatus.OPEN,
        started_at=_now(),
        last_seen_at=_now(),
        closed_at=None,
    )
    dumped = session.model_dump(mode="json")
    schema = _load_schema("session.schema.json")
    for field in schema["required"]:  # type: ignore[union-attr]
        assert field in dumped
    assert re.match(r"^sess_[A-Za-z0-9]+$", dumped["id"])
    assert dumped["status"] == "open"
    assert dumped["closed_at"] is None


def test_session_closed_requires_closed_at() -> None:
    with pytest.raises(ValueError):
        Session(
            id="sess_abc",
            host=HostId.CLAUDE,
            status=SessionStatus.CLOSED,
            started_at=_now(),
            last_seen_at=_now(),
            closed_at=None,
        )


def test_session_open_rejects_closed_at() -> None:
    with pytest.raises(ValueError):
        Session(
            id="sess_abc",
            host=HostId.CLAUDE,
            status=SessionStatus.OPEN,
            started_at=_now(),
            last_seen_at=_now(),
            closed_at=_now(),
        )


def test_checkpoint_validates_against_pydantic_and_mirror() -> None:
    checkpoint = Checkpoint(
        id="ckpt_xyz",
        session_id="sess_abc",
        modality=CheckpointModality.LESSON,
        step_kind=CheckpointStepKind.PROMPT_SHOWN,
        prompt_ref="lesson_42",
        state=SafeStepState(prompt_ref="lesson_42", step_index=0, total_steps=4),
        summary="Presented step 1 of 4",
        created_at=_now(),
    )
    dumped = checkpoint.model_dump(mode="json")
    schema = _load_schema("checkpoint.schema.json")
    for field in schema["required"]:  # type: ignore[union-attr]
        assert field in dumped
    assert dumped["modality"] == "lesson"
    assert dumped["step_kind"] == "prompt_shown"


def test_checkpoint_summary_length_capped() -> None:
    with pytest.raises(ValueError):
        Checkpoint(
            id="ckpt_xyz",
            session_id="sess_abc",
            modality=CheckpointModality.LESSON,
            step_kind=CheckpointStepKind.PROMPT_SHOWN,
            state=SafeStepState(),
            summary="x" * 281,
            created_at=_now(),
        )


def test_safe_step_state_forbids_extra_fields() -> None:
    with pytest.raises(ValueError):
        SafeStepState.model_validate({"secret_token": "leak"})


def test_safe_step_state_labels_capped() -> None:
    with pytest.raises(ValueError):
        SafeStepState(labels=[f"l{i}" for i in range(17)])


def test_boot_result_validates_against_mirror() -> None:
    context = BootContext(
        profile=_profile(),
        preferences=_preferences(),
        sections=[BootSection(title="Profile", lines=["en -> uk"])],
        generated_at=_now(),
        prior_sessions=[
            PriorSessionEntry(
                session_id="sess_prev",
                label=SessionLabel.STALE,
                last_seen_at=_now(),
                summary="Reviewed cases",
            )
        ],
    )
    result = BootResult(session_id="sess_new", context=context)
    dumped = result.model_dump(mode="json")
    schema = _load_schema("boot_result.schema.json")
    for field in schema["required"]:  # type: ignore[union-attr]
        assert field in dumped
    assert re.match(r"^sess_[A-Za-z0-9]+$", dumped["session_id"])
    prior = dumped["context"]["prior_sessions"]
    assert len(prior) == 1
    assert prior[0]["label"] == "stale"


def test_prior_session_label_enum_matches_mirror() -> None:
    schema = _load_schema("boot_result.schema.json")
    context_schema = schema["$defs"]["BootContext"]  # type: ignore[index]
    items_schema = context_schema["properties"]["prior_sessions"]["items"]  # type: ignore[index]
    assert items_schema["$ref"] == "#/$defs/PriorSessionEntry"  # type: ignore[index]
    prior_session = schema["$defs"]["PriorSessionEntry"]  # type: ignore[index]
    label_ref = prior_session["properties"]["label"]["$ref"]  # type: ignore[index]
    assert label_ref == "#/$defs/SessionLabel"
    assert set(schema["$defs"]["SessionLabel"]["enum"]) == {  # type: ignore[index]
        label.value for label in SessionLabel
    }
