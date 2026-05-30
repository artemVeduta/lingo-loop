# Lingo Loop Package Installability Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make `lingo-loop==0.1.2` a complete installable package for Hermes and OpenClaw users by bundling runtime payloads, validating them through `tutor doctor`, repairing provider files idempotently, and replacing the OpenClaw empty-text stub with real `tutor` CLI invocation.

**Architecture:** Keep the Python tutor core host-independent. Add one small package-asset resolver for runtime payload checks, keep SQL migration ownership in the DAL, keep provider install/repair in `installer/providers/*`, and keep OpenClaw host execution in the Node plugin boundary. Homelab Dockerfiles, Compose files, and service entrypoints are explicitly out of scope for this plan.

**Tech Stack:** Python 3.12, Click, Pydantic v2, stdlib `sqlite3`, Hatchling wheel `force-include`, pytest, pyright, ruff, Node.js 22, TypeScript ESM, OpenClaw plugin package metadata, `uv`, `rtk`.

---

## Scope

Implement only in `/Users/artem.veduta/python/language-tutor` (the `lingo-loop` package repo).

Do not edit `/Users/artem.veduta/proj/homelab/compute/services/*` in this plan. Homelab image consumption of `lingo-loop==0.1.2` is a separate plan after this package release exists.

All relative file paths below are relative to:

```bash
/Users/artem.veduta/python/language-tutor
```

## File Structure

| File | Responsibility | Action |
|------|----------------|--------|
| `src/language_tutor/package_assets.py` | Generic source/wheel payload root resolver plus required runtime asset lists | Create |
| `src/language_tutor/installer/assets.py` | Host installer asset resolver; delegates root selection to generic package resolver | Modify |
| `src/language_tutor/dal/migrations.py` | Load migrations from source or wheel payload; fail with exact missing filenames | Modify |
| `src/language_tutor/health.py` | `tutor doctor` runtime/package/provider payload checks | Modify |
| `src/language_tutor/installer/providers/openclaw.py` | Declared OpenClaw managed tree includes built runtime files | Modify |
| `openclaw-plugin/src/index.ts` | OpenClaw plugin invokes local `tutor` instead of returning empty stubs | Modify |
| `openclaw-plugin/package.json` | Package exports built JS/types and includes dist payload | Verify |
| `openclaw-plugin/dist/index.js` | Built OpenClaw runtime entry | Create via TypeScript build |
| `openclaw-plugin/dist/index.d.ts` | Built OpenClaw type declarations | Create via TypeScript build |
| `pyproject.toml` | Wheel force-includes migrations, skills, helper scripts, agent, CLI shim, and OpenClaw dist | Modify |
| `tests/unit/test_package_assets.py` | Unit coverage for package payload resolver | Create |
| `tests/unit/test_health.py` | Doctor validates runtime payloads and exact missing filenames | Modify |
| `tests/migration/test_migrations.py` | Migration loader fails when wheel/source payload omits SQL files | Modify |
| `tests/release/test_wheel_contents.py` | Wheel content gate covers runtime payloads plus provider files | Modify |
| `tests/packaging/test_openclaw_plugin_package.py` | OpenClaw plugin is non-stub and has built runtime entries | Modify |
| `tests/installer/test_bundled_tree.py` | Provider repair writes OpenClaw dist files idempotently | Modify |
| `tests/integration/test_tutor_init_cli.py` | Hermes/OpenClaw `tutor init` preserves learner state and unrelated files | Modify |
| `docs/install/hermes.md` | Clean `0.1.2` install path, fallback `v0.1.1`, state contract | Modify |
| `docs/install/openclaw.md` | Clean `0.1.2` install path, fallback `v0.1.1`, plugin install/enable path | Modify |
| `README.md` | Top-level package install flow reflects fixed package payload | Modify |
| `CHANGELOG.md` | Unreleased notes for package payload, doctor, OpenClaw runtime | Modify |

---

### Task 1: Add Generic Package Asset Resolver

**Files:**
- Create: `src/language_tutor/package_assets.py`
- Modify: `src/language_tutor/installer/assets.py`
- Test: `tests/unit/test_package_assets.py`

- [ ] **Step 1: Write failing resolver tests**

Create `tests/unit/test_package_assets.py`:

```python
from __future__ import annotations

from pathlib import Path

from language_tutor.package_assets import (
    REQUIRED_RUNTIME_PAYLOADS,
    missing_package_assets,
    package_assets_root,
    package_asset_path,
)


def test_package_assets_root_prefers_explicit_override(
    tmp_path: Path, monkeypatch
) -> None:  # type: ignore[no-untyped-def]
    root = tmp_path / "payload"
    root.mkdir()
    monkeypatch.setenv("LANGUAGE_TUTOR_BUNDLED_ASSETS", str(root))

    assert package_assets_root() == root.resolve()
    assert package_asset_path("migrations/001_initial.sql") == root.resolve() / "migrations/001_initial.sql"


def test_missing_package_assets_reports_exact_relative_names(
    tmp_path: Path, monkeypatch
) -> None:  # type: ignore[no-untyped-def]
    root = tmp_path / "payload"
    (root / "migrations").mkdir(parents=True)
    (root / "migrations" / "001_initial.sql").write_text("-- sql", encoding="utf-8")
    monkeypatch.setenv("LANGUAGE_TUTOR_BUNDLED_ASSETS", str(root))

    missing = missing_package_assets(
        (
            "migrations/001_initial.sql",
            "migrations/002_vocab_depth.sql",
            "skills/tutor-vocab/SKILL.md",
        )
    )

    assert missing == ("migrations/002_vocab_depth.sql", "skills/tutor-vocab/SKILL.md")


def test_required_runtime_payloads_cover_migrations_and_skill_helpers() -> None:
    assert "migrations/001_initial.sql" in REQUIRED_RUNTIME_PAYLOADS
    assert "migrations/004_sessions_checkpoints.sql" in REQUIRED_RUNTIME_PAYLOADS
    assert "skills/tutor-setup/SKILL.md" in REQUIRED_RUNTIME_PAYLOADS
    assert "skills/tutor-vocab/scripts/run.py" in REQUIRED_RUNTIME_PAYLOADS
    assert "skills/tutor-writing/scripts/run.py" in REQUIRED_RUNTIME_PAYLOADS
    assert "agents/tutor-judge.md" in REQUIRED_RUNTIME_PAYLOADS
    assert "bin/tutor" in REQUIRED_RUNTIME_PAYLOADS
```

- [ ] **Step 2: Run resolver tests to verify failure**

Run:

```bash
rtk uv run pytest tests/unit/test_package_assets.py -q
```

Expected: failure with `ModuleNotFoundError: No module named 'language_tutor.package_assets'`.

- [ ] **Step 3: Implement the resolver**

Create `src/language_tutor/package_assets.py`:

```python
"""Runtime payload resolution for source and wheel installs.

The package ships runtime files under ``language_tutor/_assets`` in wheels and
keeps the same relative paths at repository root in editable/source checkouts.
This module is host-neutral so DAL and health checks do not depend on installer
provider internals.
"""

from __future__ import annotations

import os
from importlib import resources
from pathlib import Path

REQUIRED_MIGRATION_FILES: tuple[str, ...] = (
    "migrations/001_initial.sql",
    "migrations/002_vocab_depth.sql",
    "migrations/003_progress_indexes.sql",
    "migrations/004_sessions_checkpoints.sql",
)

REQUIRED_SKILL_PAYLOAD_FILES: tuple[str, ...] = (
    "skills/tutor-setup/SKILL.md",
    "skills/tutor-vocab/SKILL.md",
    "skills/tutor-vocab/scripts/run.py",
    "skills/tutor-writing/SKILL.md",
    "skills/tutor-writing/scripts/run.py",
    "skills/tutor-progress/SKILL.md",
    "skills/tutor-progress/scripts/run.py",
    "skills/tutor-reading/SKILL.md",
    "skills/tutor-lesson/SKILL.md",
    "agents/tutor-judge.md",
    "bin/tutor",
)

REQUIRED_RUNTIME_PAYLOADS: tuple[str, ...] = (
    *REQUIRED_MIGRATION_FILES,
    *REQUIRED_SKILL_PAYLOAD_FILES,
)


def _override_root() -> Path | None:
    override = os.environ.get("LANGUAGE_TUTOR_BUNDLED_ASSETS")
    if override:
        return Path(override).expanduser().resolve()
    return None


def _source_root_candidate() -> Path:
    return Path(__file__).resolve().parents[2]


def _wheel_root_candidate() -> Path | None:
    try:
        return Path(str(resources.files("language_tutor") / "_assets"))
    except (ModuleNotFoundError, AttributeError):
        return None


def package_assets_root() -> Path:
    """Return the root containing package runtime payloads."""

    override = _override_root()
    if override is not None:
        return override

    source_root = _source_root_candidate()
    if (source_root / "migrations" / "001_initial.sql").exists():
        return source_root

    wheel_root = _wheel_root_candidate()
    if wheel_root is not None and (wheel_root / "migrations" / "001_initial.sql").exists():
        return wheel_root

    return source_root


def package_asset_path(relative_path: str) -> Path:
    """Resolve a package payload path by repository-relative name."""

    return package_assets_root() / relative_path


def missing_package_assets(
    relative_paths: tuple[str, ...] = REQUIRED_RUNTIME_PAYLOADS,
) -> tuple[str, ...]:
    """Return required payload filenames missing from the active package root."""

    root = package_assets_root()
    return tuple(rel for rel in relative_paths if not (root / rel).exists())
```

- [ ] **Step 4: Delegate installer root resolution to the generic resolver**

In `src/language_tutor/installer/assets.py`, replace the local override/source/wheel helpers with imports from `package_assets.py`. Keep the public installer functions unchanged:

```python
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
```

Keep the existing `bundled_assets_root_for()` implementation, but replace its calls to `_override_root()`, `_repo_root_candidate()`, and `_wheel_root_candidate()` with `root = package_assets_root()` and return `root / host_package` when the sentinel exists. Final helper body:

```python
def bundled_assets_root_for(host_package: str) -> Path:
    """Return the directory containing files for a single host-package."""

    root = package_assets_root()
    sentinel = _HOST_PACKAGE_SENTINELS.get(host_package)
    candidate = root / host_package
    if sentinel is None or (candidate / sentinel).exists():
        return candidate
    return candidate
```

- [ ] **Step 5: Run resolver and installer tests**

Run:

```bash
rtk uv run pytest tests/unit/test_package_assets.py tests/unit/test_installer_service.py tests/installer/test_bundled_tree.py -q
```

Expected: all selected tests pass.

- [ ] **Step 6: Commit**

```bash
rtk git add src/language_tutor/package_assets.py src/language_tutor/installer/assets.py tests/unit/test_package_assets.py
rtk git commit -m "feat: add package runtime asset resolver"
```

---

### Task 2: Load SQL Migrations From Packaged Payloads

**Files:**
- Modify: `src/language_tutor/dal/migrations.py`
- Modify: `tests/migration/test_migrations.py`

- [ ] **Step 1: Write failing migration payload test**

Append to `tests/migration/test_migrations.py`:

```python
import pytest

from language_tutor.dal.migrations import load_migrations, missing_migration_files
from language_tutor.errors import TutorError


def test_missing_packaged_migrations_fail_with_exact_names(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    payload_root = tmp_path / "_assets"
    (payload_root / "migrations").mkdir(parents=True)
    (payload_root / "migrations" / "001_initial.sql").write_text("-- sql", encoding="utf-8")
    monkeypatch.setenv("LANGUAGE_TUTOR_BUNDLED_ASSETS", str(payload_root))

    assert missing_migration_files() == (
        "migrations/002_vocab_depth.sql",
        "migrations/003_progress_indexes.sql",
        "migrations/004_sessions_checkpoints.sql",
    )

    with pytest.raises(TutorError) as excinfo:
        load_migrations()

    assert excinfo.value.code == "missing_migrations"
    assert "002_vocab_depth.sql" in excinfo.value.message
    assert "004_sessions_checkpoints.sql" in excinfo.value.repair_hint
```

- [ ] **Step 2: Run migration test to verify failure**

Run:

```bash
rtk uv run pytest tests/migration/test_migrations.py::test_missing_packaged_migrations_fail_with_exact_names -q
```

Expected: failure because `missing_migration_files` is not defined.

- [ ] **Step 3: Implement packaged migration loading**

Update `src/language_tutor/dal/migrations.py`.

Add import:

```python
from language_tutor.package_assets import REQUIRED_MIGRATION_FILES, package_assets_root
```

Replace `migration_dir()` with:

```python
def migration_dir() -> Path:
    return package_assets_root() / "migrations"
```

Add helper:

```python
def missing_migration_files(root: Path | None = None) -> tuple[str, ...]:
    base = root or package_assets_root()
    return tuple(rel for rel in REQUIRED_MIGRATION_FILES if not (base / rel).exists())
```

Add the missing-file guard at the start of `load_migrations()`:

```python
def load_migrations(root: Path | None = None) -> list[Migration]:
    if root is None:
        missing = missing_migration_files()
        if missing:
            joined = ", ".join(missing)
            raise TutorError(
                "missing_migrations",
                f"SQL migration file(s) missing from lingo-loop package: {joined}",
                f"Reinstall lingo-loop from a fixed package containing: {joined}.",
            )
        directory = migration_dir()
    else:
        directory = root
    migrations: list[Migration] = []
    for path in sorted(directory.glob("*.sql")):
        version_text, name = path.stem.split("_", 1)
        sql = path.read_text(encoding="utf-8")
        migrations.append(
            Migration(
                version=int(version_text),
                name=name,
                sql=sql,
                checksum=hashlib.sha256(sql.encode("utf-8")).hexdigest(),
            )
        )
    return migrations
```

- [ ] **Step 4: Run migration tests**

Run:

```bash
rtk uv run pytest tests/migration/test_migrations.py tests/migration/test_004_sessions_checkpoints.py -q
```

Expected: all selected tests pass; existing migration order remains `[1, 2, 3, 4]`.

- [ ] **Step 5: Commit**

```bash
rtk git add src/language_tutor/dal/migrations.py tests/migration/test_migrations.py
rtk git commit -m "fix: load migrations from packaged runtime payload"
```

---

### Task 3: Make `tutor doctor` Validate Runtime Payloads

**Files:**
- Modify: `src/language_tutor/health.py`
- Modify: `tests/unit/test_health.py`
- Modify: `tests/adapter_contract/test_doctor_cli.py`

- [ ] **Step 1: Update health tests for package assets**

In `tests/unit/test_health.py`, add helper:

```python
def _make_runtime_payload(root: Path) -> None:
    for rel in (
        "migrations/001_initial.sql",
        "migrations/002_vocab_depth.sql",
        "migrations/003_progress_indexes.sql",
        "migrations/004_sessions_checkpoints.sql",
        "skills/tutor-setup/SKILL.md",
        "skills/tutor-vocab/SKILL.md",
        "skills/tutor-vocab/scripts/run.py",
        "skills/tutor-writing/SKILL.md",
        "skills/tutor-writing/scripts/run.py",
        "skills/tutor-progress/SKILL.md",
        "skills/tutor-progress/scripts/run.py",
        "skills/tutor-reading/SKILL.md",
        "skills/tutor-lesson/SKILL.md",
        "agents/tutor-judge.md",
        "bin/tutor",
    ):
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("-- payload\n" if rel.endswith(".sql") else "# payload\n", encoding="utf-8")
```

In `test_wheel_install_manifest_ok_source_checks_na`, call `_make_runtime_payload(assets)` after writing `.claude-plugin/plugin.json`.

Add new test:

```python
def test_doctor_fails_with_exact_missing_runtime_asset(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fake_repo = tmp_path / "site-packages-adjacent"
    fake_repo.mkdir()
    assets = tmp_path / "_assets"
    (assets / ".claude-plugin").mkdir(parents=True)
    (assets / ".claude-plugin" / "plugin.json").write_text("{}", encoding="utf-8")
    _make_runtime_payload(assets)
    (assets / "migrations" / "004_sessions_checkpoints.sql").unlink()
    monkeypatch.setenv("LANGUAGE_TUTOR_BUNDLED_ASSETS", str(assets))

    report = doctor(_paths(tmp_path), fake_repo)
    checks = {c.name: c for c in report.checks}

    assert checks["runtime_payload:migrations/004_sessions_checkpoints.sql"].status == "fail"
    assert "migrations/004_sessions_checkpoints.sql" in checks[
        "runtime_payload:migrations/004_sessions_checkpoints.sql"
    ].repair_hint
    assert report.status == "fail"
```

- [ ] **Step 2: Run doctor test to verify failure**

Run:

```bash
rtk uv run pytest tests/unit/test_health.py::test_doctor_fails_with_exact_missing_runtime_asset -q
```

Expected: failure because doctor does not emit `runtime_payload:*` checks yet.

- [ ] **Step 3: Implement runtime payload checks in doctor**

In `src/language_tutor/health.py`, add imports:

```python
from language_tutor.package_assets import REQUIRED_RUNTIME_PAYLOADS, package_asset_path
```

After the manifest check, add:

```python
    for rel in REQUIRED_RUNTIME_PAYLOADS:
        path = package_asset_path(rel)
        checks.append(
            DoctorCheck(
                name=f"runtime_payload:{rel}",
                status="ok" if path.exists() else "fail",
                repair_hint=f"Reinstall lingo-loop; packaged runtime payload missing: {rel}.",
            )
        )
```

Keep the existing source-only Claude checks as `n/a` for non-editable wheels.

Update the SQLite migration exception handling to preserve missing filenames:

```python
    except TutorError as exc:
        checks.append(
            DoctorCheck(
                name="sqlite_migrations",
                status="fail",
                repair_hint=exc.repair_hint,
            )
        )
```

Keep the generic `except Exception` block after the `TutorError` block:

```python
    except Exception:
        checks.append(
            DoctorCheck(
                name="sqlite_migrations",
                status="fail",
                repair_hint="Repair SQLite file or migration records.",
            )
        )
```

- [ ] **Step 4: Assert CLI report still has no learner mutation**

In `tests/adapter_contract/test_doctor_cli.py`, extend the existing test:

```python
def test_doctor_reports_no_mutation(runner) -> None:  # type: ignore[no-untyped-def]
    report = invoke_json(runner, ["doctor", "--json"])
    assert report["learner_data_changed"] is False
    assert report["status"] == "ok"
    names = {check["name"] for check in report["checks"]}  # type: ignore[index]
    assert "runtime_payload:migrations/001_initial.sql" in names
    assert "runtime_payload:skills/tutor-vocab/SKILL.md" in names
```

- [ ] **Step 5: Run health and doctor CLI tests**

Run:

```bash
rtk uv run pytest tests/unit/test_health.py tests/adapter_contract/test_doctor_cli.py -q
```

Expected: all selected tests pass.

- [ ] **Step 6: Commit**

```bash
rtk git add src/language_tutor/health.py tests/unit/test_health.py tests/adapter_contract/test_doctor_cli.py
rtk git commit -m "fix: make doctor validate packaged runtime payloads"
```

---

### Task 4: Bundle Runtime Payloads Into The Wheel

**Files:**
- Modify: `pyproject.toml`
- Modify: `tests/release/test_wheel_contents.py`

- [ ] **Step 1: Extend the wheel content test before editing packaging**

Modify `tests/release/test_wheel_contents.py` imports:

```python
from language_tutor.package_assets import REQUIRED_RUNTIME_PAYLOADS
```

Add test:

```python
def test_wheel_bundles_runtime_payloads(built_wheel: Path) -> None:
    with zipfile.ZipFile(built_wheel) as zf:
        names = set(zf.namelist())
    expected = [f"language_tutor/_assets/{rel}" for rel in REQUIRED_RUNTIME_PAYLOADS]
    missing = [path for path in expected if path not in names]
    assert not missing, (
        "Wheel is missing runtime payload files:\n  - " + "\n  - ".join(missing)
    )
```

- [ ] **Step 2: Run release wheel test to verify failure**

Run:

```bash
rtk uv run pytest tests/release/test_wheel_contents.py::test_wheel_bundles_runtime_payloads --no-cov -q
```

Expected: failure listing missing `language_tutor/_assets/migrations/*.sql` and `language_tutor/_assets/skills/*`.

- [ ] **Step 3: Add wheel force-includes**

In `pyproject.toml`, append these lines under `[tool.hatch.build.targets.wheel.force-include]`:

```toml
"migrations/001_initial.sql" = "language_tutor/_assets/migrations/001_initial.sql"
"migrations/002_vocab_depth.sql" = "language_tutor/_assets/migrations/002_vocab_depth.sql"
"migrations/003_progress_indexes.sql" = "language_tutor/_assets/migrations/003_progress_indexes.sql"
"migrations/004_sessions_checkpoints.sql" = "language_tutor/_assets/migrations/004_sessions_checkpoints.sql"
"skills/tutor-setup/SKILL.md" = "language_tutor/_assets/skills/tutor-setup/SKILL.md"
"skills/tutor-vocab/SKILL.md" = "language_tutor/_assets/skills/tutor-vocab/SKILL.md"
"skills/tutor-vocab/scripts/run.py" = "language_tutor/_assets/skills/tutor-vocab/scripts/run.py"
"skills/tutor-writing/SKILL.md" = "language_tutor/_assets/skills/tutor-writing/SKILL.md"
"skills/tutor-writing/scripts/run.py" = "language_tutor/_assets/skills/tutor-writing/scripts/run.py"
"skills/tutor-progress/SKILL.md" = "language_tutor/_assets/skills/tutor-progress/SKILL.md"
"skills/tutor-progress/scripts/run.py" = "language_tutor/_assets/skills/tutor-progress/scripts/run.py"
"skills/tutor-reading/SKILL.md" = "language_tutor/_assets/skills/tutor-reading/SKILL.md"
"skills/tutor-lesson/SKILL.md" = "language_tutor/_assets/skills/tutor-lesson/SKILL.md"
"agents/tutor-judge.md" = "language_tutor/_assets/agents/tutor-judge.md"
"bin/tutor" = "language_tutor/_assets/bin/tutor"
```

- [ ] **Step 4: Run wheel content tests**

Run:

```bash
rtk uv run pytest tests/release/test_wheel_contents.py --no-cov -q
```

Expected: both wheel content tests pass.

- [ ] **Step 5: Commit**

```bash
rtk git add pyproject.toml tests/release/test_wheel_contents.py
rtk git commit -m "fix: bundle runtime payloads in wheel"
```

---

### Task 5: Include Built OpenClaw Runtime In Provider Package

**Files:**
- Modify: `src/language_tutor/installer/providers/openclaw.py`
- Modify: `tests/packaging/test_openclaw_plugin_package.py`
- Modify: `tests/installer/test_bundled_tree.py`
- Modify: `pyproject.toml`

- [ ] **Step 1: Add packaging tests for built OpenClaw runtime**

Append to `tests/packaging/test_openclaw_plugin_package.py`:

```python
def test_openclaw_dist_entry_points_are_committed() -> None:
    _skip_if_absent(OPENCLAW_ROOT / "dist" / "index.js")
    _skip_if_absent(OPENCLAW_ROOT / "dist" / "index.d.ts")
    js_text = (OPENCLAW_ROOT / "dist" / "index.js").read_text(encoding="utf-8")
    dts_text = (OPENCLAW_ROOT / "dist" / "index.d.ts").read_text(encoding="utf-8")
    assert "language_tutor.boot_context" in js_text
    assert "language_tutor.text_exercise" in js_text
    assert "declare" in dts_text or "export" in dts_text


def test_openclaw_source_is_not_empty_text_stub() -> None:
    entry = OPENCLAW_ROOT / "src" / "index.ts"
    _skip_if_absent(entry)
    text = entry.read_text(encoding="utf-8")
    assert 'text: ""' not in text
    assert "execFile" in text
    assert "session-start" in text
```

- [ ] **Step 2: Run OpenClaw packaging tests to verify failure**

Run:

```bash
rtk uv run pytest tests/packaging/test_openclaw_plugin_package.py::test_openclaw_dist_entry_points_are_committed tests/packaging/test_openclaw_plugin_package.py::test_openclaw_source_is_not_empty_text_stub -q
```

Expected: failure because `openclaw-plugin/dist/index.js` does not exist and `src/index.ts` still contains `text: ""`.

- [ ] **Step 3: Declare dist files in provider installer**

Update `src/language_tutor/installer/providers/openclaw.py` file list:

```python
        files=(
            "package.json",
            "openclaw.plugin.json",
            "tsconfig.json",
            "src/index.ts",
            "dist/index.js",
            "dist/index.d.ts",
        ),
```

- [ ] **Step 4: Add dist force-includes**

In `pyproject.toml`, add:

```toml
"openclaw-plugin/dist/index.js" = "language_tutor/_assets/openclaw-plugin/dist/index.js"
"openclaw-plugin/dist/index.d.ts" = "language_tutor/_assets/openclaw-plugin/dist/index.d.ts"
```

- [ ] **Step 5: Update bundled-tree tests to expect dist files**

In `tests/installer/test_bundled_tree.py`, extend `test_openclaw_profile_declares_full_bundled_tree()`:

```python
    assert "dist/index.js" in declared
    assert "dist/index.d.ts" in declared
```

- [ ] **Step 6: Run selected tests to verify they still fail only on missing dist/stub**

Run:

```bash
rtk uv run pytest tests/installer/test_bundled_tree.py::test_openclaw_profile_declares_full_bundled_tree tests/packaging/test_openclaw_plugin_package.py -q
```

Expected: profile declaration assertion passes; packaging still fails until Task 6 builds non-stub `dist`.

- [ ] **Step 7: Commit provider declaration and tests**

```bash
rtk git add src/language_tutor/installer/providers/openclaw.py tests/packaging/test_openclaw_plugin_package.py tests/installer/test_bundled_tree.py pyproject.toml
rtk git commit -m "test: require built openclaw runtime payload"
```

---

### Task 6: Replace OpenClaw Empty Stub With Tutor CLI Invocation

**Files:**
- Modify: `openclaw-plugin/src/index.ts`
- Create: `openclaw-plugin/dist/index.js`
- Create: `openclaw-plugin/dist/index.d.ts`

- [ ] **Step 1: Replace OpenClaw plugin source**

Overwrite `openclaw-plugin/src/index.ts` with:

```typescript
// Language Tutor plugin entry for the OpenClaw host.
//
// The plugin delegates stateful language-tutor behavior to the installed
// `tutor` CLI. The Python package owns pedagogy, persistence, rendering, and
// validation. This OpenClaw boundary only validates host tool parameters and
// executes an allowlisted local command.

import { execFile } from "node:child_process";
import { promisify } from "node:util";

import { defineToolPlugin } from "openclaw/plugin-sdk/tool-plugin";
import { Type } from "typebox";

const execFileAsync = promisify(execFile);
const TUTOR_BIN = process.env.LANGUAGE_TUTOR_TUTOR_BIN ?? "tutor";
const MAX_STDOUT_BYTES = 1024 * 1024;

const ALLOWED_COMMAND_ROOTS = new Set([
  "session-start",
  "checkpoint",
  "boot-context",
  "setup",
  "vocab",
  "writing",
  "reading",
  "lesson",
  "progress",
  "render",
  "host",
  "doctor",
]);

type JsonObject = Record<string, unknown>;

async function runTutor(command: string[], payload?: JsonObject): Promise<unknown> {
  if (command.length === 0 || !ALLOWED_COMMAND_ROOTS.has(command[0])) {
    throw new Error(`Unsupported tutor command: ${command.join(" ")}`);
  }

  const args = payload === undefined ? [...command] : [...command, JSON.stringify(payload)];
  const { stdout } = await execFileAsync(TUTOR_BIN, args, {
    env: process.env,
    maxBuffer: MAX_STDOUT_BYTES,
  });
  return JSON.parse(stdout);
}

export default defineToolPlugin({
  id: "language-tutor",
  name: "Language Tutor",
  description:
    "Text-only language tutor adapter for OpenClaw. Builds boot context on the first tutor message and exposes core text-modality tutor tools.",
  tools: (tool) => [
    tool({
      name: "language_tutor.boot_context",
      description:
        "Start or resume OpenClaw tutor context by invoking tutor session-start.",
      parameters: Type.Object({
        hostConversationId: Type.Optional(Type.String()),
      }),
      async execute(params) {
        return runTutor(["session-start", "--json"], {
          host: "openclaw",
          host_conversation_id: params.hostConversationId,
        });
      },
    }),
    tool({
      name: "language_tutor.text_exercise",
      description:
        "Invoke an allowlisted text-only tutor CLI command with an optional JSON payload.",
      parameters: Type.Object({
        command: Type.Array(Type.String()),
        payload: Type.Optional(Type.Record(Type.String(), Type.Unknown())),
      }),
      async execute(params) {
        return runTutor(params.command, params.payload as JsonObject | undefined);
      },
    }),
    tool({
      name: "language_tutor.run_cli",
      description:
        "Invoke an allowlisted local tutor CLI command. Binary-dependent and side-effectful; opt-in only.",
      optional: true,
      parameters: Type.Object({
        command: Type.Array(Type.String()),
        payload: Type.Optional(Type.Record(Type.String(), Type.Unknown())),
      }),
      async execute(params) {
        return runTutor(params.command, params.payload as JsonObject | undefined);
      },
    }),
  ],
});
```

- [ ] **Step 2: Install OpenClaw plugin dependencies**

Run:

```bash
rtk npm --prefix openclaw-plugin install
```

Expected: `node_modules` is created under `openclaw-plugin/`. If npm creates `openclaw-plugin/package-lock.json`, remove it after the build because this package does not currently track an npm lockfile.

- [ ] **Step 3: Build dist files**

Run:

```bash
rtk npm --prefix openclaw-plugin run build
```

Expected: TypeScript build exits 0 and creates:

```text
openclaw-plugin/dist/index.js
openclaw-plugin/dist/index.d.ts
```

- [ ] **Step 4: Verify source and dist are non-stub**

Run:

```bash
rtk rg -n 'text: ""|sections: \\[\\]|execFile|session-start|language_tutor.boot_context' openclaw-plugin/src openclaw-plugin/dist
```

Expected: no `text: ""` match, no `sections: []` match, and matches for `execFile`, `session-start`, and `language_tutor.boot_context`.

- [ ] **Step 5: Run OpenClaw packaging tests**

Run:

```bash
rtk uv run pytest tests/packaging/test_openclaw_plugin_package.py tests/installer/test_bundled_tree.py -q
```

Expected: all selected tests pass.

- [ ] **Step 6: Commit**

```bash
rtk git add openclaw-plugin/src/index.ts openclaw-plugin/dist/index.js openclaw-plugin/dist/index.d.ts
rtk git commit -m "fix(openclaw): invoke tutor cli from plugin runtime"
```

---

### Task 7: Prove Provider Init Is Idempotent And Preserves User State

**Files:**
- Modify: `tests/integration/test_tutor_init_cli.py`

- [ ] **Step 1: Add provider preservation tests**

Append to `tests/integration/test_tutor_init_cli.py`:

```python
def test_hermes_init_preserves_learner_state_and_unrelated_files(
    fake_clis: dict[str, str],
    fake_home: Path,
    no_tty: None,
    tutor_home: Path,
) -> None:
    del fake_clis, no_tty
    (fake_home / ".hermes" / "local.env").write_text(
        "ANTHROPIC_API_KEY=secret\n", encoding="utf-8"
    )
    runner = CliRunner()

    setup_result = runner.invoke(
        main,
        [
            "setup",
            "write",
            "--json",
            '{"profile":{"native_language":"en","target_language":"uk"},"preferences":{}}',
        ],
    )
    assert setup_result.exit_code == 0, setup_result.output

    first = runner.invoke(main, ["init", "--provider", "hermes", "--yes", "--json"])
    second = runner.invoke(main, ["init", "--provider", "hermes", "--yes", "--json"])

    assert first.exit_code == 0, first.output
    assert second.exit_code == 0, second.output
    assert (tutor_home / "config" / "profile.yaml").exists()
    assert (fake_home / ".hermes" / "local.env").read_text(encoding="utf-8") == "ANTHROPIC_API_KEY=secret\n"
    assert "ANTHROPIC_API_KEY" not in (
        fake_home / ".hermes" / "profiles" / "lingo-loop" / "distribution.yaml"
    ).read_text(encoding="utf-8")


def test_openclaw_init_preserves_learner_state_and_unrelated_files(
    fake_clis: dict[str, str],
    fake_home: Path,
    no_tty: None,
    tutor_home: Path,
) -> None:
    del fake_clis, no_tty
    (fake_home / ".openclaw" / "settings.json").write_text(
        '{"theme":"dark"}\n', encoding="utf-8"
    )
    runner = CliRunner()

    setup_result = runner.invoke(
        main,
        [
            "setup",
            "write",
            "--json",
            '{"profile":{"native_language":"en","target_language":"uk"},"preferences":{}}',
        ],
    )
    assert setup_result.exit_code == 0, setup_result.output

    first = runner.invoke(main, ["init", "--provider", "openclaw", "--yes", "--json"])
    second = runner.invoke(main, ["init", "--provider", "openclaw", "--yes", "--json"])

    assert first.exit_code == 0, first.output
    assert second.exit_code == 0, second.output
    assert (tutor_home / "config" / "profile.yaml").exists()
    assert (fake_home / ".openclaw" / "settings.json").read_text(encoding="utf-8") == '{"theme":"dark"}\n'
    assert (fake_home / ".openclaw" / "plugins" / "lingo-loop" / "dist" / "index.js").exists()
```

`tests/integration/test_tutor_init_cli.py` already imports `Path`, `pytest`, `CliRunner`, and `main`; keep those imports.


- [ ] **Step 2: Run provider preservation tests**

Run:

```bash
rtk uv run pytest tests/integration/test_tutor_init_cli.py::test_hermes_init_preserves_learner_state_and_unrelated_files tests/integration/test_tutor_init_cli.py::test_openclaw_init_preserves_learner_state_and_unrelated_files -q
```

Expected: both tests pass through the existing `fake_clis`, `fake_home`, and `no_tty` seams.

- [ ] **Step 3: Run full init CLI integration file**

Run:

```bash
rtk uv run pytest tests/integration/test_tutor_init_cli.py -q
```

Expected: all tests in the file pass.

- [ ] **Step 4: Commit**

```bash
rtk git add tests/integration/test_tutor_init_cli.py
rtk git commit -m "test: prove provider init preserves tutor state"
```

---

### Task 8: Update Public Install Docs For `0.1.2`

**Files:**
- Modify: `README.md`
- Modify: `docs/install/hermes.md`
- Modify: `docs/install/openclaw.md`
- Modify: `CHANGELOG.md`

- [ ] **Step 1: Update README install snippet**

In `README.md`, ensure the first install snippet uses the fixed package version:

```bash
uv tool install lingo-loop==0.1.2
tutor doctor --json
tutor init
```

Add fallback text near the install snippet:

````markdown
If `0.1.2` has not propagated to your package index yet, install the last source tag fallback:

```bash
uv tool install "git+https://github.com/artemVeduta/lingo-loop@v0.1.1"
```
````

- [ ] **Step 2: Update Hermes install doc**

In `docs/install/hermes.md`, replace the Step 0 command block with:

```bash
uv tool install lingo-loop==0.1.2
tutor doctor --json
tutor init --provider hermes --yes

# Source tag fallback until the fixed package is available:
# uv tool install "git+https://github.com/artemVeduta/lingo-loop@v0.1.1"
```

Add state contract text after Step 1:

```markdown
`LANGUAGE_TUTOR_HOME` overrides the tutor config, data, and state roots. For a Hermes container or service account, set `LANGUAGE_TUTOR_HOME=/home/hermes/.tutor`; for a normal CLI install, omit it to use platform user directories.
```

- [ ] **Step 3: Update OpenClaw install doc**

In `docs/install/openclaw.md`, replace the Step 0 command block with:

```bash
uv tool install lingo-loop==0.1.2
tutor doctor --json
tutor init --provider openclaw --yes
openclaw plugins install ~/.openclaw/plugins/lingo-loop --force
openclaw plugins enable language-tutor
openclaw plugins inspect language-tutor --runtime --json

# Source tag fallback until the fixed package is available:
# uv tool install "git+https://github.com/artemVeduta/lingo-loop@v0.1.1"
```

Add state contract text after the command block:

```markdown
`LANGUAGE_TUTOR_HOME` overrides the tutor config, data, and state roots. For an OpenClaw container or service account, set `LANGUAGE_TUTOR_HOME=/home/node/.tutor`; for a normal CLI install, omit it to use platform user directories.
```

- [ ] **Step 4: Add changelog entries**

Under `CHANGELOG.md` `[Unreleased]`, add:

```markdown
### Added

- Wheel runtime payload now includes SQL migrations, tutor skill markdown, skill helper scripts, the tutor judge agent, and the CLI shim so installed packages can validate and run without a source checkout.
- OpenClaw wheel payload now includes the built `dist/index.js` and `dist/index.d.ts` plugin runtime entries.

### Changed

- `tutor doctor --json` validates packaged runtime payloads and reports exact missing filenames with reinstall hints.
- OpenClaw plugin tools now invoke the local `tutor` CLI through an allowlisted command boundary instead of returning empty placeholder text.

### Fixed

- Wheel installs no longer pass `tutor doctor --json` while silently lacking SQL migration files needed for the first real tutor session.
```

If `[Unreleased]` already contains these headings, append the bullets under the existing headings instead of duplicating headings.

- [ ] **Step 5: Run docs tests**

Run:

```bash
rtk uv run pytest tests/docs/test_install_docs.py -q
```

Expected: docs tests pass. If the docs test rejects new `language-tutor` mentions, keep every `language-tutor` line paired with `lingo-loop` contrast context.

- [ ] **Step 6: Commit**

```bash
rtk git add README.md docs/install/hermes.md docs/install/openclaw.md CHANGELOG.md
rtk git commit -m "docs: document fixed lingo-loop package install path"
```

---

### Task 9: Verify Built Wheel In A Clean Tool Environment

**Files:**
- No source edits expected

- [ ] **Step 1: Run package gates**

Run:

```bash
rtk uv run pytest tests/unit/test_package_assets.py tests/unit/test_health.py tests/migration/test_migrations.py tests/release/test_wheel_contents.py tests/packaging/test_openclaw_plugin_package.py tests/installer/test_bundled_tree.py tests/integration/test_tutor_init_cli.py --no-cov
```

Expected: all selected tests pass.

- [ ] **Step 2: Run static gates**

Run:

```bash
rtk uv run pyright
rtk uv run ruff check .
```

Expected: `pyright` reports `0 errors`; `ruff` exits 0.

- [ ] **Step 3: Build wheel**

Run:

```bash
rtk uv build --wheel --out-dir dist-smoke
```

Expected: one wheel exists under `dist-smoke/`, with name matching current project version until release-cut updates it.

- [ ] **Step 4: Inspect wheel payload names**

Run:

```bash
rtk bash -lc 'python - <<'"'"'PY'"'"'
import zipfile
from pathlib import Path
wheel = sorted(Path("dist-smoke").glob("lingo_loop-*.whl"))[-1]
with zipfile.ZipFile(wheel) as zf:
    names = set(zf.namelist())
required = [
    "language_tutor/_assets/migrations/001_initial.sql",
    "language_tutor/_assets/migrations/004_sessions_checkpoints.sql",
    "language_tutor/_assets/skills/tutor-vocab/SKILL.md",
    "language_tutor/_assets/skills/tutor-writing/scripts/run.py",
    "language_tutor/_assets/openclaw-plugin/dist/index.js",
    "language_tutor/_assets/openclaw-plugin/dist/index.d.ts",
]
missing = [name for name in required if name not in names]
if missing:
    raise SystemExit("MISSING " + ", ".join(missing))
print("WHEEL_PAYLOAD_OK")
PY'
```

Expected:

```text
WHEEL_PAYLOAD_OK
```

- [ ] **Step 5: Clean install built wheel and run doctor**

Run:

```bash
rtk bash -lc 'set -euo pipefail
tmp="$(mktemp -d)"
wheel="$(ls dist-smoke/lingo_loop-*.whl | tail -n 1)"
uv venv --python 3.12 "$tmp/venv" >/dev/null
"$tmp/venv/bin/pip" install "$wheel" >/dev/null
LANGUAGE_TUTOR_HOME="$tmp/tutor-home" "$tmp/venv/bin/tutor" doctor --json > "$tmp/doctor.json"
python - "$tmp/doctor.json" <<'"'"'PY'"'"'
import json, sys
data = json.load(open(sys.argv[1], encoding="utf-8"))
assert data["status"] == "ok", data
assert data["learner_data_changed"] is False, data
names = {c["name"] for c in data["checks"]}
assert "runtime_payload:migrations/001_initial.sql" in names
assert "runtime_payload:skills/tutor-vocab/SKILL.md" in names
print("CLEAN_DOCTOR_OK")
PY'
```

Expected:

```text
CLEAN_DOCTOR_OK
```

- [ ] **Step 6: Clean local generated directories**

Run:

```bash
rtk git status --short
```

Expected: no uncommitted changes except generated `dist-smoke/` and `openclaw-plugin/node_modules/` if they are untracked. Remove generated local-only directories:

```bash
rtk rm -rf dist-smoke openclaw-plugin/node_modules
```

Expected after cleanup:

```bash
rtk git status --short
```

Only intentional source/docs/test changes from earlier commits are absent because they were already committed.

---

### Task 10: Release `0.1.2`

**Files:**
- Modify: `pyproject.toml`
- Modify: `CHANGELOG.md`

- [ ] **Step 1: Confirm version target**

Run:

```bash
rtk rg -n 'version = "0.1.1"|lingo-loop==0.1.2|v0.1.1' pyproject.toml README.md docs/install CHANGELOG.md
```

Expected: `pyproject.toml` still shows `version = "0.1.1"` before release-cut, public install docs mention `lingo-loop==0.1.2`, and fallback docs mention `v0.1.1`.

- [ ] **Step 2: Bump package version for release branch**

Change `pyproject.toml`:

```toml
version = "0.1.2"
```

- [ ] **Step 3: Promote changelog**

Change the top of `CHANGELOG.md` so `[Unreleased]` is empty and the package payload notes move under the dated release:

```markdown
## [Unreleased]

### Added

### Changed

### Fixed

### Removed

## [0.1.2] - 2026-05-31

### Added

- Wheel runtime payload now includes SQL migrations, tutor skill markdown, skill helper scripts, the tutor judge agent, and the CLI shim so installed packages can validate and run without a source checkout.
- OpenClaw wheel payload now includes the built `dist/index.js` and `dist/index.d.ts` plugin runtime entries.

### Changed

- `tutor doctor --json` validates packaged runtime payloads and reports exact missing filenames with reinstall hints.
- OpenClaw plugin tools now invoke the local `tutor` CLI through an allowlisted command boundary instead of returning empty placeholder text.

### Fixed

- Wheel installs no longer pass `tutor doctor --json` while silently lacking SQL migration files needed for the first real tutor session.
```

Keep the existing `## [0.1.1] - 2026-05-30` section below this new section.

- [ ] **Step 4: Run release guards**

Run:

```bash
rtk ./scripts/version-guard.sh v0.1.2
rtk ./scripts/build-check.sh
```

Expected: both scripts exit 0; build-check runs tests/build validation as defined by the repository script.

- [ ] **Step 5: Commit release bump**

```bash
rtk git add pyproject.toml CHANGELOG.md
rtk git commit -m "chore(release): 0.1.2"
```

- [ ] **Step 6: Tag after merge to main**

After the release branch is merged to `main`, run from a clean `main` checkout:

```bash
rtk git tag -a v0.1.2 -m "release 0.1.2"
rtk git push origin v0.1.2
```

Expected: GitHub Actions publish workflow starts for tag `v0.1.2`.

- [ ] **Step 7: Verify published package**

After the publish workflow is green, run:

```bash
rtk uvx --refresh --from lingo-loop==0.1.2 tutor doctor --json
```

Expected: JSON includes:

```json
{
  "status": "ok",
  "learner_data_changed": false
}
```

Also run:

```bash
rtk uv tool install --force lingo-loop==0.1.2
rtk tutor init --provider hermes --dry-run --json
rtk tutor init --provider openclaw --dry-run --json
```

Expected: both dry-runs return valid JSON plans. A missing local Hermes/OpenClaw CLI or config root may return `blocked`; that is acceptable for dry-run if the repair hint names the missing host prerequisite and does not report a missing package payload.

---

## Self-Review

**Spec coverage:** Upstream package asset ownership, `LANGUAGE_TUTOR_HOME` state routing, provider repair idempotence, doctor verification, OpenClaw non-stub runtime behavior, package docs, and release verification are each covered by Tasks 1-10. Homelab Docker/Compose updates are intentionally excluded by user scope.

**Placeholder scan:** Plan uses concrete file paths, commands, expected outputs, and code blocks for each source/test/doc edit.

**Type/name consistency:** `REQUIRED_RUNTIME_PAYLOADS`, `missing_package_assets`, `package_assets_root`, `package_asset_path`, `missing_migration_files`, `runtime_payload:<rel>`, `LANGUAGE_TUTOR_HOME`, `lingo-loop==0.1.2`, and fallback tag `v0.1.1` are used consistently across tests, code, docs, and release steps.
