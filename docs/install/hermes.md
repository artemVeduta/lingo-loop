# Install lingo-loop for Hermes

> Last verified: 2026-05-24 against Hermes version <!-- TODO: verify -->

## Prerequisites
- Python 3.12+
- Hermes CLI installed
- `ANTHROPIC_API_KEY` exported in the shell that launches Hermes (declared in `hermes-profile/distribution.yaml` `env_requires`; never bundled)

## Step 0 — Install the tutor CLI

```bash
# PyPI publish is pending; install from source for now:
uv tool install git+https://github.com/artemVeduta/lingo-loop
tutor doctor --json
```

> The distribution name is `lingo-loop` but the Python module installed on disk is still `language_tutor`. This is intentional for v0.1; see [troubleshooting](../troubleshooting.md).

## Step 1 — Guided wiring via `tutor init`

```bash
tutor init --provider hermes --yes
```

Writes a managed profile at `~/.hermes/profiles/lingo-loop/distribution.yaml`
(copy of the bundled `hermes-profile/distribution.yaml`) and verifies the
result. Rerun any time to repair drift. Use `--dry-run --json` to preview.
`ANTHROPIC_API_KEY` stays a user-owned environment variable — `tutor init`
never reads or writes it.

## Manual fallback — install the Hermes profile from a clone

The Hermes distribution lives under `hermes-profile/`. Key manifest fields:

- `schema_version`: `1`
- `name`: `language-tutor`
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
hermes profile update language-tutor
```

Export the required API key before launching:

```bash
export ANTHROPIC_API_KEY=sk-ant-...
hermes run language-tutor
```

The Hermes manifest's `exclude:` list ensures no SQLite, `.env`, secrets, sessions, memories, logs, or caches are ever packaged in the distribution.

## Screenshot

<!-- TODO(oss-baseline-assets): capture screenshot of Hermes profile listing showing language-tutor installed -->
*(Screenshot pending — see `docs/internal/launch-checklist.md`.)*

## First session

<!-- TODO(oss-baseline-assets): record asciinema cast of `hermes run language-tutor` first session -->
*(Cast pending — see `docs/internal/launch-checklist.md`.)*

## Verify

1. `hermes profile list` should include `language-tutor 0.1.0`.
2. `hermes run language-tutor` should boot, load `SOUL.md`, and invoke `tutor session-start --json` on first tutor message.
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
hermes profile uninstall language-tutor
uv tool uninstall lingo-loop
```

Local data (profile/preferences/SQLite history) persists. See [privacy](../privacy.md).
