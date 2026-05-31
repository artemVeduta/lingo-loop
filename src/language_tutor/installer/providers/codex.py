from __future__ import annotations

import os
from pathlib import Path

from language_tutor.installer.providers.base import (
    SKILLS_AREA,
    BaseProviderInstaller,
    ProviderProfile,
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

    def config_root(self) -> Path:
        configured = os.environ.get("CODEX_HOME")
        if configured:
            return Path(configured).expanduser()
        return super().config_root()
