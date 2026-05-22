# Handoff: Codex Hook / Session-Lifecycle Decision

**Status:** OPEN — needs a maintainer decision before Codex readiness.
**Date raised:** 2026-05-22
**Scope:** spec 006 (Agent Adapter Setup), Codex host only.

## Background: what must be the same vs what differs

Spec 006 requires every supported host (Hermes, OpenClaw, Claude, Codex) to
deliver the **same learner-visible session behavior**:

- Same boot context at session start (profile, due reviews, weak patterns, recap).
- Same six representative text flows (reading, lesson, transcript, vocab, writing, progress).

It does **not** require the same *mechanism* for triggering session start. That is
host-specific and modeled by `AdapterCapabilityProfile.boot_context_trigger` plus
the deterministic fallback chain in `boot_context.select_boot_trigger`
(hook → explicit_command → first_message → manual).

Hooks are therefore an **automatic-trigger convenience**, not a functional
requirement. Hosts without hooks still reach parity:

| Host | boot trigger | mechanism |
|------|--------------|-----------|
| Claude | `session_start_hook` | SessionStart hook (auto) |
| Codex | `codex_plugin_hook` | plugin hook — only if enabled (see below) |
| Hermes | `explicit_tutor_command` | no hooks → `tutor boot --json` |
| OpenClaw | `first_tutor_message` | no hooks → build on first message |

## The inconsistency

- `src/language_tutor/adapters/registry.py` declares Codex
  `lifecycle_start=hook`, `boot_context_trigger=codex_plugin_hook`.
- `.codex-plugin/plugin.json` ships `"features": {"plugin_hooks": false}`.
- Codex hook enablement is actually host-side, via `[features].plugin_hooks = true`
  in the user's `config.toml` (per research.md) — a plugin manifest cannot enable
  a host feature.

So **out-of-box, Codex's declared hook trigger cannot fire**. Without the user
opting in host-side, automatic session-start parity depends on the fallback
trigger, not the declared `codex_plugin_hook`. The profile currently assumes the
optimistic "hook enabled" case while the package ships hooks disabled and opt-in.

This is consistent with the constitution's opt-in / least-privilege rule for
side-effectful host features — but it makes the *declared default trigger* wrong
for the *shipped default state*.

## Decision needed

Pick one. Both keep the privacy/opt-in rule intact.

### Option A (recommended) — hook is an opt-in upgrade

- Codex default `lifecycle_start=first_message`, `boot_context_trigger=first_tutor_message`
  (same model as OpenClaw).
- Session-start parity works **out-of-box**, no host config change required.
- `codex_plugin_hook` documented as an optional upgrade for users who set
  `[features].plugin_hooks = true`; listed under `side_effectful_capabilities`.
- Keeps `"plugin_hooks": false` (or removes the `features` block; see manifest note).

Changes if chosen:
- `registry.py` Codex profile → `first_message` / `first_tutor_message`.
- `tests/adapter_contract/test_codex_adapter.py::test_codex_lifecycle_is_plugin_hook`
  → rename/adjust to assert first_message default + hook as opt-in.
- `contracts/host-setup-profiles/codex.md` capability prose + json block.
- `manual-install-reports/codex.md` boot-trigger line.

### Option B — hook required for parity

- Keep `codex_plugin_hook` as the declared trigger.
- Codex setup **must** instruct the user to enable `[features].plugin_hooks = true`
  in `config.toml` as a prerequisite, or session-start parity does not work.
- Document the enable step as a required install action (not optional) in
  `codex.md` and `manual-install-reports/codex.md`, and gate readiness on it.

## Manifest note (independent of A/B)

`"features": {"plugin_hooks": false}` in `.codex-plugin/plugin.json` is a
**declared-default marker**, not an enforced switch — Codex reads the real flag
from `config.toml`, and the plugin ships no `hooks/` dir anyway. If matching the
real Codex manifest schema strictly, this field may not belong in `plugin.json`;
consider moving the gating note to `codex.md` and keeping the manifest minimal.
Verify against the actual Codex plugin manifest schema before finalizing.

## Recommendation

Option A. It satisfies "same session functionality by default" without forcing a
host-side config change, matches OpenClaw's non-hook model, and treats the hook
as the privileged opt-in it actually is. Hook stays available for users who want
the automatic SessionStart-style trigger.
