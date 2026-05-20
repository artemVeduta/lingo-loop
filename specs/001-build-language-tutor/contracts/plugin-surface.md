# Plugin Surface Contract

The Claude Code plugin surface orchestrates user flows only. It must not contain pedagogy, scheduling, persistence rules, or renderer logic.

## Manifest

`.claude-plugin/plugin.json` declares plugin metadata only. Component discovery comes from root-level `skills/`, `hooks/`, `agents/`, and `bin/`.

## Hooks

### SessionStart

`hooks/session-start.sh` calls `bin/tutor boot-context --json`, then renders/returns hook-specific additional context.

Rules:

- Must not mutate learner state except for optional lifecycle event logging.
- Must tolerate missing profile by returning first-run guidance.
- Must keep output bounded and deterministic.

### SessionEnd

`hooks/session-end.sh` calls `bin/tutor session-end --json` asynchronously when supported.

Rules:

- Must validate analyzer output before persistence.
- Must not block host shutdown for non-critical analyzer failure.
- Must persist a short summary usable by the next boot context when valid.

## Skills

### `tutor-setup`

Use when learner wants onboarding or profile/preference edits. Requires native and target language only; defaults all other v1 fields.

### `tutor-vocab`

Use when learner wants due reviews, vocabulary recall, or starter vocabulary practice. Presents due items first and calls CLI commands for state/evaluation.

### `tutor-writing`

Use when learner wants free writing or structured correction. Calls `tutor-judge`, validates through CLI, and renders validated feedback.

### `tutor-progress`

Use when learner wants status, progress, due counts, weak patterns, item maturity, last recap, month-to-date estimated cost, or cost availability status.

Each skill must expose one distinct learner intent and delegate stateful work to the matching CLI command family:

- `tutor-setup`: setup and profile/preference edits through `setup read` and `setup write`.
- `tutor-vocab`: due reviews and starter vocabulary through `vocab start` and `vocab answer`.
- `tutor-writing`: free writing and structured correction through `writing prompt`, `writing record`, and `render feedback`.
- `tutor-progress`: progress/status through `progress`.

## Agent

### `tutor-judge`

Stateless evaluator for free writing. Returns only `FeedbackEnvelope` JSON and never persists.

## Forbidden In Plugin Layer

- Direct SQLite or YAML access from skills.
- SM-2 math in `SKILL.md`.
- Error-tag vocabulary duplicated in prompt prose without importing the core source.
- Feedback rendering as a separate LLM step.
- Alternate host manifests in v1.
