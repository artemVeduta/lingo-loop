# tutor-book: Book-Reading Companion Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a `tutor book` CLI command group and `tutor-book` skill that lets a learner log lookups (word/sentence/passage/question) while reading their own book, persist them per-book, and feed looked-up words into the SRS vocab deck.

**Architecture:** A new `BookRepository(conn)` owns the `book_sessions` and `book_lookups` tables (a new migration `005_book_lookups.sql` that also rebuilds `checkpoints` to accept the `book` modality + `answer_recorded` step_kind). Pure handlers in `src/language_tutor/book.py` orchestrate start/record/resume/log/list/close; `cli.py` registers the `@main.group()` and subcommands (the repo convention). Word lookups with a usable translation find-or-create an SRS card via a new `vocab.py` helper `find_or_create_vocab_card_for_book`, which reuses `item_from_definition` + a refactored nestable `_import_vocabulary_item_inner` (DRY). Rendering is deterministic, embedded as a `rendered` field on the result (KISS — no separate render subcommand).

**Tech Stack:** Python 3.12+, click, pydantic, sqlite3 (existing), pytest (by-layer: unit/integration/golden/migration/installer).

**Spec:** `docs/superpowers/specs/2026-06-22-tutor-book-reading-design.md` (approved).

---

## Parallelism map

The work decomposes into independent units. There is ONE cross-cutting prerequisite: the `import_vocabulary_item` → `_import_vocabulary_item_inner` refactor (Task 1) must land before the `book.py` SRS-feeding path (Task 5). Recommended dispatch:

- **Batch 1:** Task 1 (vocab refactor) — blocking prerequisite.
- **Batch 2 (parallel):** Task 2 (migration+enums), Task 3 (schemas), Task 7 (skill), Task 8 (spec docs) — all independent.
- **Batch 3:** Task 4 (BookRepository) — needs Tasks 2 + 3.
- **Batch 4:** Task 5 (book.py handlers) — needs Tasks 1 + 3 + 4.
- **Batch 5:** Task 6 (CLI + integration/golden tests) — needs Task 5.
- **Batch 6:** Task 9 (full suite + lint + typecheck) — needs all.

---

## File structure

**New files:**
- `migrations/005_book_lookups.sql` — DDL: `book_sessions`, `book_lookups`, indexes; rebuilds `checkpoints` (expanded CHECKs) atomically.
- `src/language_tutor/dal/book_repository.py` — `BookRepository(conn)` class covering both book tables.
- `src/language_tutor/book.py` — handlers `start_book`/`record_book`/`resume_book`/`log_book`/`list_book`/`close_book` + deterministic `render_*` helpers.
- `skills/tutor-book/SKILL.md` — runtime learner-facing skill (no `scripts/run.py` shim, matching `tutor-reading`).
- `tests/unit/test_book.py` — unit tests for handlers + rendering.
- `tests/integration/test_book_flow.py` — full CLI flow.
- `tests/golden/test_book_rendering.py` — deterministic `rendered` templates.
- `tests/migration/test_005_book_lookups.py` — migration + atomicity gate.
- `tests/fixtures/book/builders.py` — dict builders for book inputs.
- `specs/008-book-reading/spec.md` — feature spec.
- `specs/008-book-reading/contracts/book-cli.md` — CLI command contracts.
- `specs/008-book-reading/contracts/book-json.md` — JSON shape contracts.
- `specs/008-book-reading/contracts/book_record.schema.json` — generated mirror.
- `specs/008-book-reading/contracts/book_session.schema.json` — generated mirror.
- `specs/008-book-reading/contracts/book_lookup_result.schema.json` — generated mirror.
- `specs/008-book-reading/contracts/book_log.schema.json` — generated mirror.
- `specs/008-book-reading/contracts/book_list.schema.json` — generated mirror.
- `specs/008-book-reading/skill-pressure-scenarios.md` — 7 pressure scenarios.
- `specs/008-book-reading/skill-rewrite-evidence.md` — RED/GREEN/REFACTOR evidence (constitution VIII gate).
- `specs/008-book-reading/checklists/requirements.md` — acceptance checklist.

**Modified files:**
- `src/language_tutor/dal/repositories.py` — extract `_import_vocabulary_item_inner` from `import_vocabulary_item` (nestable).
- `src/language_tutor/schemas.py` — add `CheckpointModality.BOOK`, `CheckpointStepKind.ANSWER_RECORDED`, new book pydantic models, register 5 schemas in `export_json_schemas`.
- `src/language_tutor/vocab.py` — add `find_or_create_vocab_card_for_book` helper.
- `src/language_tutor/cli.py` — import book handlers, register `@main.group() def book()` + 6 subcommands.
- `src/language_tutor/package_assets.py` — append `migrations/005_book_lookups.sql` to `REQUIRED_MIGRATION_FILES`; append `skills/tutor-book/SKILL.md` to `REQUIRED_SKILL_PAYLOAD_FILES`.
- `src/language_tutor/installer/providers/base.py` — append `"tutor-book/SKILL.md"` to `SKILL_FILES`.
- `pyproject.toml` — add wheel force-include line for `skills/tutor-book/SKILL.md`.
- `specs/005-text-modalities/skill-inventory.md` — bump tutor count 7→8, add `tutor-book` row.
- `tests/migration/test_004_sessions_checkpoints.py` — `[1,2,3,4]` → `[1,2,3,4,5]` (2 places).
- `tests/migration/test_migrations.py` — `[1,2,3,4]` → `[1,2,3,4,5]` (2 places) + add `005_book_lookups.sql` to the missing-files tuple.
- `tests/unit/test_schemas.py` — add `test_book_schema_mirrors_export`.
- `schemas/book_record.schema.json` (+ 4 others) — generated into `schemas/`.

---

## Task 1: Refactor `import_vocabulary_item` into a nestable `_import_vocabulary_item_inner`

**Why first:** `book.py`'s SRS-feeding path (Task 5) needs to call the find-or-create-with-merge logic inside `book.py`'s own outer transaction (so the card write + lookup insert commit atomically). The current `import_vocabulary_item` opens its own `with transaction(self.conn):`, which would fail under an already-open transaction (bare `BEGIN`).

**Files:**
- Modify: `src/language_tutor/dal/repositories.py:152-188` (the `import_vocabulary_item` method).
- Test: `tests/unit/test_repositories.py:62-109` (existing `test_import_merges_additive_metadata_without_review_reset` must stay green).

- [ ] **Step 1: Write a failing test for the nestable inner form**

Add to `tests/unit/test_repositories.py` (after the existing `test_import_merges_additive_metadata_without_review_reset`):

```python
def test_import_vocabulary_item_inner_runs_inside_caller_transaction(tmp_path) -> None:  # type: ignore[no-untyped-def]
    from language_tutor.dal.sqlite_store import connect, transaction

    conn = connect(tmp_path / "db.sqlite3")
    try:
        repo = TutorRepository(conn)
        item = VocabularyItem(
            id=new_id("vocab"),
            target_language="uk",
            prompt="hello",
            lemma="привіт",
            accepted_answers=["привіт"],
            tags=["greetings"],
            sources=["manual"],
        )
        # Call the nestable inner form inside an outer transaction.
        with transaction(conn):
            status, item_id = repo._import_vocabulary_item_inner(item)
            assert status == "created"
            assert item_id.startswith("vocab_")
        # Outer transaction committed by the context manager; row is visible.
        stored = repo.get_vocabulary_item(item_id)
        assert stored.lemma == "привіт"
    finally:
        conn.close()


def test_import_vocabulary_item_public_contract_unchanged(tmp_path) -> None:  # type: ignore[no-untyped-def]
    conn = connect(tmp_path / "db.sqlite3")
    try:
        repo = TutorRepository(conn)
        item = VocabularyItem(
            id=new_id("vocab"),
            target_language="uk",
            prompt="hello",
            lemma="привіт",
            accepted_answers=["привіт"],
            tags=["greetings"],
            sources=["manual"],
        )
        status, item_id = repo.import_vocabulary_item(item)
        assert status == "created"
        assert item_id.startswith("vocab_")
        assert repo.get_vocabulary_item(item_id).lemma == "привіт"
    finally:
        conn.close()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/unit/test_repositories.py::test_import_vocabulary_item_inner_runs_inside_caller_transaction -v`
Expected: FAIL with `AttributeError: 'TutorRepository' object has no attribute '_import_vocabulary_item_inner'`.

- [ ] **Step 3: Extract the nestable inner method**

In `src/language_tutor/dal/repositories.py`, replace the `import_vocabulary_item` method (lines 152-188) with two methods — a nestable inner body and a public wrapper that opens its own transaction:

```python
    def _import_vocabulary_item_inner(
        self, item: VocabularyItem
    ) -> tuple[Literal["created", "updated", "skipped"], str]:
        current_id = self.find_vocabulary_duplicate(item)
        if current_id is None:
            return "created", self.insert_vocabulary_item(item)
        row = self.conn.execute(
            "SELECT * FROM vocabulary_items WHERE id = ?", (current_id,)
        ).fetchone()
        current = self._row_to_vocab(row)
        accepted_answers, changed_answers = merge_display_values(
            current.accepted_answers, item.accepted_answers
        )
        notes, changed_notes = merge_display_values(current.notes, item.notes)
        sources, changed_sources = merge_display_values(current.sources, item.sources)
        tags, changed_tags = merge_tags(current.tags, item.tags)
        changed = changed_answers or changed_notes or changed_sources or changed_tags
        if not changed:
            return "skipped", current_id
        self.conn.execute(
            """
            UPDATE vocabulary_items
            SET accepted_answers_json = ?, notes_json = ?, sources_json = ?,
                tags_json = ?, updated_at = ?
            WHERE id = ?
            """,
            (
                json.dumps(accepted_answers, ensure_ascii=False),
                json.dumps(notes, ensure_ascii=False),
                json.dumps(sources, ensure_ascii=False),
                json.dumps(tags, ensure_ascii=False),
                now_iso(),
                current_id,
            ),
        )
        return "updated", current_id

    def import_vocabulary_item(
        self, item: VocabularyItem
    ) -> tuple[Literal["created", "updated", "skipped"], str]:
        with transaction(self.conn):
            return self._import_vocabulary_item_inner(item)
```

- [ ] **Step 4: Run the new + existing tests to verify they pass**

Run: `python -m pytest tests/unit/test_repositories.py -v`
Expected: PASS — both new tests pass AND the existing `test_import_merges_additive_metadata_without_review_reset` stays green (the public contract is preserved; only the body was extracted).

- [ ] **Step 5: Commit**

```bash
git add src/language_tutor/dal/repositories.py tests/unit/test_repositories.py
git commit -m "refactor(vocab): extract nestable _import_vocabulary_item_inner

Extract the find-or-create-with-merge body of import_vocabulary_item into a
nestable _import_vocabulary_item_inner that assumes the caller manages the
transaction. import_vocabulary_item wraps it in its own transaction, preserving
the existing public contract. Enables book.py to run the SRS card write and the
book_lookups insert in a single shared transaction."
```

---

## Task 2: Migration `005_book_lookups.sql` + enum updates + registration

**Files:**
- Create: `migrations/005_book_lookups.sql`
- Modify: `src/language_tutor/schemas.py` (add `BOOK` modality + `ANSWER_RECORDED` step_kind).
- Modify: `src/language_tutor/package_assets.py:9-14` (append to `REQUIRED_MIGRATION_FILES`).
- Modify: `tests/migration/test_004_sessions_checkpoints.py` (version list).
- Modify: `tests/migration/test_migrations.py` (version list + missing-files tuple).
- Test: `tests/migration/test_005_book_lookups.py` (new).

- [ ] **Step 1: Write the failing migration test**

Create `tests/migration/test_005_book_lookups.py`:

```python
from __future__ import annotations

import sqlite3
from pathlib import Path

from language_tutor.dal.sqlite_store import connect
from language_tutor.package_assets import REQUIRED_MIGRATION_FILES

MIGRATION_PATH = Path(__file__).resolve().parents[2] / "migrations" / "005_book_lookups.sql"


def test_005_creates_book_tables_and_expands_checkpoints(tmp_path) -> None:  # type: ignore[no-untyped-def]
    conn = connect(tmp_path / "db.sqlite3")
    try:
        tables = {
            row["name"]
            for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
        }
        assert {"book_sessions", "book_lookups"} <= tables

        session_cols = {
            row["name"] for row in conn.execute("PRAGMA table_info(book_sessions)").fetchall()
        }
        assert {
            "book_session_id",
            "session_id",
            "title",
            "title_norm",
            "author",
            "status",
            "started_at",
            "closed_at",
        } <= session_cols

        lookup_cols = {
            row["name"] for row in conn.execute("PRAGMA table_info(book_lookups)").fetchall()
        }
        assert {
            "lookup_id",
            "book_session_id",
            "kind",
            "content",
            "content_norm",
            "context",
            "explanation_json",
            "vocab_item_id",
            "created_at",
        } <= lookup_cols

        indexes = {
            row["name"]
            for row in conn.execute("SELECT name FROM sqlite_master WHERE type='index'")
        }
        assert {
            "idx_book_sessions_session",
            "idx_book_sessions_open_per_session",
            "idx_book_sessions_title_norm",
            "idx_book_lookups_session",
            "idx_book_lookups_word",
            "idx_checkpoints_session",
            "idx_checkpoints_created",
        } <= indexes

        # New modality + step_kind accepted by the rebuilt checkpoints CHECKs.
        conn.execute(
            "INSERT INTO sessions (id, host, status, started_at, last_seen_at) "
            "VALUES ('sess_t1', 'claude', 'open', '2026-06-22T00:00:00', '2026-06-22T00:00:00')"
        )
        conn.execute(
            "INSERT INTO checkpoints (id, session_id, modality, step_kind, state_json, summary, created_at) "
            "VALUES ('ckpt_b1', 'sess_t1', 'book', 'answer_recorded', '{}', 'lookup', '2026-06-22T00:00:00')"
        )
        conn.rollback()
    finally:
        conn.close()


def test_005_is_sequential_version_five(tmp_path) -> None:  # type: ignore[no-untyped-def]
    conn = connect(tmp_path / "db.sqlite3")
    try:
        versions = [
            int(row["version"])
            for row in conn.execute("SELECT version FROM migration_records ORDER BY version")
        ]
        assert versions == [1, 2, 3, 4, 5]
        names = {
            str(row["name"])
            for row in conn.execute("SELECT name FROM migration_records WHERE version = 5")
        }
        assert names == {"book_lookups"}
    finally:
        conn.close()


def test_005_is_idempotent_when_reapplied(tmp_path) -> None:  # type: ignore[no-untyped-def]
    db_path = tmp_path / "db.sqlite3"
    first = connect(db_path)
    first.close()
    second = connect(db_path)
    try:
        versions = [
            int(row["version"])
            for row in second.execute("SELECT version FROM migration_records ORDER BY version")
        ]
        assert versions == [1, 2, 3, 4, 5]
    finally:
        second.close()


def test_005_rebuild_is_atomic_on_mid_rebuild_failure(tmp_path) -> None:  # type: ignore[no-untyped-def]
    # Apply all migrations, seed a checkpoint row, then run a poisoned rebuild
    # that fails mid-script. The BEGIN/COMMIT-wrapped rebuild must roll back,
    # leaving the original checkpoints (rows + schema) intact.
    conn = connect(tmp_path / "db.sqlite3")
    try:
        conn.execute(
            "INSERT INTO sessions (id, host, status, started_at, last_seen_at) "
            "VALUES ('sess_a', 'claude', 'open', '2026-06-22T00:00:00', '2026-06-22T00:00:00')"
        )
        conn.execute(
            "INSERT INTO checkpoints (id, session_id, modality, step_kind, state_json, summary, created_at) "
            "VALUES ('ckpt_orig', 'sess_a', 'reading', 'prompt_shown', '{}', 'orig', '2026-06-22T00:00:00')"
        )
        conn.commit()
    finally:
        conn.close()

    # Build a poisoned 005 script: keep the BEGIN ... DROP TABLE checkpoints,
    # then inject a broken statement before COMMIT.
    sql = MIGRATION_PATH.read_text(encoding="utf-8")
    drop_pos = sql.index("DROP TABLE checkpoints;")
    poisoned = sql[: drop_pos + len("DROP TABLE checkpoints;")] + "\nSELECT no_such_function_x();\n"
    conn = connect(tmp_path / "db.sqlite3", migrate=False)
    try:
        try:
            conn.executescript(poisoned)
        except sqlite3.OperationalError:
            pass
        conn.rollback()
    finally:
        conn.close()

    # Reopen on a fresh connection (migration_records has no version 5 entry because
    # the poisoned run never completed). Verify the original row survived and the
    # real 005 applies cleanly.
    conn = connect(tmp_path / "db.sqlite3")
    try:
        row = conn.execute(
            "SELECT id, summary FROM checkpoints WHERE id = 'ckpt_orig'"
        ).fetchone()
        assert row is not None
        assert row["summary"] == "orig"
        versions = [
            int(row["version"])
            for row in conn.execute("SELECT version FROM migration_records ORDER BY version")
        ]
        assert versions == [1, 2, 3, 4, 5]
    finally:
        conn.close()


def test_005_registered_in_required_migration_files() -> None:  # type: ignore[no-untyped-def]
    assert "migrations/005_book_lookups.sql" in REQUIRED_MIGRATION_FILES
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `python -m pytest tests/migration/test_005_book_lookups.py -v`
Expected: FAIL — the migration file does not exist yet (`FileNotFoundError` / `connect` applies only 4 migrations).

- [ ] **Step 3: Create the migration**

Create `migrations/005_book_lookups.sql`:

```sql
-- Rebuild checkpoints to accept 'book' modality and 'answer_recorded' step_kind.
-- SQLite cannot ALTER a CHECK constraint, so the table is rebuilt inside an
-- explicit BEGIN/COMMIT so a mid-rebuild failure rolls back atomically.
-- Statement order is load-bearing: create new -> copy -> drop old (frees index
-- names) -> rename -> reindex. Do NOT use CREATE INDEX IF NOT EXISTS here.
BEGIN;

CREATE TABLE checkpoints_new (
  id TEXT PRIMARY KEY,
  session_id TEXT NOT NULL REFERENCES sessions(id),
  modality TEXT NOT NULL CHECK (modality IN ('lesson', 'reading', 'transcript', 'vocab', 'writing', 'progress', 'book')),
  step_kind TEXT NOT NULL CHECK (step_kind IN ('started', 'prompt_shown', 'feedback_shown', 'progress_shown', 'answer_recorded')),
  prompt_ref TEXT,
  state_json TEXT NOT NULL,
  summary TEXT NOT NULL,
  created_at TEXT NOT NULL
);

INSERT INTO checkpoints_new (id, session_id, modality, step_kind, prompt_ref, state_json, summary, created_at)
SELECT id, session_id, modality, step_kind, prompt_ref, state_json, summary, created_at FROM checkpoints;

DROP TABLE checkpoints;

ALTER TABLE checkpoints_new RENAME TO checkpoints;

CREATE INDEX idx_checkpoints_session ON checkpoints(session_id, created_at);
CREATE INDEX idx_checkpoints_created ON checkpoints(created_at);

COMMIT;

CREATE TABLE book_sessions (
  book_session_id  TEXT PRIMARY KEY,
  session_id       TEXT NOT NULL REFERENCES sessions(id),
  title            TEXT NOT NULL,
  title_norm       TEXT NOT NULL,
  author           TEXT,
  status           TEXT NOT NULL DEFAULT 'open',
  started_at       TEXT NOT NULL,
  closed_at        TEXT
);

CREATE INDEX idx_book_sessions_session ON book_sessions(session_id);
CREATE UNIQUE INDEX idx_book_sessions_open_per_session
  ON book_sessions(session_id, title_norm) WHERE status='open';
CREATE INDEX idx_book_sessions_title_norm ON book_sessions(title_norm, started_at DESC);

CREATE TABLE book_lookups (
  lookup_id        TEXT PRIMARY KEY,
  book_session_id  TEXT NOT NULL REFERENCES book_sessions(book_session_id),
  kind             TEXT NOT NULL,
  content          TEXT NOT NULL,
  content_norm     TEXT,
  context          TEXT,
  explanation_json TEXT NOT NULL,
  vocab_item_id    TEXT REFERENCES vocabulary_items(id) ON DELETE SET NULL,
  created_at       TEXT NOT NULL
);

CREATE INDEX idx_book_lookups_session ON book_lookups(book_session_id);
CREATE UNIQUE INDEX idx_book_lookups_word ON book_lookups(book_session_id, content_norm) WHERE kind='word';
```

- [ ] **Step 4: Add the enum values to `schemas.py`**

In `src/language_tutor/schemas.py`, update the two enums:

Find `CheckpointStepKind` (lines 83-87) and add `ANSWER_RECORDED`:

```python
class CheckpointStepKind(StrEnum):
    STARTED = "started"
    PROMPT_SHOWN = "prompt_shown"
    FEEDBACK_SHOWN = "feedback_shown"
    PROGRESS_SHOWN = "progress_shown"
    ANSWER_RECORDED = "answer_recorded"
```

Find `CheckpointModality` (lines 99-105) and add `BOOK`:

```python
class CheckpointModality(StrEnum):
    LESSON = "lesson"
    READING = "reading"
    TRANSCRIPT = "transcript"
    VOCAB = "vocab"
    WRITING = "writing"
    PROGRESS = "progress"
    BOOK = "book"
```

- [ ] **Step 5: Register the migration in `REQUIRED_MIGRATION_FILES`**

In `src/language_tutor/package_assets.py`, append the new file to the tuple (lines 9-14):

```python
REQUIRED_MIGRATION_FILES: tuple[str, ...] = (
    "migrations/001_initial.sql",
    "migrations/002_vocab_depth.sql",
    "migrations/003_progress_indexes.sql",
    "migrations/004_sessions_checkpoints.sql",
    "migrations/005_book_lookups.sql",
)
```

- [ ] **Step 6: Fix the existing migration tests' version lists**

In `tests/migration/test_004_sessions_checkpoints.py`, replace `[1, 2, 3, 4]` with `[1, 2, 3, 4, 5]` in `test_004_is_idempotent_when_reapplied` and `test_004_is_sequential_version_four` (two occurrences).

In `tests/migration/test_migrations.py`, replace every `[1, 2, 3, 4]` with `[1, 2, 3, 4, 5]` (two occurrences around lines 100 and 153), and in the `test_missing_packaged_migrations_fail_with_exact_names` test (around line 165-177) add `"migrations/005_book_lookups.sql"` to the expected missing-files tuple so it becomes:

```python
        assert missing == (
            "migrations/002_vocab_depth.sql",
            "migrations/003_progress_indexes.sql",
            "migrations/004_sessions_checkpoints.sql",
            "migrations/005_book_lookups.sql",
        )
```

(Read `tests/migration/test_migrations.py` first to confirm the exact variable name and surrounding context before editing.)

- [ ] **Step 7: Run the migration tests to verify they pass**

Run: `python -m pytest tests/migration/ -v`
Expected: PASS — all migration tests green (004 + 005 + the general `test_migrations.py`).

- [ ] **Step 8: Commit**

```bash
git add migrations/005_book_lookups.sql src/language_tutor/schemas.py \
        src/language_tutor/package_assets.py tests/migration/
git commit -m "feat(dal): add 005_book_lookups migration + book/answer_recorded enums

Creates book_sessions and book_lookups tables (FK-enforced, per-row dedup for
words). Rebuilds checkpoints inside an explicit BEGIN/COMMIT to expand its CHECK
constraints to accept the 'book' modality and 'answer_recorded' step_kind;
mid-rebuild failure rolls back atomically (gate test). Registers 005 in
REQUIRED_MIGRATION_FILES and bumps the existing migration tests' version lists."
```

---

## Task 3: Pydantic models for `book` + schema registration

**Files:**
- Modify: `src/language_tutor/schemas.py` (add ~11 models; add 5 entries to `export_json_schemas`).
- Modify: `tests/unit/test_schemas.py` (add mirror test).
- Generate: 5 new files under `schemas/` + copies under `specs/008-book-reading/contracts/` (Task 8 copies).

- [ ] **Step 1: Write the failing schema-mirror test**

Add to `tests/unit/test_schemas.py` (after `test_text_modality_schema_mirrors_export`):

```python
def test_book_schema_mirrors_export(tmp_path: Path) -> None:
    export_json_schemas(tmp_path)
    for filename, title in (
        ("book_record.schema.json", BookRecordInput.__name__),
        ("book_session.schema.json", BookSession.__name__),
        ("book_lookup_result.schema.json", BookLookupResult.__name__),
        ("book_log.schema.json", BookLog.__name__),
        ("book_list.schema.json", BookList.__name__),
    ):
        schema = json.loads((tmp_path / filename).read_text())
        assert schema["title"] == title
```

Also add the imports at the top of `tests/unit/test_schemas.py` (in the existing `from language_tutor.schemas import (...)` block):

```python
    BookList,
    BookListEntry,
    BookLog,
    BookLogEntry,
    BookLookupResult,
    BookRecordInput,
    BookSession,
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `python -m pytest tests/unit/test_schemas.py::test_book_schema_mirrors_export -v`
Expected: FAIL — `ImportError: cannot import name 'BookRecordInput' ...`

- [ ] **Step 3: Add the book pydantic models to `schemas.py`**

In `src/language_tutor/schemas.py`, add the following block IMMEDIATELY BEFORE the `export_json_schemas` function (find `def export_json_schemas(` and insert above it). Use `from typing import Any, Literal` — both are already imported at the top of `schemas.py`; confirm before relying on them.

```python
class BookStartInput(TutorModel):
    """CLI input for ``tutor book start``."""

    session_id: str
    title: str
    author: str | None = None


class BookRecordInput(TutorModel):
    """CLI input for ``tutor book record`` — the one complex book payload."""

    book_session_id: str
    kind: Literal["word", "sentence", "passage", "question"]
    content: str
    context: str | None = None
    explanation: dict[str, Any]


class BookResumeInput(TutorModel):
    """CLI input for ``tutor book resume``."""

    title: str


class BookLogInput(TutorModel):
    """CLI input for ``tutor book log``."""

    book_session_id: str


class BookCloseInput(TutorModel):
    """CLI input for ``tutor book close``."""

    book_session_id: str


class BookListInput(TutorModel):
    """CLI input for ``tutor book list`` (empty)."""


class BookSession(TutorModel):
    """A per-book reading session row."""

    book_session_id: str = Field(pattern=r"^book_[A-Za-z0-9]+$")
    session_id: str = Field(pattern=r"^sess_[A-Za-z0-9]+$")
    title: str
    author: str | None = None
    status: Literal["open", "closed"] = "open"
    started_at: datetime
    closed_at: datetime | None = None


class BookLookupResult(TutorModel):
    """Output of ``tutor book record`` — the persisted lookup + rendered markdown."""

    lookup_id: str = Field(pattern=r"^lookup_[A-Za-z0-9]+$")
    vocab_item_id: str | None = None
    deduped: bool
    created_at: datetime
    rendered: str


class BookLogEntry(TutorModel):
    """One lookup inside a ``tutor book log`` result."""

    lookup_id: str = Field(pattern=r"^lookup_[A-Za-z0-9]+$")
    kind: Literal["word", "sentence", "passage", "question"]
    content: str
    created_at: datetime
    rendered: str


class BookLog(TutorModel):
    """Output of ``tutor book log`` — ordered lookups + a rendered numbered list."""

    book_session_id: str = Field(pattern=r"^book_[A-Za-z0-9]+$")
    lookups: list[BookLogEntry]
    rendered: str


class BookListEntry(TutorModel):
    """One book session inside a ``tutor book list`` result."""

    book_session_id: str = Field(pattern=r"^book_[A-Za-z0-9]+$")
    session_id: str = Field(pattern=r"^sess_[A-Za-z0-9]+$")
    title: str
    author: str | None = None
    status: Literal["open", "closed"]
    started_at: datetime
    closed_at: datetime | None = None
    lookup_count: int = Field(ge=0)


class BookList(TutorModel):
    """Output of ``tutor book list`` — all book sessions, open first."""

    sessions: list[BookListEntry]
```

- [ ] **Step 4: Register the 5 schemas in `export_json_schemas`**

In `src/language_tutor/schemas.py`, inside the `mapping` dict in `export_json_schemas` (lines ~1412-1443), add 5 entries. Place them after the `text_modality_record.schema.json` / `reading_*` / `lesson_*` / `transcript_*` block (before the `host_*` block):

```python
        "book_record.schema.json": BookRecordInput,
        "book_session.schema.json": BookSession,
        "book_lookup_result.schema.json": BookLookupResult,
        "book_log.schema.json": BookLog,
        "book_list.schema.json": BookList,
```

- [ ] **Step 5: Run the schema test to verify it passes**

Run: `python -m pytest tests/unit/test_schemas.py::test_book_schema_mirrors_export -v`
Expected: PASS.

- [ ] **Step 6: Regenerate the committed `schemas/` directory**

There is no CLI command or automated gate that regenerates `schemas/` — the committed files are regenerated manually. Run this one-off regeneration from the repo root:

```bash
python -c "from pathlib import Path; from language_tutor.schemas import export_json_schemas; export_json_schemas(Path('schemas'))"
```

Then verify the 5 new files exist:

```bash
ls schemas/book_*.schema.json
```

Expected output lists: `schemas/book_list.schema.json`, `schemas/book_log.schema.json`, `schemas/book_lookup_result.schema.json`, `schemas/book_record.schema.json`, `schemas/book_session.schema.json`.

- [ ] **Step 7: Run the full schemas + adapter-contract tests**

Run: `python -m pytest tests/unit/test_schemas.py tests/adapter_contract/test_cli_json_contract.py -v`
Expected: PASS (the regeneration must not have drifted any existing schema — if a diff appears in an existing file, undo the regeneration and re-run; the existing models are unchanged so only new files should appear).

- [ ] **Step 8: Commit**

```bash
git add src/language_tutor/schemas.py tests/unit/test_schemas.py schemas/book_*.schema.json
git commit -m "feat(schemas): add book pydantic models + register 5 book schemas

Adds BookStartInput/BookRecordInput/BookResumeInput/BookLogInput/BookCloseInput/
BookListInput (input models) and BookSession/BookLookupResult/BookLogEntry/
BookLog/BookListEntry/BookList (output models). Registers book_record/
book_session/book_lookup_result/book_log/book_list schemas in export_json_schemas
and regenerates the committed schemas/ directory."
```

---

## Task 4: `BookRepository` class

**Files:**
- Create: `src/language_tutor/dal/book_repository.py`
- Test: `tests/unit/test_book_repository.py` (new — pure DAL unit tests; the higher-level handler tests live in Task 5).

- [ ] **Step 1: Write the failing DAL test**

Create `tests/unit/test_book_repository.py`:

```python
from __future__ import annotations

from datetime import UTC, datetime

import pytest

from language_tutor.dal.book_repository import BookRepository
from language_tutor.dal.repositories import TutorRepository, new_id
from language_tutor.dal.sqlite_store import connect
from language_tutor.errors import TutorError
from language_tutor.vocab import normalize_text


def _now() -> datetime:
    return datetime(2026, 6, 22, 12, 0, 0, tzinfo=UTC)


def _seed_session(conn, session_id: str = "sess_seed") -> None:  # type: ignore[no-untyped-def]
    conn.execute(
        "INSERT INTO sessions (id, host, status, started_at, last_seen_at) "
        "VALUES (?, 'claude', 'open', ?, ?)",
        (session_id, _now().isoformat(), _now().isoformat()),
    )
    conn.commit()


def test_start_creates_open_session(tmp_path) -> None:  # type: ignore[no-untyped-def]
    conn = connect(tmp_path / "db.sqlite3")
    try:
        _seed_session(conn)
        repo = BookRepository(conn)
        session = repo.start_book_session(
            session_id="sess_seed",
            title="The City of Dreaming Books",
            title_norm=normalize_text("The City of Dreaming Books"),
            author="Walter Moers",
            now=_now(),
        )
        assert session.book_session_id.startswith("book_")
        assert session.status == "open"
        assert session.title == "The City of Dreaming Books"
        assert session.author == "Walter Moers"
        assert session.closed_at is None
    finally:
        conn.close()


def test_start_is_idempotent_within_session_for_open_title(tmp_path) -> None:  # type: ignore[no-untyped-def]
    conn = connect(tmp_path / "db.sqlite3")
    try:
        _seed_session(conn)
        repo = BookRepository(conn)
        first = repo.start_book_session(
            session_id="sess_seed", title="Esquivo", title_norm=normalize_text("Esquivo"), author=None, now=_now()
        )
        second = repo.start_book_session(
            session_id="sess_seed", title="Esquivo", title_norm=normalize_text("Esquivo"), author="New Author", now=_now()
        )
        assert first.book_session_id == second.book_session_id
        # Author set on first start only; idempotent re-start ignores new author.
        assert second.author is None
    finally:
        conn.close()


def test_start_rejects_missing_session(tmp_path) -> None:  # type: ignore[no-untyped-def]
    conn = connect(tmp_path / "db.sqlite3")
    try:
        repo = BookRepository(conn)
        with pytest.raises(KeyError):
            repo.start_book_session(
                session_id="sess_missing", title="X", title_norm="x", author=None, now=_now()
            )
    finally:
        conn.close()


def test_start_rejects_closed_tutor_session(tmp_path) -> None:  # type: ignore[no-untyped-def]
    conn = connect(tmp_path / "db.sqlite3")
    try:
        conn.execute(
            "INSERT INTO sessions (id, host, status, started_at, last_seen_at, closed_at) "
            "VALUES ('sess_closed', 'claude', 'closed', ?, ?, ?)",
            (_now().isoformat(), _now().isoformat(), _now().isoformat()),
        )
        conn.commit()
        repo = BookRepository(conn)
        with pytest.raises(TutorError) as exc:
            repo.start_book_session(
                session_id="sess_closed", title="X", title_norm="x", author=None, now=_now()
            )
        assert exc.value.code == "session_not_open"
    finally:
        conn.close()


def test_resume_finds_most_recent_open_by_title(tmp_path) -> None:  # type: ignore[no-untyped-def]
    conn = connect(tmp_path / "db.sqlite3")
    try:
        _seed_session(conn)
        repo = BookRepository(conn)
        older = repo.start_book_session(
            session_id="sess_seed", title="Reread", title_norm=normalize_text("Reread"), author=None, now=_now()
        )
        # Simulate a second open book session for the same title (different tutor session).
        conn.execute(
            "INSERT INTO sessions (id, host, status, started_at, last_seen_at) "
            "VALUES ('sess_two', 'claude', 'open', ?, ?)",
            (_now().isoformat(), _now().isoformat()),
        )
        conn.commit()
        newer = repo.start_book_session(
            session_id="sess_two", title="Reread", title_norm=normalize_text("Reread"), author=None, now=_now()
        )
        # Insert with explicit started_at ordering: newer has later started_at.
        conn.execute(
            "UPDATE book_sessions SET started_at = ? WHERE book_session_id = ?",
            (_now().isoformat(), newer.book_session_id),
        )
        conn.execute(
            "UPDATE book_sessions SET started_at = ? WHERE book_session_id = ?",
            ("2026-01-01T00:00:00+00:00", older.book_session_id),
        )
        conn.commit()
        resumed = repo.get_open_book_session_by_title(normalize_text("Reread"))
        assert resumed is not None
        assert resumed.book_session_id == newer.book_session_id
    finally:
        conn.close()


def test_record_lookup_inserts_and_dedupes_words(tmp_path) -> None:  # type: ignore[no-untyped-def]
    conn = connect(tmp_path / "db.sqlite3")
    try:
        _seed_session(conn)
        repo = BookRepository(conn)
        session = repo.start_book_session(
            session_id="sess_seed", title="Bk", title_norm="bk", author=None, now=_now()
        )
        first = repo.record_lookup(
            book_session_id=session.book_session_id,
            kind="word",
            content="esquivo",
            content_norm=normalize_text("esquivo"),
            context=None,
            explanation_json='{"translation":"evasive"}',
            vocab_item_id="vocab_1",
            now=_now(),
        )
        assert first.deduped is False
        assert first.lookup_id.startswith("lookup_")
        second = repo.record_lookup(
            book_session_id=session.book_session_id,
            kind="word",
            content="Esquivo",
            content_norm=normalize_text("Esquivo"),
            context=None,
            explanation_json='{"translation":"evasive"}',
            vocab_item_id="vocab_1",
            now=_now(),
        )
        assert second.deduped is True
        assert second.lookup_id == first.lookup_id
    finally:
        conn.close()


def test_record_lookup_rejects_closed_session(tmp_path) -> None:  # type: ignore[no-untyped-def]
    conn = connect(tmp_path / "db.sqlite3")
    try:
        _seed_session(conn)
        repo = BookRepository(conn)
        session = repo.start_book_session(
            session_id="sess_seed", title="Bk", title_norm="bk", author=None, now=_now()
        )
        repo.close_book_session(session.book_session_id, now=_now())
        with pytest.raises(TutorError) as exc:
            repo.record_lookup(
                book_session_id=session.book_session_id,
                kind="word",
                content="x",
                content_norm="x",
                context=None,
                explanation_json='{"translation":"y"}',
                vocab_item_id=None,
                now=_now(),
            )
        assert exc.value.code == "book_session_closed"
    finally:
        conn.close()


def test_close_marks_closed_and_rejects_already_closed(tmp_path) -> None:  # type: ignore[no-untyped-def]
    conn = connect(tmp_path / "db.sqlite3")
    try:
        _seed_session(conn)
        repo = BookRepository(conn)
        session = repo.start_book_session(
            session_id="sess_seed", title="Bk", title_norm="bk", author=None, now=_now()
        )
        closed = repo.close_book_session(session.book_session_id, now=_now())
        assert closed.status == "closed"
        assert closed.closed_at is not None
        with pytest.raises(TutorError) as exc:
            repo.close_book_session(session.book_session_id, now=_now())
        assert exc.value.code == "book_session_already_closed"
    finally:
        conn.close()


def test_list_orders_open_first_then_closed(tmp_path) -> None:  # type: ignore[no-untyped-def]
    conn = connect(tmp_path / "db.sqlite3")
    try:
        _seed_session(conn)
        repo = BookRepository(conn)
        a = repo.start_book_session(
            session_id="sess_seed", title="A", title_norm="a", author=None, now=_now()
        )
        b = repo.start_book_session(
            session_id="sess_seed", title="B", title_norm="b", author=None, now=_now()
        )
        repo.close_book_session(a.book_session_id, now=_now())
        sessions = repo.list_book_sessions()
        # Open (B) first, then closed (A).
        assert sessions[0].book_session_id == b.book_session_id
        assert sessions[0].status == "open"
        assert sessions[1].book_session_id == a.book_session_id
        assert sessions[1].status == "closed"
        assert sessions[0].lookup_count == 0
    finally:
        conn.close()


def test_get_lookups_orders_by_created_at_ascending(tmp_path) -> None:  # type: ignore[no-untyped-def]
    conn = connect(tmp_path / "db.sqlite3")
    try:
        _seed_session(conn)
        repo = BookRepository(conn)
        session = repo.start_book_session(
            session_id="sess_seed", title="Bk", title_norm="bk", author=None, now=_now()
        )
        repo.record_lookup(
            book_session_id=session.book_session_id, kind="sentence", content="one",
            content_norm=None, context=None, explanation_json='{"translation":"1"}',
            vocab_item_id=None, now=datetime(2026, 6, 22, 12, 1, 0, tzinfo=UTC),
        )
        repo.record_lookup(
            book_session_id=session.book_session_id, kind="sentence", content="two",
            content_norm=None, context=None, explanation_json='{"translation":"2"}',
            vocab_item_id=None, now=datetime(2026, 6, 22, 12, 0, 0, tzinfo=UTC),
        )
        lookups = repo.get_lookups(session.book_session_id)
        assert [lk.content for lk in lookups] == ["two", "one"]
    finally:
        conn.close()
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `python -m pytest tests/unit/test_book_repository.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'language_tutor.dal.book_repository'`.

- [ ] **Step 3: Implement `BookRepository`**

Create `src/language_tutor/dal/book_repository.py`:

```python
"""Persistence for the book-reading companion (book_sessions + book_lookups)."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from typing import Any, Literal

from language_tutor.dal.sqlite_store import transaction
from language_tutor.errors import TutorError
from language_tutor.schemas import (
    BookListEntry,
    BookList,
    BookLogEntry,
    BookLog,
    BookLookupResult,
    BookSession,
)


class BookRepository:
    """Owns the ``book_sessions`` and ``book_lookups`` tables.

    Shares one ``conn`` with ``TutorRepository`` so the SRS card write and the
    lookup insert can run in a single caller-managed transaction (see
    ``book.record_book``). App-layer existence checks supplement the DDL FKs
    (``PRAGMA foreign_keys = ON``), mirroring ``record_checkpoint``.
    """

    def __init__(self, conn: sqlite3.Connection) -> None:
        self.conn = conn

    def start_book_session(
        self,
        *,
        session_id: str,
        title: str,
        title_norm: str,
        author: str | None,
        now: datetime,
    ) -> BookSession:
        with transaction(self.conn):
            row = self.conn.execute(
                "SELECT id, status FROM sessions WHERE id = ?", (session_id,)
            ).fetchone()
            if row is None:
                raise KeyError(session_id)
            if row["status"] != "open":
                raise TutorError(
                    "session_not_open",
                    f"Session {session_id} is not open.",
                    "Call session-start first and use an open session_id.",
                )
            existing = self.conn.execute(
                "SELECT * FROM book_sessions WHERE session_id = ? AND title_norm = ? AND status = 'open'",
                (session_id, title_norm),
            ).fetchone()
            if existing is not None:
                return self._row_to_session(existing)
            book_session_id = f"book_{_uuid_hex()}"
            self.conn.execute(
                """
                INSERT INTO book_sessions (
                    book_session_id, session_id, title, title_norm, author, status, started_at, closed_at
                ) VALUES (?, ?, ?, ?, ?, 'open', ?, NULL)
                """,
                (book_session_id, session_id, title, title_norm, author, now.isoformat()),
            )
            row = self.conn.execute(
                "SELECT * FROM book_sessions WHERE book_session_id = ?", (book_session_id,)
            ).fetchone()
            return self._row_to_session(row)

    def get_open_book_session_by_title(self, title_norm: str) -> BookSession | None:
        row = self.conn.execute(
            "SELECT * FROM book_sessions WHERE title_norm = ? AND status = 'open' "
            "ORDER BY started_at DESC, book_session_id DESC LIMIT 1",
            (title_norm,),
        ).fetchone()
        return self._row_to_session(row) if row is not None else None

    def get_book_session(self, book_session_id: str) -> BookSession | None:
        row = self.conn.execute(
            "SELECT * FROM book_sessions WHERE book_session_id = ?", (book_session_id,)
        ).fetchone()
        return self._row_to_session(row) if row is not None else None

    def list_book_sessions(self) -> BookList:
        rows = self.conn.execute(
            "SELECT bs.*, COUNT(bl.lookup_id) AS lookup_count "
            "FROM book_sessions bs "
            "LEFT JOIN book_lookups bl ON bl.book_session_id = bs.book_session_id "
            "GROUP BY bs.book_session_id "
            "ORDER BY CASE bs.status WHEN 'open' THEN 0 ELSE 1 END, bs.started_at DESC, bs.book_session_id DESC"
        ).fetchall()
        sessions = [self._row_to_list_entry(row) for row in rows]
        return BookList(sessions=sessions)

    def record_lookup(
        self,
        *,
        book_session_id: str,
        kind: str,
        content: str,
        content_norm: str | None,
        context: str | None,
        explanation_json: str,
        vocab_item_id: str | None,
        now: datetime,
    ) -> BookLookupResult:
        with transaction(self.conn):
            return self._record_lookup_inner(
                book_session_id=book_session_id,
                kind=kind,
                content=content,
                content_norm=content_norm,
                context=context,
                explanation_json=explanation_json,
                vocab_item_id=vocab_item_id,
                now=now,
            )

    def _record_lookup_inner(
        self,
        *,
        book_session_id: str,
        kind: str,
        content: str,
        content_norm: str | None,
        context: str | None,
        explanation_json: str,
        vocab_item_id: str | None,
        now: datetime,
    ) -> BookLookupResult:
        session_row = self.conn.execute(
            "SELECT status FROM book_sessions WHERE book_session_id = ?", (book_session_id,)
        ).fetchone()
        if session_row is None:
            raise KeyError(book_session_id)
        if session_row["status"] != "open":
            raise TutorError(
                "book_session_closed",
                "This reading session is closed.",
                "Call `tutor book start` for a new session or `tutor book resume` to continue an open one.",
            )
        if kind == "word" and content_norm is not None:
            existing = self.conn.execute(
                "SELECT * FROM book_lookups WHERE book_session_id = ? AND kind = 'word' AND content_norm = ?",
                (book_session_id, content_norm),
            ).fetchone()
            if existing is not None:
                return self._row_to_lookup_result(existing)
        lookup_id = f"lookup_{_uuid_hex()}"
        self.conn.execute(
            """
            INSERT INTO book_lookups (
                lookup_id, book_session_id, kind, content, content_norm, context,
                explanation_json, vocab_item_id, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                lookup_id, book_session_id, kind, content, content_norm, context,
                explanation_json, vocab_item_id, now.isoformat(),
            ),
        )
        row = self.conn.execute(
            "SELECT * FROM book_lookups WHERE lookup_id = ?", (lookup_id,)
        ).fetchone()
        return self._row_to_lookup_result(row)

    def get_lookups(self, book_session_id: str) -> BookLog:
        rows = self.conn.execute(
            "SELECT * FROM book_lookups WHERE book_session_id = ? ORDER BY created_at ASC, lookup_id ASC",
            (book_session_id,),
        ).fetchall()
        entries = [
            BookLogEntry(
                lookup_id=str(row["lookup_id"]),
                kind=str(row["kind"]),  # type: ignore[arg-type]
                content=str(row["content"]),
                created_at=_parse_iso(row["created_at"]),
                rendered="",
            )
            for row in rows
        ]
        return BookLog(book_session_id=book_session_id, lookups=entries, rendered="")

    def close_book_session(self, book_session_id: str, *, now: datetime) -> BookSession:
        with transaction(self.conn):
            row = self.conn.execute(
                "SELECT * FROM book_sessions WHERE book_session_id = ?", (book_session_id,)
            ).fetchone()
            if row is None:
                raise KeyError(book_session_id)
            if row["status"] == "closed":
                raise TutorError(
                    "book_session_already_closed",
                    "This reading session is already closed.",
                    "Start a new session with `tutor book start`.",
                )
            self.conn.execute(
                "UPDATE book_sessions SET status = 'closed', closed_at = ? WHERE book_session_id = ?",
                (now.isoformat(), book_session_id),
            )
            row = self.conn.execute(
                "SELECT * FROM book_sessions WHERE book_session_id = ?", (book_session_id,)
            ).fetchone()
            return self._row_to_session(row)

    def _row_to_session(self, row: sqlite3.Row) -> BookSession:
        return BookSession(
            book_session_id=str(row["book_session_id"]),
            session_id=str(row["session_id"]),
            title=str(row["title"]),
            author=str(row["author"]) if row["author"] is not None else None,
            status=str(row["status"]),  # type: ignore[arg-type]
            started_at=_parse_iso(row["started_at"]),
            closed_at=_parse_iso(row["closed_at"]) if row["closed_at"] is not None else None,
        )

    def _row_to_list_entry(self, row: sqlite3.Row) -> BookListEntry:
        return BookListEntry(
            book_session_id=str(row["book_session_id"]),
            session_id=str(row["session_id"]),
            title=str(row["title"]),
            author=str(row["author"]) if row["author"] is not None else None,
            status=str(row["status"]),  # type: ignore[arg-type]
            started_at=_parse_iso(row["started_at"]),
            closed_at=_parse_iso(row["closed_at"]) if row["closed_at"] is not None else None,
            lookup_count=int(row["lookup_count"]),
        )

    def _row_to_lookup_result(self, row: sqlite3.Row) -> BookLookupResult:
        return BookLookupResult(
            lookup_id=str(row["lookup_id"]),
            vocab_item_id=str(row["vocab_item_id"]) if row["vocab_item_id"] is not None else None,
            deduped=False,
            created_at=_parse_iso(row["created_at"]),
            rendered="",
        )


def _uuid_hex() -> str:
    import uuid

    return uuid.uuid4().hex


def _parse_iso(value: str) -> datetime:
    return datetime.fromisoformat(str(value))
```

Note: the `_record_lookup_inner` returns `deduped=False` for the freshly inserted row; the `record_book` handler in Task 5 overrides `deduped` to `True` for the dedup-hit path (it detects dedup before calling insert). The `rendered` field is left empty here — `book.py`'s handler populates it from the deterministic `render_*` helpers. These two fields are presentation-layer concerns owned by the handler, not the repository.

- [ ] **Step 4: Run the DAL tests to verify they pass**

Run: `python -m pytest tests/unit/test_book_repository.py -v`
Expected: PASS — all 10 tests green.

- [ ] **Step 5: Commit**

```bash
git add src/language_tutor/dal/book_repository.py tests/unit/test_book_repository.py
git commit -m "feat(dal): add BookRepository for book_sessions + book_lookups

One BookRepository(conn) covers both book tables (a single parent/child
aggregate sharing a lifecycle and transaction). App-layer existence checks
supplement the DDL FKs. Word lookups dedup per (book_session_id, content_norm).
resume tiebreaks by started_at DESC, book_session_id DESC. list orders open
first then closed, newest first, with lookup_count."
```

---

## Task 5: `book.py` handlers + `find_or_create_vocab_card_for_book` + rendering

**Files:**
- Create: `src/language_tutor/book.py`
- Modify: `src/language_tutor/vocab.py` (add `find_or_create_vocab_card_for_book`).
- Test: `tests/unit/test_book.py` (new — handler-level unit tests with a real sqlite DB).

- [ ] **Step 1: Write the failing handler test**

Create `tests/unit/test_book.py`:

```python
from __future__ import annotations

import json
from datetime import UTC, datetime

import pytest

from language_tutor.book import (
    close_book,
    list_book,
    log_book,
    record_book,
    resume_book,
    start_book,
)
from language_tutor.dal.book_repository import BookRepository
from language_tutor.dal.repositories import TutorRepository
from language_tutor.dal.sqlite_store import connect
from language_tutor.errors import TutorError


def _now() -> datetime:
    return datetime(2026, 6, 22, 12, 0, 0, tzinfo=UTC)


def _seed(conn, session_id: str = "sess_seed") -> None:  # type: ignore[no-untyped-def]
    conn.execute(
        "INSERT INTO sessions (id, host, status, started_at, last_seen_at) "
        "VALUES (?, 'claude', 'open', ?, ?)",
        (session_id, _now().isoformat(), _now().isoformat()),
    )
    conn.commit()


def _repos(conn):  # type: ignore[no-untyped-def]
    return BookRepository(conn), TutorRepository(conn)


def test_start_book_returns_session(tmp_path) -> None:  # type: ignore[no-untyped-def]
    conn = connect(tmp_path / "db.sqlite3")
    try:
        _seed(conn)
        book_repo, _ = _repos(conn)
        session = start_book(book_repo, session_id="sess_seed", title="Esquivo", author="Cela", now=_now())
        assert session.title == "Esquivo"
        assert session.author == "Cela"
    finally:
        conn.close()


def test_record_word_feeds_srs_on_usable_translation(tmp_path) -> None:  # type: ignore[no-untyped-def]
    conn = connect(tmp_path / "db.sqlite3")
    try:
        _seed(conn)
        book_repo, tutor_repo = _repos(conn)
        session = start_book(book_repo, session_id="sess_seed", title="Bk", author=None, now=_now())
        result = record_book(
            book_repo=book_repo,
            tutor_repo=tutor_repo,
            book_session_id=session.book_session_id,
            kind="word",
            content="esquivo",
            context=None,
            explanation={"translation": "evasive", "gloss": "adjective"},
            target_language="es",
            now=_now(),
        )
        assert result.deduped is False
        assert result.vocab_item_id is not None
        assert result.vocab_item_id.startswith("vocab_")
        assert "evasive" in result.rendered
        assert "esquivo" in result.rendered
    finally:
        conn.close()


def test_record_word_skips_srs_on_echo_translation(tmp_path) -> None:  # type: ignore[no-untyped-def]
    conn = connect(tmp_path / "db.sqlite3")
    try:
        _seed(conn)
        book_repo, tutor_repo = _repos(conn)
        session = start_book(book_repo, session_id="sess_seed", title="Bk", author=None, now=_now())
        result = record_book(
            book_repo=book_repo, tutor_repo=tutor_repo,
            book_session_id=session.book_session_id, kind="word", content="hello",
            context=None, explanation={"translation": "hello"}, target_language="en", now=_now(),
        )
        assert result.vocab_item_id is None
        assert "hello" in result.rendered
    finally:
        conn.close()


def test_record_word_skips_srs_on_missing_translation(tmp_path) -> None:  # type: ignore[no-untyped-def]
    conn = connect(tmp_path / "db.sqlite3")
    try:
        _seed(conn)
        book_repo, tutor_repo = _repos(conn)
        session = start_book(book_repo, session_id="sess_seed", title="Bk", author=None, now=_now())
        result = record_book(
            book_repo=book_repo, tutor_repo=tutor_repo,
            book_session_id=session.book_session_id, kind="word", content="x",
            context=None, explanation={"translation": ""}, target_language="en", now=_now(),
        )
        assert result.vocab_item_id is None
        assert result.rendered == "**x**"
    finally:
        conn.close()


def test_record_word_dedup_returns_existing_no_srs_refeed(tmp_path) -> None:  # type: ignore[no-untyped-def]
    conn = connect(tmp_path / "db.sqlite3")
    try:
        _seed(conn)
        book_repo, tutor_repo = _repos(conn)
        session = start_book(book_repo, session_id="sess_seed", title="Bk", author=None, now=_now())
        first = record_book(
            book_repo=book_repo, tutor_repo=tutor_repo,
            book_session_id=session.book_session_id, kind="word", content="esquivo",
            context=None, explanation={"translation": "evasive"}, target_language="es", now=_now(),
        )
        second = record_book(
            book_repo=book_repo, tutor_repo=tutor_repo,
            book_session_id=session.book_session_id, kind="word", content="Esquivo",
            context=None, explanation={"translation": "evasive"}, target_language="es", now=_now(),
        )
        assert second.deduped is True
        assert second.lookup_id == first.lookup_id
        assert second.vocab_item_id == first.vocab_item_id
    finally:
        conn.close()


def test_record_sentence_passage_question_shapes(tmp_path) -> None:  # type: ignore[no-untyped-def]
    conn = connect(tmp_path / "db.sqlite3")
    try:
        _seed(conn)
        book_repo, tutor_repo = _repos(conn)
        session = start_book(book_repo, session_id="sess_seed", title="Bk", author=None, now=_now())
        s = record_book(
            book_repo=book_repo, tutor_repo=tutor_repo,
            book_session_id=session.book_session_id, kind="sentence", content="Hola mundo",
            context=None, explanation={"translation": "Hello world"}, target_language="es", now=_now(),
        )
        assert s.rendered == "> Hola mundo\n\nHello world"
        p = record_book(
            book_repo=book_repo, tutor_repo=tutor_repo,
            book_session_id=session.book_session_id, kind="passage", content="Long passage",
            context=None, explanation={"translation": "Translation"}, target_language="es", now=_now(),
        )
        assert p.rendered == "> Long passage\n\nTranslation"
        q = record_book(
            book_repo=book_repo, tutor_repo=tutor_repo,
            book_session_id=session.book_session_id, kind="question", content="Why?",
            context=None, explanation={"answer": "Because."}, target_language="es", now=_now(),
        )
        assert q.rendered == "Q: Why?\nA: Because."
    finally:
        conn.close()


def test_record_rejects_closed_session(tmp_path) -> None:  # type: ignore[no-untyped-def]
    conn = connect(tmp_path / "db.sqlite3")
    try:
        _seed(conn)
        book_repo, tutor_repo = _repos(conn)
        session = start_book(book_repo, session_id="sess_seed", title="Bk", author=None, now=_now())
        close_book(book_repo, book_session_id=session.book_session_id, now=_now())
        with pytest.raises(TutorError) as exc:
            record_book(
                book_repo=book_repo, tutor_repo=tutor_repo,
                book_session_id=session.book_session_id, kind="word", content="x",
                context=None, explanation={"translation": "y"}, target_language="en", now=_now(),
            )
        assert exc.value.code == "book_session_closed"
    finally:
        conn.close()


def test_resume_finds_open_by_title(tmp_path) -> None:  # type: ignore[no-untyped-def]
    conn = connect(tmp_path / "db.sqlite3")
    try:
        _seed(conn)
        book_repo, _ = _repos(conn)
        start_book(book_repo, session_id="sess_seed", title="Esquivo", author=None, now=_now())
        resumed = resume_book(book_repo, title="Esquivo")
        assert resumed is not None
        assert resumed.title == "Esquivo"
    finally:
        conn.close()


def test_resume_missing_title_returns_none(tmp_path) -> None:  # type: ignore[no-untyped-def]
    conn = connect(tmp_path / "db.sqlite3")
    try:
        _seed(conn)
        book_repo, _ = _repos(conn)
        assert resume_book(book_repo, title="Nope") is None
    finally:
        conn.close()


def test_log_returns_rendered_numbered_list(tmp_path) -> None:  # type: ignore[no-untyped-def]
    conn = connect(tmp_path / "db.sqlite3")
    try:
        _seed(conn)
        book_repo, tutor_repo = _repos(conn)
        session = start_book(book_repo, session_id="sess_seed", title="Bk", author=None, now=_now())
        record_book(
            book_repo=book_repo, tutor_repo=tutor_repo,
            book_session_id=session.book_session_id, kind="word", content="esquivo",
            context=None, explanation={"translation": "evasive"}, target_language="es",
            now=datetime(2026, 6, 22, 12, 0, 0, tzinfo=UTC),
        )
        record_book(
            book_repo=book_repo, tutor_repo=tutor_repo,
            book_session_id=session.book_session_id, kind="question", content="Why?",
            context=None, explanation={"answer": "Because."}, target_language="es",
            now=datetime(2026, 6, 22, 12, 1, 0, tzinfo=UTC),
        )
        log = log_book(book_repo, book_session_id=session.book_session_id)
        assert len(log.lookups) == 2
        assert log.lookups[0].content == "esquivo"
        assert log.rendered.startswith("1. [word]")
        assert "2. [question]" in log.rendered
    finally:
        conn.close()


def test_list_returns_sessions_open_first(tmp_path) -> None:  # type: ignore[no-untyped-def]
    conn = connect(tmp_path / "db.sqlite3")
    try:
        _seed(conn)
        book_repo, _ = _repos(conn)
        a = start_book(book_repo, session_id="sess_seed", title="A", author=None, now=_now())
        start_book(book_repo, session_id="sess_seed", title="B", author=None, now=_now())
        close_book(book_repo, book_session_id=a.book_session_id, now=_now())
        result = list_book(book_repo)
        assert [s.status for s in result.sessions] == ["open", "closed"]
    finally:
        conn.close()


def test_global_card_dedup_across_books(tmp_path) -> None:  # type: ignore[no-untyped-def]
    conn = connect(tmp_path / "db.sqlite3")
    try:
        _seed(conn, "sess_one")
        _seed(conn, "sess_two")
        book_repo, tutor_repo = _repos(conn)
        b1 = start_book(book_repo, session_id="sess_one", title="Book One", author=None, now=_now())
        b2 = start_book(book_repo, session_id="sess_two", title="Book Two", author=None, now=_now())
        first = record_book(
            book_repo=book_repo, tutor_repo=tutor_repo,
            book_session_id=b1.book_session_id, kind="word", content="esquivo",
            context=None, explanation={"translation": "evasive"}, target_language="es", now=_now(),
        )
        second = record_book(
            book_repo=book_repo, tutor_repo=tutor_repo,
            book_session_id=b2.book_session_id, kind="word", content="esquivo",
            context=None, explanation={"translation": "evasive"}, target_language="es", now=_now(),
        )
        # Per-book lookup dedup is independent (different book_session_id) -> not deduped.
        assert second.deduped is False
        # Global SRS card dedup -> same vocab card.
        assert second.vocab_item_id == first.vocab_item_id
    finally:
        conn.close()
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `python -m pytest tests/unit/test_book.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'language_tutor.book'`.

- [ ] **Step 3: Add `find_or_create_vocab_card_for_book` to `vocab.py`**

In `src/language_tutor/vocab.py`, add this helper (place it after `add_vocab_card`, around line 400). It composes a `VocabularyCardDefinition` and reuses `item_from_definition` + the nestable `_import_vocabulary_item_inner` (DRY — no hand-built `VocabularyItem`).

```python
def find_or_create_vocab_card_for_book(
    repo: TutorRepository,
    *,
    word: str,
    translation: str,
    gloss: str | None,
    book_source: str,
    target_language: str,
) -> tuple[Literal["created", "updated", "skipped"], str]:
    """Find-or-create the global SRS card for a book word lookup.

    Composes a VocabularyCardDefinition (card_type=standard, target=word -> lemma,
    prompt=word, accepted_answers=[translation], tags=["from-book"], source=book)
    and reuses item_from_definition + the nestable _import_vocabulary_item_inner
    so the card write merges into the caller's outer transaction. The card is
    deduped globally by standard:<word>:<word>.
    """
    definition = VocabularyCardDefinition(
        card_type="standard",
        target=word,
        prompt=word,
        accepted_answers=[translation],
        hint=gloss,
        notes=[gloss] if gloss else None,
        source=book_source,
        tags=["from-book"],
    )
    item = item_from_definition(definition, target_language, repo.create_id("vocab"))
    return repo._import_vocabulary_item_inner(item)
```

Ensure `Literal` is imported at the top of `vocab.py` (check the existing imports — `from typing import ...` should include `Literal`; if not, add it). `VocabularyCardDefinition` and `item_from_definition` are already imported/defined in `vocab.py`.

- [ ] **Step 4: Implement `book.py`**

Create `src/language_tutor/book.py`:

```python
"""Book-reading companion handlers (pure functions; CLI layer calls these)."""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any

from language_tutor.dal.book_repository import BookRepository
from language_tutor.dal.repositories import TutorRepository
from language_tutor.dal.sqlite_store import transaction
from language_tutor.errors import TutorError
from language_tutor.schemas import BookList, BookLog, BookLookupResult, BookSession
from language_tutor.vocab import find_or_create_vocab_card_for_book, normalize_text


def start_book(
    repo: BookRepository,
    *,
    session_id: str,
    title: str,
    author: str | None,
    now: datetime,
) -> BookSession:
    if not title.strip():
        raise TutorError(
            "invalid_book_start",
            "A title is required to start a reading session.",
            "Pass a non-empty title.",
        )
    return repo.start_book_session(
        session_id=session_id,
        title=title,
        title_norm=normalize_text(title),
        author=author,
        now=now,
    )


def record_book(
    *,
    book_repo: BookRepository,
    tutor_repo: TutorRepository,
    book_session_id: str,
    kind: str,
    content: str,
    context: str | None,
    explanation: dict[str, Any],
    target_language: str,
    now: datetime,
) -> BookLookupResult:
    if not content.strip():
        raise TutorError(
            "invalid_book_record",
            "content is required.",
            "Pass a non-empty word/sentence/passage/question.",
        )
    _validate_explanation_shape(kind, explanation)

    session = book_repo.get_book_session(book_session_id)
    if session is None:
        raise KeyError(book_session_id)
    if session.status != "open":
        raise TutorError(
            "book_session_closed",
            "This reading session is closed.",
            "Call `tutor book start` for a new session or `tutor book resume` to continue an open one.",
        )

    content_norm = normalize_text(content) if kind == "word" else None
    book_source = session.title if session.author is None else f"{session.title} — {session.author}"

    if kind == "word":
        # Per-book word dedup: return existing row, no SRS re-feed.
        existing = book_repo._find_word_lookup(book_session_id, content_norm)  # type: ignore[attr-defined]
        if existing is not None:
            return BookLookupResult(
                lookup_id=existing.lookup_id,
                vocab_item_id=existing.vocab_item_id,
                deduped=True,
                created_at=existing.created_at,
                rendered=existing.rendered,
            )

        translation = str(explanation.get("translation", "")).strip()
        gloss = explanation.get("gloss")
        gloss_str = str(gloss).strip() if gloss else None
        usable = bool(translation) and normalize_text(translation) != normalize_text(content)

        if usable:
            with transaction(book_repo.conn):
                _status, vocab_item_id = find_or_create_vocab_card_for_book(
                    tutor_repo,
                    word=content,
                    translation=translation,
                    gloss=gloss_str,
                    book_source=book_source,
                    target_language=target_language,
                )
                result = book_repo._record_lookup_inner(
                    book_session_id=book_session_id,
                    kind=kind,
                    content=content,
                    content_norm=content_norm,
                    context=context,
                    explanation_json=json.dumps(explanation, ensure_ascii=False),
                    vocab_item_id=vocab_item_id,
                    now=now,
                )
        else:
            result = book_repo.record_lookup(
                book_session_id=book_session_id,
                kind=kind,
                content=content,
                content_norm=content_norm,
                context=context,
                explanation_json=json.dumps(explanation, ensure_ascii=False),
                vocab_item_id=None,
                now=now,
            )
        return BookLookupResult(
            lookup_id=result.lookup_id,
            vocab_item_id=result.vocab_item_id,
            deduped=False,
            created_at=result.created_at,
            rendered=render_lookup(kind, content, explanation),
        )

    result = book_repo.record_lookup(
        book_session_id=book_session_id,
        kind=kind,
        content=content,
        content_norm=None,
        context=context,
        explanation_json=json.dumps(explanation, ensure_ascii=False),
        vocab_item_id=None,
        now=now,
    )
    return BookLookupResult(
        lookup_id=result.lookup_id,
        vocab_item_id=result.vocab_item_id,
        deduped=False,
        created_at=result.created_at,
        rendered=render_lookup(kind, content, explanation),
    )


def resume_book(repo: BookRepository, *, title: str) -> BookSession | None:
    return repo.get_open_book_session_by_title(normalize_text(title))


def log_book(repo: BookRepository, *, book_session_id: str) -> BookLog:
    log = repo.get_lookups(book_session_id)
    entries = []
    for n, entry in enumerate(log.lookups, start=1):
        explanation = json.loads(_read_explanation(repo, entry.lookup_id))
        rendered = render_lookup(entry.kind, entry.content, explanation)
        entries.append(entry.model_copy(update={"rendered": rendered}))
    full_rendered = "\n".join(
        f"{n}. [{entry.kind}] {entry.rendered}" for n, entry in enumerate(entries, start=1)
    )
    return log.model_copy(update={"lookups": entries, "rendered": full_rendered})


def list_book(repo: BookRepository) -> BookList:
    return repo.list_book_sessions()


def close_book(repo: BookRepository, *, book_session_id: str, now: datetime) -> BookSession:
    return repo.close_book_session(book_session_id, now=now)


def _validate_explanation_shape(kind: str, explanation: dict[str, Any]) -> None:
    if kind == "word":
        if "translation" not in explanation:
            raise TutorError(
                "invalid_book_record",
                "word explanation requires a 'translation' field (may be empty).",
                "Pass {\"translation\": \"...\", \"gloss\"?: \"...\"}.",
            )
    elif kind in ("sentence", "passage"):
        if "translation" not in explanation:
            raise TutorError(
                "invalid_book_record",
                f"{kind} explanation requires a 'translation' field.",
                f"Pass {{\"translation\": \"...\"}}.",
            )
    elif kind == "question":
        if "answer" not in explanation:
            raise TutorError(
                "invalid_book_record",
                "question explanation requires an 'answer' field.",
                "Pass {\"answer\": \"...\"}.",
            )


def render_lookup(kind: str, content: str, explanation: dict[str, Any]) -> str:
    if kind == "word":
        translation = str(explanation.get("translation", "")).strip()
        gloss = explanation.get("gloss")
        gloss_str = str(gloss).strip() if gloss else None
        rendered = f"**{content}**"
        if gloss_str:
            rendered += f" — {gloss_str}"
        if translation:
            rendered += f" (translation: {translation})"
        return rendered
    if kind == "sentence":
        return f"> {content}\n\n{explanation.get('translation', '')}"
    if kind == "passage":
        body = explanation.get("translation") or explanation.get("explanation", "")
        return f"> {content}\n\n{body}"
    if kind == "question":
        return f"Q: {content}\nA: {explanation.get('answer', '')}"
    raise TutorError("invalid_book_record", f"Unknown kind: {kind}", "Use word/sentence/passage/question.")


def _read_explanation(repo: BookRepository, lookup_id: str) -> str:
    row = repo.conn.execute(
        "SELECT explanation_json FROM book_lookups WHERE lookup_id = ?", (lookup_id,)
    ).fetchone()
    return str(row["explanation_json"]) if row is not None else "{}"
```

- [ ] **Step 5: Add the `_find_word_lookup` helper to `BookRepository`**

The `record_book` handler needs a read-only dedup probe. Add this method to `BookRepository` in `src/language_tutor/dal/book_repository.py` (place it next to `_record_lookup_inner`):

```python
    def _find_word_lookup(self, book_session_id: str, content_norm: str) -> BookLookupResult | None:
        row = self.conn.execute(
            "SELECT * FROM book_lookups WHERE book_session_id = ? AND kind = 'word' AND content_norm = ?",
            (book_session_id, content_norm),
        ).fetchone()
        if row is None:
            return None
        # Rendering for the deduped row: re-read the explanation blob.
        explanation = json.loads(str(row["explanation_json"]))
        rendered = _render_lookup(str(row["kind"]), str(row["content"]), explanation)
        return BookLookupResult(
            lookup_id=str(row["lookup_id"]),
            vocab_item_id=str(row["vocab_item_id"]) if row["vocab_item_id"] is not None else None,
            deduped=True,
            created_at=_parse_iso(row["created_at"]),
            rendered=rendered,
        )
```

And add the `_render_lookup` helper function at the bottom of `book_repository.py` (a private mirror of `book.render_lookup` so the repository does not import the handler module — avoids a circular import):

```python
def _render_lookup(kind: str, content: str, explanation: dict[str, Any]) -> str:
    if kind == "word":
        translation = str(explanation.get("translation", "")).strip()
        gloss = explanation.get("gloss")
        gloss_str = str(gloss).strip() if gloss else None
        rendered = f"**{content}**"
        if gloss_str:
            rendered += f" — {gloss_str}"
        if translation:
            rendered += f" (translation: {translation})"
        return rendered
    if kind == "sentence":
        return f"> {content}\n\n{explanation.get('translation', '')}"
    if kind == "passage":
        body = explanation.get("translation") or explanation.get("explanation", "")
        return f"> {content}\n\n{body}"
    if kind == "question":
        return f"Q: {content}\nA: {explanation.get('answer', '')}"
    return ""
```

Add the missing imports at the top of `book_repository.py` if not already present: `from typing import Any` (for the `_render_lookup` signature). `json` is already imported.

Note: this duplicates the rendering template across `book.py` and `book_repository.py`. This is an intentional, narrow duplication to avoid a circular import (the repository layer must not depend on the handler layer). If the implementer prefers, the template may instead be extracted into a third module `book_rendering.py` imported by both — but KISS favors the small duplication for 4 trivial templates. Document the choice in the commit message.

- [ ] **Step 6: Run the handler tests to verify they pass**

Run: `python -m pytest tests/unit/test_book.py tests/unit/test_book_repository.py -v`
Expected: PASS — all handler + DAL tests green.

- [ ] **Step 7: Commit**

```bash
git add src/language_tutor/book.py src/language_tutor/vocab.py \
        src/language_tutor/dal/book_repository.py tests/unit/test_book.py
git commit -m "feat(book): add book.py handlers + find_or_create_vocab_card_for_book

Handlers: start_book/record_book/resume_book/log_book/list_book/close_book +
deterministic render_lookup per kind. Word lookups feed the SRS deck via the
new vocab.py helper (composes VocabularyCardDefinition -> item_from_definition
-> _import_vocabulary_item_inner under book.py's shared transaction); missing/
echo translations log with vocab_item_id NULL and skip SRS. Per-book word dedup
returns the existing row without re-feeding. closed sessions rejected with
book_session_closed."
```

---

## Task 6: CLI registration + integration + golden tests

**Files:**
- Modify: `src/language_tutor/cli.py` (import handlers; register `@main.group() def book()` + 6 subcommands).
- Create: `tests/integration/test_book_flow.py`
- Create: `tests/golden/test_book_rendering.py`
- Create: `tests/fixtures/book/builders.py`

- [ ] **Step 1: Write the failing integration test**

Create `tests/fixtures/book/builders.py`:

```python
from __future__ import annotations

from typing import Any


def book_record_payload(book_session_id: str, kind: str = "word", **overrides: Any) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "book_session_id": book_session_id,
        "kind": kind,
        "content": "esquivo",
        "context": None,
        "explanation": {"translation": "evasive", "gloss": "adjective"},
    }
    if kind == "sentence" or kind == "passage":
        payload["content"] = "Hola mundo."
        payload["explanation"] = {"translation": "Hello world."}
    elif kind == "question":
        payload["content"] = "Why?"
        payload["explanation"] = {"answer": "Because."}
    payload.update(overrides)
    return payload
```

Create `tests/integration/test_book_flow.py`:

```python
from __future__ import annotations

import json

from tests.conftest import invoke_json
from tests.fixtures.book.builders import book_record_payload

SETUP = (
    '{"profile":{"native_language":"en","target_language":"Spanish","level_target":"A2"}}'
)


def _setup(runner) -> None:  # type: ignore[no-untyped-def]
    invoke_json(runner, ["setup", "write", "--json", SETUP])


def _start_session(runner) -> str:  # type: ignore[no-untyped-def]
    boot = invoke_json(runner, ["session-start", "--json", '{"host":"claude"}'])
    return str(boot["session_id"])


def _start_book(runner, session_id: str, title: str = "Esquivo") -> str:  # type: ignore[no-untyped-def]
    result = invoke_json(
        runner,
        ["book", "start", "--json", json.dumps({"session_id": session_id, "title": title, "author": "Cela"})],
    )
    return str(result["book_session_id"])


def test_book_start_record_log_close_flow(runner) -> None:  # type: ignore[no-untyped-def]
    _setup(runner)
    session_id = _start_session(runner)
    book_id = _start_book(runner, session_id, title="Esquivo")
    result = invoke_json(runner, ["book", "record", "--json", json.dumps(book_record_payload(book_id))])
    assert result["deduped"] is False
    assert result["vocab_item_id"].startswith("vocab_")
    assert "esquivo" in result["rendered"]
    log = invoke_json(runner, ["book", "log", "--json", json.dumps({"book_session_id": book_id})])
    assert len(log["lookups"]) == 1
    assert log["rendered"].startswith("1. [word]")
    closed = invoke_json(runner, ["book", "close", "--json", json.dumps({"book_session_id": book_id})])
    assert closed["status"] == "closed"


def test_book_record_on_closed_returns_error_envelope(runner) -> None:  # type: ignore[no-untyped-def]
    _setup(runner)
    session_id = _start_session(runner)
    book_id = _start_book(runner, session_id)
    invoke_json(runner, ["book", "close", "--json", json.dumps({"book_session_id": book_id})])
    result = runner.invoke(
        __import__("language_tutor.cli").cli.main,
        ["book", "record", "--json", json.dumps(book_record_payload(book_id))],
    )
    assert result.exit_code == 1
    assert json.loads(result.output)["error"]["code"] == "book_session_closed"


def test_book_resume_finds_open_session(runner) -> None:  # type: ignore[no-untyped-def]
    _setup(runner)
    session_id = _start_session(runner)
    _start_book(runner, session_id, title="Esquivo")
    resumed = invoke_json(runner, ["book", "resume", "--json", json.dumps({"title": "Esquivo"})])
    assert resumed["title"] == "Esquivo"
    assert resumed["status"] == "open"


def test_book_list_returns_open_first(runner) -> None:  # type: ignore[no-untyped-def]
    _setup(runner)
    session_id = _start_session(runner)
    a = _start_book(runner, session_id, title="A")
    _start_book(runner, session_id, title="B")
    invoke_json(runner, ["book", "close", "--json", json.dumps({"book_session_id": a})])
    result = invoke_json(runner, ["book", "list", "--json", "{}"])
    assert [s["status"] for s in result["sessions"]] == ["open", "closed"]


def test_book_record_word_echo_translation_logs_without_card(runner) -> None:  # type: ignore[no-untyped-def]
    _setup(runner)
    session_id = _start_session(runner)
    book_id = _start_book(runner, session_id)
    result = invoke_json(
        runner,
        ["book", "record", "--json", json.dumps(book_record_payload(book_id, content="hello", explanation={"translation": "hello"}))],
    )
    assert result["vocab_item_id"] is None
    assert result["rendered"] == "**hello**"
```

- [ ] **Step 2: Write the failing golden test**

Create `tests/golden/test_book_rendering.py`:

```python
from __future__ import annotations

from language_tutor.book import render_lookup


def test_word_render_with_gloss_and_translation() -> None:
    assert render_lookup("word", "esquivo", {"translation": "evasive", "gloss": "adj"}) == "**esquivo** — adj (translation: evasive)"


def test_word_render_with_translation_only() -> None:
    assert render_lookup("word", "esquivo", {"translation": "evasive"}) == "**esquivo** (translation: evasive)"


def test_word_render_with_gloss_only() -> None:
    assert render_lookup("word", "esquivo", {"gloss": "adj"}) == "**esquivo** — adj"


def test_word_render_bare_when_no_translation_or_gloss() -> None:
    assert render_lookup("word", "esquivo", {"translation": ""}) == "**esquivo**"


def test_sentence_render() -> None:
    assert render_lookup("sentence", "Hola mundo.", {"translation": "Hello world."}) == "> Hola mundo.\n\nHello world."


def test_passage_render_falls_back_to_explanation() -> None:
    assert render_lookup("passage", "Long.", {"explanation": "Body."}) == "> Long.\n\nBody."


def test_question_render() -> None:
    assert render_lookup("question", "Why?", {"answer": "Because."}) == "Q: Why?\nA: Because."
```

- [ ] **Step 3: Run the tests to verify they fail**

Run: `python -m pytest tests/integration/test_book_flow.py tests/golden/test_book_rendering.py -v`
Expected: FAIL — `No such command 'book'` (the CLI group is not registered yet); golden test may pass already if `render_lookup` exists from Task 5 (verify it does — if golden passes, that is fine; the integration test is the gate).

- [ ] **Step 4: Register the `book` group in `cli.py`**

In `src/language_tutor/cli.py`:

1. Add the import near the other handler imports (after line 22 `from language_tutor.reading import record_reading, start_reading`):

```python
from language_tutor.book import close_book, list_book, log_book, record_book, resume_book, start_book
```

2. Add the `@main.group()` + 6 subcommands. Place this block immediately AFTER the `lesson` group (after line 888, before the `host` group at line 891). Use the inline try/except pattern (book has its own handler signatures, not the shared text-modality helpers):

```python
@main.group()
def book() -> None:
    """Book-reading companion: per-book lookup log + SRS vocab feeding."""


@book.command("start")
@click.option("--json-output", "--json", "json_output", is_flag=True)
@click.argument("payload", required=True)
def book_start(json_output: bool, payload: str) -> None:
    del json_output
    try:
        state = read_setup(resolve_paths())
        data = BookStartInput.model_validate(parse_payload(payload))
        repo, conn = open_repo()
        try:
            book_repo = BookRepository(conn)
            emit(start_book(book_repo, session_id=data.session_id, title=data.title, author=data.author, now=_utc_now()))
            conn.commit()
        finally:
            conn.close()
    except (TutorError, ValidationError, KeyError) as exc:
        if isinstance(exc, TutorError):
            fail_json(exc)
        if isinstance(exc, KeyError):
            fail_json(
                TutorError(
                    "session_not_found",
                    f"Session {data.session_id} does not exist.",
                    "Call session-start first and thread its session_id.",
                )
            )
        fail_json(
            TutorError(
                "invalid_book_start",
                "Book start payload failed validation.",
                "Pass BookStartInput JSON with session_id and a non-empty title.",
            )
        )


@book.command("record")
@click.option("--json-output", "--json", "json_output", is_flag=True)
@click.argument("payload", required=True)
def book_record(json_output: bool, payload: str) -> None:
    del json_output
    try:
        state = read_setup(resolve_paths())
        data = BookRecordInput.model_validate(parse_payload(payload))
        repo, conn = open_repo()
        try:
            book_repo = BookRepository(conn)
            emit(
                record_book(
                    book_repo=book_repo,
                    tutor_repo=repo,
                    book_session_id=data.book_session_id,
                    kind=data.kind,
                    content=data.content,
                    context=data.context,
                    explanation=data.explanation,
                    target_language=state.profile.target_language,
                    now=_utc_now(),
                )
            )
            conn.commit()
        finally:
            conn.close()
    except (TutorError, ValidationError, KeyError) as exc:
        if isinstance(exc, TutorError):
            fail_json(exc)
        if isinstance(exc, KeyError):
            fail_json(
                TutorError(
                    "book_session_not_found",
                    f"Book session {data.book_session_id} does not exist.",
                    "Call `tutor book start` or `tutor book resume` first.",
                )
            )
        fail_json(
            TutorError(
                "invalid_book_record",
                "Book record payload failed validation.",
                "Pass BookRecordInput JSON with a valid kind/content/explanation.",
            )
        )


@book.command("resume")
@click.option("--json-output", "--json", "json_output", is_flag=True)
@click.argument("payload", required=True)
def book_resume(json_output: bool, payload: str) -> None:
    del json_output
    try:
        data = BookResumeInput.model_validate(parse_payload(payload))
        repo, conn = open_repo()
        try:
            book_repo = BookRepository(conn)
            session = resume_book(book_repo, title=data.title)
            if session is None:
                raise TutorError(
                    "no_open_book_session",
                    f"No open reading session for '{data.title}'.",
                    "Start one with `tutor book start`.",
                )
            emit(session)
        finally:
            conn.close()
    except (TutorError, ValidationError) as exc:
        if isinstance(exc, TutorError):
            fail_json(exc)
        fail_json(
            TutorError(
                "invalid_book_resume",
                "Book resume payload failed validation.",
                "Pass BookResumeInput JSON with a title.",
            )
        )


@book.command("log")
@click.option("--json-output", "--json", "json_output", is_flag=True)
@click.argument("payload", required=True)
def book_log(json_output: bool, payload: str) -> None:
    del json_output
    try:
        data = BookLogInput.model_validate(parse_payload(payload))
        repo, conn = open_repo()
        try:
            book_repo = BookRepository(conn)
            emit(log_book(book_repo, book_session_id=data.book_session_id))
        finally:
            conn.close()
    except (TutorError, ValidationError) as exc:
        if isinstance(exc, TutorError):
            fail_json(exc)
        fail_json(
            TutorError(
                "invalid_book_log",
                "Book log payload failed validation.",
                "Pass BookLogInput JSON with a book_session_id.",
            )
        )


@book.command("list")
@click.option("--json-output", "--json", "json_output", is_flag=True)
@click.argument("payload", required=False)
def book_list(json_output: bool, payload: str | None) -> None:
    del json_output
    try:
        BookListInput.model_validate(parse_payload(payload))
        repo, conn = open_repo()
        try:
            book_repo = BookRepository(conn)
            emit(list_book(book_repo))
        finally:
            conn.close()
    except (TutorError, ValidationError) as exc:
        if isinstance(exc, TutorError):
            fail_json(exc)
        fail_json(
            TutorError(
                "invalid_book_list",
                "Book list payload failed validation.",
                "Pass an empty JSON object {}.",
            )
        )


@book.command("close")
@click.option("--json-output", "--json", "json_output", is_flag=True)
@click.argument("payload", required=True)
def book_close(json_output: bool, payload: str) -> None:
    del json_output
    try:
        data = BookCloseInput.model_validate(parse_payload(payload))
        repo, conn = open_repo()
        try:
            book_repo = BookRepository(conn)
            emit(close_book(book_repo, book_session_id=data.book_session_id, now=_utc_now()))
            conn.commit()
        finally:
            conn.close()
    except (TutorError, ValidationError, KeyError) as exc:
        if isinstance(exc, TutorError):
            fail_json(exc)
        if isinstance(exc, KeyError):
            fail_json(
                TutorError(
                    "book_session_not_found",
                    f"Book session {data.book_session_id} does not exist.",
                    "Call `tutor book list` to find a book_session_id.",
                )
            )
        fail_json(
            TutorError(
                "invalid_book_close",
                "Book close payload failed validation.",
                "Pass BookCloseInput JSON with a book_session_id.",
            )
        )
```

3. Add the schema imports near the existing `from language_tutor.schemas import (...)` block. Add `BookCloseInput`, `BookListInput`, `BookLogInput`, `BookRecordInput`, `BookResumeInput`, `BookStartInput` to that import. Also add `from language_tutor.dal.book_repository import BookRepository` near the existing `from language_tutor.dal.repositories import TutorRepository` import.

- [ ] **Step 5: Run the integration + golden tests to verify they pass**

Run: `python -m pytest tests/integration/test_book_flow.py tests/golden/test_book_rendering.py -v`
Expected: PASS — all 6 integration tests + 7 golden tests green.

- [ ] **Step 6: Run the unit handler tests to confirm no regression**

Run: `python -m pytest tests/unit/test_book.py tests/unit/test_book_repository.py -v`
Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add src/language_tutor/cli.py tests/integration/test_book_flow.py \
        tests/golden/test_book_rendering.py tests/fixtures/book/builders.py
git commit -m "feat(cli): register tutor book command group + integration/golden tests

Adds @main.group() book with start/record/resume/log/list/close subcommands
following the cli.py convention (handlers imported from book.py). Integration
test covers the full start->record->log->close flow, closed-session rejection,
resume, list ordering, and the echo-translation skip path. Golden test pins the
4 per-kind deterministic rendered templates."
```

---

## Task 7: `tutor-book` skill + payload registration (constitution VIII gate)

**Why a dedicated task:** Constitution Principle VIII (`docs/internal/constitution.md:133-148`) requires every `SKILL.md` creation to use a subagent per skill, explicitly read the local writing-skills helper, report changed files, and produce documented RED/GREEN/REFACTOR pressure evidence. The skill-payload contract test (`tests/installer/test_skill_payload_contract.py::test_canonical_skill_tree_contains_exact_files`) fails until `SKILL_FILES` exactly matches the on-disk `skills/` tree, so the skill file and the three registration lists must land together.

**Files:**
- Create: `skills/tutor-book/SKILL.md`
- Modify: `src/language_tutor/installer/providers/base.py:45-56` (`SKILL_FILES`).
- Modify: `src/language_tutor/package_assets.py:16-27` (`REQUIRED_SKILL_PAYLOAD_FILES`).
- Modify: `pyproject.toml` (`[tool.hatch.build.targets.wheel.force-include]`).
- Test: `tests/installer/test_skill_payload_contract.py` (existing — must stay green; no edit needed).

- [ ] **Step 1: Write the failing frontmatter + body contract check**

The existing `tests/installer/test_skill_payload_contract.py` already enforces:
- `test_canonical_skill_tree_contains_exact_files` — `SKILL_FILES` exactly equals the on-disk `skills/` tree.
- `test_skill_frontmatter_is_plain_name_description_only` — frontmatter keys == `{"name", "description"}`.
- `test_skill_markdown_uses_console_tutor_not_source_bin` — body must not contain `bin/tutor`.

Run: `python -m pytest tests/installer/test_skill_payload_contract.py -v`
Expected: FAIL at `test_canonical_skill_tree_contains_exact_files` — once `skills/tutor-book/SKILL.md` is created it will appear on disk but not in `SKILL_FILES`, so the lists must be updated in lockstep. (If the file does not exist yet, the test passes; the gate activates the moment the file is added.)

- [ ] **Step 2: Dispatch a subagent to author `skills/tutor-book/SKILL.md`**

Per constitution VIII, dispatch a subagent (via the Task tool) with this prompt — it MUST read the local writing-skills helper and report changed files:

> Author `skills/tutor-book/SKILL.md` for the lingo-loop project. Before writing, read the local writing-skills helper at `/Users/artem.veduta/.claude/plugins/cache/claude-plugins-official/superpowers/5.1.0/skills/writing-skills` (if present; otherwise the 6.0.3 path under `~/.cache/opencode/packages/superpowers.../skills/writing-skills`) and follow its guidance. Also read the peer skill `skills/tutor-reading/SKILL.md` verbatim — `tutor-book` is modeled on it and ships NO `scripts/run.py` shim (it invokes the `tutor` console binary directly).
>
> Frontmatter MUST be exactly two keys: `name: tutor-book` and `description:` (a single-line trigger description). No other keys (no `version`, no `allowed-tools`). The body MUST invoke the `tutor ... --json` console script and MUST NEVER contain the literal `bin/tutor`.
>
> The skill orchestrates: `tutor session-start` → `tutor book start` → `tutor checkpoint` (modality `book`, step_kind `prompt_shown`) → lookup loop (`tutor book record` with kind word/sentence/passage/question → `tutor checkpoint` modality `book` step_kind `answer_recorded` → display the `rendered` field) → `tutor book log` for review → `tutor book list` / `tutor book resume` to continue in a new conversation → `tutor book close` ONLY on explicit learner request (never automatic, mirroring the session-close guardrail).
>
> Payload schemas to reference (do not guess fields): `schemas/book_record.schema.json` (input), `schemas/book_session.schema.json` (start/resume/close output), `schemas/book_lookup_result.schema.json` (record output), `schemas/book_log.schema.json` (log output), `schemas/book_list.schema.json` (list output), `schemas/boot_result.schema.json` (session-start output), `schemas/checkpoint.schema.json` (checkpoint input — note the new `book` modality and `answer_recorded` step_kind).
>
> Discriminator vs `tutor-reading`: own-book text vs tutor-generated passage — on-the-spot meaning lookups of text in front of the learner stay in `tutor-book`; open-ended comprehension/analysis routes to `tutor-reading`. Do NOT embed pedagogy, persistence, rendering, or scoring — all live in validated Python contracts. Report the exact files you changed.

The subagent returns the SKILL.md content and the list of changed files. Verify the frontmatter is exactly `{name, description}` and the body has no `bin/tutor`.

- [ ] **Step 3: Register the skill in the three payload lists**

In `src/language_tutor/installer/providers/base.py`, add `"tutor-book/SKILL.md",` to the `SKILL_FILES` tuple (lines 45-56). Place it after the `tutor-reading/SKILL.md` / `tutor-lesson/SKILL.md` block (the no-shim skills):

```python
SKILL_FILES: tuple[str, ...] = (
    "tutor-setup/SKILL.md",
    "tutor-vocab/SKILL.md",
    "tutor-vocab/scripts/run.py",
    "tutor-writing/SKILL.md",
    "tutor-writing/scripts/run.py",
    "tutor-reading/SKILL.md",
    "tutor-lesson/SKILL.md",
    "tutor-progress/SKILL.md",
    "tutor-progress/scripts/run.py",
    "tutor-judge/SKILL.md",
    "tutor-book/SKILL.md",
)
```

In `src/language_tutor/package_assets.py`, add `"skills/tutor-book/SKILL.md",` to `REQUIRED_SKILL_PAYLOAD_FILES` (after the `tutor-judge/SKILL.md` line):

```python
    "skills/tutor-judge/SKILL.md",
    "skills/tutor-book/SKILL.md",
)
```

In `pyproject.toml`, under `[tool.hatch.build.targets.wheel.force-include]`, add one line (after the `tutor-judge/SKILL.md` line):

```toml
"skills/tutor-book/SKILL.md" = "language_tutor/_assets/skills/tutor-book/SKILL.md"
```

- [ ] **Step 4: Run the skill payload contract tests to verify they pass**

Run: `python -m pytest tests/installer/test_skill_payload_contract.py -v`
Expected: PASS — all 5 contract tests green (canonical tree matches, frontmatter is plain, body uses console `tutor`, helper scripts unchanged).

- [ ] **Step 5: Produce RED/GREEN/REFACTOR pressure evidence**

Per constitution VIII, document the pressure evidence in `specs/008-book-reading/skill-rewrite-evidence.md` (created in Task 8). At minimum:
- **RED baseline:** without `tutor-book/SKILL.md`, an agent prompted to "help me read my book" has no skill to route to — it would either refuse or misuse `tutor-reading` (which generates passages, not lookups). Document this baseline failure.
- **GREEN minimal change:** the new SKILL.md teaches the agent the `tutor book start` → `record` → `log` flow and the own-book vs tutor-passage discriminator. The 7 skill-pressure scenarios (Task 8) pass.
- **REFACTOR / loophole closure:** verify no `bin/tutor` reference, no pedagogy embedded, no auto-close, frontmatter exactly `{name, description}`.

This evidence is produced jointly with Task 8's pressure-scenario document; the subagent in Step 2 should be asked to draft it.

- [ ] **Step 6: Commit**

```bash
git add skills/tutor-book/SKILL.md src/language_tutor/installer/providers/base.py \
        src/language_tutor/package_assets.py pyproject.toml
git commit -m "feat(skill): add tutor-book skill + register in 3 payload lists

tutor-book is a book-reading companion (peer of tutor-reading), modeled on
tutor-reading (no scripts/run.py shim). Registered in installer SKILL_FILES,
REQUIRED_SKILL_PAYLOAD_FILES, and the pyproject wheel force-include. Contract
tests gate the exact on-disk tree, plain frontmatter, and console-tutor usage."
```

---

## Task 8: `specs/008-book-reading/` spec + contracts + pressure scenarios + inventory bump

**Files:**
- Create: `specs/008-book-reading/spec.md`
- Create: `specs/008-book-reading/contracts/book-cli.md`
- Create: `specs/008-book-reading/contracts/book-json.md`
- Create: `specs/008-book-reading/contracts/book_record.schema.json` (copy of generated)
- Create: `specs/008-book-reading/contracts/book_session.schema.json` (copy of generated)
- Create: `specs/008-book-reading/contracts/book_lookup_result.schema.json` (copy of generated)
- Create: `specs/008-book-reading/contracts/book_log.schema.json` (copy of generated)
- Create: `specs/008-book-reading/contracts/book_list.schema.json` (copy of generated)
- Create: `specs/008-book-reading/skill-pressure-scenarios.md`
- Create: `specs/008-book-reading/skill-rewrite-evidence.md`
- Create: `specs/008-book-reading/checklists/requirements.md`
- Modify: `specs/005-text-modalities/skill-inventory.md` (bump 7→8 + add tutor-book row).

- [ ] **Step 1: Create the spec spine**

Create `specs/008-book-reading/spec.md` — a concise feature spec summarizing the goal, non-goals, the 6 CLI commands, the data model, and success criteria. This is the spec equivalent of `specs/007-.../spec.md`; mirror its H2 structure. Reference (do not duplicate) the approved design at `docs/superpowers/specs/2026-06-22-tutor-book-reading-design.md`.

Create `specs/008-book-reading/checklists/requirements.md` — an acceptance checklist with one bullet per success criterion from the design doc (6 criteria) plus the contract-test gates.

- [ ] **Step 2: Create the CLI + JSON contracts**

Create `specs/008-book-reading/contracts/book-cli.md` mirroring `specs/007-.../contracts/session-start.cli.md` format: one `## Command` section per CLI command (`book start`, `book record`, `book resume`, `book log`, `book list`, `book close`) with Invocation, Input table, Output, Behavior, Errors subsections. Use the error codes from the design doc's Error handling section (`book_session_closed`, `no_open_book_session`, `session_not_open`, `invalid_book_*`).

Create `specs/008-book-reading/contracts/book-json.md` mirroring `specs/005-.../contracts/text-modality-json.md`: shared literals (`kind` enum, `status` enum), `BookRecordInput` fields, `BookSession` fields, `BookLookupResult` fields, `BookLog`/`BookList` shapes, and the per-kind `explanation` shape rules.

- [ ] **Step 3: Copy the 5 generated schemas into `contracts/`**

```bash
cp schemas/book_record.schema.json specs/008-book-reading/contracts/book_record.schema.json
cp schemas/book_session.schema.json specs/008-book-reading/contracts/book_session.schema.json
cp schemas/book_lookup_result.schema.json specs/008-book-reading/contracts/book_lookup_result.schema.json
cp schemas/book_log.schema.json specs/008-book-reading/contracts/book_log.schema.json
cp schemas/book_list.schema.json specs/008-book-reading/contracts/book_list.schema.json
```

These are frozen contract artifacts mirroring the generated canonical files in `schemas/` (matching how `specs/007-.../contracts/` carries copies of `session.schema.json` etc.).

- [ ] **Step 4: Create the skill-pressure scenarios**

Create `specs/008-book-reading/skill-pressure-scenarios.md` mirroring the `specs/007-.../skill-pressure-scenarios.md` format exactly: H1 `# Skill Pressure Scenarios (T0xx)`, a lead paragraph referencing the RED→GREEN cycle, then 7 numbered `## Scenario N — <desc> (FR-xxx)` sections each with block-quoted `> Setup:` / `> PASS condition:` / `> FAIL (RED) condition:` lines. The 7 scenarios (from the design doc):

1. Learner pastes a whole chapter as a "passage" — skill routes to a length-bounded explanation or asks the learner to pick a sentence.
2. Learner asks about the book's content — the discriminator is own-book text vs tutor-generated passage: on-the-spot meaning lookup stays in `tutor-book`; open-ended comprehension/analysis routes to `tutor-reading`.
3. Learner looks up the same word twice — dedup, no duplicate SRS card.
4. Learner says "I'm done, wrap up" — agent must NOT call `book close` automatically.
5. Learner pastes content in a language that doesn't match their setup profile — skill rejects and asks for content in the target language.
6. Learner looks up a word in a `closed` book session — `book record` returns `book_session_closed`; the agent must RECOVER (offer `book start` / `book resume`), not surface the raw error.
7. Learner has two open book sessions with the same title and says "resume my book" — the agent calls `book list` first and disambiguates by author/`started_at`, rather than letting `book resume` silently pick the most-recent by tiebreak.

Close with a `## Per-command summary` table listing each `tutor book` subcommand and when the skill calls it.

- [ ] **Step 5: Create the skill-rewrite-evidence document**

Create `specs/008-book-reading/skill-rewrite-evidence.md` with the RED/GREEN/REFACTOR evidence from Task 7 Step 5, the local helper path read, the assigned subagent scope, and the changed-files report. Mirror `specs/005-.../skill-rewrite-evidence.md` structure.

- [ ] **Step 6: Bump the skill inventory**

In `specs/005-text-modalities/skill-inventory.md`:

1. Line 8 — change `Counted: 7 tutor skills + 9 Speckit skills = 16.` to `Counted: 8 tutor skills + 9 Speckit skills = 17.` (Keep the stale 9-speckit count — the design doc flags the broader reconciliation as out-of-scope for this feature; do NOT reconcile to 22 here to avoid scope creep.)

2. Add a row to the "New Skills (added during this feature)" table (after the `tutor-judge` row):

```markdown
| `skills/tutor-book/SKILL.md` | tutor-book | Use when the learner has their OWN book or text in front of them and wants on-the-spot lookups of words, sentences, or passages they don't understand, or to ask about the text they are reading. Looked-up words are saved and added to vocabulary spaced-repetition review. tutor-reading is for comprehension Q&A on tutor-generated passages; tutor-vocab is for standalone vocab drills. | created + reviewed (compliant) | [../../docs/superpowers/specs/2026-06-22-tutor-book-reading-design.md](../../docs/superpowers/specs/2026-06-22-tutor-book-reading-design.md) |
```

3. In the Findings bullets, change "All 7 tutor skills are compliant" to "All 8 tutor skills are compliant".

- [ ] **Step 7: Run the skill-suite audit artifact test**

Run: `python -m pytest tests/unit/test_skill_suite_audit_artifacts.py -v`
Expected: PASS — if this test parses `skill-inventory.md` and asserts counts, verify it still passes with the bumped count (read the test first to understand its assertions; if it hardcodes "7" or "16", update the test to "8" / "17" in the same commit).

- [ ] **Step 8: Commit**

```bash
git add specs/008-book-reading/ specs/005-text-modalities/skill-inventory.md
git commit -m "docs(specs): add specs/008-book-reading + bump skill inventory to 8 tutor skills

Adds the 008 spec spine (spec.md, checklists/requirements.md), CLI + JSON
contracts with the 5 generated book_*.schema.json mirrors, 7 skill-pressure
scenarios in the 007 format, and the RED/GREEN/REFACTOR rewrite evidence
(constitution VIII gate). Bumps specs/005 skill-inventory.md tutor count 7->8
and adds the tutor-book row."
```

---

## Task 9: Full suite + lint + typecheck

**Files:** None (verification only; fix any drift in the files touched by Tasks 1-8).

- [ ] **Step 1: Run the full test suite**

```bash
python -m pytest -q
```

Expected: all tests pass. If any test fails, read the failure, fix the underlying code (not the test, unless the test was wrong per the spec), and re-run. Common drift sources:
- An existing test asserts `CheckpointModality` / `CheckpointStepKind` members exhaustively — add the new members.
- An existing test asserts the `schemas/` directory file list exhaustively — the 5 new files must be included.
- `tests/unit/test_skill_lifecycle_tokens.py` may enumerate modalities — verify it still passes with `BOOK` added.

- [ ] **Step 2: Run lint**

```bash
ruff check src/ tests/
```

Expected: no errors. Fix any unused imports or line-length issues introduced by the new code.

- [ ] **Step 3: Run typecheck**

```bash
pyright
```

Expected: no new errors. If `pyright` reports unknown config, check `pyrightconfig.json` and run `npx pyright` or the project's configured typecheck command (check `pyproject.toml` for a `[tool.pyright]` section or a `make`/`just` target). Fix any type errors in the new modules — common ones: `str(row["kind"])` needing a `Literal` cast, `dict[str, Any]` vs `dict[str, str]` mismatches in explanation handling.

- [ ] **Step 4: Run the schema regeneration sanity check**

```bash
python -c "from pathlib import Path; from language_tutor.schemas import export_json_schemas; export_json_schemas(Path('/tmp/schemas_check'))" && diff -r schemas /tmp/schemas_check
```

Expected: no diff (the committed `schemas/` directory matches a fresh regeneration). If a diff appears, the committed schemas drifted from the models — re-run the regeneration from Task 3 Step 6 and commit the result.

- [ ] **Step 5: Commit any fixes**

```bash
git add -A
git commit -m "chore: fix lint/typecheck drift from book feature"
```

(Only if Step 2/3/4 surfaced fixes; otherwise skip this step.)

---

## Self-review

**1. Spec coverage** — checked against `docs/superpowers/specs/2026-06-22-tutor-book-reading-design.md`:
- Migration 005 + checkpoints rebuild + enum updates → Task 2. ✓
- `REQUIRED_MIGRATION_FILES` registration → Task 2 Step 5. ✓
- Atomicity gate test → Task 2 Step 1 (`test_005_rebuild_is_atomic_on_mid_rebuild_failure`). ✓
- `BookRepository` (one class, both tables, belt-and-suspenders existence checks, resume tiebreak, list open-first) → Task 4. ✓
- `import_vocabulary_item` → `_import_vocabulary_item_inner` nestable refactor → Task 1. ✓
- `find_or_create_vocab_card_for_book` helper (composes `VocabularyCardDefinition` → `item_from_definition` → `_import_vocabulary_item_inner`, `source` singular, `tags=["from-book"]`, `lemma=word`) → Task 5 Step 3. ✓
- `target_language` resolved in `cli.py` from `state.profile.target_language`, passed through → Task 6 Step 4. ✓
- SRS feeding: usable non-echo translation only; missing/echo logs with `vocab_item_id` NULL → Task 5 Step 4. ✓
- Shared transaction for SRS-fed path; separate transaction for no-SRS path → Task 5 Step 4. ✓
- Per-book word dedup (`deduped` flag) independent from global SRS card dedup → Task 5 tests. ✓
- `book_session_closed` rejection → Task 4 + Task 5. ✓
- Rendering: per-kind templates + `rendered` field + log numbered list → Task 5 Step 4 + Task 6 golden. ✓
- 5 pydantic input models + 6 output models → Task 3. ✓
- 5 `book_*.schema.json` registered in `export_json_schemas` + regenerated → Task 3. ✓
- CLI group + 6 subcommands in `cli.py` (handlers in `book.py`, `@main.group()` not in `book.py`) → Task 6. ✓
- Skill `tutor-book` (no shim, console `tutor`, plain frontmatter) → Task 7. ✓
- Three payload lists updated (`SKILL_FILES`, `REQUIRED_SKILL_PAYLOAD_FILES`, pyproject force-include) → Task 7 Step 3. ✓
- Constitution VIII subagent + RED/GREEN/REFACTOR evidence → Task 7 Steps 2 & 5. ✓
- `specs/008-book-reading/` with contracts (MD + schema.json) + 7 pressure scenarios → Task 8. ✓
- `skill-inventory.md` bumped 7→8 + tutor-book row → Task 8 Step 6. ✓
- Existing migration tests' version lists fixed → Task 2 Step 6. ✓
- `tutor book list` command → Task 6. ✓
- No `run.py` shim → Task 7 (only `SKILL.md` registered). ✓

**2. Placeholder scan** — no TBD/TODO/"implement later" in any step; every code step shows the full code; every command step shows the expected output.

**3. Type consistency** — `BookRepository.start_book_session` / `record_lookup` / `_record_lookup_inner` / `close_book_session` / `get_open_book_session_by_title` / `get_book_session` / `list_book_sessions` / `get_lookups` / `_find_word_lookup` are the names used consistently across Tasks 4, 5, 6. `start_book` / `record_book` / `resume_book` / `log_book` / `list_book` / `close_book` handler names match across Tasks 5, 6. `render_lookup` matches across Tasks 5, 6. `BookRecordInput`/`BookStartInput`/`BookResumeInput`/`BookLogInput`/`BookCloseInput`/`BookListInput`/`BookSession`/`BookLookupResult`/`BookLogEntry`/`BookLog`/`BookListEntry`/`BookList` match across Tasks 3, 4, 5, 6. `find_or_create_vocab_card_for_book` matches across Tasks 1, 5. `_import_vocabulary_item_inner` matches across Tasks 1, 5. Error codes (`book_session_closed`, `book_session_already_closed`, `session_not_open`, `no_open_book_session`, `invalid_book_*`) match across Tasks 4, 5, 6.

---

## Execution Handoff

**Plan complete and saved to `docs/superpowers/plans/2026-06-22-tutor-book-reading.md`. Two execution options:**

**1. Subagent-Driven (recommended)** — I dispatch a fresh subagent per task, review between tasks, fast iteration. Matches the user's request to fan out parallel subagents. Tasks 2, 3, 7, 8 can run in parallel after Task 1; Tasks 4→5→6 are sequential; Task 9 is the final gate.

**2. Inline Execution** — Execute tasks in this session using executing-plans, batch execution with checkpoints for review.

**Which approach?**
