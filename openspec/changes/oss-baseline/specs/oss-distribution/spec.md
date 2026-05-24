# Capability: oss-distribution

Establishes the artifacts and conventions that make this repository a legitimate, discoverable, and contributor-ready open-source project.

## ADDED Requirements

### Requirement: Repository MUST declare a permissive open-source license

The repository MUST contain a single, canonical `LICENSE` file at the repo root whose contents and SPDX identifier match the license advertised by every shipped distribution artifact (plugin manifests, profile descriptors, `pyproject.toml`). The license MUST be MIT for v0.1.

#### Scenario: License file present and canonical

- **WHEN** a visitor opens the repository on GitHub
- **THEN** GitHub's "License" sidebar identifies the license as `MIT License`
- **AND** the `LICENSE` file at repo root contains verbatim MIT text with `Copyright (c) 2026 Artem Veduta`

#### Scenario: License declarations agree across all artifacts

- **WHEN** a maintainer runs `grep -lE '"license"|license:|license *=' LICENSE pyproject.toml .claude-plugin/plugin.json .codex-plugin/plugin.json openclaw-plugin/package.json hermes-profile/distribution.yaml`
- **THEN** every matched file's license declaration resolves to `MIT`
- **AND** no file declares `see repository`, `proprietary`, or any non-MIT identifier

### Requirement: Repository MUST provide contributor infrastructure

The repository MUST include `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, `SECURITY.md`, and `CHANGELOG.md` at the repo root, plus a `.github/` scaffold with CI workflow, issue templates, PR template, and dependabot config.

#### Scenario: Required contributor files exist

- **WHEN** a new contributor clones the repository
- **THEN** the files `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, `SECURITY.md`, and `CHANGELOG.md` exist at the repo root
- **AND** `CONTRIBUTING.md` documents the dev setup, OpenSpec proposal flow, branch naming, commit conventions, and DCO sign-off requirement

#### Scenario: GitHub scaffolding wired up

- **WHEN** a contributor opens the repository's `New issue` flow on GitHub
- **THEN** they see structured templates for `bug_report` and `feature_request`
- **AND** blank issues are disabled
- **AND** a contact link routes general questions to GitHub Discussions

### Requirement: README MUST be learner-facing

The repository's `README.md` MUST address end-user language learners as the primary audience. It MUST open with a one-line tagline (not an install command), expose a copy-paste quick start for the most popular host within the first scroll, and contain no references to internal tooling (`rtk`, spec numbers, internal subagent names).

#### Scenario: README opens with end-user framing

- **WHEN** a first-time visitor scrolls the rendered README on GitHub
- **THEN** the first non-badge content is a one-line tagline describing what the tool does for the learner
- **AND** a "Quick start" section provides a complete Claude install path in six or fewer copy-paste commands
- **AND** `grep -E '(\brtk\b|Spec [0-9])' README.md` returns no matches

#### Scenario: Other hosts discoverable

- **WHEN** a visitor uses a host other than Claude
- **THEN** the README links to per-host install docs at `docs/install/<host>.md` for Codex, Hermes, and OpenClaw

### Requirement: Per-host install documentation MUST exist for every supported host

For each supported host (Claude, Codex, Hermes, OpenClaw), the repository MUST publish a dedicated install doc at `docs/install/<host>.md` following a consistent template: prerequisites, `tutor` CLI install, host-specific wiring, verification, troubleshooting, and uninstall.

#### Scenario: Install docs exist with consistent structure

- **WHEN** a maintainer lists `docs/install/`
- **THEN** the directory contains `claude.md`, `codex.md`, `hermes.md`, and `openclaw.md`
- **AND** each file contains the sections: Prerequisites, Step 0 (CLI install), host wiring, Verify, Troubleshooting, Uninstall
- **AND** each file carries a `Last verified: YYYY-MM-DD` header so staleness is detectable

#### Scenario: Placeholder assets are tracked

- **WHEN** an install doc ships with a missing screenshot or asciinema cast at merge time
- **THEN** the placeholder is marked with `<!-- TODO(oss-baseline-assets): ... -->`
- **AND** a corresponding entry exists in `docs/internal/launch-checklist.md` or an equivalent tracked location, blocking the public announcement (not the merge)

### Requirement: Continuous integration MUST run on every pull request

The repository MUST execute lint (`ruff`), type check (`pyright`), and tests (`pytest` with the existing `--cov-fail-under` gate) on every push to `main` and every pull request targeting `main`.

#### Scenario: CI runs and gates merges

- **WHEN** a contributor opens a pull request against `main`
- **THEN** the `ci` workflow runs `ruff check`, `pyright`, and `pytest` automatically
- **AND** branch protection on `main` requires the `ci` check to pass before merge
- **AND** coverage stays at or above the gate configured in `pyproject.toml`

### Requirement: Distribution metadata MUST point at the correct project location

`pyproject.toml` and `hermes-profile/distribution.yaml` MUST declare the canonical GitHub URL for this project (`https://github.com/artemVeduta/lingo-loop`), and `pyproject.toml` MUST declare classifiers, keywords, URLs, and Python version that match the repository's actual support matrix.

#### Scenario: Distribution metadata is consistent and correct

- **WHEN** a downstream packager reads `pyproject.toml`
- **THEN** the `[project.urls]` block exposes `Homepage`, `Source`, `Issues`, and `Changelog` keys pointing at `https://github.com/artemVeduta/lingo-loop` or its sub-paths
- **AND** the classifiers include `License :: OSI Approved :: MIT License`, `Programming Language :: Python :: 3.12`, `Intended Audience :: End Users/Desktop`, `Topic :: Education`, and `Topic :: Education :: Computer Aided Instruction (CAI)`
- **AND** `requires-python` is `>=3.12`

#### Scenario: Hermes profile points at this repository

- **WHEN** a Hermes user inspects `hermes-profile/distribution.yaml`
- **THEN** `source_url` is `https://github.com/artemVeduta/lingo-loop`
- **AND** `license` is `MIT`

### Requirement: Repository MUST follow a trunk-based branching model

The repository MUST use a trunk-based workflow with `main` as the single long-lived branch. All work MUST land on `main` through short-lived branches (typically under one week) named with a typed prefix and merged via squash-merge.

#### Scenario: Branch naming follows the prescribed taxonomy

- **WHEN** a contributor creates a working branch
- **THEN** the branch name matches `^(feature|fix|docs|chore|refactor|test)/[a-z0-9][a-z0-9-]*$`
- **AND** the branch is cut from the latest `main`
- **AND** the branch is merged back to `main` (no long-lived integration branches such as `develop` or `release/*` exist)

#### Scenario: Branching model is documented for contributors

- **WHEN** a contributor reads `CONTRIBUTING.md`
- **THEN** it documents the trunk-based model, the allowed branch prefixes, the requirement that branches stay short-lived, and the squash-merge policy

### Requirement: Commits MUST follow Conventional Commits with DCO sign-off

Every commit landed on `main` MUST follow the Conventional Commits 1.0 specification (`type(scope): subject`) using an allowed type from a documented list, and MUST carry a `Signed-off-by:` trailer that asserts the Developer Certificate of Origin.

#### Scenario: Commit subject conforms to Conventional Commits

- **WHEN** a maintainer inspects any commit on `main`
- **THEN** the subject matches `^(feat|fix|docs|chore|refactor|test|build|ci|perf|style|revert)(\([a-z0-9-]+\))?!?: .+`
- **AND** the subject line is 72 characters or fewer
- **AND** breaking changes are marked with `!` after the type/scope or a `BREAKING CHANGE:` footer

#### Scenario: DCO sign-off is present and documented

- **WHEN** a maintainer runs `git log --format=%B main` and greps for `Signed-off-by:`
- **THEN** every non-merge commit on `main` from this change onward contains a `Signed-off-by: Name <email>` trailer
- **AND** `CONTRIBUTING.md` documents the `git commit -s` requirement and links to https://developercertificate.org/

### Requirement: `main` MUST be protected with PR-only, CI-gated, linear history

The `main` branch MUST be protected so that direct pushes are forbidden, all changes flow through pull requests, the `ci` status check must pass before merge, and history MUST stay linear (squash or rebase merges only — no merge commits).

#### Scenario: Branch protection enforces the workflow

- **WHEN** a maintainer reads the branch-protection settings for `main` via `gh api repos/artemVeduta/lingo-loop/branches/main/protection`
- **THEN** `required_pull_request_reviews` is enabled (review count MAY be zero for solo maintainer, but PRs are required)
- **AND** `required_status_checks.contexts` includes `ci`
- **AND** `required_linear_history` is `true`
- **AND** `allow_force_pushes` is `false`
- **AND** `allow_deletions` is `false`

### Requirement: Repository MUST publish a release procedure and follow SemVer

The repository MUST publish a `RELEASING.md` runbook at the repo root that describes the end-to-end release procedure, and all published versions MUST follow Semantic Versioning 2.0 with `vMAJOR.MINOR.PATCH` git tags. The primary release path MUST be the tag-driven automated publish workflow defined in the "PyPI publish automation" requirement below; the runbook MUST also document a manual break-glass path for use when the automated workflow is unavailable.

#### Scenario: `RELEASING.md` documents the full procedure

- **WHEN** a maintainer opens `RELEASING.md`
- **THEN** it documents, in order: version-bump policy (SemVer), CHANGELOG promotion ritual (rename `[Unreleased]` → `[X.Y.Z] - YYYY-MM-DD`, add new empty `[Unreleased]` on top), tag format (`vX.Y.Z`, annotated, signed when a signing key is available), the `gh release create vX.Y.Z --notes-from-tag` command, and post-release verification steps
- **AND** it names who is authorized to cut releases (the maintainer listed in `pyproject.toml` `authors`)

#### Scenario: Tags conform to SemVer

- **WHEN** a maintainer lists tags via `git tag -l 'v*'`
- **THEN** every tag matches `^v(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)(-[0-9A-Za-z.-]+)?$`
- **AND** the first tag cut after this change merges is `v0.1.0`

#### Scenario: CHANGELOG is promoted before each tag

- **WHEN** a maintainer cuts release `X.Y.Z`
- **THEN** the commit being tagged contains a `CHANGELOG.md` whose top section reads `## [X.Y.Z] - YYYY-MM-DD`
- **AND** an empty `## [Unreleased]` section sits above it
- **AND** the tag is created on that commit, not before

### Requirement: Tagged releases MUST publish to PyPI via OIDC Trusted Publishing

The repository MUST contain `.github/workflows/workflow.yml` that triggers on `v*.*.*` tag pushes and on `workflow_dispatch`. The workflow MUST build sdist + wheel via `uv build`, verify the tag matches `pyproject.toml` `[project].version`, publish to PyPI via Trusted Publishing (OIDC, `id-token: write`, no API token stored as a repository secret), attach sigstore/SLSA attestations, and create a matching GitHub Release with the artifacts attached. The workflow filename MUST remain `workflow.yml` (bound to the PyPI pending-publisher registration for `lingo-loop`).

#### Scenario: Final tag publishes to production PyPI

- **WHEN** a maintainer pushes a tag matching `^v(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)$` (no pre-release suffix)
- **THEN** `.github/workflows/workflow.yml` runs
- **AND** the `build` job fails the workflow if the tag's version differs from `pyproject.toml` `[project].version`
- **AND** the `publish` job runs under GitHub Environment `pypi` with `id-token: write` permission
- **AND** `pypa/gh-action-pypi-publish@release/v1` is invoked with `attestations: true` (no `password:` or `username:` inputs supplied)
- **AND** a GitHub Release is created for the tag with the sdist and wheel attached and `prerelease: false`

#### Scenario: Pre-release tag publishes to TestPyPI

- **WHEN** a maintainer pushes a tag matching `^v[0-9]+\.[0-9]+\.[0-9]+-(rc|alpha|beta)\.[0-9]+$`
- **THEN** the `publish` job runs under GitHub Environment `testpypi`
- **AND** `pypa/gh-action-pypi-publish` is invoked with `repository-url: https://test.pypi.org/legacy/`
- **AND** the corresponding GitHub Release is marked `prerelease: true`
- **AND** no upload is made to pypi.org

#### Scenario: Workflow filename is bound to PyPI publisher config

- **WHEN** a maintainer inspects the workflow file path
- **THEN** the path is exactly `.github/workflows/workflow.yml`
- **AND** the file's header comment documents that the filename is bound to the PyPI Trusted Publisher entry for `lingo-loop` and MUST NOT be renamed without simultaneously updating PyPI publisher config

#### Scenario: No PyPI token stored as secret

- **WHEN** a maintainer lists repository secrets via `gh secret list`
- **THEN** no secret named `PYPI_API_TOKEN`, `PYPI_TOKEN`, or `TWINE_PASSWORD` exists
- **AND** the workflow file contains no `password:` or `username:` inputs to the PyPI publish action

### Requirement: Release lifecycle MUST be operable via project-local skills

The repository MUST ship five project-local skills under `.claude/skills/<name>/SKILL.md` that automate the release lifecycle: `pre-release-checks`, `release-cut`, `release-tag`, `hotfix`, and `feature-flow`. Each skill MUST be invocable via both a slash command and a description-based phrase match. Skills MUST call shared shell helpers in `scripts/` for deterministic mechanics rather than reimplementing them in markdown.

#### Scenario: All five release skills exist with required frontmatter

- **WHEN** a contributor lists `.claude/skills/`
- **THEN** the directories `pre-release-checks/`, `release-cut/`, `release-tag/`, `hotfix/`, and `feature-flow/` each contain a `SKILL.md`
- **AND** each `SKILL.md` declares `name`, `description`, and is invocable as `/<name>` via slash command
- **AND** each `description` includes a natural-language phrase suitable for auto-invoke matching

#### Scenario: Skills delegate mechanics to scripts/

- **WHEN** a maintainer inspects the skill files
- **THEN** `release-cut` invokes `scripts/changelog-promote.sh`
- **AND** `release-tag` invokes `scripts/version-guard.sh`
- **AND** `pre-release-checks` invokes `scripts/build-check.sh`
- **AND** the shell logic is not duplicated inline in the SKILL.md prose

#### Scenario: Skills enforce the runbook's stop boundaries

- **WHEN** a maintainer runs `/release-cut X.Y.Z`
- **THEN** the skill stops after pushing the release branch and opening the PR, and instructs the user to merge before running `/release-tag X.Y.Z`
- **AND** the skill does not push tags itself
- **AND** `/release-tag X.Y.Z` refuses to run unless the release PR for `X.Y.Z` has merged to `main`

#### Scenario: `feature-flow` orchestrates existing openspec skills without reimplementing them

- **WHEN** a contributor runs `/feature <slug> "<intent>"`
- **THEN** the skill invokes the `openspec-propose` skill, then enters an apply loop via `openspec-apply`, then archives via `openspec-archive` after the resulting PR merges
- **AND** the skill does not duplicate the proposal/apply/archive logic inline

### Requirement: CLI MUST provide an interactive provider installer

The installed tutor CLI MUST provide `tutor init` as the primary first-run setup command. The command MUST detect supported providers (Claude, Codex, Hermes, OpenClaw), let the user choose one or more providers to install, apply provider-specific plugin/profile wiring, verify the result, and print actionable repair guidance for blocked providers. The installer MUST be idempotent and MUST not write learner-owned profile/history/session/checkpoint data or host secrets.

#### Scenario: User installs package then chooses provider

- **GIVEN** the `lingo-loop` package is installed and the `tutor` console command is available
- **WHEN** a learner runs `tutor init` in an interactive terminal
- **THEN** the CLI lists Claude, Codex, Hermes, and OpenClaw with detected status
- **AND** the learner can choose one or more providers to install
- **AND** the CLI shows an install plan before writing files
- **AND** selected providers are installed or repaired through provider-specific installer modules
- **AND** the final summary shows verification status and the next host-specific reload/start command

#### Scenario: Non-interactive install is explicit

- **WHEN** a learner or CI job runs `tutor init --provider claude --provider codex --yes --json`
- **THEN** the CLI does not prompt
- **AND** only the selected providers are planned and applied
- **AND** the JSON result includes each provider id, status, actions, verification outcome, written paths, and repair hint when applicable
- **AND** if stdin is not a TTY and `--yes` or `--provider` is missing, the command fails before any write

#### Scenario: Dry run performs no writes

- **WHEN** a learner runs `tutor init --dry-run --json`
- **THEN** the CLI detects providers and returns the planned actions
- **AND** no files are created, modified, or deleted
- **AND** the result marks every action as planned rather than applied

#### Scenario: Installer is idempotent and data-safe

- **GIVEN** a provider was already installed by `tutor init`
- **WHEN** the learner runs the same provider install again
- **THEN** the command reports `installed` or `needs-repair` without duplicating files
- **AND** repair writes are limited to managed plugin/profile files for that provider
- **AND** learner profile YAML, SQLite history, sessions, checkpoints, memories, logs, local overrides, and secrets remain unchanged

#### Scenario: Missing host CLI blocks with repair guidance

- **GIVEN** a selected provider's host CLI or required config root is absent
- **WHEN** the learner runs `tutor init --provider <host> --yes`
- **THEN** the provider result is `blocked`
- **AND** the CLI does not attempt a partial install for that provider
- **AND** the repair hint names the missing prerequisite and links to `docs/install/<host>.md`
