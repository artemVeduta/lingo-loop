# Phase 0 Research: language-tutor v1

All technical-context unknowns are resolved.

## Decisions

### Runtime And Project Shape

**Decision**: Use a single synchronous Python 3.12+ package under `src/language_tutor/`, distributed with Claude plugin files in the same repo.

**Rationale**: The tutor is single-user, subprocess-driven, and local. One package keeps install, imports, tests, and marketplace bundling simple while still enforcing layer boundaries through modules and contracts.

**Alternatives considered**: Python 3.11 was broader but weaker against the documented stack target; Python 3.13-only would force avoidable upgrades. Separate `core`, `dal`, and `adapter` packages were rejected as YAGNI for one v1 host.

### CLI As Boundary

**Decision**: Expose one `bin/tutor` Click CLI that reads/writes validated JSON and dispatches hook, setup, vocab, writing, progress, rendering, session, and doctor commands.

**Rationale**: Claude hooks and skills can call the same stable interface. The host adapter translates host events; the core remains host-independent and testable.

**Alternatives considered**: Direct Python imports from skill files are brittle across plugin installs. MCP is unnecessary for synchronous local commands and would add server lifecycle complexity.

### Contracts

**Decision**: Use Pydantic v2 models as the source of truth for `BootContext`, `FeedbackEnvelope`, `SessionAnalysis`, lifecycle events, answer/review records, profile/preferences, controlled error tags, and CLI JSON payloads.

**Rationale**: Pydantic provides runtime validation for LLM output, typed Python contracts, and JSON Schema export for cross-tool contract tests.

**Alternatives considered**: `dataclasses` and `TypedDict` lack runtime validation; a separate `jsonschema` layer duplicates model definitions.

### Persistence

**Decision**: Store profile and preferences in comment-preserving YAML via `ruamel.yaml`; store transactional and derived learning state in SQLite via stdlib `sqlite3`.

**Rationale**: This enforces local data ownership: editable config remains human-friendly, while answer history, reviews, summaries, costs, and metrics stay transactional and append-friendly.

**Alternatives considered**: PyYAML loses comments on round trip. SQLAlchemy/SQLModel add ORM behavior, dependency weight, and async-adjacent patterns that are unnecessary for one local SQLite database.

### Path Resolution

**Decision**: Use platformdirs for config/data/state paths.

**Rationale**: v1 supports macOS and Linux with XDG/platform conventions and avoids hardcoded home directories.

**Alternatives considered**: Manual `~/.config` path handling is easy to get wrong on macOS and harder to test.

### SRS

**Decision**: Implement SM-2 in-tree with a single severity/verdict to quality-grade mapping.

**Rationale**: SM-2 is small, deterministic, in v1 scope, and requires corner-case golden tests. In-tree code avoids licensing and wrong-algorithm risks.

**Alternatives considered**: `anki-sm-2` is AGPL. `py-fsrs` implements FSRS, which is explicitly out of scope.

### Evaluator Strategy

**Decision**: Use `tutor-judge` only for free-writing evaluation and validate its JSON output through `FeedbackEnvelope`. Vocab with accepted answers uses comparator-style evaluation and deterministic SM-2 updates.

**Rationale**: LLM-as-judge is high-risk for Slavic morphology. Schema validation, controlled error tags, confidence, retry/fallback, and semantic fixtures reduce false definitive corrections.

**Alternatives considered**: Letting the main skill produce freeform feedback was rejected because it cannot be contract-tested or aggregated. Updating SRS from writing feedback was rejected because writing mistakes and vocab review state have different ownership.

### Rendering

**Decision**: Implement feedback and boot-context rendering as deterministic Python functions with emoji-capable and ASCII fallback output.

**Rationale**: Rendering is pure transformation from validated models to host-facing markdown and belongs in core/renderer code, not in another LLM-invoked skill.

**Alternatives considered**: A standalone `tutor-feedback` skill was rejected because it adds token cost and nondeterminism to pure rendering.

### Testing

**Decision**: Split tests by determinism: unit/golden/contract/integration/migration tests for deterministic behavior; semantic evaluator fixtures for LLM-backed quality.

**Rationale**: Golden tests should verify stable pure behavior, not brittle live model prose. Evaluator tests need schema pass rates, expected tags, and false-correction thresholds.

**Alternatives considered**: Over-mocking the evaluator hides real failure modes. Running live LLM checks as normal unit tests would be slow, costly, and flaky.

### Distribution

**Decision**: Prepare for Claude plugin marketplace distribution with plugin manifest, skills, hooks, agents, `bin/tutor`, doctor command, and a bundled or isolated Python install flow.

**Rationale**: The user-facing install must work on fresh macOS/Linux systems without global state or a cloud account.

**Alternatives considered**: Requiring a globally installed `language-tutor` command is simpler for contributors but brittle for plugin users.

## Best-Practice Inputs From Existing Docs

- `docs/ARCHITECTURE.md`: one package, thin Claude adapter, event-ledger lifecycle, state persisted per command.
- `docs/STACK.md`: Python 3.12+, Pydantic v2, ruamel.yaml, Click, platformdirs, stdlib sqlite3, pyright, ruff, pytest, syrupy.
- `docs/PITFALLS.md`: controlled tags, evaluator confidence, SM-2 corner tests, boot-context token budget, YAML/SQLite ownership split.
- `docs/SUMMARY.md`: four implementation phases: foundation, vocab loop, writing/judge, analysis/progress/distribution.
