"""Runtime payload resolution for source and wheel installs."""

from __future__ import annotations

import os
from importlib import resources
from pathlib import Path

REQUIRED_MIGRATION_FILES: tuple[str, ...] = (
    "migrations/001_initial.sql",
    "migrations/002_vocab_depth.sql",
    "migrations/003_progress_indexes.sql",
    "migrations/004_sessions_checkpoints.sql",
)

REQUIRED_SKILL_PAYLOAD_FILES: tuple[str, ...] = (
    "skills/tutor-setup/SKILL.md",
    "skills/tutor-vocab/SKILL.md",
    "skills/tutor-vocab/scripts/run.py",
    "skills/tutor-writing/SKILL.md",
    "skills/tutor-writing/scripts/run.py",
    "skills/tutor-progress/SKILL.md",
    "skills/tutor-progress/scripts/run.py",
    "skills/tutor-reading/SKILL.md",
    "skills/tutor-lesson/SKILL.md",
    "agents/tutor-judge.md",
    "bin/tutor",
)

REQUIRED_RUNTIME_PAYLOADS: tuple[str, ...] = (
    *REQUIRED_MIGRATION_FILES,
    *REQUIRED_SKILL_PAYLOAD_FILES,
)


def _override_root() -> Path | None:
    override = os.environ.get("LANGUAGE_TUTOR_BUNDLED_ASSETS")
    if override:
        return Path(override).expanduser().resolve()
    return None


def _source_root_candidate() -> Path:
    return Path(__file__).resolve().parents[2]


def _wheel_root_candidate() -> Path | None:
    try:
        return Path(str(resources.files("language_tutor") / "_assets"))
    except (ModuleNotFoundError, AttributeError):
        return None


def package_assets_root() -> Path:
    """Return the root containing package runtime payloads.

    If neither candidate has the first migration sentinel, return the source
    candidate so callers can report every missing required payload by its
    repository-relative name.
    """

    override = _override_root()
    if override is not None:
        return override

    source_root = _source_root_candidate()
    if (source_root / "migrations" / "001_initial.sql").exists():
        return source_root

    wheel_root = _wheel_root_candidate()
    if wheel_root is not None and (wheel_root / "migrations" / "001_initial.sql").exists():
        return wheel_root

    return source_root


def package_asset_path(relative_path: str) -> Path:
    return package_assets_root() / relative_path


def missing_package_assets(
    relative_paths: tuple[str, ...] = REQUIRED_RUNTIME_PAYLOADS,
) -> tuple[str, ...]:
    root = package_assets_root()
    return tuple(rel for rel in relative_paths if not (root / rel).exists())
