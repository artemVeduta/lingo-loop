"""ProviderInstaller Protocol + InstallerContext.

Each per-host module implements ProviderInstaller. The context bundles fakeable
filesystem and command-runner seams plus the bundled-asset root so providers
can be exercised hermetically in tests.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from language_tutor.installer.seams import (
    CommandRunnerSeam,
    FilesystemSeam,
    RealCommandRunner,
    RealFilesystem,
)
from language_tutor.schemas import (
    HostId,
    InitRequest,
    ProviderInstallAction,
    ProviderPlan,
    ProviderStatus,
)


@dataclass(frozen=True)
class InstallerContext:
    fs: FilesystemSeam
    runner: CommandRunnerSeam
    bundled_assets_root: Path

    @classmethod
    def real(cls, bundled_assets_root: Path) -> InstallerContext:
        return cls(
            fs=RealFilesystem(),
            runner=RealCommandRunner(),
            bundled_assets_root=bundled_assets_root,
        )


class ProviderInstaller(Protocol):
    id: HostId
    display_name: str
    docs_url: str

    def detect(self) -> ProviderStatus: ...
    def plan(self, request: InitRequest) -> ProviderPlan: ...
    def apply(self, plan: ProviderPlan, dry_run: bool) -> list[ProviderInstallAction]: ...
    def verify(self) -> tuple[bool, str | None]: ...
