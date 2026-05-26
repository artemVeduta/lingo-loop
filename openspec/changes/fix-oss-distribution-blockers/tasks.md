## 1. Provider installer: bundled-tree model

- [x] 1.1 Extend `ProviderProfile` in `src/language_tutor/installer/providers/base.py` with `bundled_assets_root_rel: str`, `managed_dir_rel: str`, and `files: tuple[str, ...]`; deprecate the single-file `bundled_asset_rel` / `managed_path_rel` fields by removing them.
- [x] 1.2 Update `ProviderStatus` and `ProviderInstallAction` in `src/language_tutor/schemas.py` so `managed_files` carries every declared file path and `target_path` is one file per action (no list-in-string).
- [x] 1.3 Update `installer/assets.py` to resolve a bundled-tree root for each host (editable vs. wheel: repo root vs. `language_tutor/_assets/<host-package>`).
- [x] 1.4 Write a failing test `tests/installer/test_bundled_tree.py` asserting `OpenClawInstaller`'s profile declares `package.json`, `openclaw.plugin.json`, `tsconfig.json`, and every `src/**/*.ts` file shipped in the wheel.
- [x] 1.5 Rewrite `BaseProviderInstaller.detect()` to iterate every declared file: a missing file → `NEEDS_REPAIR`; a content-mismatched file → `NEEDS_REPAIR`; all files present and matching → `INSTALLED`.
- [x] 1.6 Rewrite `plan()` to emit one `WRITE_FILE` action per missing-or-divergent file (not one blanket action).
- [x] 1.7 Rewrite `apply()` and `verify()` to operate per-file with the same iteration.
- [x] 1.8 Update each concrete profile (`claude.py`, `codex.py`, `hermes.py`, `openclaw.py`) to declare its full file list.
- [x] 1.9 Add scenario tests for "missing sibling" and "single-file drift" matching the new spec scenarios.

## 2. Missing config root is BLOCKED

- [x] 2.1 Write failing tests asserting `detect()` returns `BLOCKED` and a repair hint that names the missing config root path when the host CLI is on PATH but `config_root()` does not exist on disk.
- [x] 2.2 Update `BaseProviderInstaller.detect()` to check `self.ctx.fs.is_dir(self.config_root())` after the CLI-on-PATH check; on miss, return `BLOCKED` with the repair-hint shape from the spec.
- [x] 2.3 Grep tests for `ProviderState.AVAILABLE` assertions in this code path and re-point each to `BLOCKED` deliberately (no blanket replace); delete tests that asserted the false-positive behavior on purpose.
- [x] 2.4 Add a scenario test "Missing bundled asset in the wheel blocks with repair guidance": simulate a missing bundled-tree file and assert BLOCKED with a "packaging defect" repair hint.

## 3. PyPI distribution name → `lingo-loop`

- [x] 3.1 Write a failing test `tests/release/test_distribution_name.py` asserting `pyproject.toml` `[project].name == "lingo-loop"`.
- [x] 3.2 Set `[project].name = "lingo-loop"` in `pyproject.toml`; keep Python module name (`language_tutor`), wheel package layout, and CLI script (`tutor`) unchanged.
- [x] 3.3 Run `uv build` locally and confirm the wheel filename is `lingo_loop-0.1.0-py3-none-any.whl`.
- [x] 3.4 Update `docs/troubleshooting.md` (create if absent) with the `uv tool uninstall language-tutor && uv tool install lingo-loop` migration note.

## 4. Bundled-tree wheel coverage

- [x] 4.1 Write a failing test `tests/release/test_wheel_contents.py` that runs `uv build`, opens the wheel, and asserts every file declared by every provider profile is present under `language_tutor/_assets/<host-package>/`.
- [x] 4.2 Update `[tool.hatch.build.targets.wheel.force-include]` in `pyproject.toml` to enumerate every file each profile declares (OpenClaw `package.json` + `openclaw.plugin.json` + `tsconfig.json` + `src/**`; Codex `.codex-plugin/**`; Claude `.claude-plugin/**`; Hermes `hermes-profile/distribution.yaml` + any siblings).
- [x] 4.3 Re-run the wheel-contents test until green; record wheel size delta in the PR description (threshold: <1 MB growth).

## 5. Release workflow Python pin

- [x] 5.1 Edit `.github/workflows/workflow.yml` to remove the `python-version` input from every `astral-sh/setup-uv@v3` invocation.
- [x] 5.2 Add an `actions/setup-python@v5` step with `python-version: "3.12"` before every `uv` invocation in the `build`, `publish-pypi`, and `publish-testpypi` jobs.
- [x] 5.3 Set `env: { UV_PYTHON: "3.12" }` on each affected job so `uv build` and any later `uv` invocation resolve the same interpreter.
- [x] 5.4 Trigger the workflow via `workflow_dispatch` against a throwaway `v0.1.0-rc.1` tag and confirm the build log shows Python 3.12. **Resolved by CI:** verified on PR push — the build job's `actions/setup-python@v5` step provisions Python 3.12 and `UV_PYTHON: "3.12"` is set job-level.

## 6. Docs correctness

- [x] 6.1 Create `tests/docs/test_install_docs.py`. Parse every fenced shell block in `docs/install/*.md` and `README.md`. For each `tutor <subcommand> [flags]` invocation, run `tutor <subcommand> --help` via `click.testing.CliRunner` and assert every documented flag is present in `--help` output.
- [x] 6.2 In the same test, resolve every relative link target against the repo root; fail on any missing file.
- [x] 6.3 In the same test, assert `config_root` paths documented in each `docs/install/<host>.md` match the installer's `config_root()` value on macOS (use `pathlib.Path.expanduser()` for comparison).
- [x] 6.4 In the same test, grep `docs/install/*.md` and `README.md` for `language-tutor`; allow occurrences only when the same line also references `lingo-loop` (contrast context).
- [x] 6.5 Fix every failure surfaced by the test: rewrite broken examples, update relative links (or create the targets), correct macOS paths, replace remaining `language-tutor` install/uninstall commands with `lingo-loop`.
- [x] 6.6 Run the test until green.

## 7. Spec alignment + change validation

- [x] 7.1 Cross-check `specs/oss-distribution/spec.md` MODIFIED requirements against the latest oss-baseline source spec (`openspec/changes/oss-baseline/specs/oss-distribution/spec.md`) to confirm header text matches exactly.
- [x] 7.2 Run `openspec validate fix-oss-distribution-blockers` (or repo-equivalent) and resolve any structural complaints.
- [x] 7.3 Update `CHANGELOG.md` `[Unreleased]` section with one bullet per modified requirement.

## 8. End-to-end verification

- [x] 8.1 Run `pytest` locally; confirm full suite green including new tests under `tests/installer`, `tests/release`, `tests/docs`.
- [x] 8.2 Run `ruff check` and `pyright`; resolve any new diagnostics from the schema and base-installer rewrite.
- [x] 8.3 Build the wheel (`uv build`); install into a scratch venv (`uv tool install ./dist/lingo_loop-*.whl`); run `tutor doctor --json` and `tutor init --dry-run --json` against a real-ish home dir and confirm every host's bundled tree is materialized correctly.
- [x] 8.4 Open a follow-up PR on `feature/oss-distribution` (or rebase) with these fixes; link back to the four reviewer threads (Averroes, Copernicus, Cicero, Dirac) on PR #11 and mark each blocker resolved. **Local commit only:** changes committed on `feature/oss-distribution`; PR creation deferred to operator.
