"""Bundled plugin/profile asset resolution.

`tutor init` writes managed registration files derived from assets bundled with
the `lingo-loop` distribution. Resolution order:

1. Explicit override via ``LANGUAGE_TUTOR_BUNDLED_ASSETS`` env var (tests).
2. Editable / source install: repo root inferred from this module's location
   (``Path(__file__).parents[3]``), which contains ``.claude-plugin/``,
   ``.codex-plugin/``, ``openclaw-plugin/``, and ``hermes-profile/``.
3. Wheel install: ``importlib.resources.files("language_tutor") / "_assets"``
   (populated via Hatch ``force-include``).

The resolved root is the parent of ``.claude-plugin``, ``hermes-profile`` etc.
"""

from __future__ import annotations

import os
from importlib import resources
from pathlib import Path


def bundled_assets_root() -> Path:
    override = os.environ.get("LANGUAGE_TUTOR_BUNDLED_ASSETS")
    if override:
        return Path(override).expanduser().resolve()
    repo_root = Path(__file__).resolve().parents[3]
    if (repo_root / ".claude-plugin" / "plugin.json").exists():
        return repo_root
    try:
        wheel_root = Path(str(resources.files("language_tutor") / "_assets"))
        if (wheel_root / ".claude-plugin" / "plugin.json").exists():
            return wheel_root
    except (ModuleNotFoundError, AttributeError):
        pass
    return repo_root
