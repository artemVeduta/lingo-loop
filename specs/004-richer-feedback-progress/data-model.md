# Data Model: Richer Feedback & Progress

## Overview

All models are derived from local state and represented as Pydantic contracts in `src/language_tutor/schemas.py`. SQLite remains the source of truth for raw learning events. Reports are emitted on demand and are not persisted.

## Entity: ProgressReportRequest

**Purpose**: Request options for generating a progress report.

**Fields**:

- `window_size`: integer, default `10`, minimum `1`, maximum `30`.
- `generated_at`: optional UTC ISO timestamp supplied by caller/tests; CLI uses current UTC when omitted.
- `format`: optional literal `json` or `markdown` if a direct export selector is needed; default `json`.

**Validation**:

- `window_size` must be 1-30.
- `generated_at`, when provided, must parse as timezone-aware UTC or be normalized to UTC.
- Unsupported formats fail validation and do not fall back silently.

## Entity: ReportWindow

**Purpose**: Describes the completed-session window used for recap and export context.

**Fields**:

- `requested_session_count`: requested last-N completed sessions.
- `actual_session_count`: valid completed sessions used.
- `mastery_session_count`: valid completed sessions used for per-tag mastery, capped at 30.
- `start_date`: first valid session date in the recap window, nullable when empty.
- `end_date`: last valid session date in the recap window, nullable when empty.
- `active_mastery_window`: textual description such as `last_30_completed_sessions`.

**Validation**:

- `actual_session_count` cannot exceed `requested_session_count`.
- Dates are omitted when no valid completed sessions exist.

## Entity: ProgressSnapshot

**Purpose**: Current high-level learner state.

**Fields**:

- `streak_days`: current streak from answer event dates.
- `due_count`: current due vocabulary count.
- `maturity`: vocabulary item counts by state.
- `top_weak_patterns`: normalized weak tags, maximum 5.
- `month_to_date_estimated_usd`: nullable float.
- `cost_status`: `available`, `partial`, or `unavailable`.
- `next_action`: concise learner-safe next action.

**Validation**:

- Counts are non-negative.
- Cost is omitted or non-negative.
- Raw answers, full feedback prose, and host metadata are not fields.

## Entity: TagMastery

**Purpose**: Learner-facing mastery row for one normalized tag.

**Fields**:

- `tag`: normalized tag string.
- `score`: integer 0-100.
- `band`: `emerging`, `developing`, `steady`, or `strong`.
- `evidence_count`: non-negative count of safe supporting evidence.
- `last_seen_at`: latest evidence timestamp, nullable.
- `last_seen_age_days`: non-negative integer, nullable when no timestamp exists.
- `stale`: boolean indicating no evidence in the active mastery window.
- `trend`: `improving`, `steady`, `worsening`, or `insufficient_data`.
- `next_practice_hint`: concise generated hint based on band/trend/staleness.
- `score_breakdown`: four component scores for correctness/review outcomes, severity, recency, and confidence.

**Relationships**:

- Derived from `MasteryEvidence` rows grouped by normalized tag.
- Reuses `normalize_tag` and existing weak-tag signal meaning.
- Candidate tags come only from learner-safe historical evidence in completed vocabulary reviews, tagged mistake events, or completed analyzed session summaries. Vocabulary-card tags without completed review, mistake, or summary evidence are not mastery rows yet.

**Validation**:

- Score is `round(correctness_review * 0.45 + severity * 0.30 + recency * 0.15 + evidence_confidence * 0.10)`, clamped to 0-100 after each component is normalized to 0-100.
- Correctness/review maps `correct` or review quality 4-5 to 100, `partial` or quality 3 to 60, and `needs_review`, `missed`, `unanswered`, or quality 0-2 to 0; missing active-window correctness/review evidence uses 50.
- Severity is `100 - average_penalty` over active-window mistake evidence, with penalties `none=0`, `low=25`, `medium=60`, and `high=100`; tags with no active mistake evidence but other active evidence use 100, while stale tags use 50 before recency weighting.
- Recency is 100 for evidence in the most recent completed valid session and linearly decays to 0 at the oldest session in the 30-session mastery window; stale tags use 0.
- Evidence confidence averages explicit confidence values `high=100`, `medium=70`, `low=40`, uses 70 for review and summary evidence without confidence, then multiplies by `min(1, evidence_count / 5)`.
- Score maps to band: 0-49 emerging, 50-74 developing, 75-89 steady, 90-100 strong.
- Sorting order is score ascending, trend priority with worsening before steady/improving, most recent evidence descending, normalized tag ascending.
- Stale tags have historical evidence but no active-window evidence.
- Raw answer text and full feedback text are never included.

## Entity: MasteryEvidence

**Purpose**: Internal aggregate input for mastery scoring.

**Fields**:

- `session_id`: canonical completed session ID.
- `tag`: normalized tag.
- `observed_at`: evidence timestamp.
- `source`: `vocabulary_review`, `mistake_event`, or `session_summary`.
- `review_quality`: nullable 0-5.
- `verdict`: nullable review/answer verdict.
- `severity`: nullable `none`, `low`, `medium`, or `high`.
- `confidence`: nullable `low`, `medium`, or `high`.

**Relationships**:

- Vocabulary review evidence joins `vocabulary_reviews` to `vocabulary_items.tags_json`.
- Mistake evidence reads `mistake_events.tag`, `severity`, and `confidence`.
- Session summary evidence can use `weak_tags_json` and safe summaries without raw prose.

**Validation**:

- Repository reads should return only fields needed for aggregate scoring.
- Duplicate session IDs are canonicalized before evidence is windowed.

## Entity: RecentSessionRecap

**Purpose**: Summary of selected last-N valid completed sessions.

**Fields**:

- `actual_session_count`: number of valid sessions used.
- `date_range`: start/end dates or unavailable.
- `practice_totals`: answer/review/writing counts by safe category.
- `due_review_completion`: completed reviews and current due count.
- `mistake_severity_totals`: low/medium/high totals.
- `weak_tag_changes`: tags newly weak, repeated weak, resolved weak, or unavailable.
- `latest_session_summary`: learner-safe latest summary when available.
- `trends`: list of `TextTrend` models.
- `skipped_data`: list of `SkippedDataNotice` models relevant to recap.

**Validation**:

- Fewer than two valid sessions yields trend direction `insufficient_data`.
- Incomplete, invalid, unanalyzed, and duplicate records are excluded from calculations and reported.

## Entity: TextTrend

**Purpose**: ASCII-only trend for a metric across the selected valid sessions.

**Fields**:

- `metric`: stable metric name.
- `label`: learner-facing label.
- `polarity`: `higher_is_better` or `lower_is_better`.
- `direction`: `improving`, `steady`, `worsening`, or `insufficient_data`.
- `sparkline`: ASCII string using only `.:-=+*#%@`.
- `min_label`: plain text min label.
- `max_label`: plain text max label.
- `values_count`: number of values represented.

**Validation**:

- Sparkline length equals `values_count`.
- Bucket alphabet is exactly `.:-=+*#%@`.
- Constant series uses a deterministic bucket and still emits min/max labels.
- Direction compares the first `floor(n/2)` values with the last `floor(n/2)` values, ignoring the middle value for direction when `n` is odd while keeping it in the sparkline.
- Direction treats under 10% relative change as steady, both-zero averages as steady, and zero-to-nonzero averages as beyond the threshold with improving/worsening determined by metric polarity.

## Entity: DueReviewSummary

**Purpose**: Current and recent due-review facts for the report.

**Fields**:

- `due_count`: current due vocabulary count.
- `completed_in_window`: completed reviews in recap window.
- `low_quality_in_window`: reviews with quality below 3 in recap window.
- `maturity`: vocabulary item state counts.

**Validation**:

- Counts are non-negative.
- `due_count` must either be state-aware for review backlog or clearly documented as all vocabulary available now, including new cards if that existing repository meaning is preserved.
- Missing older-state fields are represented as unavailable, not fatal errors.

## Entity: SkippedDataNotice

**Purpose**: Learner-safe skip reason and count.

**Fields**:

- `reason`: `duplicate_session`, `invalid_session`, `interrupted_session`, `missing_analysis`, `stale_tag_evidence`, or `unavailable_optional_field`.
- `count`: non-negative integer.
- `scope`: `mastery`, `recap`, `export`, or `snapshot`.
- `message`: concise learner-safe text.

**Validation**:

- No raw session records, answers, feedback prose, or host metadata.
- Zero-count notices may be omitted.
- Duplicate-summary notices are emitted only for duplicate rows visible to the canonicalization layer. Current SQLite writes normally collapse duplicates before report generation.

## Entity: ProgressReport

**Purpose**: Canonical JSON export and source for markdown rendering.

**Fields**:

- `schema_version`: integer, starts at 1.
- `generated_at`: required UTC ISO timestamp.
- `report_window`: `ReportWindow`.
- `snapshot`: `ProgressSnapshot`.
- `tag_mastery`: list of `TagMastery`.
- `recent_recap`: `RecentSessionRecap`.
- `due_review_summary`: `DueReviewSummary`.
- `skipped_data`: list of `SkippedDataNotice`.
- `scope_guardrails`: list of strings naming excluded surfaces and privacy boundaries.

**Validation**:

- JSON round-trip preserves all required fields.
- Markdown and JSON exports contain equivalent core facts.
- Report serialization contains no raw learner answers, full feedback prose, complete event logs, or host metadata.

## Entity: ProgressMarkdownExport

**Purpose**: Renderer output for terminal-printable markdown.

**Fields**:

- `content_type`: literal `text/markdown`.
- `generated_at`: UTC ISO timestamp copied from `ProgressReport`.
- `report_window`: copy or summary of `ReportWindow`.
- `markdown`: rendered report text.

**Validation**:

- Markdown is rendered from a validated `ProgressReport`.
- Output is ASCII-safe for sparkline sections.
- Lines should target 100 columns where practical and wrap long tags/hints.

## State Transitions

Progress entities do not introduce persisted state transitions. The runtime flow is:

1. `ProgressReportRequest` is parsed by CLI.
2. Repository reads canonical completed sessions and safe evidence rows.
3. Core aggregates snapshot, mastery, recap, trends, and skipped-data notices.
4. `ProgressReport` is validated and emitted as JSON or passed to markdown renderer.
5. `ProgressMarkdownExport` is validated and emitted when markdown is requested.

## Migration Note

No stored progress facts are added. Migration `003_progress_indexes.sql` is planned for read-performance indexes only. If implementation proves existing indexes sufficient for the one-year fixture, the migration can be reduced or omitted during tasks with the rationale recorded.
