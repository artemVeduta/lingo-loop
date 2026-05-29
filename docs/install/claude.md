# Install lingo-loop for Claude Code

> Verification pending — not yet confirmed against a specific Claude Code CLI release. <!-- TODO: verify against current Claude Code release, then set "Last verified: YYYY-MM-DD against Claude Code vX.Y" -->

## Prerequisites
- Python 3.12+
- [Claude Code](https://docs.claude.com/claude-code) CLI installed and signed in
- An Anthropic API key configured for Claude Code (the tutor reuses the host's LLM access — it does not call Anthropic directly)

## Step 0 — Install the tutor CLI

```bash
uv tool install lingo-loop
tutor doctor --json

# Install from source instead (fallback):
# uv tool install git+https://github.com/artemVeduta/lingo-loop
```

`tutor doctor` should report `status: ok` and print the resolved profile/preferences/database paths.

> The distribution name is `lingo-loop` but the Python module installed on disk is still `language_tutor`. This is intentional for v0.1; see [troubleshooting](../troubleshooting.md).

## Step 1 — Guided wiring via `tutor init`

```bash
tutor init
```

Select **Claude Code** in the keyboard menu. Arrow keys move, Space toggles, and
Enter continues/applies; no provider id typing is required. This writes a
managed plugin registration file at
`~/.claude/plugins/lingo-loop/plugin.json` (copy of the bundled manifest) and
verifies the result. Rerun any time to repair drift; learner profile, history,
and secrets are never touched. Automation form: `tutor init --provider claude
--yes`. Pass `--dry-run --json` to preview without writing.

## Manual fallback — load the plugin directly

If you prefer to load the Claude plugin from a clone:

```bash
# from a clone of the repository
git clone https://github.com/artemVeduta/lingo-loop.git
cd lingo-loop

# tell Claude Code to load the plugin from this checkout
claude plugin install ./.claude-plugin
```

Then open Claude Code and confirm the `language-tutor` plugin appears in `/plugin` (the manifest name is `language-tutor`; the PyPI distribution is `lingo-loop`).

The plugin manifest declares:

- `name`: `language-tutor` (the in-host plugin identifier; the PyPI distribution is `lingo-loop`)
- `version`: `0.1.0`
- `license`: `MIT`

<!-- TODO: verify exact `claude plugin install` syntax against current Claude Code CLI -->

## Screenshot

<!-- TODO(oss-baseline-assets): capture screenshot of Claude /plugin panel showing the language-tutor plugin (from lingo-loop) enabled -->
*(Screenshot pending — see `docs/internal/launch-checklist.md`.)*

## First session

<!-- TODO(oss-baseline-assets): record asciinema cast of first Claude session (greeting -> tutor reading) -->
*(Cast pending — see `docs/internal/launch-checklist.md`.)*

## Verify

1. In Claude Code, send: `start a tutor reading session`.
2. The skill `tutor-reading` should activate and call `tutor session-start --json`.
3. You should see a boot context block with **Profile**, **Session**, **Due Review**, **Weak Patterns**, **Latest Recap**, **Local Status** sections.

Confirm from the shell:

```bash
tutor session-start --json | jq '.sections[].title'
```

Expected: the six section titles above.

## Troubleshooting

### Error: `tutor: command not found`
**Cause:** `uv tool install` placed the CLI in a directory not on `PATH`.
**Fix:** Add `~/.local/bin` (Linux/macOS) to your shell `PATH`, or run `uv tool update-shell`.

### Error: Claude Code does not list the plugin
**Cause:** Plugin path was not registered, or Claude Code was started before installing.
**Fix:** Re-run `claude plugin install ./.claude-plugin` from the repo root, then restart Claude Code.

### Error: `Invalid YAML at ~/.config/language-tutor/profile.yaml` (lingo-loop's on-disk module directory is still `language-tutor`)
**Cause:** The profile YAML was hand-edited into an invalid state.
**Fix:** Move the broken file aside (`mv profile.yaml profile.yaml.bak`) and re-run `tutor setup write` to regenerate defaults, then re-apply your edits.

## Uninstall

```bash
claude plugin uninstall language-tutor  # in-host plugin name; PyPI distribution is lingo-loop
uv tool uninstall lingo-loop
```

Profile, preferences, and learning history remain on disk (see [privacy](../privacy.md)). Delete them manually if desired (paths use the on-disk `language-tutor` module name from `lingo-loop`):

```bash
rm -rf ~/.config/language-tutor ~/.local/share/language-tutor ~/.local/state/language-tutor  # lingo-loop user data
```
