# language-tutor — Capability-Expansion Roadmap

**Date:** 2026-05-21 (updated 2026-05-22)
**Status:** Phase 6 (agent adapter setup) implemented on branch
`006-agent-adapter-setup` — source-backed host setup for Hermes, OpenClaw, Claude,
and Codex with shared capability/lifecycle/conformance contracts; automated gates,
pyright, and ruff green. Antigravity excluded. Phase 5 (text modalities) shipped on
`005-text-modalities`; Phase 3 in draft PR #5.
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
- [x] **Phase 6** — Host-Capability Layer + Adapter Framework
- [x] **Phase 6.x** — Adapter Rollout (hermes / openclaw / claude / codex; antigravity excluded)
- [ ] **Phase 7** — Hook-Free Incremental Lifecycle (fix)
- [ ] **Phase 8** — Audio Modalities

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
integration coverage. Verification: `uv run pytest`, `uv run pyright`,
and `uv run ruff check .`.

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
Verification: `uv run pytest`, `uv run pyright`, and
`uv run ruff check .`.

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

### Phase 6 — Host-Capability Layer + Adapter Framework ✅ *(implemented via spec `006-agent-adapter-setup`)*
Two axes of capability, not one:

- [x] **I/O modality:** `AdapterCapabilityProfile` declares `text_support` (+ audio/image locked unsupported for this spec) plus per-host quirks.
- [x] **Lifecycle availability:** `lifecycle_start`/`lifecycle_end` + `boot_context_trigger` formalized; `boot_context.select_boot_trigger` builds boot context through hook / explicit-command / first-message / manual triggers without assuming a hook fired.
- [x] Capability profiles gate flows; pedagogy stays host-blind (`run_conformance`).
- [x] Adapter-contract suite generalized into a reusable conformance kit (`tests/adapter_contract/test_conformance_kit.py`, `tests/integration/test_host_text_flows.py`).

**Exit gate:** MET — Claude re-expressed through the capability layer with zero
pedagogy change; conformance kit green; boot context builds on non-hook hosts
(Hermes explicit-command, OpenClaw first-message) verified by tests.

### Phase 6.x — Adapter Rollout ✅ *(implemented via spec `006-agent-adapter-setup`)*
Each host is an independent sub-agent-owned slice that passes the conformance
kit. Antigravity is **excluded** (dropped from scope by spec 006).

- [x] **claude** — existing plugin baseline, re-expressed + modernized (`plugin validate --strict` passes).
- [x] **openclaw** — Node/TS ESM plugin package (`openclaw-plugin/`).
- [x] **hermes** — git-backed profile distribution (`hermes-profile/`).
- [x] **codex** — local-marketplace plugin (`.codex-plugin/` + `.agents/plugins/`).
- [x] ~~**antigravity**~~ — excluded; rejected at the `HostId` schema layer.

**Exit gate (per adapter):** automated conformance + packaging-privacy gates
green; capabilities declared (both axes); pedagogy unchanged; per-host
install/distribution path shipped.

Maps to `REQUIREMENTS.md` HOST-01 (codex), HOST-02 (openclaw), HOST-03 (hermes);
HOST-04 (antigravity) is out of scope.

### Phase 7 — Hook-Free Incremental Lifecycle *(fix)*
Corrects the Phase 6/6.x lifecycle model. Source: spec
`006-agent-adapter-setup/HANDOFF-incremental-lifecycle-no-hooks.md`. Drops
host-specific hooks entirely; tutor correctness comes from first-message boot
plus incremental DB persistence. No new modality, no host dependency beyond the
shared contracts. Enforces Constitution **Principle IX — Hook-Free Incremental
Lifecycle** (v1.2.0).

Why: Codex has no documented true `SessionEnd` (`Stop` is turn-scoped); hooks can
be disabled/uninstalled and behave differently per host. One no-hook lifecycle is
simpler and gives stronger data safety than shutdown hooks.

- [x] Add `sessions` + `checkpoints` models, schemas, and migrations.
- [x] Repository methods: `open_session`, `touch_session`, `record_checkpoint`,
  `recent_sessions`, and `close_session` (explicit manual close only).
- [x] `session-start` CLI mints `session_id` and returns it alongside boot
  context; existing `boot-context` stays unchanged for backward compatibility.
- [x] Skills/adapters call `session-start` on first tutor interaction; the
  agent threads the returned `session_id` into every later call. Checkpoint
  writes on every lesson/exercise/prompt presentation; existing answer-event
  persistence is anchored to the active `session_id`.
- [x] Capability profiles for claude/codex/openclaw/hermes set
  `lifecycle_start=first_message`, `lifecycle_end=not_available`,
  `persistence_mode=incremental_checkpoint`,
  `boot_context_trigger=first_tutor_message`, plus `session_id_source`.
- [x] Removed `hooks/` (deleted) and dropped hook lifecycle assertions from
  capability/conformance/packaging surface.
- [x] CLI write paths commit durably (`open_session`, `touch_session`,
  `record_checkpoint`, `close_session` each open their own transaction).
- [x] `session-close` is the only path that flips `status=closed` / sets
  `closed_at`. `session-end` is retained as a maintenance command.

**Exit gate:** no host setup profile claims hook lifecycle as target architecture;
no host package requires hooks for correctness; conformance verifies first-message
boot + checkpoint persistence for all hosts; mid-lesson app close leaves data
through the last checkpoint intact (new session on next boot, prior session read
as stale history); packaging-privacy tests confirm checkpoint/session files
package no user-owned data; pytest, pyright, ruff green. Migration updates
`README.md`, Phase 6 lifecycle wording, host-setup profiles, manual-install
reports, and adapter/packaging tests listed in the HANDOFF.

### Phase 8 — Audio Modalities *(needs research)*
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
- Phase 6 (capability layer) gates Phase 6.x (adapters) gates Phase 7
  (hook-free lifecycle fix) gates Phase 7 (audio).
- Phase 7 fixes the 6/6.x lifecycle before audio rides the same boot/persist path.
- Audio is last by construction: it needs the capability layer, which is only
  worth abstracting once a second adapter exists to validate it.

## Process Per Phase

Each phase runs its own spec → plan → implementation cycle. This document is the
coarse roadmap; per-phase detail is produced when the phase starts.

## Phase 6 Status — Agent Adapter Setup (2026-05-22)

Implemented: source-backed host setup for Hermes, OpenClaw, Claude, and Codex.
Shared capability/lifecycle/conformance contracts, host CLI group, per-host
distribution surfaces, subagent + manual install reports, and main-agent review.
Automated gates (schema, packaging privacy, adapter conformance, host text flows)
pass; pyright and ruff clean. Manual provider verification is BLOCKED where host
CLIs are unavailable locally (`hermes`, `clawhub`) — see
`specs/006-agent-adapter-setup/manual-install-reports/`. Antigravity excluded.
