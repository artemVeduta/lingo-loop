# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog 1.1.0](https://keepachangelog.com/en/1.1.0/)
and this project adheres to [Semantic Versioning 2.0.0](https://semver.org/spec/v2.0.0.html).

While the project is on `0.x`, minor releases MAY contain breaking changes
(per SemVer §4). Breaking changes are always called out in the relevant
release section.

## [Unreleased]

### Added

- MIT `LICENSE` file at repo root.
- `CONTRIBUTING.md`, `SECURITY.md`, `CODE_OF_CONDUCT.md`, `RELEASING.md`.
- Per-host install documentation under `docs/install/`.
- `.github/` scaffold: CI workflow, issue and PR templates, dependabot config.

### Changed

- **Renamed:** repository and PyPI distribution name from `language-tutor`
  to `lingo-loop`. Scope is **name-only** in this release — the Python
  module remains `language_tutor` and the CLI command remains `tutor`. A
  follow-up release will complete the code-level rename. GitHub auto-redirects
  the old repo URL (HTTP 301), so existing clones continue to work.
- README restructured for end-user language learners (was contributor-focused).
- License made explicit and consistent: MIT across `LICENSE`,
  `pyproject.toml`, plugin manifests (already MIT), and
  `hermes-profile/distribution.yaml` (was `see repository`).

### Fixed

- `hermes-profile/distribution.yaml` `source_url` corrected from the upstream
  Hermes URL to this repository's URL.
