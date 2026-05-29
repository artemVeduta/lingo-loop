"""Contract: ``session-start --help`` documents the required PAYLOAD schema.

Regression guard: an agent discovering the command via ``--help`` must learn
that PAYLOAD is JSON requiring ``host``, instead of guessing ``{}`` and
hitting ``invalid_session_start`` on the first call.
"""

from __future__ import annotations

from language_tutor.cli import main


def test_session_start_help_documents_host(runner) -> None:  # type: ignore[no-untyped-def]
    result = runner.invoke(main, ["session-start", "--help"])
    assert result.exit_code == 0
    out = result.output
    assert "host" in out
    assert '{"host":' in out
