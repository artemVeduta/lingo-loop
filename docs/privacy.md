# Privacy

`lingo-loop` is **local-first**. The tutor CLI stores all learner data on the same machine that runs it and makes no network calls of its own.

## What we collect

**Nothing.** There is no telemetry, no analytics, no crash reporting, no usage pings, no account, no signup. The project ships no code that contacts a server controlled by the maintainer.

## What touches the network

Only the AI host you choose (Claude Code, Codex, Hermes, OpenClaw). The host sends your prompts to its configured LLM provider using credentials *you* supply to the host. Read your host's privacy policy for the details of that traffic.

The `tutor` CLI itself opens no sockets.

## Where your data lives

All paths default to OS-standard locations (resolved by [`platformdirs`](https://pypi.org/project/platformdirs/) under the app name `language-tutor`). Run `tutor doctor --json` to see your actual resolved paths.

| Data | Default location (Linux / macOS) | Contents |
|---|---|---|
| Profile | `~/.config/language-tutor/profile.yaml` | Languages, CEFR level, interests, constraints |
| Preferences | `~/.config/language-tutor/preferences.yaml` | Session length, verbosity, intensity |
| Learning history | `~/.local/state/language-tutor/history.sqlite3` | Sessions, vocab, SRS schedule, mistakes, feedback |

On Windows: `%APPDATA%\language-tutor\` and `%LOCALAPPDATA%\language-tutor\`.

Override the entire tree with `LANGUAGE_TUTOR_HOME=/path/to/dir`. See [configuration](configuration.md).

## Deleting your data

Local only — no upstream copy exists to revoke. To remove everything:

```bash
rm -rf ~/.config/language-tutor ~/.local/share/language-tutor ~/.local/state/language-tutor
```

(Adjust paths for your platform; `tutor doctor --json` prints them exactly.)

To uninstall the CLI:

```bash
uv tool uninstall lingo-loop
```

## Distribution artifacts and exclusions

The Hermes profile manifest (`hermes-profile/distribution.yaml`) explicitly excludes the following from any packaged distribution: `.env`, `*.env`, `secrets/`, `memories/`, `sessions/`, `*.sqlite*`, `*.db*`, `logs/`, `*.log`, `caches/`, `*.cache`, `local/`, `local_overrides/`. The Codex and Claude plugins ship only skill markdown and manifests — no learner data.

## What we are *not* protecting against

Local-first is not encryption. Anything in `~/.config/language-tutor/` and `~/.local/state/language-tutor/` is readable by any process or user with access to your home directory. If you need at-rest encryption, use full-disk encryption (FileVault, LUKS, BitLocker) or move `LANGUAGE_TUTOR_HOME` onto an encrypted volume.

## Questions or concerns

Open a [GitHub Discussion](https://github.com/artemVeduta/lingo-loop/discussions) or — for security-sensitive reports — file a private advisory via the repository's Security tab (see `SECURITY.md`).
