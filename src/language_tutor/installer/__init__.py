"""Interactive provider installer (`tutor init`).

Distribution glue only: detects supported AI hosts, writes managed plugin/
profile registration files for the user-selected providers, and verifies the
result. Never touches learner profile YAML, SQLite history, sessions,
checkpoints, memories, logs, or host secrets.
"""

from language_tutor.installer.protocol import InstallerContext, ProviderInstaller
from language_tutor.installer.registry import (
    SUPPORTED_PROVIDER_IDS,
    build_installer,
    build_installers,
)
from language_tutor.installer.seams import (
    CommandRunnerSeam,
    FilesystemSeam,
    RealCommandRunner,
    RealFilesystem,
)
from language_tutor.installer.service import build_plan, run_init

__all__ = [
    "CommandRunnerSeam",
    "FilesystemSeam",
    "InstallerContext",
    "ProviderInstaller",
    "RealCommandRunner",
    "RealFilesystem",
    "SUPPORTED_PROVIDER_IDS",
    "build_installer",
    "build_installers",
    "build_plan",
    "run_init",
]
