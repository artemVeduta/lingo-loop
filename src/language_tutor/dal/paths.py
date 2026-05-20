from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from platformdirs import user_config_dir, user_data_dir, user_state_dir

APP_NAME = "language-tutor"


@dataclass(frozen=True)
class TutorPaths:
    config_dir: Path
    data_dir: Path
    state_dir: Path

    @property
    def profile_path(self) -> Path:
        return self.config_dir / "profile.yaml"

    @property
    def preferences_path(self) -> Path:
        return self.config_dir / "preferences.yaml"

    @property
    def database_path(self) -> Path:
        return self.state_dir / "history.sqlite3"


def resolve_paths(base_dir: Path | None = None) -> TutorPaths:
    override = base_dir or (
        Path(os.environ["LANGUAGE_TUTOR_HOME"]) if "LANGUAGE_TUTOR_HOME" in os.environ else None
    )
    if override is not None:
        root = override.expanduser().resolve()
        return TutorPaths(root / "config", root / "data", root / "state")
    return TutorPaths(
        Path(user_config_dir(APP_NAME)),
        Path(user_data_dir(APP_NAME)),
        Path(user_state_dir(APP_NAME)),
    )


def ensure_dirs(paths: TutorPaths) -> None:
    paths.config_dir.mkdir(parents=True, exist_ok=True)
    paths.data_dir.mkdir(parents=True, exist_ok=True)
    paths.state_dir.mkdir(parents=True, exist_ok=True)
