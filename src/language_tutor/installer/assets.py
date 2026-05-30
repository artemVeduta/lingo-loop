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

from pathlib import Path

from language_tutor.package_assets import package_assets_root

_HOST_PACKAGE_SENTINELS: dict[str, str] = {
    ".claude-plugin": "plugin.json",
    ".codex-plugin": "plugin.json",
    "openclaw-plugin": "package.json",
    "hermes-profile": "distribution.yaml",
}


def bundled_assets_root() -> Path:
    """Return the directory that contains every host-package directory."""

    return package_assets_root()


def bundled_assets_root_for(host_package: str) -> Path:
    """Return the directory containing files for a single host-package."""

    root = package_assets_root()
    return root / host_package
