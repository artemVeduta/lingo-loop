from __future__ import annotations

from pathlib import Path

from language_tutor.dal.paths import ensure_dirs, resolve_paths


def test_override_paths_are_local(tmp_path: Path) -> None:
    paths = resolve_paths(tmp_path)
    ensure_dirs(paths)
    assert paths.profile_path == tmp_path / "config" / "profile.yaml"
    assert paths.database_path == tmp_path / "state" / "history.sqlite3"
    assert paths.database_path.parent.exists()
