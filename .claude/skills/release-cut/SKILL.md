---
name: release-cut
description: Use when the user says "cut release X.Y.Z", "/release-cut X.Y.Z", "open release PR", "prepare release branch", or otherwise asks to start a release of language-tutor by opening a chore/release branch and PR (does NOT push tags or merge)
---

# release-cut

## Overview

Open a release PR for version `X.Y.Z`: branch, promote CHANGELOG, bump `pyproject.toml`, commit with DCO sign-off, push, and `gh pr create`. **Stop after PR creation** — tagging, merging, and publishing are explicitly out of scope and are handled by a human reviewer (and later by `/release-tag`).

This skill assumes you are at the repository root of `language-tutor` on a clean working tree.

## When to Use

- User invokes `/release-cut X.Y.Z`.
- User says "cut release X.Y.Z", "open the release PR for X.Y.Z", "prepare the release branch".

**Do NOT use this skill to:**
- Push annotated tags (that is `/release-tag`).
- Merge the release PR.
- Publish artifacts.

## Prerequisites

1. `X.Y.Z` is a valid semver string (no leading `v`).
2. `pre-release-checks` ran clean **in this session**. If it has not, invoke it first and only proceed if it passed. Do not proceed on a stale or unknown check state.
3. Working tree is clean (`git status` shows no uncommitted changes), and you are on `main` (or whichever branch the user designated as the release base) and up to date with `origin`.
4. `CHANGELOG.md` has a populated `[Unreleased]` section worth releasing.

If any prerequisite fails, STOP and report which one — do not attempt to fix silently.

## Steps

Execute strictly in order. Do not batch step 5+ before user approval in step 4.

1. **Branch**
   ```bash
   git checkout -b chore/release-X.Y.Z
   ```

2. **Promote CHANGELOG** — invoke the existing script, do not reimplement its logic:
   ```bash
   ./scripts/changelog-promote.sh X.Y.Z
   ```
   This renames `[Unreleased]` to `[X.Y.Z] - YYYY-MM-DD` and inserts a fresh empty `[Unreleased]` section on top.

3. **Bump `pyproject.toml`** — only if `version` is not already `X.Y.Z`. Edit the single `version = "..."` line under `[project]` (or `[tool.poetry]`, whichever the file uses). Do not touch anything else.

4. **STOP — show diff and request user confirmation.** This is the irreversible step boundary.
   ```bash
   git --no-pager diff
   git --no-pager status
   ```
   Present the diff to the user and ask: "Proceed with commit, push, and PR creation?" Wait for explicit approval before continuing. Do not assume approval from prior context.

5. **Commit with DCO sign-off** (the `-s` flag adds `Signed-off-by:`; required by the project's DCO check):
   ```bash
   git add CHANGELOG.md pyproject.toml
   git commit -s -m "chore(release): X.Y.Z"
   ```

6. **Push**
   ```bash
   git push -u origin chore/release-X.Y.Z
   ```

7. **Open PR** — body is templated from the new `[X.Y.Z]` CHANGELOG section. Use a HEREDOC to preserve formatting:
   ```bash
   gh pr create --title "chore(release): X.Y.Z" --base main --head chore/release-X.Y.Z --body "$(cat <<'EOF'
   ## Release X.Y.Z

   <paste the [X.Y.Z] CHANGELOG section here verbatim>

   ## Checklist
   - [ ] CI green
   - [ ] CHANGELOG promoted
   - [ ] `pyproject.toml` version bumped
   - [ ] DCO sign-off present

   After merge: run `/release-tag X.Y.Z`.
   EOF
   )"
   ```

8. **STOP.** Report the PR URL and the next-step instruction. Do **not** continue to tagging, merging, or publishing.

## Output Format

Report exactly:

```
Release PR opened: <PR URL>
Next: after merge to main, run `/release-tag X.Y.Z`.
```

## Quick Reference

| Step | Command | Reversible? |
|------|---------|-------------|
| 1 | `git checkout -b chore/release-X.Y.Z` | yes (`git branch -D`) |
| 2 | `./scripts/changelog-promote.sh X.Y.Z` | yes (`git restore CHANGELOG.md`) |
| 3 | Edit `pyproject.toml` version | yes (`git restore`) |
| 4 | Show diff, **await user approval** | — |
| 5 | `git commit -s` | yes locally |
| 6 | `git push -u origin ...` | hard to undo (visible upstream) |
| 7 | `gh pr create --fill` body from CHANGELOG | requires PR close |
| 8 | STOP — hand off to reviewer | — |

## Red Flags — STOP and Reassess

- `pre-release-checks` did not run clean in this session → run it first.
- Working tree is dirty → stash or commit unrelated changes elsewhere.
- `[Unreleased]` section in `CHANGELOG.md` is empty → confirm with user that an empty release is intentional (usually it is not).
- `changelog-promote.sh` is missing or fails → STOP. Do not hand-edit `CHANGELOG.md` to substitute; the script is the single source of truth.
- User asks you to "also push the tag" or "also merge" → refuse and direct them to `/release-tag` after merge.

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| Hand-editing CHANGELOG instead of calling the script | Always invoke `scripts/changelog-promote.sh`. |
| `git commit` without `-s` | DCO check fails on PR. Always use `-s`. |
| Skipping the diff/approval pause (step 4) | The commit/push/PR sequence is the irreversible boundary. Always pause. |
| Pushing a tag in this skill | Out of scope. Tags are `/release-tag`'s job. |
| Merging the PR yourself | Out of scope. Human reviewer merges. |
| Prefixing version with `v` (e.g. `v1.2.3`) | Pass bare semver `X.Y.Z`; the script and `pyproject.toml` expect no prefix. |
