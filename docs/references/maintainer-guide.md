---
type: Reference
title: Maintainer guide
description: Install, usage, and per-host (Hermes, OpenClaw, Claude, Codex) agent setup and verification commands for language-tutor maintainers.
timestamp: 2026-06-22
---

# language-tutor

Local-first Claude Code language tutor with one Python CLI boundary.

## Install

```bash
uv venv
uv pip install -e ".[dev]"
```

## Use

```bash
tutor doctor --json
tutor setup write --json '{"profile":{"native_language":"en","target_language":"uk"},"preferences":{}}'
tutor boot-context --json
tutor vocab start --json
tutor writing prompt --json
tutor progress --json
```

Learner profile and preferences are editable YAML. Transactional learning state stays in local SQLite. No telemetry, auth, cloud sync, or remote storage is used.

## Agent Host Setup

The agent adapter setup work implements source-backed setup paths for Hermes, OpenClaw, Claude, and Codex. Each host slice ships in its own root: `hermes-profile/`, `openclaw-plugin/`, `.claude-plugin/` (existing baseline), and `.codex-plugin/` + `.agents/plugins/marketplace.json`. Capability profiles and boot triggers are inspectable via `tutor host capability <host>` and `tutor host boot-trigger <host>`. **Antigravity is fully out of scope** — no Antigravity profile, adapter, package, or doc artifact exists, and `HostId` rejects it at the schema layer (`tests/packaging/test_host_setup_profiles.py::test_no_antigravity_artifacts`).

### Hermes

```bash
hermes profile install <local-hermes-profile-path> --name language-tutor-test --alias
hermes profile info language-tutor-test
hermes profile update language-tutor-test
hermes profile delete language-tutor-test
```

Expected: Hermes installs a profile distribution with `distribution.yaml`, tutor prompt/config/skills as needed, and user-owned `.env`, memories, sessions, state DBs, logs, caches, and `local/` untouched.

### OpenClaw

```bash
pnpm test -- <openclaw-plugin-root>
pnpm check
clawhub package publish <org>/<plugin> --dry-run
openclaw plugins install <package-name>
```

Expected: OpenClaw recognizes `package.json`, `openclaw.plugin.json`, the TypeScript ESM entry point, focused SDK imports, and optional side-effectful tools only after user allowlist.

### Claude

```bash
claude plugin validate <plugin-root> --strict
claude --plugin-dir <plugin-root>
```

Inside Claude, run `/reload-plugins`, verify tutor skills/agents are loaded, then run reading, lesson, transcript, vocab, writing, and progress flows. The plugin does **not** install any hooks — boot happens on the first tutor message via `tutor session-start --json`.

### Codex

Codex setup uses `.codex-plugin/plugin.json` and a local or repo-scoped marketplace entry. The current official Codex build docs do not document a standalone validator, so verification is manual:

1. Add or update the marketplace entry for the local plugin.
2. Restart Codex.
3. Install or enable the plugin from that marketplace.
4. Verify tutor skills are visible.
5. Run reading, lesson, transcript, vocab, writing, and progress flows. The Codex plugin does **not** require any hook to be enabled — boot happens on the first tutor message via `tutor session-start --json`.

Expected: Codex loads the cached plugin copy and keeps workspace/user data boundaries intact.
