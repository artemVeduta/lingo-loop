from __future__ import annotations

from pathlib import Path

import pytest

from language_tutor.installer.assets import bundled_assets_root_for
from language_tutor.installer.protocol import InstallerContext
from language_tutor.installer.providers.base import SKILL_FILES, ManagedArea
from language_tutor.installer.providers.claude import ClaudeInstaller
from language_tutor.installer.providers.codex import CodexInstaller
from language_tutor.installer.providers.hermes import HermesInstaller
from language_tutor.installer.providers.openclaw import OpenClawInstaller
from language_tutor.installer.seams import FakeCommandRunner, FakeFilesystem
from language_tutor.installer.service import build_plan, run_init
from language_tutor.schemas import (
    HostId,
    InitRequest,
    ProviderActionKind,
    ProviderState,
)

HOME = Path("/fake/home")

INSTALLERS = (
    ClaudeInstaller,
    CodexInstaller,
    HermesInstaller,
    OpenClawInstaller,
)

ROOTS = {
    HostId.CLAUDE: ".claude",
    HostId.CODEX: ".codex",
    HostId.HERMES: ".hermes",
    HostId.OPENCLAW: ".openclaw",
}


def _ctx(files: dict[Path, str] | None = None) -> InstallerContext:
    fs = FakeFilesystem(home=HOME, files=files)
    for root in ROOTS.values():
        fs.mkdir(HOME / root)
    return InstallerContext(
        fs=fs,
        runner=FakeCommandRunner(
            available={host.value: f"/usr/bin/{host.value}" for host in HostId}
        ),
        bundled_assets_root=bundled_assets_root_for("skills").parent,
    )


def _skill_area(areas: tuple[ManagedArea, ...]) -> ManagedArea:
    matches = [area for area in areas if area.bundled_assets_root_rel == "skills"]
    assert len(matches) == 1
    return matches[0]


@pytest.mark.parametrize("installer_cls", INSTALLERS)
def test_every_provider_declares_the_same_flat_skill_area(installer_cls: type) -> None:
    area = _skill_area(installer_cls.profile.areas)
    assert area.managed_dir_rel == "skills"
    assert area.files == SKILL_FILES


def test_claude_and_codex_have_no_registration_area() -> None:
    assert ClaudeInstaller.profile.areas == (
        ManagedArea("skills", "skills", SKILL_FILES),
    )
    assert CodexInstaller.profile.areas == (
        ManagedArea("skills", "skills", SKILL_FILES),
    )


def test_hermes_and_openclaw_keep_registration_plus_skills() -> None:
    assert HermesInstaller.profile.areas[0] == ManagedArea(
        "hermes-profile",
        "profiles/lingo-loop",
        ("distribution.yaml", "config.yaml", "SOUL.md"),
    )
    assert HermesInstaller.profile.areas[1] == ManagedArea(
        "skills",
        "skills",
        SKILL_FILES,
    )
    assert OpenClawInstaller.profile.areas[0].bundled_assets_root_rel == "openclaw-plugin"
    assert OpenClawInstaller.profile.areas[0].managed_dir_rel == "plugins/lingo-loop"
    assert OpenClawInstaller.profile.areas[1] == ManagedArea(
        "skills",
        "skills",
        SKILL_FILES,
    )


def test_openclaw_missing_skill_sibling_triggers_one_skill_repair() -> None:
    skills_root = HOME / ".openclaw" / "skills"
    bundled_root = bundled_assets_root_for("skills")
    files: dict[Path, str] = {}
    for rel in SKILL_FILES:
        if rel == "tutor-judge/SKILL.md":
            continue
        files[skills_root / rel] = (bundled_root / rel).read_text(encoding="utf-8")
    plugin_root = HOME / ".openclaw" / "plugins" / "lingo-loop"
    plugin_bundle = bundled_assets_root_for("openclaw-plugin")
    for rel in OpenClawInstaller.profile.areas[0].files:
        files[plugin_root / rel] = (plugin_bundle / rel).read_text(encoding="utf-8")

    ctx = _ctx(files=files)
    plan = build_plan(ctx, InitRequest(providers=[HostId.OPENCLAW]))
    pp = plan.plans[0]

    assert pp.status.state == ProviderState.NEEDS_REPAIR
    write_actions = [a for a in pp.actions if a.kind == ProviderActionKind.WRITE_FILE]
    assert [a.target_path for a in write_actions] == [
        str(skills_root / "tutor-judge/SKILL.md")
    ]


def test_claude_init_writes_only_skill_area_files() -> None:
    ctx = _ctx()
    result = run_init(ctx, InitRequest(providers=[HostId.CLAUDE], yes=True))

    assert result.results[0].verified
    for rel in SKILL_FILES:
        assert ctx.fs.is_file(HOME / ".claude" / "skills" / rel)
    assert not ctx.fs.is_file(HOME / ".claude" / "plugins" / "lingo-loop" / "plugin.json")


def test_status_managed_files_lists_all_area_paths() -> None:
    ctx = _ctx()
    plan = build_plan(ctx, InitRequest(providers=[HostId.HERMES]))
    expected = [
        str(HOME / ".hermes" / "profiles" / "lingo-loop" / rel)
        for rel in ("distribution.yaml", "config.yaml", "SOUL.md")
    ]
    expected.extend(str(HOME / ".hermes" / "skills" / rel) for rel in SKILL_FILES)

    assert plan.plans[0].status.managed_files == expected
