# Quickstart: language-tutor v1

This quickstart defines the expected contributor flow once implementation tasks are complete. Run commands from the repository root.

## 1. Create Development Environment

```bash
rtk uv venv
rtk uv pip install -e ".[dev]"
```

## 2. Verify Tooling

```bash
rtk tutor doctor --json
rtk pytest
rtk pyright
rtk ruff check .
```

Expected result: doctor reports usable runtime, plugin files, data paths, and migration state; tests/type/lint pass.

## 3. First Setup

```bash
rtk tutor setup read --json
rtk tutor setup write --json '{"profile":{"native_language":"en","target_language":"uk"},"preferences":{}}'
```

Expected result: profile and preferences YAML are created or updated; learning history remains untouched.

## 4. Boot Context

```bash
rtk tutor boot-context --json
```

Expected result: concise first-session context with profile basics, no-history guidance, due-review status, and bounded output.

## 5. Vocabulary Smoke Flow

```bash
rtk tutor vocab start --json
rtk tutor vocab answer --json '{"item_id":"fixture-item","answer":"fixture-answer","idempotency_key":"quickstart-1"}'
```

Expected result: one feedback envelope, one answer event, one vocabulary review, and one future review decision. Re-running with the same idempotency key must not double-apply SRS.

## 6. Writing Smoke Flow

```bash
rtk tutor writing prompt --json
rtk tutor writing record --json '{"prompt_id":"fixture-prompt","learner_answer":"fixture answer","candidate_feedback":{"verdict":"needs_review"}}'
```

Expected result: evaluator output is validated or safely downgraded; mistake events are persisted when valid; vocabulary SRS is unchanged.

## 7. Progress

```bash
rtk tutor progress --json
```

Expected result: progress includes streak policy, due counts, weak patterns, item maturity, last recap, month-to-date estimated USD cost, and cost availability status. Empty history returns clear next action.

## 8. Plugin Local Check

```bash
rtk tutor doctor --json
```

Expected result: manifest, hooks, skills, agent file, and `bin/tutor` are discoverable and ready for Claude Code plugin testing.

## Verification Gates

- `rtk pytest tests/unit tests/golden`
- `rtk pytest tests/integration tests/adapter_contract`
- `rtk pytest tests/fixtures`
- `rtk pyright`
- `rtk ruff check .`

Semantic evaluator fixture runs may be separate from the default unit suite because they depend on host-provided model evaluation.
