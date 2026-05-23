# Feature Specification: Automated QA Agent Harness + Adapter Expansion

**Feature Branch**: `008-qa-harness-agent`

**Created**: 2026-05-23

**Status**: Draft

**Input**: User description: "specs/008-qa-harness-agent/design.md. we should split tasks to batch phases and use sub-agent per each batch"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Headless end-to-end tutor run with structured critique (Priority: P1)

A maintainer wants to validate a tutor change without manually role-playing a learner inside Claude Code. They invoke the QA harness with a named scenario. A learner agent drives a full tutor session in character against an isolated fixture profile; a separate judge agent then grades the transcript against a fixed rubric and writes a structured critique plus free-form in-character "feelings about the lesson." All artifacts land on disk under a timestamped run directory for later review and trend tracking.

**Why this priority**: This is the core value of the phase. Without it, dogfooding remains manual and qualitative signal still vanishes when the session window closes. Every other story exists only to make this one reproducible across hosts and scenarios.

**Independent Test**: Run `python -m tests.qa run reading-a2` against the bundled mock-driver scenario. Confirm a `reports/<ts>-reading-a2/` directory is produced containing `transcript.jsonl`, `tutor-state-diff.json`, `critique.json`, and `critique.md`, with `critique.json` matching the rubric schema and citing transcript spans.

**Acceptance Scenarios**:

1. **Given** a registered scenario and a healthy learner+judge driver, **When** the maintainer runs the harness, **Then** the harness produces the four named artifacts and exits zero with a one-line verdict on stdout.
2. **Given** the learner reaches the scenario's success signal, **When** the run completes, **Then** the critique contains an integer 1–5 score per rubric dimension, each with a citation quote from the transcript, plus a free-form `vibes` paragraph and a verdict of `ship | iterate | broken`.
3. **Given** a learner that stalls or breaks character (no tutor tool call for N consecutive turns), **When** the harness detects the break, **Then** it terminates the run, marks the verdict `broken`, still produces a critique, and the critique flags the persona break as a bug.
4. **Given** two harness invocations started simultaneously against the same fixture profile, **When** both attempt to reset the fixture, **Then** the second blocks on a lock (or exits cleanly under `--no-wait`) and neither run sees the other's fixture state.

---

### User Story 2 - Reproducible fixture isolation with snapshot lifecycle (Priority: P1)

The maintainer needs every run to start from a known-good learner profile and never touch real user data. A snapshot management surface lets them capture a new seed from the current fixture, list available seeds, and promote an end-state of a finished run into a new seed so multi-day continuity scenarios can be chained.

**Why this priority**: Without deterministic seeds, critique scores are not comparable across runs and the harness loses its value as a trend instrument. Sharing fate with User Story 1 — both must land together for the harness to be useful at all.

**Independent Test**: Run `python -m tests.qa snapshot new a2-baseline` after setting up a fixture, then `python -m tests.qa snapshot list` to confirm it appears, then run a scenario seeded by it and `python -m tests.qa snapshot promote <run-id> a2-day2` to capture its end-state. Verify no operation touches paths under `$HOME`.

**Acceptance Scenarios**:

1. **Given** a seed snapshot whose recorded schema head matches the current migrations head, **When** the harness resets the fixture profile, **Then** the working fixture directory exactly mirrors the snapshot and the run proceeds.
2. **Given** a seed snapshot whose schema head is older than the current migrations head, **When** the harness attempts a reset, **Then** it fails loud before the run begins with a message pointing at the documented bump procedure.
3. **Given** any fixture or snapshot operation, **When** the harness resolves filesystem paths, **Then** no resolved path falls under the maintainer's `$HOME`.

---

### User Story 3 - Multi-host learner and judge drivers (Priority: P2)

The maintainer wants the harness to work across the full supported host matrix — Claude Code, Codex, Hermes, OpenClaw, Antigravity, and OpenCode — so QA covers the same hosts that real users will install the tutor plugin into. They can override learner and judge drivers per invocation; missing driver binaries fail loud at scenario load with an install hint rather than silently skipping.

**Why this priority**: Cross-host coverage is the whole reason adapter expansion ships in this phase. It depends on User Story 1's harness skeleton existing first, so it sits below P1 but above the smoke-test story.

**Independent Test**: For each host driver, run a recorded-fixture contract test that exercises the `LearnerDriver` / `JudgeDriver` protocol surface, plus one opt-in live scenario per host gated behind a pytest marker. Confirm a deliberately-removed driver binary causes the run to fail at scenario load with a non-zero exit and the install hint in stderr.

**Acceptance Scenarios**:

1. **Given** a scenario whose declared learner driver has a tutor plugin shipped, **When** the harness loads the scenario, **Then** it accepts the configuration and proceeds.
2. **Given** a scenario whose declared learner driver has no tutor plugin shipped, **When** the harness loads the scenario, **Then** it rejects the configuration at load time with a clear capability error.
3. **Given** Antigravity and OpenCode are now supported hosts, **When** a maintainer runs the manual-install reporter, **Then** both appear as recognized hosts with capability profiles, and no test still asserts their absence.

---

### User Story 4 - CI-safe smoke pipeline without live LLM costs (Priority: P3)

A CI run needs to exercise the full harness pipeline end-to-end without spending real tokens. A deterministic mock driver supplies canned learner and judge responses so the orchestrator, fixture reset, state diff, critique schema, and report writer can all be checked on every push, while real-LLM scenarios stay opt-in behind a marker for manual runs.

**Why this priority**: Important for keeping the harness honest over time, but the harness is usable for the maintainer without it. Lower priority than the host coverage it depends on.

**Independent Test**: Run `pytest tests/qa/smoke/` in a network-isolated environment with no host CLI binaries on `PATH` except the mock. Confirm the pipeline completes, produces all artifacts, and exits zero. Run `pytest -m qa_live` separately and confirm it is not collected by the default CI command.

**Acceptance Scenarios**:

1. **Given** the mock driver is the only available driver, **When** the smoke suite runs, **Then** at least one full scenario completes and asserts on the resulting critique structure.
2. **Given** the default CI command, **When** it collects tests, **Then** no `qa_live`-marked test is executed.

---

### Edge Cases

- Driver CLI binary missing → fail at scenario load with a documented exit code and install hint; never silent-skip.
- Tutor CLI crashes mid-run → its non-zero exit is captured in the transcript, stderr lands in a `tutor-errors.log` under the run directory, no retry, and the bug surfaces in the critique.
- Judge returns invalid JSON → one retry with the prior raw output appended; second failure writes the raw response to `critique.raw.txt` and the harness exits non-zero.
- Token budget exceeded for either driver → kill the driver, mark verdict `broken` with reason `budget_exceeded`, still write a partial report.
- Judge LLM / API outage (distinct from invalid JSON) → write a partial report with transcript and state diff present, no critique, and a distinct exit code.
- Snapshot schema drift → fail at reset, not mid-run; point at the bump procedure.
- Concurrent runs against the same fixture → second run blocks on a file lock or exits under `--no-wait`.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The harness MUST orchestrate a learner agent and a judge agent as two separate processes per run and produce a per-run report directory containing the transcript, tutor state diff, structured critique JSON, and human-readable critique markdown.
- **FR-002**: The harness MUST load scenarios from declarative YAML files specifying persona, target skill, learner driver, judge driver, seed snapshot, opening message, max turns, success signals, and per-role token budgets.
- **FR-003**: The harness MUST reset the learner fixture profile from a named seed snapshot before each run, using an exclusive file lock to serialize concurrent runs against the same fixture.
- **FR-004**: The harness MUST refuse to run when a seed snapshot's recorded schema head does not equal the current migrations head, failing at reset time with a documented remediation path.
- **FR-005**: The harness MUST inject fixture-scoped environment so that the learner driver's data, config, and cache paths never resolve under the maintainer's `$HOME`; the harness MUST assert this invariant before spawning the learner.
- **FR-006**: The harness MUST terminate a learner run when any of the following occurs: success signal matched, max turns reached, tutor returns a terminal state, persona-break heuristic triggers, or token budget exceeded.
- **FR-007**: The judge MUST run in a process separate from the learner, take only the transcript, state diff, and rubric as input, and return a critique conforming to the rubric schema (integer 1–5 per dimension with a citation quote and a rationale, a bug list with severity / evidence / location, a free-form `vibes` paragraph, and a verdict of `ship | iterate | broken`).
- **FR-008**: The judge MUST be retried exactly once on parse failure with the prior raw output appended to the prompt; a second parse failure MUST persist the raw response and cause the harness to exit non-zero.
- **FR-009**: The harness MUST expose a snapshot management surface for creating a new seed from the current fixture, promoting a finished run's end-state into a new seed, and listing available seeds.
- **FR-010**: The harness MUST support six host drivers — Claude Code, Codex, Hermes, OpenClaw, Antigravity, and OpenCode — plus a deterministic mock driver used by the CI smoke suite.
- **FR-011**: A capability matrix MUST declare for each driver whether it carries a shipped tutor plugin; only drivers with a shipped plugin MUST be acceptable as learners, and this MUST be enforced at scenario load.
- **FR-012**: A missing driver binary MUST cause scenario load to fail with a distinct exit code and an install hint sourced from the capability matrix; the harness MUST NOT silently skip.
- **FR-013**: The Phase 6 adapter setup MUST be amended to remove the Antigravity reject and add OpenCode to the host enum, with capability profiles, registry entries, manual-install reports, and contract surfaces extended to both new hosts; the prior negative packaging assertion for Antigravity MUST be replaced with positive coverage.
- **FR-014**: Tutor plugin artifacts for Antigravity and OpenCode MUST ship in the repository under host-specific plugin directories that mirror the existing Codex plugin layout.
- **FR-015**: The harness MUST be invocable as `python -m tests.qa` with subcommands for `run`, `list-scenarios`, and `snapshot`; it MUST NOT introduce any production CLI surface or ship to end users.
- **FR-016**: The harness MUST emit one short verdict line on stdout per run, with full structured output written only to the per-run report directory.
- **FR-017**: A CI-safe smoke suite MUST exercise the full pipeline using only the mock driver and MUST NOT depend on any host CLI binary being available on `PATH`; live-LLM scenarios MUST be gated behind an opt-in pytest marker that the default CI command does not collect.
- **FR-018**: Implementation tasks MUST be partitioned into independent batch phases, with one subagent per batch, matching the design's adapter-expansion / harness-core / driver-layer split so the three streams can land in parallel.

### Key Entities

- **Scenario**: A named, declarative YAML describing a single QA run — persona, target skill, learner and judge drivers, seed snapshot, opening message, max turns, success signals, and per-role token budgets.
- **Persona**: A plain-markdown character sheet for the learner — role, CEFR level, native language, learning goal, expected and forbidden behaviors.
- **Seed Snapshot**: A committed, immutable bundle representing a known-good learner profile state, tagged with the schema migrations head it was captured against.
- **Transcript**: An ordered record of stream events from a single learner driver process, persisted as JSONL under the run directory.
- **State Diff**: A structured diff between the seed snapshot's tutor SQLite state and the post-run fixture state.
- **Rubric**: The judge's system prompt and the schema definition for the critique it must emit.
- **Critique**: The judge's structured output — per-dimension scores with citation quotes, a bug list, a free-form `vibes` paragraph, and a verdict.
- **Driver Capability Profile**: Per-driver metadata declaring whether the driver ships a tutor plugin, its binary name, its headless invocation form, and its stream-event schema flavor.
- **Run Report**: A timestamped per-run directory bundling transcript, state diff, critique JSON, critique markdown, and any error logs.

## Constitution Alignment *(mandatory)*

- **Affected Layers**: Host adapter (capability profiles, registry, plugin artifacts for Antigravity and OpenCode), packaging (manual-install reports, removal of negative Antigravity assertion), test-only QA harness layer under `tests/qa/` (orchestrator, drivers, scenarios, personas, rubric). No production runtime, DAL, renderer, or skill changes.
- **Data Ownership**: YAML for scenarios, personas, capability profiles, and seed snapshot metadata; markdown for personas and rubric; JSONL for transcripts; JSON for critiques, state diffs, and per-run reports; SQLite only as the existing tutor state surface inside fixture seeds (no new schema).
- **Contract Surfaces**: Pydantic models for `Scenario`, `Critique`, `StateDiff`, and `DriverCapabilityProfile`; Python `Protocol` definitions for `LearnerDriver` and `JudgeDriver`; an amendment note on the Phase 6 capability-profile contract for the two new hosts.
- **Required Validation**: Unit tests for scenario load, fixture reset, driver matrix, critique schema, and env isolation; contract tests per driver against the protocol surface; one mock-driven end-to-end smoke run in CI; opt-in live scenarios per learner driver behind the `qa_live` marker; migration-head guard on snapshot reset.
- **Skill Creation**: No new skill packages and no `SKILL.md` changes. The harness is a test-only Python module, not a Claude Code skill.
- **Scope Guardrails**: Not replacing existing unit, contract, migration, or packaging suites. No live LLM runs in default CI. Critique verdicts are advisory and never auto-gate releases. No UI — reports stay as files on disk. No audio scenarios (Phase 9). No multi-turn judge dialog. No cross-run trend dashboards beyond raw JSON. No distributed scenario execution.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A maintainer can run any registered scenario end-to-end, from invocation to written critique, in a single command without manually role-playing inside any host CLI.
- **SC-002**: Every completed run produces a report directory containing the four required artifacts (transcript, state diff, critique JSON, critique markdown), with the critique JSON conforming to the rubric schema in 100% of successful runs.
- **SC-003**: Each critique dimension score cites a verbatim span from the transcript in 100% of judge outputs that pass schema validation.
- **SC-004**: Two harness invocations launched simultaneously against the same fixture never observe each other's intermediate state.
- **SC-005**: A snapshot whose schema head lags the current migrations head causes a reset to fail before any run-time work, in 100% of attempts.
- **SC-006**: All six supported hosts plus the mock driver pass their driver contract tests; a missing driver binary always surfaces as a load-time failure with an install hint.
- **SC-007**: The default CI command exercises the full harness pipeline via the mock driver and never invokes a live LLM.
- **SC-008**: Implementation lands as three independent task batches executable in parallel by separate subagents, matching the design's adapter-expansion / harness-core / driver-layer split.

## Assumptions

- Phase 7 (hook-free incremental lifecycle) is merged before this work begins, so headless tutor lifecycles are deterministic enough for an LLM learner to drive.
- Critique outputs are advisory signal for the maintainer; they do not gate releases and are not consumed by any external service.
- Per-run reports live under a gitignored `tests/qa/reports/` directory and are retained only on the maintainer's machine; no central trend storage in this phase.
- Real-LLM scenario runs are manual and cost-bearing; the harness is not expected to run them in CI.
- Existing manual dogfood testing inside Claude Code remains available during the transition; the harness supplements rather than replaces the maintainer's ability to run the tutor manually.
- The user-provided guidance to "split tasks into batch phases with one sub-agent per batch" maps cleanly onto the three workstreams already identified in `design.md` (adapter expansion, harness core, driver layer) and does not imply additional batches beyond those.
