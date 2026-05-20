# language-tutor

Local-first Claude Code language tutor with one Python CLI boundary.

## Install

```bash
rtk uv venv
rtk uv pip install -e ".[dev]"
```

## Use

```bash
rtk tutor doctor --json
rtk tutor setup write --json '{"profile":{"native_language":"en","target_language":"uk"},"preferences":{}}'
rtk tutor boot-context --json
rtk tutor vocab start --json
rtk tutor writing prompt --json
rtk tutor progress --json
```

Learner profile and preferences are editable YAML. Transactional learning state stays in local SQLite. No telemetry, auth, cloud sync, or remote storage is used.
