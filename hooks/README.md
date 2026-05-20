# Hooks

`hooks/session-start.sh` calls `bin/tutor boot-context --json` and `bin/tutor render boot-context --json`.
`hooks/session-end.sh` calls `bin/tutor session-end --json` without owning persistence logic.

Claude discovers hooks from root-level `hooks/hooks.json`; skills, agents, and CLI wrappers remain separate root-level plugin components.
