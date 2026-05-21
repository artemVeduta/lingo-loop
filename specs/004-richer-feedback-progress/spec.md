# Feature Specification: Richer Feedback & Progress

**Feature Branch**: `004-richer-feedback-progress`

**Created**: 2026-05-21

**Status**: Draft

**Input**: User description: "Phase 4 from docs/ROADMAP.md: Richer Feedback & Progress. Renderer / analysis surface. No host dependency. Text/markdown only; no charts, GUI, web view, or rich analytics dashboard. Add per-tag mastery view, text trend / ASCII sparkline with last-N-session recap, and exportable markdown / JSON report. Exit gate: deterministic golden-tested progress views, export round-trips, text/markdown-only output, and progress view under 5 seconds on one year of daily history."

## Clarifications

### Session 2026-05-21

- Q: How should per-tag mastery score combine evidence signals? → A: Weighted score: correctness/review outcomes 45%, mistake severity 30%, recency 15%, evidence confidence 10%.
- Q: How should recap trend direction classify improving, steady, or worsening? → A: Earlier-half average vs later-half average; under 10% relative change is steady.
- Q: How should duplicated session records be handled in mastery and recap calculations? → A: Count each `session_id` once; keep the latest valid analyzed record and report skipped duplicates.
- Q: How should export `generated_at` be set for deterministic markdown and JSON reports? → A: Use required UTC ISO timestamp from request/clock; CLI defaults to current UTC.
- Q: How should ASCII sparklines encode trend values? → A: Buckets `.:-=+*#%@`, one per valid session, plus min/max labels.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Review Per-Tag Mastery (Priority: P1)

A learner checks progress and sees which grammar, vocabulary, and writing tags are strong, developing, or weak, with enough evidence to decide what to practice next.

**Why this priority**: Phase 4 must convert existing learning history into an actionable progress surface, not just a list of due cards or weak patterns.

**Independent Test**: Can be tested with completed sessions, mistake events, and vocabulary reviews across several tags, then confirming the progress view ranks tags, shows mastery bands, and identifies practice focus without using any graphical surface.

**Acceptance Scenarios**:

1. **Given** a learner has repeated activity for multiple tags, **When** the learner opens progress, **Then** each active tag appears with a mastery score, mastery band, evidence count, recency indicator, trend direction, and next-practice hint.
2. **Given** a learner has tags with no recent activity, **When** mastery is shown, **Then** those tags are clearly separated from active tags or marked as stale instead of being treated as strong.
3. **Given** a learner has no completed sessions or reviews, **When** progress is opened, **Then** the view explains that progress data is not available yet and suggests running vocabulary or writing practice.
4. **Given** two tags have identical mastery evidence, **When** the view ranks tags, **Then** the order is deterministic and stable.

---

### User Story 2 - Understand Recent Trend And Recap (Priority: P2)

A learner reviews the last few sessions and quickly understands whether practice volume, accuracy, weak patterns, and review load are improving or getting worse.

**Why this priority**: Trend and recap output gives the learner short-term feedback without turning the product into a dashboard.

**Independent Test**: Can be tested with a fixed set of completed session summaries over a selected session window and confirming the recap totals, trend directions, and ASCII sparklines are deterministic.

**Acceptance Scenarios**:

1. **Given** the learner has at least two completed sessions, **When** the learner requests a recent recap, **Then** the output shows the selected session count, date range, practice totals, weak-tag changes, and a text trend for core progress signals.
2. **Given** the learner has fewer completed sessions than the selected recap window, **When** the recap is generated, **Then** it uses all available completed sessions and labels the actual count.
3. **Given** one or more sessions are interrupted, invalid, or missing analysis, **When** the recap is generated, **Then** those sessions do not corrupt trend calculations and the output states that incomplete data was skipped.
4. **Given** identical learner history and the same selected window, **When** the recap is generated repeatedly, **Then** the output is byte-stable apart from explicitly requested export timestamps.

---

### User Story 3 - Export A Shareable Progress Report (Priority: P2)

A learner exports the same progress information as a terminal-printable report for personal review, issue reports, or offline analysis.

**Why this priority**: Export makes progress portable while keeping the project local-first and text-only.

**Independent Test**: Can be tested by generating markdown and JSON reports from the same learner history, validating that both contain equivalent report facts, and reloading the JSON report without losing required fields.

**Acceptance Scenarios**:

1. **Given** a learner has progress history, **When** the learner exports a markdown report, **Then** the report contains the progress snapshot, per-tag mastery, recent recap, due-review summary, and report window in terminal-printable markdown.
2. **Given** the same learner history, **When** the learner exports a JSON report, **Then** it contains the same core facts as the markdown report in a machine-readable structure.
3. **Given** a report is exported, **When** it is read back by validation tooling, **Then** all required sections and fields round-trip without mismatch.
4. **Given** private raw answers or full feedback text exist in history, **When** any report is exported, **Then** the report includes only aggregated learning metrics and learner-safe summaries.

### Edge Cases

- No sessions, no vocabulary reviews, and no mistake events exist yet.
- Only one completed session exists, so trend direction cannot be inferred.
- The selected recap window is larger than available completed sessions.
- Some sessions are interrupted, invalid, missing analysis, or duplicated.
- Tags exist on vocabulary cards but have no mistakes or recent reviews.
- Tags appear only in writing mistakes, only in vocabulary reviews, or both.
- Multiple tags tie on mastery score, trend, recency, and evidence count.
- Very long tag names, language names, or practice hints would wrap in a narrow terminal.
- A learner has one year of daily history with dense mistakes and reviews.
- Export is requested when no progress data exists.
- Report data contains costs, due counts, or summaries that are absent in older local state.
- A requested output format is not markdown or JSON.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST provide a per-tag mastery view for every active tag with learner history in completed sessions, mistake events, or vocabulary reviews.
- **FR-002**: System MUST compute a learner-facing mastery score from 0 to 100 for each active tag using the following weighted signals from local learning history: recent correctness and review outcomes 45%, mistake severity 30%, recency 15%, and evidence confidence 10%.
- **FR-003**: System MUST map each mastery score to a visible mastery band: emerging for 0-49, developing for 50-74, steady for 75-89, and strong for 90-100.
- **FR-004**: System MUST show, for each displayed tag, the tag name, mastery score, mastery band, evidence count, last-seen age, trend direction, and a concise next-practice hint.
- **FR-005**: System MUST rank displayed tags by lowest mastery first, then worsening trend, then most recent evidence, then normalized tag name so identical history produces stable ordering.
- **FR-006**: System MUST mark tags as stale when their latest evidence is older than the active progress window, rather than treating missing recent evidence as high mastery.
- **FR-007**: System MUST reuse the existing normalized tag vocabulary and weak-tag signal meaning so progress and practice targeting do not disagree about tag identity.
- **FR-008**: System MUST provide a recent-session recap for a selected last-N completed-session window, defaulting to the last 10 completed sessions and allowing values from 1 to 30.
- **FR-009**: System MUST include in the recent-session recap the actual session count, date range, practice totals, due-review completion totals, mistake severity totals, weak-tag changes, and learner-safe last-session summary when available.
- **FR-010**: System MUST render text trends using ASCII-only sparkline characters and plain labels; each sparkline MUST use buckets `.:-=+*#%@`, one character per valid session, plus min/max labels. Graphical charts, GUI dashboards, and web views are not allowed.
- **FR-011**: System MUST label trend direction as improving, steady, worsening, or insufficient data by comparing earlier-half and later-half averages within the selected completed-session window, treating relative changes under 10% as steady.
- **FR-012**: System MUST skip interrupted, invalid, unanalyzed, and duplicate session records in mastery and trend calculations while reporting how many records were skipped.
- **FR-013**: System MUST preserve existing progress information: streak, due-review counts, top weak patterns, and month-to-date cost when those data are available.
- **FR-014**: System MUST provide an exportable progress report in markdown format.
- **FR-015**: System MUST provide an exportable progress report in JSON format.
- **FR-016**: System MUST ensure markdown and JSON exports contain equivalent core report facts: report window, generated-at value, progress snapshot, per-tag mastery, recent recap, due-review summary, skipped-data counts, and scope guardrails.
- **FR-017**: System MUST allow exported JSON reports to be validated and read back with no required-field loss.
- **FR-018**: System MUST keep all progress views and exports terminal-printable, with tables and lines designed for a 100-column terminal; when a tag, hint, or summary cannot fit, renderers MUST wrap at word boundaries with deterministic indentation and MUST truncate only non-essential prose with an explicit ellipsis marker.
- **FR-019**: System MUST avoid raw learner answer text, full feedback prose, complete event logs, and host-specific metadata in progress views and exported reports.
- **FR-020**: System MUST handle older local state that lacks optional cost, summary, or tag evidence fields by showing omitted or unavailable values instead of failing the whole progress view.
- **FR-021**: System MUST complete default progress generation in under 5 seconds on a fixture representing one year of daily completed sessions with dense mistakes and reviews.
- **FR-022**: System MUST keep Phase 4 host-independent and local-first.
- **FR-023**: System MUST NOT add graphical charts, rich analytics dashboards, GUI screens, web views, audio, new exercise modalities, new hosts, gamification, cloud sync, multi-user behavior, or alternate scheduling algorithms.

### Requirement Details

- Active progress window means the selected recent-session window for recaps and the most recent 30 completed sessions for per-tag mastery. If fewer than 30 completed sessions exist, all valid completed sessions are considered.
- The mastery candidate tag set includes normalized tags with learner-safe historical evidence from completed vocabulary reviews, tagged mistake events, or completed analyzed session summaries. Tags that exist only on vocabulary cards with no completed review, mistake, or summary evidence are not mastery rows yet.
- Stale tag evidence means a tag has historical evidence but no evidence in the active progress window.
- Evidence count includes aggregated learner-safe events that can support a mastery judgment: completed vocabulary reviews, tagged mistakes, and completed session summaries that reference the tag. It does not expose raw answers.
- Mastery component scores are normalized to 0-100 before weighting, then combined as `round(correctness_review * 0.45 + severity * 0.30 + recency * 0.15 + evidence_confidence * 0.10)` and clamped to 0-100.
- Correctness/review score averages safe outcome points from active-window completed evidence: `correct` or vocabulary review quality 4-5 = 100, `partial` or quality 3 = 60, `needs_review`, `missed`, `unanswered`, or quality 0-2 = 0. Tags with no active-window correctness/review evidence use 50 so the confidence and recency components carry the uncertainty.
- Severity score is `100 - average_penalty` across active-window tagged mistakes, with penalties `none=0`, `low=25`, `medium=60`, and `high=100`. Tags with no active-window mistake evidence but other active evidence use 100; stale tags use 50 before the recency penalty.
- Recency score is 100 for evidence in the most recent completed valid session and decays linearly to 0 at the oldest session in the 30-session mastery window; stale tags use 0.
- Evidence confidence score averages confidence values `high=100`, `medium=70`, `low=40`, using 70 for vocabulary-review and session-summary evidence without explicit confidence, then multiplies by `min(1, evidence_count / 5)` so sparse evidence lowers confidence.
- Duplicate session records are resolved by `session_id`: count each `session_id` once, prefer the latest valid analyzed record, and include skipped duplicates in skipped-data notices.
- Trend direction is insufficient data when fewer than two valid completed sessions exist in the selected recap window.
- Trend direction compares the first `floor(n/2)` values with the last `floor(n/2)` values; for odd window sizes, the middle value is ignored for direction but remains in the sparkline. If both averages are 0, direction is steady. If the earlier average is 0 and the later average is nonzero, the change is treated as beyond the 10% threshold.
- Trend direction treats higher accuracy, completed review count, and practice volume as improving when they rise; it treats mistake severity totals, due-review backlog, and weak-tag count as improving when they fall.
- ASCII sparkline output uses only printable ASCII characters, scales each selected window independently into buckets `.:-=+*#%@`, shows one character per valid session, includes min/max labels, and must remain meaningful when copied into plain text.
- Markdown tables and plain text sections wrap long tag names, language names, hints, and learner-safe summaries deterministically for a 100-column terminal. Essential identifiers, counts, scores, trend labels, and generated-at values MUST NOT be truncated; only explanatory prose may be shortened, and shortened text MUST end with `...`.
- Markdown export is intended for human reading. JSON export is intended for validation, automation, and future tooling. Both describe the same report, but markdown may omit machine-only field names when the meaning is clear.
- Exported reports MUST include a required `generated_at` UTC ISO timestamp supplied by the request or injected clock; CLI exports default it to the current UTC time.
- Report generation is on demand. This feature does not add background jobs, notifications, telemetry, or automatic sharing.

### Key Entities *(include if feature involves data)*

- **Tag Mastery**: A learner-facing progress summary for one normalized tag. It includes score, band, evidence count, recency, trend direction, and next-practice hint.
- **Progress Snapshot**: The current high-level learning state, including streak, due-review count, top weak patterns, cost when available, and skipped-data notices.
- **Recent Session Recap**: A summary of the selected completed-session window, including session count, date range, practice totals, weak-tag changes, severity totals, and text trends.
- **Text Trend**: An ASCII-only representation of directional change across the selected session window, encoded as bucket characters with min/max labels.
- **Progress Report**: An exportable representation of the progress snapshot, tag mastery, recent recap, report window, required `generated_at` timestamp, and validation metadata.
- **Skipped Data Notice**: A learner-safe count and reason summary for records excluded because they were interrupted, invalid, duplicated, missing analysis, or too old for the selected window.

## Constitution Alignment *(mandatory)*

- **Affected Layers**: Progress aggregation, analysis summary reuse, deterministic renderers, local repositories, progress CLI output, export contract, schema mirrors, and the existing `tutor-progress` skill surface if invocation text must change. Host adapters remain out of scope.
- **Data Ownership**: Existing local transactional state owns sessions, reviews, mistakes, costs, due counts, and derived progress inputs. YAML remains limited to human-editable profile and preferences. Exported reports are derived artifacts, not a new source of truth.
- **Contract Surfaces**: Tag mastery report, recent-session recap, progress report JSON, markdown report structure, command result JSON, schema mirrors, and narrow repository reads for progress aggregation. A migration is required only if existing local state cannot represent required aggregated inputs.
- **Required Validation**: Unit tests for mastery scoring, stale evidence, tie ordering, trend labels, skipped-data handling, and report equivalence; golden tests for progress markdown and ASCII trend rendering; contract tests for JSON export and command output; integration tests for no-data, partial-data, and one-year-history progress flows; performance verification for one year of daily history; migration tests only if storage changes.
- **Skill Creation**: No new skill is created. If `skills/tutor-progress/SKILL.md` or any other project `SKILL.md` is edited, the work must use the local writing-skills helper, external skill-authoring references required by the active spec, and subagent RED/GREEN/REFACTOR pressure evidence before shipping.
- **Scope Guardrails**: Phase 4 is limited to text/markdown progress and feedback surfaces. It excludes graphical dashboards, charts beyond ASCII text trends, GUI or web views, raw event-log exports, host adapter work, new modalities, new scheduling algorithms, cloud sync, gamification, multi-user behavior, and unrelated evaluator changes.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: In deterministic fixtures with at least 12 tags and mixed review/mistake history, 100% of active tags appear with mastery score, band, evidence count, recency, trend direction, and next-practice hint.
- **SC-002**: In fixtures with tied tag evidence, tag mastery ordering is identical in 100% of repeated progress renders.
- **SC-003**: For selected recap windows of 1, 5, 10, and 30 completed sessions, recap totals and trend labels match expected fixture values in 100% of tests.
- **SC-004**: Markdown and JSON exports generated from the same learner state contain equivalent core report facts in 100% of export round-trip tests.
- **SC-005**: JSON exports validate and read back with no required-field loss in 100% of contract fixtures.
- **SC-006**: Progress view and export output contain no raw learner answer text, full feedback prose, graphical dashboard surface, GUI, web view, or host-specific metadata in 100% of privacy and scope fixtures.
- **SC-007**: The default progress view completes in under 5 seconds on a fixture representing one year of daily completed sessions.
- **SC-008**: In golden fixtures with at least 12 tags, the default terminal output shows the three weakest active tags and the recent performance direction in the first progress section, within the first 30 nonblank lines, using only terminal output.

## Assumptions

- Phase 3 is complete, including weak-tag signal contracts, deterministic selection reasons, and safe weak summaries.
- Existing local history contains enough completed sessions, vocabulary reviews, mistake events, and session summaries to derive mastery and trends.
- The controlled tag vocabulary remains the shared source for vocabulary, writing mistakes, weak patterns, and progress reports.
- The default recap window is 10 completed sessions because it gives recent feedback without bloating terminal output.
- Markdown and JSON are sufficient export formats for Phase 4; CSV, PDF, images, and web dashboards are out of scope.
- The feature extends the existing progress surface rather than creating a separate analytics product.
