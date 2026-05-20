from __future__ import annotations

from datetime import UTC, datetime

from language_tutor.dal.paths import TutorPaths, ensure_dirs
from language_tutor.dal.yaml_store import (
    default_preferences,
    default_profile,
    dump_model,
    load_model,
)
from language_tutor.schemas import LearnerPreferences, LearnerProfile, SetupState, SetupWriteResult


def read_setup(paths: TutorPaths) -> SetupState:
    ensure_dirs(paths)
    profile = load_model(paths.profile_path, LearnerProfile, default_profile())
    preferences = load_model(
        paths.preferences_path, LearnerPreferences, default_preferences(profile.target_language)
    )
    return SetupState(
        profile=profile,
        preferences=preferences,
        profile_path=str(paths.profile_path),
        preferences_path=str(paths.preferences_path),
    )


def write_setup(
    paths: TutorPaths, profile: LearnerProfile, preferences: LearnerPreferences | None = None
) -> SetupWriteResult:
    ensure_dirs(paths)
    now = datetime.now(UTC).replace(microsecond=0)
    existing = read_setup(paths).profile
    created_at = existing.created_at if paths.profile_path.exists() else now
    final_profile = profile.model_copy(update={"created_at": created_at, "updated_at": now})
    final_preferences = preferences or default_preferences(final_profile.target_language)
    final_preferences = final_preferences.model_copy(update={"updated_at": now})
    dump_model(paths.profile_path, final_profile)
    dump_model(paths.preferences_path, final_preferences)
    return SetupWriteResult(
        profile_path=str(paths.profile_path), preferences_path=str(paths.preferences_path)
    )
