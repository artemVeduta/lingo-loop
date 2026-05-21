# Phase 0 Research: Richer Feedback & Progress

## Decision: Keep the existing synchronous Python stack and add no runtime dependencies

**Rationale**: The feature requires bounded aggregation, score calculation, ASCII rendering, markdown string output, and JSON schema validation. Existing Python 3.12+, Pydantic, Click, stdlib `sqlite3`, and stdlib text/math tools cover that surface. Adding a table, chart, dataframe, markdown, or analytics library would violate the text-only scope and add dependency weight without solving a current requirement.

**Alternatives considered**:

- Add Rich/Textual for terminal tables. Rejected because output must remain host-independent text/markdown and the current renderer pattern uses plain strings.
- Add pandas or a statistics dependency. Rejected because the data windows are capped at 30 sessions for learner-facing progress and simple one-pass aggregation is enough.
- Add a markdown library. Rejected because the project emits markdown; it does not parse or transform markdown.

## Decision: Use existing SQLite state with narrow read methods and progress indexes

**Rationale**: Required inputs already exist locally: `session_summaries` defines completed analyzed sessions, `mistake_events` defines tagged mistakes and severity/confidence, `vocabulary_reviews` defines review outcomes/quality, `vocabulary_items` defines tags and due state, `answer_events` supports practice volume and streak, and `cost_events` supports month-to-date costs. Repository methods should return bounded, typed progress evidence; scoring stays in core. Read indexes are justified by the one-year-history performance gate.

The existing `due_count(now)` counts all vocabulary items with `due_at <= now`, which can include new cards. Phase 4 due-review summary should name that meaning explicitly or add a state-aware repository read for review backlog so recap wording does not overstate completed review debt.

**Alternatives considered**:

- Persist per-tag mastery snapshots. Rejected because reports are on-demand derived artifacts and persistence would create another source of truth.
- Store progress in YAML. Rejected because YAML is reserved for human-editable profile/preferences.
- Add a new analytics database/table. Rejected because existing local transactional state can represent the required facts.

## Decision: Define a request model for window size and generated-at

**Rationale**: `generated_at` must be required in exports but deterministic tests need a stable value. A `ProgressReportRequest` can accept `window_size` and optional `generated_at`; CLI defaults to current UTC when absent, while tests and scripts can inject a timestamp. Window validation belongs in Pydantic to keep CLI and skills consistent.

**Alternatives considered**:

- Use global time inside renderers. Rejected because markdown/JSON round-trip tests would not be byte-stable.
- Use command-line flags only. Rejected because the project already passes JSON payloads through Click commands and contract tests can validate one object shape.
- Require `generated_at` from every CLI caller. Rejected because default CLI use should stay ergonomic; the report still contains a required generated value.

## Decision: Use a canonical JSON report and render markdown from it

**Rationale**: JSON is the machine contract for validation and round trips. Markdown is a deterministic view of the same validated model. Rendering markdown from `ProgressReport` keeps facts equivalent and prevents duplicated aggregation logic.

**Alternatives considered**:

- Build markdown and JSON independently. Rejected because it risks mismatched facts.
- Make markdown the canonical export and parse it for tests. Rejected because markdown is human-oriented and weaker as a contract.
- Write reports to files by default. Rejected because the existing CLI emits stdout JSON/markdown for host and shell use.

## Decision: Mastery score uses four normalized components with fixed weights

**Rationale**: The spec fixes weights: correctness/review outcomes 45%, mistake severity 30%, recency 15%, and evidence confidence 10%. Each component should produce a 0-100 value and the final score should be clamped/rounded to 0-100. Evidence comes from safe aggregates only:

- Review/correctness component: vocabulary review quality and verdicts, plus completed session/mistake presence when a tag appears outside vocab reviews.
- Severity component: lower aggregate mistake severity improves score; high severity penalizes more than medium or low.
- Recency component: evidence inside the active window scores higher; tags with only historical evidence are stale.
- Confidence component: higher-confidence evidence and enough supporting events improve trust in the score.

**Alternatives considered**:

- Use only weak-tag frequency. Rejected because it ignores successful reviews and recency.
- Use only vocabulary review quality. Rejected because writing mistakes are first-class learning evidence.
- Use an LLM-generated mastery judgment. Rejected because the feature requires deterministic golden-tested progress views.

## Decision: Reuse existing normalized tag vocabulary and Phase 3 weak-tag semantics

**Rationale**: `normalize_tag` in `vocab.py` already centralizes tag identity for vocabulary and weak-tag targeting. Progress should call the same normalization helper and rely on the existing `ErrorTag` vocabulary where applicable so practice targeting and progress reports do not disagree.

**Alternatives considered**:

- Add a separate progress tag taxonomy. Rejected because it would duplicate concepts and violate DRY.
- Preserve raw tag spelling in calculations. Rejected because stable ordering and tie handling require normalized identity.

## Decision: Deduplicate sessions before windowing and report skips

**Rationale**: The learner-facing windows are based on completed valid analyzed sessions. If duplicate records exist for a `session_id`, only the latest valid analyzed record counts, and skipped duplicates are reported. Existing SQLite schema has `session_summaries.session_id UNIQUE` and current writes use `INSERT OR REPLACE`, so already-replaced duplicate summaries cannot be recovered at report time. The implementation should still make canonicalization deterministic for any duplicate rows supplied by legacy/import paths or pure tests, and should report zero duplicate skips for normal current storage when no duplicate rows are visible.

**Alternatives considered**:

- Let duplicates count as extra practice. Rejected because it inflates trend and mastery evidence.
- Fail the progress report on duplicates. Rejected because the feature requires robust skip reporting.
- Silently ignore duplicates. Rejected because FR-012 requires skipped data reporting.
- Add a persisted duplicate ledger. Rejected for Phase 4 because reports are derived artifacts and current storage already collapses duplicate summaries.

## Decision: Trend direction compares earlier-half and later-half averages with metric polarity

**Rationale**: The spec defines improving/steady/worsening by earlier-half vs later-half averages and under 10% relative change as steady. Metrics need explicit polarity: accuracy, completed reviews, and practice volume improve when values rise; mistake severity totals, due backlog, and weak-tag count improve when values fall. Fewer than two valid sessions yields insufficient data.

**Alternatives considered**:

- Linear regression. Rejected because it is more complex and not requested.
- First-vs-last comparison. Rejected because it is too sensitive to single-session outliers.
- Unpolarized trend labels. Rejected because lower values are better for backlog and severity.

## Decision: ASCII sparklines use fixed buckets and independent scaling per metric

**Rationale**: The required buckets are `.:-=+*#%@`, one character per valid session, plus min/max labels. Scaling per selected window keeps the visual meaningful for small local ranges. Constant series should produce a stable middle bucket and identical min/max labels rather than divide by zero.

**Alternatives considered**:

- Unicode sparklines. Rejected because output must be ASCII-only.
- Chart images or web charts. Rejected by scope.
- Global scaling across all history. Rejected because the recap is explicitly a selected last-N-session window.

## Decision: Markdown targets terminal readability, not table perfection

**Rationale**: The renderer should keep lines around 100 columns where possible, use short headings, wrap long hints/tag names, and avoid nested rich formatting. Markdown should contain the same core facts as JSON: report window, generated-at, snapshot, tag mastery, recap, due-review summary, skip notices, and guardrails.

**Alternatives considered**:

- Fixed-width tables for every section. Rejected because long tag names and hints can wrap badly in narrow terminals.
- Full prose narrative only. Rejected because learners need scannable weakest-tag rankings and trend facts.

## Decision: Privacy filtering is aggregate-only by construction

**Rationale**: Repository reads for progress should not return `learner_answer`, `span_text`, or full `feedback_envelope_json`. The report includes counts, tags, severity totals, quality aggregates, safe last-session summaries, and practice hints. Contract tests should assert banned raw fields and host metadata do not appear in serialized report or markdown.

**Alternatives considered**:

- Fetch full events and filter in renderer. Rejected because raw private data would cross too many layers.
- Include full feedback text for context. Rejected by FR-019 and export scope.

## Decision: Add only read-performance indexes as migration work

**Rationale**: A one-year daily history with dense mistakes/reviews should not rely on table scans over all event rows. Indexes on session/time access paths support bounded progress reads without changing data ownership or adding new persisted concepts.

**Alternatives considered**:

- No migration. Rejected as risky against the explicit <5 second exit gate.
- Add materialized aggregate tables. Rejected as overkill for bounded windows and single-user scale.
