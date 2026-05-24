from __future__ import annotations

import json
from pathlib import Path

import pytest
from click.testing import CliRunner

from language_tutor.cli import main


@pytest.fixture()
def fake_clis(monkeypatch: pytest.MonkeyPatch) -> dict[str, str]:
    """Stub which() so per-host CLIs appear to be on PATH."""
    available = {"claude", "codex", "hermes", "openclaw"}

    def fake_which(self: object, exe: str) -> str | None:
        return f"/fake/bin/{exe}" if exe in available else None

    monkeypatch.setattr(
        "language_tutor.installer.seams.RealCommandRunner.which", fake_which
    )
    return {e: f"/fake/bin/{e}" for e in available}


@pytest.fixture()
def fake_home(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Pin Path.home() so the installer writes under tmp_path, not the user's $HOME."""
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setattr(
        "language_tutor.installer.seams.RealFilesystem.home", lambda self: home
    )
    monkeypatch.setattr("pathlib.Path.home", lambda: home)
    return home


@pytest.fixture()
def tty_stdin(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("language_tutor.installer.seams.is_tty", lambda stream=None: True)


@pytest.fixture()
def no_tty(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("language_tutor.installer.seams.is_tty", lambda stream=None: False)


def test_init_help() -> None:
    runner = CliRunner()
    result = runner.invoke(main, ["init", "--help"])
    assert result.exit_code == 0
    assert "Detect supported AI hosts" in result.output
    for flag in ("--provider", "--yes", "--dry-run", "--json"):
        assert flag in result.output


def test_init_invalid_provider() -> None:
    runner = CliRunner()
    result = runner.invoke(main, ["init", "--provider", "antigravity", "--yes"])
    assert result.exit_code != 0
    assert "antigravity" in result.output or "Invalid value" in result.output


def test_init_non_tty_requires_provider_and_yes(no_tty: None, fake_home: Path) -> None:
    del no_tty, fake_home
    runner = CliRunner()
    result = runner.invoke(main, ["init"])
    assert result.exit_code != 0
    assert "init_non_interactive_unsafe" in result.output


def test_init_dry_run_json_emits_init_result(
    fake_clis: dict[str, str], fake_home: Path, no_tty: None
) -> None:
    del fake_clis, no_tty
    runner = CliRunner()
    result = runner.invoke(
        main, ["init", "--provider", "claude", "--yes", "--dry-run", "--json"]
    )
    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["dry_run"] is True
    assert payload["schema_version"] == 1
    assert payload["results"][0]["host"] == "claude"
    assert payload["results"][0]["actions"][0]["stage"] == "planned"
    assert not (fake_home / ".claude" / "plugins" / "lingo-loop" / "plugin.json").exists()


def test_init_writes_managed_file_and_is_idempotent(
    fake_clis: dict[str, str], fake_home: Path, no_tty: None
) -> None:
    del fake_clis, no_tty
    runner = CliRunner()
    first = runner.invoke(
        main, ["init", "--provider", "claude", "--yes", "--json"]
    )
    assert first.exit_code == 0, first.output
    managed = fake_home / ".claude" / "plugins" / "lingo-loop" / "plugin.json"
    assert managed.exists()

    second = runner.invoke(
        main, ["init", "--provider", "claude", "--yes", "--json"]
    )
    assert second.exit_code == 0
    payload = json.loads(second.output)
    r = payload["results"][0]
    assert r["status"]["state"] == "installed"
    assert r["actions"][0]["kind"] == "skip"
    assert r["verified"] is True


def test_init_multi_provider_json(
    fake_clis: dict[str, str], fake_home: Path, no_tty: None
) -> None:
    del fake_clis, no_tty
    runner = CliRunner()
    result = runner.invoke(
        main,
        [
            "init",
            "--provider", "claude",
            "--provider", "codex",
            "--yes",
            "--json",
        ],
    )
    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    hosts = [r["host"] for r in payload["results"]]
    assert hosts == ["claude", "codex"]
    for r in payload["results"]:
        assert r["verified"]


def test_init_blocked_when_host_cli_missing(
    fake_home: Path, no_tty: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    del fake_home, no_tty
    monkeypatch.setattr(
        "language_tutor.installer.seams.RealCommandRunner.which",
        lambda self, exe: None,
    )
    runner = CliRunner()
    result = runner.invoke(
        main, ["init", "--provider", "claude", "--yes", "--json"]
    )
    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    r = payload["results"][0]
    assert r["status"]["state"] == "blocked"
    assert r["verified"] is False
    assert r["repair_hint"]


def test_init_interactive_default_lists_providers(
    fake_clis: dict[str, str], fake_home: Path, tty_stdin: None
) -> None:
    del fake_clis, tty_stdin
    runner = CliRunner()
    result = runner.invoke(main, ["init"], input="claude\nn\n")
    assert result.exit_code == 0, result.output
    assert "Detected providers" in result.output
    assert "Claude" in result.output
    assert "Aborted." in result.output
    assert not (fake_home / ".claude" / "plugins" / "lingo-loop" / "plugin.json").exists()
