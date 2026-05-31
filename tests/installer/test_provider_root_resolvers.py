from __future__ import annotations

from pathlib import Path

from language_tutor.installer.assets import bundled_assets_root
from language_tutor.installer.protocol import InstallerContext
from language_tutor.installer.providers.claude import ClaudeInstaller
from language_tutor.installer.providers.codex import CodexInstaller
from language_tutor.installer.providers.hermes import HermesInstaller
from language_tutor.installer.seams import FakeCommandRunner, FakeFilesystem
from language_tutor.schemas import HostId

HOME = Path("/fake/home")


def _ctx() -> InstallerContext:
    return InstallerContext(
        fs=FakeFilesystem(home=HOME),
        runner=FakeCommandRunner(
            available={host.value: f"/usr/bin/{host.value}" for host in HostId}
        ),
        bundled_assets_root=bundled_assets_root(),
    )


def test_hermes_home_overrides_fake_home(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setenv("HERMES_HOME", "/opt/data")
    assert HermesInstaller(_ctx()).config_root() == Path("/opt/data")


def test_hermes_falls_back_to_home_dot_hermes(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.delenv("HERMES_HOME", raising=False)
    assert HermesInstaller(_ctx()).config_root() == HOME / ".hermes"


def test_codex_home_overrides_fake_home(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setenv("CODEX_HOME", "/var/codex")
    assert CodexInstaller(_ctx()).config_root() == Path("/var/codex")


def test_codex_falls_back_to_home_dot_codex(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.delenv("CODEX_HOME", raising=False)
    assert CodexInstaller(_ctx()).config_root() == HOME / ".codex"


def test_claude_config_dir_overrides_fake_home(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setenv("CLAUDE_CONFIG_DIR", "/var/claude")
    assert ClaudeInstaller(_ctx()).config_root() == Path("/var/claude")


def test_claude_falls_back_to_home_dot_claude(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.delenv("CLAUDE_CONFIG_DIR", raising=False)
    assert ClaudeInstaller(_ctx()).config_root() == HOME / ".claude"
