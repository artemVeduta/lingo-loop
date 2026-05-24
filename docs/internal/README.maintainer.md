# language-tutor

Local-first Claude Code language tutor with one Python CLI boundary.

## Install

```bash
rtk uv venv
rtk uv pip install -e ".[dev]"
```

## Use

```bash
rtk tutor doctor --json
rtk tutor setup write --json '{"profile":{"native_language":"en","target_language":"uk"},"preferences":{}}'
rtk tutor boot-context --json
rtk tutor vocab start --json
rtk tutor writing prompt --json
rtk tutor progress --json
```

Learner profile and preferences are editable YAML. Transactional learning state stays in local SQLite. No telemetry, auth, cloud sync, or remote storage is used.

## Agent Host Setup

Spec 006 implements source-backed setup paths for Hermes, OpenClaw, Claude, and Codex. Each host slice is owned by one implementation subagent and ships in its own root: `hermes-profile/`, `openclaw-plugin/`, `.claude-plugin/` (existing baseline), and `.codex-plugin/` + `.agents/plugins/marketplace.json`. Capability profiles and boot triggers are inspectable via `tutor host capability <host>` and `tutor host boot-trigger <host>`. **Antigravity is fully out of scope** — no Antigravity profile, adapter, package, or doc artifact exists, and `HostId` rejects it at the schema layer (`tests/packaging/test_host_setup_profiles.py::test_no_antigravity_artifacts`).

### Hermes

```bash
rtk hermes profile install <local-hermes-profile-path> --name language-tutor-test --alias
rtk hermes profile info language-tutor-test
rtk hermes profile update language-tutor-test
rtk hermes profile delete language-tutor-test
```

Expected: Hermes installs a profile distribution with `distribution.yaml`, tutor prompt/config/skills as needed, and user-owned `.env`, memories, sessions, state DBs, logs, caches, and `local/` untouched.

### OpenClaw

```bash
rtk pnpm test -- <openclaw-plugin-root>
rtk pnpm check
rtk clawhub package publish <org>/<plugin> --dry-run
rtk openclaw plugins install <package-name>
```

Expected: OpenClaw recognizes `package.json`, `openclaw.plugin.json`, the TypeScript ESM entry point, focused SDK imports, and optional side-effectful tools only after user allowlist.

### Claude

```bash
rtk claude plugin validate <plugin-root> --strict
rtk claude --plugin-dir <plugin-root>
```

Inside Claude, run `/reload-plugins`, verify tutor skills/agents are loaded, then run reading, lesson, transcript, vocab, writing, and progress flows. The plugin does **not** install any hooks — boot happens on the first tutor message via `tutor session-start --json` (spec 007 hook-free lifecycle).

### Codex

Codex setup uses `.codex-plugin/plugin.json` and a local or repo-scoped marketplace entry. The current official Codex build docs do not document a standalone validator, so verification is manual:

1. Add or update the marketplace entry for the local plugin.
2. Restart Codex.
3. Install or enable the plugin from that marketplace.
4. Verify tutor skills are visible.
5. Run reading, lesson, transcript, vocab, writing, and progress flows. The Codex plugin does **not** require any hook to be enabled — boot happens on the first tutor message via `tutor session-start --json` (spec 007 hook-free lifecycle).

Expected: Codex loads the cached plugin copy and keeps workspace/user data boundaries intact.
