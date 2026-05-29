# Install lingo-loop for Codex

> Verification pending — not yet confirmed against a specific Codex CLI release. <!-- TODO: verify against current Codex CLI release, then set "Last verified: YYYY-MM-DD against Codex CLI vX.Y" -->

## Prerequisites
- Python 3.12+
- Codex CLI installed and signed in
- LLM provider credentials configured in Codex (the tutor reuses the host's LLM access)

## Step 0 — Install the tutor CLI

```bash
uv tool install lingo-loop
tutor doctor --json

# Install from source instead (fallback):
# uv tool install git+https://github.com/artemVeduta/lingo-loop
```

> The distribution name is `lingo-loop` but the Python module installed on disk is still `language_tutor`. This is intentional for v0.1; see [troubleshooting](../troubleshooting.md).

## Step 1 — Guided wiring via `tutor init`

```bash
tutor init
```

Select **Codex** in the keyboard menu. Arrow keys move, Space toggles, and Enter
continues/applies; no provider id typing is required. This writes a managed
plugin registration at `~/.codex/plugins/lingo-loop/plugin.json` (copy of the
bundled `.codex-plugin/plugin.json`) and verifies the result. Rerun any time to
repair drift. Automation form: `tutor init --provider codex --yes`. Use
`--dry-run --json` to preview.

## Manual fallback — install the Codex plugin from a clone

The Codex plugin lives under `.codex-plugin/` in this repository. The manifest declares:

- `schema_version`: `1.0`
- `name`: `language-tutor` (in-host plugin identifier; the PyPI distribution is `lingo-loop`)
- `version`: `0.1.0`
- `license`: `MIT`
- `skills`: `./skills/` (reuses the root `skills/` tree)
- `features.plugin_hooks`: `false`

Install from a local clone:

```bash
git clone https://github.com/artemVeduta/lingo-loop.git
cd lingo-loop

codex plugin install ./.codex-plugin
```

<!-- TODO: verify exact `codex plugin install` syntax against current Codex CLI -->

## Screenshot

<!-- TODO(oss-baseline-assets): capture screenshot of Codex marketplace/plugins pane showing the language-tutor plugin (from lingo-loop) enabled -->
*(Screenshot pending — see `docs/internal/launch-checklist.md`.)*

## First session

<!-- TODO(oss-baseline-assets): record asciinema cast of first Codex tutor session -->
*(Cast pending — see `docs/internal/launch-checklist.md`.)*

## Verify

1. In Codex, invoke a tutor skill (for example, `tutor-reading`).
2. The skill calls `tutor session-start --json` and renders the boot context.

From the shell:

```bash
tutor session-start --json | jq '.profile.target_language'
```

Should print your configured target language (default `"uk"`).

## Troubleshooting

### Error: `tutor: command not found`
**Cause:** `uv tool install` did not add its bin directory to `PATH`.
**Fix:** Run `uv tool update-shell` or add `~/.local/bin` to `PATH`.

### Error: Codex does not see the plugin's skills
**Cause:** The plugin manifest points `skills` at `./skills/` (relative to the plugin root), which expects the repository checkout layout. Installing from a copy that omits the root `skills/` directory will fail.
**Fix:** Install from a full clone of the repository, not a stripped-down copy of `.codex-plugin/` alone.

### Error: Tutor reports `LANGUAGE_TUTOR_HOME` ignored
**Cause:** The variable was set in a shell that Codex did not inherit from.
**Fix:** Export `LANGUAGE_TUTOR_HOME` in the shell profile that launches Codex (e.g. `~/.zshrc`), then restart Codex.

## Uninstall

```bash
codex plugin uninstall language-tutor  # in-host plugin name; PyPI distribution is lingo-loop
uv tool uninstall lingo-loop
```

User data persists on disk; see [privacy](../privacy.md) for paths.
