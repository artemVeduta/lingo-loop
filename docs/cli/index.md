# CLI

This subsystem is the single `tutor` command-line entrypoint. It is the one process that
user-facing skills and hosts shell out to: it parses arguments, resolves paths and opens
the repository, dispatches into the engine, and serializes results (typically JSON) back to
the caller. The CLI is intentionally a thin shell — it wires the data access layer to the
engine and handles I/O and error formatting, but holds no decision logic of its own.

## Entrypoint

- `src/language_tutor/cli.py` — the Click application defining the `tutor` command group
  and its subcommands (boot context, session start/end, feedback, progress, lessons,
  reading, health/doctor, and more). It resolves XDG paths via the data access layer,
  constructs the `TutorRepository`, calls the matching engine module, and renders the
  result, converting `TutorError`s into structured JSON failures.
