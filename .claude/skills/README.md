# Project-local Claude Code skills

This directory ships repository-scoped skills that automate the release
lifecycle and feature workflow. Each skill is invocable via both a slash
command (`/<name>`) and a natural-language phrase match described in its
frontmatter. Skills delegate deterministic mechanics to shared shell helpers
under [`scripts/`](../../scripts/) and stop at well-defined human-review
boundaries — they never push tags, merge PRs, or publish on their own.

| Skill | Slash trigger | Purpose | Stops at |
|---|---|---|---|
| [`pre-release-checks`](pre-release-checks/SKILL.md) | `/pre-release-checks` | Read-only PASS/FAIL audit of repo state, build, tests, lint, types, coverage before tagging. Calls [`scripts/build-check.sh`](../../scripts/build-check.sh). | PASS/FAIL table; blockers must clear before `release-cut`. |
| [`release-cut`](release-cut/SKILL.md) | `/release-cut X.Y.Z` | Branch `chore/release-X.Y.Z`, promote CHANGELOG, bump `pyproject.toml`, sign-off commit, push, open PR. Calls [`scripts/changelog-promote.sh`](../../scripts/changelog-promote.sh). | PR URL; human reviews + merges. |
| [`release-tag`](release-tag/SKILL.md) | `/release-tag X.Y.Z` | After release PR merges to `main`, sanity-check the tag with [`scripts/version-guard.sh`](../../scripts/version-guard.sh) and push the annotated tag. Tag push triggers `.github/workflows/workflow.yml`. | `git push origin vX.Y.Z`; workflow owns publish. |
| [`hotfix`](hotfix/SKILL.md) | `/hotfix <bug-ref>` | Branch off the latest production tag (excluding prereleases), pause for fix, sign-off commit, push, PR. On merge, hand off to `release-cut` with a patch bump. | Hotfix PR URL. |
| [`feature-flow`](feature-flow/SKILL.md) | `/feature <slug> "<intent>"` | Thin orchestrator: `openspec-propose` → branch → `openspec-apply-change` → verify → PR → `openspec-archive-change`. Defers all OpenSpec judgment to those skills. | Feature PR URL + archive confirmation. |

See [`RELEASING.md`](../../RELEASING.md) for the full automated release flow
and [`CONTRIBUTING.md`](../../CONTRIBUTING.md) §Feature flow for the
feature-development entry point.
