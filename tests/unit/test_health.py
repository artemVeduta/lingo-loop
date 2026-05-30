from __future__ import annotations

import json
from pathlib import Path

import pytest

from language_tutor.dal.paths import TutorPaths
from language_tutor.health import doctor
from language_tutor.schemas import DoctorReport


def _paths(tmp_path: Path) -> TutorPaths:
    return TutorPaths(
        config_dir=tmp_path / "config",
        data_dir=tmp_path / "data",
        state_dir=tmp_path / "state",
    )


def _by_name(report: DoctorReport) -> dict[str, str]:
    return {c.name: c.status for c in report.checks}


def _make_source_tree(root: Path) -> None:
    """Materialise the plugin source layout doctor verifies in an editable checkout."""
    (root / ".claude-plugin").mkdir(parents=True)
    (root / ".claude-plugin" / "plugin.json").write_text("{}", encoding="utf-8")
    for skill in ("tutor-setup", "tutor-vocab", "tutor-writing", "tutor-progress"):
        skill_dir = root / "skills" / skill
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text("# skill", encoding="utf-8")
    (root / "agents").mkdir()
    (root / "agents" / "tutor-judge.md").write_text("# judge", encoding="utf-8")
    bin_dir = root / "bin"
    bin_dir.mkdir()
    cli = bin_dir / "tutor"
    cli.write_text("#!/usr/bin/env bash\n", encoding="utf-8")
    cli.chmod(0o755)


def test_source_checkout_all_plugin_checks_ok(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    _make_source_tree(repo)
    report = doctor(_paths(tmp_path), repo)
    statuses = _by_name(report)
    for name in (
        "manifest",
        "setup_skill",
        "vocab_skill",
        "writing_skill",
        "progress_skill",
        "judge_agent",
        "cli",
    ):
        assert statuses[name] == "ok", (name, statuses[name])
    assert report.status == "ok"


def test_wheel_install_manifest_ok_source_checks_na(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Simulate a wheel: repo_root has no plugin source tree, but the bundled
    # assets root (env-override seam) carries only the manifest.
    fake_repo = tmp_path / "site-packages-adjacent"
    fake_repo.mkdir()
    assets = tmp_path / "_assets"
    (assets / ".claude-plugin").mkdir(parents=True)
    (assets / ".claude-plugin" / "plugin.json").write_text("{}", encoding="utf-8")
    monkeypatch.setenv("LANGUAGE_TUTOR_BUNDLED_ASSETS", str(assets))

    report = doctor(_paths(tmp_path), fake_repo)
    statuses = _by_name(report)
    assert statuses["manifest"] == "ok"
    for name in (
        "setup_skill",
        "vocab_skill",
        "writing_skill",
        "progress_skill",
        "judge_agent",
        "cli",
    ):
        assert statuses[name] == "n/a", (name, statuses[name])
    # n/a is not a failure -> overall healthy.
    assert report.status == "ok"
    assert "fail" not in statuses.values()


def test_status_fail_when_a_check_fails(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    # Wheel layout but manifest missing from bundled assets -> manifest fail.
    fake_repo = tmp_path / "site-packages-adjacent"
    fake_repo.mkdir()
    assets = tmp_path / "_assets"
    assets.mkdir()
    monkeypatch.setenv("LANGUAGE_TUTOR_BUNDLED_ASSETS", str(assets))
    report = doctor(_paths(tmp_path), fake_repo)
    statuses = _by_name(report)
    assert statuses["manifest"] == "fail"
    assert report.status == "fail"


def test_report_is_json_serialisable_with_status(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    _make_source_tree(repo)
    report = doctor(_paths(tmp_path), repo)
    data = json.loads(json.dumps(report.model_dump(mode="json")))
    assert data["status"] == "ok"
