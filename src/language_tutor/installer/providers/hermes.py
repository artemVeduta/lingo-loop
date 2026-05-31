from __future__ import annotations

import os
from pathlib import Path

from language_tutor.installer.providers.base import (
    SKILLS_AREA,
    BaseProviderInstaller,
    ManagedArea,
    ProviderProfile,
)
from language_tutor.schemas import HostId

HERMES_PROFILE_AREA = ManagedArea(
    bundled_assets_root_rel="hermes-profile",
    managed_dir_rel="profiles/lingo-loop",
    files=("distribution.yaml", "config.yaml", "SOUL.md"),
)


class HermesInstaller(BaseProviderInstaller):
    profile = ProviderProfile(
        host=HostId.HERMES,
        cli_name="hermes",
        config_root_rel=".hermes",
        areas=(HERMES_PROFILE_AREA, SKILLS_AREA),
        next_command="Restart Hermes or run `hermes skills list` to confirm the tutor skills.",
    )

    def config_root(self) -> Path:
        configured = os.environ.get("HERMES_HOME")
        if configured:
            return Path(configured).expanduser()
        return super().config_root()
