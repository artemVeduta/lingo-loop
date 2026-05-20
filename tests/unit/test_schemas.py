from __future__ import annotations

import json
from pathlib import Path

from language_tutor.schemas import FeedbackEnvelope, LearnerProfile, export_json_schemas


def test_profile_requires_languages() -> None:
    profile = LearnerProfile(native_language="en", target_language="uk")
    assert profile.level_target == "A1"


def test_json_schema_export(tmp_path: Path) -> None:
    export_json_schemas(tmp_path)
    schema = json.loads((tmp_path / "feedback_envelope.schema.json").read_text())
    assert schema["title"] == FeedbackEnvelope.__name__
