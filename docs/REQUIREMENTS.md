# Requirements: language-tutor

**Defined:** 2026-05-19
**Core Value:** Learner uses it daily and retains vocabulary + improves writing — via SRS-driven drills with structured, host-identical feedback that lives in the terminal.

## v1 Requirements

Requirements for initial release. Each maps to roadmap phases.

### Platform & Lifecycle

- [ ] **PLAT-01**: Plugin installs into Claude Code and is discoverable (manifest + skills register)
- [ ] **PLAT-02**: `SessionStart` hook injects a deterministic, token-budgeted boot context into the session
- [ ] **PLAT-03**: `SessionEnd` hook triggers session analysis and final state persistence
- [ ] **PLAT-04**: Canonical session lifecycle events are defined and the Claude adapter maps every required event
- [ ] **PLAT-05**: A single `bin/tutor` CLI dispatches all tutor operations and emits validated JSON
- [ ] **PLAT-06**: Plugin installs and runs on both macOS and Linux

### Data & Persistence

- [ ] **DATA-01**: Learner profile (L1, L2, CEFR target, interests, constraints) is stored in human-editable YAML
- [ ] **DATA-02**: Preferences (session length, review intensity, feedback verbosity) are stored in human-editable YAML
- [ ] **DATA-03**: SQLite schema is created and migrated via a versioned migration runner
- [ ] **DATA-04**: Answer events and mistake events are persisted append-only as they occur
- [ ] **DATA-05**: SRS items and reviews are persisted with transactional updates
- [ ] **DATA-06**: Session summaries and skill metrics are persisted
- [ ] **DATA-07**: YAML is the only user-editable source of truth; SQLite-derived metrics are recalculable (no dual ownership)
- [ ] **DATA-08**: Data files resolve via XDG/platform paths (no hardcoded home paths)

### Contracts & Schemas

- [ ] **CTRC-01**: `BootContext` is a validated schema with an enforced token/character budget
- [ ] **CTRC-02**: `FeedbackEnvelope` is a validated schema (verdict, corrected answer, error spans, severity, explanation, tags, srs updates)
- [ ] **CTRC-03**: `SessionAnalysis` is a validated schema and invalid analyzer output is rejected before persistence
- [ ] **CTRC-04**: Error tags are a frozen controlled vocabulary covering Slavic morphology (case, aspect, gender/agreement, animacy, verbs of motion)

### Onboarding & Profile

- [ ] **ONBD-01**: `tutor-setup` runs an interactive onboarding requiring only L1 + L2, defaulting the rest
- [ ] **ONBD-02**: A learner reaches a working first vocab session in under ~60 seconds from setup
- [ ] **ONBD-03**: `tutor-setup` is re-runnable to edit profile/preferences

### Vocabulary (SRS)

- [ ] **VOCB-01**: SM-2 scheduling computes intervals, ease factor, and lapse handling correctly
- [ ] **VOCB-02**: Due SRS items are surfaced at session start
- [ ] **VOCB-03**: `tutor-vocab` presents a recall exercise, captures the answer, and evaluates it against a reference (LLM-as-comparator)
- [ ] **VOCB-04**: Evaluator verdict maps to an SM-2 quality grade via an explicit, golden-tested table
- [ ] **VOCB-05**: SRS item state updates transactionally after each graded answer
- [ ] **VOCB-06**: Exercise content is LLM-generated for any target language (no bundled curriculum)

### Writing

- [ ] **WRIT-01**: `tutor-writing` accepts a free-form passage in the target language and elicits a structured evaluation
- [ ] **WRIT-02**: `tutor-judge` subagent returns a schema-validated `FeedbackEnvelope`; invalid output retries then falls back to UNCATEGORIZED
- [ ] **WRIT-03**: Feedback identifies error spans, assigns severity, and explains in the learner's L1
- [ ] **WRIT-04**: Writing mistakes persist as mistake events and do NOT mutate SRS items
- [ ] **WRIT-05**: Evaluator calls use prompt caching and respect a per-session token cap; per-call cost is logged

### Feedback Rendering

- [ ] **FDBK-01**: A `FeedbackEnvelope` renders to deterministic markdown with severity marks (✅🟡🟠🔴)
- [ ] **FDBK-02**: Rendering output is golden-tested and identical for a given envelope regardless of host
- [ ] **FDBK-03**: Rendering degrades gracefully where emoji/markdown is unsupported (ASCII fallback)

### Analysis & Progress

- [ ] **ANLZ-01**: `tutor-session-analyzer` produces a validated `SessionAnalysis` at session end
- [ ] **ANLZ-02**: The analyzer emits a concise `summary_for_next_boot` consumed by the next boot context
- [ ] **PROG-01**: `tutor-progress` shows streak (with grace), due-review count, and top weak patterns
- [ ] **PROG-02**: Each session ends with an always-shown short summary (not gated behind a command)
- [ ] **PROG-03**: `tutor-progress` surfaces month-to-date token cost

### Quality & Distribution

- [ ] **QUAL-01**: Golden tests cover SM-2 math, feedback markdown, severity mapping, and boot-context format
- [ ] **QUAL-02**: Adapter contract tests fail if the Claude adapter stops covering a required lifecycle event
- [ ] **QUAL-03**: A Slavic-L2 semantic-eval fixture set validates evaluator quality (verdict/span/tag thresholds)
- [ ] **DIST-01**: Plugin is publishable to the Claude plugin marketplace (manifest + bundled runtime)
- [ ] **DIST-02**: A `tutor-doctor` / install check verifies environment readiness on a fresh machine

## v2 Requirements

Deferred to future release. Tracked but not in current roadmap.

### Additional Modalities

- **READ-01**: `tutor-reading` comprehension practice
- **LIST-01**: `tutor-listening` practice
- **SPEK-01**: `tutor-speaking` practice (requires audio I/O)
- **LESN-01**: `tutor-lesson` compound multi-skill sessions with adaptive routing

### Additional Hosts

- **HOST-01**: Codex host adapter (Codex CLI / desktop app)
- **HOST-02**: OpenClaw host adapter
- **HOST-03**: Hermess host adapter ([profile-distributions](https://hermes-agent.nousresearch.com/docs/user-guide/profile-distributions))
- **HOST-04**: Antigravity host adapter (Antigravity CLI)
- **HOST-CAP**: Host-capability layer — adapters declare I/O modality (text/audio/image) and lifecycle-event availability; skills gate on capabilities; reusable conformance kit
- **HOST-DIST**: Per-host install/distribution path (non-Claude hosts; verified fresh-environment)

### Vocab Enhancements

- **VOCB-07**: Manual card add flow
- **VOCB-08**: Cloze-deletion exercise type
- **VOCB-09**: Tag-filtered / weak-pattern-targeted drills
- **VOCB-10**: User-supplied seed word lists

## Out of Scope

Explicitly excluded. Documented to prevent scope creep.

| Feature | Reason |
|---------|--------|
| XP / levels / leagues / leaderboards | Gamification harms intrinsic motivation; no one to compete with in solo OSS tool |
| Cloud sync / multi-device | Local-first wedge; adds auth + ops + cost |
| Multi-user | Single-learner tool; multi-user breaks the data-ownership model |
| Built-in curated curriculum | LLM-generated content is the language-agnostic wedge |
| Multi-L1 curated UI translations | Explanations rendered in any L1 via LLM |
| Audio / TTS / speech recognition | Host I/O limits + scope; speaking deferred to v2 |
| FSRS / advanced SRS | SM-2 sufficient and simpler to golden-test for v1 |
| Rich analytics dashboards | Text `tutor-progress` view covers v1 motivation needs |
| External services / paid APIs (beyond Claude) | Own-your-data + zero-ops constraint |
| Windows support | macOS + Linux only for v1 |
| Standalone `tutor-feedback` skill | Rendering is a pure function (module), not an LLM-invoked skill |

## Traceability

Which phases cover which requirements. See
[ROADMAP.md](ROADMAP.md) for phase detail.

| Requirement | Phase | Status |
|-------------|-------|--------|
| All v1 (PLAT, DATA, CTRC, ONBD, VOCB-01..06, WRIT, FDBK, ANLZ, PROG, QUAL, DIST) | Phase 1 (spec 001) | ✅ Done |
| VOCB-07 manual card add | Phase 2 | Planned |
| VOCB-08 cloze exercise | Phase 2 | Planned |
| VOCB-09 tag-filtered / weak-targeted drills | Phase 2 (filter) + Phase 3 (targeting) | Planned |
| VOCB-10 seed word lists | Phase 2 | Planned |
| (richer SessionAnalysis + adaptive selection, extends ANLZ-01/02) | Phase 3 | Planned |
| (deeper text progress + export, extends PROG-01..03) | Phase 4 | Planned |
| READ-01 tutor-reading | Phase 5 | Planned |
| LESN-01 tutor-lesson | Phase 5 | Planned |
| HOST-CAP capability layer | Phase 6 | Planned |
| HOST-01 codex | Phase 6.x | Planned |
| HOST-02 openclaw | Phase 6.x | Planned |
| HOST-03 hermess | Phase 6.x | Planned |
| HOST-04 antigravity | Phase 6.x | Planned |
| HOST-DIST per-host distribution | Phase 6.x | Planned |
| LIST-01 tutor-listening | Phase 7 (needs audio-capable host) | Planned |
| SPEK-01 tutor-speaking | Phase 7 (needs audio-capable host) | Planned |

**Coverage:**
- v1 requirements: 38 total → all in Phase 1 (complete)
- v2 requirements: mapped to Phases 2–7
- Unmapped: 0
- Explicitly excluded: FSRS / advanced SRS (SM-2 remains sole algorithm)

---
*Requirements defined: 2026-05-19*
*Last updated: 2026-05-19 after initial definition*
