from __future__ import annotations

import os
import sys
from pathlib import Path

from language_tutor.adapters.claude import plugin_root_components
from language_tutor.dal.migrations import apply_migrations
from language_tutor.dal.paths import TutorPaths, ensure_dirs
from language_tutor.dal.sqlite_store import connect
from language_tutor.dal.yaml_store import default_preferences, default_profile, load_model
from language_tutor.schemas import DoctorCheck, DoctorReport, LearnerPreferences, LearnerProfile


def doctor(paths: TutorPaths, repo_root: Path) -> DoctorReport:
    ensure_dirs(paths)
    checks: list[DoctorCheck] = []
    checks.append(
        DoctorCheck(
            name="python_runtime",
            status="ok" if sys.version_info >= (3, 12) else "fail",
            repair_hint="Use Python 3.12+.",
        )
    )
    for name, rel in plugin_root_components().items():
        path = repo_root / rel
        executable_ok = name != "cli" or os.access(path, os.X_OK)
        checks.append(
            DoctorCheck(
                name=name,
                status="ok" if path.exists() and executable_ok else "fail",
                repair_hint=f"Restore {rel}.",
            )
        )
    for name, path in {
        "config_dir": paths.config_dir,
        "data_dir": paths.data_dir,
        "state_dir": paths.state_dir,
    }.items():
        checks.append(
            DoctorCheck(
                name=name,
                status="ok" if os.access(path, os.R_OK | os.W_OK) else "fail",
                repair_hint=f"Fix permissions for {path}.",
            )
        )
    try:
        load_model(paths.profile_path, LearnerProfile, default_profile())
        load_model(paths.preferences_path, LearnerPreferences, default_preferences())
        checks.append(DoctorCheck(name="yaml_schema", status="ok"))
    except Exception:
        checks.append(
            DoctorCheck(
                name="yaml_schema", status="fail", repair_hint="Fix profile/preferences YAML."
            )
        )
    try:
        conn = connect(paths.database_path)
        apply_migrations(conn)
        conn.close()
        checks.append(DoctorCheck(name="sqlite_migrations", status="ok"))
    except Exception:
        checks.append(
            DoctorCheck(
                name="sqlite_migrations",
                status="fail",
                repair_hint="Repair SQLite file or migration records.",
            )
        )
    return DoctorReport(checks=checks)
