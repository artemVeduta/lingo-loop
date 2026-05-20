from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast

from pydantic import BaseModel, ValidationError
from ruamel.yaml import YAML

from language_tutor.errors import TutorError
from language_tutor.schemas import LearnerPreferences, LearnerProfile

yaml = YAML()
yaml.default_flow_style = False


def _now() -> datetime:
    return datetime.now(UTC).replace(microsecond=0)


def load_model[T: BaseModel](path: Path, model: type[T], default: T) -> T:
    if not path.exists():
        return default
    try:
        raw = cast(
            dict[str, Any],
            yaml.load(path.read_text(encoding="utf-8")) or {},  # type: ignore[reportUnknownMemberType]
        )
        return model.model_validate(raw)
    except (ValidationError, OSError) as exc:
        raise TutorError(
            "invalid_yaml", f"Invalid YAML at {path}", "Fix the YAML fields or rerun setup write."
        ) from exc


def dump_model(path: Path, model: BaseModel) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    data: dict[str, Any] = model.model_dump(mode="json")
    yaml.dump(cast(Any, data), path)  # type: ignore[reportUnknownMemberType]


def default_profile() -> LearnerProfile:
    return LearnerProfile(
        native_language="en",
        target_language="uk",
        level_target="A1",
        created_at=_now(),
        updated_at=_now(),
    )


def default_preferences(target_language: str = "uk") -> LearnerPreferences:
    transliteration = target_language.lower() not in {"uk", "ru", "bg", "sr"}
    return LearnerPreferences(transliteration_tolerance=transliteration, updated_at=_now())
