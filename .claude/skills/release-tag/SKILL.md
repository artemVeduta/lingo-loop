---
name: release-tag
description: Use when the user wants to tag a release, push a release tag, cut a vX.Y.Z tag, or publish to PyPI / TestPyPI after a release PR has merged to main. Triggers on "/release-tag X.Y.Z", "tag release", "push release tag", "publish vX.Y.Z", "cut tag for X.Y.Z".
---

# release-tag

## Overview

Tag a version on `main` and push the tag to GitHub. Tag push triggers `.github/workflows/workflow.yml`, which owns build + publish routing (final tag → PyPI, `-rc.N` / `-alpha.N` / `-beta.N` → TestPyPI). This skill stops at `git push origin vX.Y.Z` — it does not wait for the workflow.

**This action is irreversible.** A pushed tag triggers a public publish. Confirm with the user before pushing.

## Inputs

- `X.Y.Z` — the version. Accept SemVer + optional pre-release suffix (`1.4.0`, `1.4.0-rc.1`, `2.0.0-beta.2`). Construct the tag as `vX.Y.Z`.

## Preconditions — REFUSE if any fail

Run these checks in order. If any fail, STOP and report to the user. Do not attempt to "fix" by committing, stashing, or switching branches automatically.

1. **Release PR merged.** The release PR for `X.Y.Z` must already be merged to `main`. Check with:
   ```bash
   gh pr list --state merged --search "release X.Y.Z in:title" --limit 5
   ```
   If no merged PR matches (try variants: `chore(release): X.Y.Z`, `release X.Y.Z`, `vX.Y.Z`), REFUSE and tell the user to merge the release PR first.

2. **On `main` with clean working tree.** After `git checkout main && git pull --ff-only`:
   ```bash
   git rev-parse --abbrev-ref HEAD   # must print: main
   git status --porcelain            # must be empty
   ```
   If dirty or not on `main`, REFUSE. Tell the user to clean up; do not auto-stash.

3. **Tag does not already exist.**
   ```bash
   git rev-parse -q --verify "refs/tags/vX.Y.Z" && echo EXISTS || echo OK
   git ls-remote --tags origin "refs/tags/vX.Y.Z"
   ```
   If either reports the tag exists, REFUSE.

4. **`pyproject.toml` matches tag.** Run the repo guard:
   ```bash
   bash scripts/version-guard.sh vX.Y.Z
   ```
   Non-zero exit → REFUSE. The merged release PR was supposed to bump `pyproject.toml`; if it didn't, that's a release-PR bug, not something to patch here.

## Procedure

After all preconditions pass:

1. `git checkout main && git pull --ff-only`
2. `bash scripts/version-guard.sh vX.Y.Z`
3. **Confirm with the user.** Show the tag, the target commit (`git rev-parse HEAD`), and state plainly: *"Pushing this tag will trigger PyPI/TestPyPI publish via `.github/workflows/workflow.yml`. This is irreversible. Proceed?"* Wait for explicit yes.
4. Create the tag. Prefer signed if a signing key is configured (`git config --get user.signingkey` returns non-empty):
   ```bash
   git tag -s vX.Y.Z -m "release X.Y.Z"   # if signing key present
   git tag -a vX.Y.Z -m "release X.Y.Z"   # otherwise
   ```
5. `git push origin vX.Y.Z`
6. Print:
   - Tag URL: `https://github.com/<owner>/<repo>/releases/tag/vX.Y.Z` (derive `<owner>/<repo>` from `gh repo view --json nameWithOwner -q .nameWithOwner`).
   - Actions URL: `https://github.com/<owner>/<repo>/actions` (or the specific run via `gh run list --workflow workflow.yml --limit 1 --json url -q '.[0].url'` once it appears).
   - Offer: *"Run `gh run watch` to follow the workflow live?"* Do not run it unless asked.

Stop here. The workflow owns build, version-guard re-check, publish routing, and provenance.

## Quick Reference

| Step | Command |
|------|---------|
| Sync main | `git checkout main && git pull --ff-only` |
| Guard | `bash scripts/version-guard.sh vX.Y.Z` |
| Tag (signed) | `git tag -s vX.Y.Z -m "release X.Y.Z"` |
| Tag (unsigned) | `git tag -a vX.Y.Z -m "release X.Y.Z"` |
| Push | `git push origin vX.Y.Z` |
| Find run | `gh run list --workflow workflow.yml --limit 1` |

## Red Flags — STOP

- Release PR for this version is not merged → REFUSE.
- Working tree dirty, or HEAD not on `main` → REFUSE. Do not auto-stash, auto-commit, or auto-checkout.
- `version-guard.sh` fails → REFUSE. Do not edit `pyproject.toml` here.
- Tag already exists locally or on `origin` → REFUSE. Do not delete and re-push.
- User has not explicitly confirmed the push → STOP. Confirmation is required because publish is irreversible.

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| Editing `pyproject.toml` when guard fails | Don't. Fix it in a release PR; re-merge; re-run skill. |
| Force-pushing or deleting an existing tag to "redo" a release | Don't. Cut a new patch version. PyPI does not allow re-upload of the same version. |
| Waiting for the workflow inside this skill | Out of scope. Hand off after `git push`. Offer `gh run watch` if the user wants live output. |
| Skipping user confirmation because "the user already said run it" | The `/release-tag` invocation is not the publish confirmation. Confirm again immediately before `git push`. |
| Treating `-rc.N` as a final release | Tag pattern routing is owned by `workflow.yml` (final → PyPI, pre-release → TestPyPI). The skill does not branch on suffix. |
