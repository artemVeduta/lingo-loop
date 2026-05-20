from __future__ import annotations

from tests.conftest import invoke_json


def test_doctor_reports_no_mutation(runner) -> None:  # type: ignore[no-untyped-def]
    report = invoke_json(runner, ["doctor", "--json"])
    assert report["learner_data_changed"] is False
