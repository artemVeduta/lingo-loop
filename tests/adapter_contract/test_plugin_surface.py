from __future__ import annotations

import json
from pathlib import Path

INVENTORY = Path("specs/005-text-modalities/skill-inventory.md")
PRESSURE = Path("tests/fixtures/text_modalities/skill_pressure.json")


def test_plugin_surface_files_exist() -> None:
    for path in [
        ".claude-plugin/plugin.json",
        "skills/tutor-setup/SKILL.md",
        "skills/tutor-vocab/SKILL.md",
        "skills/tutor-writing/SKILL.md",
        "skills/tutor-progress/SKILL.md",
        "skills/tutor-reading/SKILL.md",
        "skills/tutor-lesson/SKILL.md",
        "hooks/hooks.json",
        "agents/tutor-judge.md",
        "bin/tutor",
    ]:
        assert Path(path).exists(), path


def test_inventory_covers_every_skill_md_exactly_once() -> None:
    text = INVENTORY.read_text(encoding="utf-8")
    skill_files = sorted(
        str(path) for root in ("skills", ".agents/skills") for path in Path(root).rglob("SKILL.md")
    )
    assert skill_files, "expected at least one SKILL.md"
    for path in skill_files:
        assert text.count(f"`{path}`") == 1, f"{path} must appear exactly once in inventory"


def test_inventory_has_required_columns() -> None:
    text = INVENTORY.read_text(encoding="utf-8")
    for column in (
        "Trigger scope",
        "Pedagogy ownership",
        "Decision",
        "CLI/contract",
        "Progressive disclosure",
    ):
        assert column in text, column


def test_skill_pressure_baseline_has_existing_skill_boundaries() -> None:
    data = json.loads(PRESSURE.read_text(encoding="utf-8"))
    expected = {scenario["expected_skill"] for scenario in data["scenarios"]}
    assert {"tutor-vocab", "tutor-writing", "tutor-progress", "tutor-setup"} <= expected
    for scenario in data["scenarios"]:
        assert scenario["id"]
        assert scenario["prompt"]
        assert isinstance(scenario["must_not_trigger"], list)
