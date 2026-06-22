-- Rebuild checkpoints to accept 'book' modality and 'answer_recorded' step_kind.
-- SQLite cannot ALTER a CHECK constraint, so the table is rebuilt inside an
-- explicit BEGIN/COMMIT so any mid-migration failure rolls back atomically.
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

COMMIT;
