from __future__ import annotations

from language_tutor.installer.providers.base import (
    BaseProviderInstaller,
    ProviderProfile,
)
from language_tutor.schemas import HostId


class ClaudeInstaller(BaseProviderInstaller):
    profile = ProviderProfile(
        host=HostId.CLAUDE,
        cli_name="claude",
        config_root_rel=".claude",
        bundled_assets_root_rel=".claude-plugin",
        managed_dir_rel="plugins/lingo-loop",
        files=("plugin.json",),
        next_command="In an open Claude Code session, run `/reload-plugins`.",
    )
