# Configuration

`lingo-loop` (CLI: `tutor`) is configured through two YAML files and a small set of environment variables. All state is local; see [privacy](privacy.md).

## File locations

Resolved by [`platformdirs`](https://pypi.org/project/platformdirs/) under the application name `language-tutor`:

| File | Default path (Linux / macOS) | Purpose |
|---|---|---|
| `profile.yaml` | `~/.config/language-tutor/profile.yaml` | Who you are: languages, level, interests, constraints |
| `preferences.yaml` | `~/.config/language-tutor/preferences.yaml` | How sessions run: length, intensity, verbosity |
| `history.sqlite3` | `~/.local/state/language-tutor/history.sqlite3` | Learning history, SRS schedule, vocab |

On Windows the paths follow `%APPDATA%\language-tutor\` and `%LOCALAPPDATA%\language-tutor\`. Run `tutor doctor --json` to see the actual resolved paths on your machine.

> The on-disk app folder name is `language-tutor` (matching the Python module path). The distribution name on PyPI will be `lingo-loop`. Both refer to the same project.

## Environment variables

| Variable | Effect |
|---|---|
| `LANGUAGE_TUTOR_HOME` | Override the resolved root. The CLI uses `$LANGUAGE_TUTOR_HOME/config`, `.../data`, `.../state` instead of platform defaults. Useful for sandboxing or per-project profiles. |

The tutor CLI itself makes no network calls. The AI host (Claude, Codex, Hermes, OpenClaw) supplies the LLM and uses its own credentials. The only host-side env var declared by a shipped manifest today is `ANTHROPIC_API_KEY` (Hermes profile), which the host reads — not the tutor.

## `profile.yaml`

Schema (see `LearnerProfile` in `src/language_tutor/schemas.py`):

```yaml
schema_version: 1
native_language: en          # ISO 639-1 code or free-form string
target_language: uk          # language you are learning
level_target: A1             # CEFR level you aim for
interests: []                # list[str] — topical seeds for content
constraints: []              # list[str] — things to avoid or accommodate
created_at: 2026-05-24T00:00:00+00:00
updated_at: 2026-05-24T00:00:00+00:00
```

Defaults if the file is absent: `en → uk`, `level_target: A1`, empty `interests` and `constraints`. Run `tutor setup write` to generate the file with current defaults.

## `preferences.yaml`

Schema (see `LearnerPreferences`):

```yaml
schema_version: 1
session_length: 10           # minutes, 1..60
review_intensity: normal     # one of: light | normal | heavy  (TODO: verify enum values)
feedback_verbosity: concise  # one of: concise | detailed       (TODO: verify enum values)
transliteration_tolerance: false   # true: accept transliterated input
ascii_fallback: false              # true: render without non-ASCII glyphs
streak_grace_days: 1               # 0..14
updated_at: 2026-05-24T00:00:00+00:00
```

`transliteration_tolerance` defaults to `true` for non-Cyrillic target languages and `false` for `uk`/`ru`/`bg`/`sr`.

## Overriding configuration

There are three ways to change config, in order of preference:

1. **Edit the YAML files directly.** Re-run `tutor doctor --json` to confirm they parse.
2. **`tutor setup write`** — regenerates files from defaults; existing fields you have set are preserved where possible.
3. **`LANGUAGE_TUTOR_HOME=/tmp/sandbox tutor ...`** — point the entire config/data/state tree at a different root for a one-off run.

## Validating

```bash
tutor doctor --json
```

Reports:

- resolved paths
- whether each file exists and parses
- database migrations status
- overall `status: ok | error`

If YAML fails to parse you will see `error_code: invalid_yaml` with the offending path. Move the file aside and re-run `tutor setup write` to regenerate defaults.
