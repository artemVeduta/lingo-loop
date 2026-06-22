# Skill Rewrite Evidence: tutor-book (Book-Reading Companion)

**Purpose**: Record required proof for every created or rewritten project `SKILL.md`,
per constitution Principle VIII "Skill Creation as Tested Contract"
(`docs/internal/constitution.md:133-148`). Source contract pattern:
[specs/005-text-modalities/skill-rewrite-evidence.md](../005-text-modalities/skill-rewrite-evidence.md).
Design source:
[docs/superpowers/specs/2026-06-22-tutor-book-reading-design.md](../../docs/superpowers/specs/2026-06-22-tutor-book-reading-design.md).

## Required inputs for every skill change

- **Local helper (mandatory)**: the constitution pins
  `/Users/artem.veduta/.claude/plugins/cache/claude-plugins-official/superpowers/5.1.0/skills/writing-skills`.
  That path is present on disk and was read for this skill. The
  `6.0.3` cache copy at
  `/Users/artem.veduta/.cache/opencode/packages/superpowers@git+https:/github.com/obra/superpowers.git/node_modules/superpowers/skills/writing-skills/SKILL.md`
  is also installed alongside it and was read by the authoring subagent (the two copies
  are byte-identical `SKILL.md` + supporting files; either satisfies the gate).
- **External references (mandatory coverage)**: the peer skill
  `skills/tutor-reading/SKILL.md` (read verbatim — `tutor-book` is modeled on it and
  ships no `scripts/run.py` shim, invoking the `tutor` console binary directly); the
  payload schemas `schemas/book_record.schema.json`, `schemas/book_session.schema.json`,
  `schemas/book_lookup_result.schema.json`, `schemas/book_log.schema.json`,
  `schemas/book_list.schema.json`, `schemas/boot_result.schema.json`, and
  `schemas/checkpoint.schema.json` (read for field-accurate payload references); and
  the design doc "Architecture & skill surface" + "Skill registration & discovery"
  subsections (frontmatter + body constraints, the 3 payload lists).
- **Subagent scope**: one subagent for the single new `tutor-book` skill (this package
  worker IS the constitution-VIII skill-authoring subagent for Package C, per the
  dispatch brief).
- **Evidence per skill**: RED baseline pressure, GREEN minimal change, REFACTOR/loophole
  closure, changed files reported by the subagent, main-agent review of every changed
  file (below).

## Blocked-rewrite decision rule

If the local writing-skills helper path above is missing, or a required external
reference is unavailable during implementation, the affected rewrite is **blocked**. A
blocked rewrite:

1. Is recorded here with `decision: blocked` and the missing input named.
2. Does not edit the target `SKILL.md`.
3. Blocks acceptance of any new skill that depends on the blocked rewrite (per the
   audit failure rules).

For `tutor-book`: `decision: not blocked` — the helper path is present, all schemas and
the peer skill were read, the design doc is approved. Authoring proceeded.

## Baseline pressure (RED) — `tutor-book` (new skill)

**Method**: Before authoring `skills/tutor-book/SKILL.md`, an agent prompted to "help me
read my book" has no skill to route to. The pressure scenarios in
[skill-pressure-scenarios.md](skill-pressure-scenarios.md) describe the rules the new
skill must teach.

**RED result**: Baseline failure (the skill does not exist yet).

- With no `tutor-book` skill, an agent asked to "help me read my book" either refuses
  or misuses `tutor-reading`, which generates a tutor-authored passage and asks
  comprehension questions — the opposite of an on-the-spot meaning lookup of the
  learner's own text. The learner's own-book lookup need is unmet.
- The own-book-text vs tutor-generated-passage discriminator is invisible at trigger
  time: nothing tells the agent that "what does this sentence in my book mean?" stays
  in a book skill while "what's the main idea of this chapter?" routes to
  `tutor-reading`.
- No skill teaches the `book start` → `book record` → `book log` orchestration, the
  `book` checkpoint modality + `answer_recorded` step_kind, the `book close`-only-on-
  explicit-request guardrail, or the `book list`-before-`resume` disambiguation.

This is a genuine RED baseline (a missing skill, not a non-compliant existing one), so
a full RED→GREEN→REFACTOR cycle is required.

## Created skill — `tutor-book`

- **Helper used (mandatory)**:
  `/Users/artem.veduta/.claude/plugins/cache/claude-plugins-official/superpowers/5.1.0/skills/writing-skills`
  (constitution-pinned; present on disk and read). The `6.0.3` cache copy was also read
  (byte-identical).
- **External references**: writing-skills guidance on naming, concrete trigger-oriented
  descriptions ("Use when…", not workflow summaries), plain `{name, description}`
  frontmatter, progressive disclosure, and the no-`bin/tutor` console-binary rule; plus
  the existing compliant peer template `skills/tutor-reading/SKILL.md` (no shim, console
  `tutor` only, thin orchestration).
- **Subagent scope**: one subagent for `tutor-book` (this package worker).
- **RED (baseline pressure)**: see Baseline pressure above — the skill did not exist;
  an agent had no route for "help me read my book" and would misuse `tutor-reading`.
- **GREEN (minimal change)**: authored `skills/tutor-book/SKILL.md` as a thin
  orchestrator that runs only `tutor` for stateful work, teaching the
  `session-start` → `book start` → `checkpoint` (`modality:"book"`,
  `step_kind:"prompt_shown"`) → lookup loop (`book record` → `checkpoint`
  `step_kind:"answer_recorded"` → display the returned `rendered`) → `book log` →
  `book list` / `book resume` → `book close`-only-on-explicit-request flow, plus the
  own-book vs tutor-passage discriminator. The 7 pressure scenarios in
  [skill-pressure-scenarios.md](skill-pressure-scenarios.md) PASS against the authored
  skill.
- **REFACTOR (loophole closure)**:
  - No `bin/tutor` literal in the body — the contract test
    `test_skill_markdown_uses_console_tutor_not_source_bin` passes (body invokes the
    `tutor` console binary only).
  - No embedded pedagogy, persistence, rendering, or scoring — the skill states the
    CLI owns validation, persistence, SRS card find-or-create, rendering, and dedup,
    and forbids inventing explanations and persisting directly, rendering through
    another LLM step, or building SRS cards itself.
  - No automatic `book close` — the skill states `book close` runs ONLY on explicit
    learner request, mirroring the `session-close` guardrail; same for
    `session-close`/`session-end`.
  - Frontmatter is EXACTLY `{name, description}` — the contract test
    `test_skill_frontmatter_is_plain_name_description_only` passes (no `version`, no
    `allowed-tools`, no other keys).
  - Ships no `scripts/run.py` shim (matches `tutor-reading`, the peer it is modeled
    on; YAGNI per the design doc).
- **Final description**: "Use when the learner has their OWN book or text in front of
  them and wants on-the-spot lookups of words, sentences, or passages they don't
  understand, or to ask about the text they are reading. Looked-up words are saved and
  added to vocabulary spaced-repetition review. tutor-reading is for comprehension Q&A
  on tutor-generated passages; tutor-vocab is for standalone vocab drills." (trigger-
  oriented "Use when…" with the own-book vs tutor-reading vs tutor-vocab discriminator
  surfaced at trigger time, per the design doc.)
- **Changed files reported by the subagent**:
  - `skills/tutor-book/SKILL.md` (created)
  - `src/language_tutor/installer/providers/base.py` (registered in `SKILL_FILES`)
  - `src/language_tutor/package_assets.py` (registered in `REQUIRED_SKILL_PAYLOAD_FILES`)
  - `pyproject.toml` (registered in `[tool.hatch.build.targets.wheel.force-include]`)
- **Main-agent changed-file review**: reviewed all four files. Confirmed: thin
  (orchestrate `tutor ... --json` console commands only), no pedagogy/persistence in
  the skill, lowercase-hyphen name, concrete trigger-oriented description, plain
  `{name, description}` frontmatter, no `bin/tutor` literal, no auto-close, the 3
  payload lists updated in lockstep with the file creation so
  `tests/installer/test_skill_payload_contract.py` stays green (5/5). **Accepted.**
