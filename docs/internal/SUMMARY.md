# Project Research Summary

**Project:** language-tutor
**Domain:** Agentic-CLI AI language tutor (Claude Code plugin; Python core + YAML/SQLite; SM-2 SRS; LLM-as-judge; vocab + writing MVP; Slavic L2 dogfood; OSS)
**Researched:** 2026-05-19
**Confidence:** HIGH (stack + architecture + plugin mechanics verified against official Claude Code docs; MEDIUM-HIGH on LLM-as-judge / Slavic GEC reliability)

## Executive Summary

This is an own-your-data, terminal-native language tutor shipped as a Claude Code plugin. Experts in this niche do **not** compete on SRS math (a solved ~80-line algorithm) — they compete on **integration surface, data ownership, and reproducible structured feedback**. The recommended build is a single synchronous Python package (3.12+) distributed as a plugin where each user-facing skill is a thin `SKILL.md` that shells out to one `bin/tutor` Click CLI; state lives in stdlib `sqlite3` + human-editable `ruamel.yaml`, every contract is a Pydantic v2 model (the single source of truth, JSON-Schema-exported for free), and pure functions (SM-2, renderer, boot context) are golden-tested with syrupy + freezegun. No ORM, no async, no web framework, no SRS library (AGPL/wrong-algorithm), no MCP. The architecture is layered (host adapter → core → DAL → renderer) with the lifecycle persisted as an **append-only event ledger in SQLite**, because Claude Code is turn-based and spawns a fresh process per hook/skill call — there is no long-running in-memory session.

The recommended approach makes three corrections to the existing `docs/design.md`: (1) collapse the proposed `core/`/`adapters/`/`dal/` three-package split into one package with module boundaries (YAGNI); (2) treat `tutor-feedback` rendering and `SessionAnalysis` as **internal Python modules**, not standalone skills (rendering is a pure function — wrapping it in a skill wastes an LLM round-trip); (3) build the Claude adapter as a thin `typing.Protocol` shim with **no base class and no method without a caller** — resist designing for hypothetical Codex/OpenClaw/Hermess hosts.

The dominant risk cluster is the LLM-as-judge on **Slavic morphology**: ~10% wrong-feedback rates are catastrophic for a tutor, case/aspect/gender are precisely the hardest GEC classes, and "same input → same output" is not a property even at temperature 0. Mitigation is structural, not hopeful: a frozen controlled error-tag enum (Slavic-aware), an LLM-as-comparator (not judge) path for vocab cards with known reference answers, an explicit golden-tested severity→SM-2 grade table, a hard token budget on boot context and per session, prompt caching from the first API call, and a disciplined test split — golden-test only the deterministic boundary (renderer, SM-2, boot context), use N=3-5 semantic-eval suites for the non-deterministic evaluator. Get all of these into the floor of the build, because every one is far cheaper to design in than to retrofit.

## Key Findings

### Recommended Stack

Single-language synchronous Python core, smallest possible dependency surface for a marketplace plugin. Pydantic is the single source of truth for all contracts; SQLite and YAML own state and config respectively (and never overlap). See `STACK.md` for full version matrix and "what NOT to use" rationale. Confidence HIGH — verified against official Claude Code docs, PyPI, library repos.

**Core technologies (with versions):**
- **Python 3.12+** (target 3.13): runtime for core + adapter + DAL — broadest non-EOL base; do not require 3.13. (Note: PROJECT.md says ≥3.11; STACK recommends ≥3.12 — reconcile during Phase 1.)
- **stdlib `sqlite3`**: transactional single-writer state store — zero install, no ORM needed for ~7 tables, WAL mode.
- **`ruamel.yaml` ^0.18**: human-editable profile/preferences with comment+key-order preservation — PyYAML drops comments. (Note: PROJECT.md/design said PyYAML; ruamel is the corrected pick.)
- **Pydantic v2 ^2.13**: all inter-layer contracts (`BootContext`, `FeedbackEnvelope`, `SessionAnalysis`, `AnswerEvent`), validates LLM JSON on the hot path, exports JSON Schema for `schemas/*.json` for free.
- **`click` ^8.1**: single `bin/tutor` CLI entrypoint invoked from skills via `` !`...` `` injection — not Typer.
- **`platformdirs` ^4.3**: XDG path resolution (macOS + Linux), no hardcoded `~/.config`.
- **In-tree SM-2** (~80 lines): no library — `anki-sm-2` is AGPL (viral), `py-fsrs` is the wrong algorithm.
- **Dev:** `pytest` + `syrupy` (golden) + `freezegun` (deterministic time) + `pyright --strict` + `ruff` + `hatchling` + `uv`.

### Expected Features

v1 surface = exactly the skills that cover the SRS loop + free production. See `FEATURES.md`. Confidence HIGH for SRS/writing patterns, MEDIUM for agentic-CLI differentiators (novel surface).

**Must have (table stakes):**
- SM-2 scheduling with EF + interval + lapse handling, due-queue surfaced at session start.
- Free-form writing eval with **error-span identification + per-error severity (✅🟡🟠🔴) + corrected version + explanation in learner's L1**.
- Controlled (closed) error-tag vocabulary — without it, weak-pattern aggregation is garbage.
- Markdown feedback rendering with severity marks; deterministic for a given envelope.
- Onboarding capturing L1/L2/CEFR/interests/session-length (YAML, re-runnable).
- Progress view: streak (with grace), due count, top weak tags, last-session recap; plus an always-shown end-of-session 3-line summary.

**Should have (differentiators):**
- YAML + SQLite as plain grep-able/git-able files in `$HOME` — the wedge.
- Natural-language skill activation in Claude Code (no app to open).
- Structured `FeedbackEnvelope`/`SessionAnalysis` contracts → reproducible, testable, shell-composable.
- Language-agnostic LLM-generated content (any L2 by editing one YAML field).
- No telemetry / no auth / no cloud — local-only privacy promise.

**Defer (v1.x / v2+):**
- Manual card add, per-card history view, cloze cards, tag-filtered drills (v1.x, dogfood-triggered).
- Reading/listening/speaking/lesson skills, other host adapters, FSRS, user seed-word lists, audio/image cards (v2+).

**Explicit anti-features:** XP/levels/leagues/leaderboards, cloud sync, multi-user, push notifications, built-in curriculum, rich charts, AI personality/mascot, inline freeform chat.

### Architecture Approach

Layered and turn-based. The plugin manifest exposes hooks (SessionStart/SessionEnd), user-facing skills, and one judge subagent; all of them shell out to a single Python CLI. The host adapter (thin Protocol) normalizes Claude hook JSON into canonical `LifecycleEvent` records; the core owns lifecycle/boot/SRS/schema; the DAL owns YAML+SQLite. **State lives in SQLite as an append-only ledger** — write incrementally on every `AnswerRecorded`, never defer persistence to `SessionEnd`. See `ARCHITECTURE.md` for full schemas.

**Major components:**
1. **Plugin surface** (`plugin.json`, `hooks/`, `skills/`, `agents/tutor-judge.md`) — discovery + orchestration only, zero pedagogy.
2. **Host adapter** (`adapters/claude.py` behind a `Protocol`) — hook JSON ↔ canonical lifecycle.
3. **Core engine** (`schemas.py`, `lifecycle.py`, `boot_context.py`, `srs.py`, `feedback.py`, `evaluators.py`, `session.py`) — pure decision logic, golden-tested.
4. **DAL** (`yaml_store.py`, `sqlite_store.py`, `migrations.py`, `repositories.py`, `paths.py`) — CRUD + transactions + XDG paths.
5. **tutor-judge subagent** — isolated-context LLM-as-judge for free writing; returns schema-validated `FeedbackEnvelope`; stateless.

### Critical Pitfalls

1. **LLM-as-judge hallucinates on Slavic morphology** — frozen controlled tag enum, LLM-as-comparator against reference for vocab, two-pass justify for severity ≥ orange, `confidence` field, pinned model + temp 0.
2. **Severity → SM-2 grade mapping breaks** — one golden-tested mapping table; EF floor 1.3, I(1)=1/I(2)=6, reset n=0 on grade<3 but still update EF; free writing does NOT touch SRS (emits `mistake_events` only).
3. **Boot context bloat** — hard `MAX_BOOT_CONTEXT_TOKENS` budget in CI, summarized state only, analyzer's `summary_for_next_boot` as canonical handoff.
4. **Token cost explosion** — prompt caching from first call, per-session token cap, per-call cost logging surfaced in `tutor-progress`.
5. **Golden tests pass but real tutor inconsistent** — test split: golden only deterministic pure functions; N=3-5 semantic-eval for evaluator gated nightly; Pydantic schema validation as boundary backstop.

Also material: premature adapter abstraction (one Protocol, no base class), skill description misfire (directive "Use when..." descriptions, manifest lint), YAML/SQLite dual source of truth (YAML = user-editable, SQLite = derived, one-way sync), first-session friction (<60s to working session, 5 starter words), progress invisibility (auto summary + streak-with-grace), cross-platform install (platformdirs + macOS/Linux CI + `tutor-doctor`).

## Implications for Roadmap

Reconciled into **4 broad phases** for coarse-granularity, weeks-long solo sprint. Strict rule: *no skill ships until its schemas + DAL repos + golden tests exist.*

### Phase 1: Foundation — Scaffold, Schemas, DAL, Lifecycle
Installable plugin scaffold with working SessionStart hook injecting a token-budgeted `BootContext`; all Pydantic schemas + JSON-Schema mirrors; YAML+SQLite DAL with `001_initial.sql` + migration runner; append-only lifecycle ledger; thin Claude adapter Protocol; cross-platform CI; manifest lint.
**Avoids:** boot-context bloat, dual source of truth, premature adapter abstraction, hook unreliability, cross-platform install failure.

### Phase 2: Vocab Loop — SM-2 + Feedback Renderer + tutor-vocab + Setup
Golden-tested in-tree SM-2; severity→grade mapping table; `feedback.py` markdown renderer (golden-tested, ASCII fallback); `tutor-setup` (L1+L2 required, <60s); `tutor-vocab` end-to-end with LLM-as-comparator against reference answers; always-shown end-of-session 3-line summary.
**Avoids:** SM-2 corner-case bugs, severity→grade drift, first-session friction, progress invisibility.

### Phase 3: Writing + Judge — tutor-judge subagent + tutor-writing + Slavic tag vocab
Frozen Slavic-aware `ErrorTag` enum; `tutor-judge` agent returning schema-validated `FeedbackEnvelope` with retry+fallback-to-UNCATEGORIZED; `tutor-writing` end-to-end; prompt caching + per-call cost logging + per-session token cap; ~20-sentence Slavic golden semantic-eval set (UA-GEC-inspired). **Highest-risk phase.**
**Avoids:** Slavic miscorrection, token explosion, test-strategy traps.

### Phase 4: Analysis, Progress, Distribution
`tutor-session-analyzer` (SessionEnd hook, validated `SessionAnalysis`, accumulator input); `tutor-progress` (streak-with-grace, due counts, weak tags, cost); adapter contract test suite; `marketplace.json` + bundled-venv install + `tutor-doctor`; fresh-machine install verification.
**Avoids:** analyzer output drift, streak-loss demotivation, trivially-passing contract tests, OSS install failures.

### Research Flags
- **Phase 3 (Writing + Judge):** highest novelty + risk — needs deep per-phase research (Slavic GEC prompting, severity calibration, semantic-eval methodology).
- **Phase 1 (Foundation):** light flag — verify current plugin install/venv-bundling + hook reliability edge cases against live docs.
- **Phase 2 / Phase 4:** standard patterns; skip research-phase.

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | Verified vs official docs, PyPI, repos+licenses. Minor reconciliation (3.11→3.12; PyYAML→ruamel). |
| Features | HIGH (SRS/writing) / MEDIUM (CLI differentiators) | SRS/WCF well-studied; agentic-CLI surface novel. |
| Architecture | HIGH (plugin model, schemas, build order) / MEDIUM (judge orchestration) | Invocation/hook/lifecycle verified. |
| Pitfalls | HIGH (plugin + SM-2 + token economics) / MEDIUM-HIGH (LLM-judge + Slavic GEC) | Recent docs + post-mortems + pricing. |

**Overall confidence:** HIGH for the build's shape; the Slavic-evaluator quality risk is well-understood and structurally mitigated, but its real-world pass rate is only knowable via dogfood.

### Gaps to Address
- Evaluator real-world accuracy on Slavic — only dogfood reveals true miscorrection rate.
- Determinism vs golden tests — even temp-0 drifts; use the deterministic/semantic split.
- Token economics under real use — per-call cost logging from call #1.
- Stack reconciliation vs PROJECT.md — Python ≥3.11→≥3.12, PyYAML→ruamel; confirm in Phase 1.
- Install mechanism — bundled-venv vs PATH-assumption; verify at Phase 4.
- `tutor-feedback`/`tutor-session-analyzer` as skills vs internal modules — recommend modules; resolve in Phase 1/4.

## Sources

### Primary (HIGH)
- Claude Code official docs — plugins, plugins-reference, skills, hooks, sub-agents.
- PyPI / repos — Pydantic v2.13, ruamel.yaml 0.18, click 8.1, platformdirs 4.3, syrupy, freezegun, hatchling, uv; py-fsrs + anki-sm-2 licenses.
- Python devguide version windows; SuperMemo SM-2 spec; Anthropic API pricing.

### Secondary (MEDIUM)
- LLM-as-judge reliability: arXiv 2412.12509. Russian/Ukrainian GEC: TACL Q19-1001, UA-GEC 2103.16997.
- L2 written corrective feedback studies. Gamification anti-features: arXiv 2203.16175; Duolingo case studies.
- Claude Code skill activation post-mortems. Non-determinism at temp 0: arXiv 2408.04667.

---
*Research completed: 2026-05-19*
*Ready for roadmap: yes*

## Phase 6 — Agent Adapter Setup (2026-05-22)

Adds source-backed, privacy-preserving host setup for Hermes, OpenClaw, Claude,
and Codex with shared capability/lifecycle/conformance contracts. Tutor core
(pedagogy, feedback, progress, DAL) is unchanged and host-independent. Antigravity
out of scope.
