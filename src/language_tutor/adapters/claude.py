from __future__ import annotations


def normalize_hook_payload(payload: dict[str, object]) -> dict[str, object]:
    return dict(payload)


def plugin_root_components() -> dict[str, str]:
    return {
        "manifest": ".claude-plugin/plugin.json",
        "hooks": "hooks/hooks.json",
        "setup_skill": "skills/tutor-setup/SKILL.md",
        "vocab_skill": "skills/tutor-vocab/SKILL.md",
        "writing_skill": "skills/tutor-writing/SKILL.md",
        "progress_skill": "skills/tutor-progress/SKILL.md",
        "judge_agent": "agents/tutor-judge.md",
        "cli": "bin/tutor",
    }
