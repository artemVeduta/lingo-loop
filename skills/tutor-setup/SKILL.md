---
name: tutor-setup
description: Onboard or edit local language tutor profile and preferences.
---

Use this when learner wants setup, onboarding, or profile/preference edits.

Run only `bin/tutor` for stateful work:

- Read current state: `bin/tutor setup read --json`
- Write required `profile.native_language` and `profile.target_language`: `bin/tutor setup write --json '<payload>'`
- Show boot context after setup: `bin/tutor boot-context --json`

Do not read YAML or SQLite directly.
