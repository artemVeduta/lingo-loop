"""Shared provider installer machinery.

Concrete per-host installers (claude.py, codex.py, hermes.py, openclaw.py)
subclass ``BaseProviderInstaller`` and override only the small surface that
differs between hosts: CLI name, conventional config-root, bundled-asset
relative path, managed-file destination relative path, and post-install
"next command" hint.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from language_tutor.adapters.base import supported_host_targets
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
    bundled_asset_rel: str
    managed_path_rel: str
    next_command: str


class BaseProviderInstaller:
    profile: ProviderProfile

    def __init__(self, ctx: InstallerContext) -> None:
        self.ctx = ctx
        self.id: HostId = self.profile.host
        target = supported_host_targets()[self.profile.host]
        self.display_name: str = target.display_name
        self.docs_url: str = f"{DOCS_BASE_URL}/{self.profile.host.value}.md"

    def config_root(self) -> Path:
        return self.ctx.fs.home() / self.profile.config_root_rel

    def managed_path(self) -> Path:
        return self.config_root() / self.profile.managed_path_rel

    def bundled_path(self) -> Path:
        return self.ctx.bundled_assets_root / self.profile.bundled_asset_rel

    def bundled_content(self) -> str:
        path = self.bundled_path()
        if not path.exists():
            raise FileNotFoundError(
                f"bundled asset missing for {self.profile.host.value}: {path}"
            )
        return path.read_text(encoding="utf-8")

    def detect(self) -> ProviderStatus:
        cli_path = self.ctx.runner.which(self.profile.cli_name)
        detected_cli = cli_path is not None
        if not detected_cli:
            return ProviderStatus(
                host=self.profile.host,
                display_name=self.display_name,
                state=ProviderState.BLOCKED,
                detected_cli=False,
                cli_path=None,
                config_root=str(self.config_root()),
                managed_files=[str(self.managed_path())],
                repair_hint=(
                    f"Install {self.display_name} first (CLI '{self.profile.cli_name}' "
                    f"not on PATH); see {self.docs_url}"
                ),
                docs_url=self.docs_url,
            )

        managed = self.managed_path()
        managed_present = self.ctx.fs.is_file(managed)
        if managed_present:
            current = self.ctx.fs.read_text(managed)
            expected = self.bundled_content()
            if current == expected:
                state = ProviderState.INSTALLED
                hint: str | None = None
            else:
                state = ProviderState.NEEDS_REPAIR
                hint = "Managed file drifted from bundled content; rerun to repair."
        else:
            state = ProviderState.AVAILABLE
            hint = None

        return ProviderStatus(
            host=self.profile.host,
            display_name=self.display_name,
            state=state,
            detected_cli=True,
            cli_path=cli_path,
            config_root=str(self.config_root()),
            managed_files=[str(managed)],
            repair_hint=hint,
            docs_url=self.docs_url,
        )

    def plan(self, request: InitRequest) -> ProviderPlan:
        del request
        status = self.detect()
        actions: list[ProviderInstallAction] = []
        if status.state == ProviderState.BLOCKED:
            actions.append(
                ProviderInstallAction(
                    kind=ProviderActionKind.BLOCK,
                    target_path=str(self.managed_path()),
                    description=status.repair_hint or "Host prerequisite missing.",
                    stage=ProviderActionStage.BLOCKED,
                )
            )
        elif status.state == ProviderState.INSTALLED:
            actions.append(
                ProviderInstallAction(
                    kind=ProviderActionKind.SKIP,
                    target_path=str(self.managed_path()),
                    description="Already installed; nothing to do.",
                    stage=ProviderActionStage.SKIPPED,
                )
            )
        else:
            actions.append(
                ProviderInstallAction(
                    kind=ProviderActionKind.WRITE_FILE,
                    target_path=str(self.managed_path()),
                    description=(
                        f"Write managed {self.display_name} registration file from "
                        f"bundled {self.profile.bundled_asset_rel}."
                    ),
                )
            )
        return ProviderPlan(
            host=self.profile.host,
            status=status,
            actions=actions,
            next_command=self.profile.next_command,
        )

    def apply(self, plan: ProviderPlan, dry_run: bool) -> list[ProviderInstallAction]:
        applied: list[ProviderInstallAction] = []
        for action in plan.actions:
            if action.kind == ProviderActionKind.WRITE_FILE and not dry_run:
                try:
                    content = self.bundled_content()
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
        managed = self.managed_path()
        if not self.ctx.fs.is_file(managed):
            return False, f"managed file missing: {managed}"
        try:
            current = self.ctx.fs.read_text(managed)
            expected = self.bundled_content()
        except FileNotFoundError as exc:
            return False, str(exc)
        if current != expected:
            return False, "managed file content differs from bundled asset"
        return True, None
