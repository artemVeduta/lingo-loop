from __future__ import annotations

from tests.conftest import invoke_json


def test_doctor_reports_no_mutation(runner) -> None:  # type: ignore[no-untyped-def]
    report = invoke_json(runner, ["doctor", "--json"])
    assert report["learner_data_changed"] is False
    assert report["status"] == "ok"
    names = {check["name"] for check in report["checks"]}  # type: ignore[index]
    assert "runtime_payload:migrations/001_initial.sql" in names
    assert "runtime_payload:skills/tutor-vocab/SKILL.md" in names
