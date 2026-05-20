from __future__ import annotations

from pathlib import Path


def test_plugin_surface_files_exist() -> None:
    for path in [
        ".claude-plugin/plugin.json",
        "skills/tutor-setup/SKILL.md",
        "skills/tutor-vocab/SKILL.md",
        "skills/tutor-writing/SKILL.md",
        "skills/tutor-progress/SKILL.md",
        "hooks/hooks.json",
        "agents/tutor-judge.md",
        "bin/tutor",
    ]:
        assert Path(path).exists()
