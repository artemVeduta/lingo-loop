from __future__ import annotations

import os
import sys
from pathlib import Path

from language_tutor.adapters.claude import plugin_root_components
from language_tutor.dal.migrations import apply_migrations
from language_tutor.dal.paths import TutorPaths, ensure_dirs
from language_tutor.dal.sqlite_store import connect
from language_tutor.dal.yaml_store import default_preferences, default_profile, load_model
from language_tutor.installer.assets import bundled_assets_root
from language_tutor.schemas import DoctorCheck, DoctorReport, LearnerPreferences, LearnerProfile

_MANIFEST_COMPONENT = "manifest"


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
    components = plugin_root_components()
    # The manifest is the only plugin asset shipped in the wheel and installed by
    # ``tutor init``; resolve it via the bundled-assets resolver so the check is
    # honest on both editable and PyPI/wheel installs.
    manifest_rel = components[_MANIFEST_COMPONENT]
    manifest_path = bundled_assets_root() / manifest_rel
    checks.append(
        DoctorCheck(
            name=_MANIFEST_COMPONENT,
            status="ok" if manifest_path.exists() else "fail",
            repair_hint=f"Restore {manifest_rel}.",
        )
    )
    # Skills/agents/CLI live in the source tree only — they are neither bundled
    # in the wheel nor installed for any host. Verify them in an editable
    # checkout; report ``n/a`` on wheel installs where ``repo_root`` has no tree.
    is_source_checkout = (repo_root / manifest_rel).exists()
    for name, rel in components.items():
        if name == _MANIFEST_COMPONENT:
            continue
        if not is_source_checkout:
            checks.append(
                DoctorCheck(
                    name=name,
                    status="n/a",
                    repair_hint="Source-only check; not applicable to wheel installs.",
                )
            )
            continue
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
    overall = "fail" if any(check.status == "fail" for check in checks) else "ok"
    return DoctorReport(checks=checks, status=overall)
