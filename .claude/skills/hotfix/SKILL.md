---
name: hotfix
description: Use when patching a bug in an already-released production version, hotfixing a shipped release, applying an emergency fix off the latest production tag, or invoked via /hotfix <bug-ref>. Branches off the latest production tag (excluding prereleases), not main. Triggers a patch-version release on merge.
---

# hotfix

## Overview

Apply a fix to the **last shipped production version** without pulling in unreleased work from `main`. The fix branches off the latest production tag (excluding `-rc*`, `-alpha*`, `-beta*`), gets reviewed via PR, and triggers a patch bump (`X.Y.Z+1`) through the `release-cut` skill on merge.

**Core principle:** Hotfixes isolate users from main's drift. Never branch a hotfix off `main`.

## When to Use

- User invokes `/hotfix <bug-ref>` where `<bug-ref>` is a GitHub issue number or short slug.
- A bug reported against a released version must be patched without shipping unreleased work.
- An emergency fix needs to ship before the next planned release.

**When NOT to use:**
- Bug only reproduces against unreleased `main` work → fix on `main` via normal PR flow.
- Bug fix wants to bundle with other unreleased features → normal PR flow.

## Hard Preconditions (REFUSE if violated)

1. **Working tree must be clean.** Run `git status --porcelain`; if output is non-empty, STOP and tell the user to stash/commit/discard first. Do not proceed.
2. **A production tag must exist.** Step 1 of the workflow must return a tag; if it errors (no tags match), STOP and report.

## Workflow

### Step 1 — Verify clean tree

```bash
git status --porcelain
```
If non-empty → REFUSE. Output: `Working tree dirty; commit/stash before /hotfix.`

### Step 2 — Determine latest production tag

```bash
git fetch --tags --quiet
LATEST_TAG=$(git describe --tags --abbrev=0 --match 'v*.*.*' \
  --exclude '*-rc*' --exclude '*-alpha*' --exclude '*-beta*')
echo "$LATEST_TAG"
```

**Critical:** the `--exclude` flags MUST be present. A prerelease tag (`v1.2.0-rc1`) would otherwise be picked and the hotfix would branch off unreleased code.

### Step 3 — Create fix branch off the tag

```bash
git checkout -b "fix/<slug>" "$LATEST_TAG"
```
`<slug>` derives from `<bug-ref>`: GH issue → `issue-<n>`, otherwise the user-supplied slug. Branch name must start with `fix/`.

### Step 4 — PAUSE for user implementation

**STOP here.** Hand control back to the user:

> Branched `fix/<slug>` off `<LATEST_TAG>`. Implement the fix and tests now. Reply `done` when ready to verify and ship.

Do NOT proceed to Step 5 until the user signals completion.

### Step 5 — Verify tests green

```bash
pytest
```
If any test fails → STOP, report, do not commit.

### Step 6 — Update CHANGELOG

Append an entry under `[Unreleased]` → `### Fixed` in `CHANGELOG.md`. If those sections do not exist, create them. Format:

```markdown
## [Unreleased]

### Fixed
- <one-line description> (<bug-ref>)
```

### Step 7 — Commit with DCO sign-off

```bash
git add -A
git commit -s -m "fix(<scope>): <subject>"
```
The `-s` flag is **mandatory** (DCO sign-off). `<scope>` matches the affected module; `<subject>` is imperative, lowercase, no period.

### Step 8 — Push and open PR

```bash
git push -u origin "fix/<slug>"
gh pr create --base main --head "fix/<slug>" \
  --title "fix(<scope>): <subject>" \
  --body "Fixes <bug-ref>. Branched off <LATEST_TAG>."
```

### Step 9 — Hand off to release-cut on merge

After the PR merges, invoke the `release-cut` skill with a **patch bump** (`X.Y.Z` → `X.Y.(Z+1)`). Tell the user:

> PR merged. Next: run `release-cut` with patch bump from `<LATEST_TAG>`.

## Quick Reference

| Step | Command / Action | Stop condition |
|------|------------------|----------------|
| 1 | `git status --porcelain` | non-empty → REFUSE |
| 2 | `git describe ... --exclude '*-rc*' ...` | error → REFUSE |
| 3 | `git checkout -b fix/<slug> <tag>` | — |
| 4 | **PAUSE** for user fix | wait for `done` |
| 5 | `pytest` | failure → STOP |
| 6 | Edit `CHANGELOG.md` `[Unreleased]/Fixed` | — |
| 7 | `git commit -s -m "fix(...): ..."` | — |
| 8 | `git push` + `gh pr create` | — |
| 9 | Hand off to `release-cut` (patch bump) | — |

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| Branching off `main` | Always branch off `$LATEST_TAG` from Step 2. |
| Dropping `--exclude '*-rc*'` | Hotfix lands on unreleased prerelease. Keep all `--exclude` flags. |
| Forgetting `-s` on commit | DCO check fails on PR. Re-commit with `--amend -s` or new commit. |
| Skipping the user-pause | Skill must not implement the fix itself. Pause at Step 4. |
| Bumping minor/major on release | Hotfix → patch bump only. Hand `release-cut` an explicit patch instruction. |
| CHANGELOG entry under a version heading | Must go under `[Unreleased]` → `### Fixed`. |

## Red Flags — STOP

- Working tree dirty when invoked.
- `git describe` returned a tag containing `-rc`, `-alpha`, or `-beta`.
- About to run `git checkout -b fix/... main` — wrong base.
- About to commit without `-s`.
- About to hand off to `release-cut` with anything other than patch bump.
