from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
from pydantic import ValidationError

from language_tutor.schemas import (
    ConformanceRun,
    Decision,
    FlowResult,
    HostId,
    ManualProviderInstallReport,
    RepresentativeFlow,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
CONTEXT_DIR = REPO_ROOT / "specs/006-agent-adapter-setup/subagent-reports"
HOSTS = ("hermes", "openclaw", "claude", "codex")

CONTEXT_REQUIRED_SECTIONS = (
    "## Scope",
    "## Required Reads",
    "## Official Source",
    "## Shared Contracts",
    "## Verification Requirements",
    "## Report Requirements",
)


def _passing_flows() -> dict[str, str]:
    return {flow.value: FlowResult.PASS.value for flow in RepresentativeFlow}


def _run(**overrides: Any) -> dict[str, Any]:
    data: dict[str, Any] = {
        "host": HostId.CLAUDE,
        "capability_profile": "schemas/host_capability_profile.schema.json",
        "flows": _passing_flows(),
        "boot_context_result": FlowResult.PASS,
        "feedback_contract_result": FlowResult.PASS,
        "progress_contract_result": FlowResult.PASS,
        "error_behavior_result": FlowResult.PASS,
        "data_ownership_result": FlowResult.PASS,
        "decision": Decision.PASS,
    }
    data.update(overrides)
    return data


def test_conformance_requires_all_six_flows() -> None:
    flows = _passing_flows()
    del flows["progress"]
    with pytest.raises(ValidationError):
        ConformanceRun(**_run(flows=flows))


def test_skipped_flow_requires_capability_gate() -> None:
    flows = _passing_flows()
    flows["transcript"] = FlowResult.SKIPPED.value
    with pytest.raises(ValidationError):
        ConformanceRun(**_run(flows=flows))


def test_skipped_flow_allowed_when_gated() -> None:
    flows = _passing_flows()
    flows["transcript"] = FlowResult.SKIPPED.value
    run = ConformanceRun(**_run(flows=flows, skipped_flows=[RepresentativeFlow.TRANSCRIPT]))
    assert run.decision == Decision.PASS.value


def test_manual_report_requires_all_flow_results() -> None:
    results: dict[Any, str] = {flow.value: "pass" for flow in RepresentativeFlow}
    del results["vocab"]
    with pytest.raises(ValidationError):
        ManualProviderInstallReport(
            host=HostId.CODEX,
            performed_on="2026-05-22",
            package_ref="local",
            install_result="pass",
            launch_result="pass",
            capability_check_result="pass",
            representative_flow_results=results,
            update_or_reload_result="pass",
            inspect_result="pass",
            remove_result="n/a",
            user_data_preservation="pass",
        )


# --- US2: subagent context packages --------------------------------------


@pytest.mark.parametrize("host", HOSTS)
def test_context_package_has_required_sections(host: str) -> None:
    path = CONTEXT_DIR / f"{host}-context.md"
    if not path.exists():
        pytest.skip(f"{host}-context.md not yet created")
    text = path.read_text(encoding="utf-8")
    for section in CONTEXT_REQUIRED_SECTIONS:
        assert section in text, f"{host} context missing {section}"
    assert f"host-setup-profiles/{host}.md" in text
    assert f"subagent-reports/{host}.md" in text


# --- US3: manual reports cover all six representative flows ---------------

MANUAL_DIR = REPO_ROOT / "specs/006-agent-adapter-setup/manual-install-reports"
SIX_FLOWS = ("reading", "lesson", "transcript", "vocab", "writing", "progress")


@pytest.mark.parametrize("host", HOSTS)
def test_manual_report_covers_six_flows(host: str) -> None:
    path = MANUAL_DIR / f"{host}.md"
    if not path.exists():
        pytest.skip(f"manual report {host}.md not yet created")
    text = path.read_text(encoding="utf-8").lower()
    for flow in SIX_FLOWS:
        assert flow in text, f"{host} manual report missing flow: {flow}"


# --- US4: host setup error behavior --------------------------------------

ERROR_CATEGORIES = (
    "missing_prerequisite",
    "invalid_configuration",
    "permission_required",
    "unsupported_capability",
    "source_changed",
    "unknown",
)


@pytest.mark.parametrize("category", ERROR_CATEGORIES)
def test_host_setup_failure_is_learner_safe(category: str) -> None:
    from language_tutor.errors import host_setup_failure_payload, make_host_setup_failure

    failure = make_host_setup_failure(
        host="hermes",
        phase="install",
        category=category,
        detail="the hermes CLI was not found on PATH",
    )
    assert failure.category == category
    assert "hermes" in failure.message
    assert failure.remediation
    # Data-safe by default and never leaks secrets/answers.
    assert "no learner data" in failure.data_safety.lower()
    payload = host_setup_failure_payload(failure)["host_setup_failure"]
    assert payload["host"] == "hermes"
    assert payload["phase"] == "install"


def test_host_setup_failure_reports_affected_paths_when_unsafe() -> None:
    from language_tutor.errors import make_host_setup_failure

    failure = make_host_setup_failure(
        host="codex",
        phase="update",
        category="invalid_configuration",
        detail="skill hub rewrite touched a tracked file",
        data_safe=False,
        affected_paths=["skills/tutor-setup/SKILL.md"],
    )
    assert "skills/tutor-setup/SKILL.md" in failure.data_safety
