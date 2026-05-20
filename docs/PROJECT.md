# language-tutor

## What This Is

An agentic-CLI-native AI language tutor that runs as a Claude Code plugin. The shared Python core owns teaching logic (SRS, evaluation, feedback) while host adapters translate lifecycle events — so the same tutor can later run on Codex, OpenClaw, or Hermess without rewriting pedagogy. v1 targets Claude Code only and ships two skills: vocabulary practice and free writing. Distributed as OSS via the Claude plugin marketplace.

## Core Value

Learner uses it daily and retains vocabulary + improves writing — via SRS-driven drills with structured, host-identical feedback that lives where they already work (the terminal/agentic CLI).

## Requirements

### Validated

(None yet — ship to validate)

### Active

- [ ] Cross-platform Python core with strict layered architecture (host adapter → core → DAL → renderer)
- [ ] Canonical session lifecycle events (SessionStart → BootContext → Exercise → Answer → Feedback → SessionAnalyzed → StatePersisted → SessionEnd)
- [ ] Claude Code host adapter implementing every canonical lifecycle event
- [ ] `get_boot_context()` returns deterministic, token-budgeted learner state
- [ ] YAML profile + preferences (human-editable)
- [ ] SQLite transactional store (answer events, mistake events, SRS items/reviews, session summaries, skill metrics)
- [ ] `tutor-setup` skill — interactive onboarding writes profile/preferences YAML
- [ ] `tutor-vocab` skill — SRS-driven vocab drills, SM-2 algorithm
- [ ] `tutor-writing` skill — free production with structured evaluator feedback
- [ ] `tutor-session-analyzer` skill — emits validated JSON `SessionAnalysis`, persists summary for next boot
- [ ] `tutor-feedback` skill / renderer — markdown + severity emojis from `FeedbackEnvelope`
- [ ] `tutor-progress` skill — show streaks, due-review count, weak patterns
- [ ] LLM generates exercises on-demand for any L2 (no bundled curriculum)
- [ ] Profile-declared learner L1; feedback explanations rendered in learner's L1
- [ ] Plugin installs via Claude plugin marketplace
- [ ] Golden tests for feedback markdown + severity rendering
- [ ] Adapter contract tests prove Claude adapter covers full lifecycle

### Out of Scope

- Other hosts (Codex, OpenClaw, Hermess) — adapter layer stays generic so they can land later, but v1 only ships Claude adapter
- `tutor-reading`, `tutor-listening`, `tutor-speaking`, `tutor-lesson` skills — defer to post-v1
- Audio I/O, speech recognition, TTS — host I/O limitations + scope
- Bundled curated curriculum / language packs — LLM-generated content for v1
- Multi-L1 curated UI translations — explanations via LLM in any L1
- Cloud sync, multi-user, multi-device — local-first, single-user
- Rich analytics dashboards beyond `tutor-progress` text view
- External services / paid APIs other than the Claude API itself — fully local persistence
- Adaptive lesson sequencing across modalities — single-skill sessions for v1
- FSRS / advanced SRS algorithms — SM-2 only for v1

## Context

- **Existing design:** `docs/design.md` lays out the architecture (layered: manifests → adapters → core → DAL → renderers; canonical lifecycle; FeedbackEnvelope; SessionAnalysis; YAML+SQLite split). Treated as working draft — refined during questioning.
- **Builder profile:** Author wants filesystem-level control over the agent setup to experiment with how AI-driven tutoring works in agentic CLIs. The OSS angle lets others tinker too. This is part product, part research artifact.
- **Dogfood language:** Russian / Ukrainian / Slavic — rich morphology (case, aspect, gender) stresses the evaluator and exposes weak prompts early.
- **Pedagogy stance:** LLM-as-judge for evaluation, SM-2 for spacing. Structured contracts (`FeedbackEnvelope`, `SessionAnalysis`) keep behavior identical across future hosts.

## Constraints

- **Tech stack**: Python (≥3.11 recommended) for shared core, adapters, DAL — `sqlite3` stdlib + PyYAML — Why: integrates with target hosts, no extra runtime
- **Persistence**: YAML (human-editable config) + SQLite (transactional state) — Why: source of truth is local files; host memory is cache-only
- **No external services**: No paid APIs (other than Claude itself), no cloud DBs, no telemetry — Why: own-your-data wedge + zero ops burden
- **Distribution**: Claude plugin marketplace — Why: real install UX for OSS users
- **Timeline**: Weeks-long sprint to daily-use MVP — Why: validate the wedge with personal use before broadening
- **Cross-platform**: macOS + Linux dev/runtime; Windows skipped for v1

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| v1 ships Claude adapter only; other hosts deferred | "All 4 hosts" was aspirational. One real adapter + clean abstraction proves the model. | — Pending |
| Language-agnostic engine from day 1, LLM-generated content | No team to curate packs; LLM coverage is the wedge for "any L2 you want" | — Pending |
| Profile-declared L1; feedback in learner's L1 via LLM | Avoids shipping i18n strings; relies on LLM multilingual ability | — Pending |
| MVP skills = vocab + writing only | Two skills cover SRS loop + free production. Reading/listening/speaking deferred. | — Pending |
| SM-2 for SRS (not FSRS, not Leitner) | Battle-tested, simple to implement and golden-test | — Pending |
| Local-only persistence (YAML + SQLite) | Own-your-data wedge; no cloud cost; no auth/sync complexity | — Pending |
| Dogfood with Slavic L2 | Rich morphology stresses evaluator early; finds prompt weaknesses fast | — Pending |
| Distribute via Claude plugin marketplace | Best install UX once available; falls back to git clone | — Pending |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd-transition`):
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone** (via `/gsd:complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-05-19 after initialization*
