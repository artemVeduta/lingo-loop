CREATE TABLE IF NOT EXISTS migration_records (
  version INTEGER PRIMARY KEY,
  name TEXT NOT NULL,
  checksum TEXT NOT NULL,
  applied_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS lifecycle_events (
  id TEXT PRIMARY KEY,
  session_id TEXT NOT NULL,
  event_type TEXT NOT NULL,
  payload_json TEXT NOT NULL,
  occurred_at TEXT NOT NULL,
  source TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS vocabulary_items (
  id TEXT PRIMARY KEY,
  target_language TEXT NOT NULL,
  prompt TEXT NOT NULL,
  lemma TEXT,
  accepted_answers_json TEXT NOT NULL,
  hint TEXT,
  tags_json TEXT NOT NULL,
  state TEXT NOT NULL,
  ease_factor REAL NOT NULL CHECK (ease_factor >= 1.3),
  repetition_count INTEGER NOT NULL CHECK (repetition_count >= 0),
  interval_days INTEGER NOT NULL CHECK (interval_days >= 0),
  due_at TEXT NOT NULL,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  dedupe_key TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS answer_events (
  id TEXT PRIMARY KEY,
  idempotency_key TEXT UNIQUE,
  session_id TEXT NOT NULL,
  skill TEXT NOT NULL,
  prompt_ref TEXT NOT NULL,
  learner_answer TEXT NOT NULL,
  outcome TEXT NOT NULL,
  feedback_envelope_json TEXT,
  recorded_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS vocabulary_reviews (
  id TEXT PRIMARY KEY,
  session_id TEXT NOT NULL,
  vocabulary_item_id TEXT NOT NULL REFERENCES vocabulary_items(id),
  answer_event_id TEXT NOT NULL UNIQUE REFERENCES answer_events(id),
  verdict TEXT NOT NULL,
  quality INTEGER NOT NULL CHECK (quality BETWEEN 0 AND 5),
  previous_state_json TEXT NOT NULL,
  next_state_json TEXT NOT NULL,
  reviewed_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS mistake_events (
  id TEXT PRIMARY KEY,
  session_id TEXT NOT NULL,
  answer_event_id TEXT REFERENCES answer_events(id),
  skill TEXT NOT NULL,
  span_start INTEGER,
  span_end INTEGER,
  span_text TEXT,
  severity TEXT NOT NULL,
  tag TEXT NOT NULL,
  explanation TEXT NOT NULL,
  confidence TEXT NOT NULL,
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS session_summaries (
  id TEXT PRIMARY KEY,
  session_id TEXT NOT NULL UNIQUE,
  summary_for_user TEXT NOT NULL,
  summary_for_next_boot TEXT NOT NULL,
  weak_tags_json TEXT NOT NULL,
  next_focus TEXT NOT NULL,
  cost_snapshot_json TEXT NOT NULL,
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS skill_metrics (
  id TEXT PRIMARY KEY,
  metric_date TEXT NOT NULL,
  metric_name TEXT NOT NULL,
  metric_value REAL NOT NULL,
  dimensions_json TEXT NOT NULL,
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS cost_events (
  id TEXT PRIMARY KEY,
  session_id TEXT NOT NULL,
  operation TEXT NOT NULL,
  model TEXT NOT NULL,
  input_tokens INTEGER NOT NULL CHECK (input_tokens >= 0),
  output_tokens INTEGER NOT NULL CHECK (output_tokens >= 0),
  cache_read_tokens INTEGER NOT NULL CHECK (cache_read_tokens >= 0),
  estimated_cost_usd REAL CHECK (estimated_cost_usd IS NULL OR estimated_cost_usd >= 0),
  pricing_source TEXT NOT NULL,
  source_event_id TEXT,
  created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_vocabulary_due ON vocabulary_items(due_at, state);
CREATE INDEX IF NOT EXISTS idx_answers_session ON answer_events(session_id, recorded_at);
CREATE INDEX IF NOT EXISTS idx_mistakes_tag ON mistake_events(tag, created_at);
CREATE INDEX IF NOT EXISTS idx_cost_month ON cost_events(created_at);
