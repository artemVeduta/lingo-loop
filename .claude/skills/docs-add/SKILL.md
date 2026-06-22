---
name: docs-add
description: Scaffold a new OKF concept in the docs/ bundle (Decision, Specification, Convention, Glossary, Reference) or a subsystem index node, with conformant frontmatter, and update the parent index.md + log.md. Use when adding documentation, an ADR/decision record, a spec, a glossary term, or a new subsystem to docs/ — or when invoked as /docs-add.
---

# docs-add

## First, read the canonical policy

**MANDATORY:** before scaffolding anything, read `docs/conventions/documentation.md` —
the single source of truth for the frontmatter standard, the taxonomy, reserved-file
rules, and the create/update/supersede flow. This skill does not restate those rules; it
applies them.

## What this skill does

Scaffolds one conformant concept from the matching template in
`.claude/skills/docs-add/templates/`, places it at the right bundle path, updates the
parent `index.md`, and appends a `log.md` `**Creation**` entry.

## Procedure

1. **Pick the `type`** (Decision / Specification / Convention / Glossary / Reference) — or
   a Subsystem index node. Pick the location: repo-wide knowledge at the top level
   (`docs/conventions|glossary|references/`), subsystem knowledge nested
   (`docs/<subsystem>/...`).
2. **Choose the concept ID** = the bundle-relative path minus `.md`, kebab-case filename.
3. **Copy the template** from `templates/<type>.md` (or `templates/subsystem-index.md`)
   and fill every `<placeholder>`: real `title`, one-sentence `description`, and today's
   ISO `timestamp`. `type` is non-empty and from the taxonomy.
4. **Update the parent `index.md`** — add a `[Title](/abs/path.md) - description` bullet
   under the right section heading.
5. **Append to the nearest `log.md`** — `* **Creation**: <one line> [Title](/abs/path.md).`
   under today's `## YYYY-MM-DD` heading (create the heading if absent, newest first).

## Approval gate — STOP before writing

**Analyse first, then ask, then wait.** Present the full plan in one message: the concept
path, its frontmatter, the body skeleton, the `index.md` bullet, and the `log.md` line.
Ask plainly — **"Ready to apply this? (yes / no)"** — and wait. Silence or "looks good"
is not approval; only an explicit yes is.

## Verification

After writing, run from the repo root:

```
npm run docs:validate
```

Confirm **zero hard ERRORS** for the new file. Triage warnings (missing recommended
fields, broken links). The validator never blocks — a clean errors section is the bar.

## Things to NEVER do

- Never put frontmatter in a non-root `index.md`, or omit `okf_version` from the root one.
- Never invent a frontmatter `type` outside the taxonomy without first noting it in
  `docs/conventions/documentation.md` (the taxonomy is open, but record additions).
- Never rewrite a `Decision`'s history — append a dated `# Amendments` entry instead.
- Never skip updating `index.md` + `log.md` — a concept that nothing links to is invisible.
- Never write into `docs/superpowers/**` — that is not part of the bundle.
