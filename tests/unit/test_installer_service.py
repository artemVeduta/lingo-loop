from __future__ import annotations

from pathlib import Path

import pytest

from language_tutor.installer.assets import bundled_assets_root
from language_tutor.installer.protocol import InstallerContext
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

# Per-host conventional config roots that every installer expects to already
# exist (the host CLI creates these on its own first-run). Tests that drive
# the happy path must precreate these dirs, otherwise the installer returns
# BLOCKED with a "run the host CLI once" repair hint (spec scenario
# "Missing host config root blocks with repair guidance").
_HOST_CONFIG_ROOTS: dict[HostId, str] = {
    HostId.CLAUDE: ".claude",
    HostId.CODEX: ".codex",
    HostId.HERMES: ".hermes",
    HostId.OPENCLAW: ".openclaw",
}


def make_ctx(
    available_clis: dict[str, str] | None = None,
    files: dict[Path, str] | None = None,
    precreate_config_roots: bool = True,
) -> InstallerContext:
    fs = FakeFilesystem(home=HOME, files=files)
    if precreate_config_roots:
        for host in HostId:
            fs.mkdir(HOME / _HOST_CONFIG_ROOTS[host])
    return InstallerContext(
        fs=fs,
        runner=FakeCommandRunner(available=available_clis or {}),
        bundled_assets_root=bundled_assets_root(),
    )


def _managed_path(host: HostId) -> Path:
    suffix = {
        HostId.CLAUDE: ".claude/plugins/lingo-loop/plugin.json",
        HostId.CODEX: ".codex/plugins/lingo-loop/plugin.json",
        HostId.HERMES: ".hermes/profiles/lingo-loop/distribution.yaml",
        HostId.OPENCLAW: ".openclaw/plugins/lingo-loop/package.json",
    }[host]
    return HOME / suffix


def _bundled(host: HostId) -> str:
    rel = {
        HostId.CLAUDE: ".claude-plugin/plugin.json",
        HostId.CODEX: ".codex-plugin/plugin.json",
        HostId.HERMES: "hermes-profile/distribution.yaml",
        HostId.OPENCLAW: "openclaw-plugin/package.json",
    }[host]
    return (bundled_assets_root() / rel).read_text(encoding="utf-8")


@pytest.mark.parametrize("host", list(HostId))
def test_detect_blocked_when_cli_missing(host: HostId) -> None:
    ctx = make_ctx(available_clis={})
    result = run_init(ctx, InitRequest(providers=[host], yes=True))
    assert result.results[0].status.state == ProviderState.BLOCKED
    assert result.results[0].repair_hint is not None
    assert not result.results[0].verified


@pytest.mark.parametrize("host", list(HostId))
def test_detect_available_writes_file(host: HostId) -> None:
    ctx = make_ctx(available_clis={host.value: f"/usr/bin/{host.value}"})
    plan = build_plan(ctx, InitRequest(providers=[host]))
    pp = plan.plans[0]
    assert pp.status.state == ProviderState.AVAILABLE
    assert pp.actions[0].kind == ProviderActionKind.WRITE_FILE

    result = run_init(ctx, InitRequest(providers=[host], yes=True))
    assert result.results[0].verified
    written = ctx.fs.read_text(_managed_path(host))
    assert written == _bundled(host)
    assert result.results[0].actions[0].stage == ProviderActionStage.APPLIED


@pytest.mark.parametrize("host", list(HostId))
def test_dry_run_writes_nothing(host: HostId) -> None:
    ctx = make_ctx(available_clis={host.value: f"/usr/bin/{host.value}"})
    result = run_init(ctx, InitRequest(providers=[host], yes=True, dry_run=True))
    assert not ctx.fs.is_file(_managed_path(host))
    assert result.dry_run is True
    assert result.results[0].actions[0].stage == ProviderActionStage.PLANNED


@pytest.mark.parametrize("host", list(HostId))
def test_idempotent_second_run(host: HostId) -> None:
    ctx = make_ctx(available_clis={host.value: f"/usr/bin/{host.value}"})
    run_init(ctx, InitRequest(providers=[host], yes=True))
    second = run_init(ctx, InitRequest(providers=[host], yes=True))
    assert second.results[0].status.state == ProviderState.INSTALLED
    assert second.results[0].actions[0].kind == ProviderActionKind.SKIP
    assert second.results[0].verified


@pytest.mark.parametrize("host", list(HostId))
def test_needs_repair_when_managed_file_drifts(host: HostId) -> None:
    ctx = make_ctx(
        available_clis={host.value: f"/usr/bin/{host.value}"},
        files={_managed_path(host): "STALE-CONTENT"},
    )
    plan = build_plan(ctx, InitRequest(providers=[host]))
    assert plan.plans[0].status.state == ProviderState.NEEDS_REPAIR
    result = run_init(ctx, InitRequest(providers=[host], yes=True))
    assert result.results[0].verified
    assert ctx.fs.read_text(_managed_path(host)) == _bundled(host)


def test_multi_provider_all_four() -> None:
    ctx = make_ctx(available_clis={h.value: f"/usr/bin/{h.value}" for h in HostId})
    result = run_init(ctx, InitRequest(providers=list(HostId), yes=True))
    assert [r.host for r in result.results] == list(HostId)
    assert all(r.verified for r in result.results)


def test_default_selection_includes_all_supported() -> None:
    ctx = make_ctx(available_clis={h.value: f"/usr/bin/{h.value}" for h in HostId})
    result = run_init(ctx, InitRequest(yes=True))
    assert {r.host for r in result.results} == set(HostId)
