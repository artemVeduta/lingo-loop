<!--
Sync Impact Report
Version change: 1.2.0 -> 1.3.0
Modified principles:
- V. Simplicity and Scope Discipline (lifts Antigravity exclusion; adds
  OpenCode and the headless QA harness to in-scope v1 surfaces; QA harness
  declared a test surface, not a release gate)
- III. Testable Deterministic Behavior (adds reproducible headless QA via
  MockDriver smoke as a deterministic surface; live QA runs remain opt-in and
  non-gating)
Added principles:
- X. Advisory Semantic QA Harness
Added sections:
- None
Removed sections:
- None
Templates requiring updates:
- ✅ checked .specify/templates/plan-template.md (Constitution Check stays
  principle-agnostic; no edit required)
- ✅ checked .specify/templates/spec-template.md (scope/out-of-scope guidance
  already covers new principle; no edit required)
- ✅ checked .specify/templates/tasks-template.md (QA harness tasks fit
  existing contract/integration/test categories; no edit required)
- ✅ checked .specify/templates/checklist-template.md (no principle-specific
  language; no edit required)
- ✅ checked .specify/extensions/git/commands/*.md (no constitutional
  references requiring update)
- ✅ docs/ROADMAP.md already reflects Phase 8 scope (QA harness + adapter
  expansion incl. agy/opencode); no edit required for this amendment
- ⚠ pending specs/006-agent-adapter-setup/ amendment note pointing at Phase 8
  (per design.md §Adapter expansion) — to be authored during Phase 8 planning
Follow-up TODOs:
- Phase 8 implementation MUST land the spec 006 amendment note, the
  `HostId` enum update (add `opencode`, drop antigravity reject),
  positive packaging coverage replacing `test_no_antigravity_artifacts`,
  and the `agy-plugin/` + `opencode-plugin/` artifacts before declaring
  the adapter-expansion exit gate met.
-->
# language-tutor Constitution

## Core Principles

### I. Layered Single-Responsibility Boundaries

Every module MUST have one reason to change. Host adapters translate host events
and paths only. The core owns pedagogy, lifecycle state, schemas, SRS, and
feedback semantics. The DAL owns YAML, SQLite, migrations, repositories, and
transactions. Renderers turn validated models into host-facing output. Feature
plans MUST name the touched layer and MUST justify any cross-layer call.

Rationale: strict separation keeps the tutor portable across hosts without
letting Claude-specific mechanics leak into teaching logic or data ownership.

### II. Contracts and Abstractions First

Inter-layer data MUST move through explicit contracts: Pydantic models, narrow
Protocols, JSON schemas, SQL migrations, or documented CLI JSON. Callers MUST
depend on those contracts, not concrete storage, renderer, or host adapter
details. Substitutable implementations MUST pass the same contract tests.
Generic interfaces, optional fields, and catch-all dictionaries are forbidden
unless the feature spec proves the current need.

Rationale: the project relies on stable `BootContext`, `FeedbackEnvelope`,
`SessionAnalysis`, lifecycle, and persistence contracts to make LLM behavior
auditable and host-identical.

### III. Testable Deterministic Behavior

Pure behavior MUST be deterministic and covered at the right boundary. SM-2
math, severity mapping, boot-context rendering, feedback markdown, YAML
validation, schema validation, and migration behavior require unit or golden
tests. Host adapters require contract tests, and adapter conformance MUST verify
first-message boot and per-step checkpoint persistence rather than hook-driven
lifecycle. User journeys that cross CLI, core, and DAL require integration
tests. LLM evaluator quality requires semantic fixture evaluation with
controlled tags and confidence thresholds. The QA harness MUST keep at least
one deterministic surface: a `MockDriver` end-to-end smoke run in CI that
exercises the full learner → tutor → judge pipeline without real LLM calls.
Live LLM-driven QA runs are opt-in (`pytest -m qa_live`), non-gating, and MUST
NOT be required for merge. Skill creation and rewrite behavior requires
subagent pressure tests and best-practice compliance checks before any
`SKILL.md` change ships.

Rationale: a language tutor loses trust when schedules, corrections, or rendered
feedback drift without explanation, and a skill-driven product loses trust when
its invocation rules fail under realistic agent pressure. Determinism on the
harness itself is what lets the advisory critique signal stay comparable across
runs.

### IV. Local-First Data Ownership

YAML MUST contain only human-editable profile and preference fields. SQLite MUST
contain transactional and derived state: sessions, checkpoints, answer events,
mistake events, SRS items, SRS reviews, session summaries, skill metrics,
migrations, and costs. Source-of-truth writes MUST be incremental: a session
record on boot, a checkpoint on each lesson/exercise/prompt step, and answer,
feedback, mistake, and review events on each learner answer. `session-end` is
NOT source of truth and MUST NOT be required for data safety; durable next-boot
memory MUST derive from per-step checkpoints and events. Checkpoints and session
rows MUST store only safe step metadata — no raw host logs, full transcripts,
secrets, or local config. The system MUST validate YAML on load, version
schemas, use platform/XDG paths, and avoid cloud services, telemetry, auth, or
remote storage in v1.

Rationale: own-your-data is a product constraint, and incremental persistence
guarantees that data through the last completed step survives an abrupt app
close without depending on any shutdown event.

### V. Simplicity and Scope Discipline

Implement current v1 requirements only: host adapters for Claude Code, Codex,
Hermes, OpenClaw, Antigravity, and OpenCode; local Python core; YAML and SQLite
persistence; vocab SRS; free writing; reading/lesson/dictation text modalities;
feedback rendering; session analysis; progress; install checks; skill-suite
quality gates; and the headless QA harness used as a test surface. Dashboards,
gamification, cloud sync, multi-user support, FSRS, bundled curricula, audio
modalities, and new user-facing skills are out of scope until a documented
amendment or feature spec moves them into scope. Plans MUST reject speculative
abstractions, unused dependencies, and methods without current callers.

Rationale: the MVP must become a daily-use tutor before the architecture expands,
and the adapter set is now wide enough that adding more hosts is an explicit
amendment, not a default.

### VI. DRY Without False Coupling

Each concept MUST have one source of truth: schemas define data contracts,
migrations define database structure, YAML defaults define editable config, and
renderers define presentation. Duplication is allowed only when coupling
unrelated logic would make change risk higher; such duplication MUST be named in
the plan. Repeated literals, tag vocabularies, severity maps, path rules, and
prompt rubrics MUST be centralized.

Rationale: duplicated teaching and data rules cause inconsistent feedback,
unreliable analytics, and migration drift.

### VII. Composition and Demeter

Behavior MUST be assembled from small functions, dependency-injected services,
repositories, and adapters. Inheritance hierarchies, service locators, global
mutable state, and long object navigation chains are forbidden. A module MAY
talk only to its immediate collaborators through explicit methods or Protocols.

Rationale: composition keeps tests small and prevents feature code from reaching
through adapters, DAL internals, or renderer details.

### VIII. Skill Creation as Tested Contract

Every creation or update of a project `SKILL.md` MUST be treated as a tested
contract change, not as prose cleanup. The work MUST use a subagent per skill or
coherent skill family. The subagent prompt MUST explicitly require reading the
local helper at
`/Users/artem.veduta/.claude/plugins/cache/claude-plugins-official/superpowers/5.1.0/skills/writing-skills`
and reporting changed files. Skill work MUST apply the active feature's required
external skill-authoring references; the baseline skill-authoring references are
Anthropic skill authoring best practices, Anthropic's Complete Guide to Building
Skills, and the Superpowers skill corpus. No skill may ship without documented
RED/GREEN/REFACTOR evidence: baseline subagent behavior without the change,
minimal skill change, pressure verification with the change, and any loophole
closures. `SKILL.md` files MUST remain thin orchestration and discovery
documents; pedagogy, persistence, rendering, scoring, migrations, and privacy
filters belong in validated Python contracts and tests.

Rationale: skills are runtime control surfaces. Untested or overgrown skills
silently misroute learner requests, duplicate core logic, and bypass the
deterministic contracts that make the tutor auditable.

### IX. Hook-Free Incremental Lifecycle

All hosts MUST share one lifecycle with no host-specific hooks. `lifecycle_start`
MUST be `first_message`: the first tutor message creates a new tutor session and
returns boot context plus the active `session_id`. `lifecycle_end` MUST be
`not_available`: there is no automatic session end, and a closed session is only
produced by an explicit manual close command. `persistence_mode` MUST be
`incremental_checkpoint` for every host. A new host conversation MUST create a
new `session_id` (from the host conversation id when available, else
tutor-generated) and MUST NOT mutate prior session ids; prior `open`/`stale`
sessions are read as history only. Host capability profiles MUST NOT model Codex
`Stop`, Claude `SessionStart`/`SessionEnd`, OpenClaw `session_end`, or Hermes
`on_session_end` as target tutor lifecycle. Hook files, if retained during
migration, MUST be marked deprecated legacy compatibility and excluded from
capability and conformance assertions.

Rationale: hooks can be disabled, uninstalled, or behave differently per host;
one no-hook lifecycle with first-message boot and per-step persistence is simpler
and gives stronger data safety than shutdown hooks across heterogeneous hosts.

### X. Advisory Semantic QA Harness

The headless QA harness (`tests/qa/`) is an advisory test surface, not a release
gate. Critique verdicts, vibe paragraphs, and rubric scores MUST NOT
auto-promote into merge requirements or block CI; they inform triage. Required
properties of the harness:

- **Separation of roles.** Learner and judge MUST run in separate driver
  processes so persona prompts cannot leak into grading prompts.
- **Host neutrality.** The harness core (`harness.py`, `learner.py`,
  `judge.py`, `fixtures.py`) MUST NOT import host-specific code; per-host
  logic lives only in `tests/qa/drivers/<host>.py` behind the
  `LearnerDriver` / `JudgeDriver` Protocols. Adding a host MUST NOT change
  the harness core.
- **Fixture isolation.** Learner runs MUST execute against an isolated
  fixture profile under repo-relative paths injected via `TUTOR_DATA_DIR`,
  `XDG_DATA_HOME`, and `XDG_CONFIG_HOME`. The harness MUST assert none of
  these resolve under `$HOME` and MUST serialize concurrent runs via
  `flock` on `qa-learner/.lock`. Seed snapshots live under
  `data/fixtures/qa-snapshots/<id>/` and MUST fail loud when their recorded
  migration head diverges from the current `migrations/` head.
- **Schema-validated critique.** Judge output MUST parse as the `Critique`
  Pydantic model with one retry on parse failure; second failure writes
  `critique.raw.txt` and exits non-zero. Each rubric score MUST cite a
  transcript span (`quote`) to deter hallucinated grading.
- **Cost discipline.** Live LLM runs MUST be opt-in (`pytest -m qa_live`)
  and MUST NOT run by default in CI. The default CI pipeline MUST exercise
  the harness only through `MockDriver`.
- **Privacy.** Per-run reports under `tests/qa/reports/` MUST be gitignored;
  no transcripts, critiques, or fixture state MAY ship in distributed
  packages or be required by adapter packaging-privacy tests.

Rationale: an LLM judge is useful for trend signal and bug triage but is
non-deterministic and token-priced; treating its output as advisory keeps the
deterministic merge gate intact, while strict isolation prevents the harness
from leaking learner state into the maintainer's real tutor data or shipped
artifacts.

## Operational Constraints

- Runtime MUST remain Python 3.12+ with a synchronous core.
- SQLite MUST use stdlib `sqlite3`; ORM or async storage requires a constitution
  amendment with a measured need.
- Human-editable YAML MUST use comment-preserving round trips for setup/edit
  flows and safe reads for boot-time loading.
- The CLI MUST expose validated JSON for host adapters and skills.
- v1 hosts are Claude Code, Codex, Hermes, OpenClaw, Antigravity, and OpenCode;
  host-portability work MUST stay limited to contracts and adapter seams shared
  by these adapters. Adding a host outside this set requires an amendment.
- LLM evaluator outputs MUST be schema-validated before persistence or rendering.
- Boot context MUST be deterministic and token-budgeted, and boot MUST return
  the active `session_id` alongside context.
- Host lifecycle MUST NOT depend on hooks; hooks MUST NOT be packaged as required
  adapter surface for any host.
- The QA harness MUST NOT ship as production CLI surface, MUST live under
  `tests/qa/`, MUST keep per-run artifacts gitignored, and MUST guard fixture
  reset with the documented `flock` + XDG isolation contract.
- Skill frontmatter names MUST use lowercase letters, numbers, and hyphens; the
  description MUST be third-person, concrete, trigger-oriented, and free of
  workflow summaries that let an agent skip the full skill body.
- Skill reference files MUST use progressive disclosure: one-level links from
  `SKILL.md`, descriptive filenames, and scripts for deterministic operations
  where a script is safer than generated instructions.
- Shell verification in this repository MUST use the `rtk` command prefix.

## Development Workflow

- Every feature spec MUST state user value, out-of-scope items, affected layers,
  data ownership, and measurable success criteria.
- Every plan MUST pass the Constitution Check before research and after design.
- Every task list MUST group work by independently testable user story and add
  contract, data, rendering, migration, and semantic-eval tasks when those
  surfaces change.
- Every task list that creates or changes project skills MUST include skill
  inventory, subagent dispatch, local writing-skills helper use, external
  reference checks, pressure-test evidence, activation/description review, and a
  main-agent integration review of reported changed files.
- Tests that define required behavior MUST be written before implementation for
  contract, persistence, rendering, SRS, boot-context, and evaluator semantics.
- Skill tests MUST be written before skill edits: pressure scenarios first,
  baseline failure documented, then skill edit, then subagent verification.
- QA harness changes MUST be written with unit tests for scenario load, fixture
  reset, driver matrix, critique schema, and env isolation before driver or
  scenario code lands; a `MockDriver` smoke run MUST stay green on every PR
  that touches the harness.
- Reviews MUST reject SOLID, DRY, KISS, YAGNI, SoC, composition, or Demeter
  violations and skill-creation gate violations unless the plan records the
  violation and the simpler alternative rejected.
- Changes MUST preserve existing user work in the repository and avoid unrelated
  refactors.

## Governance

This constitution supersedes conflicting local practices for architecture,
scope, data ownership, testing, and review. Amendments require a written change
to this file, a semantic version bump, a Sync Impact Report, and updates to
affected templates or runtime guidance.

Versioning policy:
- MAJOR: removes or redefines a principle, weakens a mandatory gate, or expands
  v1 scope in a way that breaks prior governance.
- MINOR: adds a principle, section, mandatory gate, or materially expands
  guidance.
- PATCH: clarifies wording, fixes typos, or tightens non-semantic guidance.

Compliance review expectations:
- Plans and reviews MUST cite this constitution when accepting complexity,
  dependencies, cross-layer calls, or scope changes.
- Template updates MUST be completed in the same change as constitutional
  amendments.
- Skill governance updates MUST cite the local writing-skills helper and the
  active spec's required skill-authoring references when skill creation or
  rewrite work is in scope.
- QA harness critique output MUST NOT be cited as a merge gate; reviews MAY
  cite it as advisory evidence only.
- Deferred governance questions MUST be recorded as TODO entries in the Sync
  Impact Report and resolved before implementation depends on them.

**Version**: 1.3.0 | **Ratified**: 2026-05-19 | **Last Amended**: 2026-05-23
