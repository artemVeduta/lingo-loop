## Why

PR #11 (OSS distribution baseline) is CI-green but reviewers from four parallel sub-agent reviews (Averroes, Copernicus, Cicero, Dirac) blocked merge. The shipped installer reports success while host plugins are partially broken on disk, the release pipeline cannot publish because the distribution name mismatches the Trusted Publisher binding, the installer behaves opposite to its own spec when host config roots are missing, public install docs contain commands and links that fail, and the release workflow's Python pin is silently ignored. Without these fixes the baseline cannot be safely tagged, learners following the README will hit dead ends, and the first PyPI publish will fail.

## What Changes

- **BREAKING** Rename PyPI distribution from `language-tutor` to `lingo-loop` in `pyproject.toml` (`[project].name`) so tag-triggered publish matches the Trusted Publisher entry and `pypi.org/project/lingo-loop/` URLs in `.github/workflows/workflow.yml`. Python module name `language_tutor` and CLI `tutor` are unchanged (full module/CLI rename remains deferred to `rename-lingo-loop`).
- Replace single-file `bundled_path()` / `managed_path()` model in `installer/providers/base.py` with a bundled-tree model: a provider profile declares a bundled-asset source directory plus a managed destination directory and one or more files to materialize. Installer copies and verifies every declared file (openclaw needs `package.json` + `openclaw.plugin.json` + `tsconfig.json` + `src/**`; codex `.codex-plugin` needs `plugin.json` + adjacent assets; hermes needs profile YAML + sibling files). Drift detection compares the full tree, not one file. `tutor doctor` and `tutor init --json` report drift per file.
- Fix `BaseProviderInstaller.detect()` so a missing host config root yields `ProviderState.BLOCKED` (not `AVAILABLE`), matching the spec scenario "Missing host CLI blocks with repair guidance". Repair hint names the missing root and links to `docs/install/<host>.md`. Update existing installer tests that assert AVAILABLE in this state.
- Fix `.github/workflows/workflow.yml` Python provisioning: drop the ignored `python-version` input from `astral-sh/setup-uv@v3` and add an explicit `actions/setup-python@v5` step (or upgrade to `setup-uv@v4` with documented Python pinning), so the workflow honors Python 3.12 across `build`, `publish-pypi`, and `publish-testpypi` jobs.
- Fix public install docs under `docs/install/*.md` and `README.md`:
  - Replace any `uv tool install language-tutor` / `pip install language-tutor` with `lingo-loop`.
  - Repair broken relative links (`../troubleshooting.md` etc.) — either create the target or rewrite the link.
  - Correct macOS config-root paths (`~/.codex`, `~/.openclaw`, `~/.claude`, Hermes profile dir) so they match what the installer writes.
  - Verify every documented CLI example (`tutor init`, `tutor doctor`, `tutor init --provider <host> --yes --json`) against the shipped CLI; remove or fix any that no longer parse.

## Capabilities

### New Capabilities

(none)

### Modified Capabilities

- `oss-distribution`: tighten the **interactive provider installer** requirement to mandate full bundled-tree fidelity (every declared asset present and matching) and to make missing config root a BLOCKED state with repair guidance; tighten **distribution metadata MUST point at the correct project location** to require `pyproject.toml [project].name == "lingo-loop"`; tighten **tagged releases MUST publish to PyPI via OIDC Trusted Publishing** to require the workflow uses a Python provisioning step whose pin is actually honored; tighten **per-host install documentation MUST exist for every supported host** to require every CLI example and link in `docs/install/*.md` and `README.md` resolves against the shipped CLI and filesystem.

## Impact

- Code: `src/language_tutor/installer/providers/base.py`, `claude.py`, `codex.py`, `hermes.py`, `openclaw.py`, `src/language_tutor/installer/assets.py` (bundled-tree resolver), `src/language_tutor/schemas.py` (provider profile / status shape for per-file drift).
- Config: `pyproject.toml` (`[project].name`), `[tool.hatch.build.targets.wheel.force-include]` (bundle full host trees, not just one file).
- Workflows: `.github/workflows/workflow.yml` Python provisioning across all three jobs.
- Docs: `README.md`, `docs/install/claude.md`, `docs/install/codex.md`, `docs/install/hermes.md`, `docs/install/openclaw.md`, `docs/troubleshooting.md` (create or link-target).
- Tests: `tests/installer/test_*` (config-root blocked behavior, per-file drift, missing-sibling detection), `tests/installer/test_assets.py` (bundled-tree resolver), `tests/release/test_version_guard.py` (asserts distribution name `lingo-loop`).
- PyPI: first publish will land as `lingo-loop` 0.1.0; the previously-reserved `language-tutor` name is abandoned.
- Backwards compat: editable installs from existing checkouts keep importing `language_tutor` and running `tutor`; only the wheel distribution name changes. Anyone who previously ran `uv tool install language-tutor` from this repo (none in production) must `uv tool install lingo-loop`.
