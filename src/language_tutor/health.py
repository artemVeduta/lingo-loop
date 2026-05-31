from __future__ import annotations

import os
import sys
from pathlib import Path

from language_tutor.dal.migrations import apply_migrations
from language_tutor.dal.paths import TutorPaths, ensure_dirs
from language_tutor.dal.sqlite_store import connect
from language_tutor.dal.yaml_store import default_preferences, default_profile, load_model
from language_tutor.errors import TutorError
from language_tutor.package_assets import REQUIRED_RUNTIME_PAYLOADS, package_asset_path
from language_tutor.schemas import DoctorCheck, DoctorReport, LearnerPreferences, LearnerProfile


def doctor(paths: TutorPaths, repo_root: Path) -> DoctorReport:
    del repo_root
    ensure_dirs(paths)
    checks: list[DoctorCheck] = []
    checks.append(
        DoctorCheck(
            name="python_runtime",
            status="ok" if sys.version_info >= (3, 12) else "fail",
            repair_hint="Use Python 3.12+.",
        )
    )
    for rel in REQUIRED_RUNTIME_PAYLOADS:
        path = package_asset_path(rel)
        checks.append(
            DoctorCheck(
                name=f"runtime_payload:{rel}",
                status="ok" if path.exists() else "fail",
                repair_hint=f"Reinstall lingo-loop; packaged runtime payload missing: {rel}.",
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
    except TutorError as exc:
        checks.append(
            DoctorCheck(
                name="sqlite_migrations",
                status="fail",
                repair_hint=exc.repair_hint,
            )
        )
    except Exception:
        checks.append(
            DoctorCheck(
                name="sqlite_migrations",
                status="fail",
                repair_hint="Repair SQLite file or migration records.",
            )
        )
    overall = "fail" if any(check.status == "fail" for check in checks) else "ok"
    return DoctorReport(checks=checks, status=overall)
