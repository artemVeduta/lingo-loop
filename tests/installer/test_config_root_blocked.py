"""Missing-config-root and missing-bundled-asset BLOCKED behavior (§2).

Spec scenarios:
- "Missing host config root blocks with repair guidance"
- "Missing bundled asset in the wheel blocks with repair guidance"
"""

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
_HOST_ROOT = {
    HostId.CLAUDE: ".claude",
    HostId.CODEX: ".codex",
    HostId.HERMES: ".hermes",
    HostId.OPENCLAW: ".openclaw",
}


def _ctx(
    *,
    available: dict[str, str] | None = None,
    bundled_assets_override: Path | None = None,
    precreated_roots: list[str] | None = None,
) -> InstallerContext:
    fs = FakeFilesystem(home=HOME)
    for rel in precreated_roots or []:
        fs.mkdir(HOME / rel)
    return InstallerContext(
        fs=fs,
        runner=FakeCommandRunner(
            available=available or {h.value: f"/usr/bin/{h.value}" for h in HostId}
        ),
        bundled_assets_root=bundled_assets_override or bundled_assets_root(),
    )


# --- 2.1 / 2.2: missing config root -> BLOCKED ------------------------------


@pytest.mark.parametrize("host", list(HostId))
def test_detect_blocked_when_config_root_missing(host: HostId) -> None:
    # CLI on PATH but the host's config root does NOT exist on disk.
    ctx = _ctx(precreated_roots=[])
    result = run_init(ctx, InitRequest(providers=[host], yes=True))
    r = result.results[0]
    assert r.status.state == ProviderState.BLOCKED
    assert r.verified is False
    assert r.repair_hint is not None
    # Repair hint MUST name the missing config root path and link to the docs.
    expected_root = str(HOME / _HOST_ROOT[host])
    assert expected_root in r.repair_hint
    assert f"docs/install/{host.value}.md" in r.repair_hint
    # Repair hint MUST identify the kind of missing prerequisite (config root)
    # by instructing the learner to run the host CLI to initialise it.
    assert "Run" in r.repair_hint
    # No writes occurred.
    assert ctx.fs.list_writes() == {}


@pytest.mark.parametrize("host", list(HostId))
def test_plan_emits_block_action_when_config_root_missing(host: HostId) -> None:
    ctx = _ctx(precreated_roots=[])
    plan = build_plan(ctx, InitRequest(providers=[host]))
    pp = plan.plans[0]
    assert pp.status.state == ProviderState.BLOCKED
    assert len(pp.actions) == 1
    assert pp.actions[0].kind == ProviderActionKind.BLOCK
    assert pp.actions[0].stage == ProviderActionStage.BLOCKED


def test_detect_unblocked_once_config_root_exists() -> None:
    # Smoke-test: precreate every config root and detection proceeds past the
    # missing-config-root guard.
    ctx = _ctx(precreated_roots=list(_HOST_ROOT.values()))
    result = run_init(ctx, InitRequest(providers=list(HostId), yes=True))
    assert all(
        r.status.state != ProviderState.BLOCKED for r in result.results
    ), [r.status.repair_hint for r in result.results]


# --- 2.4: missing bundled asset -> BLOCKED with "packaging defect" hint -----


def test_detect_blocked_when_bundled_asset_missing(tmp_path: Path) -> None:
    """Simulate a packaging defect: the wheel ships an empty bundled-assets
    root with no host-package files. Every provider must report BLOCKED with a
    repair hint that identifies the missing path as a packaging defect."""

    empty_root = tmp_path / "empty_assets"
    empty_root.mkdir()
    # Override env so the installer's per-host resolver picks this empty root.
    import os

    prev = os.environ.get("LANGUAGE_TUTOR_BUNDLED_ASSETS")
    os.environ["LANGUAGE_TUTOR_BUNDLED_ASSETS"] = str(empty_root)
    try:
        ctx = _ctx(
            precreated_roots=list(_HOST_ROOT.values()),
            bundled_assets_override=empty_root,
        )
        for host in HostId:
            result = run_init(ctx, InitRequest(providers=[host], yes=True))
            r = result.results[0]
            assert r.status.state == ProviderState.BLOCKED, (
                f"{host}: expected BLOCKED, got {r.status.state} ({r.repair_hint})"
            )
            assert r.repair_hint is not None
            assert "packaging defect" in r.repair_hint
            assert f"docs/install/{host.value}.md" in r.repair_hint
            assert r.verified is False
        # No writes performed for any host.
        assert ctx.fs.list_writes() == {}
    finally:
        if prev is None:
            os.environ.pop("LANGUAGE_TUTOR_BUNDLED_ASSETS", None)
        else:
            os.environ["LANGUAGE_TUTOR_BUNDLED_ASSETS"] = prev
