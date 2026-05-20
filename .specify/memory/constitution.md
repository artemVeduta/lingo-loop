<!--
Sync Impact Report
Version change: template -> 1.0.0
Modified principles:
- Placeholder Principle 1 -> I. Layered Single-Responsibility Boundaries
- Placeholder Principle 2 -> II. Contracts and Abstractions First
- Placeholder Principle 3 -> III. Testable Deterministic Behavior
- Placeholder Principle 4 -> IV. Local-First Data Ownership
- Placeholder Principle 5 -> V. Simplicity and Scope Discipline
Added principles:
- VI. DRY Without False Coupling
- VII. Composition and Demeter
Added sections:
- Operational Constraints
- Development Workflow
Removed sections:
- Template placeholder section 2
- Template placeholder section 3
Templates requiring updates:
- ✅ updated .specify/templates/plan-template.md
- ✅ updated .specify/templates/spec-template.md
- ✅ updated .specify/templates/tasks-template.md
- ✅ updated .specify/templates/checklist-template.md
- ✅ checked .specify/extensions/git/commands/*.md
- ✅ updated AGENTS.md
Follow-up TODOs:
- None
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
tests. Host adapters require contract tests. User journeys that cross CLI,
core, and DAL require integration tests. LLM evaluator quality requires
semantic fixture evaluation with controlled tags and confidence thresholds.

Rationale: a language tutor loses trust when schedules, corrections, or rendered
feedback drift without explanation.

### IV. Local-First Data Ownership

YAML MUST contain only human-editable profile and preference fields. SQLite MUST
contain transactional and derived state: answer events, mistake events, SRS
items, SRS reviews, session summaries, skill metrics, migrations, and costs.
The system MUST validate YAML on load, version schemas, use platform/XDG paths,
and avoid cloud services, telemetry, auth, or remote storage in v1.

Rationale: own-your-data is a product constraint and prevents dual sources of
truth between editable config and computed learner state.

### V. Simplicity and Scope Discipline

Implement current v1 requirements only: Claude Code adapter, local Python core,
YAML and SQLite persistence, vocab SRS, free writing, feedback rendering,
session analysis, progress, and install checks. New hosts, modalities,
dashboards, gamification, cloud sync, multi-user support, FSRS, and bundled
curricula are out of scope until a documented amendment moves them into scope.
Plans MUST reject speculative abstractions, unused dependencies, and methods
without current callers.

Rationale: the MVP must become a daily-use tutor before the architecture expands.

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

## Operational Constraints

- Runtime MUST remain Python 3.12+ with a synchronous core.
- SQLite MUST use stdlib `sqlite3`; ORM or async storage requires a constitution
  amendment with a measured need.
- Human-editable YAML MUST use comment-preserving round trips for setup/edit
  flows and safe reads for boot-time loading.
- The CLI MUST expose validated JSON for host adapters and skills.
- Claude Code is the only v1 host; host-portability work MUST stay limited to
  contracts and adapter seams used by the Claude adapter.
- LLM evaluator outputs MUST be schema-validated before persistence or rendering.
- Boot context MUST be deterministic and token-budgeted.
- Shell verification in this repository MUST use the `rtk` command prefix.

## Development Workflow

- Every feature spec MUST state user value, out-of-scope items, affected layers,
  data ownership, and measurable success criteria.
- Every plan MUST pass the Constitution Check before research and after design.
- Every task list MUST group work by independently testable user story and add
  contract, data, rendering, migration, and semantic-eval tasks when those
  surfaces change.
- Tests that define required behavior MUST be written before implementation for
  contract, persistence, rendering, SRS, boot-context, and evaluator semantics.
- Reviews MUST reject SOLID, DRY, KISS, YAGNI, SoC, composition, or Demeter
  violations unless the plan records the violation and the simpler alternative
  rejected.
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
- Deferred governance questions MUST be recorded as TODO entries in the Sync
  Impact Report and resolved before implementation depends on them.

**Version**: 1.0.0 | **Ratified**: 2026-05-19 | **Last Amended**: 2026-05-19
