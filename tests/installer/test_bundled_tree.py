"""Bundled-tree model for provider installers (fix-oss-distribution-blockers §1).

Each provider profile declares a directory tree of files. The installer must
materialize, verify, and drift-detect every declared file individually. A
missing or content-divergent sibling marks the host ``NEEDS_REPAIR`` and the
repair plan emits one ``WRITE_FILE`` action per divergent file.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from language_tutor.installer.assets import (
    bundled_assets_root,
    bundled_assets_root_for,
)
from language_tutor.installer.protocol import InstallerContext
from language_tutor.installer.providers.openclaw import OpenClawInstaller
from language_tutor.installer.seams import FakeCommandRunner, FakeFilesystem
from language_tutor.installer.service import build_plan, run_init
from language_tutor.schemas import (
    HostId,
    InitRequest,
    ProviderActionKind,
    ProviderActionStage,
    ProviderState,
)

HOME = Path("/fake/home")
_HOST_ROOT = {
    HostId.CLAUDE: ".claude",
    HostId.CODEX: ".codex",
    HostId.HERMES: ".hermes",
    HostId.OPENCLAW: ".openclaw",
}
_MANAGED_DIR = {
    HostId.CLAUDE: ".claude/plugins/lingo-loop",
    HostId.CODEX: ".codex/plugins/lingo-loop",
    HostId.HERMES: ".hermes/profiles/lingo-loop",
    HostId.OPENCLAW: ".openclaw/plugins/lingo-loop",
}


def _ctx(
    *,
    files: dict[Path, str] | None = None,
    available: dict[str, str] | None = None,
) -> InstallerContext:
    fs = FakeFilesystem(home=HOME, files=files)
    for rel in _HOST_ROOT.values():
        fs.mkdir(HOME / rel)
    return InstallerContext(
        fs=fs,
        runner=FakeCommandRunner(
            available=available or {h.value: f"/usr/bin/{h.value}" for h in HostId}
        ),
        bundled_assets_root=bundled_assets_root(),
    )


# --- 1.4: OpenClaw profile declares its full file list ----------------------


def test_openclaw_profile_declares_full_bundled_tree() -> None:
    declared = set(OpenClawInstaller.profile.files)
    assert "package.json" in declared
    assert "openclaw.plugin.json" in declared
    assert "tsconfig.json" in declared

    # Every `src/**/*.ts` file currently shipped in the bundled tree must be
    # declared. If a new TS file is added to the bundle, this catches the
    # missing manifest entry.
    bundled_root = bundled_assets_root_for("openclaw-plugin")
    ts_files = {
        str(p.relative_to(bundled_root))
        for p in bundled_root.rglob("src/*.ts")
    }
    assert ts_files, "expected at least one bundled openclaw src/*.ts file"
    assert ts_files <= declared, (
        f"openclaw profile is missing TS files: {ts_files - declared}"
    )


def test_openclaw_install_materializes_every_declared_file() -> None:
    ctx = _ctx()
    result = run_init(ctx, InitRequest(providers=[HostId.OPENCLAW], yes=True))
    assert result.results[0].verified

    managed_dir = HOME / _MANAGED_DIR[HostId.OPENCLAW]
    for rel in OpenClawInstaller.profile.files:
        target = managed_dir / rel
        assert ctx.fs.is_file(target), f"missing managed file: {target}"
        bundled_path = bundled_assets_root_for("openclaw-plugin") / rel
        assert ctx.fs.read_text(target) == bundled_path.read_text(encoding="utf-8")


# --- 1.6 / 1.9: missing sibling triggers per-file repair --------------------


def test_missing_sibling_triggers_single_file_repair() -> None:
    """Spec scenario: OpenClaw has ``package.json`` but missing
    ``openclaw.plugin.json`` -> needs-repair with one WRITE_FILE action for the
    missing sibling only."""

    managed_dir = HOME / _MANAGED_DIR[HostId.OPENCLAW]
    bundled_root = bundled_assets_root_for("openclaw-plugin")
    # Pre-populate every declared file EXCEPT openclaw.plugin.json with the
    # correct content so the only divergence is the missing sibling.
    files: dict[Path, str] = {}
    for rel in OpenClawInstaller.profile.files:
        if rel == "openclaw.plugin.json":
            continue
        files[managed_dir / rel] = (bundled_root / rel).read_text(encoding="utf-8")

    ctx = _ctx(files=files)
    plan = build_plan(ctx, InitRequest(providers=[HostId.OPENCLAW]))
    pp = plan.plans[0]
    assert pp.status.state == ProviderState.NEEDS_REPAIR
    write_actions = [
        a for a in pp.actions if a.kind == ProviderActionKind.WRITE_FILE
    ]
    assert len(write_actions) == 1
    assert write_actions[0].target_path == str(managed_dir / "openclaw.plugin.json")

    # Apply and verify every file is present.
    result = run_init(ctx, InitRequest(providers=[HostId.OPENCLAW], yes=True))
    assert result.results[0].verified
    for rel in OpenClawInstaller.profile.files:
        assert ctx.fs.is_file(managed_dir / rel)


# --- 1.9: single-file drift in a multi-file tree ----------------------------


@pytest.mark.parametrize(
    ("host", "drift_rel"),
    [
        (HostId.OPENCLAW, "tsconfig.json"),
        (HostId.OPENCLAW, "src/index.ts"),
    ],
)
def test_single_file_drift_rewrites_only_divergent_file(
    host: HostId, drift_rel: str
) -> None:
    managed_dir = HOME / _MANAGED_DIR[host]
    bundled_root = bundled_assets_root_for(
        {
            HostId.CLAUDE: ".claude-plugin",
            HostId.CODEX: ".codex-plugin",
            HostId.HERMES: "hermes-profile",
            HostId.OPENCLAW: "openclaw-plugin",
        }[host]
    )
    profile = {
        HostId.OPENCLAW: OpenClawInstaller.profile,
    }[host]

    files: dict[Path, str] = {}
    for rel in profile.files:
        content = (bundled_root / rel).read_text(encoding="utf-8")
        if rel == drift_rel:
            content = "// DRIFTED " + content
        files[managed_dir / rel] = content

    ctx = _ctx(files=files)
    plan = build_plan(ctx, InitRequest(providers=[host]))
    pp = plan.plans[0]
    assert pp.status.state == ProviderState.NEEDS_REPAIR
    write_actions = [
        a for a in pp.actions if a.kind == ProviderActionKind.WRITE_FILE
    ]
    assert [a.target_path for a in write_actions] == [str(managed_dir / drift_rel)]

    # Snapshot non-divergent files; they must not be rewritten.
    non_divergent = [r for r in profile.files if r != drift_rel]
    before = {r: ctx.fs.read_text(managed_dir / r) for r in non_divergent}

    result = run_init(ctx, InitRequest(providers=[host], yes=True))
    assert result.results[0].verified
    # Non-divergent files unchanged.
    for rel in non_divergent:
        assert ctx.fs.read_text(managed_dir / rel) == before[rel]
    # Drifted file rewritten to bundled content.
    assert ctx.fs.read_text(managed_dir / drift_rel) == (
        bundled_root / drift_rel
    ).read_text(encoding="utf-8")


def test_status_managed_files_lists_every_declared_path() -> None:
    ctx = _ctx()
    plan = build_plan(ctx, InitRequest(providers=[HostId.OPENCLAW]))
    status = plan.plans[0].status
    managed_dir = HOME / _MANAGED_DIR[HostId.OPENCLAW]
    expected = [str(managed_dir / rel) for rel in OpenClawInstaller.profile.files]
    assert status.managed_files == expected


def test_idempotent_full_tree() -> None:
    ctx = _ctx()
    run_init(ctx, InitRequest(providers=[HostId.OPENCLAW], yes=True))
    second = run_init(ctx, InitRequest(providers=[HostId.OPENCLAW], yes=True))
    assert second.results[0].status.state == ProviderState.INSTALLED
    assert second.results[0].actions[0].kind == ProviderActionKind.SKIP
    assert second.results[0].actions[0].stage == ProviderActionStage.SKIPPED
    assert second.results[0].verified
