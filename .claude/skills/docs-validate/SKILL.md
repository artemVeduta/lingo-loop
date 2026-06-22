---
name: docs-validate
description: Validate the docs/ OKF bundle for conformance (parseable frontmatter + non-empty type) and report soft warnings. Use when the user asks to "validate docs", "check the docs bundle", "find docs conformance issues", or invokes /docs-validate directly.
---

# docs-validate

## First, read the canonical policy

**MANDATORY:** read `docs/conventions/documentation.md` first — it defines the
frontmatter standard, reserved-file rules, and what is hard vs soft. This skill does not
restate them.

## The command

Run from the **repo root** (your Claude launch directory):

```
npm run docs:validate
```

It walks `docs/` (excluding `docs/superpowers/**`) and prints a report. Do not pass flags
— the script accepts only an optional root path argument and is not meant to take flags.

```
"docs:validate": "node scripts/validate-docs.mjs"
```

## How to read the output

The validator is **advisory and always exits 0** (it never blocks). Read the _output_,
not the exit code:

| Section                               | Meaning                                                                                                                       | Action                                                             |
| ------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------ |
| `ERRORS — OKF §9 conformance`         | A non-reserved file has unparseable frontmatter or an empty/missing `type`. **This is the hard bar.**                         | Fix the frontmatter before considering the bundle conformant.      |
| `Warnings — recommended/soft`         | Missing `title`/`description`/`timestamp`, non-ISO timestamp, broken internal link, or a concept missing from its `index.md`. | Triage. Broken links may be not-yet-written knowledge (tolerated). |
| `OKF bundle conformant; no warnings.` | Clean.                                                                                                                        | Report success.                                                    |

## Resolution flow

1. Show the user the full report.
2. **Errors** — for each, open the file and add/fix the `type` (and the `---` fences).
   Propose the edit; apply only after the user approves.
3. **Warnings** — propose fixes (add recommended fields, fix the link target or remove
   the link, add the missing `index.md` entry). Apply only after approval.
4. Re-run `npm run docs:validate` and confirm the ERRORS section is empty.

## Things to NEVER do

- Never treat a warning as a failure — broken links and missing optional fields are
  tolerated by OKF.
- Never add frontmatter to a non-root `index.md` to "fix" it — that is itself a violation.
- Never invent CLI flags (`--fix`, `--json`); there are none.
- Never edit files under `docs/superpowers/**` — they are outside the bundle.
