from __future__ import annotations

from datetime import UTC, datetime

from language_tutor.dal.repositories import TutorRepository
from language_tutor.schemas import BootContext, BootSection, LearnerPreferences, LearnerProfile


def build_boot_context(
    repo: TutorRepository, profile: LearnerProfile, preferences: LearnerPreferences
) -> BootContext:
    now = datetime.now(UTC).replace(microsecond=0)
    due = repo.due_count(now)
    weak = repo.weak_tags()
    latest = repo.latest_summary()
    sections = [
        BootSection(
            title="Profile",
            lines=[
                f"{profile.native_language} -> {profile.target_language}",
                f"Level target: {profile.level_target}",
            ],
        ),
        BootSection(
            title="Session",
            lines=[
                f"Length: {preferences.session_length}",
                f"Review intensity: {preferences.review_intensity}",
            ],
        ),
        BootSection(title="Due Review", lines=[f"Due items: {due}"]),
        BootSection(title="Weak Patterns", lines=weak or ["No weak patterns yet."]),
        BootSection(
            title="Latest Recap",
            lines=[
                latest or "First session guidance: set up profile, then try vocabulary or writing."
            ],
        ),
        BootSection(
            title="Local Status", lines=["Profile/preferences: available", "History: local SQLite"]
        ),
    ]
    return BootContext(
        profile=profile, preferences=preferences, sections=sections, generated_at=now
    )


def render_boot_context(context: BootContext) -> str:
    lines: list[str] = []
    for section in context.sections[:8]:
        lines.append(f"## {section.title}")
        lines.extend(f"- {line}" for line in section.lines)
    rendered = "\n".join(lines)
    if len(rendered) <= context.max_rendered_chars:
        return rendered
    return rendered[: context.max_rendered_chars - 20].rstrip() + "\n- truncated"
