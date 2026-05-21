# Quickstart: Vocab Depth

This quickstart defines the expected contributor flow after Phase 2 implementation tasks are complete. Run commands from the repository root.

## 1. Create Development Environment

```bash
rtk uv venv
rtk uv pip install -e ".[dev]"
```

## 2. Verify Baseline

```bash
rtk tutor doctor --json
rtk pytest tests/integration/test_vocabulary_flow.py
rtk pytest tests/adapter_contract/test_vocab_cli.py
```

Expected result: existing vocabulary start/answer behavior still works.

## 3. Add a Manual Standard Card

```bash
rtk tutor vocab add --json '{"card_type":"standard","target":"privit","prompt":"hello","accepted_answers":["privit"],"tags":["greetings"],"source":"manual"}'
```

Expected result: one card is created and can appear in `tutor vocab start --json`.

## 4. Reject a Duplicate Manual Card

```bash
rtk tutor vocab add --json '{"card_type":"standard","target":"Privit","prompt":" hello ","accepted_answers":["privit"],"tags":["daily"]}'
```

Expected result: duplicate response names the existing card id and does not create review history.

## 5. Import a Seed List

Use a `.json` file shaped like `specs/002-vocab-depth/contracts/seed-list-json.md`.

```bash
rtk tutor vocab import --json '{"path":"tests/fixtures/vocabulary/phase2_seed.json"}'
rtk tutor vocab import --json '{"path":"tests/fixtures/vocabulary/phase2_seed.json"}'
```

Expected result: first import reports created/updated/invalid entries; second import creates zero duplicates and preserves review state.

## 6. Run a Tag-Filtered Drill

```bash
rtk tutor vocab start --json '{"tags":["greetings"]}'
```

Expected result: every returned card has the `greetings` tag, due cards appear before new matching cards, and empty output distinguishes no matching cards from matching cards not due.

Multi-tag filters use inclusive OR matching. Empty tag arrays are rejected.

## 7. Add and Review a Cloze Card

```bash
rtk tutor vocab add --json '{"card_type":"cloze","target":"privit","prompt":"{{answer}} is a common greeting.","accepted_answers":["privit"],"tags":["greetings","cloze"]}'
rtk tutor vocab start --json '{"tags":["cloze"]}'
```

Expected result: drill prompt hides the answer. Answering the card returns normal feedback, a vocabulary review, and a reveal of the complete sentence.

## 8. Inspect Review History

```bash
rtk tutor vocab history --json '{"item_id":"fixture-item"}'
```

Expected result: new cards show no attempts and due status; reviewed cards show chronological attempts with verdicts, times, and previous/next review state.

## Verification Gates

```bash
rtk pytest tests/unit/test_schemas.py tests/unit/test_repositories.py tests/unit/test_srs.py
rtk pytest tests/golden/test_vocab_feedback.py
rtk pytest tests/adapter_contract/test_vocab_cli.py
rtk pytest tests/integration/test_vocabulary_flow.py
rtk pytest tests/migration/test_migrations.py
rtk pyright
rtk ruff check .
```

Expected result: Phase 2 vocabulary behavior is deterministic, local-first, schema-validated, and host-independent.
