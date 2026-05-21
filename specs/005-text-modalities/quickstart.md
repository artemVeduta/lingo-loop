# Quickstart: Text Modalities + Skill Authoring

## 1. Verify setup

```bash
rtk bin/tutor doctor --json
rtk bin/tutor setup read --json
```

Expected: local setup is readable and no learner data path changes are required.

## 2. Inventory skills before new work

```bash
rtk rg --files skills .agents/skills
```

Expected: every `SKILL.md` is recorded once in `specs/005-text-modalities/skill-inventory.md` with trigger scope, convention status, and compliance decision.

## 3. Validate a reading exercise candidate

```bash
rtk bin/tutor reading start --json '{"mode":"comprehension","candidate":{"modality":"reading","target_language":"Ukrainian","level_target":"A2","focus":"case","instructions":"Read the passage and answer briefly.","content":"...","questions":["..."],"answer_key":["..."],"rubric":["..."],"tags":["case"]}}'
```

Expected: output is a validated exercise under 1200 rendered characters.

## 4. Record reading feedback

```bash
rtk bin/tutor reading record --json '{"exercise_id":"reading_demo","modality":"reading","learner_response":"...","response_status":"completed","candidate_feedback":{"verdict":"partial","corrected_answer":"","severity":"low","confidence":"medium","error_spans":[],"explanation":"...","next_drill_hint":"..."},"score_metadata":{"questions_total":2,"questions_correct":1},"exercise_summary":"Demo reading exercise."}'
```

Expected: output embeds `FeedbackEnvelope`, records one answer event, and persists only safe mistake spans.

## 5. Validate a guided lesson

```bash
rtk bin/tutor lesson start --json '{"candidate":{"modality":"lesson","target_language":"Ukrainian","level_target":"A2","focus":"verbs_of_motion","instructions":"Read and complete the practice step.","content":"...","questions":["..."],"answer_key":["..."],"rubric":["..."],"tags":["verbs_of_motion"]}}'
```

Expected: output is a focused micro-lesson with one bounded topic and a practice step.

## 6. Run transcript drill as reading submode

```bash
rtk bin/tutor reading start --json '{"mode":"transcript","candidate":{"modality":"transcript","mode":"transcript_reconstruction","target_language":"Ukrainian","level_target":"A2","focus":"word_order","instructions":"Reconstruct the text-only transcript.","content":"...","questions":["..."],"answer_key":["..."],"rubric":["..."],"tags":["word_order"]}}'
```

Expected: output clearly stays text-only and does not imply audio support.

## 7. Check progress visibility

```bash
rtk bin/tutor progress --json '{"window_size":10}'
```

Expected: completed reading, lesson, and transcript attempts contribute aggregate practice totals and safe mistake signals without raw learner responses or exercise bodies.

## 8. Run verification gates

```bash
rtk uv run pytest tests/unit/test_text_modalities.py tests/unit/test_reading.py tests/unit/test_lessons.py tests/unit/test_schemas.py tests/unit/test_repositories.py
rtk uv run pytest tests/golden/test_text_modality_rendering.py tests/adapter_contract/test_reading_cli.py tests/adapter_contract/test_lesson_cli.py
rtk uv run pytest tests/integration/test_text_modality_flow.py tests/integration/test_progress_flow.py
rtk uv run pytest tests/adapter_contract/test_evaluator_semantic_thresholds.py tests/semantic/test_text_modality_feedback.py
rtk uv run pyright
rtk uv run ruff check .
```

Expected: deterministic, contract, integration, semantic-eval, type, and lint gates pass before Phase 5 is marked complete.

## 9. Dogfood evidence (T076)

Recorded 2026-05-22 against a fresh local `LANGUAGE_TUTOR_HOME`, profile Ukrainian/A2:

| Modality | `start` result | `record` result |
|----------|----------------|-----------------|
| Reading | `exercise_id=reading_cfffa9e9aede`, rendered 151 chars (≤1200) | `skill=reading`, `persisted_mistakes=1` |
| Lesson | `exercise_id=lesson_2dec6b0460b3`, `modality=lesson` | `skill=lesson` |
| Transcript | `exercise_id=transcript_54de33d137b8`, `modality=transcript`, text-only | stored `skill=reading` (transcript submode) |

`bin/tutor progress --json` exposed aggregate guardrails (`aggregate_metrics_only`) with no
raw learner responses or exercise bodies. All three flows validated the candidate, embedded
an unchanged `FeedbackEnvelope`, and persisted through existing tables only — no new table
was created (verified by `tests/integration/test_local_data_ownership.py`).

> Note: the semantic-eval gate (5 live judge runs × 3 fixtures × 3 modalities, thresholds in
> `contracts/semantic-eval.md`) is a manual operational gate run with judge/API access. The
> repository CI validates the fixtures deterministically
> (`tests/semantic/test_text_modality_feedback.py`,
> `tests/adapter_contract/test_evaluator_semantic_thresholds.py`).
