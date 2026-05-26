"""Wheel bundles every file declared by every provider installer.

Per the `oss-distribution` spec scenario "Wheel bundles every file declared by
every provider installer", running `uv build` on a clean checkout MUST produce
a wheel that contains every file declared in each provider profile's bundled
tree under ``language_tutor/_assets/<host-package>/<relative-path>``.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

import pytest

from language_tutor.installer.providers.claude import ClaudeInstaller
from language_tutor.installer.providers.codex import CodexInstaller
from language_tutor.installer.providers.hermes import HermesInstaller
from language_tutor.installer.providers.openclaw import OpenClawInstaller

REPO_ROOT = Path(__file__).resolve().parents[2]

PROFILES = (
    ClaudeInstaller.profile,
    CodexInstaller.profile,
    HermesInstaller.profile,
    OpenClawInstaller.profile,
)


def _expected_wheel_paths() -> list[str]:
    paths: list[str] = []
    for profile in PROFILES:
        host_package = profile.bundled_assets_root_rel
        for rel in profile.files:
            paths.append(f"language_tutor/_assets/{host_package}/{rel}")
    return paths


@pytest.fixture(scope="module")
def built_wheel(tmp_path_factory: pytest.TempPathFactory) -> Path:
    if shutil.which("uv") is None:
        pytest.skip("uv not on PATH; cannot build wheel")
    out_dir = tmp_path_factory.mktemp("wheel-out")
    result = subprocess.run(
        ["uv", "build", "--wheel", "--out-dir", str(out_dir)],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        sys.stdout.write(result.stdout)
        sys.stderr.write(result.stderr)
        raise AssertionError(f"`uv build --wheel` failed (exit {result.returncode})")
    wheels = sorted(out_dir.glob("lingo_loop-*.whl"))
    assert wheels, f"no wheel produced in {out_dir}"
    return wheels[-1]


def test_wheel_bundles_every_provider_declared_file(built_wheel: Path) -> None:
    with zipfile.ZipFile(built_wheel) as zf:
        names = set(zf.namelist())
    missing = [path for path in _expected_wheel_paths() if path not in names]
    assert not missing, (
        "Wheel is missing provider-declared bundled-tree files:\n  - "
        + "\n  - ".join(missing)
    )
