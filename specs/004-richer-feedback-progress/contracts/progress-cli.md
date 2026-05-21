# Contract: Progress CLI

## Commands

### `tutor progress --json [payload]`

Generates the canonical progress report as JSON. Omitting `payload` is valid and uses defaults.

**Request payload**:

```json
{
  "window_size": 10,
  "generated_at": "2026-05-21T12:00:00Z",
  "format": "json"
}
```

**Defaults**:

- `window_size`: `10`
- `generated_at`: current UTC timestamp from the CLI clock
- `format`: `json`

**Validation**:

- `window_size` must be between 1 and 30.
- `generated_at`, when supplied, must be a UTC ISO timestamp or normalizable to UTC.
- `format` must be `json` or `markdown` if direct format selection is implemented.
- Invalid payloads return the existing structured error envelope style.

**Response for JSON format**:

Returns a `ProgressReport` JSON object as defined in `progress-json-report.md`.

### `tutor render progress-report --json <payload>`

Renders a validated `ProgressReport` JSON object into terminal-printable markdown.

**Request payload**: a complete `ProgressReport`.

**Response**:

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

If direct markdown format is implemented on `tutor progress`, it MUST produce the same markdown contract by internally generating a `ProgressReport` and passing it through the same renderer.

## Backward Compatibility

The existing no-argument command remains valid:

```bash
rtk tutor progress --json
```

The response becomes richer but must retain core snapshot fields or obvious replacements for:

- streak
- due count
- weak patterns
- maturity counts
- latest recap or no-data message
- month-to-date cost status
- next action

## Privacy Rules

The CLI response MUST NOT include:

- raw learner answers
- mistake span text
- full feedback prose
- full event logs
- host adapter metadata
- local filesystem paths except documented config/report paths if explicitly requested in future

## Determinism Rules

With identical SQLite state, request payload, and generated-at value, repeated CLI runs MUST produce byte-stable JSON after sorted-key emission.

## Error Cases

- Invalid JSON payload: `invalid_json`.
- Unsupported format: `invalid_progress_format`.
- Window outside 1-30: Pydantic validation error mapped to a progress request error.
- No learner history: valid report with no-data snapshot/recap, not an error.
- Older state missing optional cost/summary/tag fields: valid report with unavailable notices, not an error.
