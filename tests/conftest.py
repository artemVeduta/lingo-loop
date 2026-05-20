from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import pytest
from click.testing import CliRunner

from language_tutor.cli import main


@pytest.fixture()
def tutor_home(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.setenv("LANGUAGE_TUTOR_HOME", str(tmp_path))
    return tmp_path


@pytest.fixture()
def runner(tutor_home: Path) -> Iterator[CliRunner]:
    del tutor_home
    yield CliRunner()


def invoke_json(runner: CliRunner, args: list[str]) -> dict[str, object]:
    result = runner.invoke(main, args)
    assert result.exit_code == 0, result.output
    import json

    return json.loads(result.output)
