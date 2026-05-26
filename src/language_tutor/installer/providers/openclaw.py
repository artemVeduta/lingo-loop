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
        bundled_assets_root_rel="openclaw-plugin",
        managed_dir_rel="plugins/lingo-loop",
        files=(
            "package.json",
            "openclaw.plugin.json",
            "tsconfig.json",
            "src/index.ts",
        ),
        next_command="Run `openclaw plugins install lingo-loop` to register the plugin with OpenClaw.",
    )
