"""Shared provider installer machinery.

Concrete per-host installers (claude.py, codex.py, hermes.py, openclaw.py)
subclass ``BaseProviderInstaller`` and override only the small surface that
differs between hosts: CLI name, conventional config-root, the bundled-asset
host-package directory, the managed destination directory, the explicit file
list, and post-install "next command" hint.

Each provider is a *bundled directory tree*: the profile declares one or more
files under ``files``; every file is materialised, verified, and drift-detected
independently. A missing or content-divergent sibling marks the host
``NEEDS_REPAIR`` and the repair plan schedules one ``WRITE_FILE`` action per
divergent file.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from language_tutor.adapters.base import supported_host_targets
from language_tutor.installer.assets import bundled_assets_root_for
from language_tutor.installer.protocol import InstallerContext
from language_tutor.schemas import (
    HostId,
    InitRequest,
    ProviderActionKind,
    ProviderActionStage,
    ProviderInstallAction,
    ProviderPlan,
    ProviderState,
    ProviderStatus,
)

DOCS_BASE_URL = "https://github.com/artemVeduta/lingo-loop/blob/main/docs/install"


@dataclass(frozen=True)
class ProviderProfile:
    host: HostId
    cli_name: str
    config_root_rel: str
    # Directory name of the bundled host-package (e.g. ``openclaw-plugin``).
    # Resolved against the wheel ``_assets`` dir or the editable repo root.
    bundled_assets_root_rel: str
    # Directory relative to ``config_root`` where managed files are written.
    managed_dir_rel: str
    # Explicit list of relative paths under both the bundled-tree root and the
    # managed-dir root. Every file is copied and verified one-for-one.
    files: tuple[str, ...]
    next_command: str


class BaseProviderInstaller:
    profile: ProviderProfile

    def __init__(self, ctx: InstallerContext) -> None:
        self.ctx = ctx
        self.id: HostId = self.profile.host
        target = supported_host_targets()[self.profile.host]
        self.display_name: str = target.display_name
        self.docs_url: str = f"{DOCS_BASE_URL}/{self.profile.host.value}.md"

    # -- path helpers -------------------------------------------------------

    def config_root(self) -> Path:
        return self.ctx.fs.home() / self.profile.config_root_rel

    def managed_dir(self) -> Path:
        return self.config_root() / self.profile.managed_dir_rel

    def bundled_root(self) -> Path:
        return bundled_assets_root_for(self.profile.bundled_assets_root_rel)

    def managed_files(self) -> list[Path]:
        root = self.managed_dir()
        return [root / rel for rel in self.profile.files]

    def bundled_files(self) -> list[Path]:
        root = self.bundled_root()
        return [root / rel for rel in self.profile.files]

    def _bundled_content(self, rel: str) -> str:
        path = self.bundled_root() / rel
        if not path.exists():
            raise FileNotFoundError(
                f"bundled asset missing for {self.profile.host.value}: {path}"
            )
        return path.read_text(encoding="utf-8")

    # -- BLOCKED status helper ----------------------------------------------

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

    # -- detect/plan/apply/verify ------------------------------------------

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
                f"before installing the plugin; see {self.docs_url}"
            )
            return self._blocked_status(hint, detected_cli=True, cli_path=cli_path)

        # Check bundled assets are actually present in the distribution.
        missing_bundled: list[str] = []
        for rel in self.profile.files:
            if not (self.bundled_root() / rel).exists():
                missing_bundled.append(rel)
        if missing_bundled:
            joined = ", ".join(missing_bundled)
            hint = (
                f"Bundled asset(s) missing from the lingo-loop wheel for "
                f"{self.display_name} (packaging defect): {joined}; see {self.docs_url}"
            )
            return self._blocked_status(hint, detected_cli=True, cli_path=cli_path)

        # Per-file presence + content comparison.
        any_missing = False
        any_drift = False
        for rel in self.profile.files:
            managed_path = self.managed_dir() / rel
            if not self.ctx.fs.is_file(managed_path):
                any_missing = True
                continue
            try:
                expected = self._bundled_content(rel)
            except FileNotFoundError:
                # Already covered by missing_bundled above, but be defensive.
                any_drift = True
                continue
            current = self.ctx.fs.read_text(managed_path)
            if current != expected:
                any_drift = True

        if not any_missing and not any_drift:
            state = ProviderState.INSTALLED
            hint = None
        else:
            # Distinguish between a brand-new install (every file missing) and
            # a partial / drifted state.
            all_missing = all(
                not self.ctx.fs.is_file(self.managed_dir() / rel)
                for rel in self.profile.files
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

    def _divergent_files(self) -> list[str]:
        """Return relative file paths that are missing or content-mismatched."""

        divergent: list[str] = []
        for rel in self.profile.files:
            managed_path = self.managed_dir() / rel
            if not self.ctx.fs.is_file(managed_path):
                divergent.append(rel)
                continue
            try:
                expected = self._bundled_content(rel)
            except FileNotFoundError:
                continue
            if self.ctx.fs.read_text(managed_path) != expected:
                divergent.append(rel)
        return divergent

    def plan(self, request: InitRequest) -> ProviderPlan:
        del request
        status = self.detect()
        actions: list[ProviderInstallAction] = []
        if status.state == ProviderState.BLOCKED:
            actions.append(
                ProviderInstallAction(
                    kind=ProviderActionKind.BLOCK,
                    target_path=str(self.managed_dir()),
                    description=status.repair_hint or "Host prerequisite missing.",
                    stage=ProviderActionStage.BLOCKED,
                )
            )
        elif status.state == ProviderState.INSTALLED:
            actions.append(
                ProviderInstallAction(
                    kind=ProviderActionKind.SKIP,
                    target_path=str(self.managed_dir()),
                    description="Already installed; nothing to do.",
                    stage=ProviderActionStage.SKIPPED,
                )
            )
        else:
            divergent = self._divergent_files()
            if not divergent:
                # Defensive: fall back to skip when the status is not BLOCKED /
                # INSTALLED but nothing is divergent (should not happen).
                actions.append(
                    ProviderInstallAction(
                        kind=ProviderActionKind.SKIP,
                        target_path=str(self.managed_dir()),
                        description="Already installed; nothing to do.",
                        stage=ProviderActionStage.SKIPPED,
                    )
                )
            else:
                for rel in divergent:
                    target = self.managed_dir() / rel
                    actions.append(
                        ProviderInstallAction(
                            kind=ProviderActionKind.WRITE_FILE,
                            target_path=str(target),
                            description=(
                                f"Write managed {self.display_name} file "
                                f"{rel} from bundled "
                                f"{self.profile.bundled_assets_root_rel}/{rel}."
                            ),
                        )
                    )
        return ProviderPlan(
            host=self.profile.host,
            status=status,
            actions=actions,
            next_command=self.profile.next_command,
        )

    def _bundled_rel_for_target(self, target_path: str) -> str | None:
        managed_dir = self.managed_dir()
        try:
            rel = Path(target_path).relative_to(managed_dir)
        except ValueError:
            return None
        rel_str = str(rel)
        return rel_str if rel_str in self.profile.files else None

    def apply(self, plan: ProviderPlan, dry_run: bool) -> list[ProviderInstallAction]:
        applied: list[ProviderInstallAction] = []
        for action in plan.actions:
            if action.kind == ProviderActionKind.WRITE_FILE and not dry_run:
                rel = self._bundled_rel_for_target(action.target_path)
                if rel is None:
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
                    content = self._bundled_content(rel)
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
        for rel in self.profile.files:
            managed_path = self.managed_dir() / rel
            if not self.ctx.fs.is_file(managed_path):
                return False, f"managed file missing: {managed_path}"
            try:
                expected = self._bundled_content(rel)
            except FileNotFoundError as exc:
                return False, str(exc)
            current = self.ctx.fs.read_text(managed_path)
            if current != expected:
                return False, f"managed file content differs from bundled asset: {managed_path}"
        return True, None
