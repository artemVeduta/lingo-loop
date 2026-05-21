# Contract: Progress JSON Report

## Top-Level Shape

```json
{
  "schema_version": 1,
  "generated_at": "2026-05-21T12:00:00Z",
  "report_window": {
    "requested_session_count": 10,
    "actual_session_count": 10,
    "mastery_session_count": 30,
    "start_date": "2026-05-12",
    "end_date": "2026-05-21",
    "active_mastery_window": "last_30_completed_sessions"
  },
  "snapshot": {
    "streak_days": 6,
    "due_count": 12,
    "maturity": {"learning": 8, "review": 35, "mature": 14},
    "top_weak_patterns": ["case", "aspect"],
    "month_to_date_estimated_usd": 1.24,
    "cost_status": "partial",
    "next_action": "Review due vocabulary."
  },
  "tag_mastery": [
    {
      "tag": "case",
      "score": 42,
      "band": "emerging",
      "evidence_count": 18,
      "last_seen_at": "2026-05-21T10:00:00Z",
      "last_seen_age_days": 0,
      "stale": false,
      "trend": "worsening",
      "next_practice_hint": "Practice short case drills.",
      "score_breakdown": {
        "correctness": 38,
        "severity": 40,
        "recency": 100,
        "confidence": 72
      }
    }
  ],
  "recent_recap": {
    "actual_session_count": 10,
    "date_range": {"start_date": "2026-05-12", "end_date": "2026-05-21"},
    "practice_totals": {"answers": 82, "vocabulary_reviews": 64, "writing_answers": 18},
    "due_review_completion": {"completed": 64, "current_due_count": 12},
    "mistake_severity_totals": {"low": 9, "medium": 6, "high": 2},
    "weak_tag_changes": {
      "new": ["case"],
      "repeated": ["aspect"],
      "resolved": ["word_order"]
    },
    "latest_session_summary": "Focused practice saved.",
    "trends": [
      {
        "metric": "review_accuracy",
        "label": "Review accuracy",
        "polarity": "higher_is_better",
        "direction": "improving",
        "sparkline": ".:-=+*#%@",
        "min_label": "min 40%",
        "max_label": "max 90%",
        "values_count": 9
      }
    ],
    "skipped_data": []
  },
  "due_review_summary": {
    "due_count": 12,
    "completed_in_window": 64,
    "low_quality_in_window": 7,
    "maturity": {"learning": 8, "review": 35, "mature": 14}
  },
  "skipped_data": [
    {
      "reason": "duplicate_session",
      "count": 1,
      "scope": "recap",
      "message": "1 duplicate session record skipped."
    }
  ],
  "scope_guardrails": [
    "text_markdown_only",
    "aggregate_metrics_only",
    "no_raw_answers",
    "no_host_metadata"
  ]
}
```

## Required Fields

The following top-level fields are required:

- `schema_version`
- `generated_at`
- `report_window`
- `snapshot`
- `tag_mastery`
- `recent_recap`
- `due_review_summary`
- `skipped_data`
- `scope_guardrails`

## Mastery Bands

- `emerging`: 0-49
- `developing`: 50-74
- `steady`: 75-89
- `strong`: 90-100

## Trend Directions

- `improving`
- `steady`
- `worsening`
- `insufficient_data`

## Sparkline Rules

- `sparkline` uses only `.:-=+*#%@`.
- Length equals `values_count`.
- One character represents one valid completed session in the selected recap window.
- `min_label` and `max_label` are required when `values_count` is greater than zero.

## Round-Trip Rules

- JSON export MUST validate back into `ProgressReport` with no required-field loss.
- Re-serializing a validated report with sorted keys MUST be stable for identical input.
- Markdown export tests compare facts from this JSON model, not independently recomputed values.

## Excluded Fields

The JSON report MUST NOT include these keys or equivalent raw data:

- `learner_answer`
- `span_text`
- `feedback_envelope_json`
- `payload_json`
- full `explanation` text from mistakes
- host-specific metadata
