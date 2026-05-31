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
continues/applies; no provider id typing is required.

`tutor init --provider codex --yes` writes the shared tutor skills into the
personal Codex skills hub at `<CODEX_HOME|~/.codex>/skills`. No Codex plugin
manifest and no local entry are installed. Restart Codex after initial install
so the skills are loaded. Rerun any time to repair drift. Use `--dry-run --json`
to preview.

## Screenshot

<!-- TODO(oss-baseline-assets): capture screenshot of Codex tutor skill invocation -->
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

### Error: Codex does not see the tutor skills
**Cause:** Codex was started before `~/.codex/skills` was created, or `CODEX_HOME` points elsewhere.
**Fix:** Confirm `~/.codex/skills/tutor-setup/SKILL.md` exists, or check `<CODEX_HOME>/skills/tutor-setup/SKILL.md`, then restart Codex.

### Error: Tutor reports `LANGUAGE_TUTOR_HOME` ignored
**Cause:** The variable was set in a shell that Codex did not inherit from.
**Fix:** Export `LANGUAGE_TUTOR_HOME` in the shell profile that launches Codex (e.g. `~/.zshrc`), then restart Codex.

## Uninstall

```bash
rm -rf ~/.codex/skills/tutor-setup ~/.codex/skills/tutor-vocab ~/.codex/skills/tutor-writing ~/.codex/skills/tutor-reading ~/.codex/skills/tutor-lesson ~/.codex/skills/tutor-progress ~/.codex/skills/tutor-judge
uv tool uninstall lingo-loop
```

User data persists on disk; see [privacy](../privacy.md) for paths.
