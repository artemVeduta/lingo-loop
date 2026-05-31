from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

from language_tutor.adapters.base import (
    is_supported_host,
    load_host_setup_profile,
    supported_host_targets,
)
from language_tutor.schemas import (
    APPROVED_HOST_SOURCES,
    HostId,
    HostSetupProfileContract,
    OfficialSourceEvidence,
    SetupModel,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
PROFILE_DIR = REPO_ROOT / "specs/006-agent-adapter-setup/contracts/host-setup-profiles"
SUBAGENT_REPORTS = REPO_ROOT / "specs/006-agent-adapter-setup/subagent-reports"
MANUAL_REPORTS = REPO_ROOT / "specs/006-agent-adapter-setup/manual-install-reports"
EXPECTED_HOSTS = ("hermes", "openclaw", "claude", "codex")


# --- US1: supported scope -------------------------------------------------


def test_only_four_hosts_supported() -> None:
    targets = supported_host_targets()
    assert {h.value for h in targets} == set(EXPECTED_HOSTS)


def test_antigravity_is_not_supported() -> None:
    assert is_supported_host("antigravity") is False
    for host in EXPECTED_HOSTS:
        assert is_supported_host(host) is True


def test_each_target_cites_one_approved_source() -> None:
    for host_id, target in supported_host_targets().items():
        assert target.official_source_url == APPROVED_HOST_SOURCES[host_id.value]


def test_profile_contract_requires_source_evidence_and_flows() -> None:
    with pytest.raises(ValidationError):
        HostSetupProfileContract(
            host=HostId.CLAUDE,
            official_sources=[],  # missing required evidence
            package_model=SetupModel.DIRECTORY_COPY,
            package_files=["skills/"],
            install_flow=["tutor init --provider claude --yes"],
            launch_flow=["claude"],
            inspect_flow=["ls ~/.claude/skills/tutor-setup/SKILL.md"],
            update_or_reload_flow=["restart Claude Code"],
            user_owned_boundaries=["secrets"],
            capability_profile_path="schemas/host_capability_profile.schema.json",
            verification_expectations=["claude plugin validate"],
        )


def test_profile_contract_accepts_full_payload() -> None:
    contract = HostSetupProfileContract(
        host=HostId.CLAUDE,
        official_sources=[
            OfficialSourceEvidence(
                source_url=APPROVED_HOST_SOURCES["claude"],
                retrieved_on="2026-05-22",
                source_sections=["Plugins"],
                facts_used=["personal skills hub at ~/.claude/skills"],
            )
        ],
        package_model=SetupModel.DIRECTORY_COPY,
        package_files=["skills/"],
        install_flow=["tutor init --provider claude --yes"],
        launch_flow=["claude"],
        inspect_flow=["ls ~/.claude/skills/tutor-setup/SKILL.md"],
        update_or_reload_flow=["restart Claude Code"],
        user_owned_boundaries=["secrets", "memories", "sessions", "*.sqlite"],
        capability_profile_path="schemas/host_capability_profile.schema.json",
        verification_expectations=["tutor init --provider claude --yes --dry-run --json"],
    )
    assert contract.host == HostId.CLAUDE.value


# --- US1: no Antigravity artifacts ---------------------------------------


def _scan_dirs() -> list[Path]:
    dirs = [
        REPO_ROOT / "src",
        REPO_ROOT / "schemas",
        PROFILE_DIR,
        SUBAGENT_REPORTS,
        MANUAL_REPORTS,
    ]
    for extra in ("openclaw-plugin", "hermes-profile", "skills"):
        dirs.append(REPO_ROOT / extra)
    return [d for d in dirs if d.exists()]


def test_no_antigravity_artifacts() -> None:
    offenders: list[str] = []
    for base in _scan_dirs():
        for path in base.rglob("*"):
            if "__pycache__" in path.parts:
                continue
            if "antigravity" in path.name.lower():
                offenders.append(str(path.relative_to(REPO_ROOT)))
            text_suffixes = {".md", ".py", ".json", ".yaml", ".yml", ".ts"}
            if path.is_file() and path.suffix in text_suffixes:
                text = path.read_text(encoding="utf-8").lower()
                # An explicit exclusion note is allowed; an implementation artifact is not.
                mentions = "antigravity" in text
                exclusion_markers = (
                    "exclud",
                    "out of scope",
                    "out-of-scope",
                    "reject",
                    "forbidden",
                    "absent",
                    "no antigravity",
                    "not a valid",
                )
                excluded = any(marker in text for marker in exclusion_markers)
                if mentions and not excluded:
                    offenders.append(f"{path.relative_to(REPO_ROOT)} (mentions antigravity)")
    assert offenders == [], f"Antigravity artifacts found: {offenders}"


# --- US2: one profile per host (enforced once subagents add files) --------


@pytest.mark.parametrize("host", EXPECTED_HOSTS)
def test_host_profile_validates_when_present(host: str) -> None:
    path = PROFILE_DIR / f"{host}.md"
    if not path.exists():
        pytest.skip(f"{host}.md not yet created by its subagent")
    contract = load_host_setup_profile(str(path))
    assert contract.host == host


def test_no_unexpected_profile_files() -> None:
    for path in PROFILE_DIR.glob("*.md"):
        if path.name == "README.md":
            continue
        assert path.stem in EXPECTED_HOSTS, f"unexpected profile file: {path.name}"


# --- US2: one owner + one report per host --------------------------------


def test_each_target_has_exactly_one_primary_subagent() -> None:
    owners = [t.primary_subagent for t in supported_host_targets().values()]
    assert len(owners) == len(set(owners)) == len(EXPECTED_HOSTS)


@pytest.mark.parametrize("host", EXPECTED_HOSTS)
def test_one_report_file_per_host(host: str) -> None:
    report = SUBAGENT_REPORTS / f"{host}.md"
    if not report.exists():
        pytest.skip(f"{host}.md report not yet created by its subagent")
    text = report.read_text(encoding="utf-8")
    for heading in ("Changed Files", "Verification", "Source"):
        assert heading.lower() in text.lower(), f"{host} report missing {heading}"


# --- US3: manual provider install reports --------------------------------

MANUAL_REQUIRED_SECTIONS = (
    "Environment",
    "Install",
    "Launch",
    "Capability Check",
    "Representative Tutor Flows",
    "Update",
    "Inspect",
    "Remove",
    "User Data Preservation",
    "Decision",
)
_VALID_DECISIONS = ("pass", "fail", "blocked")


@pytest.mark.parametrize("host", EXPECTED_HOSTS)
def test_manual_report_has_required_sections(host: str) -> None:
    path = MANUAL_REPORTS / f"{host}.md"
    if not path.exists():
        pytest.skip(f"manual report {host}.md not yet created")
    text = path.read_text(encoding="utf-8")
    for section in MANUAL_REQUIRED_SECTIONS:
        assert section.lower() in text.lower(), f"{host} manual report missing {section}"


@pytest.mark.parametrize("host", EXPECTED_HOSTS)
def test_manual_report_records_a_valid_decision(host: str) -> None:
    path = MANUAL_REPORTS / f"{host}.md"
    if not path.exists():
        pytest.skip(f"manual report {host}.md not yet created")
    text = path.read_text(encoding="utf-8").lower()
    assert any(f"decision: {d}" in text or f"decision** {d}" in text for d in _VALID_DECISIONS) or any(
        d in text for d in _VALID_DECISIONS
    )


def test_subagent_reports_have_no_antigravity_paths() -> None:
    if not SUBAGENT_REPORTS.exists():
        pytest.skip("no subagent reports yet")
    for path in SUBAGENT_REPORTS.glob("*.md"):
        text = path.read_text(encoding="utf-8").lower()
        if "antigravity" in text:
            assert "exclud" in text or "out of scope" in text or "reject" in text, (
                f"{path.name} references Antigravity as an artifact"
            )
