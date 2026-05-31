# Lingo Loop Hermes Skill Hub Release Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Release `lingo-loop==0.1.3` with Hermes profile files and tutor skills installed from the packaged wheel into the Hermes profile root and Hermes skills hub.

**Architecture:** Keep `lingo-loop` as the single source of truth for Hermes-managed assets. Extend the existing provider installer asset model so Hermes can copy one package payload into two managed roots: the profile under the Hermes config root and the skill hub under the Hermes data root. Keep skills as thin CLI orchestration documents; the Python core remains the owner of pedagogy, persistence, validation, and rendering.

**Tech Stack:** Python 3.12, Click CLI, Pydantic models, Hatch/uv packaging, pytest, pyright, ruff, GitHub CLI (`gh`), GitHub Actions trusted publishing.

---

## Execution Rules

- At execution start, use `superpowers:using-git-worktrees` before touching code.
- Then use `superpowers:subagent-driven-development` task-by-task, or `superpowers:executing-plans` inline with checkpoints.
- Use `superpowers:verification-before-completion` before claiming the implementation is complete.
- Use `github:yeet` for the commit/push/draft PR phase.
- Any `SKILL.md` edit must be handled by a subagent that reads `/Users/artem.veduta/.claude/plugins/cache/claude-plugins-official/superpowers/5.1.0/skills/writing-skills` and reports the exact files changed.
- Commands below are upstream repo commands. Do not prefix them with local `rtk` in this plan.
- Scope is upstream only: `/Users/artem.veduta/python/language-tutor`. Homelab changes are release consumers and post-release verification, not implementation in this plan.

## Scope Check

The source design spans upstream `lingo-loop` and downstream homelab. This plan covers only the upstream release slice:

- HermesInstaller path resolution and managed asset copy/repair.
- Packaged Hermes profile and skill assets.
- Tutor skill command contract for wheel/container use.
- `tutor doctor --json` package asset checks.
- Tests, package metadata, release PR, tag `v0.1.3`, GitHub Actions inspection, and post-release upstream verification.

Downstream homelab Dockerfile, compose, entrypoint, Telegram shortcuts, compute rebuild, and Telegram smoke tests are not modified here. They are listed in the release handoff and post-release verification so the consuming repo can pick up `lingo-loop==0.1.3`.

## File Structure

### Source Files

- Modify: `src/language_tutor/installer/providers/base.py`
  - Responsibility: generic provider asset copy/verify/repair machinery.
  - Change: add explicit source-to-target asset specs while preserving existing provider profiles.
- Modify: `src/language_tutor/installer/providers/hermes.py`
  - Responsibility: Hermes-specific path resolution and asset declaration.
  - Change: declare profile assets plus Hermes skill hub assets; resolve `HERMES_HOME` to data root and profile root.
- Modify: `src/language_tutor/package_assets.py`
  - Responsibility: package payload inventory and package asset path resolution.
  - Change: add Hermes provider payloads required by provider init/doctor.
- Modify: `src/language_tutor/health.py`
  - Responsibility: `tutor doctor` health report.
  - Change: report missing Hermes provider payloads by exact relative path without creating learner sessions.
- Modify: `skills/tutor-setup/SKILL.md`
- Modify: `skills/tutor-vocab/SKILL.md`
- Modify: `skills/tutor-writing/SKILL.md`
- Modify: `skills/tutor-progress/SKILL.md`
- Modify: `skills/tutor-reading/SKILL.md`
- Modify: `skills/tutor-lesson/SKILL.md`
  - Responsibility: host-facing tutor flow orchestration.
  - Change: use installed `tutor ... --json` command rather than source-relative `bin/tutor ... --json`.
- Modify: `skills/tutor-vocab/scripts/run.py`
- Modify: `skills/tutor-writing/scripts/run.py`
- Modify: `skills/tutor-progress/scripts/run.py`
  - Responsibility: deterministic helper shims for skill flows.
  - Change: resolve `LANGUAGE_TUTOR_TUTOR_BIN`, defaulting to `tutor`.
- Modify: `hermes-profile/distribution.yaml`
  - Responsibility: Hermes profile metadata.
  - Change: remove dead `profile.skills: ../skills`; set release version to `0.1.3`.
- Modify: `docs/install/hermes.md`
  - Responsibility: upstream install documentation.
  - Change: document `0.1.3`, skill hub materialization, and no source `../skills` requirement.
- Modify: `pyproject.toml`
  - Responsibility: package version and wheel asset inventory.
  - Change: bump to `0.1.3`; keep force-included profile and runtime payloads aligned.
- Modify: `CHANGELOG.md`
  - Responsibility: release notes.
  - Change: add `0.1.3` release section.

### Test Files

- Create: `tests/installer/test_hermes_skill_hub.py`
  - Covers Hermes two-root path resolution, materialization, idempotence, drift repair, and exact missing asset hints.
- Modify: `tests/unit/test_installer_service.py`
  - Keeps provider smoke tests aligned with Hermes writing more than the profile manifest.
- Modify: `tests/release/test_wheel_contents.py`
  - Uses provider-declared asset specs so wheel checks include Hermes profile assets and skill hub sources.
- Create: `tests/packaging/test_hermes_skill_command_contract.py`
  - Ensures skills/scripts use `tutor` and `LANGUAGE_TUTOR_TUTOR_BIN`, not `bin/tutor`.
- Modify: `tests/packaging/test_hermes_profile_distribution.py`
  - Ensures distribution manifest no longer points at `../skills` and version matches package metadata.
- Modify: `tests/unit/test_package_assets.py`
  - Ensures Hermes provider payloads are part of package asset inventory.
- Modify: `tests/unit/test_health.py`
  - Ensures doctor reports missing Hermes provider payloads exactly and creates no session rows.
- Create: `tests/release/test_release_metadata.py`
  - Ensures release metadata says `0.1.3` and the changelog section exists.

---

## Task 0: Start Execution In An Isolated Worktree

**Files:**
- Read only: `/Users/artem.veduta/python/language-tutor`

- [ ] **Step 1: Load the worktree skill**

Use `superpowers:using-git-worktrees`.

- [ ] **Step 2: Inspect current branch and remotes**

Run:

```bash
git status --short
git branch --show-current
git remote -v
```

Expected: current branch and any dirty files are visible. Do not revert or overwrite files that are not part of this plan.

- [ ] **Step 3: Fetch main**

Run:

```bash
git fetch origin main --tags
```

Expected: command exits 0.

- [ ] **Step 4: Create the implementation worktree**

Run:

```bash
git worktree add ../language-tutor-hermes-skill-hub -b codex/hermes-skill-hub-release origin/main
cd ../language-tutor-hermes-skill-hub
```

Expected: new worktree exists on branch `codex/hermes-skill-hub-release`.

- [ ] **Step 5: Select execution skill**

Use one:

```text
superpowers:subagent-driven-development
```

or:

```text
superpowers:executing-plans
```

Expected: executor follows this plan task-by-task with review checkpoints.

---

## Task 1: Add Failing Hermes Skill Hub Installer Tests

**Files:**
- Create: `tests/installer/test_hermes_skill_hub.py`
- Modify later: `src/language_tutor/installer/providers/base.py`
- Modify later: `src/language_tutor/installer/providers/hermes.py`

- [ ] **Step 1: Write the failing test file**

Create `tests/installer/test_hermes_skill_hub.py`:

```python
from __future__ import annotations

from pathlib import Path

import pytest

from language_tutor.installer.assets import bundled_assets_root, bundled_assets_root_for
from language_tutor.installer.protocol import InstallerContext
from language_tutor.installer.providers.hermes import HermesInstaller
from language_tutor.installer.seams import FakeCommandRunner, FakeFilesystem
from language_tutor.installer.service import build_plan, run_init
from language_tutor.schemas import (
    HostId,
    InitRequest,
    ProviderActionKind,
    ProviderActionStage,
    ProviderState,
)

HOME = Path("/fake/home")
HERMES_HOME = Path("/opt/data")
PROFILE_ROOT = HERMES_HOME / "home" / ".hermes" / "profiles" / "lingo-loop"
SKILLS_ROOT = HERMES_HOME / "skills"

PROFILE_FILES = (
    "distribution.yaml",
    "config.yaml",
    "SOUL.md",
)

SKILL_SOURCE_TO_TARGET = {
    "skills/tutor-setup/SKILL.md": "language-tutor/tutor-setup/SKILL.md",
    "skills/tutor-vocab/SKILL.md": "language-tutor/tutor-vocab/SKILL.md",
    "skills/tutor-vocab/scripts/run.py": "language-tutor/tutor-vocab/scripts/run.py",
    "skills/tutor-writing/SKILL.md": "language-tutor/tutor-writing/SKILL.md",
    "skills/tutor-writing/scripts/run.py": "language-tutor/tutor-writing/scripts/run.py",
    "skills/tutor-progress/SKILL.md": "language-tutor/tutor-progress/SKILL.md",
    "skills/tutor-progress/scripts/run.py": "language-tutor/tutor-progress/scripts/run.py",
    "skills/tutor-reading/SKILL.md": "language-tutor/tutor-reading/SKILL.md",
    "skills/tutor-lesson/SKILL.md": "language-tutor/tutor-lesson/SKILL.md",
    "agents/tutor-judge.md": "autonomous-ai-agents/tutor-judge/SKILL.md",
}


def _ctx(
    monkeypatch: pytest.MonkeyPatch,
    *,
    files: dict[Path, str] | None = None,
    hermes_home: Path | None = HERMES_HOME,
) -> InstallerContext:
    if hermes_home is None:
        monkeypatch.delenv("HERMES_HOME", raising=False)
    else:
        monkeypatch.setenv("HERMES_HOME", str(hermes_home))
    fs = FakeFilesystem(home=HOME, files=files)
    config_root = (
        HOME / ".hermes"
        if hermes_home is None
        else hermes_home / "home" / ".hermes"
    )
    fs.mkdir(config_root)
    return InstallerContext(
        fs=fs,
        runner=FakeCommandRunner(available={"hermes": "/usr/bin/hermes"}),
        bundled_assets_root=bundled_assets_root(),
    )


def _expected_content_by_target() -> dict[Path, str]:
    profile_root = bundled_assets_root_for("hermes-profile")
    package_root = bundled_assets_root()
    expected: dict[Path, str] = {
        PROFILE_ROOT / rel: (profile_root / rel).read_text(encoding="utf-8")
        for rel in PROFILE_FILES
    }
    for source_rel, target_rel in SKILL_SOURCE_TO_TARGET.items():
        expected[SKILLS_ROOT / target_rel] = (package_root / source_rel).read_text(
            encoding="utf-8"
        )
    return expected


def test_hermes_managed_files_include_profile_and_skill_hub(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    ctx = _ctx(monkeypatch)
    managed = {str(path) for path in HermesInstaller(ctx).managed_files()}

    for rel in PROFILE_FILES:
        assert str(PROFILE_ROOT / rel) in managed
    for target_rel in SKILL_SOURCE_TO_TARGET.values():
        assert str(SKILLS_ROOT / target_rel) in managed


def test_hermes_without_hermes_home_uses_normal_user_hermes_data_root(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    ctx = _ctx(monkeypatch, hermes_home=None)
    managed = {str(path) for path in HermesInstaller(ctx).managed_files()}

    assert str(HOME / ".hermes" / "profiles" / "lingo-loop" / "distribution.yaml") in managed
    assert str(HOME / ".hermes" / "skills" / "language-tutor" / "tutor-setup" / "SKILL.md") in managed


def test_hermes_init_writes_profile_files_and_skill_hub_files(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    ctx = _ctx(monkeypatch)
    result = run_init(ctx, InitRequest(providers=[HostId.HERMES], yes=True))

    assert result.results[0].verified
    for target, expected in _expected_content_by_target().items():
        assert ctx.fs.is_file(target), f"missing managed file: {target}"
        assert ctx.fs.read_text(target) == expected


def test_hermes_second_init_is_idempotent(monkeypatch: pytest.MonkeyPatch) -> None:
    ctx = _ctx(monkeypatch)
    run_init(ctx, InitRequest(providers=[HostId.HERMES], yes=True))

    second = run_init(ctx, InitRequest(providers=[HostId.HERMES], yes=True))

    assert second.results[0].status.state == ProviderState.INSTALLED
    assert second.results[0].actions[0].kind == ProviderActionKind.SKIP
    assert second.results[0].actions[0].stage == ProviderActionStage.SKIPPED
    assert second.results[0].verified


def test_hermes_single_skill_drift_repairs_only_that_file(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    expected = _expected_content_by_target()
    drift_target = SKILLS_ROOT / "language-tutor" / "tutor-writing" / "SKILL.md"
    files = dict(expected)
    files[drift_target] = "DRIFTED\n"
    ctx = _ctx(monkeypatch, files=files)

    plan = build_plan(ctx, InitRequest(providers=[HostId.HERMES]))
    write_actions = [
        action for action in plan.plans[0].actions if action.kind == ProviderActionKind.WRITE_FILE
    ]

    assert plan.plans[0].status.state == ProviderState.NEEDS_REPAIR
    assert [action.target_path for action in write_actions] == [str(drift_target)]

    result = run_init(ctx, InitRequest(providers=[HostId.HERMES], yes=True))
    assert result.results[0].verified
    assert ctx.fs.read_text(drift_target) == expected[drift_target]


def test_hermes_missing_packaged_skill_reports_exact_source_path(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source_root = bundled_assets_root()
    fake_assets = tmp_path / "_assets"
    for rel in (
        "hermes-profile/distribution.yaml",
        "hermes-profile/config.yaml",
        "hermes-profile/SOUL.md",
        *SKILL_SOURCE_TO_TARGET.keys(),
    ):
        if rel == "skills/tutor-reading/SKILL.md":
            continue
        source = source_root / rel
        target = fake_assets / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(source.read_text(encoding="utf-8"), encoding="utf-8")
    monkeypatch.setenv("LANGUAGE_TUTOR_BUNDLED_ASSETS", str(fake_assets))
    ctx = _ctx(monkeypatch)

    plan = build_plan(ctx, InitRequest(providers=[HostId.HERMES]))

    assert plan.plans[0].status.state == ProviderState.BLOCKED
    assert "skills/tutor-reading/SKILL.md" in (plan.plans[0].status.repair_hint or "")
```

- [ ] **Step 2: Run the new tests to verify they fail**

Run:

```bash
uv run pytest tests/installer/test_hermes_skill_hub.py -v
```

Expected: FAIL. The first failure should show Hermes managed files do not include `/opt/data/skills/language-tutor/tutor-setup/SKILL.md` or `HERMES_HOME` is ignored.

- [ ] **Step 3: Commit the failing tests**

Run:

```bash
git add tests/installer/test_hermes_skill_hub.py
git commit -m "test: define hermes skill hub install contract"
```

Expected: commit succeeds with only the new test file staged.

---

## Task 2: Implement Hermes Dual-Root Managed Assets

**Files:**
- Modify: `src/language_tutor/installer/providers/base.py`
- Modify: `src/language_tutor/installer/providers/hermes.py`
- Modify: `tests/release/test_wheel_contents.py`

- [ ] **Step 1: Add generic provider asset specs**

In `src/language_tutor/installer/providers/base.py`, add `ProviderAsset` above `ProviderProfile` and extend `ProviderProfile`:

```python
@dataclass(frozen=True)
class ProviderAsset:
    source_root_rel: str
    source_rel: str
    target_area: str = "managed_dir"
    target_rel: str | None = None

    @property
    def managed_rel(self) -> str:
        return self.target_rel or self.source_rel

    @property
    def source_display(self) -> str:
        return f"{self.source_root_rel}/{self.source_rel}".strip("/")


@dataclass(frozen=True)
class ProviderProfile:
    host: HostId
    cli_name: str
    config_root_rel: str
    bundled_assets_root_rel: str
    managed_dir_rel: str
    files: tuple[str, ...]
    next_command: str
    assets: tuple[ProviderAsset, ...] = ()
```

Then replace the path/content helpers in `BaseProviderInstaller` with:

```python
    def asset_specs(self) -> tuple[ProviderAsset, ...]:
        if self.profile.assets:
            return self.profile.assets
        return tuple(
            ProviderAsset(
                source_root_rel=self.profile.bundled_assets_root_rel,
                source_rel=rel,
            )
            for rel in self.profile.files
        )

    def managed_root_for_area(self, area: str) -> Path:
        if area == "managed_dir":
            return self.managed_dir()
        raise ValueError(f"unknown managed area for {self.profile.host.value}: {area}")

    def _bundled_path(self, asset: ProviderAsset) -> Path:
        root = (
            bundled_assets_root_for(asset.source_root_rel)
            if asset.source_root_rel
            else bundled_assets_root_for("")
        )
        return root / asset.source_rel

    def _managed_path(self, asset: ProviderAsset) -> Path:
        return self.managed_root_for_area(asset.target_area) / asset.managed_rel

    def managed_files(self) -> list[Path]:
        return [self._managed_path(asset) for asset in self.asset_specs()]

    def bundled_files(self) -> list[Path]:
        return [self._bundled_path(asset) for asset in self.asset_specs()]

    def _bundled_content(self, asset: ProviderAsset) -> str:
        path = self._bundled_path(asset)
        if not path.exists():
            raise FileNotFoundError(
                f"bundled asset missing for {self.profile.host.value}: {asset.source_display}"
            )
        return path.read_text(encoding="utf-8")
```

Replace every `for rel in self.profile.files` loop in `detect()`, `_divergent_files()`, `plan()`, `apply()`, and `verify()` with asset-spec loops:

```python
        missing_bundled: list[str] = []
        for asset in self.asset_specs():
            if not self._bundled_path(asset).exists():
                missing_bundled.append(asset.source_display)
```

```python
    def _divergent_files(self) -> list[ProviderAsset]:
        divergent: list[ProviderAsset] = []
        for asset in self.asset_specs():
            managed_path = self._managed_path(asset)
            if not self.ctx.fs.is_file(managed_path):
                divergent.append(asset)
                continue
            try:
                expected = self._bundled_content(asset)
            except FileNotFoundError:
                continue
            if self.ctx.fs.read_text(managed_path) != expected:
                divergent.append(asset)
        return divergent
```

```python
                for asset in divergent:
                    target = self._managed_path(asset)
                    actions.append(
                        ProviderInstallAction(
                            kind=ProviderActionKind.WRITE_FILE,
                            target_path=str(target),
                            description=(
                                f"Write managed {self.display_name} file "
                                f"{asset.managed_rel} from bundled {asset.source_display}."
                            ),
                        )
                    )
```

```python
    def _asset_for_target(self, target_path: str) -> ProviderAsset | None:
        target = Path(target_path)
        for asset in self.asset_specs():
            if self._managed_path(asset) == target:
                return asset
        return None
```

```python
                asset = self._asset_for_target(action.target_path)
                if asset is None:
                    applied.append(
                        action.model_copy(
                            update={
                                "stage": ProviderActionStage.FAILED,
                                "error": (
                                    f"target {action.target_path} is not declared "
                                    f"by {self.profile.host.value} profile"
                                ),
                            }
                        )
                    )
                    continue
                try:
                    content = self._bundled_content(asset)
                    self.ctx.fs.write_text(Path(action.target_path), content)
```

```python
    def verify(self) -> tuple[bool, str | None]:
        for asset in self.asset_specs():
            managed_path = self._managed_path(asset)
            if not self.ctx.fs.is_file(managed_path):
                return False, f"managed file missing: {managed_path}"
            try:
                expected = self._bundled_content(asset)
            except FileNotFoundError as exc:
                return False, str(exc)
            current = self.ctx.fs.read_text(managed_path)
            if current != expected:
                return False, f"managed file content differs from bundled asset: {managed_path}"
        return True, None
```

Also update the `all_missing` expression in `detect()`:

```python
            all_missing = all(
                not self.ctx.fs.is_file(self._managed_path(asset))
                for asset in self.asset_specs()
            )
```

- [ ] **Step 2: Implement Hermes-specific `HERMES_HOME` paths and asset specs**

Replace `src/language_tutor/installer/providers/hermes.py` with:

```python
from __future__ import annotations

import os
from pathlib import Path

from language_tutor.installer.providers.base import (
    BaseProviderInstaller,
    ProviderAsset,
    ProviderProfile,
)
from language_tutor.schemas import HostId

HERMES_PROFILE_FILES = (
    "distribution.yaml",
    "config.yaml",
    "SOUL.md",
)

HERMES_SKILL_ASSETS = (
    ProviderAsset(
        source_root_rel="",
        source_rel="skills/tutor-setup/SKILL.md",
        target_area="hermes_skills",
        target_rel="language-tutor/tutor-setup/SKILL.md",
    ),
    ProviderAsset(
        source_root_rel="",
        source_rel="skills/tutor-vocab/SKILL.md",
        target_area="hermes_skills",
        target_rel="language-tutor/tutor-vocab/SKILL.md",
    ),
    ProviderAsset(
        source_root_rel="",
        source_rel="skills/tutor-vocab/scripts/run.py",
        target_area="hermes_skills",
        target_rel="language-tutor/tutor-vocab/scripts/run.py",
    ),
    ProviderAsset(
        source_root_rel="",
        source_rel="skills/tutor-writing/SKILL.md",
        target_area="hermes_skills",
        target_rel="language-tutor/tutor-writing/SKILL.md",
    ),
    ProviderAsset(
        source_root_rel="",
        source_rel="skills/tutor-writing/scripts/run.py",
        target_area="hermes_skills",
        target_rel="language-tutor/tutor-writing/scripts/run.py",
    ),
    ProviderAsset(
        source_root_rel="",
        source_rel="skills/tutor-progress/SKILL.md",
        target_area="hermes_skills",
        target_rel="language-tutor/tutor-progress/SKILL.md",
    ),
    ProviderAsset(
        source_root_rel="",
        source_rel="skills/tutor-progress/scripts/run.py",
        target_area="hermes_skills",
        target_rel="language-tutor/tutor-progress/scripts/run.py",
    ),
    ProviderAsset(
        source_root_rel="",
        source_rel="skills/tutor-reading/SKILL.md",
        target_area="hermes_skills",
        target_rel="language-tutor/tutor-reading/SKILL.md",
    ),
    ProviderAsset(
        source_root_rel="",
        source_rel="skills/tutor-lesson/SKILL.md",
        target_area="hermes_skills",
        target_rel="language-tutor/tutor-lesson/SKILL.md",
    ),
    ProviderAsset(
        source_root_rel="",
        source_rel="agents/tutor-judge.md",
        target_area="hermes_skills",
        target_rel="autonomous-ai-agents/tutor-judge/SKILL.md",
    ),
)


class HermesInstaller(BaseProviderInstaller):
    profile = ProviderProfile(
        host=HostId.HERMES,
        cli_name="hermes",
        config_root_rel=".hermes",
        bundled_assets_root_rel="hermes-profile",
        managed_dir_rel="profiles/lingo-loop",
        files=HERMES_PROFILE_FILES,
        next_command="Run `hermes skills list` to confirm the lingo-loop tutor skills are enabled.",
        assets=(
            *(
                ProviderAsset(
                    source_root_rel="hermes-profile",
                    source_rel=rel,
                )
                for rel in HERMES_PROFILE_FILES
            ),
            *HERMES_SKILL_ASSETS,
        ),
    )

    def hermes_data_root(self) -> Path:
        configured = os.environ.get("HERMES_HOME")
        if configured:
            return Path(configured).expanduser()
        return self.ctx.fs.home() / ".hermes"

    def config_root(self) -> Path:
        configured = os.environ.get("HERMES_HOME")
        if configured:
            return Path(configured).expanduser() / "home" / ".hermes"
        return super().config_root()

    def managed_root_for_area(self, area: str) -> Path:
        if area == "hermes_skills":
            return self.hermes_data_root() / "skills"
        return super().managed_root_for_area(area)
```

- [ ] **Step 3: Fix package root lookup for empty source roots**

In `src/language_tutor/installer/providers/base.py`, import `bundled_assets_root`:

```python
from language_tutor.installer.assets import bundled_assets_root, bundled_assets_root_for
```

Then adjust `_bundled_path()`:

```python
    def _bundled_path(self, asset: ProviderAsset) -> Path:
        root = (
            bundled_assets_root_for(asset.source_root_rel)
            if asset.source_root_rel
            else bundled_assets_root()
        )
        return root / asset.source_rel
```

- [ ] **Step 4: Update wheel content test to use asset specs**

Modify `tests/release/test_wheel_contents.py`:

```python
def _expected_wheel_paths() -> list[str]:
    paths: list[str] = []
    for profile in PROFILES:
        installer_cls = {
            HostId.CLAUDE: ClaudeInstaller,
            HostId.CODEX: CodexInstaller,
            HostId.HERMES: HermesInstaller,
            HostId.OPENCLAW: OpenClawInstaller,
        }[profile.host]
        ctx = InstallerContext(
            fs=FakeFilesystem(home=Path("/fake/home")),
            runner=FakeCommandRunner(available={}),
            bundled_assets_root=REPO_ROOT,
        )
        installer = installer_cls(ctx)
        for asset in installer.asset_specs():
            source_root = f"{asset.source_root_rel}/" if asset.source_root_rel else ""
            paths.append(f"language_tutor/_assets/{source_root}{asset.source_rel}")
    return paths
```

Add these imports:

```python
from language_tutor.installer.protocol import InstallerContext
from language_tutor.installer.seams import FakeCommandRunner, FakeFilesystem
from language_tutor.schemas import HostId
```

- [ ] **Step 5: Run the focused tests**

Run:

```bash
uv run pytest tests/installer/test_hermes_skill_hub.py tests/release/test_wheel_contents.py -v
```

Expected: PASS.

- [ ] **Step 6: Run existing installer tests**

Run:

```bash
uv run pytest tests/unit/test_installer_service.py tests/installer/test_bundled_tree.py -v
```

Expected: PASS.

- [ ] **Step 7: Commit implementation**

Run:

```bash
git add src/language_tutor/installer/providers/base.py src/language_tutor/installer/providers/hermes.py tests/release/test_wheel_contents.py
git commit -m "feat: install hermes tutor skills from packaged assets"
```

Expected: commit succeeds.

---

## Task 3: Enforce Installed Tutor Command In Skills And Helper Scripts

**Files:**
- Create: `tests/packaging/test_hermes_skill_command_contract.py`
- Modify: `skills/tutor-setup/SKILL.md`
- Modify: `skills/tutor-vocab/SKILL.md`
- Modify: `skills/tutor-writing/SKILL.md`
- Modify: `skills/tutor-progress/SKILL.md`
- Modify: `skills/tutor-reading/SKILL.md`
- Modify: `skills/tutor-lesson/SKILL.md`
- Modify: `skills/tutor-vocab/scripts/run.py`
- Modify: `skills/tutor-writing/scripts/run.py`
- Modify: `skills/tutor-progress/scripts/run.py`

- [ ] **Step 1: Dispatch skill-edit subagent**

Use a subagent for this task. Include this exact instruction in the subagent prompt:

```text
Read /Users/artem.veduta/.claude/plugins/cache/claude-plugins-official/superpowers/5.1.0/skills/writing-skills before editing any SKILL.md. Update only the six tutor flow SKILL.md files and the three helper run.py files listed in Task 3. Preserve the existing lifecycle/checkpoint requirements. Replace source-relative bin/tutor command text with installed tutor command text. Report changed files and verification commands.
```

Expected: subagent confirms it read the helper and reports only the listed files.

- [ ] **Step 2: Write failing command-contract tests**

Create `tests/packaging/test_hermes_skill_command_contract.py`:

```python
from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

FLOW_SKILLS = (
    "skills/tutor-setup/SKILL.md",
    "skills/tutor-vocab/SKILL.md",
    "skills/tutor-writing/SKILL.md",
    "skills/tutor-progress/SKILL.md",
    "skills/tutor-reading/SKILL.md",
    "skills/tutor-lesson/SKILL.md",
)

HELPER_SCRIPTS = (
    "skills/tutor-vocab/scripts/run.py",
    "skills/tutor-writing/scripts/run.py",
    "skills/tutor-progress/scripts/run.py",
)


def test_flow_skill_markdown_uses_installed_tutor_command() -> None:
    offenders: list[str] = []
    for rel in FLOW_SKILLS:
        text = (REPO_ROOT / rel).read_text(encoding="utf-8")
        if "bin/tutor" in text:
            offenders.append(rel)
        assert "tutor " in text, rel
        assert "--json" in text, rel
    assert offenders == [], "source-relative bin/tutor references remain: " + ", ".join(offenders)


def test_helper_scripts_use_language_tutor_tutor_bin_default() -> None:
    for rel in HELPER_SCRIPTS:
        text = (REPO_ROOT / rel).read_text(encoding="utf-8")
        assert 'os.environ.get("LANGUAGE_TUTOR_TUTOR_BIN", "tutor")' in text, rel
        assert 'ROOT / "bin" / "tutor"' not in text, rel
        assert "Path(__file__)" not in text, rel
```

- [ ] **Step 3: Run test to verify it fails**

Run:

```bash
uv run pytest tests/packaging/test_hermes_skill_command_contract.py -v
```

Expected: FAIL with `source-relative bin/tutor references remain`.

- [ ] **Step 4: Update helper scripts**

Replace each helper script (`skills/tutor-vocab/scripts/run.py`, `skills/tutor-writing/scripts/run.py`, `skills/tutor-progress/scripts/run.py`) with:

```python
from __future__ import annotations

import os
import subprocess
import sys


def main() -> int:
    tutor_bin = os.environ.get("LANGUAGE_TUTOR_TUTOR_BIN", "tutor")
    return subprocess.call([tutor_bin, *sys.argv[1:]])


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 5: Update skill markdown command examples**

In each of the six flow skill files, replace command text as follows:

```text
bin/tutor
```

with:

```text
tutor
```

Keep all existing `session-start`, `session_id`, `checkpoint`, `session-close`, `session-end`, schema, privacy, and validation instructions intact.

For `skills/tutor-setup/SKILL.md`, the command block must contain these exact command forms after edit:

```markdown
- Read current state: `tutor setup read --json`
- Write required `profile.native_language` and `profile.target_language`: `tutor setup write --json '<payload>'`
- Show boot context after setup: `tutor boot-context --json`
```

For `skills/tutor-vocab/SKILL.md`, the lifecycle precondition must begin:

```markdown
`tutor session-start --json '{"host":"<host>"}'` and capture the returned
```

For `skills/tutor-writing/SKILL.md`, the flow must begin:

```markdown
1. If this conversation has no `session_id` yet, FIRST run `tutor session-start --json '{"host":"<host>"}'` and capture `session_id` from the response.
```

For `skills/tutor-progress/SKILL.md`, diagnostics must read:

```markdown
5. Diagnostics (no session_id needed): `tutor doctor --json`.
```

For `skills/tutor-reading/SKILL.md`, validation must read:

```markdown
2. Validate it: `tutor reading start --json '{"session_id":"sess_...","mode":"comprehension","candidate":{...}}'`
```

For `skills/tutor-lesson/SKILL.md`, validation must read:

```markdown
4. Validate it: `tutor lesson start --json '{"session_id":"sess_...","candidate":{...}}'`.
```

- [ ] **Step 6: Run contract and lifecycle tests**

Run:

```bash
uv run pytest tests/packaging/test_hermes_skill_command_contract.py tests/unit/test_skill_lifecycle_tokens.py -v
```

Expected: PASS.

- [ ] **Step 7: Commit skill command contract**

Run:

```bash
git add tests/packaging/test_hermes_skill_command_contract.py skills/tutor-setup/SKILL.md skills/tutor-vocab/SKILL.md skills/tutor-writing/SKILL.md skills/tutor-progress/SKILL.md skills/tutor-reading/SKILL.md skills/tutor-lesson/SKILL.md skills/tutor-vocab/scripts/run.py skills/tutor-writing/scripts/run.py skills/tutor-progress/scripts/run.py
git commit -m "fix: use installed tutor command in packaged skills"
```

Expected: commit succeeds.

---

## Task 4: Fix Hermes Profile Manifest Metadata

**Files:**
- Modify: `tests/packaging/test_hermes_profile_distribution.py`
- Modify: `hermes-profile/distribution.yaml`

- [ ] **Step 1: Add failing profile manifest tests**

Append to `tests/packaging/test_hermes_profile_distribution.py`:

```python
import tomllib

from ruamel.yaml import YAML


def _load_distribution() -> dict[str, object]:
    yaml = YAML(typ="safe")
    data = yaml.load((HERMES_ROOT / "distribution.yaml").read_text(encoding="utf-8"))
    assert isinstance(data, dict)
    return data


def test_hermes_distribution_does_not_reference_source_skills_tree() -> None:
    _skip_if_absent(HERMES_ROOT / "distribution.yaml")
    data = _load_distribution()
    profile = data.get("profile")
    assert isinstance(profile, dict)
    assert "skills" not in profile


def test_hermes_distribution_version_matches_pyproject() -> None:
    _skip_if_absent(HERMES_ROOT / "distribution.yaml")
    distribution = _load_distribution()
    pyproject = tomllib.loads((REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    assert str(distribution["version"]) == pyproject["project"]["version"]
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
uv run pytest tests/packaging/test_hermes_profile_distribution.py -v
```

Expected: FAIL because `profile.skills` exists and `version` is `0.1.0`.

- [ ] **Step 3: Update Hermes distribution manifest**

In `hermes-profile/distribution.yaml`, change:

```yaml
version: 0.1.0
```

to:

```yaml
version: 0.1.3
```

Replace the `profile:` block with:

```yaml
profile:
  prompt: SOUL.md
  config: config.yaml

# Tutor flow skills and the tutor-judge agent are materialized by:
#   tutor init --provider hermes --yes
# They are installed into the Hermes skills hub, not into this profile directory.
```

- [ ] **Step 4: Run profile tests**

Run:

```bash
uv run pytest tests/packaging/test_hermes_profile_distribution.py -v
```

Expected before Task 7 version bump: FAIL only on `test_hermes_distribution_version_matches_pyproject` because `pyproject.toml` still says `0.1.2`. This failure is intentional until the release metadata task.

- [ ] **Step 5: Commit profile manifest change and tests**

Run:

```bash
git add tests/packaging/test_hermes_profile_distribution.py hermes-profile/distribution.yaml
git commit -m "fix: remove dead hermes skills pointer"
```

Expected: commit succeeds. The temporary profile-version test failure remains tracked for Task 7.

---

## Task 5: Add Doctor Checks For Hermes Provider Payloads

**Files:**
- Modify: `src/language_tutor/package_assets.py`
- Modify: `src/language_tutor/health.py`
- Modify: `tests/unit/test_package_assets.py`
- Modify: `tests/unit/test_health.py`

- [ ] **Step 1: Add failing package asset inventory tests**

Append to `tests/unit/test_package_assets.py`:

```python
from language_tutor.package_assets import REQUIRED_HERMES_PROVIDER_PAYLOADS


def test_required_hermes_provider_payloads_cover_profile_files() -> None:
    assert "hermes-profile/distribution.yaml" in REQUIRED_HERMES_PROVIDER_PAYLOADS
    assert "hermes-profile/config.yaml" in REQUIRED_HERMES_PROVIDER_PAYLOADS
    assert "hermes-profile/SOUL.md" in REQUIRED_HERMES_PROVIDER_PAYLOADS
```

- [ ] **Step 2: Add failing doctor tests**

In `tests/unit/test_health.py`, update `_make_runtime_payload()` to also write Hermes provider payloads:

```python
        "hermes-profile/distribution.yaml",
        "hermes-profile/config.yaml",
        "hermes-profile/SOUL.md",
```

Then append:

```python
def test_doctor_reports_hermes_provider_payloads(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake_repo = tmp_path / "site-packages-adjacent"
    fake_repo.mkdir()
    assets = tmp_path / "_assets"
    (assets / ".claude-plugin").mkdir(parents=True)
    (assets / ".claude-plugin" / "plugin.json").write_text("{}", encoding="utf-8")
    _make_runtime_payload(assets)
    monkeypatch.setenv("LANGUAGE_TUTOR_BUNDLED_ASSETS", str(assets))

    report = doctor(_paths(tmp_path), fake_repo)
    names = {check.name for check in report.checks}

    assert "provider_payload:hermes-profile/distribution.yaml" in names
    assert "provider_payload:hermes-profile/config.yaml" in names
    assert "provider_payload:hermes-profile/SOUL.md" in names
    assert report.status == "ok"


def test_doctor_fails_with_exact_missing_hermes_provider_payload(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake_repo = tmp_path / "site-packages-adjacent"
    fake_repo.mkdir()
    assets = tmp_path / "_assets"
    (assets / ".claude-plugin").mkdir(parents=True)
    (assets / ".claude-plugin" / "plugin.json").write_text("{}", encoding="utf-8")
    _make_runtime_payload(assets)
    (assets / "hermes-profile" / "config.yaml").unlink()
    monkeypatch.setenv("LANGUAGE_TUTOR_BUNDLED_ASSETS", str(assets))

    report = doctor(_paths(tmp_path), fake_repo)
    checks = {check.name: check for check in report.checks}

    check = checks["provider_payload:hermes-profile/config.yaml"]
    assert check.status == "fail"
    assert "hermes-profile/config.yaml" in (check.repair_hint or "")
    assert report.status == "fail"


def test_doctor_does_not_create_learner_session(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    _make_source_tree(repo)

    paths = _paths(tmp_path)
    report = doctor(paths, repo)

    conn = connect(paths.database_path)
    try:
        session_count = conn.execute("SELECT COUNT(*) FROM sessions").fetchone()[0]
    finally:
        conn.close()
    assert report.status == "ok"
    assert session_count == 0
```

Add import at the top of `tests/unit/test_health.py`:

```python
from language_tutor.dal.sqlite_store import connect
```

- [ ] **Step 3: Run tests to verify they fail**

Run:

```bash
uv run pytest tests/unit/test_package_assets.py tests/unit/test_health.py -v
```

Expected: FAIL because `REQUIRED_HERMES_PROVIDER_PAYLOADS` is not defined and doctor does not report `provider_payload:*` checks.

- [ ] **Step 4: Add Hermes provider payload inventory**

In `src/language_tutor/package_assets.py`, add:

```python
REQUIRED_HERMES_PROVIDER_PAYLOADS: tuple[str, ...] = (
    "hermes-profile/distribution.yaml",
    "hermes-profile/config.yaml",
    "hermes-profile/SOUL.md",
)
```

Keep `REQUIRED_RUNTIME_PAYLOADS` unchanged so existing doctor check names remain stable.

- [ ] **Step 5: Update doctor to report provider payloads**

In `src/language_tutor/health.py`, update the import:

```python
from language_tutor.package_assets import (
    REQUIRED_HERMES_PROVIDER_PAYLOADS,
    REQUIRED_RUNTIME_PAYLOADS,
    package_asset_path,
)
```

After the runtime payload loop, add:

```python
    for rel in REQUIRED_HERMES_PROVIDER_PAYLOADS:
        path = package_asset_path(rel)
        checks.append(
            DoctorCheck(
                name=f"provider_payload:{rel}",
                status="ok" if path.exists() else "fail",
                repair_hint=f"Reinstall lingo-loop; packaged provider payload missing: {rel}.",
            )
        )
```

- [ ] **Step 6: Run doctor/package tests**

Run:

```bash
uv run pytest tests/unit/test_package_assets.py tests/unit/test_health.py tests/adapter_contract/test_doctor_cli.py -v
```

Expected: PASS.

- [ ] **Step 7: Commit doctor payload checks**

Run:

```bash
git add src/language_tutor/package_assets.py src/language_tutor/health.py tests/unit/test_package_assets.py tests/unit/test_health.py
git commit -m "feat: validate hermes provider payloads in doctor"
```

Expected: commit succeeds.

---

## Task 6: Update Installer Service Smoke Tests For Hermes Multi-File Writes

**Files:**
- Modify: `tests/unit/test_installer_service.py`
- Modify: `tests/installer/test_bundled_tree.py`
- Modify: `tests/integration/test_tutor_init_cli.py`

- [ ] **Step 1: Update expected Hermes managed paths where tests list only first file**

In `tests/unit/test_installer_service.py`, keep `_managed_path(HostId.HERMES)` pointing at:

```python
HostId.HERMES: ".hermes/profiles/lingo-loop/distribution.yaml",
```

Then add a Hermes-specific assertion after `test_detect_available_writes_file`:

```python
def test_hermes_detect_available_writes_skill_hub_file() -> None:
    ctx = make_ctx(available_clis={"hermes": "/usr/bin/hermes"})
    result = run_init(ctx, InitRequest(providers=[HostId.HERMES], yes=True))

    assert result.results[0].verified
    target = HOME / ".hermes" / "skills" / "language-tutor" / "tutor-setup" / "SKILL.md"
    assert ctx.fs.is_file(target)
```

- [ ] **Step 2: Add bundled-tree assertion for Hermes asset specs**

Append to `tests/installer/test_bundled_tree.py`:

```python
from language_tutor.installer.providers.hermes import HermesInstaller


def test_hermes_profile_declares_profile_and_skill_hub_assets() -> None:
    ctx = _ctx()
    assets = {asset.source_display: asset.managed_rel for asset in HermesInstaller(ctx).asset_specs()}

    assert assets["hermes-profile/distribution.yaml"] == "distribution.yaml"
    assert assets["skills/tutor-setup/SKILL.md"] == "language-tutor/tutor-setup/SKILL.md"
    assert assets["skills/tutor-vocab/scripts/run.py"] == "language-tutor/tutor-vocab/scripts/run.py"
    assert assets["agents/tutor-judge.md"] == "autonomous-ai-agents/tutor-judge/SKILL.md"
```

- [ ] **Step 3: Update CLI integration test to check a Hermes skill file**

In `tests/integration/test_tutor_init_cli.py`, append:

```python
def test_init_hermes_writes_skill_hub_file(
    fake_clis: dict[str, str],
    fake_home: Path,
    no_tty: None,
) -> None:
    del fake_clis, no_tty
    runner = CliRunner()

    result = runner.invoke(main, ["init", "--provider", "hermes", "--yes", "--json"])

    assert result.exit_code == 0, result.output
    target = fake_home / ".hermes" / "skills" / "language-tutor" / "tutor-setup" / "SKILL.md"
    assert target.exists()
```

- [ ] **Step 4: Run installer smoke tests**

Run:

```bash
uv run pytest tests/unit/test_installer_service.py tests/installer/test_bundled_tree.py tests/integration/test_tutor_init_cli.py -v
```

Expected: PASS.

- [ ] **Step 5: Commit smoke test alignment**

Run:

```bash
git add tests/unit/test_installer_service.py tests/installer/test_bundled_tree.py tests/integration/test_tutor_init_cli.py
git commit -m "test: cover hermes skill hub smoke paths"
```

Expected: commit succeeds.

---

## Task 7: Bump Release Metadata And Upstream Hermes Docs

**Files:**
- Modify: `pyproject.toml`
- Modify: `CHANGELOG.md`
- Create: `tests/release/test_release_metadata.py`
- Modify: `docs/install/hermes.md`

- [ ] **Step 1: Add failing release metadata tests**

Create `tests/release/test_release_metadata.py`:

```python
from __future__ import annotations

import tomllib
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


def test_pyproject_version_is_0_1_3() -> None:
    pyproject = tomllib.loads((REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    assert pyproject["project"]["version"] == "0.1.3"


def test_changelog_has_0_1_3_release_section() -> None:
    text = (REPO_ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    assert "## [0.1.3] - 2026-05-31" in text
    assert "Hermes" in text
    assert "skill hub" in text
```

- [ ] **Step 2: Run release metadata tests to verify they fail**

Run:

```bash
uv run pytest tests/release/test_release_metadata.py tests/packaging/test_hermes_profile_distribution.py -v
```

Expected: FAIL because `pyproject.toml` still says `0.1.2` and changelog has no `0.1.3` section.

- [ ] **Step 3: Bump package version**

In `pyproject.toml`, change:

```toml
version = "0.1.2"
```

to:

```toml
version = "0.1.3"
```

- [ ] **Step 4: Add changelog release section**

In `CHANGELOG.md`, below the empty `[Unreleased]` block, add:

```markdown
## [0.1.3] - 2026-05-31

### Added

- Hermes provider init now materializes the packaged tutor flow skills and `tutor-judge` agent into the Hermes skills hub.
- `tutor doctor --json` now verifies Hermes provider payloads required by `tutor init --provider hermes --yes`.

### Changed

- Hermes profile metadata no longer points at the source-tree `../skills` path; the package installer owns skill installation.
- Packaged tutor skills invoke the installed `tutor` console script and helper scripts honor `LANGUAGE_TUTOR_TUTOR_BIN`.

### Fixed

- Wheel/container Hermes installs no longer depend on a source checkout for tutor skill discovery.
```

- [ ] **Step 5: Update upstream Hermes install docs**

In `docs/install/hermes.md`, make these exact content changes:

```markdown
uv tool install lingo-loop==0.1.3
tutor doctor --json
tutor init --provider hermes --yes
```

Replace the git fallback with:

```markdown
# Source tag fallback:
# uv tool install "lingo-loop @ git+https://github.com/artemVeduta/lingo-loop@v0.1.3"
```

Replace the managed profile paragraph with:

```markdown
This writes the Hermes profile under `~/.hermes/profiles/lingo-loop/` and writes tutor skills under `~/.hermes/skills/language-tutor/` plus `~/.hermes/skills/autonomous-ai-agents/tutor-judge/SKILL.md`. If `HERMES_HOME` is set, the profile root is `$HERMES_HOME/home/.hermes/profiles/lingo-loop/` and the skill hub root is `$HERMES_HOME/skills/`.
```

Replace the manual fallback bullet:

```markdown
- `profile.skills`: omitted; skill installation is owned by `tutor init --provider hermes --yes`
```

Remove the troubleshooting section titled:

```markdown
### Error: Skills do not load (`../skills not found`)
```

- [ ] **Step 6: Run release/docs tests**

Run:

```bash
uv run pytest tests/release/test_release_metadata.py tests/packaging/test_hermes_profile_distribution.py tests/docs/test_install_docs.py -v
```

Expected: PASS.

- [ ] **Step 7: Run version guard**

Run:

```bash
./scripts/version-guard.sh v0.1.3
```

Expected:

```text
version-guard: OK (0.1.3)
```

- [ ] **Step 8: Commit release metadata**

Run:

```bash
git add pyproject.toml CHANGELOG.md tests/release/test_release_metadata.py docs/install/hermes.md
git commit -m "chore: prepare 0.1.3 release metadata"
```

Expected: commit succeeds.

---

## Task 8: Build And Verify The Wheel Locally

**Files:**
- Read only: `dist/`
- Read only: package wheel generated by `uv build`

- [ ] **Step 1: Run focused release tests**

Run:

```bash
uv run pytest tests/installer/test_hermes_skill_hub.py tests/packaging/test_hermes_skill_command_contract.py tests/unit/test_health.py tests/release/test_wheel_contents.py tests/release/test_release_metadata.py -v
```

Expected: PASS.

- [ ] **Step 2: Run full Python gate**

Run:

```bash
uv run pytest
uv run pyright
uv run ruff check .
```

Expected: all three commands exit 0.

- [ ] **Step 3: Build wheel and sdist**

Run:

```bash
rm -rf dist
uv build
```

Expected: `dist/lingo_loop-0.1.3-py3-none-any.whl` and `dist/lingo_loop-0.1.3.tar.gz` exist.

- [ ] **Step 4: Inspect wheel contents for Hermes assets**

Run:

```bash
python - <<'PY'
import zipfile
from pathlib import Path

wheel = next(Path("dist").glob("lingo_loop-0.1.3-*.whl"))
required = {
    "language_tutor/_assets/hermes-profile/distribution.yaml",
    "language_tutor/_assets/hermes-profile/config.yaml",
    "language_tutor/_assets/hermes-profile/SOUL.md",
    "language_tutor/_assets/skills/tutor-setup/SKILL.md",
    "language_tutor/_assets/skills/tutor-vocab/SKILL.md",
    "language_tutor/_assets/skills/tutor-vocab/scripts/run.py",
    "language_tutor/_assets/skills/tutor-writing/SKILL.md",
    "language_tutor/_assets/skills/tutor-writing/scripts/run.py",
    "language_tutor/_assets/skills/tutor-progress/SKILL.md",
    "language_tutor/_assets/skills/tutor-progress/scripts/run.py",
    "language_tutor/_assets/skills/tutor-reading/SKILL.md",
    "language_tutor/_assets/skills/tutor-lesson/SKILL.md",
    "language_tutor/_assets/agents/tutor-judge.md",
}
with zipfile.ZipFile(wheel) as zf:
    names = set(zf.namelist())
missing = sorted(required - names)
if missing:
    raise SystemExit("missing:\n" + "\n".join(missing))
print(f"ok: {wheel.name}")
PY
```

Expected:

```text
ok: lingo_loop-0.1.3-py3-none-any.whl
```

- [ ] **Step 5: Smoke test wheel install in a temp venv**

Run:

```bash
tmpdir="$(mktemp -d)"
python3 -m venv "$tmpdir/venv"
"$tmpdir/venv/bin/python" -m pip install --upgrade pip
"$tmpdir/venv/bin/python" -m pip install dist/lingo_loop-0.1.3-py3-none-any.whl
LANGUAGE_TUTOR_HOME="$tmpdir/tutor-home" "$tmpdir/venv/bin/tutor" doctor --json
```

Expected: JSON output contains:

```json
"status": "ok"
```

and includes checks named:

```text
provider_payload:hermes-profile/distribution.yaml
runtime_payload:skills/tutor-setup/SKILL.md
```

- [ ] **Step 6: Smoke test Hermes init from installed wheel with fake Hermes CLI**

Run:

```bash
tmpdir="$(mktemp -d)"
cat > "$tmpdir/hermes" <<'SH'
#!/usr/bin/env sh
exit 0
SH
chmod +x "$tmpdir/hermes"
mkdir -p "$tmpdir/hermes-home/home/.hermes"
PATH="$tmpdir:$PATH" HERMES_HOME="$tmpdir/hermes-home" "$tmpdir/venv/bin/tutor" init --provider hermes --yes --json
find "$tmpdir/hermes-home/skills/language-tutor" "$tmpdir/hermes-home/skills/autonomous-ai-agents" -maxdepth 3 -type f | sort
```

Expected: JSON init output has `"verified": true`; `find` output includes:

```text
tutor-setup/SKILL.md
tutor-vocab/SKILL.md
tutor-writing/SKILL.md
tutor-reading/SKILL.md
tutor-lesson/SKILL.md
tutor-progress/SKILL.md
tutor-judge/SKILL.md
```

- [ ] **Step 7: Commit any verification-driven fixes**

If Task 8 required edits, commit them:

```bash
git add <changed-files>
git commit -m "fix: align hermes wheel verification"
```

Expected: commit only if files changed.

---

## Task 9: Open Draft PR And Inspect CI

**Files:**
- No code edits expected.

- [ ] **Step 1: Use verification skill before publishing branch**

Use `superpowers:verification-before-completion`.

Run:

```bash
git status --short
uv run pytest
uv run pyright
uv run ruff check .
uv build
./scripts/version-guard.sh v0.1.3
```

Expected: clean or only intentional generated `dist/` ignored files; all commands exit 0.

- [ ] **Step 2: Use GitHub publishing skill**

Use `github:yeet` to stage, commit any remaining intended changes, push `codex/hermes-skill-hub-release`, and open a draft PR.

If using direct commands because the skill asks for explicit command execution, run:

```bash
git status --short
git push -u origin codex/hermes-skill-hub-release
gh pr create --draft --title "Release lingo-loop 0.1.3 Hermes skill hub" --body-file - <<'MD'
## Summary
- installs Hermes tutor skills and tutor-judge from packaged lingo-loop assets
- removes dead Hermes profile skills pointer
- makes packaged skills use the installed tutor command
- adds doctor/package checks and release metadata for 0.1.3

## Verification
- uv run pytest
- uv run pyright
- uv run ruff check .
- uv build
- ./scripts/version-guard.sh v0.1.3
MD
```

Expected: draft PR URL is printed.

- [ ] **Step 3: Watch PR checks**

Run:

```bash
gh pr checks --watch
```

Expected: all checks pass.

- [ ] **Step 4: Inspect failed CI if any check fails**

Run:

```bash
gh run list --limit 10
gh run view --log-failed
```

Expected if failures exist: failed job logs identify the exact command/test failure. Fix failures with TDD in a new commit, push, and rerun `gh pr checks --watch`.

- [ ] **Step 5: Mark PR ready after CI is green**

Run:

```bash
gh pr ready
```

Expected: PR becomes ready for review.

---

## Task 10: Merge, Tag, Release, And Verify `v0.1.3`

**Files:**
- No code edits expected after merge.

- [ ] **Step 1: Merge the PR after approval and green CI**

Run:

```bash
gh pr merge --squash --delete-branch
```

Expected: PR merges to `main`.

- [ ] **Step 2: Sync local main**

Run:

```bash
git checkout main
git pull --ff-only origin main
./scripts/version-guard.sh v0.1.3
```

Expected:

```text
version-guard: OK (0.1.3)
```

- [ ] **Step 3: Create and push annotated tag**

Run:

```bash
git tag -a v0.1.3 -m "release 0.1.3"
git push origin v0.1.3
```

Expected: tag push succeeds and starts `.github/workflows/workflow.yml`.

- [ ] **Step 4: Inspect release workflow with GitHub CLI**

Run:

```bash
gh run list --workflow workflow.yml --limit 5
```

Expected: newest run is for tag `v0.1.3`.

Then watch it:

```bash
run_id="$(gh run list --workflow workflow.yml --limit 1 --json databaseId --jq '.[0].databaseId')"
gh run watch "$run_id"
gh run view "$run_id" --log-failed
```

Expected: workflow completes successfully. If `--log-failed` prints no failed logs, continue.

- [ ] **Step 5: Verify GitHub Release**

Run:

```bash
gh release view v0.1.3
```

Expected: release exists, is not a prerelease, and lists generated artifacts.

- [ ] **Step 6: Verify PyPI artifact**

Run:

```bash
python -m pip index versions lingo-loop
uvx --refresh --from lingo-loop==0.1.3 tutor doctor --json
```

Expected: PyPI lists `0.1.3`; `tutor doctor --json` returns JSON with `"status": "ok"`.

- [ ] **Step 7: Verify published package can materialize Hermes skill hub**

Run:

```bash
tmpdir="$(mktemp -d)"
cat > "$tmpdir/hermes" <<'SH'
#!/usr/bin/env sh
exit 0
SH
chmod +x "$tmpdir/hermes"
mkdir -p "$tmpdir/hermes-home/home/.hermes"
PATH="$tmpdir:$PATH" HERMES_HOME="$tmpdir/hermes-home" uvx --refresh --from lingo-loop==0.1.3 tutor init --provider hermes --yes --json
find "$tmpdir/hermes-home/skills/language-tutor" "$tmpdir/hermes-home/skills/autonomous-ai-agents" -maxdepth 3 -type f | sort
```

Expected output includes:

```text
tutor-setup/SKILL.md
tutor-vocab/SKILL.md
tutor-vocab/scripts/run.py
tutor-writing/SKILL.md
tutor-writing/scripts/run.py
tutor-progress/SKILL.md
tutor-progress/scripts/run.py
tutor-reading/SKILL.md
tutor-lesson/SKILL.md
tutor-judge/SKILL.md
```

- [ ] **Step 8: Record upstream release evidence**

Save these values in the PR or release follow-up comment:

```bash
gh release view v0.1.3 --json tagName,url,isPrerelease,publishedAt
uvx --refresh --from lingo-loop==0.1.3 tutor doctor --json
```

Expected: evidence shows tag `v0.1.3`, release URL, and doctor `"status": "ok"`.

---

## Task 11: Handoff To Homelab Rollout

**Files:**
- No upstream code edits.

- [ ] **Step 1: Provide downstream version pin**

Give homelab this package target:

```bash
LINGO_LOOP_INSTALL_SPEC=lingo-loop==0.1.3
```

and this git fallback:

```bash
LINGO_LOOP_INSTALL_SPEC='lingo-loop @ git+https://github.com/artemVeduta/lingo-loop@v0.1.3'
```

Expected: downstream work updates homelab only after upstream release exists.

- [ ] **Step 2: Provide compute smoke commands from the approved design**

Handoff commands:

```bash
ssh compute "docker ps --filter name=hermes-language-tutor"
ssh compute "docker logs hermes-language-tutor --tail 150"
ssh compute "docker exec hermes-language-tutor sh -lc 'which tutor && tutor --help >/dev/null && env | grep \"^LANGUAGE_TUTOR_HOME=\"'"
ssh compute "docker exec hermes-language-tutor tutor doctor --json"
ssh compute "docker exec hermes-language-tutor sh -lc 'find /opt/data/skills/language-tutor /opt/data/skills/autonomous-ai-agents -maxdepth 3 -type f | sort'"
ssh compute "docker exec hermes-language-tutor hermes skills list"
ssh compute "docker exec hermes-language-tutor sh -lc 'grep -n \"quick_commands\\|command_allowlist\\|tutor-setup\" /opt/data/config.yaml'"
```

Expected after homelab consumes `0.1.3`:

- `tutor doctor --json` returns `"status": "ok"`.
- Hermes skills list includes `tutor-setup`, `tutor-vocab`, `tutor-writing`, `tutor-reading`, `tutor-lesson`, `tutor-progress`, and `tutor-judge`.
- Listed tutor skills are enabled.
- Telegram `/tutor-setup` is recognized and reaches the tutor agent.
- `/tutor-progress` uses persisted state from `/home/hermes/.tutor`.

- [ ] **Step 3: State upstream boundary**

Record this handoff note:

```text
Upstream lingo-loop v0.1.3 owns Hermes profile files and tutor skill bodies. Homelab should not copy or maintain placeholder tutor skill bodies; it should install lingo-loop and run tutor init --provider hermes --yes during language-tutor startup.
```

Expected: downstream implementation avoids duplicating tutor skill bodies.

---

## Self-Review

### Spec Coverage

- Managed profile files: Task 2 and Task 4.
- Managed skills hub files: Task 1, Task 2, Task 6, Task 8, Task 10.
- `HERMES_HOME` path behavior: Task 1 and Task 2.
- Drift repair and idempotence: Task 1 and Task 2.
- Missing packaged assets exact paths: Task 1 and Task 5.
- Skill command contract using installed `tutor`: Task 3.
- Helper scripts using `LANGUAGE_TUTOR_TUTOR_BIN`: Task 3.
- Dead `profile.skills: ../skills` removal: Task 4.
- `tutor doctor --json` package/migration/state/config validation without learner session creation: Task 5.
- Package metadata/assets: Task 7 and Task 8.
- Full upstream verification: Task 8 and Task 9.
- `github:yeet`, draft PR, GitHub Actions inspection with `gh`: Task 9.
- Release/tag creation for `v0.1.3`: Task 10.
- Post-release verification and rollout handoff around the approved design lines 177-240: Task 10 and Task 11.

### Red-Flag Scan

Search this plan before execution:

```bash
grep -RInE 'TBD|implement later|fill in details|appropriate error handling|add validation|handle edge cases|Similar to Task|Write tests for the above' docs/superpowers/plans/2026-05-31-lingo-loop-hermes-skill-hub-release.md
```

Expected: no matches.

### Type Consistency

- `ProviderAsset.source_root_rel`, `source_rel`, `target_area`, `target_rel`, `managed_rel`, and `source_display` are introduced in Task 2 and used consistently in tests.
- Hermes target area string is exactly `hermes_skills` in Task 2 tests and implementation.
- Doctor check prefix is exactly `provider_payload:` in Task 5 tests and implementation.
- Release version is exactly `0.1.3`; tag is exactly `v0.1.3`.

Plan complete and saved to `docs/superpowers/plans/2026-05-31-lingo-loop-hermes-skill-hub-release.md`. Two execution options:

1. Subagent-Driven (recommended) - dispatch a fresh subagent per task, review between tasks, fast iteration
2. Inline Execution - execute tasks in this session using executing-plans, batch execution with checkpoints

