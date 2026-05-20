from __future__ import annotations

from tests.conftest import invoke_json


def test_cli_error_envelope(runner) -> None:  # type: ignore[no-untyped-def]
    result = runner.invoke(
        __import__("language_tutor.cli").cli.main, ["setup", "write", "--json", "{bad"]
    )
    assert result.exit_code == 1
    assert '"error"' in result.output


def test_doctor_json(runner) -> None:  # type: ignore[no-untyped-def]
    data = invoke_json(runner, ["doctor", "--json"])
    assert "checks" in data
