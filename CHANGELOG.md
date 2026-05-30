# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog 1.1.0](https://keepachangelog.com/en/1.1.0/)
and this project adheres to [Semantic Versioning 2.0.0](https://semver.org/spec/v2.0.0.html).

While the project is on `0.x`, minor releases MAY contain breaking changes
(per SemVer §4). Breaking changes are always called out in the relevant
release section.

## [Unreleased]

### Added

- `tutor doctor` JSON now carries an aggregate `status` field (`ok`/`fail`);
  `n/a` checks do not count as failures.

### Changed

- `tutor doctor` resolves the plugin `manifest` check via the bundled-assets
  resolver, so it is honest on wheel/PyPI installs.

### Fixed

- `tutor doctor` no longer reports spurious `fail` for `setup_skill`,
  `vocab_skill`, `writing_skill`, `progress_skill`, `judge_agent`, and `cli` on
  non-editable (wheel/PyPI) installs. These source-only payloads are neither
  bundled nor installed (install contract = manifest only) and are now reported
  `n/a` outside an editable checkout.

### Removed

## [0.1.0] - 2026-05-29

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
- **Interactive provider installer** now models each host as a bundled
  directory tree: every declared file is materialized, verified, and
  drift-checked per file; missing or content-divergent siblings are
  reported as `needs-repair` and rewritten individually. A missing host
  config root or a missing bundled asset in the wheel now yields
  `BLOCKED` with a kind-tagged repair hint (CLI / config root / packaging
  defect) linking to `docs/install/<host>.md`.
- **Distribution metadata** now requires `pyproject.toml [project].name`
  to be exactly `lingo-loop` and `[tool.hatch.build.targets.wheel.force-include]`
  to enumerate every file declared by every provider installer (no
  reliance on globs picking up bundled assets implicitly).
- **Tagged releases** workflow provisions Python 3.12 via an explicit
  `actions/setup-python@v5` step before every `uv` invocation, with
  `UV_PYTHON: "3.12"` on each affected job — the prior `python-version`
  input to `astral-sh/setup-uv@v3` was silently ignored.
- **Per-host install documentation** is now gated by a docs-correctness
  test (`tests/docs/test_install_docs.py`) that asserts every `tutor`
  CLI example parses against the shipped CLI, every relative link
  resolves, every documented config-root path matches the installer's
  reported path on macOS, and every `language-tutor` mention is in
  contrast context with `lingo-loop`.

### Fixed

- `hermes-profile/distribution.yaml` `source_url` corrected from the upstream
  Hermes URL to this repository's URL.
