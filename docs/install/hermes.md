# Install lingo-loop for Hermes

> Verification pending — not yet confirmed against a specific Hermes release. <!-- TODO: verify against current Hermes release, then set "Last verified: YYYY-MM-DD against Hermes vX.Y" -->

## Prerequisites
- Python 3.12+
- Hermes CLI installed
- `ANTHROPIC_API_KEY` exported in the shell that launches Hermes (declared in `hermes-profile/distribution.yaml` `env_requires`; never bundled)

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

Select **Hermes** in the keyboard menu. Arrow keys move, Space toggles, and Enter
continues/applies; no provider id typing is required. This writes a managed
profile at `~/.hermes/profiles/lingo-loop/distribution.yaml` (copy of the
bundled `hermes-profile/distribution.yaml`) and verifies the result. Rerun any
time to repair drift. Automation form: `tutor init --provider hermes --yes`.
Use `--dry-run --json` to preview.
`ANTHROPIC_API_KEY` stays a user-owned environment variable — `tutor init`
never reads or writes it.

## Manual fallback — install the Hermes profile from a clone

The Hermes distribution lives under `hermes-profile/`. Key manifest fields:

- `schema_version`: `1`
- `name`: `language-tutor` (in-host profile identifier; the PyPI distribution is `lingo-loop`)
- `display_name`: `Language Tutor`
- `version`: `0.1.0`
- `license`: `MIT`
- `source_url`: `https://github.com/artemVeduta/lingo-loop`
- `profile.prompt`: `SOUL.md`
- `profile.config`: `config.yaml`
- `profile.skills`: `../skills` (reuses the root `skills/` tree)

Install (recommended via the upstream Hermes profile installer):

```bash
hermes profile install https://github.com/artemVeduta/lingo-loop --subdir hermes-profile
```

<!-- TODO: verify exact `hermes profile install` syntax for git+subdir against current Hermes release -->

Update later with:

```bash
hermes profile update language-tutor  # Hermes profile name; PyPI distribution is lingo-loop
```

Export the required API key before launching:

```bash
export ANTHROPIC_API_KEY=sk-ant-...
hermes run language-tutor  # Hermes profile name; PyPI distribution is lingo-loop
```

The Hermes manifest's `exclude:` list ensures no SQLite, `.env`, secrets, sessions, memories, logs, or caches are ever packaged in the distribution.

## Screenshot

<!-- TODO(oss-baseline-assets): capture screenshot of Hermes profile listing showing the language-tutor profile (from lingo-loop) installed -->
*(Screenshot pending — see `docs/internal/launch-checklist.md`.)*

## First session

<!-- TODO(oss-baseline-assets): record asciinema cast of `hermes run language-tutor` (lingo-loop) first session -->
*(Cast pending — see `docs/internal/launch-checklist.md`.)*

## Verify

1. `hermes profile list` should include `language-tutor 0.1.0` (the Hermes profile name shipped by `lingo-loop`).
2. `hermes run language-tutor` (Hermes profile name; PyPI distribution is `lingo-loop`) should boot, load `SOUL.md`, and invoke `tutor session-start --json` on first tutor message.
3. Confirm the boot block renders Profile / Session / Due Review / Weak Patterns / Latest Recap / Local Status.

## Troubleshooting

### Error: `ANTHROPIC_API_KEY is not set`
**Cause:** Hermes launched without the required env var; `env_requires` is documentation-only and is not auto-injected.
**Fix:** `export ANTHROPIC_API_KEY=...` in the shell that runs `hermes run`, or add it to your shell profile.

### Error: Profile install pulls the wrong directory
**Cause:** The Hermes profile lives in the `hermes-profile/` subdirectory of the repository, not at the repository root.
**Fix:** Pass `--subdir hermes-profile` to the install command, or point at a Hermes-only mirror if your release process publishes one.

### Error: Skills do not load (`../skills not found`)
**Cause:** The profile manifest references `../skills` relative to the profile root, expecting the full repository layout.
**Fix:** Install from a full repository checkout. Standalone copies of `hermes-profile/` will not work.

## Uninstall

```bash
hermes profile uninstall language-tutor  # Hermes profile name; PyPI distribution is lingo-loop
uv tool uninstall lingo-loop
```

Local data (profile/preferences/SQLite history) persists. See [privacy](../privacy.md).
