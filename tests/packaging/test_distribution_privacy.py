from __future__ import annotations

import fnmatch
from pathlib import Path

import pytest
from pydantic import ValidationError

from language_tutor.schemas import PRIVACY_EXCLUDED_PATTERNS, HostId, SetupPackage

REPO_ROOT = Path(__file__).resolve().parents[2]

# Distribution roots that hosts may package. Each must stay free of user-owned data.
PACKAGE_ROOTS = (
    "openclaw-plugin",
    "hermes-profile",
    "skills",
)

# Forbidden, machine-local / learner-owned artifacts that must never be packaged.
FORBIDDEN = (
    ".env",
    "*.sqlite",
    "*.sqlite3",
    "*.db",
    "*.db-wal",
    "*.db-shm",
    "*.log",
    "memories",
    "sessions",
)


def _iter_files(root: Path) -> list[Path]:
    if not root.exists():
        return []
    return [p for p in root.rglob("*") if p.is_file() and "__pycache__" not in p.parts]


def test_no_secrets_or_state_in_package_roots() -> None:
    offenders: list[str] = []
    for rel in PACKAGE_ROOTS:
        for path in _iter_files(REPO_ROOT / rel):
            name = path.name
            for pattern in FORBIDDEN:
                if fnmatch.fnmatch(name, pattern) or name == pattern:
                    offenders.append(str(path.relative_to(REPO_ROOT)))
    assert offenders == [], f"user-owned artifacts found in package roots: {offenders}"


def test_setup_package_requires_user_owned_exclusions() -> None:
    with pytest.raises(ValidationError):
        SetupPackage(
            host=HostId.CLAUDE,
            root_path="skills",
            manifest_paths=["skills/tutor-setup/SKILL.md"],
            excluded_paths=["nothing-useful"],
            verification_command="tutor init --provider claude --yes --dry-run --json",
        )


def test_setup_package_accepts_full_exclusions() -> None:
    package = SetupPackage(
        host=HostId.CLAUDE,
        root_path="skills",
        manifest_paths=["skills/tutor-setup/SKILL.md"],
        excluded_paths=[
            "secrets",
            "memories",
            "sessions",
            "checkpoints",
            "logs",
            "local",
            "*.sqlite",
        ],
        verification_command="tutor init --provider claude --yes --dry-run --json",
    )
    assert package.host == HostId.CLAUDE.value


def test_privacy_pattern_list_covers_core_categories() -> None:
    joined = " ".join(PRIVACY_EXCLUDED_PATTERNS)
    for token in ("secrets", "memories", "sessions", "logs", "local", ".env"):
        assert token in joined
    assert any("sqlite" in p for p in PRIVACY_EXCLUDED_PATTERNS)
