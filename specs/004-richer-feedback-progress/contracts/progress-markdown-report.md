# Contract: Progress Markdown Report

## Output Model

```json
{
  "content_type": "text/markdown",
  "generated_at": "2026-05-21T12:00:00Z",
  "report_window": {
    "requested_session_count": 10,
    "actual_session_count": 10
  },
  "markdown": "# Progress Report\n..."
}
```

## Required Markdown Sections

Markdown rendered from a non-empty report MUST include:

- Title and generated-at timestamp.
- Report window: requested count, actual count, date range.
- Progress snapshot: streak, due count, maturity, weak patterns, cost status when available, next action.
- Per-tag mastery: tag, score, band, evidence count, last-seen age, trend, stale marker when relevant, next-practice hint.
- Recent recap: practice totals, due-review completion, mistake severity totals, weak-tag changes, latest safe summary when available.
- Text trends: plain labels, ASCII sparkline, min/max labels, trend direction.
- Skipped-data notices.
- Scope guardrails.

Markdown rendered from an empty/no-history report MUST include:

- Generated-at timestamp.
- No-data message.
- Suggested next action.
- Scope guardrails.

## Formatting Rules

- Output is terminal-printable markdown, not a GUI/dashboard.
- Sparkline characters are ASCII only: `.:-=+*#%@`.
- No graphical chart images, Mermaid, SVG, HTML, CSS, web links to local files, or rich terminal control codes.
- Lines should target 100 columns where practical.
- Long tags and hints wrap or truncate deterministically with the full value still present in JSON.
- Tables may be used for compact rows, but prose lines are allowed where tables would wrap badly.

## Equivalence Rules

Markdown MUST be rendered from a validated `ProgressReport`.

For a given report, markdown MUST preserve these core facts:

- `generated_at`
- report window
- snapshot due/streak/cost/maturity facts
- all displayed tag mastery rows and their score/band/trend/evidence/stale values
- recap totals and trend directions
- skipped-data counts
- guardrails

Markdown MAY omit machine-only field names when the meaning is clear.

## Privacy Rules

Markdown MUST NOT contain:

- raw learner answers
- mistake span text
- full feedback prose
- complete event logs
- host adapter metadata
- graphical dashboard language

## Determinism Rules

With identical `ProgressReport` JSON, markdown rendering MUST be byte-stable.

Golden tests MUST cover:

- no-data report
- tied mastery ordering
- stale tag evidence
- improving/steady/worsening/insufficient trends
- long tag or hint wrapping
- skipped duplicate/invalid data notices
