# Data Model: Text Modalities + Skill Authoring

## SkillInventoryRecord

Repository evidence record for one `SKILL.md`.

**Fields**:

- `path`: project-relative path to the skill file.
- `root`: `.agents/skills` or `skills`.
- `name`: frontmatter `name`.
- `description`: frontmatter `description`.
- `purpose`: concise purpose inferred from the skill body.
- `trigger_scope`: concrete user intents that should invoke the skill.
- `progressive_disclosure_status`: `pass`, `warn`, or `fail`.
- `cli_contract_status`: `pass`, `warn`, `fail`, or `not_applicable`.
- `pedagogy_ownership_status`: confirms pedagogy stays in Python contracts/tests.
- `issues`: list of concrete issues.
- `decision`: `compliant`, `rewrite_required`, `blocked`, or `not_in_scope`.
- `evidence_required`: list of required proof before acceptance.

**Validation rules**:

- Every `SKILL.md` under `skills/` and `.agents/skills/` appears exactly once.
- Frontmatter names use lowercase letters, numbers, and hyphens.
- Descriptions are third-person, concrete, trigger-oriented, and not workflow summaries.

## SkillRewriteEvidence

Proof package for a created or rewritten skill.

**Fields**:

- `skill_path`: project-relative `SKILL.md`.
- `helper_path`: must be `/Users/artem.veduta/.claude/plugins/cache/claude-plugins-official/superpowers/5.1.0/skills/writing-skills`.
- `external_references`: named skill-authoring references consulted.
- `subagent_scope`: skill or coherent skill family assigned.
- `baseline_pressure`: RED evidence before the change.
- `minimal_change`: GREEN change summary.
- `refactor_pressure`: loopholes closed after verification.
- `changed_files_reported`: files reported by the subagent.
- `main_agent_review`: review result for every changed file.

**Validation rules**:

- Required for every new or rewritten project `SKILL.md`.
- Missing helper, missing references, missing subagent report, or unreviewed changed files blocks acceptance.

## SkillSuiteCoherenceAudit

Final suite-level review after existing and new skills are considered.

**Fields**:

- `inventoried_count`: number of existing skills inventoried.
- `new_skill_count`: number of accepted new skills.
- `trigger_overlaps`: unresolved overlaps, expected empty.
- `convention_drift`: unresolved convention issues, expected empty.
- `duplicated_pedagogy`: duplicated skill-owned pedagogy, expected empty.
- `description_budget_status`: confirms combined descriptions remain concise.
- `decision`: `pass` or `fail`.

## TextExerciseCandidate

Common input envelope for generated reading, lesson, and transcript candidates.

**Fields**:

- `modality`: `reading`, `lesson`, or `transcript`.
- `mode`: `comprehension`, `lesson`, `transcript_reconstruction`, `transcript_correction`, or `transcript_comprehension`.
- `target_language`: learner target language.
- `level_target`: learner level.
- `focus`: weak tag, common error, learner topic, or requested focus.
- `instructions`: learner-facing instructions.
- `content`: passage, lesson explanation, or transcript-like material.
- `questions`: comprehension or practice prompts.
- `answer_key`: expected answers or key points.
- `rubric`: learner-safe scoring criteria.
- `tags`: normalized expected tags.
- `rendered_char_count`: computed by validation, not trusted from candidate input.

**Validation rules**:

- Rendered exercise output is at most 1200 characters.
- Candidate includes either an answer key or rubric sufficient for feedback.
- Candidate matches profile target language and level.
- Candidate contains no audio, image, dashboard, host-specific, cloud, or scheduling behavior.

## ReadingExercise

Validated reading comprehension exercise.

**Relationships**:

- Derived from `TextExerciseCandidate` with `modality=reading` and `mode=comprehension`.
- Produces `TextModalityResult` with `modality=reading`.

## MicroLesson

Validated guided micro-lesson.

**Relationships**:

- Derived from `TextExerciseCandidate` with `modality=lesson`.
- Focuses on one weak tag, common error, or learner-selected topic.
- Produces `TextModalityResult` with `modality=lesson`.

## TranscriptDrill

Text-only listening proxy.

**Relationships**:

- Derived from `TextExerciseCandidate` with `modality=transcript`.
- Owned by `tutor-reading`; stored answer events use skill `reading`.
- Produces `TextModalityResult` with `modality=transcript`.

## TextModalityRecordInput

CLI input for completed or attempted text-modality responses.

**Fields**:

- `exercise_id`: deterministic ID or candidate-provided ID after validation.
- `modality`: `reading`, `lesson`, or `transcript`.
- `session_id`: existing session ID, default `default`.
- `idempotency_key`: optional key for duplicate-safe recording.
- `learner_response`: learner response text.
- `response_status`: `completed`, `empty`, `abandoned`, `off_topic`, or `mixed_language`.
- `candidate_feedback`: existing `FeedbackEnvelope`.
- `score_metadata`: modality-specific score facts.
- `exercise_summary`: learner-safe summary or prompt reference.

**Validation rules**:

- Feedback rendering is at most 900 characters.
- Empty or abandoned responses do not emit mistake events.
- Off-topic or mixed-language responses emit mistake events only when feedback spans are safe and validated.

## TextModalityResult

Canonical result wrapper emitted by reading, lesson, and transcript record commands.

**Fields**:

- `schema_version`: `1`.
- `modality`: `reading`, `lesson`, or `transcript`.
- `exercise_id`: prompt reference used by `answer_events`.
- `session_id`: local session ID.
- `feedback`: embedded `FeedbackEnvelope`.
- `score_metadata`: modality-specific scoring metadata.
- `answer_event`: existing `AnswerEvent` or null for refusal/abandonment without recording.
- `persisted_mistakes`: count of safe mistake events inserted.
- `response_status`: `completed`, `empty`, `abandoned`, `off_topic`, `mixed_language`, or `refused`.
- `scope_guardrails`: text-only, no raw private export, no host-specific behavior.

## AnswerEvent Extension

Existing runtime event for learner answers.

**Change**:

- `skill` allowed values expand from `vocab|writing` to `vocab|writing|reading|lesson`.
- Transcript drills store `skill=reading` and `TextModalityResult.modality=transcript`.

**Validation rules**:

- Existing vocab and writing payloads remain valid.
- Progress and session analysis must treat new skill values as local text practice, not as new storage ownership.

## Progress Practice Totals Extension

Existing aggregate progress model.

**Change**:

- Practice totals add reading, lesson, and transcript attempt counts if implementation needs user-visible totals.
- Existing `answers`, `vocabulary_reviews`, and `writing_answers` remain stable.

**Validation rules**:

- Progress reports remain aggregate-only.
- No raw learner responses, exercise bodies, full feedback prose, answer keys, or host metadata appear in progress output.
