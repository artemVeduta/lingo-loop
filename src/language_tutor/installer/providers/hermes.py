from __future__ import annotations

from language_tutor.installer.providers.base import (
    BaseProviderInstaller,
    ProviderProfile,
)
from language_tutor.schemas import HostId


class HermesInstaller(BaseProviderInstaller):
    profile = ProviderProfile(
        host=HostId.HERMES,
        cli_name="hermes",
        config_root_rel=".hermes",
        bundled_assets_root_rel="hermes-profile",
        managed_dir_rel="profiles/lingo-loop",
        files=("distribution.yaml", "config.yaml", "SOUL.md"),
        next_command="Run `hermes profile update` to refresh the lingo-loop profile.",
    )
