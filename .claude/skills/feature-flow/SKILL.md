---
name: feature-flow
description: Use when the user says "/feature <slug> '<intent>'", "start a feature", "new feature with spec", "feature flow", "spec-then-implement a feature", or otherwise asks to take a feature from intent through OpenSpec proposal, branch, implementation, verification, PR, and archive in one orchestrated pass.
---

# feature-flow

## Overview

Thin orchestrator that walks a feature from **intent** to **merged PR + archived OpenSpec change** by delegating each phase to an existing skill. This skill does **not** reimplement any OpenSpec judgment, task selection, or archiving logic — it only sequences the existing `openspec-propose`, `openspec-apply-change`, and `openspec-archive-change` skills around a branch, verify, and PR step.

**Stops at:** the merged feature PR URL plus archive confirmation. Anything further (release cut, tag, publish) is out of scope.

## When to Use

- User invokes `/feature <slug> "<intent>"`.
- User says "start a feature called X", "spec and implement Y", "run the full feature flow for Z".

**Do NOT use this skill to:**
- Make OpenSpec design decisions (delegate to `openspec-propose`).
- Decide task ordering or implementation strategy (delegate to `openspec-apply-change`).
- Decide archive readiness (delegate to `openspec-archive-change`).
- Cut a release, tag, or publish — use `release-cut` / `release-tag`.

## Inputs

| Input | Format | Example |
|-------|--------|---------|
| `<slug>` | kebab-case, must match `^[a-z0-9][a-z0-9-]*$` (CONTRIBUTING.md §Branching) | `add-spanish-pack` |
| `<intent>` | one-line natural-language description | `"Add a Spanish vocabulary pack with audio prompts"` |

If either is missing, ask the user once and stop. Do not invent a slug from the intent — confirm with the user.

## Steps

Execute strictly in order. Each phase delegates to a sub-skill; do not inline its logic.

1. **Propose** — delegate to `openspec-propose`.
   - Invoke the `openspec-propose` skill, passing `<slug>` and `<intent>` as the change description.
   - That skill creates `openspec/changes/<slug>/{proposal,design,tasks}.md`.
   - Do not edit those artifacts here. If clarification is needed, let `openspec-propose` ask.

2. **Branch** — create the feature branch off the latest `main`.
   ```bash
   git fetch origin
   git checkout main && git pull --ff-only
   git checkout -b feature/<slug>
   ```
   The branch name **MUST** match `^feature/[a-z0-9][a-z0-9-]*$` per CONTRIBUTING.md §Branching. If it does not, STOP and ask the user for a valid slug.

3. **Apply** — delegate to `openspec-apply-change`.
   - Invoke the `openspec-apply-change` skill with `<slug>`.
   - That skill iterates over `openspec/changes/<slug>/tasks.md` and drives implementation.
   - Commits made during this phase MUST follow Conventional Commits 1.0 (e.g. `feat(<scope>): ...`, `fix(<scope>): ...`, `test(<scope>): ...`). `openspec-apply-change` is responsible for producing them; do not rewrite its commit messages here.

4. **Verify** — run the project's verification gates. Do not skip on green-looking output; require explicit success from each.
   ```bash
   pytest
   ruff check .
   pyright
   ```
   If any fails, STOP. Hand control back to `openspec-apply-change` (or the user) to fix; do not paper over failures.

5. **Push & open PR**
   ```bash
   git push -u origin feature/<slug>
   ```
   Open the PR with title and body derived from `openspec/changes/<slug>/proposal.md` (summary section verbatim). Use a HEREDOC to preserve formatting:
   ```bash
   gh pr create --base main --head feature/<slug> --title "feat(<slug>): <one-line summary from proposal>" --body "$(cat <<'EOF'
   ## Summary

   <paste the Summary section of openspec/changes/<slug>/proposal.md>

   ## OpenSpec change
   `openspec/changes/<slug>/`

   ## Verification
   - [x] `pytest`
   - [x] `ruff check .`
   - [x] `pyright`
   EOF
   )"
   ```
   Report the PR URL to the user.

6. **Wait for merge.** Do not poll, do not merge yourself. Stop until the user confirms the PR has merged to `main`.

7. **Archive** — delegate to `openspec-archive-change`.
   - After the user confirms the PR merged, invoke the `openspec-archive-change` skill with `<slug>`.
   - That skill moves `openspec/changes/<slug>/` to `openspec/archive/` and updates any indices. Do not move files by hand here.

## Output Format

Report exactly:

```
Feature flow complete for <slug>.
PR: <PR URL>
Archived: openspec/archive/<slug>/
```

If you stopped before merge (step 6), instead report:

```
Feature PR opened for <slug>: <PR URL>
Next: after merge to main, re-invoke /feature <slug> or ask me to archive.
```

## Quick Reference

| Step | Delegates to / Action | Output |
|------|----------------------|--------|
| 1 | `openspec-propose` skill | `openspec/changes/<slug>/{proposal,design,tasks}.md` |
| 2 | `git checkout -b feature/<slug>` | feature branch on local |
| 3 | `openspec-apply-change` skill | commits implementing tasks |
| 4 | `pytest` && `ruff check .` && `pyright` | all green |
| 5 | `git push` + `gh pr create` | PR URL |
| 6 | **STOP** — await human merge | — |
| 7 | `openspec-archive-change` skill | archived change |

## Red Flags — STOP and Reassess

- Slug does not match `^[a-z0-9][a-z0-9-]*$` → ask user for a valid slug; do not auto-sanitize.
- Already on a non-`main` branch with uncommitted work → STOP; do not stash silently.
- `openspec/changes/<slug>/` already exists before step 1 → ask user whether to resume or pick a new slug; do not overwrite.
- Verification (step 4) fails → STOP; do not push or open a PR with red verification.
- Tempted to edit `proposal.md` / `tasks.md` outside of `openspec-propose` → don't. Re-invoke the propose skill instead.
- Tempted to write commit messages directly instead of letting `openspec-apply-change` produce them → don't. The apply skill owns commit content and Conventional Commits formatting.
- User asks you to also tag or publish → refuse and direct them to `/release-cut` then `/release-tag`.

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| Inlining proposal/design content instead of calling `openspec-propose` | Always delegate; this skill never authors OpenSpec artifacts. |
| Branch named `feat/...` or `feature_<slug>` | Use `feature/<slug>` exactly; the repo enforces this regex. |
| Skipping `git pull --ff-only` on `main` before branching | Stale base → painful rebases. Always sync first. |
| Running `pytest` only and skipping `ruff` / `pyright` | All three are required gates; partial verification is no verification. |
| Merging the PR yourself or via `gh pr merge` | Out of scope. Human reviewer merges. |
| Archiving before merge | `openspec-archive-change` is post-merge only. Wait for user confirmation. |
| Re-running `openspec-propose` after edits start | Treat the proposal as frozen once step 3 begins; iterate via new changes if needed. |
