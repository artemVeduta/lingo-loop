# Skill Rewrite Evidence: Text Modalities + Skill Authoring

**Purpose**: Record required proof for every created or rewritten project `SKILL.md`.
Source contract: [contracts/skill-suite-audit.md](contracts/skill-suite-audit.md).

## Required inputs for every skill change

- **Local helper (mandatory)**:
  `/Users/artem.veduta/.claude/plugins/cache/claude-plugins-official/superpowers/5.1.0/skills/writing-skills`
- **External references (mandatory coverage)**: skill-authoring references named by the
  active spec and `.specify/memory/constitution.md`. Each rewrite records which references
  were consulted.
- **Subagent scope**: one subagent per skill or coherent skill family.
- **Evidence per skill**: RED baseline pressure, GREEN minimal change, REFACTOR/loophole
  closure, changed files reported by the subagent, main-agent review of every changed file.

## Blocked-rewrite decision rule

If the local writing-skills helper path above is missing, or a required external reference
is unavailable during implementation, the affected rewrite is **blocked**. A blocked rewrite:

1. Is recorded here with `decision: blocked` and the missing input named.
2. Does not edit the target `SKILL.md`.
3. Blocks acceptance of any new skill that depends on the blocked rewrite (per the audit
   failure rules).

## Baseline pressure (RED) — existing skills (T021)

**Method**: Reviewed all 13 inventoried `SKILL.md` files against the trigger-boundary
pressure scenarios in `tests/fixtures/text_modalities/skill_pressure.json` and the
constitution skill-creation gate (thin orchestration, `bin/tutor ... --json` only,
pedagogy owned by Python contracts/tests, concrete trigger-oriented descriptions,
lowercase-hyphen names, progressive disclosure).

**RED result**: No baseline failure found.

- 4 tutor skills (`tutor-setup`, `tutor-vocab`, `tutor-writing`, `tutor-progress`):
  each is thin, CLI-only, defers pedagogy to the CLI, and has a concrete description.
  Pressure scenarios route to the correct single skill with no cross-trigger. **No
  rewrite triggered.**
- 9 Speckit skills: vendored from `github-spec-kit`, out of tutor scope, no pedagogy
  duplication, no trigger overlap with tutor skills. **Not in scope for rewrite.**

Because no existing skill is non-compliant, T022 and T023 produce **no changes** and no
RED→GREEN→REFACTOR rewrite cycle is required for existing skills. The subagent +
writing-skills-helper authoring gate still applies to the **new** skills created in this
feature (`tutor-reading` in T039/T069, `tutor-lesson` in T055).

## Created / rewritten skills

### Existing tutor skills (T022) and Speckit skills (T023)

`decision: compliant` (tutor) / `not_in_scope` (Speckit). No edits performed; see baseline
above. Main-agent review: confirmed against the inventory and current `SKILL.md` contents.

### New skills — tutor-reading (T041) + tutor-reading transcript submode (T070) + tutor-lesson (T057)

- **Helper used (mandatory)**:
  `/Users/artem.veduta/.claude/plugins/cache/claude-plugins-official/superpowers/5.1.0/skills/writing-skills`
  (read by the assigned subagent).
- **External references**: writing-skills guidance on naming, concrete trigger-oriented
  descriptions ("use when…", not workflow summaries), progressive disclosure, and
  subagent invocation-pressure testing; plus the existing compliant tutor-skill template
  (`tutor-writing`, `tutor-vocab`, `tutor-progress`).
- **Subagent scope**: one subagent for the coherent `tutor-reading` + `tutor-lesson`
  family (transcript is a `tutor-reading` submode, reviewed in the same pass).
- **RED (baseline pressure)**:
  - `tutor-reading`: description was a capability/what-it-does summary, not trigger-oriented;
    no negative boundary (risked co-triggering with `tutor-writing`/`tutor-lesson`/`tutor-vocab`);
    text-only/no-audio guard lived only in the body, invisible at trigger-selection time.
  - `tutor-lesson`: description was a what-it-does summary; no negative boundary (risked
    over-triggering on broad "teach me X" and bleeding into reading/writing); the
    one-bounded-topic scope existed only in the body.
- **GREEN (minimal change)**: rewrote the YAML `description` of both skills only. Bodies
  were already thin and compliant (CLI-only orchestration, explicit no-audio for reading,
  transcript as `mode:"transcript"` submode, one-topic guard for lesson).
- **REFACTOR**: surfaced text-only/no-audio (reading) and single-topic scope (lesson) into
  the trigger; added explicit exclusion lists; no body edits needed.
- **Final descriptions**:
  - tutor-reading: "Use when the learner wants to read a passage and answer comprehension
    questions, or reconstruct a text transcript drill (text-only, no audio). Not for free
    writing, vocabulary review, or guided lessons."
  - tutor-lesson: "Use when the learner wants a guided micro-lesson on one weak tag or one
    chosen topic (one explanation plus one practice step). Not for reading comprehension,
    free writing, vocabulary review, or progress reports."
- **Changed files reported by subagent**:
  - `skills/tutor-reading/SKILL.md`
  - `skills/tutor-lesson/SKILL.md`
- **Main-agent changed-file review**: reviewed both files. Confirmed: thin (orchestrate
  `bin/tutor ... --json` + `render feedback` + `tutor-judge` only), no pedagogy/persistence
  in skill, lowercase-hyphen names, concrete trigger-oriented descriptions, reading stays
  text-only with transcript as a submode (not a separate skill), lesson bounded to one
  topic + one practice step. **Accepted.**
