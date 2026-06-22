---
name: pre-release-checks
description: Use when about to cut a release, tag a version, publish to PyPI, or the user says "/pre-release", "before I cut a release", "verify release readiness", "pre-release checks", or "is this ready to ship" — runs a read-only PASS/FAIL audit of repo state, build, tests, lint, types, and coverage before tagging.
---

# Pre-Release Checks

## Overview

Read-only gate that verifies the repo is safe to tag and publish. Runs a fixed
checklist and prints a PASS/FAIL table. Does **not** mutate the repo: no
commits, tags, pushes, or version bumps. If any check FAILs, the release is
blocked until the blocker is fixed by the human (or a separate skill).

## Trigger

- Slash form: `/pre-release` or `/pre-release X.Y.Z`
- Natural language: "before I cut a release", "pre-release checks",
  "verify release readiness", "is this ready to ship".

## Inputs

| Input | Required | Default |
|-------|----------|---------|
| `version` (X.Y.Z) | no | next patch bump from `pyproject.toml [project].version` |

The version is informational — used to compute the tag name `vX.Y.Z` for the
"tag does not exist" check. No file is rewritten.

## Checks

All must PASS. Run in this order; keep going after a FAIL so the final table
shows every blocker, not just the first.

| # | Check | Command | PASS condition |
|---|-------|---------|----------------|
| 1 | Working tree clean | `git status --porcelain` | empty output |
| 2 | On `main`           | `git rev-parse --abbrev-ref HEAD` | equals `main` |
| 3 | Up-to-date with `origin/main` | `git fetch origin main` then compare `git rev-parse HEAD` vs `git rev-parse origin/main` | equal |
| 4 | `CHANGELOG.md` `[Unreleased]` non-empty | parse `CHANGELOG.md` | `[Unreleased]` section contains at least one subsection (`### Added/Changed/Fixed/...`) with at least one non-blank bullet |
| 5 | Tag `vX.Y.Z` unused | `git rev-parse -q --verify "refs/tags/vX.Y.Z"` and `git ls-remote --tags origin "vX.Y.Z"` | both empty / non-zero exit |
| 6 | Build + metadata     | `bash scripts/build-check.sh` | exit 0 |
| 7 | Tests green          | `uv run pytest` | exit 0 |
| 8 | Lint clean           | `uv run ruff check` | exit 0 |
| 9 | Types clean          | `uv run pyright` | exit 0 |
| 10 | Coverage gate       | covered by check 7 (`--cov-fail-under` configured in `pyproject.toml [tool.pytest.ini_options].addopts`) | pytest exit 0 satisfies it |

**Delegate build + metadata to the script.** Do not inline `uv build` or
`twine check` — call `bash scripts/build-check.sh` so the logic stays in one
place.

## Workflow

1. Resolve `version`: use the user-supplied value if given, else read
   `[project].version` from `pyproject.toml` and bump patch.
2. Run checks 1–5 (cheap, no side effects in the working tree).
3. Run check 6 (`scripts/build-check.sh`); it writes to `dist/` but does not
   touch tracked files. Capture exit code; do not abort the suite on failure.
4. Run checks 7–9 sequentially. Capture each exit code.
5. Print the PASS/FAIL table (see below).
6. If any row is FAIL, exit the skill with a clear "BLOCKED" verdict. Do not
   propose tagging, pushing, or editing files.

## Output Format

Print exactly one table, then a verdict line, then per-FAIL remediation.

```
Pre-release checks for v0.2.0

| #  | Check                          | Result |
|----|--------------------------------|--------|
| 1  | Working tree clean             | PASS   |
| 2  | On main                        | PASS   |
| 3  | Up-to-date with origin/main    | FAIL   |
| 4  | CHANGELOG [Unreleased] populated| PASS  |
| 5  | Tag v0.2.0 unused              | PASS   |
| 6  | uv build + twine check         | PASS   |
| 7  | pytest (incl. coverage gate)   | PASS   |
| 8  | ruff check                     | PASS   |
| 9  | pyright                        | PASS   |

Verdict: BLOCKED (1 failure)

Blockers:
- #3 Up-to-date with origin/main — local main is 2 commits behind. Fix:
     `git pull --ff-only origin main`, then re-run /pre-release.
```

On full pass:

```
Verdict: READY to tag v0.2.0
```

## Remediation Hints (per check)

| Check | Typical fix |
|-------|-------------|
| 1 | Commit, stash, or revert pending changes. |
| 2 | `git switch main`. |
| 3 | `git pull --ff-only origin main`; resolve divergence before retrying. |
| 4 | Add entries under `## [Unreleased]` in `CHANGELOG.md`. |
| 5 | Pick a different version, or delete the stale tag (only if intentional). |
| 6 | Read `dist/` and `twine check` output; fix packaging metadata in `pyproject.toml`. |
| 7 | Fix failing tests or raise coverage above the configured `--cov-fail-under` gate. |
| 8 | `uv run ruff check --fix` for autofixable items; otherwise fix manually. |
| 9 | Resolve type errors reported by `pyright`. |

## Constraints (Iron Rules)

- **Read-only.** No `git add`, no `git commit`, no `git tag`, no `git push`,
  no edits to `pyproject.toml` / `CHANGELOG.md`. The only writes allowed are
  build artifacts under `dist/` (produced by `scripts/build-check.sh`).
- **No partial verdicts.** Always print the full table covering every check,
  even if an early check fails.
- **Delegate, don't duplicate.** Build + metadata validation lives in
  `scripts/build-check.sh`. Do not re-implement it in markdown or in the
  shell session.
- **Don't auto-fix.** Suggest fixes in the remediation section; let the human
  (or a different skill) apply them.

## Red Flags — STOP

- About to run `git tag` or `git push` → STOP, that belongs to the release
  skill, not this one.
- About to edit `pyproject.toml` to bump version → STOP, read-only.
- Skipping a check because "it was green last time" → STOP, run all checks.
- Reporting PASS without having actually run the command → STOP, run it.
