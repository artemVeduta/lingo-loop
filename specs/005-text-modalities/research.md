# Research: Text Modalities + Skill Authoring

## Decision: Treat skill audit evidence as repository design artifacts

**Rationale**: Phase 5 must prove skill-suite coherence before adding skills, but this evidence is project governance, not learner data. Keeping `skill-inventory.md`, `skill-rewrite-evidence.md`, and `skill-suite-coherence-audit.md` under `specs/005-text-modalities/` preserves reviewability without adding runtime persistence.

**Alternatives considered**: SQLite tables for skill audits were rejected because they create a new persistence path unrelated to learner state. Untracked notes were rejected because they fail the required review evidence gate.

## Decision: Validate generated exercise candidates through CLI/core contracts

**Rationale**: Reading passages, micro-lessons, and transcript drills need generated text, but skills should stay thin and generated content is provisional. Host skills can ask the model for candidate JSON, then `bin/tutor` validates modality, level fit, answerability, rubric/key presence, scope guardrails, and rendered character budgets before presenting the exercise.

**Alternatives considered**: Python-only deterministic content generation was rejected because Phase 5 requires useful generated language material. Letting skills present raw generated prose was rejected because it bypasses contracts, output budgets, and retry/refusal behavior.

## Decision: Keep `FeedbackEnvelope` unchanged and embed it in result wrappers

**Rationale**: The existing feedback contract already feeds rendering, mistake persistence, and progress analysis. Modality-specific wrappers can add exercise metadata, score metadata, response summary, and guardrails while keeping all existing feedback consumers substitutable.

**Alternatives considered**: Adding fields to `FeedbackEnvelope` was rejected because the clarification explicitly keeps it unchanged. Separate feedback models per modality were rejected because they duplicate verdict, severity, confidence, error span, and next-drill semantics.

## Decision: Reuse existing SQLite answer and mistake tables

**Rationale**: `answer_events`, `mistake_events`, and `session_summaries` already represent completed attempts, feedback, taggable mistakes, and progress inputs. Expanding allowed skill values to `reading` and `lesson` lets text modalities contribute to existing progress without a new storage owner. Transcript drills use `reading` as the stored skill and `transcript` as modality metadata.

**Alternatives considered**: A persisted exercise table was rejected because Phase 5 does not require a new source of truth for generated exercise bodies or answer keys. Storing transcript as a third skill was rejected because the spec makes it a `tutor-reading` submode.

## Decision: Extend progress through existing safe signals

**Rationale**: Progress mastery already reads `mistake_events` across sessions. Reading, lesson, and transcript attempts can emit safe mistake events through the same table and extend practice totals in the report contract. This keeps progress local, aggregate-safe, and consistent with Phase 4.

**Alternatives considered**: A separate text-modality progress report was rejected because it fragments the learner view. Raw exercise replay in progress was rejected because reports must stay aggregate-only and avoid raw private learner data.

## Decision: Enforce one repair/regeneration attempt

**Rationale**: The spec sets a strict retry policy. One repair attempt catches common malformed or overlong generated exercise candidates while preventing unbounded loops in terminal workflows. A second failure returns a clear refusal and records no answer or mistake signal.

**Alternatives considered**: Unlimited repair loops were rejected as unreliable and slow. Immediate refusal on first invalid candidate was rejected because it fails the requested repair path.

## Decision: Use the local writing-skills helper for every skill creation/rewrite

**Rationale**: The constitution requires treating `SKILL.md` changes as tested contract changes. The helper path exists locally and includes skill-writing and subagent-testing references, so implementation can use it as the required local source while also recording external reference coverage.

**Alternatives considered**: Main-agent-only skill edits were rejected by constitution. Bulk skill rewrites without per-skill or per-family pressure evidence were rejected because they cannot prove trigger boundaries under realistic invocation pressure.

## Decision: No new runtime dependency

**Rationale**: Existing Pydantic, Click, SQLite, pytest, syrupy, and stdlib tools cover contracts, CLI, persistence, deterministic rendering, and validation. Text modality support is mostly model validation, orchestration, and persistence mapping.

**Alternatives considered**: Markdown/table/rendering libraries and content-generation packages were rejected as unnecessary. ORM or async storage was rejected by constitution and scope.
