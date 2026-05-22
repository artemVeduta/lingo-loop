# Hook Lifecycle Research: OpenClaw, Hermes, Codex

**Date**: 2026-05-22
**Status**: Research note; implementation not applied
**Scope**: Feasibility of adding Claude-like lifecycle hooks to OpenClaw, Hermes, and Codex.

## Summary

Claude already has thin `SessionStart` / `SessionEnd` shell wrappers that delegate to
`bin/tutor`. Current upstream docs show similar lifecycle surfaces now exist for
OpenClaw, Hermes, and Codex, but their semantics are not identical.

| Host | Boot hook feasible | End hook feasible | Best fit | Notes |
| --- | --- | --- | --- | --- |
| Codex | Yes | Partial | `SessionStart` for boot; `Stop` for turn-end persistence | No documented true `SessionEnd`; plugin-bundled hooks remain opt-in. |
| OpenClaw | Yes | Yes | Plugin hook prompt injection plus `session_end` lifecycle hook | Existing spec 006 OpenClaw profile is stale. |
| Hermes | Yes | Yes | Plugin hook or shell hook with `pre_llm_call`, `on_session_end`, `on_session_finalize` | Existing spec 006 Hermes profile is stale. |

## Existing Tutor Hook Contract

Current Claude hook model:

- `hooks/session-start.sh` runs `bin/tutor boot-context --json`, then renders it with
  `bin/tutor render boot-context --json`.
- `hooks/session-end.sh` runs `bin/tutor session-end --json "$PAYLOAD" || true`.
- Shell wrappers stay thin; the Python CLI owns validation, rendering, persistence,
  and error JSON.

The same design should be preserved for other hosts:

- Host hook translates host payload into tutor CLI input.
- `bin/tutor` remains the only owner of tutor state and pedagogy.
- Hook failures must not block shutdown or crash host sessions.

## Codex

### Sources

- Official docs: <https://developers.openai.com/codex/hooks>
- Checked: 2026-05-22

### Findings

Codex now documents first-class hooks. Hooks are enabled by default through the
canonical `[features].hooks` key. To disable:

```toml
[features]
hooks = false
```

Codex discovers hooks from active config layers:

- `~/.codex/hooks.json`
- `~/.codex/config.toml`
- `<repo>/.codex/hooks.json`
- `<repo>/.codex/config.toml`

Installed plugins can also bundle hooks, but plugin hooks are off by default and
require:

```toml
[features]
plugin_hooks = true
```

Important current events:

- `SessionStart`
- `PreToolUse`
- `PermissionRequest`
- `PostToolUse`
- `UserPromptSubmit`
- `Stop`

`SessionStart` can add model-visible context. Plain text on stdout is added as
developer context. JSON can return:

```json
{
  "hookSpecificOutput": {
    "hookEventName": "SessionStart",
    "additionalContext": "..."
  }
}
```

`Stop` runs at turn scope and can continue/stop processing, but it is not a true
process/session-finalization hook.

### Tutor Mapping

Recommended boot path:

- Add repo-local `.codex/hooks.json`.
- Register `SessionStart` with matcher `startup|resume|clear`.
- Command calls a thin wrapper that renders tutor boot context.
- Wrapper emits plain text or `additionalContext`.

Recommended end path:

- Treat `Stop` as turn-end persistence only.
- Do not claim Codex has a real `SessionEnd`.
- If used, call `bin/tutor session-end --json` with minimal payload and never rely
  on it for guaranteed final shutdown persistence.

### Recommended Package Shape

Prefer project-local hooks for the current repo:

```text
.codex/
  hooks.json
  hooks/
    session-start.sh
    stop.sh
```

Reason: repo-local hooks use normal Codex hook loading and do not require
`[features].plugin_hooks = true`. Plugin-bundled hooks remain possible later, but
they add an extra opt-in gate.

### Contract Impact

Current `.codex-plugin/plugin.json` has:

```json
"features": {
  "plugin_hooks": false
}
```

That remains a conservative default. If using repo-local `.codex/hooks.json`,
plugin hooks can stay disabled.

Capability model should distinguish:

- `lifecycle_start = hook`
- `boot_context_trigger = codex_session_start_hook`
- `lifecycle_end = turn_stop` or `not_available`, not true `hook`

## OpenClaw

### Sources

- Official hooks docs: <https://docs.openclaw.ai/automation/hooks>
- Official plugin internals docs: <https://docs.openclaw.ai/plugins/architecture>
- OpenClaw hooks reference discovered via search: <https://docs.openclaw.ai/plugins/hooks>
- Checked: 2026-05-22

### Findings

OpenClaw has two relevant hook systems:

- Internal hooks: Gateway scripts for events such as `/new`, `/reset`, `/stop`,
  `agent:bootstrap`, `gateway:startup`, compaction, and session patches.
- Plugin hooks: in-process plugin extension points for agent runs, tool calls,
  message flow, session lifecycle, subagent routing, installs, and Gateway
  startup.

Internal hook docs list lifecycle-related events:

- `command:new`
- `command:reset`
- `command:stop`
- `session:compact:before`
- `session:compact:after`
- `session:patch`
- `agent:bootstrap`
- `gateway:startup`

Plugin hook docs and release notes indicate richer lifecycle coverage, including:

- `before_model_resolve`
- `agent_turn_prepare`
- `before_prompt_build`
- `before_agent_run`
- `agent_end`
- `session_start`
- `session_end`

OpenClaw release notes also mention typed `session_end` plugin hooks firing during
shutdown/restart for active sessions, with bounded drain behavior.

### Tutor Mapping

Recommended boot path:

- Use plugin prompt/context injection, not only lifecycle observation.
- Best candidates: `agent_turn_prepare` or `before_prompt_build`.
- Inject rendered `bin/tutor boot-context --json` output only once per session.
- Use OpenClaw session extension / plugin state if available to avoid repeated
  boot injection.

Recommended end path:

- Use typed plugin `session_end` when available.
- Call `bin/tutor session-end --json` from the plugin hook.
- Keep payload small: host `session_id`, completion/reason metadata, optional
  analysis only if a trusted analyzer produced it.
- Hook must be fire-and-forget or bounded; do not block Gateway shutdown.

### Recommended Package Shape

Extend current `openclaw-plugin/src/index.ts`:

- Keep existing tools.
- Register lifecycle/prompt hooks through the OpenClaw plugin API.
- Keep shelling out to `bin/tutor` behind explicit operator trust/allowlist if the
  host treats local binary execution as side-effectful.

### Contract Impact

Current OpenClaw artifacts say:

- lifecycle start: `first_message`
- lifecycle end: `not_available`
- boot trigger: `first_tutor_message`

Those are stale relative to current upstream hook docs. Update targets should be:

- lifecycle start: `hook`
- lifecycle end: `hook`
- boot trigger: OpenClaw prompt/session hook

## Hermes

### Sources

- Official hooks docs: <https://hermes-agent.nousresearch.com/docs/user-guide/features/hooks/>
- Checked: 2026-05-22

### Findings

Hermes documents three hook systems:

- Gateway hooks: `HOOK.yaml` + `handler.py` under `~/.hermes/hooks/`; Gateway only.
- Plugin hooks: `ctx.register_hook()` in a plugin; CLI + Gateway.
- Shell hooks: `hooks:` block in `~/.hermes/config.yaml`; CLI + Gateway.

Relevant Gateway events:

- `gateway:startup`
- `session:start`
- `session:end`
- `session:reset`
- `agent:start`
- `agent:step`
- `agent:end`
- `command:*`

Relevant plugin hooks:

- `pre_tool_call`
- `post_tool_call`
- `pre_llm_call`
- `post_llm_call`
- `on_session_start`
- `on_session_end`
- `on_session_finalize`
- `on_session_reset`
- `subagent_stop`
- `pre_gateway_dispatch`

`pre_llm_call` can inject context into the LLM turn by returning a dict with a
`context` field. `on_session_end` fires at the end of every `run_conversation()`
call and from the CLI exit handler if the agent was mid-turn. `on_session_finalize`
fires when CLI or Gateway tears down an active session.

### Tutor Mapping

Recommended boot path:

- Use `pre_llm_call` to inject rendered boot context.
- Guard injection so it runs only once per session.
- `on_session_start` is useful for bookkeeping, but return value is ignored, so it
  should not be the only boot-context mechanism.

Recommended end path:

- Use `on_session_end` for normal turn/session completion.
- Use `on_session_finalize` as final flush before session identity is discarded.
- Both should call `bin/tutor session-end --json` through a thin wrapper and must
  swallow failures.

### Recommended Package Shape

Two viable options:

1. Hermes plugin:
   - Register `pre_llm_call`, `on_session_end`, and `on_session_finalize`.
   - Best fit for CLI + Gateway support.

2. Hermes shell hooks:
   - Configure shell scripts in `config.yaml`.
   - Lower implementation effort.
   - Requires allowlist/trust review for commands.

Gateway-only `HOOK.yaml` is not enough for parity because it does not cover CLI.

### Contract Impact

Current Hermes artifacts say:

- lifecycle start: `explicit_command`
- lifecycle end: `not_available`
- boot trigger: `explicit_tutor_command`

Those are stale relative to current upstream hook docs. Update targets should be:

- lifecycle start: `hook`
- lifecycle end: `hook`
- boot trigger: Hermes `pre_llm_call` hook

## Cross-Host Design Notes

Do not force all hosts into Claude's exact event names. Use capability semantics:

- `boot_context_injection`: whether host can inject context into model-visible
  startup/turn context.
- `session_end_persistence`: whether host can run guaranteed or best-effort
  persistence at session/turn end.
- `shutdown_finalizer`: whether host can flush during process/session teardown.

Proposed enum refinements:

- Add `LifecycleEnd.TURN_STOP` for Codex `Stop`.
- Add boot trigger values:
  - `codex_session_start_hook`
  - `openclaw_prompt_hook`
  - `hermes_pre_llm_hook`
- Keep `not_available` for hosts with no reliable finalization hook.

Preserve core boundaries:

- No host adapter owns pedagogy.
- No host hook reads or writes SQLite directly.
- No host package ships learner state, sessions, memories, secrets, logs, or local
  config.
- All host hooks delegate to `bin/tutor`.

## Implementation Sequence

1. Update contracts and capability schemas before changing host packages.
2. Add host-specific thin wrappers.
3. Add package/privacy tests for new hook files.
4. Add adapter contract tests for new lifecycle declarations.
5. Manually verify each host because hook execution is host-runtime behavior.

Suggested rollout order:

1. Codex project-local `SessionStart` hook, because official config shape is simple.
2. Hermes plugin/shell hooks, because `pre_llm_call` directly supports context injection.
3. OpenClaw plugin hook update, because current TypeScript package likely needs SDK API
   changes and real SDK validation.

## Open Questions

- Should Codex use project-local hooks only, or also ship plugin-bundled hooks for
  users who install outside this repo?
- Should `bin/tutor session-end` accept a host-normalized lifecycle payload with
  `reason`, `completed`, and `interrupted` fields?
- How should OpenClaw track "boot injected once per session" without adding tutor
  state to the host plugin?
- Should Hermes use a plugin package or shell hooks in profile config for first
  implementation?

