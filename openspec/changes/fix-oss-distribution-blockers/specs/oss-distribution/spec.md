## MODIFIED Requirements

### Requirement: CLI MUST provide an interactive provider installer

The installed tutor CLI MUST provide `tutor init` as the primary first-run setup command. The command MUST detect supported providers (Claude, Codex, Hermes, OpenClaw), let the user choose one or more providers to install through a keyboard-driven terminal selector, apply provider-specific plugin/profile wiring, verify the result, and print actionable repair guidance for blocked providers. Interactive setup MUST NOT require typing provider ids, comma-separated lists, or `y`/`n` confirmation. The installer MUST be idempotent and MUST NOT write learner-owned profile/history/session/checkpoint data or host secrets.

Each provider MUST be modeled as a bundled directory tree. The provider's installer MUST declare every file it owns under that tree, MUST materialize every declared file on apply, MUST verify every declared file on detect, and MUST report `NEEDS_REPAIR` if any declared file is missing or content-divergent from the bundled source. The installer MUST NOT report `INSTALLED` based on a single representative file. Drift output MUST name each divergent file path so the learner can audit what will be rewritten.

A provider MUST report `BLOCKED` when its host CLI is not on PATH, when its conventional config root does not exist on disk, or when bundled assets for the host are missing from the wheel. In every BLOCKED case, the repair hint MUST name the missing prerequisite by kind (CLI, config root, or bundled asset) and MUST link to `docs/install/<host>.md`.

#### Scenario: User installs package then chooses provider

- **GIVEN** the `lingo-loop` package is installed and the `tutor` console command is available
- **WHEN** a learner runs `tutor init` in an interactive terminal
- **THEN** the CLI lists Claude, Codex, Hermes, and OpenClaw with detected status
- **AND** the learner can choose one or more providers to install with arrow keys, Space, and Enter
- **AND** the learner does not need to type provider names, comma-separated provider lists, or `y`/`n`
- **AND** the CLI shows an install plan before writing files
- **AND** the apply/abort step uses a keyboard menu before any write
- **AND** selected providers are installed or repaired through provider-specific installer modules
- **AND** the final summary shows verification status and the next host-specific reload/start command

#### Scenario: Non-interactive install is explicit

- **WHEN** a learner or CI job runs `tutor init --provider claude --provider codex --yes --json`
- **THEN** the CLI does not prompt
- **AND** only the selected providers are planned and applied
- **AND** the JSON result includes each provider id, status, actions, verification outcome, written paths, and repair hint when applicable
- **AND** if stdin is not a TTY and `--yes` or `--provider` is missing, the command fails before any write
- **AND** any `--json` invocation that would write files fails before any write unless `--yes` is supplied

#### Scenario: Dry run performs no writes

- **WHEN** a learner runs `tutor init --dry-run --json`
- **THEN** the CLI detects providers and returns the planned actions
- **AND** no files are created, modified, or deleted
- **AND** the result marks every action as planned rather than applied

#### Scenario: Installer is idempotent and data-safe

- **GIVEN** a provider was already installed by `tutor init` and every declared file in its bundled tree is present and content-matching
- **WHEN** the learner runs the same provider install again
- **THEN** the command reports `installed` without duplicating or rewriting any file
- **AND** learner profile YAML, SQLite history, sessions, checkpoints, memories, logs, local overrides, and secrets remain unchanged

#### Scenario: Missing sibling file in bundled tree triggers per-file repair

- **GIVEN** the OpenClaw managed directory contains `package.json` matching the bundled source but is missing `openclaw.plugin.json`
- **WHEN** the learner runs `tutor init --provider openclaw --yes --json`
- **THEN** the provider status is `needs-repair`
- **AND** the repair plan contains exactly one `WRITE_FILE` action whose target_path is the missing `openclaw.plugin.json`
- **AND** the verification step lists every file in the bundled tree and asserts each is present and content-matching after apply

#### Scenario: Content drift in one file of a multi-file tree triggers repair on that file only

- **GIVEN** the Codex managed directory contains every declared file but one file's content differs from the bundled source
- **WHEN** the learner runs `tutor init --provider codex --yes --json`
- **THEN** the provider status is `needs-repair`
- **AND** the repair plan rewrites only the divergent file
- **AND** files that match the bundled content are not rewritten

#### Scenario: Missing host CLI blocks with repair guidance

- **GIVEN** a selected provider's host CLI is not on PATH
- **WHEN** the learner runs `tutor init --provider <host> --yes`
- **THEN** the provider result is `blocked`
- **AND** the CLI does not attempt a partial install for that provider
- **AND** the repair hint names the missing CLI by name and links to `docs/install/<host>.md`

#### Scenario: Missing host config root blocks with repair guidance

- **GIVEN** a selected provider's host CLI is on PATH but the conventional config root for that host does not exist on disk
- **WHEN** the learner runs `tutor init --provider <host> --yes`
- **THEN** the provider result is `blocked`
- **AND** the CLI does not create the config root and does not attempt a partial install
- **AND** the repair hint names the missing config root path, instructs the learner to run the host CLI once to initialize it, and links to `docs/install/<host>.md`

#### Scenario: Missing bundled asset in the wheel blocks with repair guidance

- **GIVEN** the installed `lingo-loop` wheel is missing one or more files declared by a provider's bundled tree
- **WHEN** the learner runs `tutor init --provider <host> --yes`
- **THEN** the provider result is `blocked`
- **AND** the repair hint names the missing bundled asset path and identifies it as a packaging defect
- **AND** the CLI does not attempt a partial install

### Requirement: Distribution metadata MUST point at the correct project location

`pyproject.toml` and `hermes-profile/distribution.yaml` MUST declare the canonical GitHub URL for this project (`https://github.com/artemVeduta/lingo-loop`), and `pyproject.toml` MUST declare a project name, classifiers, keywords, URLs, and Python version that match the repository's actual support matrix and the PyPI Trusted Publisher binding.

#### Scenario: Distribution name matches the PyPI Trusted Publisher binding

- **WHEN** a downstream packager reads `pyproject.toml`
- **THEN** `[project].name` is exactly `lingo-loop`
- **AND** the value matches the project name registered with the PyPI Trusted Publisher for this repository

#### Scenario: Distribution metadata is consistent and correct

- **WHEN** a downstream packager reads `pyproject.toml`
- **THEN** the `[project.urls]` block exposes `Homepage`, `Source`, `Issues`, and `Changelog` keys pointing at `https://github.com/artemVeduta/lingo-loop` or its sub-paths
- **AND** the classifiers include `License :: OSI Approved :: MIT License`, `Programming Language :: Python :: 3.12`, `Intended Audience :: End Users/Desktop`, `Topic :: Education`, and `Topic :: Education :: Computer Aided Instruction (CAI)`
- **AND** `requires-python` is `>=3.12`

#### Scenario: Wheel bundles every file declared by every provider installer

- **WHEN** a maintainer runs `uv build` on a clean checkout and inspects the resulting wheel
- **THEN** every file path declared in any provider's bundled-tree manifest is present inside the wheel under `language_tutor/_assets/<host-package>/<relative-path>`
- **AND** the `[tool.hatch.build.targets.wheel.force-include]` block in `pyproject.toml` enumerates every such file (no provider relies on files that are not force-included)

#### Scenario: Hermes profile points at this repository

- **WHEN** a Hermes user inspects `hermes-profile/distribution.yaml`
- **THEN** `source_url` is `https://github.com/artemVeduta/lingo-loop`
- **AND** `license` is `MIT`

### Requirement: Tagged releases MUST publish to PyPI via OIDC Trusted Publishing

The repository MUST contain `.github/workflows/workflow.yml` that triggers on `v*.*.*` tag pushes and on `workflow_dispatch`. The workflow MUST build sdist + wheel via `uv build`, verify the tag matches `pyproject.toml` `[project].version`, publish to PyPI via Trusted Publishing (OIDC, `id-token: write`, no API token stored as a repository secret), attach sigstore/SLSA attestations, and create a matching GitHub Release with the artifacts attached. The workflow filename MUST remain `workflow.yml` (bound to the PyPI pending-publisher registration for `lingo-loop`). Every job that invokes `uv` MUST first provision Python 3.12 via a step whose `python-version` input is actually honored by the action it is passed to.

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

#### Scenario: Python pin is honored by the provisioning step

- **WHEN** a maintainer inspects every job in `.github/workflows/workflow.yml` that invokes `uv`
- **THEN** the job contains an `actions/setup-python@v5` step (or an equivalent action that accepts a `python-version` input) declaring `python-version: "3.12"` before any `uv` invocation
- **AND** no step passes a `python-version` input to an action that does not accept that input
- **AND** the job sets `UV_PYTHON: "3.12"` so `uv build` resolves the same interpreter

### Requirement: Per-host install documentation MUST exist for every supported host

For each supported host (Claude, Codex, Hermes, OpenClaw), the repository MUST publish a dedicated install doc at `docs/install/<host>.md` following a consistent template: prerequisites, `tutor` CLI install, host-specific wiring, verification, troubleshooting, and uninstall. Every CLI example printed in these docs and in `README.md` MUST parse against the shipped CLI, every relative link MUST resolve to a file in the repository, every documented filesystem path MUST match what the installer actually writes, and every reference to the distribution name MUST use `lingo-loop` (the Python module name `language_tutor` MAY be referenced only when explicitly contrasting it with the distribution name).

#### Scenario: Install docs exist with consistent structure

- **WHEN** a maintainer lists `docs/install/`
- **THEN** the directory contains `claude.md`, `codex.md`, `hermes.md`, and `openclaw.md`
- **AND** each file contains the sections: Prerequisites, Step 0 (CLI install), host wiring, Verify, Troubleshooting, Uninstall
- **AND** each file carries a `Last verified: YYYY-MM-DD` header so staleness is detectable

#### Scenario: Documented CLI examples parse against the shipped CLI

- **WHEN** the docs-correctness test extracts every `tutor ...` invocation from `docs/install/*.md` and `README.md`
- **THEN** invoking `<command> --help` for each example succeeds (exit 0)
- **AND** every flag named in the example is present in the `--help` output

#### Scenario: Documented relative links resolve

- **WHEN** the docs-correctness test extracts every relative link target from `docs/install/*.md` and `README.md`
- **THEN** every target resolves to a file that exists in the repository

#### Scenario: Documented config-root paths match installer behavior

- **WHEN** the docs-correctness test compares the `config_root` path documented in each `docs/install/<host>.md` against the value returned by the corresponding provider installer's `config_root()` method on macOS
- **THEN** the documented path equals the installer-reported path (modulo `$HOME` normalization)

#### Scenario: Distribution-name references use `lingo-loop`

- **WHEN** the docs-correctness test greps `docs/install/*.md` and `README.md` for `language-tutor`
- **THEN** any remaining occurrence is part of a sentence that explicitly contrasts it with `lingo-loop` (e.g. clarifying that the Python module is still `language_tutor`)
- **AND** no install or uninstall command targets the `language-tutor` distribution

#### Scenario: Placeholder assets are tracked

- **WHEN** an install doc ships with a missing screenshot or asciinema cast at merge time
- **THEN** the placeholder is marked with `<!-- TODO(oss-baseline-assets): ... -->`
- **AND** a corresponding entry exists in `docs/internal/launch-checklist.md` or an equivalent tracked location, blocking the public announcement (not the merge)
