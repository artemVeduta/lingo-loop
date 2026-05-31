"""T038 (US3): packaging-privacy regression for the hook-free lifecycle.

Covers SC-004 + FR-014:
- No package requires a hook for correctness — the ``hooks/`` directory must
  not exist (FR-011).
- Zero user-owned ``sessions``/``checkpoints`` data may ship in any package
  root (FR-014).
- ``SetupPackage.excluded_paths`` rejects manifests that omit either
  ``sessions`` or ``checkpoints``.
- ``PRIVACY_EXCLUDED_PATTERNS`` enumerates both ``sessions`` and
  ``checkpoints``.
"""

from __future__ import annotations

import fnmatch
from pathlib import Path

import pytest
from pydantic import ValidationError

from language_tutor.schemas import PRIVACY_EXCLUDED_PATTERNS, HostId, SetupPackage

REPO_ROOT = Path(__file__).resolve().parents[2]

PACKAGE_ROOTS = (
    "openclaw-plugin",
    "hermes-profile",
    "skills",
)

FORBIDDEN_USER_OWNED = ("sessions", "checkpoints", "*.sqlite", "*.sqlite3", "*.db")


def _iter_files(root: Path) -> list[Path]:
    if not root.exists():
        return []
    return [p for p in root.rglob("*") if p.is_file() and "__pycache__" not in p.parts]


def test_no_hook_directory_shipped() -> None:
    """FR-011: hooks/ removed — no package may require a hook for correctness."""
    assert not (REPO_ROOT / "hooks").exists(), (
        "hooks/ must not exist: the no-hook lifecycle is the only target (FR-011)"
    )


def test_no_user_owned_session_state_in_packages() -> None:
    """FR-014 / SC-004: no shipped user-owned session/checkpoint data."""
    offenders: list[str] = []
    for rel in PACKAGE_ROOTS:
        for path in _iter_files(REPO_ROOT / rel):
            for pattern in FORBIDDEN_USER_OWNED:
                if fnmatch.fnmatch(path.name, pattern) or path.name == pattern:
                    offenders.append(str(path.relative_to(REPO_ROOT)))
    assert offenders == [], f"user-owned session state in package roots: {offenders}"


def test_privacy_pattern_list_covers_sessions_and_checkpoints() -> None:
    joined = " ".join(PRIVACY_EXCLUDED_PATTERNS)
    assert "sessions" in joined, "sessions must be in PRIVACY_EXCLUDED_PATTERNS"
    assert "checkpoints" in joined, "checkpoints must be in PRIVACY_EXCLUDED_PATTERNS"


def test_setup_package_requires_checkpoints_exclusion() -> None:
    with pytest.raises(ValidationError):
        SetupPackage(
            host=HostId.CLAUDE,
            root_path="skills",
            manifest_paths=["skills/tutor-setup/SKILL.md"],
            # Missing 'checkpoints' (and others).
            excluded_paths=["secrets", "memories", "sessions", "logs", "local"],
            verification_command="tutor init --provider claude --yes --dry-run --json",
        )


def test_setup_package_accepts_full_exclusions_with_checkpoints() -> None:
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
