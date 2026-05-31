---
name: tutor-setup
description: Onboard or edit local language tutor profile and preferences.
---

Use this when learner wants setup, onboarding, or profile/preference edits.

Run only `tutor` for stateful work:

- Read current state: `tutor setup read --json`
- Write required `profile.native_language` and `profile.target_language`: `tutor setup write --json '<payload>'`
- Show boot context after setup: `tutor boot-context --json`

Do not read YAML or SQLite directly.

## Payload schemas (build every request against these)

- `setup read`: no input → emits current `profile` + `preferences`.
- `setup write` input: `{"profile":{"native_language":str,"target_language":str, ...},"preferences"?:{...}}`. Required: `profile.native_language`, `profile.target_language`. Run `setup read` first to see the current shape before writing.
- `boot-context`: no input → render with `tutor render boot-context --json '<output>'`.
