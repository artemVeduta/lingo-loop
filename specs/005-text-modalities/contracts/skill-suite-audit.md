# Contract: Skill Suite Audit

## Scope

This contract governs Phase 5 skill inventory, rewrite evidence, and final coherence review.

## Inventory Inputs

Inventory source roots:

```text
skills/
.agents/skills/
```

File selector:

```text
**/SKILL.md
```

## Inventory Output

Artifact:

```text
specs/005-text-modalities/skill-inventory.md
```

Each row must include:

- Project-relative path.
- Skill name.
- Frontmatter description.
- Purpose.
- Trigger scope.
- Progressive disclosure status.
- CLI/contract convention status.
- Pedagogy ownership status.
- Compliance decision.
- Required evidence or blocker.

## Rewrite Evidence Output

Artifact:

```text
specs/005-text-modalities/skill-rewrite-evidence.md
```

Required for every created or rewritten `SKILL.md`:

- Local helper use: `/Users/artem.veduta/.claude/plugins/cache/claude-plugins-official/superpowers/5.1.0/skills/writing-skills`.
- External reference coverage required by the active spec and constitution.
- Assigned subagent scope.
- RED baseline pressure evidence.
- GREEN minimal-change evidence.
- REFACTOR/loophole closure evidence.
- Changed files reported by the subagent.
- Main-agent changed-file review.

## Final Coherence Output

Artifact:

```text
specs/005-text-modalities/skill-suite-coherence-audit.md
```

The final audit passes only when:

- Every existing skill is inventoried exactly once.
- `tutor-reading` and `tutor-lesson` are included after creation.
- Transcript drills are confirmed as `tutor-reading` submode, not a standalone skill.
- No unresolved trigger overlap exists across tutor and active Speckit skills.
- No duplicated pedagogy lives in skills instead of Python contracts/tests.
- CLI command conventions match existing `bin/tutor ... --json` usage.
- Frontmatter names and descriptions meet constitution rules.

## Failure Rules

Any missing inventory row, missing rewrite evidence, unresolved trigger overlap, unreviewed changed file, or unavailable required helper/reference blocks new skill acceptance.
