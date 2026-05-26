"""Installer MUST never write learner-owned state.

Spec: `tutor init` writes only managed plugin/profile files under per-host
config roots. Learner profile YAML, SQLite history, sessions, checkpoints,
memories, logs, secrets, and tutor data dirs are out of bounds.
"""

from __future__ import annotations

import fnmatch
from pathlib import Path

from language_tutor.installer.assets import bundled_assets_root
from language_tutor.installer.protocol import InstallerContext
from language_tutor.installer.seams import FakeCommandRunner, FakeFilesystem
from language_tutor.installer.service import run_init
from language_tutor.schemas import PRIVACY_EXCLUDED_PATTERNS, HostId, InitRequest

HOME = Path("/fake/home")
FORBIDDEN_DIR_NAMES = {
    "secrets",
    "memories",
    "sessions",
    "checkpoints",
    "logs",
    "caches",
    "local_overrides",
}


def _ctx_all_hosts() -> InstallerContext:
    fs = FakeFilesystem(home=HOME)
    # Precreate per-host config roots so detect() does not short-circuit to
    # BLOCKED on the "missing config root" check (covered by dedicated tests).
    for rel in (".claude", ".codex", ".hermes", ".openclaw"):
        fs.mkdir(HOME / rel)
    return InstallerContext(
        fs=fs,
        runner=FakeCommandRunner(available={h.value: f"/usr/bin/{h.value}" for h in HostId}),
        bundled_assets_root=bundled_assets_root(),
    )


def _violates_privacy(path: Path) -> str | None:
    parts = path.parts
    for part in parts:
        if part in FORBIDDEN_DIR_NAMES:
            return f"path contains forbidden segment '{part}': {path}"
        for pat in PRIVACY_EXCLUDED_PATTERNS:
            if fnmatch.fnmatchcase(part, pat):
                return f"path segment '{part}' matches excluded pattern '{pat}': {path}"
    if path.name in {"profile.yaml", "preferences.yaml", "history.sqlite3"}:
        return f"path is a learner-owned artifact: {path}"
    return None


def test_init_writes_only_under_per_host_config_root() -> None:
    ctx = _ctx_all_hosts()
    run_init(ctx, InitRequest(providers=list(HostId), yes=True))
    writes = ctx.fs.list_writes()
    assert writes, "expected installer to write managed files"
    for path in writes:
        violation = _violates_privacy(path)
        assert violation is None, violation
        rel = path.relative_to(HOME)
        first = rel.parts[0]
        assert first in {".claude", ".codex", ".hermes", ".openclaw"}, (
            f"installer wrote outside per-host config roots: {path}"
        )
        assert "lingo-loop" in rel.parts, (
            f"managed file not scoped to lingo-loop dir: {path}"
        )


def test_dry_run_writes_nothing_anywhere() -> None:
    ctx = _ctx_all_hosts()
    run_init(ctx, InitRequest(providers=list(HostId), yes=True, dry_run=True))
    assert ctx.fs.list_writes() == {}


def test_repair_does_not_touch_unrelated_files() -> None:
    ctx = _ctx_all_hosts()
    pre = HOME / ".claude" / "settings.json"
    ctx.fs.write_text(pre, '{"user":"data"}')
    run_init(ctx, InitRequest(providers=[HostId.CLAUDE], yes=True))
    assert ctx.fs.read_text(pre) == '{"user":"data"}'
