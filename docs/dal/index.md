# Data access layer

This subsystem is the persistence boundary for the tutor. It owns where data lives on
disk and how it is read and written, keeping storage concerns out of the decision engine.
Configuration is stored as human-editable YAML; learner activity is recorded in an
append-only SQLite event ledger. All locations follow XDG conventions so the engine and
CLI never hard-code paths and can be exercised hermetically against a temporary root.

## Paths

- `src/language_tutor/dal/paths.py` — resolves the XDG config, data, and state
  directories (`TutorPaths`) and the derived file locations (e.g. the profile YAML), so
  every other module asks here for "where" rather than computing paths itself.

## Stores

- `src/language_tutor/dal/yaml_store.py` — reads and writes the human-editable YAML
  configuration (profile and preferences).
- `src/language_tutor/dal/sqlite_store.py` — opens the SQLite connection (foreign keys
  on, row factory configured) and exposes the transaction helper for the append-only
  event ledger.
- `src/language_tutor/dal/migrations.py` — applies the schema migrations the SQLite store
  needs before use.

## Repositories

- `src/language_tutor/dal/repositories.py` — the `TutorRepository` facade that the engine
  and CLI call; it composes the YAML and SQLite stores behind one interface so callers
  depend on an abstraction rather than on raw storage details.
