# Engine

This subsystem is the core decision logic of the tutor — the pure, golden-tested heart
that decides what to teach, how to schedule reviews, and how to score answers. It lives as
top-level modules in `src/language_tutor/` and deliberately depends only on the data access
layer and the shared contracts, never on a host. Keeping it pure is what lets it be golden
-tested: given the same inputs it produces the same outputs, independent of which host or
storage backend is wired up.

## Contracts

- `src/language_tutor/schemas.py` — the Pydantic models and enums that are the single
  source of truth for every contract in the system (boot, lifecycle, feedback, vocabulary,
  install, host capabilities). Every other module imports its shapes from here.
- `src/language_tutor/errors.py` — the shared `TutorError` and structured-failure
  helpers used across the engine and CLI.

## Session lifecycle and boot

- `src/language_tutor/lifecycle.py` — starting and ending sessions, prior-session
  summaries, and the abandonment/labeling rules.
- `src/language_tutor/boot_context.py` — assembles the token-budgeted boot context
  (learner profile, preferences, weak-tag signals) and maps a host's declared boot trigger
  to a lifecycle path.

## Scheduling and scoring

- `src/language_tutor/srs.py` — the in-tree SM-2 spaced-repetition scheduler: maps a
  verdict to a quality score and computes the next review interval.
- `src/language_tutor/evaluators.py` — scores learner answers into verdicts the rest of
  the engine consumes.
- `src/language_tutor/feedback.py` — renders structured feedback (error spans, verdicts,
  review history) into the markdown the learner sees.

## Learning modes

- `src/language_tutor/vocab.py`, `src/language_tutor/writing.py`,
  `src/language_tutor/reading.py`, `src/language_tutor/lessons.py`,
  `src/language_tutor/text_modalities.py` — the per-mode decision logic for vocabulary
  drills, writing practice, reading practice, structured lessons, and shared text
  handling.

## Progress, setup, and health

- `src/language_tutor/progress.py` and `src/language_tutor/progress_rendering.py` —
  compute a progress report and render it to markdown.
- `src/language_tutor/setup.py` — the learner-facing setup/onboarding decision logic.
- `src/language_tutor/health.py` — the doctor/health check over the install and data state.
- `src/language_tutor/package_assets.py` — locates assets packaged with the distribution.
