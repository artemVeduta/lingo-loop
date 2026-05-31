from __future__ import annotations

from pathlib import Path

from language_tutor.adapters import claude
from language_tutor.adapters.base import run_conformance
from language_tutor.boot_context import select_boot_trigger
from language_tutor.schemas import (
    BootTrigger,
    CapabilitySupport,
    Decision,
    LifecycleStart,
    TriggerType,
)

REPO_ROOT = Path(__file__).resolve().parents[2]


def test_claude_capability() -> None:
    profile = claude.capability_profile()
    assert profile.host == "claude"
    assert profile.text_support == CapabilitySupport.SUPPORTED.value
    assert profile.audio_support == "unsupported"


def test_claude_lifecycle_is_first_message() -> None:
    """spec 007 FR-009/FR-010: Claude shares the no-hook lifecycle."""
    profile = claude.capability_profile()
    assert profile.lifecycle_start == LifecycleStart.FIRST_MESSAGE.value
    assert profile.boot_context_trigger == BootTrigger.FIRST_TUTOR_MESSAGE.value
    trigger = select_boot_trigger(profile.boot_context_trigger)
    assert trigger.trigger_type == TriggerType.FIRST_MESSAGE.value
    assert trigger.command == "tutor session-start --json"


def test_claude_skill_hub_baseline_preserved() -> None:
    for rel in ("skills/tutor-setup/SKILL.md", "skills/tutor-judge/SKILL.md"):
        assert (REPO_ROOT / rel).exists()
    assert not (REPO_ROOT / (".claude" + "-plugin") / "plugin.json").exists()
    assert not (REPO_ROOT / "hooks").exists(), "hooks/ removed in spec 007"


def test_claude_conformance_passes() -> None:
    run = run_conformance(claude.capability_profile())
    assert run.decision == Decision.PASS.value
    assert run.skipped_flows == []
