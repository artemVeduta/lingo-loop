from __future__ import annotations

import os
from pathlib import Path

from language_tutor.installer.providers.base import (
    SKILLS_AREA,
    BaseProviderInstaller,
    ProviderProfile,
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

    def config_root(self) -> Path:
        configured = os.environ.get("CLAUDE_CONFIG_DIR")
        if configured:
            return Path(configured).expanduser()
        return super().config_root()
