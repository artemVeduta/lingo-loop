# Feature Specification: Text Modalities + Skill Authoring

**Feature Branch**: `005-text-modalities`

**Created**: 2026-05-21

**Status**: Draft

**Input**: User description: "fifth phase from docs/ROADMAP.md"

## Clarifications

### Session 2026-05-21

- Q: Which user-facing surface owns the transcript drill? → A: `tutor-reading` submode
- Q: How should Phase 5 represent modality-specific feedback and scoring metadata? → A: Existing `FeedbackEnvelope` unchanged, embedded in modality-specific result wrappers
- Q: What semantic-eval acceptance threshold should Phase 5 use for reading, lesson, and transcript feedback? → A: 5 live runs per fixture; schema-valid 5/5; expected verdict/rubric 4/5; required tags present; no unsafe definitive correction
- Q: What terminal-readable size budget should generated Phase 5 exercises obey? → A: Exercise output <= 1200 rendered chars; feedback output <= 900 rendered chars
- Q: When a generated reading, lesson, or transcript exercise fails validation, how many repair/regeneration attempts are allowed before refusing? → A: Retry/repair once, then refuse with clear learner-facing message

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Verify Skill Suite Coherence (Priority: P1)

Project maintainers inventory every project skill, confirm each skill has a clear trigger boundary, and rewrite any non-compliant skill before new learning skills are added.

**Why this priority**: Phase 5 changes the skill suite. Existing invocation surfaces must be trusted before adding new exercise types, otherwise new skills may overlap, duplicate pedagogy, or bypass validated tutor contracts.

**Independent Test**: Can be tested by scanning all project `SKILL.md` files, recording a compliance decision for each file, and confirming any rewrite has required review evidence before implementation continues.

**Acceptance Scenarios**:

1. **Given** project skills exist under `.agents/skills/` and `skills/`, **When** the phase inventory runs, **Then** every `SKILL.md` is listed exactly once with location, purpose, trigger description, and compliance status.
2. **Given** a skill has overlapping triggers, workflow-heavy frontmatter, duplicated pedagogy, or unclear progressive disclosure, **When** it is reviewed, **Then** it is marked for rewrite with the specific issue and required evidence.
3. **Given** a skill is rewritten, **When** the rewrite is accepted, **Then** the record includes helper use, external reference coverage, assigned subagent pressure evidence, and changed-file review.
4. **Given** all existing and Speckit skills are reviewed, **When** new skills are considered, **Then** maintainers can confirm there is no trigger overlap or convention drift across the full suite.

---

### User Story 2 - Practice Reading Comprehension (Priority: P2)

A learner requests a short generated passage at their level, answers comprehension questions, and receives actionable feedback that uses the same feedback shape as existing writing and vocabulary practice.

**Why this priority**: Reading comprehension is the first new text modality and adds high learner value without host-specific capabilities or audio.

**Independent Test**: Can be tested by starting a reading practice session, answering questions with correct and incorrect responses, and confirming the learner receives passage-level feedback, mistake events, and next-practice guidance without new storage ownership.

**Acceptance Scenarios**:

1. **Given** a learner has a configured target language and level, **When** they start reading practice, **Then** they receive a passage, comprehension questions, and clear answer instructions.
2. **Given** the learner submits answers, **When** feedback is returned, **Then** it identifies comprehension strengths, missed meaning, relevant language issues, and next steps using the existing feedback envelope.
3. **Given** the passage or questions are unsuitable for the learner level, **When** validation detects the mismatch, **Then** the learner receives a safe retry path instead of a misleading exercise.
4. **Given** the learner completes the exercise, **When** progress is analyzed, **Then** safe mistake events and session analysis reflect the reading practice.

---

### User Story 3 - Complete Guided Micro-Lessons (Priority: P2)

A learner requests a focused micro-lesson for a weak tag, common error, or chosen topic, completes a short explanation and practice step, and receives feedback that feeds existing progress and targeting.

**Why this priority**: Micro-lessons turn detected weaknesses into structured practice while keeping the tutor text-only and local-first.

**Independent Test**: Can be tested by selecting a weak pattern, completing a micro-lesson, and confirming the lesson remains focused, produces feedback, and records safe learning signals.

**Acceptance Scenarios**:

1. **Given** the learner has weak-tag history, **When** they request a lesson without a topic, **Then** the lesson focuses on a relevant weakness and explains why it was selected.
2. **Given** the learner chooses a topic, **When** they request a lesson, **Then** the lesson stays within that topic and does not add unrelated curriculum.
3. **Given** the lesson includes practice, **When** the learner responds, **Then** feedback distinguishes concept understanding, usage errors, and next action.
4. **Given** a lesson is completed, **When** progress is reviewed later, **Then** safe lesson outcomes contribute to existing mistake and session signals.

---

### User Story 4 - Run Text-Based Transcript Drills (Priority: P3)

A learner practices listening-adjacent comprehension through transcript-based drills that use text only, such as reconstructing, correcting, or answering questions about an utterance-like transcript.

**Why this priority**: The roadmap calls for a dictation/transcript drill before audio is available. This delivers part of the learning value while preserving the Phase 5 text-only boundary.

**Independent Test**: Can be tested by running a transcript drill, submitting a reconstruction or correction, and confirming feedback captures comprehension and language mistakes without audio input or output.

**Acceptance Scenarios**:

1. **Given** the learner starts a transcript drill, **When** the exercise is generated, **Then** it presents text-only transcript material and a clear reconstruction, correction, or comprehension task.
2. **Given** the learner submits a response, **When** feedback is generated, **Then** it compares the response with the intended meaning and records safe mistake signals.
3. **Given** the learner expects audio playback, **When** they run Phase 5 transcript practice, **Then** the experience clearly remains text-only and does not imply audio support.

### Edge Cases

- No project `SKILL.md` files exist in one of the expected roots.
- A project skill has valid frontmatter but a trigger description that overlaps with another skill.
- A Speckit skill is used during Phase 5 and needs review even though it is not a tutor exercise skill.
- A required skill-authoring reference or local helper path is unavailable.
- A subagent pressure test reports changed files that the main agent has not reviewed.
- A learner has no weak-tag history when requesting a lesson.
- A generated passage, lesson, or transcript drill is above or below the learner's configured level.
- A generated exercise has no valid answer key, rubric, or learner-safe feedback path.
- A learner abandons a reading, lesson, or transcript drill before completion.
- A learner submits an empty, off-topic, or mixed-language answer.
- Existing mistake-event or feedback contracts cannot represent a new exercise result without expansion.
- A new skill would duplicate behavior already covered by `tutor-vocab`, `tutor-writing`, `tutor-progress`, or `tutor-setup`.
- Text output is too long for a practical terminal session.
- Audio, image, dashboard, host-adapter, or new persistence requests appear during Phase 5.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST inventory every project `SKILL.md` under `.agents/skills/` and `skills/`, including Speckit skills active during Phase 5.
- **FR-002**: System MUST record, for each inventoried skill, its path, purpose, trigger description, progressive-disclosure structure, CLI or contract conventions, and compliance decision.
- **FR-003**: System MUST identify and resolve skill trigger overlap, duplicated pedagogy, missing progressive disclosure, non-compliant frontmatter, and convention drift before new skills are accepted.
- **FR-004**: System MUST require any project skill creation or rewrite to use the local writing-skills helper, required external skill-authoring references, assigned subagent pressure evidence, and main-agent changed-file review.
- **FR-005**: System MUST document RED/GREEN/REFACTOR pressure evidence for each created or rewritten skill: baseline behavior, minimal change, verification after change, and loophole closures.
- **FR-006**: System MUST confirm the full skill suite remains coherent after adding new skills, including existing tutor skills and Speckit skills.
- **FR-007**: System MUST add a learner-facing reading comprehension skill that can generate a target-language passage and comprehension questions matching the learner profile language, configured level band, and requested focus.
- **FR-008**: System MUST allow learners to submit reading comprehension answers and receive feedback through the existing feedback envelope shape.
- **FR-009**: System MUST add a learner-facing guided micro-lesson skill for weak tags, common errors, or learner-selected topics.
- **FR-010**: System MUST keep micro-lessons focused on one bounded topic and include at least one practice step with feedback.
- **FR-011**: System MUST provide transcript drills as a `tutor-reading` text-only submode for listening-adjacent practice without audio input, audio output, image input, or image output.
- **FR-012**: System MUST keep `FeedbackEnvelope` unchanged and route reading, lesson, and transcript exercise feedback through modality-specific result wrappers that embed the existing envelope unless an explicit contract expansion is specified and tested.
- **FR-013**: System MUST emit safe mistake events for completed reading, lesson, and transcript exercises when learner responses contain taggable mistakes.
- **FR-014**: System MUST make completed text-modality sessions visible to existing progress and session analysis surfaces through existing learning signals.
- **FR-015**: System MUST ensure new exercise output is learner-safe, level-appropriate, terminal-readable, and actionable, with generated exercise output no more than 1200 rendered characters and feedback output no more than 900 rendered characters; validation must reject outputs without clear learner instructions, answerability/rubric evidence, or configured-level fit.
- **FR-016**: System MUST handle invalid generated exercises by retrying or repairing once, then refusing the exercise with a clear learner-facing message if validation still fails.
- **FR-017**: System MUST handle empty, abandoned, off-topic, or mixed-language responses without corrupting progress signals.
- **FR-018**: System MUST keep Phase 5 host-independent and usable on any text-capable host.
- **FR-019**: System MUST introduce no new persistence path; existing local learner state remains the source of truth for sessions, feedback, mistake events, and progress inputs.
- **FR-020**: System MUST keep new skills consistent with existing tutor CLI and contract conventions.
- **FR-021**: System MUST NOT add audio playback, speech recognition, image modalities, graphical dashboards, web views, new hosts, host-capability abstraction, cloud sync, multi-user behavior, gamification, bundled curriculum, FSRS, or a new scheduling algorithm.

### Key Entities *(include if feature involves data)*

- **Skill Inventory Record**: A review entry for one project skill, including path, trigger scope, compliance status, issues, and required evidence.
- **Skill Rewrite Evidence**: The proof package for a created or rewritten skill, including helper use, external references, subagent pressure results, and changed-file review.
- **Reading Exercise**: A generated passage, comprehension prompts, expected-answer guidance, learner responses, and feedback summary.
- **Micro-Lesson**: A bounded teaching unit for one weak tag, common error, or selected topic, including explanation, practice prompt, learner response, and feedback.
- **Transcript Drill**: A text-only listening proxy that asks the learner to reconstruct, correct, or understand transcript-like material.
- **Text Modality Result**: A modality-specific result wrapper for reading, lesson, or transcript attempts that contains exercise metadata, answer key or rubric reference, learner response summary, scoring metadata, and an embedded `FeedbackEnvelope`.
- **Text Modality Session**: A completed reading, lesson, or transcript practice attempt that contributes learner-safe feedback and mistake signals to existing progress.
- **Skill Suite Coherence Audit**: The final review that confirms trigger boundaries, frontmatter, progressive disclosure, CLI conventions, and pedagogy ownership across all project skills.

## Constitution Alignment *(mandatory)*

- **Affected Layers**: Skills, CLI command surfaces, core exercise orchestration, evaluator or judge contracts, feedback rendering, session analysis, progress signal ingestion, local repositories only where existing stored signals need contract-compatible extension, and tests. Host adapters remain out of scope.
- **Data Ownership**: Existing local SQLite state owns sessions, mistake events, feedback-derived signals, and progress inputs. YAML remains limited to human-editable learner profile and preferences. No cloud, telemetry, remote storage, host-owned learner data, or new persistence path is allowed.
- **Contract Surfaces**: Reading exercise, micro-lesson, transcript drill, text modality result wrappers, unchanged feedback envelope usage, judge request/result shape, mistake event shape, CLI JSON for new commands, JSON schema mirrors, and skill frontmatter/description contracts. Any contract expansion must be explicit and substitutable.
- **Required Validation**: Skill inventory and coherence audit evidence; subagent RED/GREEN/REFACTOR pressure tests for each created or rewritten skill; unit tests for exercise validation and safe signal mapping; contract tests for judge, feedback, mistake-event, and CLI JSON surfaces; golden tests for deterministic terminal rendering; integration tests for completed and abandoned exercise flows; semantic-eval suites for reading, lesson, and transcript feedback quality. Each semantic-eval fixture MUST run 5 live evaluations; output MUST be schema-valid in 5/5 runs, match expected verdict or rubric outcome in at least 4/5 runs, preserve required tags across the run set, and produce no unsafe definitive correction.
- **Skill Creation**: New `tutor-reading` and `tutor-lesson` skills are in scope. Existing `tutor-setup`, `tutor-vocab`, `tutor-writing`, `tutor-progress`, and active Speckit skills must be inventoried and rewritten only where needed. All skill creation or rewrite work must use the local writing-skills helper at `/Users/artem.veduta/.claude/plugins/cache/claude-plugins-official/superpowers/5.1.0/skills/writing-skills`, required external skill-authoring references, assigned subagent pressure evidence, and main-agent changed-file review.
- **Scope Guardrails**: Phase 5 is limited to text-only reading, micro-lesson, transcript-drill practice, and skill-suite authoring quality. It excludes audio modalities, image modalities, host adapters, host-capability abstraction, dashboards, GUI/web surfaces, new persistence paths, new scheduling algorithms, bundled curriculum, gamification, cloud sync, multi-user behavior, and unrelated progress redesign.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of project `SKILL.md` files under `.agents/skills/` and `skills/` are inventoried with path, trigger scope, compliance status, and review decision before new skills are accepted.
- **SC-002**: 100% of created or rewritten skills include documented helper use, external reference coverage, assigned subagent pressure evidence, and main-agent changed-file review.
- **SC-003**: Skill-suite coherence audit finds zero unresolved trigger overlaps or duplicated pedagogy among existing tutor skills, active Speckit skills, `tutor-reading`, and `tutor-lesson`.
- **SC-004**: A learner can complete a reading comprehension exercise from start to feedback in one session in 100% of primary-flow acceptance tests.
- **SC-005**: A learner can complete a guided micro-lesson from topic selection to feedback in one session in 100% of primary-flow acceptance tests.
- **SC-006**: A learner can complete a text-only transcript drill from prompt to feedback in one session in 100% of primary-flow acceptance tests.
- **SC-007**: Completed reading, lesson, and transcript exercises emit feedback and safe mistake signals through existing learning surfaces in 100% of contract fixtures where taggable mistakes are present.
- **SC-008**: Invalid generated exercises are retried or repaired once before refusal, and invalid generated exercises, empty responses, abandoned sessions, and off-topic submissions are handled without corrupting progress signals in 100% of edge-case tests.
- **SC-009**: New exercise output contains no audio, image, graphical dashboard, web view, raw private learner data, or host-specific behavior in 100% of scope-guardrail checks.
- **SC-010**: Semantic-eval suites for reading, lesson, and transcript feedback meet the phase acceptance threshold on at least 3 representative fixtures per modality: 5 live runs per fixture, schema-valid 5/5, expected verdict or rubric outcome in at least 4/5, required tags present across the run set, and zero unsafe definitive corrections.
- **SC-011**: Generated reading, lesson, and transcript exercise output stays within 1200 rendered characters and generated feedback output stays within 900 rendered characters in 100% of terminal-rendering fixtures.
- **SC-012**: A dogfood session demonstrates both new skills live and usable, plus transcript-drill practice, before Phase 5 is marked complete.

## Assumptions

- Phase 4 is complete, including progress reports, safe mistake aggregation, and existing feedback/progress contracts.
- Phase 5 adds exactly two new learner-facing skills: `tutor-reading` and `tutor-lesson`.
- The transcript drill is a text-only `tutor-reading` submode, not a third standalone skill.
- Reading, lesson, and transcript practice reuse existing learner profile, weak-tag, feedback, mistake-event, and session-analysis concepts through modality-specific result wrappers, with explicit contract extensions only where necessary.
- Existing tutor skills remain valid unless the inventory finds trigger overlap, frontmatter issues, duplicated pedagogy, or convention drift.
- External skill-authoring references are available during implementation, and unavailable references block skill rewrites until the dependency is resolved or explicitly documented.
- Any generated teaching content is treated as provisional until validated against level, focus, answerability, and learner-safety criteria.
