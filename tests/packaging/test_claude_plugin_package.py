from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

REQUIRED_SKILLS = (
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
)


def test_claude_personal_skill_hub_components_present() -> None:
    for rel in REQUIRED_SKILLS:
        assert (REPO_ROOT / rel).exists(), rel


def test_claude_plugin_manifest_removed() -> None:
    assert not (REPO_ROOT / (".claude" + "-plugin") / "plugin.json").exists()


def test_claude_package_has_no_hook_directory() -> None:
    assert not (REPO_ROOT / "hooks").exists()
