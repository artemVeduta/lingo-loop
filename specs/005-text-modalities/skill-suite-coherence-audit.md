# Skill Suite Coherence Audit: Text Modalities + Skill Authoring

**Purpose**: Suite-level review of skill coherence. Two checkpoints:

1. **Pre-new-skill gate** (T026): existing suite is inventoried and any required rewrite has
   evidence before `tutor-reading` / `tutor-lesson` are accepted.
2. **Final audit** (T075): re-run after the new skills exist.

Source contract: [contracts/skill-suite-audit.md](contracts/skill-suite-audit.md).

## Pre-new-skill coherence decision (T026)

- `inventoried_count`: 13 (4 tutor + 9 Speckit), each `SKILL.md` listed exactly once.
- `unresolved_trigger_overlaps`: none. Tutor skills route to distinct intents
  (setup / vocab / writing / progress); Speckit skills are workflow-only and never
  overlap tutor scopes.
- `convention_drift`: none. All tutor skills use `bin/tutor ... --json` only and defer
  pedagogy to Python.
- `duplicated_pedagogy`: none. No skill embeds scoring/persistence/aggregation.
- `blockers`: none. The local writing-skills helper path is required and available for
  new-skill authoring; no required reference is recorded as unavailable.
- `allowed_next_steps`: create `tutor-reading` (T039) and `tutor-lesson` (T055) through
  the subagent + writing-skills-helper gate; add transcript as a `tutor-reading` submode
  (T069), not a third skill.
- `decision`: **pass** (pre-new-skill gate). New skills may be created.

## Final coherence audit (T075)

Re-run after `tutor-reading` and `tutor-lesson` were created and hardened.

- `inventoried_count`: 15 (4 existing tutor + 9 Speckit + 2 new tutor), each `SKILL.md`
  listed exactly once.
- `new_skill_count`: 2 (`tutor-reading`, `tutor-lesson`).
- `trigger_overlaps` (expected empty): none. The 6 tutor skills route to distinct intents
  (setup / vocab / writing / reading / lesson / progress). New descriptions carry explicit
  negative boundaries; pressure scenarios in `skill_pressure.json` cover the
  reading↔writing, lesson↔progress, and reading↔lesson edges.
- `convention_drift` (expected empty): none. Both new skills are thin, use
  `bin/tutor ... --json` only, and defer all pedagogy to Python.
- `duplicated_pedagogy` (expected empty): none. Validation, budgets, scoring, persistence,
  and progress live in Python contracts/tests, not in any skill.
- `description_budget_status`: ok. Each description is one concrete trigger-oriented
  sentence plus a short exclusion clause; combined suite descriptions remain concise.
- `transcript_is_reading_submode`: confirmed. Transcript is `tutor-reading`
  `mode=transcript`, stored as `skill=reading`; there is no standalone transcript skill.
- `decision`: **pass**.

## Design review (T079)

- **SOLID**:
  - *S*: `text_modalities.py` owns shared rules; `reading.py`/`lessons.py` own modality
    orchestration; CLI owns I/O; repositories own persistence. Each module has one reason
    to change.
  - *O*: new modalities added via the shared `validate_candidate`/`record_text_modality`
    helpers and `STORED_SKILL`/`DEFAULT_MODE` maps — no edits to existing vocab/writing
    paths.
  - *L*: `AnswerEvent.skill` expanded to a superset literal; existing `vocab`/`writing`
    payloads still validate and substitute (covered by schema + migration tests).
  - *I*: narrow repository helper `record_text_modality_answer` rather than a fat method;
    skills expose only the specific `bin/tutor` commands they need.
  - *D*: orchestration depends on Pydantic contracts and the repository helper, not on
    SQLite details.
- **DRY**: budgets, guardrails, modality/skill maps, safe-mistake filtering, and the record
  path are single-source in `text_modalities.py`; reading/lesson/transcript compose them.
- **KISS**: no new tables, no new dependencies, deterministic exercise IDs via a hash; the
  one-repair-then-refuse rule is a simple bound, not a retry engine.
- **YAGNI**: no audio/image/dashboard/host-adapter/scheduler scaffolding; transcript reuses
  reading rather than adding a third skill or storage owner.
- **SoC**: skill (orchestration) / CLI (validation+I/O) / core (rules) / DAL (persistence) /
  rendering remain separated; `FeedbackEnvelope` unchanged.
- **Composition over inheritance**: behavior assembled from small functions + maps; no new
  class hierarchies.
- **Demeter**: orchestration talks to its immediate collaborators (repo helper, validators,
  feedback sanitizer); no deep reach-through into DAL internals.
- **Local-first data ownership**: SQLite owns attempts/mistakes; transcript stores
  `skill=reading`; progress stays aggregate-only; no cloud/telemetry/new table (regression
  test enforced).
- **Scope guardrails**: text-only enforced by candidate scanning + golden tests; rendered
  budgets enforced (≤1200 exercise, ≤900 feedback); no host-specific behavior.
- **Verification**: `pytest` 151 passed (90% coverage), `pyright` 0 errors, `ruff` clean.

**Decision**: no constitution violations; no complexity exceptions required.
