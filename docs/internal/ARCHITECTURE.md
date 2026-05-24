# Architecture Research

**Domain:** Agentic-CLI plugin — AI language tutor (Claude Code, v1)
**Researched:** 2026-05-19
**Confidence:** HIGH on plugin invocation model, schemas, build order; MEDIUM on Claude-as-judge orchestration patterns (one verified pattern, alternatives noted).

---

## Executive Verdict on the Existing Design

`docs/design.md`'s layered model (manifests → adapters → core → DAL → skills) is **sound** but needs three adjustments for v1:

1. **Adapter layer is real, not theoretical** — even with one host, define the Protocol now so Claude code paths don't leak pedagogy. But: **the Claude adapter is mostly trivial** for v1 because hooks + skills already deliver the canonical lifecycle. The adapter shrinks to thin shims (event normalization + path resolution). Resist the urge to overbuild it.
2. **Lifecycle is NOT executed by one long-running process.** Claude Code is turn-based. `SessionStart` and `SessionEnd` are *hook events*; the rest of the lifecycle is enacted by the *user's conversation with skills*. Treat lifecycle as a state-machine ledger persisted in SQLite, not in-memory.
3. **"Skills" overloaded.** Some lifecycle stages (Setup, Vocab, Writing, Progress) are user-facing skills. Others (FeedbackEnvelope rendering, SessionAnalysis) are *internal helper modules* called from Python — not standalone `SKILL.md`s. The design.md skill list conflates these. Reorganize: user-facing skills vs core Python modules.

---

## Standard Architecture

### Smarter Engine Boundaries

Weak-tag signal ranking and queue selection live in `src/language_tutor/vocab.py`.
`src/language_tutor/dal/repositories.py` only supplies bounded source rows and
candidate cards. `src/language_tutor/schemas.py` owns the JSON contracts for
signals, reasons, policies, and session plans. `boot_context.py` and
`progress.py` render the shared weak-signal helper output without reading raw
events or feedback prose.

### System Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                      CLAUDE CODE HOST PROCESS                        │
│  (turn-based: user prompt → tool calls → response → repeat)          │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │              PLUGIN MANIFEST  .claude-plugin/plugin.json        │ │
│  └────────────────────────────────────────────────────────────────┘ │
│       │              │                │                   │         │
│       ▼              ▼                ▼                   ▼         │
│  ┌─────────┐  ┌─────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │ HOOKS   │  │ SKILLS      │  │ AGENTS       │  │ (no MCP v1)  │  │
│  │ ──────  │  │ ──────      │  │ ──────       │  │              │  │
│  │ Session │  │ tutor-setup │  │ tutor-judge  │  │              │  │
│  │ Start   │  │ tutor-vocab │  │ (subagent    │  │              │  │
│  │ Session │  │ tutor-      │  │  for         │  │              │  │
│  │ End     │  │  writing    │  │  evaluation) │  │              │  │
│  │         │  │ tutor-      │  │              │  │              │  │
│  │         │  │  progress   │  │              │  │              │  │
│  └────┬────┘  └──────┬──────┘  └──────┬───────┘  └──────────────┘  │
│       │              │                │                              │
│       │   shell out  │  !`python`     │                              │
│       │   to Python  │  injection     │                              │
│       └──────────────┴────────────────┘                              │
│                      │                                               │
└──────────────────────┼───────────────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────────────┐
│                     HOST ADAPTER LAYER (Python)                      │
│  language_tutor_adapters/claude.py                                   │
│  - parses hook JSON stdin                                            │
│  - resolves ${CLAUDE_PLUGIN_ROOT}, ${CLAUDE_PLUGIN_DATA} paths       │
│  - emits SessionStart additionalContext (boot context)               │
│  - normalizes skill-driven events into LifecycleEvent records        │
└────────────────────────────────────────────────┬────────────────────┘
                                                 │
                                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        SHARED CORE ENGINE (Python)                   │
│  core/language_tutor/                                                │
│  ┌───────────────┐  ┌─────────────┐  ┌──────────────┐               │
│  │ lifecycle.py  │  │ schemas.py  │  │ feedback.py  │               │
│  │ boot_         │  │ (Pydantic)  │  │ (envelope    │               │
│  │  context.py   │  │             │  │  builder)    │               │
│  └───────────────┘  └─────────────┘  └──────────────┘               │
│  ┌───────────────┐  ┌─────────────┐  ┌──────────────┐               │
│  │ srs.py        │  │ session.py  │  │ evaluators.py│               │
│  │ (SM-2)        │  │ (state      │  │ (judge       │               │
│  │               │  │  machine)   │  │  prompt mgmt)│               │
│  └───────────────┘  └─────────────┘  └──────────────┘               │
└────────────────────────────────────────────────┬────────────────────┘
                                                 │
                                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    DATA ACCESS LAYER (Python)                        │
│  dal/language_tutor_dal/                                             │
│  ┌────────────────┐  ┌──────────────────┐  ┌──────────────────┐    │
│  │ yaml_store.py  │  │ sqlite_store.py  │  │ repositories.py  │    │
│  │ profile,       │  │ connection,      │  │ AnswerRepo,      │    │
│  │ preferences    │  │ migrations,      │  │ SrsRepo,         │    │
│  │                │  │ transactions     │  │ SessionRepo, …   │    │
│  └────────────────┘  └──────────────────┘  └──────────────────┘    │
└────────────────────────────────────────────────┬────────────────────┘
                                                 │
                                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│                     LOCAL FILESYSTEM (XDG-compliant)                 │
│  ${XDG_CONFIG_HOME:-~/.config}/language-tutor/                       │
│    profile.yaml          ← human-editable                            │
│    preferences.yaml      ← human-editable                            │
│  ${XDG_DATA_HOME:-~/.local/share}/language-tutor/                    │
│    tutor.sqlite          ← transactional state                       │
│    backups/              ← timestamped snapshots                     │
│  ${XDG_STATE_HOME:-~/.local/state}/language-tutor/                   │
│    logs/                 ← debug, eval traces                        │
└─────────────────────────────────────────────────────────────────────┘
```

### Component Responsibilities

| Component | Owns | Talks To | Does NOT |
|-----------|------|----------|----------|
| **plugin.json** | Plugin metadata, component discovery | (Claude Code reads it) | Contain logic |
| **hooks/session-start** | Inject `BootContext` as `additionalContext` JSON on session start | Python core via shell | Mutate learner state, render feedback |
| **hooks/session-end** | Run `tutor-session-analyzer`, persist `SessionAnalysis`, close SQLite | Python core via shell | Block session end on errors (non-blocking) |
| **Skills (user-facing)** | Conversational UX: `tutor-setup`, `tutor-vocab`, `tutor-writing`, `tutor-progress` | Python core via `` !`python -m language_tutor.cli ...` `` dynamic injection | Hold learner state, decide pedagogy |
| **tutor-judge subagent** | Runs evaluation prompt in isolated context, returns `FeedbackEnvelope` JSON | Called via Task tool from `tutor-writing` skill | Persist anything; pure function |
| **Host adapter (Python)** | Translate Claude hook JSON ↔ canonical `LifecycleEvent` | Core engine | Pedagogy, SRS math, feedback semantics |
| **Core engine** | Lifecycle state machine, boot context selection, SRS math, schema validation | DAL | Read hook JSON, render markdown, call LLMs directly |
| **DAL** | YAML I/O, SQLite migrations, transactional writes, repository interfaces | Filesystem | Apply pedagogy, validate semantics |
| **Renderers (`feedback.py`)** | `FeedbackEnvelope` → markdown + emojis | (called by skill scripts) | Decide severity, choose tags |

---

## Recommended Project Structure

```
language-tutor/
├── .claude-plugin/
│   └── plugin.json                 # plugin manifest
├── .claude-plugin/marketplace.json # only if this repo IS the marketplace; usually elsewhere
│
├── hooks/
│   ├── hooks.json                  # event → script bindings (event-loop level)
│   ├── session-start.sh            # thin shim; calls python core
│   ├── session-end.sh              # thin shim; calls python core
│   └── README.md
│
├── skills/                         # user-facing slash commands
│   ├── tutor-setup/
│   │   ├── SKILL.md                # /tutor-setup → onboarding wizard
│   │   └── scripts/
│   │       └── run.py              # invoked via !`python ...`
│   ├── tutor-vocab/
│   │   ├── SKILL.md                # /tutor-vocab → SRS drill loop
│   │   └── scripts/
│   ├── tutor-writing/
│   │   ├── SKILL.md                # /tutor-writing → free production w/ judge
│   │   └── scripts/
│   └── tutor-progress/
│       ├── SKILL.md                # /tutor-progress → analytics view
│       └── scripts/
│
├── agents/
│   └── tutor-judge.md              # LLM-as-judge subagent for evaluation
│
├── src/                            # editable-install Python package (single wheel)
│   └── language_tutor/
│       ├── __init__.py
│       ├── cli.py                  # entrypoint: `python -m language_tutor.cli ...`
│       ├── lifecycle.py            # LifecycleEvent enum + state machine
│       ├── boot_context.py         # build_boot_context(repos) -> BootContext
│       ├── schemas.py              # Pydantic models (single source of truth)
│       ├── feedback.py             # FeedbackEnvelope -> markdown renderer
│       ├── srs.py                  # SM-2 implementation
│       ├── session.py              # session state machine
│       ├── evaluators.py           # judge prompt templates + parsing
│       ├── errors.py
│       ├── adapters/
│       │   ├── __init__.py
│       │   ├── base.py             # HostAdapter Protocol
│       │   └── claude.py           # ClaudeAdapter
│       └── dal/
│           ├── __init__.py
│           ├── paths.py            # XDG path resolution
│           ├── yaml_store.py
│           ├── sqlite_store.py
│           ├── migrations.py
│           └── repositories.py
│
├── migrations/
│   ├── 001_initial.sql
│   └── README.md
│
├── schemas/                        # JSON schema mirrors (for cross-tool validation, tests)
│   ├── boot_context.schema.json
│   ├── feedback_envelope.schema.json
│   ├── session_analysis.schema.json
│   └── answer_event.schema.json
│
├── data/
│   └── defaults/
│       ├── profile.yaml            # template copied on first run
│       └── preferences.yaml
│
├── tests/
│   ├── unit/                       # srs, schemas, boot_context, feedback rendering
│   ├── golden/                     # markdown output fixtures
│   ├── integration/                # full lifecycle via fake adapter
│   ├── adapter_contract/           # any adapter must pass these
│   └── fixtures/
│
├── pyproject.toml                  # package metadata + deps
├── README.md
└── LICENSE
```

### Structure Rationale

- **`src/language_tutor/` (single package):** Avoids the design.md's three-package split (`core/`, `adapters/`, `dal/`). YAGNI — one package keeps imports simple, single wheel, easier to install editable. Module-level boundaries enforce SoC; package boundaries are overkill for v1. Promote to multi-package only if a real second adapter materializes.
- **`agents/` separate from `skills/`:** The judge is a *subagent invoked by skills*, not a user-facing command. Storing it under `agents/` matches Claude Code conventions and prevents accidental `/tutor-judge` invocation.
- **`hooks/` shells are dumb:** They `exec python -m language_tutor.cli hook <event>` and pass stdin through. All logic in Python.
- **`schemas/` JSON mirrors of Pydantic:** Generated from Pydantic models; used by tests and (future) other-language consumers. Pydantic is the source of truth.
- **`migrations/` flat numbered SQL:** Simpler than Alembic for single-user local DB. Tracked via `PRAGMA user_version`.

---

## Architectural Patterns

### Pattern 1: Boot Context Injection via SessionStart Hook

**What:** On `SessionStart`, `hooks/session-start.sh` invokes Python which loads YAML profile + queries SQLite for due reviews, weak patterns, last session summary, builds a `BootContext`, and emits it as `additionalContext` JSON to stdout. Claude Code injects it at conversation start. Token-budgeted (target ≤ 1500 tokens).

**When to use:** Every session, automatically. No user action required.

**Trade-offs:**
- Pro: Zero-cost from the user's POV; learner state always available without "remembering" to load it.
- Pro: Deterministic, schema-validated.
- Con: Stale within a session — if user does two skills in one session, second skill sees same boot context as first. Mitigated by writing back to `session_summaries` mid-session if needed.

**Example:**
```bash
# hooks/session-start.sh
#!/usr/bin/env bash
exec python -m language_tutor.cli hook session-start
```

```python
# In language_tutor/cli.py
def hook_session_start():
    payload = json.load(sys.stdin)  # session_id, cwd, etc.
    ctx = build_boot_context(repos=Repos.open())
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "SessionStart",
            "additionalContext": render_boot_context(ctx)  # human-readable markdown
        }
    }))
```

### Pattern 2: Skill-as-Slash-Command, Python-as-Backend

**What:** Each user-facing skill (`tutor-vocab`, `tutor-writing`) has a `SKILL.md` that uses dynamic context injection (`` !`python ...` ``) to pull current state into the prompt, then Claude conducts the conversation. Skills do NOT contain pedagogy logic — they orchestrate.

**When to use:** Every interactive user-driven flow (drills, writing, progress).

**Trade-offs:**
- Pro: Skills stay small; logic lives in testable Python.
- Pro: User can invoke as `/tutor-vocab` or just say "let's do vocab" — Claude auto-triggers via description.
- Con: Token cost — each skill invocation re-injects state. Mitigate by keeping injected JSON terse.

**Example:**
```yaml
# skills/tutor-vocab/SKILL.md
---
description: Use when the learner wants vocabulary practice, due SRS reviews,
  flashcard drills, word recall, or lexical correction. Invoke proactively when
  user says "let's practice vocab", "review words", "vocabulary", or similar.
allowed-tools: Bash(python -m language_tutor.cli *) Read Write
---

## Current state
!`python -m language_tutor.cli vocab boot`

## Instructions
You are running a vocabulary drill session for the learner whose profile is
above. Present one due item from the queue. After the learner answers, run:

`python -m language_tutor.cli vocab grade --item-id=<id> --answer="<user input>"`

This returns a FeedbackEnvelope JSON. Render it using:

`python -m language_tutor.cli render feedback --json='<envelope>'`

Loop until queue empty or learner says stop.
```

### Pattern 3: LLM-as-Judge via Subagent (Claude-Calling-Claude)

**What:** For free-production evaluation (`tutor-writing`), the skill delegates to a `tutor-judge` subagent via the Task tool. The subagent receives a structured prompt (rubric + user answer + expected answer + tags vocabulary), runs in an isolated context, and returns a `FeedbackEnvelope` JSON. The skill parses, validates against schema, persists, renders.

**When to use:** Free-form answer evaluation where deterministic rules don't suffice (writing, open-ended vocab production). NOT used for binary-correct SRS card flips (those evaluate in Python).

**Trade-offs:**
- Pro: Isolated context — judge doesn't see conversation history, so biases from prior turns don't leak.
- Pro: Can swap judge model independently of session model.
- Con: Adds a turn round-trip; latency cost.
- Con: Schema-validated parsing must reject malformed judge output and retry.
- Pitfall: Judge may hallucinate tags outside controlled vocabulary — enforce via Pydantic enum validation, retry once with stricter prompt, fall back to `["uncategorized"]` + log.

**Example:**
```markdown
# agents/tutor-judge.md
---
name: tutor-judge
description: Evaluates a language learner's answer against expected output.
  Returns ONLY valid JSON matching FeedbackEnvelope schema.
---

You are a language evaluator for ${L2}. You receive:
- expected_answer
- learner_answer
- learner_l1 (for explanation language)
- controlled tag vocabulary

Return JSON only. No prose. Schema:
{ "verdict": "correct|partial|incorrect", "severity": "ok|minor|major|blocking",
  "corrected_answer": "...", "error_spans": [...], "explanation": "...",
  "tags": ["case_genitive_singular", ...], "next_drill_hint": "..." }

Tag vocabulary (use ONLY these): case_nominative, case_genitive, case_dative,
case_accusative, case_instrumental, case_prepositional, aspect_imperfective,
aspect_perfective, gender_agreement, number_agreement, verb_conjugation,
word_order, lexical_choice, spelling, transliteration, register
```

### Pattern 4: Lifecycle as Append-Only Event Log

**What:** Each canonical `LifecycleEvent` is a row in SQLite. State derives from event replay. `BootContext` queries the latest summary; no in-memory session state needs to survive between turns.

**When to use:** Always — fits Claude Code's turn-based model where Python may be invoked many times per session.

**Trade-offs:**
- Pro: Crash-safe; user can `Ctrl+C` mid-session and resume.
- Pro: Auditability — every drill answer is reconstructible.
- Con: Slightly more writes than mutable state. Negligible at single-user scale.

### Pattern 5: Adapter as Protocol, Not Inheritance

**What:** Use `typing.Protocol` (structural typing) for `HostAdapter`, not `abc.ABC`. Composition over inheritance.

```python
# src/language_tutor/adapters/base.py
from typing import Protocol, runtime_checkable
from ..schemas import LifecycleEvent, UserInput, CoreMessage, HostMessage, AdapterResult

@runtime_checkable
class HostAdapter(Protocol):
    name: str

    def supports_lifecycle(self) -> bool: ...
    def map_host_event(self, raw: dict) -> LifecycleEvent: ...
    def render_core_message(self, msg: CoreMessage) -> HostMessage: ...
    def receive_user_input(self, raw: dict) -> UserInput: ...
    def emit_event(self, event: LifecycleEvent) -> AdapterResult: ...
```

**When to use:** Always for v1. ABC adds inheritance noise without benefit at one-implementation scale.

**Trade-offs:**
- Pro: Duck-typed; future Codex/Hermess adapters don't need to import base class.
- Pro: `runtime_checkable` enables `isinstance()` for contract tests.
- Con: No method-not-implemented errors at class definition time. Mitigated by adapter contract tests.

---

## Concrete Schemas

### BootContext (Pydantic)

```python
class BootContext(BaseModel):
    schema_version: Literal["1.0"]
    generated_at: datetime
    session_id: str

    profile: ProfileSummary
    # name, l1, l2, cefr_target, days_active

    due_srs_summary: DueSrsSummary
    # total_due: int, by_skill: dict, oldest_overdue_days: int

    top_weak_patterns: list[WeakPattern]  # max 5
    # tag, count_30d, last_seen, severity_distribution

    last_session_summary: str | None  # max 400 chars
    recent_progress: ProgressSnapshot
    # streak_days, sessions_7d, accuracy_trend

    active_constraints: list[str]  # from preferences.yaml
    # e.g. ["no transliteration", "session_minutes: 15"]

    token_budget_used: int  # for telemetry
```

**Rendered example (what Claude actually sees):**
```markdown
## Language Tutor — Boot Context

**Learner:** Artem (L1: en → L2: ru, CEFR target: B1)
**Active 12 days, current streak: 4**

### Due reviews (8 total)
- Vocab: 6 due (oldest: 3 days overdue)
- Writing prompts: 2 due

### Recent weakness patterns
1. `case_genitive_singular` — 12 errors in last 30d
2. `aspect_perfective` — 7 errors, last seen yesterday
3. `gender_agreement` — 4 errors

### Last session (yesterday)
Vocab drill 12 items: 9 correct, 3 errors. Focus next: aspect contrasts.

### Constraints
- Session length ≤ 15min
- Feedback in English
- No transliteration
```

### FeedbackEnvelope (Pydantic)

```python
class ErrorSpan(BaseModel):
    start: int           # character index in learner answer
    end: int
    tag: ErrorTag        # enum, controlled vocab
    severity: Severity   # enum

class SrsUpdate(BaseModel):
    item_id: str
    quality: int         # 0-5, SM-2 input
    delta_reason: str

class FeedbackEnvelope(BaseModel):
    schema_version: Literal["1.0"]
    item_id: str
    verdict: Literal["correct", "partial", "incorrect"]
    severity: Severity   # ok|minor|major|blocking → ✅🟡🟠🔴
    corrected_answer: str
    error_spans: list[ErrorSpan]
    explanation: str     # in learner's L1
    next_drill_hint: str | None
    tags: list[ErrorTag]
    srs_updates: list[SrsUpdate]
```

**Controlled `ErrorTag` enum (Slavic-aware):**
```python
class ErrorTag(str, Enum):
    # case
    CASE_NOMINATIVE = "case_nominative"
    CASE_GENITIVE = "case_genitive"
    CASE_DATIVE = "case_dative"
    CASE_ACCUSATIVE = "case_accusative"
    CASE_INSTRUMENTAL = "case_instrumental"
    CASE_PREPOSITIONAL = "case_prepositional"
    # aspect
    ASPECT_IMPERFECTIVE = "aspect_imperfective"
    ASPECT_PERFECTIVE = "aspect_perfective"
    # agreement
    GENDER_AGREEMENT = "gender_agreement"
    NUMBER_AGREEMENT = "number_agreement"
    PERSON_AGREEMENT = "person_agreement"
    # verbs
    VERB_CONJUGATION = "verb_conjugation"
    VERB_MOTION = "verb_motion"      # Slavic-specific
    REFLEXIVE = "reflexive"
    # lexis
    LEXICAL_CHOICE = "lexical_choice"
    COLLOCATION = "collocation"
    REGISTER = "register"
    # surface
    SPELLING = "spelling"
    PUNCTUATION = "punctuation"
    WORD_ORDER = "word_order"
    TRANSLITERATION = "transliteration"
    # fallback
    UNCATEGORIZED = "uncategorized"  # judge fallback, never hand-written
```

### SessionAnalysis (Pydantic)

```python
class SessionAnalysis(BaseModel):
    schema_version: Literal["1.0"]
    session_id: str
    session_started_at: datetime
    session_ended_at: datetime
    skill: Literal["vocab", "writing"]

    severity_counts: dict[Severity, int]  # {ok: 9, minor: 2, major: 1, blocking: 0}
    items_attempted: int
    items_correct: int
    accuracy: float

    new_error_tags: list[ErrorTag]       # tags appearing first time in 30d window
    repeated_error_tags: list[ErrorTag]  # tags also seen in prior 30d
    resolved_error_tags: list[ErrorTag]  # tags last-seen >14d ago that recurred but were corrected

    pattern_drift: str                   # 1-2 sentences, LLM-generated

    recommended_next_focus: list[str]    # 1-3 specific recommendations
    srs_adjustments: list[SrsUpdate]

    summary_for_next_boot: str           # ≤ 300 chars — exact text fed to next BootContext
```

**`summary_for_next_boot` example:**
> "Vocab 12 items, 75% accuracy. Aspect confusion persists (3 errors, 'pisat'/'napisat'). Gender agreement improved. Next: drill perfective verbs of motion."

---

## SQLite Schema Sketch

```sql
-- migrations/001_initial.sql
PRAGMA foreign_keys = ON;
PRAGMA journal_mode = WAL;

-- schema migration tracking
CREATE TABLE schema_migrations (
    version INTEGER PRIMARY KEY,
    applied_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    description TEXT NOT NULL
);

-- SRS items: one row per word/prompt the learner is tracking
CREATE TABLE srs_items (
    item_id TEXT PRIMARY KEY,            -- UUID
    skill TEXT NOT NULL,                 -- 'vocab' | 'writing'
    l2_token TEXT NOT NULL,              -- the word/phrase being learned
    l1_gloss TEXT,                       -- learner's L1 translation
    metadata_json TEXT,                  -- POS, gender, aspect, etc.
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    -- SM-2 state
    ease_factor REAL NOT NULL DEFAULT 2.5,
    interval_days INTEGER NOT NULL DEFAULT 0,
    repetitions INTEGER NOT NULL DEFAULT 0,
    next_review_at TIMESTAMP NOT NULL,
    last_review_at TIMESTAMP,

    -- soft-delete for review history preservation
    archived_at TIMESTAMP
);
CREATE INDEX idx_srs_items_due ON srs_items(next_review_at) WHERE archived_at IS NULL;
CREATE INDEX idx_srs_items_skill ON srs_items(skill);

-- Every SRS review event (append-only)
CREATE TABLE srs_reviews (
    review_id INTEGER PRIMARY KEY AUTOINCREMENT,
    item_id TEXT NOT NULL REFERENCES srs_items(item_id),
    session_id TEXT NOT NULL,
    reviewed_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    quality INTEGER NOT NULL CHECK (quality BETWEEN 0 AND 5),
    interval_before INTEGER NOT NULL,
    interval_after INTEGER NOT NULL,
    ease_before REAL NOT NULL,
    ease_after REAL NOT NULL
);
CREATE INDEX idx_srs_reviews_session ON srs_reviews(session_id);
CREATE INDEX idx_srs_reviews_item ON srs_reviews(item_id, reviewed_at);

-- Every learner answer (append-only, across vocab + writing)
CREATE TABLE answer_events (
    answer_id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    item_id TEXT REFERENCES srs_items(item_id),    -- nullable for ad-hoc writing
    skill TEXT NOT NULL,
    prompt TEXT NOT NULL,
    learner_answer TEXT NOT NULL,
    corrected_answer TEXT,
    verdict TEXT NOT NULL,                          -- correct|partial|incorrect
    severity TEXT NOT NULL,                         -- ok|minor|major|blocking
    feedback_envelope_json TEXT NOT NULL,           -- full FeedbackEnvelope
    answered_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_answer_events_session ON answer_events(session_id);

-- Mistake events: denormalized one-per-error-span, for fast weak-pattern queries
CREATE TABLE mistake_events (
    mistake_id INTEGER PRIMARY KEY AUTOINCREMENT,
    answer_id INTEGER NOT NULL REFERENCES answer_events(answer_id),
    session_id TEXT NOT NULL,
    item_id TEXT REFERENCES srs_items(item_id),
    tag TEXT NOT NULL,                              -- ErrorTag enum
    severity TEXT NOT NULL,
    occurred_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_mistake_events_tag ON mistake_events(tag, occurred_at);
CREATE INDEX idx_mistake_events_session ON mistake_events(session_id);

-- Session lifecycle log (append-only event ledger)
CREATE TABLE lifecycle_events (
    event_id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    event_name TEXT NOT NULL,                       -- SessionStart, BootContextLoaded, etc.
    payload_json TEXT,
    occurred_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_lifecycle_events_session ON lifecycle_events(session_id, occurred_at);

-- Session-end summary (one row per session)
CREATE TABLE session_summaries (
    session_id TEXT PRIMARY KEY,
    started_at TIMESTAMP NOT NULL,
    ended_at TIMESTAMP,
    skill TEXT NOT NULL,
    items_attempted INTEGER NOT NULL DEFAULT 0,
    items_correct INTEGER NOT NULL DEFAULT 0,
    severity_counts_json TEXT NOT NULL,             -- {"ok":9,"minor":2,...}
    session_analysis_json TEXT,                     -- full SessionAnalysis
    summary_for_next_boot TEXT                      -- the ≤300-char string
);

-- Per-skill rolling metrics (recalculable; cache only)
CREATE TABLE skill_metrics (
    skill TEXT PRIMARY KEY,
    streak_days INTEGER NOT NULL DEFAULT 0,
    last_session_at TIMESTAMP,
    sessions_total INTEGER NOT NULL DEFAULT 0,
    items_total INTEGER NOT NULL DEFAULT 0,
    accuracy_30d REAL,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Initial migration marker
INSERT INTO schema_migrations (version, description) VALUES (1, 'initial schema');
```

**Migration runner contract:**
```python
# dal/migrations.py
def run_migrations(conn: sqlite3.Connection, migrations_dir: Path) -> None:
    current = conn.execute("PRAGMA user_version").fetchone()[0]
    for sql_file in sorted(migrations_dir.glob("*.sql")):
        version = int(sql_file.name.split("_")[0])
        if version > current:
            with conn:                        # transactional
                conn.executescript(sql_file.read_text())
                conn.execute(f"PRAGMA user_version = {version}")
```

---

## YAML File Layout

### Disk locations (XDG-compliant)

```python
# src/language_tutor/dal/paths.py
import os
from pathlib import Path

APP_NAME = "language-tutor"

def config_dir() -> Path:
    base = os.environ.get("XDG_CONFIG_HOME") or str(Path.home() / ".config")
    return Path(base) / APP_NAME

def data_dir() -> Path:
    base = os.environ.get("XDG_DATA_HOME") or str(Path.home() / ".local" / "share")
    return Path(base) / APP_NAME

def state_dir() -> Path:
    base = os.environ.get("XDG_STATE_HOME") or str(Path.home() / ".local" / "state")
    return Path(base) / APP_NAME

def profile_path() -> Path: return config_dir() / "profile.yaml"
def preferences_path() -> Path: return config_dir() / "preferences.yaml"
def db_path() -> Path: return data_dir() / "tutor.sqlite"
```

**macOS note:** XDG vars usually unset → falls back to `~/.config/language-tutor/`. Don't use `~/Library/Application Support/` for v1 — keeps cross-platform behavior identical.

### profile.yaml shape

```yaml
# ~/.config/language-tutor/profile.yaml
schema_version: "1.0"
learner:
  name: "Artem"
  l1: "en"                    # ISO 639-1
  l2: "ru"
  cefr_target: "B1"           # A1|A2|B1|B2|C1|C2
  topics: ["tech", "travel", "philosophy"]

constraints:
  no_transliteration: true
  avoid_topics: []
  formality: "neutral"        # informal|neutral|formal

correction_style:
  verbosity: "medium"         # terse|medium|verbose
  explanation_language: "l1"  # l1|l2|bilingual

started_at: "2026-05-19T08:00:00Z"
```

### preferences.yaml shape

```yaml
# ~/.config/language-tutor/preferences.yaml
schema_version: "1.0"
session:
  default_length_minutes: 15
  default_skill: "vocab"

review:
  daily_target_items: 20
  max_new_items_per_session: 5
  intensity: "balanced"       # gentle|balanced|intensive

feedback:
  show_emojis: true
  show_error_spans: true
  show_explanation: true
  next_drill_hint: true

display:
  use_color: true             # for tutor-progress markdown render

evaluation:
  judge_model: "inherit"      # or specific Claude model name
  retry_on_invalid_json: 1
```

**Validation:** Both files parsed via Pydantic on every load; missing fields filled from `data/defaults/`. Schema-version mismatch → migration script.

---

## Adapter Contract — Concrete Python

```python
# src/language_tutor/adapters/base.py
from __future__ import annotations
from typing import Protocol, runtime_checkable
from ..schemas import (
    LifecycleEvent, LifecycleEventName,
    UserInput, CoreMessage, HostMessage, AdapterResult,
)

@runtime_checkable
class HostAdapter(Protocol):
    """Contract every host (Claude, Codex, Hermess, ...) must satisfy.

    Adapters translate between host-native event/IO formats and the
    canonical tutor lifecycle. They MUST NOT contain pedagogy logic.
    """
    name: str  # e.g. "claude-code"

    def supports_lifecycle(self, event_name: LifecycleEventName) -> bool:
        """Return True iff this host can emit/observe this lifecycle event."""
        ...

    def map_host_event(self, raw: dict) -> LifecycleEvent:
        """Parse host-native event payload (hook stdin, etc.) into canonical event.

        Raises:
            UnmappableEventError if the raw event cannot be normalized.
        """
        ...

    def receive_user_input(self, raw: dict) -> UserInput:
        """Extract learner's raw input (typed text) from a host payload."""
        ...

    def render_core_message(self, msg: CoreMessage) -> HostMessage:
        """Convert a core-produced message (markdown FeedbackEnvelope render,
        BootContext markdown) into the host's expected output shape."""
        ...

    def emit_event(self, event: LifecycleEvent) -> AdapterResult:
        """Persist the lifecycle event and trigger any host-side side-effects
        (e.g. write additionalContext JSON to stdout for SessionStart hook)."""
        ...
```

```python
# src/language_tutor/adapters/claude.py
class ClaudeAdapter:
    name = "claude-code"

    SUPPORTED_EVENTS = {
        LifecycleEventName.SESSION_START,           # hook
        LifecycleEventName.BOOT_CONTEXT_REQUESTED,  # implicit on SessionStart
        LifecycleEventName.BOOT_CONTEXT_LOADED,     # additionalContext emitted
        LifecycleEventName.DUE_REVIEWS_LOADED,      # skill script
        LifecycleEventName.WEAK_PATTERNS_LOADED,    # skill script
        LifecycleEventName.EXERCISE_PRESENTED,      # skill via Claude
        LifecycleEventName.ANSWER_RECEIVED,         # skill via Claude
        LifecycleEventName.ANSWER_RECORDED,         # skill script writes DB
        LifecycleEventName.FEEDBACK_RENDERED,       # skill script
        LifecycleEventName.SESSION_ANALYSIS_REQUESTED,  # SessionEnd hook
        LifecycleEventName.SESSION_ANALYZED,        # judge subagent result
        LifecycleEventName.STATE_PERSISTED,         # DB commit
        LifecycleEventName.SESSION_END,             # hook
    }

    def supports_lifecycle(self, event_name): return event_name in self.SUPPORTED_EVENTS
    # ... etc
```

**Contract tests (`tests/adapter_contract/`):** Each adapter runs the same scripted lifecycle scenario (fake user, fake judge) and must pass identical assertions. Forces feature parity.

---

## Lifecycle as State Machine (Persisted, Not In-Memory)

```
┌──────────────┐
│ SessionStart │  hook fires → write lifecycle_events row,
└──────┬───────┘            → query DB for due/weak/last summary
       ▼                    → emit additionalContext JSON to stdout
┌──────────────────────┐
│ BootContextLoaded    │  (implicit, same hook turn)
└──────┬───────────────┘
       │
       │   user types or system invokes /tutor-vocab
       ▼
┌──────────────────────┐    Claude (with skill in context):
│ DueReviewsLoaded     │    runs `python -m language_tutor.cli vocab boot`
│ WeakPatternsLoaded   │    → returns next item + drill stats JSON
└──────┬───────────────┘
       ▼
┌──────────────────────┐
│ ExercisePresented    │    Claude shows item to user (markdown render)
└──────┬───────────────┘
       │
       │   user types answer
       ▼
┌──────────────────────┐    Claude:
│ AnswerReceived       │    runs `python -m language_tutor.cli vocab grade --answer="..."`
│                      │    (for free-form: vocab/writing → judge subagent via Task tool)
└──────┬───────────────┘
       ▼
┌──────────────────────┐    Python:
│ AnswerRecorded       │    → INSERT into answer_events + mistake_events + srs_reviews
│                      │    → UPDATE srs_items (SM-2)
│                      │    → return FeedbackEnvelope JSON
└──────┬───────────────┘
       ▼
┌──────────────────────┐    Claude:
│ FeedbackRendered     │    runs `python -m language_tutor.cli render feedback`
│                      │    → shows markdown to user
└──────┬───────────────┘
       │
       │   loop until session length / user stops
       ▼
┌──────────────────────────────┐
│ SessionAnalysisRequested     │    SessionEnd hook fires:
│ SessionAnalyzed              │    → calls judge subagent w/ session-summary prompt
│ StatePersisted               │    → validates + writes session_summaries row
│ SessionEnd                   │    → updates skill_metrics
└──────────────────────────────┘    → closes SQLite connections
```

**Where state lives:**
- **Across turns within a session:** SQLite (`lifecycle_events`, `answer_events`, `srs_items`). Claude's context window is cache only.
- **Within a single Python invocation:** in-memory dataclasses. No long-running daemon.
- **Across sessions:** SQLite + `session_summaries.summary_for_next_boot`.

---

## Data Flow

### Read flow: User starts session, asks "let's do vocab"

```
SessionStart hook
    │ (Claude Code spawns process w/ JSON stdin)
    ▼
hooks/session-start.sh → python -m language_tutor.cli hook session-start
    │
    ▼
language_tutor.cli.hook_session_start()
    │
    ├─→ DAL.YamlStore.load_profile()       ← profile.yaml
    ├─→ DAL.SqliteStore.open()              ← tutor.sqlite
    ├─→ Repositories.SrsRepo.due_summary()
    ├─→ Repositories.MistakeRepo.top_patterns(n=5)
    ├─→ Repositories.SessionRepo.last_summary()
    │
    ▼
language_tutor.boot_context.build_boot_context(repos) → BootContext
    │
    ▼
language_tutor.feedback.render_boot_context(ctx) → markdown
    │
    ▼
stdout: {"hookSpecificOutput": {"hookEventName": "SessionStart",
                                "additionalContext": "<markdown>"}}
    │
    ▼
Claude Code injects into session prompt
    │
    ▼
User: "let's practice vocab"
    │
    ▼
Claude matches /tutor-vocab skill description → loads SKILL.md
    │
    ▼
SKILL.md `!`python -m language_tutor.cli vocab boot`` runs preprocessing
    │
    ▼
Returns due-queue JSON → Claude presents first item
```

### Write flow: User answers a writing prompt

```
User types answer in chat
    │
    ▼
tutor-writing skill instructs Claude to call:
    Task tool with subagent_type=tutor-judge
    args = {expected, learner_answer, l1, tags_vocab}
    │
    ▼
tutor-judge subagent runs (isolated context)
    │
    ▼
Returns JSON FeedbackEnvelope candidate
    │
    ▼
Claude runs: python -m language_tutor.cli writing record \
                --envelope='<json>' --item-id=<id>
    │
    ▼
Python:
  1. validate FeedbackEnvelope against Pydantic schema
     (on ValidationError → retry judge once with stricter prompt;
      on second failure → coerce tag to UNCATEGORIZED, log)
  2. begin transaction
  3. INSERT answer_events row
  4. INSERT mistake_events rows (one per error_span)
  5. SM-2 update srs_items + INSERT srs_reviews
  6. INSERT lifecycle_events (AnswerRecorded)
  7. commit
  8. return validated FeedbackEnvelope JSON
    │
    ▼
Claude runs: python -m language_tutor.cli render feedback --json='...'
    │
    ▼
Returns rendered markdown with severity emojis
    │
    ▼
Claude shows to user
```

---

## Build Order — Critical Dependencies

Top-down dependency stack. **Build bottom-up.**

```
                ┌───────────────────────────┐
                │   User-facing skills      │  ← Phase 4
                │   /tutor-vocab,           │
                │   /tutor-writing,         │
                │   /tutor-progress         │
                └─────────────┬─────────────┘
                              │ depends on
                ┌─────────────▼─────────────┐
                │   tutor-judge subagent    │  ← Phase 3.5
                │   (writing eval only)     │
                └─────────────┬─────────────┘
                              │ depends on
                ┌─────────────▼─────────────┐
                │   FeedbackEnvelope        │  ← Phase 3
                │   renderer + SM-2         │
                └─────────────┬─────────────┘
                              │ depends on
                ┌─────────────▼─────────────┐
                │   Lifecycle state         │  ← Phase 2.5
                │   machine + cli           │
                │   entrypoints             │
                └─────────────┬─────────────┘
                              │ depends on
                ┌─────────────▼─────────────┐
                │   DAL: repos, sqlite,     │  ← Phase 2
                │   migrations, yaml        │
                └─────────────┬─────────────┘
                              │ depends on
                ┌─────────────▼─────────────┐
                │   Pydantic schemas        │  ← Phase 1
                │   (single source of       │
                │   truth for all data)     │
                └─────────────┬─────────────┘
                              │ depends on
                ┌─────────────▼─────────────┐
                │   Plugin scaffold +       │  ← Phase 0
                │   adapter Protocol +      │
                │   hello-world SessionStart│
                │   hook                    │
                └───────────────────────────┘
```

### Suggested Phases (informs roadmap)

| Phase | Goal | Build | Verify by |
|-------|------|-------|-----------|
| **0 Scaffold** | Plugin installs and SessionStart hook injects "hello" context | `plugin.json`, `hooks/`, `cli.py` stub, adapter Protocol | `claude /plugin install ...` + observe injection |
| **1 Schemas** | Every data shape has Pydantic model + JSON schema dump | `schemas.py`, `schemas/*.json`, schema unit tests | `pytest tests/unit/test_schemas.py` |
| **2 DAL** | Can read/write YAML + transactional SQLite from CLI | `dal/`, `migrations/001_initial.sql`, `cli` smoke commands | Integration test: write profile → query DB |
| **2.5 Lifecycle** | Full event ledger; `BootContext` builds from real data | `lifecycle.py`, `boot_context.py`, `session.py` | SessionStart hook returns real boot ctx |
| **3 Vocab + SM-2 + Feedback** | `tutor-vocab` skill runs deterministic drills end-to-end | `srs.py`, `feedback.py`, `skills/tutor-vocab/`, golden render tests | Manually run /tutor-vocab, complete a drill |
| **3.5 Judge** | `tutor-judge` agent returns valid FeedbackEnvelope for writing | `agents/tutor-judge.md`, `evaluators.py` w/ retry+fallback | Adversarial fixtures (malformed answers, hallucinated tags) |
| **4 Writing + Progress + Setup** | All four user-facing skills work | `tutor-writing`, `tutor-progress`, `tutor-setup` | Daily-use dogfood |
| **5 Session analyzer** | SessionEnd hook persists structured `SessionAnalysis` | `tutor-session-analyzer` agent, SessionEnd hook | Session N+1 boot context reflects session N |
| **6 Adapter contract tests** | Prove Claude adapter satisfies generic contract | `tests/adapter_contract/` | `pytest tests/adapter_contract` passes |
| **7 Distribution** | Plugin installs cleanly from marketplace | `marketplace.json` entry, install docs | Fresh-machine install works |

**Key build rule:** No skill can be merged until its underlying schemas + DAL repos + golden render tests exist. New or edited `SKILL.md` files also require assigned-subagent RED/GREEN/REFACTOR pressure evidence using the local writing-skills helper and active spec references. This stops "skill works locally but writes nothing useful to DB" and "skill routes correctly only when the author is driving."

---

## Plugin Distribution Shape

### Bundle layout (what gets installed)

The plugin is a **single repo** containing both Claude artifacts (`hooks/`, `skills/`, `agents/`, `.claude-plugin/`) and the Python package (`src/language_tutor/`, `pyproject.toml`).

**Two install strategies — pick ONE:**

| Strategy | How | Pros | Cons |
|----------|-----|------|------|
| **A. Bundled venv (recommended)** | Plugin postinstall script creates `${CLAUDE_PLUGIN_DATA}/.venv`, runs `pip install -e $CLAUDE_PLUGIN_ROOT`. Hooks/skills invoke `${CLAUDE_PLUGIN_DATA}/.venv/bin/python`. | Self-contained, no user setup, isolates deps | Larger install (~30MB w/ Pydantic) |
| **B. Assume `language-tutor` on PATH** | User does `pipx install language-tutor` separately, plugin shells out to `language-tutor` command. | Smaller plugin bundle | Brittle UX — install fails silently if user skips step |

**Recommendation: A.** OSS plugin marketplace UX should be one-command. Document fallback for power users.

### marketplace.json entry

```json
{
  "name": "language-tutor",
  "description": "Daily-use AI language tutor: SRS vocab drills + free writing with structured feedback. Local-first, your data stays on disk.",
  "author": { "name": "Artem Veduta" },
  "category": "productivity",
  "source": {
    "source": "url",
    "url": "https://github.com/<user>/language-tutor.git",
    "ref": "v0.1.0"
  },
  "homepage": "https://github.com/<user>/language-tutor",
  "version": "0.1.0",
  "tags": ["language-learning", "srs", "tutoring"]
}
```

### plugin.json

```json
{
  "$schema": "https://anthropic.com/claude-code/plugin.schema.json",
  "name": "language-tutor",
  "version": "0.1.0",
  "description": "AI language tutor — SRS vocab drills and free writing with structured feedback",
  "author": { "name": "Artem Veduta", "url": "https://github.com/<user>" },
  "license": "MIT"
}
```

Components auto-discovered from `skills/`, `agents/`, `hooks/hooks.json`.

### hooks.json

```json
{
  "hooks": {
    "SessionStart": [{
      "hooks": [{
        "type": "command",
        "command": "${CLAUDE_PLUGIN_DATA}/.venv/bin/python",
        "args": ["-m", "language_tutor.cli", "hook", "session-start"],
        "timeout": 10
      }]
    }],
    "SessionEnd": [{
      "hooks": [{
        "type": "command",
        "command": "${CLAUDE_PLUGIN_DATA}/.venv/bin/python",
        "args": ["-m", "language_tutor.cli", "hook", "session-end"],
        "async": true
      }]
    }]
  }
}
```

---

## Scaling Considerations

| Scale | What Changes | Action |
|-------|--------------|--------|
| **Single user, daily use** (target) | n/a | Default architecture handles this indefinitely. SQLite at single-digit MB. |
| **One user, multi-device** | Sync `tutor.sqlite` | Out of scope v1. If added: `litestream` to S3, or git-sync of plaintext YAML + dump SQL. |
| **Multi-user (e.g. classroom)** | Concurrency, auth | Significant redesign. Don't optimize for this; explicitly out of scope. |
| **Persisted analytics history >1y** | Indexes on `occurred_at` | Already covered by `idx_mistake_events_tag` etc. Add periodic VACUUM. |

### First bottlenecks (in order)

1. **Judge latency** — every writing answer adds a subagent round-trip (~3-5s). Mitigation: batch answers if multiple in one turn; cache identical prompts.
2. **Boot context token bloat** — as `mistake_events` grows, "top weak patterns" query stays O(log n) due to index, but the rendered context grows if you naively dump all tags. Hard-cap rendering to top 5.
3. **Skill listing budget overflow in Claude Code** — if you ship many skills, descriptions get truncated. v1 has only 4 user-facing skills — well under any budget.

---

## Anti-Patterns

### Anti-Pattern 1: Pedagogy in `SKILL.md` body

**What people do:** Embed SRS math, severity rules, error tag logic directly in the markdown of `tutor-vocab/SKILL.md`. "Calculate new interval as old_interval × ease_factor..."
**Why wrong:** Becomes prompt-engineered guess; non-deterministic; not testable; impossible to maintain across multiple skills (DRY violation). Changing the SM-2 algorithm requires editing N skills.
**Do instead:** SKILL.md only orchestrates: "call `python -m language_tutor.cli vocab grade --answer=...`, then render the returned JSON." All math lives in `srs.py` with unit tests.

### Anti-Pattern 2: In-memory session state across turns

**What people do:** Maintain a Python `Session` object in memory and expect it to persist between turns.
**Why wrong:** Claude Code spawns a fresh process for each hook invocation, and skill `!`...`` injections likewise. Process memory is gone after each call.
**Do instead:** Persist every state-mutation to SQLite immediately. Read fresh state on every CLI invocation. Lifecycle is an event log, not a long-running actor.

### Anti-Pattern 3: Tag vocabulary as free-form strings

**What people do:** Let the judge subagent return `tags: ["wrong genitive ending", "weird word choice"]`.
**Why wrong:** Aggregation impossible. Weak-pattern detection becomes regex soup. Boot context fills with synonyms of the same problem.
**Do instead:** Strict `ErrorTag` enum; validate at ingestion; coerce hallucinated tags to `UNCATEGORIZED` and log. Curate enum based on Slavic-specific error categories.

### Anti-Pattern 4: Single `tutor-feedback` skill that renders markdown

**What people do:** Per design.md, create `skills/tutor-feedback/SKILL.md` for rendering feedback.
**Why wrong:** Rendering is a pure function on a `FeedbackEnvelope`. Wrapping it in a separate skill adds a token round-trip and another LLM call where there should be none.
**Do instead:** `feedback.py` Python module called via `python -m language_tutor.cli render feedback --json='...'` from inside vocab/writing skills. Golden-test the output.

### Anti-Pattern 5: One repo per host adapter (premature monorepo)

**What people do:** Split into `language-tutor-core`, `language-tutor-claude-adapter`, `language-tutor-codex-adapter` packages.
**Why wrong:** v1 ships only Claude. Three packages × pyproject × CI × versioning = drag.
**Do instead:** Single package, adapters as submodules. Split only when a second adapter materializes and proves the seam.

### Anti-Pattern 6: Generating curriculum at build time

**What people do:** Pre-generate vocab lists / writing prompts and ship them.
**Why wrong:** Out of scope per PROJECT.md ("LLM generates exercises on-demand"). Defeats "any L2" wedge.
**Do instead:** Skills prompt Claude to generate next item on demand; persisted to `srs_items` once introduced.

### Anti-Pattern 7: Storing renderer output in `answer_events`

**What people do:** Save the rendered markdown alongside the structured envelope.
**Why wrong:** Couples persistence to display format; can't re-render with new style. Bloats DB.
**Do instead:** Store only the structured `feedback_envelope_json`. Always re-render at read time.

---

## Integration Points

### External Services

| Service | Integration | Notes |
|---------|-------------|-------|
| Claude API (via Claude Code) | Subagent + main agent — no direct API calls from Python | Out of scope: direct Anthropic SDK. Claude Code orchestrates LLM. |
| (None other) | — | Per PROJECT.md: no paid APIs, no telemetry, no cloud. |

### Internal Boundaries

| Boundary | Direction | Mechanism | Forbidden Cross-talk |
|----------|-----------|-----------|----------------------|
| Hook script ↔ Adapter | Bidirectional (stdin/stdout JSON) | subprocess | Hook script cannot import core directly — must go through adapter |
| Adapter ↔ Core | Adapter calls core | Python function calls | Core must not import adapter or know host names |
| Skill `!`...`` ↔ CLI ↔ Core | Inject → run → return JSON | subprocess | Skill cannot directly query DB; must go through `cli` |
| Core ↔ DAL | Core calls DAL | Python (repository pattern) | DAL must not apply pedagogy; pure CRUD + transactions |
| DAL ↔ Filesystem | DAL reads/writes | `sqlite3`, `PyYAML` | No other module touches files |
| tutor-judge subagent ↔ Skill | Skill calls Task tool, judge returns JSON | Claude Code Task tool | Judge cannot read SQLite or YAML; pure stateless function |

---

## Claude Code Plugin Invocation Model — Verified Mapping

| Tutor Lifecycle Event | Claude Code Surface | Verified? |
|-----------------------|---------------------|-----------|
| SessionStart | `hooks/hooks.json` SessionStart hook → emits `additionalContext` | HIGH (docs) |
| BootContextRequested / Loaded | Implicit in SessionStart hook return value | HIGH |
| DueReviewsLoaded / WeakPatternsLoaded | Skill body `!`python ...`` dynamic injection at skill load | HIGH (docs: "Inject dynamic context") |
| ExercisePresented | Skill content → Claude generates exercise turn | HIGH (conversation-driven) |
| AnswerReceived | User types next message in conversation | HIGH (default) |
| AnswerRecorded | Skill instructs Claude to run `!`python -m ... grade ...`` or `allowed-tools` Bash call | HIGH |
| FeedbackRendered | Python returns markdown; skill displays | HIGH |
| SessionAnalysisRequested / Analyzed | SessionEnd hook (async) | HIGH (docs: SessionEnd async) |
| StatePersisted | DB commit at end of each grade call + in SessionEnd | HIGH |
| SessionEnd | `hooks/hooks.json` SessionEnd hook | HIGH (docs) |

---

## Phase 2 Vocabulary Data Ownership

Vocabulary Phase 2 keeps the same layered boundary:

- `schemas.py` owns card definition, import summary, drill request/session plan, and review-history contracts plus JSON schema mirrors.
- `vocab.py` owns duplicate identity normalization, cloze prompt/reveal helpers, import orchestration, drill selection rules, and history service composition.
- `repositories.py` owns SQLite persistence, per-entry import transactions, additive metadata merge, tag-filter query, and review-history joins.
- SQLite remains canonical for cards, review state, imports, and attempts. Seed JSON is an input only.
- `skills/tutor-vocab` still shells out to `bin/tutor`; it does not implement scheduling, validation, or persistence.

## Sources

- [Plugins reference - Claude Code Docs](https://code.claude.com/docs/en/plugins-reference) — plugin.json schema, component discovery, `${CLAUDE_PLUGIN_ROOT}` / `${CLAUDE_PLUGIN_DATA}` placeholders
- [Extend Claude with skills - Claude Code Docs](https://code.claude.com/docs/en/skills) — SKILL.md frontmatter (`description`, `disable-model-invocation`, `allowed-tools`, `context: fork`), dynamic context injection via `` !`cmd` ``, skill content lifecycle
- [Hooks reference - Claude Code Docs](https://code.claude.com/docs/en/hooks) — SessionStart/SessionEnd events, stdin/stdout JSON protocol, `additionalContext` injection, async hooks
- [Create custom subagents - Claude Code Docs](https://code.claude.com/docs/en/sub-agents) — Task tool, subagent context isolation, `agents/*.md` discovery
- [claude-plugins-official marketplace.json](https://github.com/anthropics/claude-plugins-official/blob/main/.claude-plugin/marketplace.json) — marketplace registration shape, `source` types
- [Claude Code Hooks: Complete Guide to All 12 Lifecycle Events](https://claudefa.st/blog/tools/hooks/hooks-guide) — hook cadence taxonomy (per-session vs per-turn vs per-tool)
- [Understanding Claude Code's Full Stack: MCP, Skills, Subagents, and Hooks](https://alexop.dev/posts/understanding-claude-code-full-stack/) — when to use which surface
- [SM-2 algorithm reference - supermemo.com](https://www.supermemo.com/english/ol/sm2.htm) — ease factor + interval + repetitions formulas
- [supermemo2 PyPI](https://pypi.org/project/supermemo2/) — reference Python implementation (optional dep)
- [Event Sourcing with SQLite: Append-Only Design](https://www.sqliteforum.com/p/event-sourcing-with-sqlite) — append-only event store pattern
- [xdg-base-dirs - PyPI](https://pypi.org/project/xdg-base-dirs/) — XDG path resolution in Python
- [PyXDG basedirectory docs](https://pyxdg.readthedocs.io/en/latest/basedirectory.html) — XDG_CONFIG_HOME / XDG_DATA_HOME semantics
- [suckless SQLite schema migrations in Python](https://eskerda.com/sqlite-schema-migrations-python/) — `PRAGMA user_version` migration pattern

---

## Phase 5 Addendum — Text Modalities (2026-05-22)

Reading comprehension, guided micro-lessons, and transcript drills were added without new
architecture layers or new persistence:

- **No new storage path.** Attempts persist as existing `answer_events` (skill expanded to
  `vocab|writing|reading|lesson`) and `mistake_events`. Transcript drills store
  `skill=reading` with result `modality=transcript`; they are distinguished in progress by
  the `transcript_` exercise-id prefix, not by a new column or table.
- **`FeedbackEnvelope` unchanged.** Modality-specific `TextModalityResult` wrappers embed it
  verbatim, preserving every existing feedback consumer (rendering, mistake persistence,
  progress analysis).
- **Layering preserved.** Skills (`tutor-reading`, `tutor-lesson`) orchestrate
  `bin/tutor reading|lesson start|record --json`; CLI validates candidates and budgets;
  `text_modalities.py` owns shared validation/guardrails/safe-signal mapping; `reading.py`
  and `lessons.py` own modality orchestration; narrow repository helpers persist. Host
  adapters are untouched.
- **Transcript is a `tutor-reading` submode** (`mode=transcript`), text-only, never audio.

---

*Architecture research for: agentic-CLI plugin AI language tutor (Claude Code v1)*
*Researched: 2026-05-19*

## Phase 6 Addendum — Agent Adapter Setup (2026-05-22)

Spec 006 adds a host-adapter layer above the existing local-first core without
touching pedagogy, scheduling, feedback semantics, progress calculation, or DAL
ownership.

- **Capability/lifecycle contracts** (`src/language_tutor/schemas.py`):
  `HostSetupTarget`, `OfficialSourceEvidence`, `HostSetupProfileContract`,
  `AdapterCapabilityProfile`, `BootContextTrigger`, `SetupPackage`,
  `ConformanceRun`, `ManualProviderInstallReport`, `HostSetupFailure`, plus
  JSON-schema mirrors under `schemas/`.
- **Supported-host registry** (`src/language_tutor/adapters/base.py`): single
  source of truth for the four approved hosts (Hermes, OpenClaw, Claude, Codex),
  their approved official source URLs, setup models, and contract paths.
  Antigravity is intentionally absent and rejected by the `HostId` enum.
- **Capability defaults** (`src/language_tutor/adapters/registry.py`) with thin
  per-host adapter modules (`hermes.py`, `openclaw.py`, `claude.py`, `codex.py`)
  that delegate to the registry — composition over inheritance.
- **Boot routing** (`src/language_tutor/boot_context.py::select_boot_trigger`):
  deterministic mapping from a host's declared trigger to hook / explicit-command
  / first-message / manual lifecycle paths. Core boot-context rendering stays
  host-blind.
- **Conformance runner** (`base.py::run_conformance`): host-blind, derives the six
  representative text-flow outcomes from the capability profile.
- **Host CLI group** (`tutor host targets|capability|boot-trigger`) emits the
  registry, capability profiles, and selected boot triggers as JSON.
- **Distribution surfaces**: `hermes-profile/`, `openclaw-plugin/`,
  `.claude-plugin/` (baseline), `.codex-plugin/` + `.agents/plugins/`. Privacy
  exclusions (secrets, memories, sessions, SQLite, logs, caches, local overrides)
  are enforced by packaging tests.
