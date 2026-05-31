# Lingo Loop Skill Hub Install Design Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make `tutor init --provider <hermes|openclaw|claude|codex>` install the shared seven-skill tutor hub from one packaged `skills/` asset tree, with Hermes/OpenClaw keeping their existing registration files and Claude/Codex dropping plugin registration.

**Architecture:** Add a `ManagedArea` contract so the shared base installer can copy and verify multiple independent managed trees per provider with the same byte-comparison logic. Provider subclasses stay thin: each declares registration and/or skills areas, and only Hermes/Codex/Claude override root resolution for their documented environment variables. Canonical skill markdown lives only under repo `skills/` and is shipped once under `language_tutor/_assets/skills/`.

**Tech Stack:** Python 3.12, Click CLI, Pydantic contracts, Hatch wheel `force-include`, pytest, pyright, ruff, local fake filesystem and command-runner seams.

---

## File Structure

- Modify `src/language_tutor/installer/providers/base.py`: add `ManagedArea`, shared `SKILL_FILES`, shared `SKILLS_AREA`, and multi-area detect/plan/apply/verify logic.
- Modify `src/language_tutor/installer/providers/claude.py`: declare only the skills area and resolve `CLAUDE_CONFIG_DIR`.
- Modify `src/language_tutor/installer/providers/codex.py`: declare only the skills area and resolve `CODEX_HOME`.
- Modify `src/language_tutor/installer/providers/hermes.py`: declare profile registration plus skills areas and resolve `HERMES_HOME`.
- Modify `src/language_tutor/installer/providers/openclaw.py`: declare plugin registration plus skills areas.
- Modify `src/language_tutor/installer/assets.py`: update docs and asset-root assumptions to remove Claude/Codex plugin packages.
- Modify `src/language_tutor/package_assets.py`: remove plugin manifests, old judge agent, and source `bin/tutor` from required runtime payloads; add `skills/tutor-judge/SKILL.md`.
- Modify `src/language_tutor/health.py`: make `tutor doctor --json` validate packaged runtime payloads directly, not a Claude plugin manifest.
- Modify `src/language_tutor/adapters/claude.py`: replace plugin component metadata with skill-hub component metadata.
- Modify `src/language_tutor/adapters/codex.py`: update docstring from local-marketplace plugin to personal skills hub.
- Modify `src/language_tutor/adapters/registry.py`: update Claude/Codex setup/update strings to personal skills hub wording.
- Create `skills/tutor-judge/SKILL.md`: moved canonical judge skill.
- Delete `agents/tutor-judge.md`: old judge agent asset.
- Delete `.claude-plugin/plugin.json`: dropped Claude plugin manifest.
- Delete `.codex-plugin/plugin.json`: dropped Codex plugin manifest.
- Delete `.agents/plugins/marketplace.json`: dropped Codex local marketplace registration.
- Modify `skills/tutor-setup/SKILL.md`, `skills/tutor-vocab/SKILL.md`, `skills/tutor-writing/SKILL.md`, `skills/tutor-reading/SKILL.md`, `skills/tutor-lesson/SKILL.md`, `skills/tutor-progress/SKILL.md`: replace `bin/tutor` command text with installed `tutor`.
- Modify `skills/tutor-vocab/scripts/run.py`, `skills/tutor-writing/scripts/run.py`, `skills/tutor-progress/scripts/run.py`: resolve `LANGUAGE_TUTOR_TUTOR_BIN` with default `tutor`.
- Modify `pyproject.toml`: update included package roots and wheel asset mappings.
- Modify installer, packaging, adapter, health, integration, privacy, and release tests listed in the tasks below.
- Modify `README.md` and `docs/install/{claude,codex,hermes,openclaw}.md`: describe skill hub installs rather than Claude/Codex plugin installs.

Shared skill file list used everywhere:

```python
SKILL_FILES: tuple[str, ...] = (
    "tutor-setup/SKILL.md",
    "tutor-vocab/SKILL.md",
    "tutor-vocab/scripts/run.py",
    "tutor-writing/SKILL.md",
    "tutor-writing/scripts/run.py",
    "tutor-reading/SKILL.md",
    "tutor-lesson/SKILL.md",
    "tutor-progress/SKILL.md",
    "tutor-progress/scripts/run.py",
    "tutor-judge/SKILL.md",
)
```

### Task 1: Multi-Area Provider Installer Core

**Files:**
- Modify: `src/language_tutor/installer/providers/base.py`
- Modify: `src/language_tutor/installer/providers/claude.py`
- Modify: `src/language_tutor/installer/providers/codex.py`
- Modify: `src/language_tutor/installer/providers/hermes.py`
- Modify: `src/language_tutor/installer/providers/openclaw.py`
- Create: `tests/installer/test_provider_areas.py`
- Modify: `tests/installer/test_bundled_tree.py`
- Modify: `tests/release/test_wheel_contents.py`

- [ ] **Step 1: Write failing provider-area tests**

Create `tests/installer/test_provider_areas.py`:

```python
from __future__ import annotations

from pathlib import Path

import pytest

from language_tutor.installer.assets import bundled_assets_root_for
from language_tutor.installer.protocol import InstallerContext
from language_tutor.installer.providers.base import SKILL_FILES, ManagedArea
from language_tutor.installer.providers.claude import ClaudeInstaller
from language_tutor.installer.providers.codex import CodexInstaller
from language_tutor.installer.providers.hermes import HermesInstaller
from language_tutor.installer.providers.openclaw import OpenClawInstaller
from language_tutor.installer.seams import FakeCommandRunner, FakeFilesystem
from language_tutor.installer.service import build_plan, run_init
from language_tutor.schemas import (
    HostId,
    InitRequest,
    ProviderActionKind,
    ProviderState,
)

HOME = Path("/fake/home")

INSTALLERS = (
    ClaudeInstaller,
    CodexInstaller,
    HermesInstaller,
    OpenClawInstaller,
)

ROOTS = {
    HostId.CLAUDE: ".claude",
    HostId.CODEX: ".codex",
    HostId.HERMES: ".hermes",
    HostId.OPENCLAW: ".openclaw",
}


def _ctx(files: dict[Path, str] | None = None) -> InstallerContext:
    fs = FakeFilesystem(home=HOME, files=files)
    for root in ROOTS.values():
        fs.mkdir(HOME / root)
    return InstallerContext(
        fs=fs,
        runner=FakeCommandRunner(
            available={host.value: f"/usr/bin/{host.value}" for host in HostId}
        ),
        bundled_assets_root=bundled_assets_root_for("skills").parent,
    )


def _skill_area(areas: tuple[ManagedArea, ...]) -> ManagedArea:
    matches = [area for area in areas if area.bundled_assets_root_rel == "skills"]
    assert len(matches) == 1
    return matches[0]


@pytest.mark.parametrize("installer_cls", INSTALLERS)
def test_every_provider_declares_the_same_flat_skill_area(installer_cls: type) -> None:
    area = _skill_area(installer_cls.profile.areas)
    assert area.managed_dir_rel == "skills"
    assert area.files == SKILL_FILES


def test_claude_and_codex_have_no_registration_area() -> None:
    assert ClaudeInstaller.profile.areas == (
        ManagedArea("skills", "skills", SKILL_FILES),
    )
    assert CodexInstaller.profile.areas == (
        ManagedArea("skills", "skills", SKILL_FILES),
    )


def test_hermes_and_openclaw_keep_registration_plus_skills() -> None:
    assert HermesInstaller.profile.areas[0] == ManagedArea(
        "hermes-profile",
        "profiles/lingo-loop",
        ("distribution.yaml", "config.yaml", "SOUL.md"),
    )
    assert HermesInstaller.profile.areas[1] == ManagedArea(
        "skills",
        "skills",
        SKILL_FILES,
    )
    assert OpenClawInstaller.profile.areas[0].bundled_assets_root_rel == "openclaw-plugin"
    assert OpenClawInstaller.profile.areas[0].managed_dir_rel == "plugins/lingo-loop"
    assert OpenClawInstaller.profile.areas[1] == ManagedArea(
        "skills",
        "skills",
        SKILL_FILES,
    )


def test_openclaw_missing_skill_sibling_triggers_one_skill_repair() -> None:
    skills_root = HOME / ".openclaw" / "skills"
    bundled_root = bundled_assets_root_for("skills")
    files: dict[Path, str] = {}
    for rel in SKILL_FILES:
        if rel == "tutor-judge/SKILL.md":
            continue
        files[skills_root / rel] = (bundled_root / rel).read_text(encoding="utf-8")
    plugin_root = HOME / ".openclaw" / "plugins" / "lingo-loop"
    plugin_bundle = bundled_assets_root_for("openclaw-plugin")
    for rel in OpenClawInstaller.profile.areas[0].files:
        files[plugin_root / rel] = (plugin_bundle / rel).read_text(encoding="utf-8")

    ctx = _ctx(files=files)
    plan = build_plan(ctx, InitRequest(providers=[HostId.OPENCLAW]))
    pp = plan.plans[0]

    assert pp.status.state == ProviderState.NEEDS_REPAIR
    write_actions = [a for a in pp.actions if a.kind == ProviderActionKind.WRITE_FILE]
    assert [a.target_path for a in write_actions] == [
        str(skills_root / "tutor-judge/SKILL.md")
    ]


def test_claude_init_writes_only_skill_area_files() -> None:
    ctx = _ctx()
    result = run_init(ctx, InitRequest(providers=[HostId.CLAUDE], yes=True))

    assert result.results[0].verified
    for rel in SKILL_FILES:
        assert ctx.fs.is_file(HOME / ".claude" / "skills" / rel)
    assert not ctx.fs.is_file(HOME / ".claude" / "plugins" / "lingo-loop" / "plugin.json")


def test_status_managed_files_lists_all_area_paths() -> None:
    ctx = _ctx()
    plan = build_plan(ctx, InitRequest(providers=[HostId.HERMES]))
    expected = [
        str(HOME / ".hermes" / "profiles" / "lingo-loop" / rel)
        for rel in ("distribution.yaml", "config.yaml", "SOUL.md")
    ]
    expected.extend(str(HOME / ".hermes" / "skills" / rel) for rel in SKILL_FILES)

    assert plan.plans[0].status.managed_files == expected
```

Update `tests/installer/test_bundled_tree.py` to read `OpenClawInstaller.profile.areas[0].files` for plugin registration files and `OpenClawInstaller.profile.areas[1].files` for skills. Replace direct `profile.files` references in this file with this helper:

```python
def _area_files(host: HostId, bundled_root: str) -> tuple[str, ...]:
    profile = {
        HostId.OPENCLAW: OpenClawInstaller.profile,
    }[host]
    matches = [
        area.files
        for area in profile.areas
        if area.bundled_assets_root_rel == bundled_root
    ]
    assert len(matches) == 1
    return matches[0]
```

Update `tests/release/test_wheel_contents.py` so `_expected_wheel_paths()` iterates every area:

```python
def _expected_wheel_paths() -> list[str]:
    paths: list[str] = []
    for profile in PROFILES:
        for area in profile.areas:
            for rel in area.files:
                paths.append(f"language_tutor/_assets/{area.bundled_assets_root_rel}/{rel}")
    return paths
```

- [ ] **Step 2: Run provider-area tests to verify they fail**

Run:

```bash
rtk uv run pytest tests/installer/test_provider_areas.py tests/installer/test_bundled_tree.py tests/release/test_wheel_contents.py -q
```

Expected: FAIL because `ManagedArea`, `SKILL_FILES`, and `ProviderProfile.areas` do not exist yet.

- [ ] **Step 3: Implement multi-area installer contracts**

In `src/language_tutor/installer/providers/base.py`, replace `ProviderProfile` and the path/content helper methods with:

```python
@dataclass(frozen=True)
class ManagedArea:
    bundled_assets_root_rel: str
    managed_dir_rel: str
    files: tuple[str, ...]


SKILL_FILES: tuple[str, ...] = (
    "tutor-setup/SKILL.md",
    "tutor-vocab/SKILL.md",
    "tutor-vocab/scripts/run.py",
    "tutor-writing/SKILL.md",
    "tutor-writing/scripts/run.py",
    "tutor-reading/SKILL.md",
    "tutor-lesson/SKILL.md",
    "tutor-progress/SKILL.md",
    "tutor-progress/scripts/run.py",
    "tutor-judge/SKILL.md",
)

SKILLS_AREA = ManagedArea(
    bundled_assets_root_rel="skills",
    managed_dir_rel="skills",
    files=SKILL_FILES,
)


@dataclass(frozen=True)
class ProviderProfile:
    host: HostId
    cli_name: str
    config_root_rel: str
    areas: tuple[ManagedArea, ...]
    next_command: str
```

In the same file, replace the single-area path helpers with:

```python
    def config_root(self) -> Path:
        return self.ctx.fs.home() / self.profile.config_root_rel

    def managed_dir_for(self, area: ManagedArea) -> Path:
        return self.config_root() / area.managed_dir_rel

    def bundled_root_for(self, area: ManagedArea) -> Path:
        return bundled_assets_root_for(area.bundled_assets_root_rel)

    def managed_files(self) -> list[Path]:
        paths: list[Path] = []
        for area in self.profile.areas:
            root = self.managed_dir_for(area)
            paths.extend(root / rel for rel in area.files)
        return paths

    def bundled_files(self) -> list[Path]:
        paths: list[Path] = []
        for area in self.profile.areas:
            root = self.bundled_root_for(area)
            paths.extend(root / rel for rel in area.files)
        return paths

    def _bundled_content(self, area: ManagedArea, rel: str) -> str:
        path = self.bundled_root_for(area) / rel
        if not path.exists():
            raise FileNotFoundError(
                f"bundled asset missing for {self.profile.host.value}: "
                f"{area.bundled_assets_root_rel}/{rel}"
            )
        return path.read_text(encoding="utf-8")

    def _iter_declared_files(self) -> list[tuple[ManagedArea, str, Path, Path]]:
        files: list[tuple[ManagedArea, str, Path, Path]] = []
        for area in self.profile.areas:
            managed_root = self.managed_dir_for(area)
            bundled_root = self.bundled_root_for(area)
            files.extend((area, rel, managed_root / rel, bundled_root / rel) for rel in area.files)
        return files
```

Replace every single-area use in `detect()`, `_divergent_files()`, `plan()`, `_bundled_rel_for_target()`, `apply()`, and `verify()` with this multi-area implementation:

```python
    def _blocked_status(
        self,
        repair_hint: str,
        *,
        detected_cli: bool,
        cli_path: str | None,
    ) -> ProviderStatus:
        return ProviderStatus(
            host=self.profile.host,
            display_name=self.display_name,
            state=ProviderState.BLOCKED,
            detected_cli=detected_cli,
            cli_path=cli_path,
            config_root=str(self.config_root()),
            managed_files=[str(p) for p in self.managed_files()],
            repair_hint=repair_hint,
            docs_url=self.docs_url,
        )

    def detect(self) -> ProviderStatus:
        cli_path = self.ctx.runner.which(self.profile.cli_name)
        detected_cli = cli_path is not None
        if not detected_cli:
            hint = (
                f"Install {self.display_name} first (CLI "
                f"'{self.profile.cli_name}' not on PATH); see {self.docs_url}"
            )
            return self._blocked_status(hint, detected_cli=False, cli_path=None)

        config_root = self.config_root()
        if not self.ctx.fs.is_dir(config_root):
            hint = (
                f"Run {self.profile.cli_name} once to create {config_root} "
                f"before installing lingo-loop assets; see {self.docs_url}"
            )
            return self._blocked_status(hint, detected_cli=True, cli_path=cli_path)

        missing_bundled: list[str] = []
        for area, rel, _managed_path, bundled_path in self._iter_declared_files():
            if not bundled_path.exists():
                missing_bundled.append(f"{area.bundled_assets_root_rel}/{rel}")
        if missing_bundled:
            joined = ", ".join(missing_bundled)
            hint = (
                f"Bundled asset(s) missing from the lingo-loop wheel for "
                f"{self.display_name} (packaging defect): {joined}; see {self.docs_url}"
            )
            return self._blocked_status(hint, detected_cli=True, cli_path=cli_path)

        any_missing = False
        any_drift = False
        for area, rel, managed_path, _bundled_path in self._iter_declared_files():
            if not self.ctx.fs.is_file(managed_path):
                any_missing = True
                continue
            expected = self._bundled_content(area, rel)
            current = self.ctx.fs.read_text(managed_path)
            if current != expected:
                any_drift = True

        if not any_missing and not any_drift:
            state = ProviderState.INSTALLED
            hint = None
        else:
            all_missing = all(
                not self.ctx.fs.is_file(managed_path)
                for _area, _rel, managed_path, _bundled_path in self._iter_declared_files()
            )
            if all_missing:
                state = ProviderState.AVAILABLE
                hint = None
            else:
                state = ProviderState.NEEDS_REPAIR
                hint = (
                    "Managed tree diverged from bundled assets; rerun to repair "
                    "missing or modified files."
                )

        return ProviderStatus(
            host=self.profile.host,
            display_name=self.display_name,
            state=state,
            detected_cli=True,
            cli_path=cli_path,
            config_root=str(self.config_root()),
            managed_files=[str(p) for p in self.managed_files()],
            repair_hint=hint,
            docs_url=self.docs_url,
        )

    def _divergent_files(self) -> list[tuple[ManagedArea, str, Path]]:
        divergent: list[tuple[ManagedArea, str, Path]] = []
        for area, rel, managed_path, _bundled_path in self._iter_declared_files():
            if not self.ctx.fs.is_file(managed_path):
                divergent.append((area, rel, managed_path))
                continue
            try:
                expected = self._bundled_content(area, rel)
            except FileNotFoundError:
                continue
            if self.ctx.fs.read_text(managed_path) != expected:
                divergent.append((area, rel, managed_path))
        return divergent

    def plan(self, request: InitRequest) -> ProviderPlan:
        del request
        status = self.detect()
        actions: list[ProviderInstallAction] = []
        if status.state == ProviderState.BLOCKED:
            actions.append(
                ProviderInstallAction(
                    kind=ProviderActionKind.BLOCK,
                    target_path=str(self.config_root()),
                    description=status.repair_hint or "Host prerequisite missing.",
                    stage=ProviderActionStage.BLOCKED,
                )
            )
        elif status.state == ProviderState.INSTALLED:
            actions.append(
                ProviderInstallAction(
                    kind=ProviderActionKind.SKIP,
                    target_path=str(self.config_root()),
                    description="Already installed; nothing to do.",
                    stage=ProviderActionStage.SKIPPED,
                )
            )
        else:
            divergent = self._divergent_files()
            if not divergent:
                actions.append(
                    ProviderInstallAction(
                        kind=ProviderActionKind.SKIP,
                        target_path=str(self.config_root()),
                        description="Already installed; nothing to do.",
                        stage=ProviderActionStage.SKIPPED,
                    )
                )
            else:
                for area, rel, target in divergent:
                    actions.append(
                        ProviderInstallAction(
                            kind=ProviderActionKind.WRITE_FILE,
                            target_path=str(target),
                            description=(
                                f"Write managed {self.display_name} file "
                                f"{rel} from bundled "
                                f"{area.bundled_assets_root_rel}/{rel}."
                            ),
                        )
                    )
        return ProviderPlan(
            host=self.profile.host,
            status=status,
            actions=actions,
            next_command=self.profile.next_command,
        )

    def _bundled_ref_for_target(self, target_path: str) -> tuple[ManagedArea, str] | None:
        target = Path(target_path)
        for area in self.profile.areas:
            managed_dir = self.managed_dir_for(area)
            try:
                rel = target.relative_to(managed_dir)
            except ValueError:
                continue
            rel_str = str(rel)
            if rel_str in area.files:
                return area, rel_str
        return None

    def apply(self, plan: ProviderPlan, dry_run: bool) -> list[ProviderInstallAction]:
        applied: list[ProviderInstallAction] = []
        for action in plan.actions:
            if action.kind == ProviderActionKind.WRITE_FILE and not dry_run:
                ref = self._bundled_ref_for_target(action.target_path)
                if ref is None:
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
                area, rel = ref
                try:
                    content = self._bundled_content(area, rel)
                    self.ctx.fs.write_text(Path(action.target_path), content)
                    applied.append(
                        action.model_copy(update={"stage": ProviderActionStage.APPLIED})
                    )
                except Exception as exc:
                    applied.append(
                        action.model_copy(
                            update={
                                "stage": ProviderActionStage.FAILED,
                                "error": str(exc),
                            }
                        )
                    )
            else:
                applied.append(action)
        return applied

    def verify(self) -> tuple[bool, str | None]:
        for area, rel, managed_path, _bundled_path in self._iter_declared_files():
            if not self.ctx.fs.is_file(managed_path):
                return False, f"managed file missing: {managed_path}"
            try:
                expected = self._bundled_content(area, rel)
            except FileNotFoundError as exc:
                return False, str(exc)
            current = self.ctx.fs.read_text(managed_path)
            if current != expected:
                return False, f"managed file content differs from bundled asset: {managed_path}"
        return True, None
```

- [ ] **Step 4: Convert provider profiles to area declarations**

Replace `src/language_tutor/installer/providers/claude.py` with:

```python
from __future__ import annotations

from language_tutor.installer.providers.base import (
    BaseProviderInstaller,
    ProviderProfile,
    SKILLS_AREA,
)
from language_tutor.schemas import HostId


class ClaudeInstaller(BaseProviderInstaller):
    profile = ProviderProfile(
        host=HostId.CLAUDE,
        cli_name="claude",
        config_root_rel=".claude",
        areas=(SKILLS_AREA,),
        next_command="Restart Claude Code if the skills directory was created mid-session.",
    )
```

Replace `src/language_tutor/installer/providers/codex.py` with:

```python
from __future__ import annotations

from language_tutor.installer.providers.base import (
    BaseProviderInstaller,
    ProviderProfile,
    SKILLS_AREA,
)
from language_tutor.schemas import HostId


class CodexInstaller(BaseProviderInstaller):
    profile = ProviderProfile(
        host=HostId.CODEX,
        cli_name="codex",
        config_root_rel=".codex",
        areas=(SKILLS_AREA,),
        next_command="Restart Codex so the personal skills hub is reloaded.",
    )
```

Replace `src/language_tutor/installer/providers/hermes.py` with:

```python
from __future__ import annotations

from language_tutor.installer.providers.base import (
    BaseProviderInstaller,
    ManagedArea,
    ProviderProfile,
    SKILLS_AREA,
)
from language_tutor.schemas import HostId

HERMES_PROFILE_AREA = ManagedArea(
    bundled_assets_root_rel="hermes-profile",
    managed_dir_rel="profiles/lingo-loop",
    files=("distribution.yaml", "config.yaml", "SOUL.md"),
)


class HermesInstaller(BaseProviderInstaller):
    profile = ProviderProfile(
        host=HostId.HERMES,
        cli_name="hermes",
        config_root_rel=".hermes",
        areas=(HERMES_PROFILE_AREA, SKILLS_AREA),
        next_command="Restart Hermes or run `hermes skills list` to confirm the tutor skills.",
    )
```

Replace `src/language_tutor/installer/providers/openclaw.py` with:

```python
from __future__ import annotations

from language_tutor.installer.providers.base import (
    BaseProviderInstaller,
    ManagedArea,
    ProviderProfile,
    SKILLS_AREA,
)
from language_tutor.schemas import HostId

OPENCLAW_PLUGIN_AREA = ManagedArea(
    bundled_assets_root_rel="openclaw-plugin",
    managed_dir_rel="plugins/lingo-loop",
    files=(
        "package.json",
        "openclaw.plugin.json",
        "tsconfig.json",
        "src/index.ts",
        "src/node-shims.d.ts",
        "dist/index.js",
        "dist/index.d.ts",
    ),
)


class OpenClawInstaller(BaseProviderInstaller):
    profile = ProviderProfile(
        host=HostId.OPENCLAW,
        cli_name="openclaw",
        config_root_rel=".openclaw",
        areas=(OPENCLAW_PLUGIN_AREA, SKILLS_AREA),
        next_command="Run `openclaw plugins install lingo-loop` to register the OpenClaw plugin.",
    )
```

- [ ] **Step 5: Run provider-area tests to verify they pass**

Run:

```bash
rtk uv run pytest tests/installer/test_provider_areas.py tests/installer/test_bundled_tree.py -q
```

Expected: PASS.

- [ ] **Step 6: Commit multi-area installer core**

```bash
rtk git add src/language_tutor/installer/providers/base.py src/language_tutor/installer/providers/claude.py src/language_tutor/installer/providers/codex.py src/language_tutor/installer/providers/hermes.py src/language_tutor/installer/providers/openclaw.py tests/installer/test_provider_areas.py tests/installer/test_bundled_tree.py tests/release/test_wheel_contents.py
rtk git commit -m "feat: install provider-managed skill areas"
```

### Task 2: Provider Root Resolvers

**Files:**
- Create: `tests/installer/test_provider_root_resolvers.py`
- Modify: `tests/installer/test_config_root_blocked.py`
- Modify: `tests/docs/test_install_docs.py`
- Modify: `src/language_tutor/installer/providers/claude.py`
- Modify: `src/language_tutor/installer/providers/codex.py`
- Modify: `src/language_tutor/installer/providers/hermes.py`

- [ ] **Step 1: Write resolver tests**

Create `tests/installer/test_provider_root_resolvers.py`:

```python
from __future__ import annotations

from pathlib import Path

from language_tutor.installer.assets import bundled_assets_root
from language_tutor.installer.protocol import InstallerContext
from language_tutor.installer.providers.claude import ClaudeInstaller
from language_tutor.installer.providers.codex import CodexInstaller
from language_tutor.installer.providers.hermes import HermesInstaller
from language_tutor.installer.seams import FakeCommandRunner, FakeFilesystem
from language_tutor.schemas import HostId

HOME = Path("/fake/home")


def _ctx() -> InstallerContext:
    return InstallerContext(
        fs=FakeFilesystem(home=HOME),
        runner=FakeCommandRunner(
            available={host.value: f"/usr/bin/{host.value}" for host in HostId}
        ),
        bundled_assets_root=bundled_assets_root(),
    )


def test_hermes_home_overrides_fake_home(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setenv("HERMES_HOME", "/opt/data")
    assert HermesInstaller(_ctx()).config_root() == Path("/opt/data")


def test_hermes_falls_back_to_home_dot_hermes(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.delenv("HERMES_HOME", raising=False)
    assert HermesInstaller(_ctx()).config_root() == HOME / ".hermes"


def test_codex_home_overrides_fake_home(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setenv("CODEX_HOME", "/var/codex")
    assert CodexInstaller(_ctx()).config_root() == Path("/var/codex")


def test_codex_falls_back_to_home_dot_codex(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.delenv("CODEX_HOME", raising=False)
    assert CodexInstaller(_ctx()).config_root() == HOME / ".codex"


def test_claude_config_dir_overrides_fake_home(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setenv("CLAUDE_CONFIG_DIR", "/var/claude")
    assert ClaudeInstaller(_ctx()).config_root() == Path("/var/claude")


def test_claude_falls_back_to_home_dot_claude(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.delenv("CLAUDE_CONFIG_DIR", raising=False)
    assert ClaudeInstaller(_ctx()).config_root() == HOME / ".claude"
```

Update `tests/installer/test_config_root_blocked.py` so `_HOST_ROOT` stays:

```python
_HOST_ROOT = {
    HostId.CLAUDE: ".claude",
    HostId.CODEX: ".codex",
    HostId.HERMES: ".hermes",
    HostId.OPENCLAW: ".openclaw",
}
```

and add this test:

```python
def test_hermes_missing_env_root_reports_hermes_home(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setenv("HERMES_HOME", "/opt/data")
    ctx = _ctx(precreated_roots=[])
    result = run_init(ctx, InitRequest(providers=[HostId.HERMES], yes=True))
    hint = result.results[0].repair_hint
    assert hint is not None
    assert "/opt/data" in hint
    assert str(HOME / ".hermes") not in hint
```

- [ ] **Step 2: Run resolver tests to verify they fail before overrides**

Run:

```bash
rtk uv run pytest tests/installer/test_provider_root_resolvers.py tests/installer/test_config_root_blocked.py::test_hermes_missing_env_root_reports_hermes_home -q
```

Expected: FAIL before provider-specific `config_root()` overrides are present.

- [ ] **Step 3: Add provider overrides and adjust docs test expectations**

In `src/language_tutor/installer/providers/claude.py`, add these imports:

```python
import os
from pathlib import Path
```

and add this method to `ClaudeInstaller`:

```python
    def config_root(self) -> Path:
        configured = os.environ.get("CLAUDE_CONFIG_DIR")
        if configured:
            return Path(configured).expanduser()
        return super().config_root()
```

In `src/language_tutor/installer/providers/codex.py`, add these imports:

```python
import os
from pathlib import Path
```

and add this method to `CodexInstaller`:

```python
    def config_root(self) -> Path:
        configured = os.environ.get("CODEX_HOME")
        if configured:
            return Path(configured).expanduser()
        return super().config_root()
```

In `src/language_tutor/installer/providers/hermes.py`, add these imports:

```python
import os
from pathlib import Path
```

and add this method to `HermesInstaller`:

```python
    def config_root(self) -> Path:
        configured = os.environ.get("HERMES_HOME")
        if configured:
            return Path(configured).expanduser()
        return super().config_root()
```

In `tests/docs/test_install_docs.py`, any expected Claude/Codex plugin target should become the provider root from `config_root()` plus `skills`; any Hermes root expectation should use `HERMES_HOME` when set. Use this assertion shape in the config-root section:

```python
expected = _installer_config_root(HOST_TO_INSTALLER[host])
assert expected == Path(documented_root).expanduser()
```

For Claude docs, `documented_root` must be `~/.claude`. For Codex docs, `documented_root` must be `~/.codex`. For Hermes docs, the test must accept `HERMES_HOME` as the first resolver and `~/.hermes` as fallback.

- [ ] **Step 4: Run resolver tests to verify they pass**

Run:

```bash
rtk uv run pytest tests/installer/test_provider_root_resolvers.py tests/installer/test_config_root_blocked.py tests/docs/test_install_docs.py -q
```

Expected: PASS.

- [ ] **Step 5: Commit resolver tests and docs-test updates**

```bash
rtk git add tests/installer/test_provider_root_resolvers.py tests/installer/test_config_root_blocked.py tests/docs/test_install_docs.py src/language_tutor/installer/providers/claude.py src/language_tutor/installer/providers/codex.py src/language_tutor/installer/providers/hermes.py
rtk git commit -m "test: cover provider config root resolvers"
```

### Task 3: Canonical Skill Payload Tree

**Files:**
- Create: `skills/tutor-judge/SKILL.md`
- Delete: `agents/tutor-judge.md`
- Modify: `skills/tutor-setup/SKILL.md`
- Modify: `skills/tutor-vocab/SKILL.md`
- Modify: `skills/tutor-vocab/scripts/run.py`
- Modify: `skills/tutor-writing/SKILL.md`
- Modify: `skills/tutor-writing/scripts/run.py`
- Modify: `skills/tutor-reading/SKILL.md`
- Modify: `skills/tutor-lesson/SKILL.md`
- Modify: `skills/tutor-progress/SKILL.md`
- Modify: `skills/tutor-progress/scripts/run.py`
- Create: `tests/installer/test_skill_payload_contract.py`
- Modify: `tests/adapter_contract/test_plugin_surface.py`
- Modify: `tests/unit/test_skill_lifecycle_tokens.py`

- [ ] **Step 1: Dispatch the required skill-review subagent**

Use `superpowers:subagent-driven-development` at execution time and dispatch one subagent for this skill family. The subagent prompt must include:

```text
Review the seven tutor skill files for the skill-hub install change. Read the local helper at /Users/artem.veduta/.claude/plugins/cache/claude-plugins-official/superpowers/5.1.0/skills/writing-skills before editing or approving skill markdown. Verify these requirements: frontmatter has only name and description; all commands use installed `tutor`, not `bin/tutor`; helper scripts resolve os.environ.get("LANGUAGE_TUTOR_TUTOR_BIN", "tutor"); tutor-judge lives at skills/tutor-judge/SKILL.md; no pedagogy or persistence logic is duplicated in skill prose. Report changed files and RED/GREEN/REFACTOR evidence.
```

- [ ] **Step 2: Write failing skill payload contract tests**

Create `tests/installer/test_skill_payload_contract.py`:

```python
from __future__ import annotations

from pathlib import Path

from language_tutor.installer.providers.base import SKILL_FILES

REPO_ROOT = Path(__file__).resolve().parents[2]


def _frontmatter_keys(path: Path) -> set[str]:
    lines = path.read_text(encoding="utf-8").splitlines()
    assert lines[0] == "---", path
    end = lines.index("---", 1)
    keys: set[str] = set()
    for line in lines[1:end]:
        key, _sep, _value = line.partition(":")
        keys.add(key)
    return keys


def test_canonical_skill_tree_contains_exact_files() -> None:
    actual = sorted(
        str(path.relative_to(REPO_ROOT / "skills"))
        for path in (REPO_ROOT / "skills").rglob("*")
        if path.is_file()
    )
    assert actual == sorted(SKILL_FILES)


def test_judge_is_skill_not_agent() -> None:
    assert (REPO_ROOT / "skills" / "tutor-judge" / "SKILL.md").exists()
    assert not (REPO_ROOT / "agents" / "tutor-judge.md").exists()


def test_skill_frontmatter_is_plain_name_description_only() -> None:
    for rel in SKILL_FILES:
        if not rel.endswith("SKILL.md"):
            continue
        assert _frontmatter_keys(REPO_ROOT / "skills" / rel) == {"name", "description"}


def test_skill_markdown_uses_console_tutor_not_source_bin() -> None:
    offenders: list[str] = []
    for rel in SKILL_FILES:
        path = REPO_ROOT / "skills" / rel
        if path.suffix != ".md":
            continue
        text = path.read_text(encoding="utf-8")
        if "bin/tutor" in text:
            offenders.append(rel)
    assert offenders == []


def test_helper_scripts_resolve_tutor_bin_from_environment() -> None:
    scripts = [
        "tutor-vocab/scripts/run.py",
        "tutor-writing/scripts/run.py",
        "tutor-progress/scripts/run.py",
    ]
    for rel in scripts:
        text = (REPO_ROOT / "skills" / rel).read_text(encoding="utf-8")
        assert 'os.environ.get("LANGUAGE_TUTOR_TUTOR_BIN", "tutor")' in text
        assert "ROOT = Path(__file__)" not in text
        assert 'ROOT / "bin" / "tutor"' not in text
```

Update `tests/adapter_contract/test_plugin_surface.py` into a skill-hub surface test:

```python
def test_skill_hub_surface_files_exist() -> None:
    for path in [
        "skills/tutor-setup/SKILL.md",
        "skills/tutor-vocab/SKILL.md",
        "skills/tutor-vocab/scripts/run.py",
        "skills/tutor-writing/SKILL.md",
        "skills/tutor-writing/scripts/run.py",
        "skills/tutor-progress/SKILL.md",
        "skills/tutor-progress/scripts/run.py",
        "skills/tutor-reading/SKILL.md",
        "skills/tutor-lesson/SKILL.md",
        "skills/tutor-judge/SKILL.md",
    ]:
        assert Path(path).exists(), path
```

- [ ] **Step 3: Run skill payload tests to verify they fail**

Run:

```bash
rtk uv run pytest tests/installer/test_skill_payload_contract.py tests/adapter_contract/test_plugin_surface.py -q
```

Expected: FAIL because `skills/tutor-judge/SKILL.md` is missing and existing skills still mention `bin/tutor`.

- [ ] **Step 4: Move judge skill and update helper scripts**

Create `skills/tutor-judge/SKILL.md` with exactly:

```markdown
---
name: tutor-judge
description: Grades a learner answer and returns only a FeedbackEnvelope JSON object using the supplied allowed_error_tags.
---

# tutor-judge

Return only a `FeedbackEnvelope` JSON object. No prose outside JSON.

Use the `allowed_error_tags` supplied in input. Do not invent tags. Keep `confidence` one of `high`, `medium`, or `low`. Low confidence cannot be definitive high-severity correction. Include `next_drill_hint`.
```

Delete `agents/tutor-judge.md`.

Replace each helper script `skills/tutor-vocab/scripts/run.py`, `skills/tutor-writing/scripts/run.py`, and `skills/tutor-progress/scripts/run.py` with:

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

- [ ] **Step 5: Replace source-relative skill commands**

In these six files, replace every literal `` `bin/tutor`` with `` `tutor`` and every literal `bin/tutor` outside code ticks with `tutor`:

```text
skills/tutor-setup/SKILL.md
skills/tutor-vocab/SKILL.md
skills/tutor-writing/SKILL.md
skills/tutor-reading/SKILL.md
skills/tutor-lesson/SKILL.md
skills/tutor-progress/SKILL.md
```

Do not change the command arguments. Example transformation:

```markdown
- Start queue: `bin/tutor vocab start --json`
```

becomes:

```markdown
- Start queue: `tutor vocab start --json`
```

- [ ] **Step 6: Run skill payload tests to verify they pass**

Run:

```bash
rtk uv run pytest tests/installer/test_skill_payload_contract.py tests/adapter_contract/test_plugin_surface.py tests/unit/test_skill_lifecycle_tokens.py -q
```

Expected: PASS.

- [ ] **Step 7: Commit canonical skill payload changes**

```bash
rtk git add skills/tutor-judge/SKILL.md skills/tutor-setup/SKILL.md skills/tutor-vocab/SKILL.md skills/tutor-vocab/scripts/run.py skills/tutor-writing/SKILL.md skills/tutor-writing/scripts/run.py skills/tutor-reading/SKILL.md skills/tutor-lesson/SKILL.md skills/tutor-progress/SKILL.md skills/tutor-progress/scripts/run.py tests/installer/test_skill_payload_contract.py tests/adapter_contract/test_plugin_surface.py tests/unit/test_skill_lifecycle_tokens.py
rtk git rm agents/tutor-judge.md
rtk git commit -m "feat: make judge a shared tutor skill"
```

### Task 4: Runtime Payload and Wheel Packaging

**Files:**
- Modify: `src/language_tutor/package_assets.py`
- Modify: `src/language_tutor/installer/assets.py`
- Modify: `src/language_tutor/health.py`
- Modify: `tests/unit/test_package_assets.py`
- Modify: `tests/unit/test_health.py`
- Modify: `tests/release/test_wheel_contents.py`
- Modify: `pyproject.toml`

- [ ] **Step 1: Write failing runtime payload tests**

In `tests/unit/test_package_assets.py`, replace `test_required_runtime_payloads_cover_migrations_and_skill_helpers()` with:

```python
def test_required_runtime_payloads_cover_migrations_and_skill_helpers() -> None:
    assert "migrations/001_initial.sql" in REQUIRED_RUNTIME_PAYLOADS
    assert "migrations/004_sessions_checkpoints.sql" in REQUIRED_RUNTIME_PAYLOADS
    assert "skills/tutor-setup/SKILL.md" in REQUIRED_RUNTIME_PAYLOADS
    assert "skills/tutor-vocab/scripts/run.py" in REQUIRED_RUNTIME_PAYLOADS
    assert "skills/tutor-writing/scripts/run.py" in REQUIRED_RUNTIME_PAYLOADS
    assert "skills/tutor-progress/scripts/run.py" in REQUIRED_RUNTIME_PAYLOADS
    assert "skills/tutor-judge/SKILL.md" in REQUIRED_RUNTIME_PAYLOADS
    assert "agents/tutor-judge.md" not in REQUIRED_RUNTIME_PAYLOADS
    assert "bin/tutor" not in REQUIRED_RUNTIME_PAYLOADS
    assert ".claude-plugin/plugin.json" not in REQUIRED_RUNTIME_PAYLOADS
    assert ".codex-plugin/plugin.json" not in REQUIRED_RUNTIME_PAYLOADS
```

In `tests/unit/test_health.py`, replace `_make_source_tree()` with:

```python
def _make_source_tree(root: Path) -> None:
    for skill in (
        "tutor-setup",
        "tutor-vocab",
        "tutor-writing",
        "tutor-progress",
        "tutor-reading",
        "tutor-lesson",
        "tutor-judge",
    ):
        skill_dir = root / "skills" / skill
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text("# skill", encoding="utf-8")
    for script in (
        "skills/tutor-vocab/scripts/run.py",
        "skills/tutor-writing/scripts/run.py",
        "skills/tutor-progress/scripts/run.py",
    ):
        path = root / script
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("# script\n", encoding="utf-8")
```

Replace `_make_runtime_payload()` skill entries with the shared skill list and remove `agents/tutor-judge.md` and `bin/tutor`:

```python
        "skills/tutor-reading/SKILL.md",
        "skills/tutor-lesson/SKILL.md",
        "skills/tutor-judge/SKILL.md",
```

Replace `test_source_checkout_all_plugin_checks_ok()` with:

```python
def test_source_checkout_runtime_payload_checks_ok(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    _make_source_tree(repo)
    for rel in (
        "migrations/001_initial.sql",
        "migrations/002_vocab_depth.sql",
        "migrations/003_progress_indexes.sql",
        "migrations/004_sessions_checkpoints.sql",
    ):
        path = repo / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("-- sql\n", encoding="utf-8")
    monkeypatch.setenv("LANGUAGE_TUTOR_BUNDLED_ASSETS", str(repo))

    report = doctor(_paths(tmp_path), repo)
    statuses = _by_name(report)

    assert statuses["runtime_payload:skills/tutor-judge/SKILL.md"] == "ok"
    assert "manifest" not in statuses
    assert report.status == "ok"
```

Replace `test_wheel_install_manifest_ok_source_checks_na()` with:

```python
def test_wheel_install_runtime_payloads_ok(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fake_repo = tmp_path / "site-packages-adjacent"
    fake_repo.mkdir()
    assets = tmp_path / "_assets"
    _make_runtime_payload(assets)
    monkeypatch.setenv("LANGUAGE_TUTOR_BUNDLED_ASSETS", str(assets))

    report = doctor(_paths(tmp_path), fake_repo)
    statuses = _by_name(report)

    assert statuses["runtime_payload:skills/tutor-judge/SKILL.md"] == "ok"
    assert "manifest" not in statuses
    assert "fail" not in statuses.values()
    assert report.status == "ok"
```

- [ ] **Step 2: Run runtime payload tests to verify they fail**

Run:

```bash
rtk uv run pytest tests/unit/test_package_assets.py tests/unit/test_health.py tests/release/test_wheel_contents.py -q
```

Expected: FAIL because required payloads and doctor still reference the old plugin/agent/bin surface.

- [ ] **Step 3: Update required runtime payloads**

Replace `REQUIRED_SKILL_PAYLOAD_FILES` in `src/language_tutor/package_assets.py` with:

```python
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
    "skills/tutor-judge/SKILL.md",
)
```

In `src/language_tutor/installer/assets.py`, replace the module docstring first paragraph with:

```python
"""Bundled provider asset resolution.

`tutor init` writes managed registration files for Hermes/OpenClaw and the
shared flat skill hub for every provider. Provider areas declare a bundled
asset directory such as ``skills``, ``openclaw-plugin``, or ``hermes-profile``.
Editable installs resolve those directories from the repo root; wheel installs
resolve them from ``language_tutor/_assets``.
"""
```

Replace `_HOST_PACKAGE_SENTINELS` with:

```python
_HOST_PACKAGE_SENTINELS: dict[str, str] = {
    "skills": "tutor-setup/SKILL.md",
    "openclaw-plugin": "package.json",
    "hermes-profile": "distribution.yaml",
}
```

- [ ] **Step 4: Update doctor to validate runtime payloads only**

In `src/language_tutor/health.py`, remove:

```python
from language_tutor.adapters.claude import plugin_root_components
from language_tutor.installer.assets import bundled_assets_root
```

Remove `_MANIFEST_COMPONENT = "manifest"` and remove the whole manifest/source-only component block. Keep the Python runtime check, runtime payload loop, directory permission checks, YAML check, and SQLite migration check. The start of `doctor()` should be:

```python
def doctor(paths: TutorPaths, repo_root: Path) -> DoctorReport:
    del repo_root
    ensure_dirs(paths)
    checks: list[DoctorCheck] = []
    checks.append(
        DoctorCheck(
            name="python_runtime",
            status="ok" if sys.version_info >= (3, 12) else "fail",
            repair_hint="Use Python 3.12+.",
        )
    )
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

- [ ] **Step 5: Update wheel force-includes**

In `pyproject.toml`, remove these `include` entries:

```toml
  "/agents",
  "/.claude-plugin/plugin.json",
  "/.codex-plugin/plugin.json",
  "/.agents/plugins/marketplace.json",
```

Remove these `force-include` mappings:

```toml
".claude-plugin/plugin.json" = "language_tutor/_assets/.claude-plugin/plugin.json"
".codex-plugin/plugin.json" = "language_tutor/_assets/.codex-plugin/plugin.json"
"agents/tutor-judge.md" = "language_tutor/_assets/agents/tutor-judge.md"
"bin/tutor" = "language_tutor/_assets/bin/tutor"
```

Add this mapping:

```toml
"skills/tutor-judge/SKILL.md" = "language_tutor/_assets/skills/tutor-judge/SKILL.md"
```

- [ ] **Step 6: Run packaging and health tests to verify they pass**

Run:

```bash
rtk uv run pytest tests/unit/test_package_assets.py tests/unit/test_health.py tests/release/test_wheel_contents.py -q
```

Expected: PASS.

- [ ] **Step 7: Commit payload and wheel packaging changes**

```bash
rtk git add src/language_tutor/package_assets.py src/language_tutor/installer/assets.py src/language_tutor/health.py tests/unit/test_package_assets.py tests/unit/test_health.py tests/release/test_wheel_contents.py pyproject.toml
rtk git commit -m "build: ship shared skill hub assets"
```

### Task 5: Init CLI Integration and Privacy Boundaries

**Files:**
- Modify: `tests/unit/test_installer_service.py`
- Modify: `tests/integration/test_tutor_init_cli.py`
- Modify: `tests/unit/test_installer_privacy.py`
- Modify: `tests/integration/test_local_data_ownership.py`

- [ ] **Step 1: Update init service tests for skill destinations**

In `tests/unit/test_installer_service.py`, replace `_managed_path()` and `_bundled()` with:

```python
def _managed_path(host: HostId) -> Path:
    suffix = {
        HostId.CLAUDE: ".claude/skills/tutor-setup/SKILL.md",
        HostId.CODEX: ".codex/skills/tutor-setup/SKILL.md",
        HostId.HERMES: ".hermes/skills/tutor-setup/SKILL.md",
        HostId.OPENCLAW: ".openclaw/skills/tutor-setup/SKILL.md",
    }[host]
    return HOME / suffix


def _bundled(host: HostId) -> str:
    del host
    return (bundled_assets_root() / "skills/tutor-setup/SKILL.md").read_text(
        encoding="utf-8"
    )
```

Add this Hermes registration assertion to `test_detect_available_writes_file()` after `run_init()`:

```python
    if host == HostId.HERMES:
        assert ctx.fs.is_file(HOME / ".hermes/profiles/lingo-loop/distribution.yaml")
```

Add this OpenClaw registration assertion:

```python
    if host == HostId.OPENCLAW:
        assert ctx.fs.is_file(HOME / ".openclaw/plugins/lingo-loop/package.json")
```

- [ ] **Step 2: Update CLI integration tests for all required provider files**

In `tests/integration/test_tutor_init_cli.py`, replace `PROVIDER_MANAGED_FILES` with:

```python
PROVIDER_REQUIRED_FILES = [
    ("claude", [".claude/skills/tutor-setup/SKILL.md", ".claude/skills/tutor-judge/SKILL.md"]),
    ("codex", [".codex/skills/tutor-setup/SKILL.md", ".codex/skills/tutor-judge/SKILL.md"]),
    (
        "hermes",
        [
            ".hermes/profiles/lingo-loop/distribution.yaml",
            ".hermes/skills/tutor-setup/SKILL.md",
            ".hermes/skills/tutor-judge/SKILL.md",
        ],
    ),
    (
        "openclaw",
        [
            ".openclaw/plugins/lingo-loop/package.json",
            ".openclaw/skills/tutor-setup/SKILL.md",
            ".openclaw/skills/tutor-judge/SKILL.md",
        ],
    ),
]
```

Replace the parametrized test signature and managed-file assertion with:

```python
@pytest.mark.parametrize("provider, required_rels", PROVIDER_REQUIRED_FILES)
def test_init_writes_managed_file_and_is_idempotent_per_provider(
    provider: str,
    required_rels: list[str],
    fake_clis: dict[str, str],
    fake_home: Path,
    no_tty: None,
) -> None:
    del fake_clis, no_tty
    runner = CliRunner()
    first = runner.invoke(main, ["init", "--provider", provider, "--yes", "--json"])
    assert first.exit_code == 0, first.output
    for rel in required_rels:
        managed = fake_home / rel
        assert managed.exists(), f"{provider}: expected managed file at {managed}"

    second = runner.invoke(main, ["init", "--provider", provider, "--yes", "--json"])
    assert second.exit_code == 0, second.output
    payload = json.loads(second.output)
    r = payload["results"][0]
    assert r["host"] == provider
    assert r["status"]["state"] == "installed"
    assert r["actions"][0]["kind"] == "skip"
    assert r["verified"] is True
```

Update `test_init_dry_run_json_emits_init_result()` and interactive-selection assertions to check that `.claude/skills/tutor-setup/SKILL.md` exists or does not exist instead of `.claude/plugins/lingo-loop/plugin.json`.

- [ ] **Step 3: Update privacy tests for skill hubs**

In `tests/unit/test_installer_privacy.py`, replace the final lingo-loop scoping assertion in `test_init_writes_only_under_per_host_config_root()` with:

```python
        is_registration_file = "lingo-loop" in rel.parts
        is_skill_file = len(rel.parts) >= 3 and rel.parts[1] == "skills"
        assert is_registration_file or is_skill_file, (
            f"managed file not scoped to registration or skills area: {path}"
        )
```

Update `test_repair_does_not_touch_unrelated_files()` to precreate and preserve an unrelated skill:

```python
def test_repair_does_not_touch_unrelated_files() -> None:
    ctx = _ctx_all_hosts()
    settings = HOME / ".claude" / "settings.json"
    unrelated_skill = HOME / ".claude" / "skills" / "gws-search" / "SKILL.md"
    ctx.fs.write_text(settings, '{"user":"data"}')
    ctx.fs.write_text(unrelated_skill, "# user skill\n")

    run_init(ctx, InitRequest(providers=[HostId.CLAUDE], yes=True))

    assert ctx.fs.read_text(settings) == '{"user":"data"}'
    assert ctx.fs.read_text(unrelated_skill) == "# user skill\n"
```

In `tests/integration/test_local_data_ownership.py`, remove `.claude-plugin`, `.codex-plugin`, `.agents/plugins`, and `agents` from package roots scanned for shipped state. Keep `openclaw-plugin`, `hermes-profile`, and `skills`.

- [ ] **Step 4: Run init and privacy tests to verify they fail before implementation is complete**

Run:

```bash
rtk uv run pytest tests/unit/test_installer_service.py tests/integration/test_tutor_init_cli.py tests/unit/test_installer_privacy.py tests/integration/test_local_data_ownership.py -q
```

Expected before Tasks 1-4 are applied: FAIL due old plugin targets. Expected after Tasks 1-4 are applied and this task's test edits are complete: PASS.

- [ ] **Step 5: Run init and privacy tests to verify they pass**

Run:

```bash
rtk uv run pytest tests/unit/test_installer_service.py tests/integration/test_tutor_init_cli.py tests/unit/test_installer_privacy.py tests/integration/test_local_data_ownership.py -q
```

Expected: PASS.

- [ ] **Step 6: Commit init and privacy test updates**

```bash
rtk git add tests/unit/test_installer_service.py tests/integration/test_tutor_init_cli.py tests/unit/test_installer_privacy.py tests/integration/test_local_data_ownership.py
rtk git commit -m "test: verify skill hub init writes"
```

### Task 6: Drop Claude/Codex Plugin Surfaces

**Files:**
- Delete: `.claude-plugin/plugin.json`
- Delete: `.codex-plugin/plugin.json`
- Delete: `.agents/plugins/marketplace.json`
- Modify: `src/language_tutor/adapters/claude.py`
- Modify: `src/language_tutor/adapters/codex.py`
- Modify: `src/language_tutor/adapters/registry.py`
- Modify: `tests/adapter_contract/test_claude_adapter.py`
- Modify: `tests/adapter_contract/test_codex_adapter.py`
- Modify: `tests/packaging/test_claude_plugin_package.py`
- Modify: `tests/packaging/test_codex_plugin_package.py`
- Modify: `tests/packaging/test_distribution_privacy.py`
- Modify: `tests/packaging/test_no_hook_privacy.py`
- Modify: `tests/packaging/test_host_setup_profiles.py`

- [ ] **Step 1: Write failing absence tests for plugin artifacts**

Replace `tests/packaging/test_claude_plugin_package.py` with:

```python
from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

REQUIRED_SKILLS = (
    "skills/tutor-setup/SKILL.md",
    "skills/tutor-vocab/SKILL.md",
    "skills/tutor-vocab/scripts/run.py",
    "skills/tutor-writing/SKILL.md",
    "skills/tutor-writing/scripts/run.py",
    "skills/tutor-progress/SKILL.md",
    "skills/tutor-progress/scripts/run.py",
    "skills/tutor-reading/SKILL.md",
    "skills/tutor-lesson/SKILL.md",
    "skills/tutor-judge/SKILL.md",
)


def test_claude_personal_skill_hub_components_present() -> None:
    for rel in REQUIRED_SKILLS:
        assert (REPO_ROOT / rel).exists(), rel


def test_claude_plugin_manifest_removed() -> None:
    assert not (REPO_ROOT / ".claude-plugin" / "plugin.json").exists()


def test_claude_package_has_no_hook_directory() -> None:
    assert not (REPO_ROOT / "hooks").exists()
```

Replace `tests/packaging/test_codex_plugin_package.py` with:

```python
from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


def test_codex_plugin_manifest_removed() -> None:
    assert not (REPO_ROOT / ".codex-plugin" / "plugin.json").exists()


def test_codex_marketplace_registration_removed() -> None:
    assert not (REPO_ROOT / ".agents" / "plugins" / "marketplace.json").exists()


def test_root_skills_available_for_codex() -> None:
    assert (REPO_ROOT / "skills/tutor-setup/SKILL.md").exists()
    assert (REPO_ROOT / "skills/tutor-judge/SKILL.md").exists()
```

In `tests/adapter_contract/test_claude_adapter.py`, replace `test_claude_baseline_preserved()` with:

```python
def test_claude_skill_hub_baseline_preserved() -> None:
    for rel in ("skills/tutor-setup/SKILL.md", "skills/tutor-judge/SKILL.md"):
        assert (REPO_ROOT / rel).exists()
    assert not (REPO_ROOT / ".claude-plugin" / "plugin.json").exists()
    assert not (REPO_ROOT / "hooks").exists(), "hooks/ removed in spec 007"
```

In `tests/adapter_contract/test_codex_adapter.py`, replace manifest assertions with:

```python
def test_codex_uses_personal_skill_hub_surface() -> None:
    assert (REPO_ROOT / "skills/tutor-setup/SKILL.md").exists()
    assert (REPO_ROOT / "skills/tutor-judge/SKILL.md").exists()
    assert not (REPO_ROOT / ".codex-plugin" / "plugin.json").exists()
```

- [ ] **Step 2: Run plugin-surface tests to verify they fail**

Run:

```bash
rtk uv run pytest tests/packaging/test_claude_plugin_package.py tests/packaging/test_codex_plugin_package.py tests/adapter_contract/test_claude_adapter.py tests/adapter_contract/test_codex_adapter.py -q
```

Expected: FAIL because plugin manifest files still exist and adapter metadata still says plugin.

- [ ] **Step 3: Replace adapter metadata**

Replace `src/language_tutor/adapters/claude.py` with:

```python
from __future__ import annotations

from language_tutor.adapters.registry import capability_profile_for
from language_tutor.schemas import AdapterCapabilityProfile, HostId


def capability_profile() -> AdapterCapabilityProfile:
    """Claude capability profile. No-hook lifecycle; skills live in the personal hub."""
    return capability_profile_for(HostId.CLAUDE.value)


def skill_hub_components() -> dict[str, str]:
    return {
        "setup_skill": "skills/tutor-setup/SKILL.md",
        "vocab_skill": "skills/tutor-vocab/SKILL.md",
        "writing_skill": "skills/tutor-writing/SKILL.md",
        "reading_skill": "skills/tutor-reading/SKILL.md",
        "lesson_skill": "skills/tutor-lesson/SKILL.md",
        "progress_skill": "skills/tutor-progress/SKILL.md",
        "judge_skill": "skills/tutor-judge/SKILL.md",
    }
```

Replace `src/language_tutor/adapters/codex.py` docstring with:

```python
"""Codex host adapter.

Codex discovers tutor skills from the user's personal skills hub and boots the
tutor on the first tutor-skill invocation. Setup is package-only. This module
exposes the host capability profile and leaves pedagogy, feedback, progress,
and learner state to the tutor core.
"""
```

In `src/language_tutor/adapters/registry.py`, update these fields:

```python
        setup_entry_point="personal skills hub at <CLAUDE_CONFIG_DIR|~/.claude>/skills",
        update_behavior="restart Claude Code if the skills directory was created mid-session",
```

and:

```python
        setup_entry_point="personal skills hub at <CODEX_HOME|~/.codex>/skills",
        update_behavior="restart Codex so personal skills are reloaded",
```

- [ ] **Step 4: Delete plugin artifacts and update privacy root lists**

Delete:

```text
.claude-plugin/plugin.json
.codex-plugin/plugin.json
.agents/plugins/marketplace.json
```

In `tests/packaging/test_distribution_privacy.py` and `tests/packaging/test_no_hook_privacy.py`, set package roots to:

```python
PACKAGE_ROOTS = (
    "openclaw-plugin",
    "hermes-profile",
    "skills",
)
```

In `tests/packaging/test_host_setup_profiles.py`, update `_scan_dirs()` extras to:

```python
    for extra in ("openclaw-plugin", "hermes-profile", "skills"):
        dirs.append(REPO_ROOT / extra)
```

Update `test_profile_contract_accepts_full_payload()` so the accepted Claude profile uses personal skills hub vocabulary:

```python
        package_model=SetupModel.DIRECTORY_COPY,
        package_files=["skills/"],
        install_flow=["tutor init --provider claude --yes"],
        launch_flow=["claude"],
        inspect_flow=["ls ~/.claude/skills/tutor-setup/SKILL.md"],
        update_or_reload_flow=["restart Claude Code"],
        verification_expectations=["tutor init --provider claude --yes --dry-run --json"],
```

If `SetupModel.DIRECTORY_COPY` does not exist, add this enum value in `src/language_tutor/schemas.py`:

```python
    DIRECTORY_COPY = "directory_copy"
```

- [ ] **Step 5: Run plugin-surface tests to verify they pass**

Run:

```bash
rtk uv run pytest tests/packaging/test_claude_plugin_package.py tests/packaging/test_codex_plugin_package.py tests/adapter_contract/test_claude_adapter.py tests/adapter_contract/test_codex_adapter.py tests/packaging/test_distribution_privacy.py tests/packaging/test_no_hook_privacy.py tests/packaging/test_host_setup_profiles.py -q
```

Expected: PASS.

- [ ] **Step 6: Commit plugin-surface removal**

```bash
rtk git add src/language_tutor/adapters/claude.py src/language_tutor/adapters/codex.py src/language_tutor/adapters/registry.py src/language_tutor/schemas.py tests/adapter_contract/test_claude_adapter.py tests/adapter_contract/test_codex_adapter.py tests/packaging/test_claude_plugin_package.py tests/packaging/test_codex_plugin_package.py tests/packaging/test_distribution_privacy.py tests/packaging/test_no_hook_privacy.py tests/packaging/test_host_setup_profiles.py
rtk git rm .claude-plugin/plugin.json .codex-plugin/plugin.json .agents/plugins/marketplace.json
rtk git commit -m "refactor: drop claude codex plugin surfaces"
```

### Task 7: Install Docs and User-Facing References

**Files:**
- Modify: `README.md`
- Modify: `docs/install/claude.md`
- Modify: `docs/install/codex.md`
- Modify: `docs/install/hermes.md`
- Modify: `docs/install/openclaw.md`
- Modify: `specs/005-text-modalities/skill-inventory.md`
- Modify: `tests/docs/test_install_docs.py`

- [ ] **Step 1: Update documentation assertions**

In `tests/docs/test_install_docs.py`, add assertions for current install docs:

```python
def test_claude_and_codex_docs_describe_personal_skill_hub() -> None:
    claude = (DOCS_DIR / "claude.md").read_text(encoding="utf-8")
    codex = (DOCS_DIR / "codex.md").read_text(encoding="utf-8")

    assert "~/.claude/skills" in claude
    assert "~/.codex/skills" in codex
    assert "marketplace" not in codex.lower()
    assert "plugin uninstall language-tutor" not in claude
    assert "plugin uninstall language-tutor" not in codex
```

- [ ] **Step 2: Run docs tests to verify they fail before docs edits**

Run:

```bash
rtk uv run pytest tests/docs/test_install_docs.py -q
```

Expected: FAIL while docs still describe Claude/Codex plugin installs.

- [ ] **Step 3: Update install docs**

In `docs/install/claude.md`, replace plugin-install language with:

```markdown
`tutor init --provider claude --yes` writes the shared tutor skills into the
personal Claude Code skills hub at `<CLAUDE_CONFIG_DIR|~/.claude>/skills`.
No Claude plugin manifest is installed. If the top-level `skills` directory is
created while Claude Code is already running, restart Claude Code before using
the tutor skills.
```

In `docs/install/codex.md`, replace marketplace language with:

```markdown
`tutor init --provider codex --yes` writes the shared tutor skills into the
personal Codex skills hub at `<CODEX_HOME|~/.codex>/skills`. No Codex plugin
manifest and no local marketplace entry are installed. Restart Codex after
initial install so the skills are loaded.
```

In `docs/install/hermes.md`, add:

```markdown
Hermes resolves its root from `HERMES_HOME` when set, otherwise `~/.hermes`.
`tutor init --provider hermes --yes` writes the existing lingo-loop profile
files under `<root>/profiles/lingo-loop/` and writes the shared flat tutor
skills under `<root>/skills/`.
```

In `docs/install/openclaw.md`, add:

```markdown
OpenClaw keeps the `openclaw-plugin/` registration files under
`~/.openclaw/plugins/lingo-loop/` and also receives the shared flat tutor skills
under `~/.openclaw/skills/`.
```

In `README.md`, update the host install summary to mention that all four providers get `skills/<skill-name>/SKILL.md`, while only Hermes/OpenClaw also get registration files.

In `specs/005-text-modalities/skill-inventory.md`, replace `bin/tutor` references with `tutor` and add one row for `skills/tutor-judge/SKILL.md` with the existing judge description.

- [ ] **Step 4: Run docs tests to verify they pass**

Run:

```bash
rtk uv run pytest tests/docs/test_install_docs.py tests/adapter_contract/test_plugin_surface.py -q
```

Expected: PASS.

- [ ] **Step 5: Commit docs updates**

```bash
rtk git add README.md docs/install/claude.md docs/install/codex.md docs/install/hermes.md docs/install/openclaw.md specs/005-text-modalities/skill-inventory.md tests/docs/test_install_docs.py
rtk git commit -m "docs: document personal skill hub installs"
```

### Task 8: Full Verification and Release Gate

**Files:**
- Verify: entire repository

- [ ] **Step 1: Search for stale plugin and source-bin references**

Run:

```bash
rtk rg -n "bin/tutor|agents/tutor-judge|\\.claude-plugin|\\.codex-plugin|marketplace plugin|local marketplace" src tests skills docs README.md pyproject.toml specs/005-text-modalities specs/006-agent-adapter-setup
```

Expected: no matches in active implementation/tests/docs, except archived spec/report text under `specs/006-agent-adapter-setup/subagent-reports/` if those historical reports are intentionally left unchanged. If historical reports match, do not edit them unless an active test scans them.

- [ ] **Step 2: Run targeted installer tests**

Run:

```bash
rtk uv run pytest tests/installer tests/unit/test_installer_service.py tests/integration/test_tutor_init_cli.py -q
```

Expected: PASS.

- [ ] **Step 3: Run packaging and health tests**

Run:

```bash
rtk uv run pytest tests/unit/test_package_assets.py tests/unit/test_health.py tests/packaging tests/release/test_wheel_contents.py -q
```

Expected: PASS.

- [ ] **Step 4: Run full test suite**

Run:

```bash
rtk uv run pytest
```

Expected: PASS with coverage at or above configured threshold.

- [ ] **Step 5: Run static checks**

Run:

```bash
rtk uv run pyright
```

Expected: PASS.

Run:

```bash
rtk uv run ruff check .
```

Expected: PASS.

- [ ] **Step 6: Build wheel**

Run:

```bash
rtk uv build --wheel
```

Expected: PASS and a `dist/lingo_loop-*.whl` file exists. The wheel must contain `language_tutor/_assets/skills/tutor-judge/SKILL.md` and must not contain `language_tutor/_assets/.claude-plugin/plugin.json`, `language_tutor/_assets/.codex-plugin/plugin.json`, `language_tutor/_assets/agents/tutor-judge.md`, or `language_tutor/_assets/bin/tutor`.

- [ ] **Step 7: Inspect wheel contents**

Run:

```bash
rtk python - <<'PY'
from pathlib import Path
import zipfile

wheel = sorted(Path("dist").glob("lingo_loop-*.whl"))[-1]
with zipfile.ZipFile(wheel) as zf:
    names = set(zf.namelist())

required = {
    "language_tutor/_assets/skills/tutor-setup/SKILL.md",
    "language_tutor/_assets/skills/tutor-vocab/SKILL.md",
    "language_tutor/_assets/skills/tutor-vocab/scripts/run.py",
    "language_tutor/_assets/skills/tutor-writing/SKILL.md",
    "language_tutor/_assets/skills/tutor-writing/scripts/run.py",
    "language_tutor/_assets/skills/tutor-reading/SKILL.md",
    "language_tutor/_assets/skills/tutor-lesson/SKILL.md",
    "language_tutor/_assets/skills/tutor-progress/SKILL.md",
    "language_tutor/_assets/skills/tutor-progress/scripts/run.py",
    "language_tutor/_assets/skills/tutor-judge/SKILL.md",
}
forbidden = {
    "language_tutor/_assets/.claude-plugin/plugin.json",
    "language_tutor/_assets/.codex-plugin/plugin.json",
    "language_tutor/_assets/agents/tutor-judge.md",
    "language_tutor/_assets/bin/tutor",
}
missing = sorted(required - names)
present_forbidden = sorted(forbidden & names)
print(f"wheel={wheel}")
print(f"missing={missing}")
print(f"present_forbidden={present_forbidden}")
raise SystemExit(1 if missing or present_forbidden else 0)
PY
```

Expected:

```text
missing=[]
present_forbidden=[]
```

- [ ] **Step 8: Commit final cleanup**

```bash
rtk git status --short
rtk git add .
rtk git commit -m "chore: verify skill hub install design"
```

## Self-Review Result

Spec coverage:
- Shared flat `skills/` tree: Tasks 1, 3, 4.
- Seven skills including `tutor-judge`: Tasks 1, 3, 4, 8.
- Multi-area base installer: Task 1.
- Hermes/OpenClaw registration plus skills: Tasks 1, 5.
- Claude/Codex personal hub only: Tasks 1, 5, 6, 7.
- Env root resolvers: Task 2.
- Drift repair, missing packaged asset, aggregate status: Tasks 1, 4, 5.
- No unrelated skill/state modification: Task 5.
- Wheel packaging and doctor checks: Tasks 4, 8.
- Docs and user-facing install references: Task 7.

Placeholder scan:
- No unfinished markers, deferred work markers, or unspecified validation steps remain in the plan.

Type consistency:
- `ManagedArea`, `ProviderProfile.areas`, `SKILL_FILES`, `SKILLS_AREA`, `skill_hub_components()`, and provider `config_root()` names are consistent across tasks.
