from __future__ import annotations

from language_tutor.installer.providers.base import (
    BaseProviderInstaller,
    ProviderProfile,
)
from language_tutor.schemas import HostId


class CodexInstaller(BaseProviderInstaller):
    profile = ProviderProfile(
        host=HostId.CODEX,
        cli_name="codex",
        config_root_rel=".codex",
        bundled_asset_rel=".codex-plugin/plugin.json",
        managed_path_rel="plugins/lingo-loop/plugin.json",
        next_command="Restart Codex so the local marketplace plugin is discovered.",
    )
