"""Provider installer registry.

Single source of truth for which providers ``tutor init`` can install. Derived
from ``language_tutor.adapters.base.supported_host_targets()`` so the four
approved hosts (Claude, Codex, Hermes, OpenClaw) flow through; antigravity
remains rejected.
"""

from __future__ import annotations

from collections.abc import Callable

from language_tutor.adapters.base import supported_host_targets
from language_tutor.installer.protocol import InstallerContext, ProviderInstaller
from language_tutor.installer.providers.claude import ClaudeInstaller
from language_tutor.installer.providers.codex import CodexInstaller
from language_tutor.installer.providers.hermes import HermesInstaller
from language_tutor.installer.providers.openclaw import OpenClawInstaller
from language_tutor.schemas import HostId

_BUILDERS: dict[HostId, Callable[[InstallerContext], ProviderInstaller]] = {
    HostId.CLAUDE: ClaudeInstaller,
    HostId.CODEX: CodexInstaller,
    HostId.HERMES: HermesInstaller,
    HostId.OPENCLAW: OpenClawInstaller,
}

SUPPORTED_PROVIDER_IDS: tuple[HostId, ...] = tuple(supported_host_targets().keys())


def build_installer(host: HostId, ctx: InstallerContext) -> ProviderInstaller:
    if host not in _BUILDERS:
        raise KeyError(f"no installer for host {host}")
    return _BUILDERS[host](ctx)


def build_installers(
    ctx: InstallerContext, hosts: list[HostId] | None = None
) -> list[ProviderInstaller]:
    selected = hosts if hosts is not None else list(SUPPORTED_PROVIDER_IDS)
    return [build_installer(h, ctx) for h in selected]
