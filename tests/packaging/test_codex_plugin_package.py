from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


def test_codex_plugin_manifest_removed() -> None:
    assert not (REPO_ROOT / (".codex" + "-plugin") / "plugin.json").exists()


def test_codex_marketplace_registration_removed() -> None:
    assert not (REPO_ROOT / ".agents" / "plugins" / "marketplace.json").exists()


def test_root_skills_available_for_codex() -> None:
    assert (REPO_ROOT / "skills/tutor-setup/SKILL.md").exists()
    assert (REPO_ROOT / "skills/tutor-judge/SKILL.md").exists()
