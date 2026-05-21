# Quickstart: Richer Feedback & Progress

## Goal

Verify that Phase 4 progress generation stays local-first, deterministic, text/markdown-only, and fast on one year of daily history.

## Generate A JSON Progress Report

```bash
rtk tutor progress --json '{"window_size":10,"generated_at":"2026-05-21T12:00:00Z"}'
```

Expected:

- Valid `ProgressReport` JSON.
- Required `generated_at` equals the supplied timestamp.
- Per-tag mastery rows include score, band, evidence count, last-seen age, trend, and next-practice hint when history exists.
- No raw learner answers, span text, full feedback prose, event logs, or host metadata.

## Render Markdown From A Report

```bash
rtk tutor progress --json '{"window_size":10,"generated_at":"2026-05-21T12:00:00Z"}' > /tmp/progress-report.json
rtk tutor render progress-report --json "$(rtk proxy cat /tmp/progress-report.json)"
```

Expected:

- Response content type is `text/markdown`.
- Markdown contains report window, snapshot, tag mastery, recent recap, ASCII trends, skipped-data notices, and guardrails.
- Sparkline output uses only `.:-=+*#%@`.
- No chart, GUI, web view, Mermaid, SVG, or rich dashboard output.

## No-Data Flow

```bash
rtk tutor progress --json '{"generated_at":"2026-05-21T12:00:00Z"}'
```

Expected with empty local state:

- Valid report, not an error.
- Recap direction is `insufficient_data`.
- Message suggests vocabulary or writing practice.
- Costs and optional summaries are marked unavailable or omitted safely.

## Determinism Check

Run the same command twice with the same local state and supplied timestamp:

```bash
rtk tutor progress --json '{"window_size":10,"generated_at":"2026-05-21T12:00:00Z"}' > /tmp/progress-a.json
rtk tutor progress --json '{"window_size":10,"generated_at":"2026-05-21T12:00:00Z"}' > /tmp/progress-b.json
rtk diff -u /tmp/progress-a.json /tmp/progress-b.json
```

Expected: no diff.

## Window Validation

```bash
rtk tutor progress --json '{"window_size":0}'
rtk tutor progress --json '{"window_size":31}'
```

Expected: structured validation errors.

## Required Test Gates

```bash
rtk uv run pytest tests/unit/test_progress.py tests/unit/test_schemas.py tests/unit/test_repositories.py
rtk uv run pytest tests/golden/test_progress_rendering.py
rtk uv run pytest tests/adapter_contract/test_progress_cli.py tests/adapter_contract/test_cli_json_contract.py
rtk uv run pytest tests/integration/test_progress_flow.py
rtk uv run pytest tests/migration/test_migrations.py
rtk uv run pytest tests/performance/test_progress_performance.py
rtk uv run pyright
rtk uv run ruff check .
```

## Fixture Expectations

Implementation tasks should create deterministic fixtures for:

- No sessions, reviews, or mistakes.
- One completed session.
- Last-N windows of 1, 5, 10, and 30 sessions.
- Tied tag mastery evidence.
- Historical stale tag evidence.
- Duplicate session IDs where the latest valid analyzed record wins, covered through the canonicalization unit tests even though current SQLite writes usually collapse duplicate summaries.
- Interrupted, invalid, missing-analysis, and older-state optional-field gaps.
- Long tag names and long practice hints.
- One year of daily completed sessions with dense mistakes and reviews.

## Exit Gate

Phase 4 is ready for tasks only when this plan's artifacts define:

- The canonical JSON report contract.
- Markdown rendering contract.
- Mastery scoring and sorting rules.
- Trend and ASCII sparkline rules.
- Skipped-data reporting.
- Test and performance gates.
