 Pre-Merge Checklist — PR #12 (OSS distribution baseline)

  A. Repo hygiene (do first)

- [x] Commit + push uncommitted src/language_tutor/cli.py and tests/integration/test_tutor_init_cli.py (git status shows them dirty — CI won't see them otherwise) — branch clean and matches upstream at eb7ecac
- [x] CI green on PR: ruff check, pyright, pytest, doc-name guard (rtk/Spec N leak check) — GitHub PR #12 checks pass at 8b213a3
- [x] Coverage ≥ 80% (--cov-fail-under=80) — local pytest coverage 89.92%
- [x] ./scripts/build-check.sh and ./scripts/version-guard.sh v0.1.0 pass locally — both pass

B. Build / wheel distribution (local)

- [x] uv build → produces sdist + wheel, no errors — build-check produced `dist/lingo_loop-0.1.0.tar.gz` and `dist/lingo_loop-0.1.0-py3-none-any.whl`
- [x] tests/release/test_wheel_contents.py passes — bundled _assets/ present (.claude-plugin, .codex-plugin, openclaw-plugin, hermes-profile) — `uv run pytest tests/release/test_wheel_contents.py --no-cov` passes
- [x] tests/release/test_distribution_name.py passes — dist name lingo-loop — `uv run pytest tests/release/test_distribution_name.py --no-cov` passes
- [x] Install built wheel in clean venv → tutor init can read bundled assets via importlib.resources (not just repo-root path) — installed wheel into temp venv; `tutor init --provider claude --yes --json` wrote `.claude/plugins/lingo-loop/plugin.json`

C. Per-provider install test

  Automated provider smoke runs package install, isolated HOME/XDG paths, `tutor init`, `tutor doctor --json`, managed-file checks, and secret-leak checks. It does not replace live manual provider verification.

  - [x] Run all provider smoke checks: `scripts/provider-smoke.sh` — SKIPPED/ACCEPTED: script is absent from current branch; related smoke-harness spec docs were removed in 65505d6; user accepted skipping per-provider install test
  - [x] Run focused provider smoke when debugging: `scripts/provider-smoke.sh --provider claude --keep-workdir` — SKIPPED/ACCEPTED with provider smoke section
  - [x] If a smoke run fails, inspect the preserved temp workdir printed by the script: `reports/<host>.json` for decisions, `logs/` for command output, and `home/` for isolated managed files. Passing runs delete the workdir unless `--keep-workdir` is set. — SKIPPED/ACCEPTED with provider smoke section

  Live manual provider verification still requires a clean machine/container and host CLI checks. Source-install path (PyPI pending):
  uv tool install git+https://github.com/artemVeduta/lingo-loop
  tutor doctor --json    # expect status: ok

  Claude Code (docs/install/claude.md)
  - [ ] tutor init → keyboard menu, select Claude → writes ~/.claude/plugins/lingo-loop/plugin.json
  - [ ] tutor init --provider claude --yes (automation form)
  - [ ] tutor init --provider claude --dry-run --json (preview, no write)
  - [ ] Rerun tutor init repairs drift, leaves profile/history/secrets untouched
  - [ ] Verify host syntax claude plugin install ./.claude-plugin vs current Claude Code CLI (TODO marker at claude.md:57)
  - [ ] tutor session-start --json | jq '.sections[].title' → 6 sections
  - [ ] Uninstall: claude plugin uninstall language-tutor + uv tool uninstall lingo-loop

  Codex (docs/install/codex.md)
  - [ ] tutor init (Codex) → ~/.codex/plugins/lingo-loop/plugin.json; --yes and --dry-run --json
  - [ ] Verify codex plugin install ./.codex-plugin vs current Codex CLI (TODO codex.md:53)
  - [ ] Skills resolve from full clone (./skills/), not stripped copy
  - [ ] tutor session-start --json | jq '.profile.target_language' → "uk"

  Hermes (docs/install/hermes.md)
  - [ ] tutor init (Hermes) → ~/.hermes/profiles/lingo-loop/distribution.yaml; --yes, --dry-run
  - [ ] Verify hermes profile install <repo> --subdir hermes-profile syntax (TODO hermes.md:55)
  - [ ] export ANTHROPIC_API_KEY=... then hermes run language-tutor boots, loads SOUL.md
  - [ ] hermes profile list shows language-tutor 0.1.0
  - [ ] Confirm tutor init never reads/writes ANTHROPIC_API_KEY

  OpenClaw (docs/install/openclaw.md)
  - [ ] Node 22+ present; OpenClaw ≥1.0.0
  - [ ] tutor init (OpenClaw) → ~/.openclaw/plugins/lingo-loop/package.json, then openclaw plugins install lingo-loop
  - [ ] Verify openclaw plugins install lingo-loop (Step 1, TODO openclaw.md:35) and openclaw plugin install $(pwd) (manual fallback, TODO openclaw.md:59); reconcile plugins/plugin noun
  - [ ] Manual build path: npm install && npm run build → dist/index.js exists
  - [ ] tutor doctor --json | jq '.status' → "ok"

  D. GitHub repo setup (one-time infra — needed for release, not PR merge)

  - [ ] Repo public at github.com/artemVeduta/lingo-loop, MIT LICENSE renders — repo is PUBLIC; LICENSE exists on PR branch; GitHub `licenseInfo` is null and `LICENSE?ref=main` 404 until PR files land on main
  - [x] Branch protection on main: require CI green + PR review — main requires `ci (3.12)` with strict status checks and 1 approving PR review; admin enforcement enabled
  - [x] GH Environments created: pypi and testpypi (match workflow.yml) — GitHub API lists both environments
  - [ ] PyPI Trusted Publisher registered: project lingo-loop, owner artemVeduta, repo lingo-loop, workflow filename workflow.yml, environment pypi (renaming workflow.yml breaks this —
  comment at top of file) — public API shows `lingo-loop` 404/unclaimed; publisher registration still requires PyPI owner setup
  - [ ] TestPyPI Trusted Publisher registered: same, environment testpypi — public API shows `lingo-loop` 404/unclaimed; publisher registration still requires TestPyPI owner setup
  - [x] No PyPI API tokens in repo secrets (OIDC only — confirm) — `gh secret list --repo artemVeduta/lingo-loop` returned no repo secrets
  - [x] Dependabot enabled (.github/dependabot.yml) — config present on PR branch for pip and GitHub Actions weekly updates
  - [ ] Issue templates + PR template render in GH UI — templates present on PR branch; main returns 404 until merge, so GH UI render cannot be confirmed yet
  - [x] FUNDING.yml — currently all commented out; uncomment if funding channel wanted (optional) — file present and all funding channels remain commented
  - [ ] Reserve dist name on PyPI + TestPyPI (lingo-loop not taken) — PyPI and TestPyPI JSON APIs both return 404 for `lingo-loop`; name appears available but not reserved

  E. Release dry-run (after merge, before public)

  - [ ] /pre-release-checks (read-only audit) passes — DEFERRED: release skill is a post-merge gate; local `build-check.sh`, `version-guard.sh`, CI, coverage, and wheel checks passed in PR
  - [ ] Prerelease first: tag v0.1.0-rc.1 → routes to testpypi → verify on test.pypi.org, prerelease GH Release, attestations — DEFERRED until merge + TestPyPI Trusted Publisher/environment setup
  - [ ] workflow_dispatch manual trigger works (input ref) — DEFERRED until release workflow is on main
  - [ ] Real v0.1.0 → pypi → verify per RELEASING.md:
    - PyPI page pypi.org/project/lingo-loop/0.1.0/ shows sdist+wheel
    - Sigstore/PEP 740 provenance on release page
    - gh release view v0.1.0 notes correct
    - Releases sidebar lists v0.1.0
    - CHANGELOG.md on main has [0.1.0] + fresh empty [Unreleased]
  - [ ] pip install lingo-loop (from real PyPI) → tutor doctor ok — DEFERRED until real PyPI release

  F. Launch-blocking (NOT merge-blocking — track per docs/internal/launch-checklist.md)

  - [ ] Resolve all <!-- TODO: verify --> host-CLI markers (9 across install docs) — launch-blocking only; still tracked in `docs/internal/launch-checklist.md`
  - [ ] Set Last verified: YYYY-MM-DD per provider (headers currently say "Verification pending") — launch-blocking only; still tracked in `docs/internal/launch-checklist.md`
  - [x] Verify review_intensity / feedback_verbosity enums (configuration.md:51-52) — confirmed against schemas.py (FeedbackVerbosity also has `standard`; doc fixed), markers removed
  - [ ] Capture screenshots + asciinema casts (8 assets) into docs/assets/ — launch-blocking only; still tracked in `docs/internal/launch-checklist.md`
  - [ ] README demo.cast + demo.gif — launch-blocking only; still tracked in `docs/internal/launch-checklist.md`
  - [ ] Mirror launch checklist to pinned GH issue "Launch-blocking assets" — launch-blocking only; still tracked in `docs/internal/launch-checklist.md`
