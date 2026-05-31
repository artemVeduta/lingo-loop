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
    for skill in (
        "tutor-setup",
        "tutor-vocab",
        "tutor-writing",
        "tutor-progress",
        "tutor-reading",
        "tutor-lesson",
        "tutor-judge",
    ):
        skill_dir = root / "skills" / skill
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text("# skill", encoding="utf-8")
    for script in (
        "skills/tutor-vocab/scripts/run.py",
        "skills/tutor-writing/scripts/run.py",
        "skills/tutor-progress/scripts/run.py",
    ):
        path = root / script
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("# script\n", encoding="utf-8")


def _make_runtime_payload(root: Path) -> None:
    for rel in (
        "migrations/001_initial.sql",
        "migrations/002_vocab_depth.sql",
        "migrations/003_progress_indexes.sql",
        "migrations/004_sessions_checkpoints.sql",
        "skills/tutor-setup/SKILL.md",
        "skills/tutor-vocab/SKILL.md",
        "skills/tutor-vocab/scripts/run.py",
        "skills/tutor-writing/SKILL.md",
        "skills/tutor-writing/scripts/run.py",
        "skills/tutor-progress/SKILL.md",
        "skills/tutor-progress/scripts/run.py",
        "skills/tutor-reading/SKILL.md",
        "skills/tutor-lesson/SKILL.md",
        "skills/tutor-judge/SKILL.md",
    ):
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("-- payload\n" if rel.endswith(".sql") else "# payload\n", encoding="utf-8")


def test_source_checkout_runtime_payload_checks_ok(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    _make_source_tree(repo)
    for rel in (
        "migrations/001_initial.sql",
        "migrations/002_vocab_depth.sql",
        "migrations/003_progress_indexes.sql",
        "migrations/004_sessions_checkpoints.sql",
    ):
        path = repo / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("-- sql\n", encoding="utf-8")
    monkeypatch.setenv("LANGUAGE_TUTOR_BUNDLED_ASSETS", str(repo))

    report = doctor(_paths(tmp_path), repo)
    statuses = _by_name(report)

    assert statuses["runtime_payload:skills/tutor-judge/SKILL.md"] == "ok"
    assert "manifest" not in statuses
    assert report.status == "ok"


def test_wheel_install_runtime_payloads_ok(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fake_repo = tmp_path / "site-packages-adjacent"
    fake_repo.mkdir()
    assets = tmp_path / "_assets"
    _make_runtime_payload(assets)
    monkeypatch.setenv("LANGUAGE_TUTOR_BUNDLED_ASSETS", str(assets))

    report = doctor(_paths(tmp_path), fake_repo)
    statuses = _by_name(report)

    assert statuses["runtime_payload:skills/tutor-judge/SKILL.md"] == "ok"
    assert "manifest" not in statuses
    assert "fail" not in statuses.values()
    assert report.status == "ok"


def test_doctor_fails_with_exact_missing_runtime_asset(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fake_repo = tmp_path / "site-packages-adjacent"
    fake_repo.mkdir()
    assets = tmp_path / "_assets"
    _make_runtime_payload(assets)
    (assets / "migrations" / "004_sessions_checkpoints.sql").unlink()
    monkeypatch.setenv("LANGUAGE_TUTOR_BUNDLED_ASSETS", str(assets))

    report = doctor(_paths(tmp_path), fake_repo)
    checks = {c.name: c for c in report.checks}

    assert checks["runtime_payload:migrations/004_sessions_checkpoints.sql"].status == "fail"
    assert "migrations/004_sessions_checkpoints.sql" in checks[
        "runtime_payload:migrations/004_sessions_checkpoints.sql"
    ].repair_hint
    assert report.status == "fail"


def test_status_fail_when_a_check_fails(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    fake_repo = tmp_path / "site-packages-adjacent"
    fake_repo.mkdir()
    assets = tmp_path / "_assets"
    assets.mkdir()
    monkeypatch.setenv("LANGUAGE_TUTOR_BUNDLED_ASSETS", str(assets))
    report = doctor(_paths(tmp_path), fake_repo)
    statuses = _by_name(report)
    assert statuses["runtime_payload:migrations/001_initial.sql"] == "fail"
    assert report.status == "fail"


def test_report_is_json_serialisable_with_status(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    _make_source_tree(repo)
    for rel in (
        "migrations/001_initial.sql",
        "migrations/002_vocab_depth.sql",
        "migrations/003_progress_indexes.sql",
        "migrations/004_sessions_checkpoints.sql",
    ):
        path = repo / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("-- sql\n", encoding="utf-8")
    monkeypatch.setenv("LANGUAGE_TUTOR_BUNDLED_ASSETS", str(repo))
    report = doctor(_paths(tmp_path), repo)
    data = json.loads(json.dumps(report.model_dump(mode="json")))
    assert data["status"] == "ok"
