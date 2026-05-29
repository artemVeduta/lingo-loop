# Install lingo-loop for OpenClaw

> Verification pending — not yet confirmed against a specific OpenClaw release. <!-- TODO: verify against current OpenClaw release, then set "Last verified: YYYY-MM-DD against OpenClaw vX.Y" -->

## Prerequisites
- Python 3.12+
- Node.js 22+ (declared by the plugin's `engines.node`)
- OpenClaw ≥ 1.0.0 installed (declared as a `peerDependency`)

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

Select **OpenClaw** in the keyboard menu. Arrow keys move, Space toggles, and
Enter continues/applies; no provider id typing is required. This writes a
managed plugin registration at
`~/.openclaw/plugins/lingo-loop/package.json` (copy of the bundled
`openclaw-plugin/package.json`) and verifies the result. After it succeeds,
run `openclaw plugins install lingo-loop` so OpenClaw picks up the plugin.
Rerun `tutor init` any time to repair drift. Automation form: `tutor init
--provider openclaw --yes`. Use `--dry-run --json` to preview.

<!-- TODO: verify exact `openclaw plugins install lingo-loop` syntax against current OpenClaw release, including whether the host CLI noun is `plugins` (this command, by-name) or `plugin` (the manual-fallback by-path form below) — reconcile to whichever the real CLI uses -->

## Manual fallback — install the OpenClaw plugin from a clone

The plugin package is `@language-tutor/openclaw-plugin` (npm scope; the PyPI distribution is `lingo-loop`) under `openclaw-plugin/` in this repository. Manifest highlights:

- `license`: `MIT`
- `engines.node`: `>=22`
- `peerDependencies.openclaw`: `>=1.0.0`
- `openclaw.extensions`: `./dist/index.js`
- `main`: `dist/index.js`

Build and install from a local clone:

```bash
git clone https://github.com/artemVeduta/lingo-loop.git
cd lingo-loop/openclaw-plugin
npm install
npm run build

# install into OpenClaw from the built directory
openclaw plugin install $(pwd)
```

<!-- TODO: verify exact `openclaw plugin install` syntax against current OpenClaw release -->

## Screenshot

<!-- TODO(oss-baseline-assets): capture screenshot of OpenClaw plugins panel showing @language-tutor/openclaw-plugin (from lingo-loop) enabled -->
*(Screenshot pending — see `docs/internal/launch-checklist.md`.)*

## First session

<!-- TODO(oss-baseline-assets): record asciinema cast of first OpenClaw tutor session -->
*(Cast pending — see `docs/internal/launch-checklist.md`.)*

## Verify

1. In OpenClaw's plugins panel, `@language-tutor/openclaw-plugin 0.1.0` (shipped by the `lingo-loop` distribution) is listed and enabled.
2. Triggering a tutor skill from the OpenClaw host invokes `tutor session-start --json` and renders the boot context.

```bash
tutor doctor --json | jq '.status'
```

Should print `"ok"`.

## Troubleshooting

### Error: `Unsupported engine: required node >=22`
**Cause:** OpenClaw is running on an older Node runtime than the plugin requires.
**Fix:** Upgrade to Node.js 22 or newer (e.g. via `nvm install 22 && nvm use 22`), then reinstall the plugin.

### Error: Plugin fails to load — `Cannot find module './dist/index.js'`
**Cause:** The plugin was installed without running `npm run build`.
**Fix:** `cd openclaw-plugin && npm install && npm run build`, then reinstall.

### Error: `peer dep openclaw >=1.0.0 not satisfied`
**Cause:** The host OpenClaw version is older than 1.0.0.
**Fix:** Upgrade OpenClaw to ≥1.0.0. The plugin does not bundle the host.

## Uninstall

```bash
openclaw plugin uninstall @language-tutor/openclaw-plugin  # npm package name; PyPI distribution is lingo-loop
uv tool uninstall lingo-loop
```

Local data (profile/preferences/SQLite history) persists. See [privacy](../privacy.md).
