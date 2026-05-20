# language-tutor — Capability-Expansion Roadmap

**Date:** 2026-05-21
**Status:** Approved design (pending user spec review)
**Baseline:** Phase 1 = spec `001-build-language-tutor` (full v1) — treated as **complete** (98/98 tasks, 28 tests passing, layered Python package + 4 skills + Claude adapter shipped).

## Goal

Capability expansion: deepen the existing vocab/writing core, add new exercise
modalities, make the scheduling/analysis engine smarter, enrich feedback and
progress, and prove the host-adapter abstraction across multiple hosts —
unlocking audio modalities last.

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

## Phases

### Phase 2 — Vocab Depth
Deepen the existing SRS loop. No host dependency.

- Manual card add (CLI command + `tutor-vocab` path).
- User seed-word lists (YAML in, idempotent import).
- Per-card review history view.
- Tag-filtered drills.
- Cloze card type (new `VocabularyItem` kind + renderer branch).

**Exit gate:** new card kinds golden-tested; seed-list import idempotent;
`tutor-vocab` drills filterable by tag; you can build and drill your own Slavic
deck end-to-end.

### Phase 3 — Smarter Engine
Core analysis depth. No host dependency. **SM-2 stays the only algorithm** —
FSRS remains explicitly out of scope (per `REQUIREMENTS.md`); this phase makes
the *existing* SM-2 loop smarter, not pluggable.

- Richer `SessionAnalysis`: cross-session weak-tag targeting feeds the next
  due-queue.
- Adaptive item selection: weak-pattern signal biases which due items and which
  new items surface (selection logic, not a new scheduling algorithm).
- SM-2 parameter tuning surfaced through preferences (intensity already exists),
  golden-tested.

**Exit gate:** weak-tag targeting demonstrably changes which cards surface;
selection logic golden-tested deterministic; SM-2 math unchanged and still
passes its existing golden suite.

### Phase 4 — Richer Feedback & Progress
Renderer / analysis surface. No host dependency. **Text/markdown only** — stays
clear of the banned "rich analytics dashboard" (`REQUIREMENTS.md` Out of Scope):
no charts, no GUI, no web view.

- Per-tag mastery view.
- Text trend / ASCII sparkline; last-N-session recap.
- Exportable report (markdown / JSON, terminal-printable).

**Exit gate:** progress views golden-tested deterministic; export round-trips;
output is text/markdown only (no graphical surface); progress view <5s on one
year of daily history (spec-001 perf bar preserved).

### Phase 5 — Text Modalities
First new exercise types. Text-only, runs on any host.

- `tutor-reading` — LLM-generated passage + comprehension questions, feedback
  via the existing `FeedbackEnvelope`.
- `tutor-lesson` — guided micro-lesson.
- Dictation / transcript drill as a text-based "listening" proxy.

**Exit gate:** each new skill reuses `FeedbackEnvelope` + judge contract; emits
`mistake_events`; introduces no new persistence path; **skill-suite coherence
audit passes** (existing tutor-vocab/writing/progress/setup re-checked for
trigger overlap and convention sync); two new skills live and dogfoodable.

### Phase 6 — Host-Capability Layer + Adapter Framework
Architecture only — no new host lands in this phase.

Two axes of capability, not one:

- **I/O modality:** capability descriptor on the adapter Protocol
  (`supports: text | audio | image`, plus per-host I/O quirks).
- **Lifecycle availability:** the existing `supports_lifecycle(event_name)` seam
  formalized — not every host has Claude's SessionStart/SessionEnd hooks. Hosts
  lacking hook-driven boot must declare it; core must build/persist boot context
  through an alternate trigger (e.g. first-message, explicit command) without
  assuming a hook fired. This is the real risk in Phase 6, above I/O.
- Skills gate behavior on declared capabilities; pedagogy stays host-blind.
- Generalize the adapter-contract test suite into a reusable **conformance kit**
  every adapter must pass (covers both axes).

**Exit gate:** the existing Claude adapter is re-expressed through the
capability layer (both axes) with zero pedagogy change; conformance kit green;
boot context provably builds on a host with no SessionStart hook (simulated).

### Phase 6.x — Adapter Rollout
Four new adapters (Claude already shipped in Phase 1). Each is an independent
slice that passes the conformance kit; ship/dogfood per adapter — no big-bang.
**Order decided at phase entry** (not fixed here).

- **openclaw**
- **hermess** — Nous Research Hermes agent. Profile-distributions doc feeds how
  the learner profile maps to host:
  https://hermes-agent.nousresearch.com/docs/user-guide/profile-distributions
- **codex** — via Codex CLI / desktop app.
- **antigravity** — via Antigravity CLI.

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

- `tutor-listening`, `tutor-speaking`.
- Audio / image cards.

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
