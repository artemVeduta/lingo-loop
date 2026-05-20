# Feature Specification: language-tutor v1

**Feature Branch**: `001-build-language-tutor`

**Created**: 2026-05-20

**Status**: Draft

**Input**: User description: "lets build an languale-tutor app. Whole design you will have in docs folder"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Start a First Learning Session (Priority: P1)

A learner installs the tutor, runs setup, records their native language, target language, level, interests, and session preferences, then receives a usable first-session context without creating an account or using remote storage.

**Why this priority**: Every other learning workflow depends on a valid learner profile, preferences, and local state. First-session friction must be low enough for daily dogfood.

**Independent Test**: Can be tested on a fresh local data path by completing setup with only native and target language as required inputs, then starting a session and receiving valid first-session context.

**Acceptance Scenarios**:

1. **Given** no existing learner profile, **When** the learner starts setup, **Then** the tutor requests native language and target language as required fields and applies documented defaults for level, interests, constraints, feedback verbosity, review intensity, transliteration tolerance, session length, display fallback, and streak grace.
2. **Given** setup is complete, **When** a new tutor session starts, **Then** the learner receives concise context that includes profile basics, current review status, weak-pattern summary if any, and first-session guidance when no history exists.
3. **Given** the learner reruns setup, **When** they update preferences, **Then** editable profile data changes without deleting or rewriting prior learning history.
4. **Given** local storage is unavailable or invalid, **When** setup or session start runs, **Then** the tutor shows a clear repair-oriented message and does not silently discard learner data.

---

### User Story 2 - Practice Vocabulary With Review Scheduling (Priority: P1)

A learner practices due vocabulary items in short terminal-native sessions, answers recall prompts, receives immediate correction, and has the next review scheduled from the result.

**Why this priority**: Retaining vocabulary is one half of the core value proposition and creates the daily habit loop.

**Independent Test**: Can be tested by seeding a learner with due vocabulary, completing correct, partially correct, and missed answers, then verifying visible feedback and future review timing reflect the answer quality.

**Acceptance Scenarios**:

1. **Given** due vocabulary exists, **When** the learner starts vocabulary practice, **Then** the tutor presents due items before optional new content and respects the learner's session-length preference.
2. **Given** a learner answers a vocabulary prompt, **When** the answer is evaluated against the accepted reference, **Then** the tutor shows the correct form, the verdict, and any correction needed.
3. **Given** a graded vocabulary answer, **When** the tutor records the result, **Then** the item's future review state changes exactly once and the review event remains visible in progress history.
4. **Given** no due vocabulary exists, **When** the learner requests practice, **Then** the tutor either introduces appropriate generated practice content or explains that there is nothing due, without pretending a review occurred.

---

### User Story 3 - Improve Free Writing With Structured Feedback (Priority: P1)

A learner writes a free-form passage in the target language and receives localized corrective feedback with exact error spans, severity, tags, corrected text, and explanations in their native language.

**Why this priority**: Writing improvement is the second half of the core value proposition and differentiates the tutor from plain flashcard tools.

**Independent Test**: Can be tested by submitting target-language passages containing known grammar, vocabulary, punctuation, and Slavic morphology errors, then checking that feedback identifies the expected spans, categories, severity, and explanations.

**Acceptance Scenarios**:

1. **Given** a learner profile with target language, level, and interests, **When** the learner starts writing practice, **Then** the tutor offers an appropriate prompt or accepts the learner's own passage.
2. **Given** a submitted passage, **When** the tutor evaluates it, **Then** feedback includes a corrected version, localized error spans, severity level, controlled error tags, and an explanation in the learner's native language.
3. **Given** the evaluator has low confidence or returns malformed feedback, **When** the tutor prepares the result, **Then** it retries or softens the claim and avoids presenting uncertain corrections as definitive.
4. **Given** writing feedback produces mistake patterns, **When** state is recorded, **Then** those mistakes contribute to weak-pattern summaries without changing vocabulary review schedules.

---

### User Story 4 - Review Progress and Next Focus (Priority: P2)

A learner checks progress and sees streak, due review count, recent weak patterns, last-session recap, item maturity, and month-to-date tutor cost in a compact text view.

**Why this priority**: The tutor needs enough visible progress to sustain a learning habit without adding gamification or dashboards.

**Independent Test**: Can be tested after one or more completed sessions by requesting progress and comparing the displayed streak, due counts, weak tags, and summaries to recorded session outcomes.

**Acceptance Scenarios**:

1. **Given** completed sessions exist, **When** the learner requests progress, **Then** the tutor displays streak with grace handling, due counts for today and the near future, top weak patterns, and last-session recap.
2. **Given** no completed sessions exist, **When** the learner requests progress, **Then** the tutor explains that there is no learning history yet and points to vocabulary or writing practice as the next action.
3. **Given** a session ends, **When** the tutor summarizes the session, **Then** the learner sees a short recap and a next-focus hint without needing to run a separate command.

---

### User Story 5 - Trust Local, Portable Tutor Behavior (Priority: P2)

A learner or contributor can verify installation health, inspect local data ownership, and rely on stable behavior across sessions without cloud accounts, telemetry, or hidden state.

**Why this priority**: Own-your-data and reproducible behavior are core differentiators and reduce support burden for an OSS plugin.

**Independent Test**: Can be tested by running the health check on macOS and Linux, completing sessions offline except for host-provided model evaluation, and confirming profile, history, summaries, and costs remain locally inspectable.

**Acceptance Scenarios**:

1. **Given** the tutor is installed, **When** the learner runs the health check, **Then** it reports whether required local components, profile files, learning history, and plugin registration are usable.
2. **Given** the learner completes multiple sessions, **When** they inspect their local files, **Then** editable profile/preferences are separate from derived learning history and no remote account is required.
3. **Given** the same recorded feedback model is rendered again, **When** the tutor displays it, **Then** the output is stable for the same input and environment.

### Edge Cases

- Fresh install with no profile, no vocabulary, and no prior sessions.
- Invalid or manually edited profile fields that do not match expected values.
- Target language or native language omitted during setup.
- No due vocabulary at session start.
- Duplicate vocabulary items generated or added from multiple sessions.
- Learner answers with "I don't know", blank input, transliteration, or mixed target/native language.
- Learner changes editable profile or preference files by hand with unknown fields, invalid values, or a version mismatch.
- Writing evaluator returns malformed, contradictory, unsupported-tag, or low-confidence feedback.
- Slavic morphology errors where case, aspect, agreement, animacy, motion verbs, punctuation, or Russian/Ukrainian interference matter.
- Session ends before analysis completes.
- Startup context grows too large to be useful.
- Terminal or host cannot display severity symbols cleanly.
- Local data path is missing, read-only, or partially migrated.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST provide setup that requires only learner native language and target language, captures optional level target, interests, constraints, session length, review intensity, feedback verbosity, transliteration tolerance, display fallback, and streak grace, and applies documented defaults for omitted optional fields.
- **FR-002**: System MUST allow setup to be rerun to edit profile and preferences without erasing learning history.
- **FR-003**: System MUST keep learner profile and preferences as human-editable local data and keep transactional learning history as separate local state.
- **FR-004**: System MUST avoid cloud sync, telemetry, authentication, multi-user accounts, and remote storage in v1.
- **FR-005**: System MUST build a concise session-start learning context from profile, due review counts, top weak patterns, latest session recap, local cost/status data from `CostEvent` and `SkillMetric` records, and first-session guidance when history is empty; if cost data is unavailable, the context MUST state that status explicitly rather than estimating silently.
- **FR-006**: System MUST keep session-start context deterministic, ordered by documented section priority, capped at 6,000 rendered characters, and free of raw event dumps so repeated reads of the same learner state produce the same concise result.
- **FR-007**: System MUST provide a vocabulary practice flow that prioritizes due reviews, presents recall prompts, captures answers, shows immediate feedback, and uses session length plus review intensity to size the practice queue.
- **FR-008**: System MUST evaluate vocabulary answers against accepted reference answers, treat blank and "I don't know" responses as unanswered, apply transliteration tolerance only when the learner preference enables it, and distinguish correct, minor, important, blocking, mixed-language, and unanswered outcomes.
- **FR-009**: System MUST update future vocabulary review timing from a documented spaced-repetition rule after each graded vocabulary answer.
- **FR-010**: System MUST record every vocabulary answer and review result exactly once, even when a session is interrupted.
- **FR-011**: System MUST generate or select target-language practice content without bundled curricula only when the content declares target language, level target, prompt, accepted-answer forms, learner-constraint fit, weak-pattern or interest rationale, and a normalized duplicate key; content missing those fields or conflicting with profile constraints MUST NOT be queued.
- **FR-012**: System MUST provide a free-writing flow that offers prompts matching the learner's target language, level target, interests, and constraints when available, and accepts learner-provided passages when no generated prompt is wanted or no prompt candidate satisfies those fit rules.
- **FR-013**: System MUST return writing feedback with a corrected version, exact error spans where possible, severity level, confidence level (`high`, `medium`, or `low`), controlled error tags, explanation in the learner's native language, a next-drill hint, and explanation detail shaped by feedback verbosity.
- **FR-014**: System MUST leave corrected target-language forms and error tags in the target/controlled form while rendering explanations in the learner's native language.
- **FR-015**: System MUST record writing mistakes as mistake history and weak-pattern inputs without changing vocabulary review schedules by default.
- **FR-016**: System MUST use a frozen controlled error-tag vocabulary for v1, including Slavic morphology categories for case, aspect, agreement, animacy, verbs of motion, punctuation, and Russian/Ukrainian interference.
- **FR-017**: System MUST reject or safely downgrade malformed, unsupported-tag, contradictory, or low-confidence evaluator output before it is persisted or rendered as definitive correction; `low` or missing confidence MUST render as tentative and MUST NOT create a definitive high-severity correction.
- **FR-018**: System MUST render feedback in stable markdown-style text with severity markers and an ASCII fallback when symbols are unavailable.
- **FR-019**: System MUST create a short end-of-session summary that can be shown immediately and reused as the next session's recap; if session analysis is interrupted, recorded events MUST remain persisted and the summary status MUST be marked pending rather than blocking shutdown.
- **FR-020**: System MUST provide progress that includes streak with a documented one-day default grace policy, due review counts, weak patterns, item maturity, last-session recap, and month-to-date model cost.
- **FR-021**: System MUST provide an install or health check that verifies Python runtime readiness, `bin/tutor` executability, plugin manifest/hooks/skills/agent discovery, platform data path permissions, profile/preference YAML schema health, SQLite migration state, and common corrupt-profile or corrupt-history fixtures, with actionable repair messages that identify the failed area, whether learner data was changed, and the next safe step.
- **FR-022**: System MUST install and run on macOS and Linux for v1.
- **FR-023**: System MUST expose user-facing tutor actions as discoverable commands for setup, vocabulary, writing, progress, and doctor/health, with each action mapped to a distinct learner intent and expected user value.
- **FR-024**: System MUST keep setup, vocabulary, writing, progress, rendering, lifecycle analysis, and data ownership decoupled so each can be tested independently.
- **FR-025**: System MUST exclude v1 anti-features beyond the local tutor workflow: games, XP, leagues, push notifications, multi-device sync, rich dashboards, speaking/listening/reading modes, and additional host adapters.

### Key Entities *(include if feature involves data)*

- **Learner Profile**: User-editable language-learning identity, including native language, target language, level target, interests, and constraints.
- **Learner Preferences**: User-editable session and feedback choices, including session length, review intensity, feedback verbosity, and transliteration tolerance.
- **Boot Context**: Canonical session-start context view of profile, due reviews, weak patterns, latest recap, and status needed to guide the current interaction.
- **Vocabulary Item**: A target-language recall unit with accepted answer forms, prompt data, learning state, and maturity.
- **Vocabulary Review**: A recorded answer attempt, verdict, quality outcome, and next-review decision for one vocabulary item.
- **Answer Event**: Append-only record that a learner answered an exercise, including timing, skill, prompt reference, and outcome.
- **Mistake Event**: Structured record of a writing or vocabulary issue, including span, severity, tag, explanation, and confidence.
- **Feedback Result**: Structured correction package containing verdict, corrected answer, error spans, severity, controlled tags, explanation, and required next-drill hint.
- **Lifecycle Event**: Append-only record of setup, vocabulary, writing, progress, or session lifecycle activity used to preserve session history.
- **Session Analysis**: Validated end-of-session analysis used to create summaries, weak-pattern updates, skill metrics, cost records, and pending-status handoff when analysis is interrupted.
- **Session Summary**: End-of-session recap with key outcomes, weak patterns, next focus, and a concise handoff for the next session.
- **Skill Metric**: Aggregated learning or cost metric used for progress, habit tracking, and operational visibility.
- **Cost Event**: Append-only local record of host-provided usage metadata for evaluator or analyzer calls, including operation, model, token counts, optional USD estimate, source, and timestamp.
- **Migration Record**: Local SQLite migration marker with applied version and checksum state.
- **Error Tag**: Controlled category used to group mistakes consistently across feedback, progress, and future practice.

## Constitution Alignment *(mandatory)*

- **Affected Layers**: Host adapter, core, DAL, renderer, user-facing skills, hooks, and packaging are all in scope for the v1 app. Host adapters translate host events and paths only; core owns pedagogy, lifecycle state, schemas, SRS, and feedback semantics; DAL owns local config/state, migrations, repositories, and transactions; renderers convert validated feedback to host-facing text.
- **Data Ownership**: YAML owns only human-editable profile and preferences. SQLite owns transactional and derived learning state: answer events, mistake events, SRS items, SRS reviews, session summaries, skill metrics, migrations, and costs. No cloud services, telemetry, auth, remote storage, or dual ownership are allowed in v1.
- **Contract Surfaces**: BootContext, FeedbackEnvelope, SessionAnalysis, lifecycle events, answer/review records, profile/preferences contracts, controlled error-tag vocabulary, CLI JSON, JSON schema mirrors, and SQL migrations.
- **Required Validation**: Unit tests for pure scheduling and mappings; golden tests for boot context and feedback rendering; contract tests for host adapter and command JSON; integration tests for setup, vocabulary, writing, progress, and lifecycle flows; migration tests for local state; semantic evaluator fixtures for Slavic feedback quality.
- **Scope Guardrails**: Current v1 scope is Claude Code host, local Python core, YAML and SQLite persistence, vocabulary SRS, free writing, feedback rendering, session analysis, progress, install checks, and packaging. New hosts, dashboards, gamification, cloud sync, multi-user, FSRS, bundled curricula, rich charts, speaking/listening/reading modes, and speculative abstractions are out of scope.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A fresh learner can complete setup and reach first-session context in under 60 seconds using only native language and target language as required setup inputs.
- **SC-002**: 100% of normal session starts show a concise learner context of no more than eight ordered sections and 6,000 rendered characters, including current review status or clear first-session guidance.
- **SC-003**: In acceptance tests, 100% of graded vocabulary answers produce one visible feedback result, one recorded review event, and one future review decision with no duplicate state changes.
- **SC-004**: In a curated fixture set of at least 20 non-empty writing submissions that pass input validation, at least 95% produce feedback containing corrected text, span or location guidance, severity, controlled tag, and native-language explanation.
- **SC-005**: In curated Slavic evaluator fixtures, expected verdicts and core morphology tags are produced for at least 90% of cases, with no definitive high-severity correction shown for known-correct sentences.
- **SC-006**: Progress view answers streak, due count, weak patterns, item maturity, last-session recap, month-to-date estimated USD cost, and cost availability status in under 5 seconds for a learner with one year of daily history.
- **SC-007**: Re-rendering the same validated feedback or session-start context produces identical displayed text in 100% of deterministic fixtures.
- **SC-008**: A learner can complete 30 consecutive days of local sessions without creating an account, enabling telemetry, using cloud storage, or manually repairing learning state.
- **SC-009**: macOS and Linux fresh-machine checks identify missing prerequisites or corrupt local data with actionable messages in 100% of tested failure fixtures.
- **SC-010**: Dogfood use reaches at least five completed tutor sessions per week for two consecutive weeks, measured from local session summaries where a completed session records at least one setup, vocabulary, writing, progress, or session-end outcome, without losing history or requiring direct edits to derived learning state.

## Assumptions

- v1 is a single-learner, local-first tutor used from an agentic CLI environment.
- Claude Code is the only host supported in v1; support for other hosts is out of scope.
- The learner brings access to host-provided model evaluation; the tutor itself does not add separate cloud accounts or remote storage.
- Host-provided model evaluation is responsible for language-generation quality; the tutor is responsible for well-formed feedback, validation, display, local records, and safe downgrade behavior.
- Exercise content is generated or selected on demand instead of bundled as a curated curriculum.
- Cost display uses local usage metadata captured from host-provided evaluator or analyzer calls; when token counts or pricing metadata are absent, progress and boot context show cost status as unavailable.
- The initial daily-use surface is setup, vocabulary, writing, progress, session start context, and session end summary.
- Russian/Ukrainian/Slavic dogfood drives evaluator quality requirements, but the learner profile can name any target language.
- Native-language explanations are required; controlled tags remain stable and language-neutral.
- First-run defaults are level target A2, empty interests and constraints, concise feedback verbosity, standard review intensity, transliteration tolerance off, 10-minute session length, automatic ASCII fallback, and one-day streak grace.
- Local data may be manually inspected by the learner, but derived history is changed through tutor workflows rather than hand edits.
