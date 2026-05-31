from __future__ import annotations

from language_tutor.installer.providers.base import (
    SKILLS_AREA,
    BaseProviderInstaller,
    ManagedArea,
    ProviderProfile,
)
from language_tutor.schemas import HostId

OPENCLAW_PLUGIN_AREA = ManagedArea(
    bundled_assets_root_rel="openclaw-plugin",
    managed_dir_rel="plugins/lingo-loop",
    files=(
        "package.json",
        "openclaw.plugin.json",
        "tsconfig.json",
        "src/index.ts",
        "src/node-shims.d.ts",
        "dist/index.js",
        "dist/index.d.ts",
    ),
)


class OpenClawInstaller(BaseProviderInstaller):
    profile = ProviderProfile(
        host=HostId.OPENCLAW,
        cli_name="openclaw",
        config_root_rel=".openclaw",
        areas=(OPENCLAW_PLUGIN_AREA, SKILLS_AREA),
        next_command="Run `openclaw plugins install lingo-loop` to register the plugin with OpenClaw.",
    )
