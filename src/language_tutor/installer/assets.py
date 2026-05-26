"""Bundled plugin/profile asset resolution.

`tutor init` writes managed registration files derived from assets bundled with
the `lingo-loop` distribution. Each provider profile declares a host-package
directory (e.g. ``openclaw-plugin``, ``.claude-plugin``) that lives at the
repository root in editable installs and under
``language_tutor/_assets/<host-package>/`` in the wheel.

Resolution order for the assets *root* (the parent of every host-package
directory):

1. Explicit override via ``LANGUAGE_TUTOR_BUNDLED_ASSETS`` env var (tests).
2. Editable / source install: repo root inferred from this module's location
   (``Path(__file__).parents[3]``), which contains ``.claude-plugin/``,
   ``.codex-plugin/``, ``openclaw-plugin/``, and ``hermes-profile/``.
3. Wheel install: ``importlib.resources.files("language_tutor") / "_assets"``
   (populated via Hatch ``force-include``).

``bundled_assets_root_for(host_package)`` returns the directory containing the
host-package's files; ``bundled_assets_root()`` returns the parent directory
(retained for back-compat with ``InstallerContext.bundled_assets_root``).
"""

from __future__ import annotations

import os
from importlib import resources
from pathlib import Path

_HOST_PACKAGE_SENTINELS: dict[str, str] = {
    ".claude-plugin": "plugin.json",
    ".codex-plugin": "plugin.json",
    "openclaw-plugin": "package.json",
    "hermes-profile": "distribution.yaml",
}


def _override_root() -> Path | None:
    override = os.environ.get("LANGUAGE_TUTOR_BUNDLED_ASSETS")
    if override:
        return Path(override).expanduser().resolve()
    return None


def _repo_root_candidate() -> Path:
    return Path(__file__).resolve().parents[3]


def _wheel_root_candidate() -> Path | None:
    try:
        return Path(str(resources.files("language_tutor") / "_assets"))
    except (ModuleNotFoundError, AttributeError):
        return None


def bundled_assets_root() -> Path:
    """Return the directory that contains every host-package directory.

    Editable installs return the repo root; wheel installs return
    ``language_tutor/_assets``. The presence of ``.claude-plugin/plugin.json``
    is used as the canonical sentinel.
    """

    override = _override_root()
    if override is not None:
        return override
    repo_root = _repo_root_candidate()
    if (repo_root / ".claude-plugin" / "plugin.json").exists():
        return repo_root
    wheel_root = _wheel_root_candidate()
    if wheel_root is not None and (wheel_root / ".claude-plugin" / "plugin.json").exists():
        return wheel_root
    return repo_root


def bundled_assets_root_for(host_package: str) -> Path:
    """Return the directory containing files for a single host-package.

    Probes both the editable repo root and the wheel ``_assets`` directory and
    returns whichever contains the host-package's sentinel file. Falls back to
    the editable root so callers can surface a clear missing-asset error.
    """

    override = _override_root()
    # Explicit override takes strict precedence (tests need to assert that a
    # missing bundled asset produces a packaging-defect BLOCKED state without
    # the resolver silently falling back to the editable repo root).
    if override is not None:
        return override / host_package
    sentinel = _HOST_PACKAGE_SENTINELS.get(host_package)
    candidates: list[Path] = [_repo_root_candidate() / host_package]
    wheel_root = _wheel_root_candidate()
    if wheel_root is not None:
        candidates.append(wheel_root / host_package)
    if sentinel is not None:
        for candidate in candidates:
            if (candidate / sentinel).exists():
                return candidate
    # Last-resort: editable repo root path (may not exist; callers handle that).
    return _repo_root_candidate() / host_package
