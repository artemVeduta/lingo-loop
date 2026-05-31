---
name: tutor-progress
description: Use when learner wants progress, exportable progress reports, next focus, due counts, weak patterns, maturity, local status, or cost status.
---

Use this when learner wants progress, next focus, due counts, weak patterns,
local status, cost status, or a markdown/JSON progress export.

Run only `tutor`. No SessionStart/SessionEnd hooks; the agent owns lifecycle.

**Lifecycle (do in this order):**

1. **First stateful step of the conversation:** if no `session_id` is known, run
   `tutor session-start --json '{"host":"<host>"}'` BEFORE any other
   `tutor` call (including `progress`). Capture `session_id` from the
   response and thread it into every later call this conversation.
2. **Run progress:** `tutor progress --json` (does not require `session_id`).
   Options: `tutor progress --json '{"window_size":10,"generated_at":"..."}'`;
   markdown export: `tutor progress --json '{"format":"markdown"}'`;
   render existing JSON: `tutor render progress-report --json '<ProgressReport JSON>'`.
3. **Immediately after `progress --json` returns and BEFORE showing the report
   to the learner**, call:
   `tutor checkpoint --json '{"session_id":"sess_...","modality":"progress","step_kind":"progress_shown","summary":"<short>"}'`.
   Only then present the report.
4. **Do NOT call session-close or session-end at the end of normal flows.**
   `tutor session-close --json '{"session_id":"sess_...","analysis":{...},"costs":{...}}'`
   and the legacy `tutor session-end --json '<payload>'` run ONLY when the
   learner explicitly asks to wrap up the session. Both payloads MUST embed the
   active `session_id`. No automatic close, no close after the last report.
5. Diagnostics (no session_id needed): `tutor doctor --json`.

Do not hand-format progress markdown, recompute scoring, invent examples, or read
raw storage. The CLI owns pedagogy, scoring, aggregation, validation, and rendering.

Weak patterns come from active weak-tag signals over recent completed analyzed
sessions. Exports are aggregate-only. Show tag names, bands, counts, trends,
guardrails, and next actions from CLI output only; do not expose raw answers,
mistake spans, prompts, full feedback prose, event logs, host metadata, or local
paths.
Never include learner-specific examples unless CLI output contains sanitized
aggregate examples explicitly intended for export.

## Payload schemas (build every request against these)

Read the referenced `schemas/*.schema.json` before constructing the payload; do not guess fields.

- `session-start` input: `{"host":"claude|codex|openclaw|hermes","host_conversation_id"?:str}` → output `schemas/boot_result.schema.json`.
- `progress` input → `schemas/progress_request.schema.json` → output `schemas/progress_report.schema.json` (markdown export: `schemas/progress_markdown_export.schema.json`).
- `checkpoint` input → `schemas/checkpoint.schema.json`. Required: `session_id`, `modality` (`progress`), `step_kind` (`progress_shown`), `summary`. `state` (optional) takes `prompt_ref`, `step_index`, `total_steps`, `modality_hint`, `labels` (≤16).
- `render progress-report` input → `schemas/progress_report.schema.json`.
- `session-close` / `session-end` input (`SessionEndInput`): `{"session_id":"sess_...","analysis"?:{...},"costs"?:[...]}`; `analysis` → `schemas/session_analysis.schema.json`. Explicit learner request only.
