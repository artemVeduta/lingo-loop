"""Distribution metadata MUST point at the correct project location.

The PyPI distribution name is `lingo-loop`. The Python module name remains
`language_tutor` (intentional for v0.1).
"""

from __future__ import annotations

import tomllib
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


def test_pyproject_distribution_name_is_lingo_loop() -> None:
    pyproject = REPO_ROOT / "pyproject.toml"
    data = tomllib.loads(pyproject.read_text(encoding="utf-8"))
    assert data["project"]["name"] == "lingo-loop"
