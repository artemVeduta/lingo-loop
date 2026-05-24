# Contributing

Thanks for your interest in contributing.

## Project status

Solo-maintained, pre-1.0. Issue triage and PR review are best-effort and may
take up to **14 days**. Please be patient and keep contributions focused.

## Dev setup

Requires Python 3.12+ and [uv](https://github.com/astral-sh/uv).

```bash
uv venv
uv pip install -e ".[dev]"

# Verification commands run on every PR by CI:
pytest
ruff check
pyright
```

## OpenSpec workflow

Non-trivial changes (new features, breaking changes, architecture shifts) go
through an OpenSpec proposal before implementation. Proposals live under
`openspec/changes/<change-name>/` and contain `proposal.md`, `design.md`,
`tasks.md`, and any spec deltas.

Use the `openspec-propose` (or `/opsx:propose`) skill to scaffold a new
change. Trivial fixes (typos, one-line bugs, doc tweaks) can go straight to a
PR without a proposal.

## Feature flow

For non-trivial work, the canonical entry point is the `/feature` skill:

```
/feature <slug> "<intent>"
```

This thin orchestrator walks the change from intent to merged PR by
delegating to existing skills: `openspec-propose` to draft the proposal,
`openspec-apply-change` to work through tasks, then PR creation and
`openspec-archive-change` on merge. The skill itself reimplements none of
that judgment — it just sequences the phases around a `feature/<slug>`
branch and a verify step (`pytest`, `ruff check`, `pyright`).

See [`.claude/skills/README.md`](.claude/skills/README.md) for the full
list of project-local skills (feature flow, release lifecycle, hotfix).

## Branching model

Trunk-based. `main` is the single long-lived branch. All work lands on `main`
through short-lived (under one week) feature branches and **squash merges**.
There are no `develop`, `release/*`, or `hotfix/*` branches.

Branch names MUST match `^(feature|fix|docs|chore|refactor|test)/[a-z0-9][a-z0-9-]*$`.
Examples:

- `feature/add-spanish-pack`
- `fix/doctor-exit-code`
- `docs/install-codex`
- `chore/bump-pyright`
- `refactor/profile-loader`
- `test/cover-reading-flow`

Cut branches from the latest `main`; rebase rather than merge to stay current.

## Commit messages

Follow [Conventional Commits 1.0](https://www.conventionalcommits.org/en/v1.0.0/).
Subject format:

```
<type>(<optional-scope>)<optional !>: <subject>
```

Allowed types: `feat`, `fix`, `docs`, `chore`, `refactor`, `test`, `build`,
`ci`, `perf`, `style`, `revert`.

Rules:

- Subject **≤ 72 characters**, imperative mood, no trailing period.
- Scope is lowercase, hyphenated (e.g. `feat(cli): ...`, `fix(hermes): ...`).
- Breaking changes are marked either with `!` after the type/scope
  (`feat(api)!: drop --legacy flag`) **or** with a `BREAKING CHANGE:` footer
  in the commit body.
- Body explains **why**, not what. Wrap at 100 columns.

Every commit must also carry a DCO sign-off trailer (see below).

## DCO sign-off

This project requires all commits to be signed off under the
[Developer Certificate of Origin](https://developercertificate.org/) (DCO).
By signing off, you certify that you wrote the patch or otherwise have the
right to submit it under the project's license.

Sign off automatically with the `-s` flag:

```bash
git commit -s -m "feat(cli): add --json flag to doctor"
```

This appends a trailer:

```
Signed-off-by: Your Name <your.email@example.com>
```

PRs with unsigned commits will be asked to amend (rebase and re-sign). A
programmatic DCO bot check will be enabled in a later change; for now the
requirement is enforced socially during review.

## PR checklist

Before requesting review, confirm:

- [ ] `pytest` passes locally.
- [ ] `ruff check` is clean.
- [ ] `pyright` is clean.
- [ ] Non-trivial changes have an OpenSpec proposal under
      `openspec/changes/`.
- [ ] README and `docs/` updated where user-visible behavior changed.
- [ ] `CHANGELOG.md` `[Unreleased]` section updated with a one-line entry
      under `Added` / `Changed` / `Fixed` / `Removed`.
- [ ] All commits are signed off (`git commit -s`).

## Code of Conduct

This project follows the [Contributor Covenant v2.1](CODE_OF_CONDUCT.md).
By participating you agree to abide by its terms. Report violations to
`veduta.artem20@gmail.com`.
