from __future__ import annotations

from pathlib import Path

import language_tutor.package_assets as package_assets
from language_tutor.package_assets import (
    REQUIRED_RUNTIME_PAYLOADS,
    missing_package_assets,
    package_asset_path,
    package_assets_root,
)


def test_package_assets_root_prefers_explicit_override(
    tmp_path: Path, monkeypatch
) -> None:  # type: ignore[no-untyped-def]
    root = tmp_path / "payload"
    root.mkdir()
    monkeypatch.setenv("LANGUAGE_TUTOR_BUNDLED_ASSETS", str(root))

    assert package_assets_root() == root.resolve()
    assert package_asset_path("migrations/001_initial.sql") == root.resolve() / "migrations/001_initial.sql"


def test_missing_package_assets_reports_exact_relative_names(
    tmp_path: Path, monkeypatch
) -> None:  # type: ignore[no-untyped-def]
    root = tmp_path / "payload"
    (root / "migrations").mkdir(parents=True)
    (root / "migrations" / "001_initial.sql").write_text("-- sql", encoding="utf-8")
    monkeypatch.setenv("LANGUAGE_TUTOR_BUNDLED_ASSETS", str(root))

    missing = missing_package_assets(
        (
            "migrations/001_initial.sql",
            "migrations/002_vocab_depth.sql",
            "skills/tutor-vocab/SKILL.md",
        )
    )

    assert missing == ("migrations/002_vocab_depth.sql", "skills/tutor-vocab/SKILL.md")


def test_package_assets_root_prefers_source_payload(
    tmp_path: Path, monkeypatch
) -> None:  # type: ignore[no-untyped-def]
    source_root = tmp_path / "repo"
    wheel_root = tmp_path / "wheel"
    (source_root / "migrations").mkdir(parents=True)
    (wheel_root / "migrations").mkdir(parents=True)
    (source_root / "migrations" / "001_initial.sql").write_text("-- sql", encoding="utf-8")
    (wheel_root / "migrations" / "001_initial.sql").write_text("-- sql", encoding="utf-8")
    monkeypatch.setattr(package_assets, "_source_root_candidate", lambda: source_root)
    monkeypatch.setattr(package_assets, "_wheel_root_candidate", lambda: wheel_root)

    assert package_assets_root() == source_root


def test_package_assets_root_falls_back_to_wheel_payload(
    tmp_path: Path, monkeypatch
) -> None:  # type: ignore[no-untyped-def]
    source_root = tmp_path / "repo"
    wheel_root = tmp_path / "wheel"
    source_root.mkdir()
    (wheel_root / "migrations").mkdir(parents=True)
    (wheel_root / "migrations" / "001_initial.sql").write_text("-- sql", encoding="utf-8")
    monkeypatch.setattr(package_assets, "_source_root_candidate", lambda: source_root)
    monkeypatch.setattr(package_assets, "_wheel_root_candidate", lambda: wheel_root)

    assert package_assets_root() == wheel_root


def test_required_runtime_payloads_cover_migrations_and_skill_helpers() -> None:
    assert "migrations/001_initial.sql" in REQUIRED_RUNTIME_PAYLOADS
    assert "migrations/004_sessions_checkpoints.sql" in REQUIRED_RUNTIME_PAYLOADS
    assert "skills/tutor-setup/SKILL.md" in REQUIRED_RUNTIME_PAYLOADS
    assert "skills/tutor-vocab/scripts/run.py" in REQUIRED_RUNTIME_PAYLOADS
    assert "skills/tutor-writing/scripts/run.py" in REQUIRED_RUNTIME_PAYLOADS
    assert "agents/tutor-judge.md" in REQUIRED_RUNTIME_PAYLOADS
    assert "bin/tutor" in REQUIRED_RUNTIME_PAYLOADS
