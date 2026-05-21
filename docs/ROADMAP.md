# language-tutor — Capability-Expansion Roadmap

**Date:** 2026-05-21 (updated 2026-05-22)
**Status:** Phase 3 implemented in draft PR #5; Phase 5 (text modalities) implemented on
branch `005-text-modalities` — reading comprehension, guided micro-lessons, and
transcript drills as text-only CLI/skill flows with no new persistence and
`FeedbackEnvelope` unchanged. Scope guardrails: no audio, image, dashboard, host adapter,
or new scheduler.
**Baseline:** Phase 1 = spec `001-build-language-tutor` (full v1) — treated as **complete** (98/98 tasks, 28 tests passing, layered Python package + 4 skills + Claude adapter shipped).

## Goal

Capability expansion: deepen the existing vocab/writing core, add new exercise
modalities, make the scheduling/analysis engine smarter, enrich feedback and
progress, and prove the host-adapter abstraction across multiple hosts —
unlocking audio modalities last.

## Phase Tracker

Check a phase when its exit gate is met. (Granular item boxes live in each phase below.)

- [x] **Phase 1** — Foundation + Core Loop
- [x] **Phase 2** — Vocab Depth
- [x] **Phase 3** — Smarter Engine
- [x] **Phase 4** — Richer Feedback & Progress
- [x] **Phase 5** — Text Modalities
- [ ] **Phase 6** — Host-Capability Layer + Adapter Framework
- [ ] **Phase 6.x** — Adapter Rollout (openclaw / hermess / codex / antigravity)
- [ ] **Phase 7** — Audio Modalities

## Sequencing Decision

**Approach: Core-first, host-last.** Ship all host-independent value before
touching the adapter layer. Rationale: every early checkpoint stays dogfoodable
on Claude Code today; the two real risks (host-capability abstraction, audio)
are deferred until the core engine is rich enough to justify them; the
capability layer lands as one clean architectural phase rather than smeared
across the work.

Rejected: capability-layer-first (architectural risk before core value;
debugging two hard things at once) and breadth-first thin slices (nothing
reaches depth; fuzzy checkpoints; violates focus).

## Cross-Cutting Principles (every phase)

- **Spec-001 rule holds:** no skill ships until its schemas + DAL repositories +
  golden tests exist.
- **Test split held:** golden-test only deterministic boundaries (renderer,
  scheduler math, boot context); N=3–5 semantic-eval suites for
  non-deterministic evaluator paths.
- **Token budget guard** stays enforced in CI.
- **Every phase ends with a working dogfood session** — no phase is "done" until
  it can be used end-to-end.
- **Every new contract** gets a Pydantic model + JSON-Schema mirror.
- **No pedagogy code references a host** — host specifics live only in adapters.
- **Skill-suite coherence audit (any phase that adds a skill):** when a new skill
  lands, re-audit *every* existing skill for fit and sync — no overlapping or
  conflicting `description` triggers, consistent CLI/contract conventions, shared
  `FeedbackEnvelope`/boot-context usage, no duplicated pedagogy, and the combined
  skill-listing stays within Claude Code's description budget. New skills must
  slot into the suite, not fork it.
- **Skill creation is subagent-tested:** every new or edited `SKILL.md` uses the
  local writing-skills helper, external best-practice references required by the
  active spec, and RED/GREEN/REFACTOR pressure evidence from an assigned
  subagent before it ships.

## Phases

### Phase 1 — Foundation + Core Loop ✅ *(complete)*
Spec `001-build-language-tutor` — full v1. Shipped, treated as the baseline this
roadmap builds on.

- [x] Installable Claude Code plugin: manifest, SessionStart/SessionEnd hooks,
  one `bin/tutor` Click CLI, thin Claude adapter Protocol.
- [x] Layered Python package (adapter → core → DAL → renderer); Pydantic
  contracts + JSON-Schema mirrors; append-only SQLite lifecycle ledger + YAML.
- [x] In-tree SM-2; deterministic feedback renderer; frozen Slavic `ErrorTag` enum.
- [x] Four skills live: `tutor-setup`, `tutor-vocab`, `tutor-writing`,
  `tutor-progress`; `tutor-judge` subagent; session analyzer.
- [x] Token-budgeted boot context; golden/contract/integration/semantic tiers.

**Status:** 98/98 spec-001 tasks done; 28 tests passing. Covers all v1
requirements (PLAT, DATA, CTRC, ONBD, VOCB-01..06, WRIT, FDBK, ANLZ, PROG, QUAL,
DIST) — see `REQUIREMENTS.md` traceability.

### Phase 2 — Vocab Depth ✅ *(complete)*
Deepen the existing SRS loop. No host dependency.

- [x] Manual card add (CLI command + `tutor-vocab` path).
- [x] User seed-word lists (JSON in, idempotent import).
- [x] Per-card review history view.
- [x] Tag-filtered drills.
- [x] Cloze card type (new `VocabularyItem` kind + renderer branch).

**Exit gate:** new card kinds golden-tested; seed-list import idempotent;
`tutor-vocab` drills filterable by tag; you can build and drill your own Slavic
deck end-to-end.

### Phase 3 — Smarter Engine ✅ *(implemented)*
Core analysis depth. No host dependency. **SM-2 stays the only algorithm** —
FSRS remains explicitly out of scope (per `REQUIREMENTS.md`); this phase makes
the *existing* SM-2 loop smarter, not pluggable.

- [x] Richer `SessionAnalysis`: cross-session weak-tag targeting feeds the next
  due-queue.
- [x] Adaptive item selection: weak-pattern signal biases which due items and
  which new items surface (selection logic, not a new scheduling algorithm).
- [x] SM-2 parameter tuning surfaced through preferences (intensity already
  exists), golden-tested.

**Exit gate:** weak-tag targeting demonstrably changes which cards surface;
selection logic golden-tested deterministic; SM-2 math unchanged and still
passes its existing golden suite.

**Status:** Implemented via spec `003-smarter-engine`. Adds weak-tag signal
contracts, deterministic weak-aware queue selection, safe boot/progress weak
summaries, intensity queue sizing capped at 60, and schema/contract/golden/
integration coverage. Verification: `rtk uv run pytest`, `rtk uv run pyright`,
and `rtk uv run ruff check .`.

### Phase 4 — Richer Feedback & Progress ✅ *(implemented)*
Renderer / analysis surface. No host dependency. **Text/markdown only** — stays
clear of the banned "rich analytics dashboard" (`REQUIREMENTS.md` Out of Scope):
no charts, no GUI, no web view.

- [x] Per-tag mastery view.
- [x] Text trend / ASCII sparkline; last-N-session recap.
- [x] Exportable report (markdown / JSON, terminal-printable).

**Exit gate:** progress views golden-tested deterministic; export round-trips;
output is text/markdown only (no graphical surface); progress view <5s on one
year of daily history (spec-001 perf bar preserved).

**Status:** Implemented via spec `004-richer-feedback-progress`. Adds validated
progress report/request/markdown contracts, schema mirrors, aggregate-safe DAL
reads, read-performance indexes, deterministic markdown rendering, CLI JSON and
markdown export paths, `tutor-progress` routing updates, skill pressure evidence,
and unit/golden/contract/integration/migration/performance coverage.
Verification: `rtk uv run pytest`, `rtk uv run pyright`, and
`rtk uv run ruff check .`.

### Phase 5 — Text Modalities + Skill Authoring
First new exercise types plus full project skill review/rewrite. Text-only,
runs on any host.

- [x] Inventory and review every project `SKILL.md` under `.agents/skills/` and
  `skills/`, including active Speckit skills used during the phase.
- [x] Rewrite existing skills where needed using the local writing-skills helper,
  required external skill-authoring references, and assigned subagent
  RED/GREEN/REFACTOR pressure evidence.
- [x] Confirm trigger descriptions, frontmatter, progressive disclosure,
  CLI/contract conventions, and no duplicated pedagogy across the full skill
  suite before adding new skills.
- [x] `tutor-reading` — LLM-generated passage + comprehension questions,
  feedback via the existing `FeedbackEnvelope`.
- [x] `tutor-lesson` — guided micro-lesson.
- [x] Dictation / transcript drill as a text-based "listening" proxy.

**Exit gate:** 100% of project `SKILL.md` files are inventoried and either
confirmed compliant or rewritten with subagent evidence; each new skill reuses
`FeedbackEnvelope` + judge contract, emits `mistake_events`, and introduces no
new persistence path; **skill-suite coherence audit passes** (existing
tutor-vocab/writing/progress/setup and Speckit skills re-checked for trigger
overlap and convention sync); two new skills live and dogfoodable.

### Phase 6 — Host-Capability Layer + Adapter Framework
Architecture only — no new host lands in this phase.

Two axes of capability, not one:

- [ ] **I/O modality:** capability descriptor on the adapter Protocol
  (`supports: text | audio | image`, plus per-host I/O quirks).
- [ ] **Lifecycle availability:** the existing `supports_lifecycle(event_name)`
  seam formalized — not every host has Claude's SessionStart/SessionEnd hooks.
  Hosts lacking hook-driven boot must declare it; core must build/persist boot
  context through an alternate trigger (e.g. first-message, explicit command)
  without assuming a hook fired. This is the real risk in Phase 6, above I/O.
- [ ] Skills gate behavior on declared capabilities; pedagogy stays host-blind.
- [ ] Generalize the adapter-contract test suite into a reusable **conformance
  kit** every adapter must pass (covers both axes).

**Exit gate:** the existing Claude adapter is re-expressed through the
capability layer (both axes) with zero pedagogy change; conformance kit green;
boot context provably builds on a host with no SessionStart hook (simulated).

### Phase 6.x — Adapter Rollout
Four new adapters (Claude already shipped in Phase 1). Each is an independent
slice that passes the conformance kit; ship/dogfood per adapter — no big-bang.
**Order decided at phase entry** (not fixed here).

- [ ] **openclaw**
- [ ] **hermess** — Nous Research Hermes agent. Profile-distributions doc feeds
  how the learner profile maps to host:
  https://hermes-agent.nousresearch.com/docs/user-guide/profile-distributions
- [ ] **codex** — via Codex CLI / desktop app.
- [ ] **antigravity** — via Antigravity CLI.

**Exit gate (per adapter):** passes the full lifecycle conformance kit; declares
its real capabilities (both axes); the same pedagogy runs unchanged; **ships a
working per-host install/distribution path** (the Claude marketplace path does
not apply to other hosts — hermess profile-distributions, codex plugin format,
etc.) verified on a fresh environment, mirroring spec-001 `DIST-01/02` per host.

Maps to `REQUIREMENTS.md` HOST-01 (codex), HOST-02 (openclaw), HOST-03
(hermess), HOST-04 (antigravity).

### Phase 7 — Audio Modalities *(needs research)*
Rides the Phase 6 capability layer and whichever adapters declared audio support
(e.g. desktop apps, or Telegram-fronted openclaw/hermess — confirmed per adapter
in Phase 6.x, not assumed here).

- [ ] `tutor-listening`, `tutor-speaking`.
- [ ] Audio / image cards.

**Exit gate:** audio skills are capability-gated and degrade gracefully (hidden)
on text-only hosts; **skill-suite coherence audit passes** (full suite re-checked
with audio skills added); semantic-eval set covers pronunciation / listening
quality.

## Dependency Spine

- Phases 2, 3, 4 are independent core deepening — reorderable.
- Phase 5 depends on nothing new.
- Phase 6 (capability layer) gates Phase 6.x (adapters) gates Phase 7 (audio).
- Audio is last by construction: it needs the capability layer, which is only
  worth abstracting once a second adapter exists to validate it.

## Process Per Phase

Each phase runs its own spec → plan → implementation cycle. This document is the
coarse roadmap; per-phase detail is produced when the phase starts.
