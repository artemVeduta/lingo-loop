from __future__ import annotations

from pathlib import Path

from tests.conftest import invoke_json


def test_setup_does_not_create_history(runner, tutor_home: Path) -> None:  # type: ignore[no-untyped-def]
    invoke_json(
        runner,
        [
            "setup",
            "write",
            "--json",
            '{"profile":{"native_language":"en","target_language":"uk"},"preferences":{}}',
        ],
    )
    assert not (tutor_home / "state" / "history.sqlite3").exists()
