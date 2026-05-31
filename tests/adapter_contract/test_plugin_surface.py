from __future__ import annotations

from pathlib import Path


def test_skill_hub_surface_files_exist() -> None:
    for path in [
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
    ]:
        assert Path(path).exists(), path
