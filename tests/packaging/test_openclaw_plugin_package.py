from __future__ import annotations

import json
from pathlib import Path

import pytest

from language_tutor.installer.providers.openclaw import OpenClawInstaller

REPO_ROOT = Path(__file__).resolve().parents[2]
OPENCLAW_ROOT = REPO_ROOT / "openclaw-plugin"


def _skip_if_absent(path: Path) -> None:
    if not path.exists():
        pytest.skip(f"{path.relative_to(REPO_ROOT)} not yet created by the OpenClaw subagent")


def test_openclaw_package_json_present_and_esm() -> None:
    pkg = OPENCLAW_ROOT / "package.json"
    _skip_if_absent(pkg)
    data = json.loads(pkg.read_text(encoding="utf-8"))
    assert data.get("type") == "module", "OpenClaw plugin must be ESM (type=module)"


def test_openclaw_plugin_manifest_present() -> None:
    _skip_if_absent(OPENCLAW_ROOT / "openclaw.plugin.json")
    data = json.loads((OPENCLAW_ROOT / "openclaw.plugin.json").read_text(encoding="utf-8"))
    assert json.dumps(data)


def test_openclaw_entry_point_is_typescript() -> None:
    entry = OPENCLAW_ROOT / "src" / "index.ts"
    _skip_if_absent(entry)
    text = entry.read_text(encoding="utf-8")
    assert "text: \"\"" not in text
    assert "execFile" in text
    assert "session-start" in text


def test_openclaw_built_artifacts_are_present_and_usable() -> None:
    dist_js = OPENCLAW_ROOT / "dist" / "index.js"
    dist_dts = OPENCLAW_ROOT / "dist" / "index.d.ts"
    _skip_if_absent(dist_js)
    _skip_if_absent(dist_dts)

    js_text = dist_js.read_text(encoding="utf-8")
    dts_text = dist_dts.read_text(encoding="utf-8")

    assert "language_tutor.boot_context" in js_text
    assert "language_tutor.text_exercise" in js_text
    assert "declare" in dts_text or "export" in dts_text


def test_openclaw_declares_built_runtime_files() -> None:
    manifest = json.loads((OPENCLAW_ROOT / "openclaw.plugin.json").read_text(encoding="utf-8"))
    entry = manifest.get("entry")
    assert entry == "dist/index.js"
    declared = set(OpenClawInstaller.profile.files)
    assert {
        "package.json",
        "openclaw.plugin.json",
        "tsconfig.json",
        "src/index.ts",
        "dist/index.js",
        "dist/index.d.ts",
    } <= declared


def test_openclaw_excludes_user_owned_data() -> None:
    _skip_if_absent(OPENCLAW_ROOT)
    offenders: list[str] = []
    for path in OPENCLAW_ROOT.rglob("*"):
        if "node_modules" in path.parts:
            continue
        if path.is_file() and path.suffix in (".env", ".sqlite", ".db", ".log"):
            offenders.append(str(path.relative_to(REPO_ROOT)))
    assert offenders == [], f"user-owned data in openclaw-plugin: {offenders}"
