# Skill Inventory: Text Modalities + Skill Authoring

**Purpose**: Inventory every `SKILL.md` under `skills/` and `.agents/skills/` exactly
once before any new skill is accepted. Source contract:
[contracts/skill-suite-audit.md](contracts/skill-suite-audit.md).

**Inventory rule**: Every `**/SKILL.md` under the two source roots appears exactly once.
Counted: 4 tutor skills + 9 Speckit skills = 13.

## Tutor Skills (`skills/`)

| Path | Name | Description | Purpose | Trigger scope | Progressive disclosure | CLI/contract | Pedagogy ownership | Decision | Evidence/blocker |
|------|------|-------------|---------|---------------|------------------------|--------------|--------------------|----------|------------------|
| `skills/tutor-setup/SKILL.md` | tutor-setup | Onboard or edit local language tutor profile and preferences. | Drive `bin/tutor setup`/`boot-context` for onboarding and profile/preference edits. | Setup, onboarding, profile/preference edits. | pass | pass (`bin/tutor ... --json`) | pass (no pedagogy in skill) | compliant | none |
| `skills/tutor-vocab/SKILL.md` | tutor-vocab | Practice due vocabulary through the local tutor CLI. | Drive `bin/tutor vocab` start/add/import/answer/history. | Vocabulary review, card add, seed import, tag drill, cloze, history, answer correction. | pass | pass | pass (explicitly defers SM-2/persistence to CLI) | compliant | none |
| `skills/tutor-writing/SKILL.md` | tutor-writing | Free writing prompt and structured feedback orchestration. | Drive `bin/tutor writing prompt`/`record` plus judge handoff and render. | Free writing or structured correction. | pass | pass | pass (judge owns feedback; CLI persists) | compliant | none |
| `skills/tutor-progress/SKILL.md` | tutor-progress | Use when learner wants progress, exportable progress reports, next focus, due counts, weak patterns, maturity, local status, or cost status. | Drive `bin/tutor progress`/`render`/`session-end`/`doctor`; never recompute. | Progress, next focus, due counts, weak patterns, maturity, cost/local status, exports. | pass | pass | pass (CLI owns scoring/aggregation/rendering) | compliant | none |

## Speckit Skills (`.agents/skills/`)

Vendored from `github-spec-kit` (`source: templates/commands/*.md`). These are
spec-workflow skills, not tutor pedagogy. They do not touch `bin/tutor`, carry no
language-teaching pedagogy, and do not overlap tutor trigger scopes. Treated as
`not_in_scope` for rewrite; inventoried for coverage and overlap analysis only.

| Path | Name | Description (frontmatter) | Trigger scope | Pedagogy ownership | Decision |
|------|------|---------------------------|---------------|--------------------|----------|
| `.agents/skills/speckit-analyze/SKILL.md` | speckit-analyze | Cross-artifact consistency/quality analysis across spec/plan/tasks. | Post-tasks analysis. | not_applicable | not_in_scope (vendored) |
| `.agents/skills/speckit-checklist/SKILL.md` | speckit-checklist | Generate a custom feature checklist. | Checklist generation. | not_applicable | not_in_scope (vendored) |
| `.agents/skills/speckit-clarify/SKILL.md` | speckit-clarify | Identify underspecified spec areas via targeted questions. | Spec clarification. | not_applicable | not_in_scope (vendored) |
| `.agents/skills/speckit-constitution/SKILL.md` | speckit-constitution | Create/update project constitution; keep templates in sync. | Constitution authoring. | not_applicable | not_in_scope (vendored) |
| `.agents/skills/speckit-implement/SKILL.md` | speckit-implement | Execute the implementation plan from tasks.md. | Implementation execution. | not_applicable | not_in_scope (vendored) |
| `.agents/skills/speckit-plan/SKILL.md` | speckit-plan | Execute the planning workflow to generate design artifacts. | Implementation planning. | not_applicable | not_in_scope (vendored) |
| `.agents/skills/speckit-specify/SKILL.md` | speckit-specify | Create/update the feature spec from a description. | Specification authoring. | not_applicable | not_in_scope (vendored) |
| `.agents/skills/speckit-tasks/SKILL.md` | speckit-tasks | Generate a dependency-ordered tasks.md. | Task generation. | not_applicable | not_in_scope (vendored) |
| `.agents/skills/speckit-taskstoissues/SKILL.md` | speckit-taskstoissues | Convert tasks into dependency-ordered GitHub issues. | Tasks→issues conversion. | not_applicable | not_in_scope (vendored) |

## New Skills (added during this feature)

| Path | Name | Description | Decision | Evidence |
|------|------|-------------|----------|----------|
| `skills/tutor-reading/SKILL.md` | tutor-reading | Use when the learner wants to read a passage and answer comprehension questions, or reconstruct a text transcript drill (text-only, no audio). Not for free writing, vocabulary review, or guided lessons. | created + reviewed (compliant) | [skill-rewrite-evidence.md](skill-rewrite-evidence.md) |
| `skills/tutor-lesson/SKILL.md` | tutor-lesson | Use when the learner wants a guided micro-lesson on one weak tag or one chosen topic (one explanation plus one practice step). Not for reading comprehension, free writing, vocabulary review, or progress reports. | created + reviewed (compliant) | [skill-rewrite-evidence.md](skill-rewrite-evidence.md) |

## Findings

- All 4 tutor skills are **compliant**: thin, `bin/tutor ... --json` only, pedagogy
  delegated to Python contracts/tests, concrete trigger-oriented descriptions, valid
  lowercase-hyphen names. **No rewrite required** (T022 yields no changes).
- All 9 Speckit skills are vendored and **not_in_scope**; no tutor-pedagogy duplication
  and no trigger overlap with tutor skills (T023 yields no changes).
- No existing skill blocks acceptance of `tutor-reading` / `tutor-lesson`. New skill
  creation still requires the subagent + writing-skills helper gate (T039, T055).
