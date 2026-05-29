# lingo-loop

> Learn languages inside your AI coding assistant — local-first, no telemetry.

[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![CI](https://github.com/artemVeduta/lingo-loop/actions/workflows/ci.yml/badge.svg)](https://github.com/artemVeduta/lingo-loop/actions/workflows/ci.yml)

<!-- TODO(oss-baseline-assets): record top-level demo cast and render gif via agg, then restore the image + cast links below.
     Until the assets land, omit them to avoid broken-image rendering on GitHub. Tracked in docs/internal/launch-checklist.md. -->
*(Demo recording pending — see [`docs/internal/launch-checklist.md`](docs/internal/launch-checklist.md).)*

## Why

- **Local-first.** Your profile, vocabulary, and progress live in plain files on your machine.
- **No telemetry.** Nothing is sent anywhere except the LLM API call your host already makes.
- **Works inside your IDE.** Practice reading, writing, and vocabulary without leaving Claude Code, Codex, Hermes, or OpenClaw.

## Features

- Reading practice with adaptive vocabulary surfacing.
- Short writing prompts with corrections from your assistant.
- Spaced-repetition vocabulary loop, scheduled across sessions.
- Lesson and transcript flows tailored to your native and target languages.
- Progress tracking you can inspect with a single command.
- Editable YAML profile — language pair, level, and preferences in one place.
- Works across four AI coding hosts with the same CLI underneath.

## Quick start (Claude Code)

> Install with [`uv`](https://docs.astral.sh/uv/) (or clone and run `uv pip install -e ".[dev]"` for a dev setup — see [CONTRIBUTING.md](CONTRIBUTING.md)).

```bash
# 1. Install the CLI
uv tool install lingo-loop

# 2. Detect AI hosts and install plugin wiring for the ones you use
tutor init

# 3. Write your learner profile (native + target language)
tutor setup write --json '{"profile":{"native_language":"en","target_language":"uk"},"preferences":{}}'

# 4. Inside Claude, run /reload-plugins, then ask: "start a reading session"
```

`tutor init` detects Claude, Codex, Hermes, and OpenClaw and shows a keyboard
menu: arrow keys move, Space toggles providers, and Enter continues/applies.
Rerun any time to repair drift — it never touches your learner profile, history,
or secrets.
Non-interactive form: `tutor init --provider claude --yes` (also `--dry-run`,
`--json`).

Full Claude install doc: [`docs/install/claude.md`](docs/install/claude.md)

## Other hosts

- Codex — [`docs/install/codex.md`](docs/install/codex.md)
- Hermes — [`docs/install/hermes.md`](docs/install/hermes.md)
- OpenClaw — [`docs/install/openclaw.md`](docs/install/openclaw.md)

## How it works

```
┌──────────────┐       ┌────────────────┐       ┌─────────────────┐
│  AI Host     │──────▶│  Tutor skill   │──────▶│  tutor CLI      │
│  (Claude/    │       │  (markdown +   │       │  (Python)       │
│  Codex/...)  │       │  prompts)      │       │                 │
└──────────────┘       └────────────────┘       └─────────────────┘
                                                          │
                                          ┌───────────────┼────────────────┐
                                          ▼               ▼                ▼
                                   ┌──────────┐   ┌──────────────┐   ┌─────────┐
                                   │ profile  │   │  learning    │   │  data/  │
                                   │  YAML    │   │   SQLite     │   │ defaults│
                                   └──────────┘   └──────────────┘   └─────────┘

       All state local. No network calls except the host's own LLM API.
```

## Privacy

Your learner profile and preferences live in editable YAML files. Transactional learning state (vocabulary intervals, session history, progress) stays in a local SQLite database under your user data directory. There is no telemetry, no account, no cloud sync, and no remote storage. The only network traffic is the LLM API call your AI host already makes on your behalf.

## Roadmap

Tracked publicly on GitHub:

- [Milestones](https://github.com/artemVeduta/lingo-loop/milestones) — versioned scope.
- [Projects](https://github.com/artemVeduta/lingo-loop/projects) — in-flight work.
- [Discussions](https://github.com/artemVeduta/lingo-loop/discussions) — propose ideas before they become issues.

## Contributing

Pull requests welcome. See [CONTRIBUTING.md](CONTRIBUTING.md) for dev setup, branch naming, commit conventions, and the DCO sign-off policy.

## License

[MIT](LICENSE) © 2026 Artem Veduta
