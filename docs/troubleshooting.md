# Troubleshooting

Cross-host index of common errors. For host-specific issues, jump to that host's install doc:

- [Claude Code](install/claude.md#troubleshooting)
- [Codex](install/codex.md#troubleshooting)
- [Hermes](install/hermes.md#troubleshooting)
- [OpenClaw](install/openclaw.md#troubleshooting)

When in doubt, start with:

```bash
tutor doctor --json
```

It prints the resolved config/data/state paths, whether the YAML files parse, and whether the SQLite database is reachable and migrated.

## Migrating from `language-tutor`

Earlier pre-releases were published under the distribution name `language-tutor`. The PyPI distribution is now `lingo-loop` (the Python module and the `tutor` CLI command are unchanged). If you installed the old name, swap it in place:

```bash
uv tool uninstall language-tutor
uv tool install lingo-loop
```

Your config, data, and state directories are untouched — only the wheel name changed.

## Install-time

### `tutor: command not found`
The `uv tool install` bin directory is not on `PATH`. Run `uv tool update-shell` and restart the shell. The default tool bin directory is `~/.local/bin` (Linux/macOS) or `%USERPROFILE%\.local\bin` (Windows); confirm the exact path with `uv tool dir --bin`.

### `ModuleNotFoundError: No module named 'language_tutor'`
You attempted to run from a source checkout without installing dependencies. Run `uv pip install -e ".[dev]"` from the repo root, or install the published CLI with `uv tool install lingo-loop`.

> Note: the distribution is named `lingo-loop` but the Python module is `language_tutor` and the CLI is `tutor`. This split is intentional.

### `pyright` / `ruff` complaints when running from a clone
You are seeing developer tooling output. End users do not need either tool — install the CLI via `uv tool install`. See `CONTRIBUTING.md` for the dev setup.

## Runtime

### `Invalid YAML at <path>`
A YAML file was hand-edited into an invalid state. Move it aside and regenerate defaults:

```bash
mv ~/.config/language-tutor/profile.yaml ~/.config/language-tutor/profile.yaml.bak
tutor setup write
```

Then re-apply your edits one field at a time, running `tutor doctor --json` after each.

### The boot context is missing sections
The boot context renders up to six sections (Profile, Session, Due Review, Weak Patterns, Latest Recap, Local Status). If any are absent, the underlying repository is empty (no prior sessions) — this is normal on first run.

### SQLite migration errors
The CLI applies migrations on connect. If you see a migration error, the database is older than the installed CLI expects. Easiest recovery: move `history.sqlite3` aside and let the CLI create a fresh database. You will lose history; copy back manually if you can resolve the schema by hand.

```bash
mv ~/.local/state/language-tutor/history.sqlite3{,.bak}
tutor doctor --json
```

### `LANGUAGE_TUTOR_HOME` not honored
The env var must be set in the shell that launches the host (Claude/Codex/Hermes/OpenClaw), not just the one where you run `tutor` directly. Add it to your shell profile (`~/.zshrc`, `~/.bashrc`) and relaunch the host.

## Host wiring

### Skill does not activate in the host
Confirm the plugin/profile is installed and enabled. Each host's panel/list command:

- Claude: `/plugin`
- Codex: plugins pane
- Hermes: `hermes profile list`
- OpenClaw: plugins panel

Then re-check the install doc's *Verify* section.

### Host loads the plugin but `tutor` itself is unreachable from the host
The host runs the plugin's skill markdown, which invokes `tutor` as an external CLI. If `tutor` is not on the host's `PATH`, the skill will fail. Easiest fix: install the CLI globally with `uv tool install lingo-loop` (puts it in `~/.local/bin`) and ensure your shell's `PATH` is inherited by the host.

## Still stuck

Open a [GitHub Discussion](https://github.com/artemVeduta/lingo-loop/discussions) and include the output of `tutor doctor --json`, your host + version, and the OS.
