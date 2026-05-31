from __future__ import annotations

from language_tutor.adapters.registry import capability_profile_for
from language_tutor.schemas import AdapterCapabilityProfile, HostId


def capability_profile() -> AdapterCapabilityProfile:
    """Claude capability profile. No-hook lifecycle; skills live in the personal hub."""
    return capability_profile_for(HostId.CLAUDE.value)


def skill_hub_components() -> dict[str, str]:
    return {
        "setup_skill": "skills/tutor-setup/SKILL.md",
        "vocab_skill": "skills/tutor-vocab/SKILL.md",
        "writing_skill": "skills/tutor-writing/SKILL.md",
        "reading_skill": "skills/tutor-reading/SKILL.md",
        "lesson_skill": "skills/tutor-lesson/SKILL.md",
        "progress_skill": "skills/tutor-progress/SKILL.md",
        "judge_skill": "skills/tutor-judge/SKILL.md",
    }
