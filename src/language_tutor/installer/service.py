"""Orchestrator: detect → plan → apply → verify across selected providers."""

from __future__ import annotations

from datetime import UTC, datetime

from language_tutor.installer.protocol import InstallerContext, ProviderInstaller
from language_tutor.installer.registry import (
    SUPPORTED_PROVIDER_IDS,
    build_installer,
)
from language_tutor.schemas import (
    HostId,
    InitPlan,
    InitRequest,
    InitResult,
    ProviderActionStage,
    ProviderPlan,
    ProviderResult,
    ProviderState,
)


def _now() -> datetime:
    return datetime.now(UTC).replace(microsecond=0)


def _select(hosts: list[HostId] | None) -> list[HostId]:
    if hosts:
        return list(hosts)
    return list(SUPPORTED_PROVIDER_IDS)


def build_plan(ctx: InstallerContext, request: InitRequest) -> InitPlan:
    hosts = _select(request.providers)
    plans: list[ProviderPlan] = []
    for host in hosts:
        installer: ProviderInstaller = build_installer(host, ctx)
        plans.append(installer.plan(request))
    return InitPlan(generated_at=_now(), plans=plans)


def run_init(ctx: InstallerContext, request: InitRequest) -> InitResult:
    plan = build_plan(ctx, request)
    results: list[ProviderResult] = []
    for provider_plan in plan.plans:
        installer = build_installer(provider_plan.host, ctx)
        actions = installer.apply(provider_plan, dry_run=request.dry_run)
        verified = False
        verify_hint: str | None = None
        if not request.dry_run and any(
            a.stage == ProviderActionStage.APPLIED for a in actions
        ) or provider_plan.status.state == ProviderState.INSTALLED:
            verified, verify_hint = installer.verify()
        repair_hint = provider_plan.status.repair_hint or verify_hint
        results.append(
            ProviderResult(
                host=provider_plan.host,
                status=provider_plan.status,
                actions=actions,
                verified=verified,
                next_command=provider_plan.next_command,
                repair_hint=repair_hint,
            )
        )
    return InitResult(
        completed_at=_now(),
        dry_run=request.dry_run,
        results=results,
    )
