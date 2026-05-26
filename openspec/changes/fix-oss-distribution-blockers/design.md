## Context

PR #11 lands the OSS distribution baseline (`oss-baseline` change) and turns CI green, but four independent sub-agent reviews surfaced merge blockers that the green build did not catch:

- **Installer false-positive success** — `BaseProviderInstaller` (`src/language_tutor/installer/providers/base.py`) models each host as a single bundled-file → single managed-file copy. The real shipped host packages are directory trees: the OpenClaw plugin needs `package.json` plus `openclaw.plugin.json` plus `tsconfig.json` plus a `src/` tree; the Codex plugin layout under `.codex-plugin/` similarly requires adjacent assets. `tutor init` writes one file, the installer reports `INSTALLED`, but the host actually fails to load the plugin at runtime.
- **Release/distribution name mismatch** — `pyproject.toml` `[project].name = "language-tutor"` while the PyPI Trusted Publisher entry, GitHub Environment URLs, and every install doc target `lingo-loop`. The first tag-driven publish would fail.
- **Spec-vs-implementation divergence on missing config root** — the `interactive provider installer` requirement says a missing host config root yields `BLOCKED` with repair guidance, but `detect()` returns `AVAILABLE` (and `plan()` schedules a write) when the host CLI is on PATH but the config root doesn't exist. Tests assert the wrong behavior.
- **Docs that don't work** — `docs/install/*.md` and `README.md` contain CLI examples that no longer parse, broken relative links (e.g. `../troubleshooting.md`), wrong macOS config-root paths, and lingering `language-tutor` package-name references.
- **Workflow Python pin ignored** — `.github/workflows/workflow.yml` uses `astral-sh/setup-uv@v3` with `python-version: "3.12"`, but `setup-uv@v3` does not accept that input; the build job inherits whatever Python the runner ships with.

This change is the targeted fix-pack required to unblock merge of PR #11 and the first PyPI publish. It does not re-litigate the broader OSS baseline scope — it patches the four review-surfaced gaps and tightens the `oss-distribution` capability so the same gaps cannot regress.

## Goals / Non-Goals

**Goals:**

- Distribution name in `pyproject.toml` matches the Trusted Publisher binding and all docs (`lingo-loop`).
- Installer treats each host as a bundled directory tree; `detect()`, `plan()`, `apply()`, and `verify()` operate on every declared file, and drift is reported per file.
- A missing host config root is a `BLOCKED` state with actionable repair guidance, exactly matching the existing spec scenario.
- Release workflow honors Python 3.12 across all jobs and the version-guard script.
- Every CLI example and link in `README.md` and `docs/install/*.md` resolves against the shipped CLI and on-disk paths.
- Spec deltas pin these behaviors so a future regression is caught by spec review, not by hand review of a CI-green PR.

**Non-Goals:**

- Renaming the Python module `language_tutor` → `lingo_loop` (still tracked by future `rename-lingo-loop` change).
- Renaming the CLI command `tutor`.
- Adding new providers, new install paths, or new doc surfaces.
- Re-architecting `tutor doctor` or `tutor init` UX — only the internal installer model changes; the public CLI surface stays.
- Cutting the actual `v0.1.0` tag (the release flow remains operator-driven via `/release-cut` then `/release-tag`).

## Decisions

### 1. Provider installer: bundled-tree model, not bundled-file

**Decision.** Replace the single-file `bundled_asset_rel` / `managed_path_rel` pair on `ProviderProfile` with a `ProviderAssets` declaration: a bundled source directory (resolved via `installer/assets.py`) plus a managed destination directory plus an explicit list of relative file paths to materialize. `detect()`, `plan()`, `apply()`, `verify()` iterate over every declared file. `ProviderStatus.managed_files` becomes a list of every managed file, not a one-element list. Drift detection compares per file; a missing or content-mismatched sibling marks the host `NEEDS_REPAIR` and the repair plan schedules `WRITE_FILE` actions only for the divergent files.

**Why over the alternatives:**

- *Whole-directory copy with no manifest.* Simpler, but the wheel ships `_assets/openclaw-plugin/package.json` only (per `pyproject.toml`'s `force-include` block). A whole-directory copy would silently materialize anything we happen to bundle later, including dev-only files. Explicit file lists keep the contract auditable.
- *Per-host hand-rolled installers (no shared base).* Avoids the abstraction but duplicates four nearly-identical detect/plan/apply/verify loops. Reviewers would have to re-check the same logic in four places; the present base + profile composition (Composition > Inheritance, DI via `InstallerContext`) stays, only the profile shape widens.

**Schema impact.** `ProviderProfile` adds `bundled_assets_root_rel: str`, `managed_dir_rel: str`, `files: tuple[str, ...]`. `ProviderInstallAction.target_path` stays a single file path (one action per file). `ProviderStatus.managed_files` already a list — populate fully. `pyproject.toml` `[tool.hatch.build.targets.wheel.force-include]` widens to bundle every file each profile names.

### 2. Missing config root is `BLOCKED`, not `AVAILABLE`

**Decision.** `BaseProviderInstaller.detect()` checks both that the host CLI is on PATH *and* that `config_root()` exists as a directory. If the CLI exists but the config root does not, return `ProviderState.BLOCKED` with `repair_hint = f"Run {host} once to create {config_root} before installing the plugin; see {docs_url}"`. This makes the existing spec scenario "Missing host CLI blocks with repair guidance" pass by construction; the scenario already says "the host CLI **or required config root** is absent".

**Why over the alternative.** We considered creating the config root ourselves on first `tutor init`. Rejected because (a) host CLIs use that directory to store credentials and per-user state on their own first run, and quietly creating it could shadow that initialization; (b) the spec was deliberately written to defer to the host's own first-run; (c) the repair hint already exists in the spec text — we're catching up to the spec, not changing it.

**Test impact.** The Copernicus review flagged tests that assert `AVAILABLE` in this state. Those tests get re-pointed to assert `BLOCKED` + the repair hint shape. A new scenario covers each provider individually.

### 3. PyPI distribution name = `lingo-loop`

**Decision.** Set `pyproject.toml` `[project].name = "lingo-loop"`. Leave the Python module name (`language_tutor`), package layout (`src/language_tutor`), and CLI script (`tutor = "language_tutor.cli:main"`) unchanged. Wheel filename becomes `lingo_loop-0.1.0-…` (hyphen→underscore normalization) which matches what the Trusted Publisher expects.

**Why over the alternative.** A full module/CLI rename (`language_tutor → lingo_loop`, `tutor → lingo`) is intentionally deferred to `rename-lingo-loop` per the oss-baseline proposal §"Project Rename". Forcing it into this fix-pack would balloon the diff (every import path, every test, every doc snippet) and re-open scope that was already decided. The distribution-name-only change is one line and matches what the Trusted Publisher was registered for.

**Version-guard impact.** `scripts/version-guard.sh` reads `[project].version` and compares to the tag. It does not match on `[project].name`, so the rename doesn't break it; we add a test that asserts `[project].name == "lingo-loop"` to lock the value.

### 4. Release workflow Python pin

**Decision.** Remove the ignored `python-version` input from `astral-sh/setup-uv@v3` and add an explicit `actions/setup-python@v5` step with `python-version: "3.12"` ahead of every `uv` invocation in `build`, `publish-pypi`, and `publish-testpypi`. Set `UV_PYTHON: "3.12"` on the job so `uv build` resolves the same interpreter.

**Why over the alternatives:**

- *Upgrade to `astral-sh/setup-uv@v4`* (which does accept a `python-version` input). Tempting, but `setup-uv@v4` was released recently and the migration would silently change uv binary version too; this fix is meant to be minimal and reversible.
- *Skip Python provisioning entirely and let `uv` resolve.* `uv build` will install a managed Python on its own, but that hides the interpreter version from the build log and from CI cache keys. Explicit is better.

### 5. Doc-correctness gate

**Decision.** Add a `tests/docs/test_install_docs.py` that, for each file in `docs/install/*.md` and `README.md`:

1. Parses every fenced shell block. For every line that starts with `tutor `, invoke the CLI with `--help` on the leaf subcommand (e.g. `tutor init --help`) and assert the documented flags are accepted (parse-only, no side effects).
2. Resolves every relative link target against the repo root and asserts the file exists.
3. Greps for `language-tutor` outside contexts that explicitly contrast it with `lingo-loop` (e.g. "the Python module is still `language_tutor`" stays) and fails the test on drift.

**Why.** The Dirac review flagged broken examples and links that hand review missed for two passes; the only durable fix is a test. Cost is small (the docs surface is 4 files + README) and the test is read-only.

## Risks / Trade-offs

- **[Risk] Wheel size grows when we bundle full host trees.** → Mitigation: `[tool.hatch.build.targets.wheel.force-include]` enumerates only files actually needed at install time; OpenClaw's `dist/` build output stays excluded (it's regenerated at host load). Measured wheel delta tracked in tasks; if it exceeds 1 MB we revisit.
- **[Risk] Distribution rename breaks anyone who already ran `uv tool install language-tutor` from this checkout.** → Mitigation: no production users yet (pre-PyPI). README's install section explicitly notes the rename in the install-docs update. `uv tool uninstall language-tutor && uv tool install lingo-loop` documented in `docs/troubleshooting.md`.
- **[Risk] Tests that asserted `AVAILABLE` for missing-config-root behavior are load-bearing for unrelated code paths.** → Mitigation: tasks include grepping all `ProviderState.AVAILABLE` assertions and updating each deliberately, not via blanket replace.
- **[Risk] Doc-correctness test is flaky if CLI `--help` output drifts.** → Mitigation: test parses help text only for *flag presence*, not output equality; no snapshot.
- **[Trade-off] We do not bump `oss-baseline` itself with these fixes.** Two paths considered: (a) amend the oss-baseline change in-place, (b) ship a follow-up fix-pack change. We chose (b) because oss-baseline is on PR #11 with a long review trail and these fixes are independent enough to land as their own PR/archive. The OpenSpec archive flow will reconcile spec deltas on archive of oss-baseline first, then this change.

## Migration Plan

1. **PR sequencing.** Open `fix-oss-distribution-blockers` PR against the same `feature/oss-distribution` branch (or a rebase of it) so reviewers can see the delta against PR #11.
2. **Test-first per task.** Each blocker has tests written before the fix (TDD per project convention).
3. **Rollback.** Every change is local to this branch; revert is a single PR revert. The PyPI rename is the only externally-visible decision — if we need to roll back, leave the rename in place (it's still unpublished) and revert only the code.
4. **Verification on the merged branch.** Before tagging `v0.1.0`: run `tutor doctor` against a real OpenClaw checkout, run `uv build`, inspect the wheel contents (`unzip -l dist/lingo_loop-0.1.0-*.whl`) to confirm host trees are present, run the docs test, and dry-run the release workflow via `workflow_dispatch` with a `v0.1.0-rc.1` tag against TestPyPI.

## Open Questions

- Should we cache the bundled-tree content hash in `ProviderStatus` so `tutor doctor` can show a one-line "drift in 2 of 4 files" summary without printing each path? Defer until a user actually asks for the rolled-up view.
- Does `tutor init --provider openclaw --yes --json` need a `--missing-asset-policy=strict|warn` switch? Not in v0.1; strict-by-default is the spec, anything else can be a follow-up.
