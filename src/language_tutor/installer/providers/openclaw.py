from __future__ import annotations

from language_tutor.installer.providers.base import (
    BaseProviderInstaller,
    ProviderProfile,
)
from language_tutor.schemas import HostId


class OpenClawInstaller(BaseProviderInstaller):
    profile = ProviderProfile(
        host=HostId.OPENCLAW,
        cli_name="openclaw",
        config_root_rel=".openclaw",
        bundled_asset_rel="openclaw-plugin/package.json",
        managed_path_rel="plugins/lingo-loop/package.json",
        next_command="Run `openclaw plugins install lingo-loop` to register the plugin with OpenClaw.",
    )
