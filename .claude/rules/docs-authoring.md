---
paths:
  - "docs/**/*.md"
---

# Authoring the docs bundle

- The `docs/` bundle is OKF v0.1. The canonical policy is
  `docs/conventions/documentation.md` — apply it, do not restate it here.
- The validator skips any excluded top-level dir (default: `superpowers/`); edit
  `excludedTopLevelDirs` in `scripts/validate-docs.mjs` if your bundle needs a different set.
- Every non-reserved file needs frontmatter with a non-empty `type`; recommended:
  `title`, `description`, ISO `timestamp`. Links are bundle-relative absolute (`/a/b.md`).
- `index.md` carries no frontmatter (except root's `okf_version`); `log.md` uses
  `## YYYY-MM-DD` headings, newest first.
- **Update ceremony** (this is an edit, so it applies now): bump `timestamp`; append a
  `log.md` entry; amend `Decision`s (dated `# Amendments`, never rewrite); supersede via
  `status` + `superseded_by`, never silent delete.
- **Separate truth by type** — `docs/` holds explanatory truth (ADRs, glossary, business
  rules, runbooks, architecture/ownership/cross-system context); executable truth (code,
  tests, schemas, workflow YAML, generated API ref — everything outside `docs/`) is
  referenced, never pasted. It drifts and the validator can't catch it. Short
  pseudo-code/formulas/shapes are fine. See "Code in concepts" in the policy.
- Use the `docs-add` skill to scaffold a new concept; `docs-validate` is the backstop.
