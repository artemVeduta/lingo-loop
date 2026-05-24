# Tasks: oss-baseline

Sequence: do tasks in numbered order within each section. Sections can be parallelized (legal, manifests, README, docs, .github) once Section 0 prerequisites land.

## 0. Prerequisites (must complete before any other section)

- [x] 0.1 ~~Confirm PyPI name availability~~ — resolved 2026-05-24: project renamed to `lingo-loop`; PyPI `lingo-loop` 404 (free), npm 404 (free), `github.com/artemVeduta/lingo-loop` 404 (free). `github.com/lingo-loop` (org/user) is taken — acceptable for solo-maintainer personal-repo path.
- [x] 0.2 ~~Confirm maintainer agrees with MIT~~ — locked 2026-05-24.
- [x] 0.3 Enable GitHub Discussions on the repo (manual: Settings → Features → Discussions). Required for `ISSUE_TEMPLATE/config.yml` link to work.
- [x] 0.4 Confirm current repo visibility (`gh repo view --json visibility`). If `public`, LICENSE must land in the very first commit of this change. If `private`, normal order applies. — repo PUBLIC; squash-merge to main means single public commit, LICENSE lands inside this change's commits (user-approved 2026-05-24).
- [x] 0.5 Rename GitHub repo `language-tutor` → `lingo-loop` (Settings → General → Repository name). Verify old URL returns 301. Update local clone remote: `git remote set-url origin git@github.com:artemVeduta/lingo-loop.git`. — done 2026-05-24, 301 verified.

## 1. Legal artifacts

- [x] 1.1 Create `LICENSE` at repo root with verbatim MIT text (SPDX `MIT`, e.g. https://opensource.org/license/mit/); copyright line: `Copyright (c) 2026 Artem Veduta`.
- [x] 1.2 Create `CODE_OF_CONDUCT.md` using Contributor Covenant v2.1 verbatim from https://www.contributor-covenant.org/version/2/1/code_of_conduct.md ; set enforcement contact to `veduta.artem20@gmail.com`.
- [x] 1.3 Create `SECURITY.md` per design Section 5 (supported versions, reporting via GitHub Security Advisories, 14-day SLA, scope, disclosure policy).
- [x] 1.4 Create `CONTRIBUTING.md` per design Section 4 (dev setup, OpenSpec workflow, branch naming, commit conventions, PR checklist).
- [x] 1.4a In `CONTRIBUTING.md`, add a **DCO sign-off** section: require contributors to sign commits with `git commit -s`, link to https://developercertificate.org/, and state that PRs missing sign-off will be asked to amend. (DCO GitHub App enablement deferred to later repository-hardening work.)
- [x] 1.5 Create `CHANGELOG.md` seeded with `[Unreleased]` section per design Section 7.

## 2. License field synchronization

- [x] 2.1 `.claude-plugin/plugin.json`: verify `"license": "MIT"` (already MIT — no change expected).
- [x] 2.2 `.codex-plugin/plugin.json`: verify `"license": "MIT"` (already MIT — no change expected).
- [x] 2.3 `openclaw-plugin/package.json`: verify `"license": "MIT"` (already MIT — no change expected).
- [x] 2.4 `hermes-profile/distribution.yaml`: change `license: see repository` → `license: MIT`.
- [x] 2.5 `hermes-profile/distribution.yaml`: change `source_url: https://github.com/synesthesias/hermes` → `source_url: https://github.com/artemVeduta/lingo-loop`.
- [x] 2.6 `pyproject.toml`: add `license = { text = "MIT" }` under `[project]`.

## 3. pyproject.toml metadata

- [x] 3.1 Add `[project.urls]` block with `Homepage`, `Source`, `Issues`, `Changelog` keys pointing to `https://github.com/artemVeduta/lingo-loop` and its sub-paths.
- [x] 3.2 Add `classifiers` list: at minimum `License :: OSI Approved :: MIT License`, `Programming Language :: Python :: 3.12`, `Operating System :: OS Independent`, `Intended Audience :: End Users/Desktop`, `Topic :: Education`, `Topic :: Education :: Computer Aided Instruction (CAI)`.
- [x] 3.3 Add `keywords = ["language-learning", "tutor", "claude-code", "codex", "local-first", "cli", "lingo-loop"]`.
- [x] 3.4 Add `authors = [{ name = "Artem Veduta", email = "veduta.artem20@gmail.com" }]` if not present.
- [x] 3.5 Confirm `requires-python = ">=3.12"` matches classifier (3.12 only); pin via `pyproject.toml` and reference in README "Prerequisites".
- [x] 3.6 **Do not** change `[project] name` or module path in this change — package is still installed as `language-tutor` locally; rename to `lingo-loop` happens in `rename-lingo-loop` follow-up change before the first production PyPI tag. Confirmed: `name = "language-tutor"` unchanged; wheel package `src/language_tutor` unchanged.

## 4. README rewrite

- [x] 4.1 Back up current README to `docs/internal/README.maintainer.md` (preserves the `rtk` / Spec-NNN material for maintainer use).
- [x] 4.2 Write new README per design Section 2 structure (12 sections, learner-first).
- [x] 4.3 Embed ASCII architecture diagram (design Section 2, "How it works") in README.
- [x] 4.4 Replace all `rtk <cmd>` examples with bare `<cmd>` or `uv` equivalents; no `rtk` reference remains in README.
- [x] 4.5 Remove all "Spec 006", "Spec 007", and similar internal references from README.
- [x] 4.6 Add placeholder for asciinema cast + rendered GIF: `<!-- TODO(oss-baseline-assets): record top-level demo cast and render gif via agg -->`; link targets `docs/assets/demo.cast` and `docs/assets/demo.gif`. README embeds the GIF (GitHub strips JS so the asciinema-player widget would not render); cast file is linked for users who want to replay interactively.
- [x] 4.7 Add badge row: license (shields.io MIT), Python version, CI status. Badges point at `artemVeduta/lingo-loop`; CI badge will render broken until first green run on `main`, then self-heals.
- [x] 4.8 Write Claude quick-start block (≤6 copy-paste commands). Snippets reference future `pip install lingo-loop` as the published distribution name; the executable command remains `tutor ...` (CLI name is unchanged in this change).
- [x] 4.9 Add three one-line links to `docs/install/{codex,hermes,openclaw}.md` under "Other hosts" section.
- [x] 4.10 Replace any remaining `language-tutor` URL/name references in README with `lingo-loop` (distribution name and GitHub URL only — module name `language_tutor` is unchanged and not exposed in README).

## 5. docs/ tree

- [x] 5.1 Create `docs/install/claude.md` from template in design Section 3.
- [x] 5.2 Create `docs/install/codex.md` from template.
- [x] 5.3 Create `docs/install/hermes.md` from template.
- [x] 5.4 Create `docs/install/openclaw.md` from template.
- [x] 5.5 Create `docs/configuration.md` (profile/preferences YAML reference + override locations).
- [x] 5.6 Create `docs/privacy.md` (one-page restatement of local-first / no telemetry / data locations).
- [x] 5.7 Create `docs/troubleshooting.md` (cross-host common errors index).
- [x] 5.8 Create `docs/architecture.md` (longer architecture reference; expands the README's ASCII diagram with module-level detail). Moved pre-existing maintainer-facing `docs/ARCHITECTURE.md` to `docs/internal/ARCHITECTURE.md` to free the case-insensitive path.
- [x] 5.9 Create `docs/assets/` directory with `.gitkeep`.
- [x] 5.10 For each `install/<host>.md`, add screenshot placeholder + asciinema placeholder with a tracked `<!-- TODO(oss-baseline-assets): ... -->` comment; record the placeholders in a "Launch-blocking assets" checklist (separate file `docs/internal/launch-checklist.md` or pinned issue once repo is public).

## 6. .github/ scaffold

- [x] 6.1 Create `.github/workflows/ci.yml` per design Section 6 (ruff + pyright + pytest with coverage gate, Python 3.12).
- [x] 6.2 Create `.github/ISSUE_TEMPLATE/bug_report.yml` (form schema, fields per design Section 6).
- [x] 6.3 Create `.github/ISSUE_TEMPLATE/feature_request.yml`.
- [x] 6.4 Create `.github/ISSUE_TEMPLATE/config.yml` with `blank_issues_enabled: false` and Discussions contact link.
- [x] 6.5 Create `.github/PULL_REQUEST_TEMPLATE.md` (summary, linked issue/change, test plan, checklist).
- [x] 6.6 Create `.github/dependabot.yml` weekly schedule for `pip` and `github-actions` ecosystems; group minor/patch updates.
- [x] 6.7 Create `.github/FUNDING.yml` with commented examples (no active funding key yet).

## 6a. Branching, commits, release procedure

- [x] 6a.1 Create `RELEASING.md` at repo root per spec Requirement "Repository MUST publish a release procedure and follow SemVer": SemVer policy, CHANGELOG promotion ritual, `vX.Y.Z` annotated tag, `gh release create vX.Y.Z --notes-from-tag`, post-release verification, authorized releaser.
- [x] 6a.2 In `CONTRIBUTING.md`, add a **Branching model** section: trunk-based, allowed prefixes `feature|fix|docs|chore|refactor|test`, short-lived (<1 week), squash-merge to `main`, no `develop`/`release/*`.
- [x] 6a.3 In `CONTRIBUTING.md`, add a **Commit messages** section: Conventional Commits 1.0, allowed types list (`feat|fix|docs|chore|refactor|test|build|ci|perf|style|revert`), subject ≤72 chars, breaking changes marked with `!` or `BREAKING CHANGE:` footer. Cross-link to DCO sign-off section (1.4a).
- [ ] 6a.4 Configure branch protection on `main` (manual GH settings, overlaps with 8.2 but expanded): require PR, require `ci` status check, `required_linear_history: true`, `allow_force_pushes: false`, `allow_deletions: false`. Verify via `gh api repos/artemVeduta/lingo-loop/branches/main/protection`. — manual GH settings — verify in §7.12
- [x] 6a.5 Add `CHANGELOG.md` promotion checklist line to `RELEASING.md` showing the exact diff: rename `[Unreleased]` → `[0.1.0] - YYYY-MM-DD`, add new empty `[Unreleased]` on top.

## 7. Verification

- [x] 7.1 Run `openspec validate oss-baseline --strict`; fix any errors. — `Change 'oss-baseline' is valid`.
- [x] 7.2 Run `ruff check .` on entire repo (should pass since no code changed). — `All checks passed!`
- [x] 7.3 Run `pyright` (should pass). — `0 errors, 0 warnings, 0 informations`.
- [x] 7.4 Run `pytest` (should pass; no behavior changed). — `391 passed in 6.68s`.
- [x] 7.4a Run `pytest --cov --cov-report=term` and record the actual coverage percentage. If it is below the `--cov-fail-under=80` gate set in `pyproject.toml`, either (a) raise coverage with new tests where trivial, or (b) lower the gate to the floor of the current measurement, file a GitHub issue titled "Restore --cov-fail-under=80", and link the issue from `pyproject.toml` with a code comment. Do not silently disable the gate. — Total coverage: **90.71%** (well above 80% gate); no action needed.
- [x] 7.5 Grep README for forbidden tokens: `grep -E '(\brtk\b|Spec [0-9])' README.md` → must return empty. — empty.
- [x] 7.6 Grep `docs/` (excluding `docs/internal/`) for same forbidden tokens → must return empty. — empty after stripping `rtk ` prefix from 4 lines in `docs/ROADMAP.md`.
- [x] 7.7 Confirm all six license fields read `MIT`: `grep -r 'license' LICENSE pyproject.toml .claude-plugin/plugin.json .codex-plugin/plugin.json openclaw-plugin/package.json hermes-profile/distribution.yaml`. — all six confirm `MIT` (LICENSE text, `license = { text = "MIT" }`, three `"license": "MIT"`, `license: MIT`).
- [ ] 7.8 Open the new README in GitHub's preview (push to a branch, open in browser) and confirm visual structure matches design Section 2. — **manual: push branch + visual check**.
- [ ] 7.9 Trigger CI on the branch by opening a draft PR; confirm green. — **manual: requires draft PR**.
- [x] 7.10 Verify `RELEASING.md` exists at repo root and contains the SemVer / CHANGELOG promotion / tag / `gh release create` / verification sections. — present, 11 matches across required sections.
- [x] 7.11 Verify `CONTRIBUTING.md` documents trunk-based branching and Conventional Commits per spec requirements. — Branching, Conventional Commits, DCO/Sign-off sections present (6 matches).
- [ ] 7.12 Verify branch protection on `main` via `gh api repos/artemVeduta/lingo-loop/branches/main/protection | jq '{pr: .required_pull_request_reviews != null, ci: (.required_status_checks.contexts // [] | index("ci")), linear: .required_linear_history.enabled, force: .allow_force_pushes.enabled, del: .allow_deletions.enabled}'`. Expect `pr=true, ci!=null, linear=true, force=false, del=false`. — **manual: requires GH Settings + `ci` workflow to exist on `main` first (chicken-and-egg — wire up after 7.9 green)**.

## 8. Merge & announce-prep (post-merge, but tracked here)

- [ ] 8.1 After merge to `main`, on the repo settings page set: Description (from README tagline), Website (placeholder until docs site), Topics (`language-learning`, `claude-code`, `codex`, `cli`, `local-first`, `agent-plugin`).
- [ ] 8.2 Enable "Require status checks to pass before merging" on `main` branch protection, with `ci` as required check.
- [ ] 8.3 Verify the repository's License sidebar shows "MIT License".
- [ ] 8.4 Create issue "Launch-blocking assets" tracking all placeholder screenshots, asciinema casts, and rendered GIFs before any public announcement.
- [ ] 8.5 Confirm `https://github.com/artemVeduta/language-tutor` still 301-redirects to `https://github.com/artemVeduta/lingo-loop` (GitHub does this automatically after rename).
- [ ] 8.6 Open follow-up change `rename-lingo-loop` (module `language_tutor` → `lingo_loop`, CLI entry-point name, plugin manifest `name` fields). Sequenced **before** the first production PyPI tag so the first published artifact ships under the final module name. Spawn via `/opsx:propose`.
- [ ] 8.7 After `rename-lingo-loop` merges, cut `v0.1.0-rc.1` and verify TestPyPI + `uv tool install lingo-loop && tutor init` end-to-end.

## 9. PyPI publish automation (folded in 2026-05-25)

- [ ] 9.0 Confirm PyPI pending publisher already registered for project `lingo-loop` (owner=`artemVeduta`, repo=`lingo-loop`, workflow filename=`workflow.yml`, env=`pypi`). Same for TestPyPI (env=`testpypi`). User registered on 2026-05-25; verify in PyPI → Manage → Publishing.
- [ ] 9.1 Create GitHub Environment `pypi` (Settings → Environments → New). No approvers for solo maintainer; add later when contributors exist.
- [ ] 9.2 Create GitHub Environment `testpypi` (same settings). Used for `-rc.N` / `-alpha.N` / `-beta.N` tag routing.
- [x] 9.3 Create `scripts/version-guard.sh` per design §11 (compares tag `vX.Y.Z` against `pyproject.toml` `[project].version`, exits 1 on mismatch). `chmod +x`. — smoke-tested 2026-05-25: PASS on `v0.1.0`, fails as expected on mismatch.
- [x] 9.4 Create `scripts/changelog-promote.sh` (rename `[Unreleased]` → `[X.Y.Z] - YYYY-MM-DD`, insert empty `[Unreleased]` on top). Used by `release-cut` skill and CI sanity check. `chmod +x`. — smoke-tested 2026-05-25: BSD-awk safe (no multi-line `-v`), idempotent dup-guard verified.
- [x] 9.5 Create `scripts/build-check.sh` (`uv build` then `twine check dist/*`; non-zero on any failure). `chmod +x`. — twine fetched on-demand via `uvx` (not added as dev dep).
- [x] 9.6 Create `.github/workflows/workflow.yml` per design §11:
      - trigger: `push: tags: ['v*.*.*']` + `workflow_dispatch`
      - `build` job: checkout, `astral-sh/setup-uv@v3`, `scripts/version-guard.sh ${{ github.ref_name }}`, `uv build`, `actions/upload-artifact@v4`
      - `publish` job: needs build, environment selected by tag pattern (rc → testpypi else pypi), `permissions: { id-token: write, contents: write }`, `actions/download-artifact@v4`, `pypa/gh-action-pypi-publish@release/v1` with `attestations: true` and `repository-url` set for testpypi, `softprops/action-gh-release@v2` with `prerelease` set per tag pattern
      - top-of-file comment: "Filename `workflow.yml` is bound to the PyPI Trusted Publisher config for `lingo-loop`. Do NOT rename without simultaneously updating the PyPI publisher entry."
      — split into two publish jobs (`publish-pypi` / `publish-testpypi`) gated on `needs.build.outputs.environment` since GH Environments cannot be set via expression on a single job.
- [x] 9.7 Update `RELEASING.md`:
      - replace §Automation roadmap with §Automated procedure (push tag → watch Actions → verify PyPI + GH Release)
      - move existing manual procedure under §Break-glass (kept for offline / GH Actions outage)
      - cross-link to `pre-release-checks`, `release-cut`, `release-tag` skills
- [ ] 9.8 Dry-run: tag `v0.1.0-rc.1` after rename-lingo-loop has landed (if applicable) or against current package name if rc'ing before rename. Confirm: workflow runs, artifacts land on test.pypi.org, GH Release marked prerelease, attestations attached. If `invalid-publisher` error: filename/env/repo mismatch — fix PyPI publisher config OR workflow file, retag.
- [ ] 9.9 First production release: cut `v0.1.0` tag via `release-tag` skill (after `release-cut` PR merged). Confirm publish to pypi.org under `lingo-loop` name (pending publisher auto-promotes to active on first success).
- [ ] 9.10 Verify in `gh secret list` that no `PYPI_API_TOKEN` / `PYPI_TOKEN` / `TWINE_PASSWORD` secret exists. Trusted Publishing only.

## 10. Release-management skills (folded in 2026-05-25)

**Authoring constraint**: every skill in this section MUST be created by a dispatched subagent using the local `writing-skills` helper at `/Users/artem.veduta/.claude/plugins/cache/claude-plugins-official/superpowers/5.1.0/skills/writing-skills` (per repo CLAUDE.md). Main thread MUST NOT edit `SKILL.md` files directly. Each subagent receives: the skill's design subsection from design §12, target path `.claude/skills/<name>/SKILL.md`, and shared script paths from §9.

- [x] 10.1 Dispatch subagent to author `.claude/skills/pre-release-checks/SKILL.md` per design §12 "pre-release-checks". Invokes `scripts/build-check.sh`. Reports PASS/FAIL table only; does not mutate repo. — authored via subagent + writing-skills helper; skill loaded in session.
- [x] 10.2 Dispatch subagent to author `.claude/skills/release-cut/SKILL.md` per design §12 "release-cut". Invokes `scripts/changelog-promote.sh`. Stops after PR creation; outputs PR URL and "next: `/release-tag X.Y.Z` after merge". — authored via subagent; skill loaded.
- [x] 10.3 Dispatch subagent to author `.claude/skills/release-tag/SKILL.md` per design §12 "release-tag". Invokes `scripts/version-guard.sh`. Refuses if release PR not merged. Hands off to workflow.yml after `git push origin vX.Y.Z`. — authored via subagent; skill loaded.
- [x] 10.4 Dispatch subagent to author `.claude/skills/hotfix/SKILL.md` per design §12 "hotfix". Branches off latest production tag (excludes `-rc*`). On merge, hands off to `release-cut` with patch bump. — authored via subagent; skill loaded.
- [x] 10.5 Dispatch subagent to author `.claude/skills/feature-flow/SKILL.md` per design §12 "feature-flow". Thin orchestrator over `openspec-propose` → branch → `openspec-apply` → verify → PR → `openspec-archive`. MUST NOT reimplement openspec-* judgment. — authored via subagent; skill loaded.
- [x] 10.6 Add `.claude/skills/README.md` (one paragraph + table) listing the five skills and when to call each. Cross-link from `RELEASING.md` §Automated procedure and `CONTRIBUTING.md` §Feature flow. — README added; RELEASING.md §Automated procedure and CONTRIBUTING.md §Feature flow cross-link to it.
- [x] 10.7 Add §Feature flow to `CONTRIBUTING.md` pointing contributors at `/feature <slug>` as the canonical entry point for non-trivial work. — section inserted after §OpenSpec workflow.
- [x] 10.8 Verify each `SKILL.md` frontmatter declares `name`, `description` (with natural-language phrase for auto-invoke), and that `/<name>` slash invocation works in this session. — all 5 SKILL.md files have `name` + `description` with auto-invoke phrases; all 5 visible in Claude Code's loaded skill list this session (`pre-release-checks`, `release-cut`, `release-tag`, `hotfix`, `feature-flow`).
- [x] 10.9 Verify release skills after sections 9 and 10 land; final OpenSpec validation runs after Section 11 too. — sections 9 + 10 landed; `openspec validate oss-baseline --strict` → `Change 'oss-baseline' is valid`. Final re-run deferred to 11.11.

## 11. Interactive provider installer (`tutor init`)

**Scope guard**: this section may edit the CLI/distribution installer surface only. Do not change pedagogy, SRS, feedback, learner profile/history schemas, lifecycle persistence, or tutor skill behavior.

- [x] 11.1 Add installer contracts to schemas and JSON-schema mirror output: `InitRequest`, `InitPlan`, `ProviderStatus`, `ProviderInstallAction`, and `InitResult`.
- [x] 11.2 Add a provider-installer Protocol and registry that derives supported providers from `language_tutor.adapters.base.supported_host_targets()` (Claude, Codex, Hermes, OpenClaw only; antigravity remains rejected).
- [x] 11.3 Implement provider detection with fakeable filesystem/command-runner seams: CLI presence, conventional config roots, existing managed files, blocked/unknown states.
- [x] 11.4 Implement provider planning/apply/verify modules for Claude, Codex, Hermes, and OpenClaw using the host setup profiles as source of truth; all writes are idempotent and limited to managed plugin/profile files.
- [x] 11.5 Add `tutor init` CLI with Click prompts and status output; support `--provider <id>` repeated, `--yes`, `--dry-run`, and `--json`.
- [x] 11.6 Add non-interactive safety: if stdin is not a TTY and writes are required, fail unless `--provider` and `--yes` are supplied.
- [x] 11.7 Add privacy guard tests proving `tutor init` never writes learner profile YAML, SQLite history, sessions, checkpoints, memories, logs, or secrets.
- [x] 11.8 Add CLI tests for interactive defaults, selected providers, multi-provider install, dry-run JSON, blocked host, invalid provider, and second-run idempotence.
- [x] 11.9 Update README and `docs/install/{claude,codex,hermes,openclaw}.md` so the primary install path is package install → `tutor init`, with manual host commands retained as fallback.
- [x] 11.10 Run `ruff check .`, `pyright`, and `pytest` after installer implementation.
- [x] 11.11 Run `openspec validate oss-baseline --strict`; fix any errors.

## Notes
- Application code changes are allowed only for Section 11 installer/CLI contracts. If any task drifts into pedagogy, SRS, feedback, lifecycle persistence, or learner data schemas, stop and escalate.
- Assets (screenshots, asciinema casts) may ship as placeholders to unblock merge, but every placeholder must be a tracked task (8.4).
- **Implementation dispatch**: execute tasks via parallel subagents, one subagent per section (Section 1 legal, Section 2 license sync, Section 3 pyproject, Section 4 README, Section 5 docs, Section 6 .github, Section 6a branching/commits/release). Sections are independent once Section 0 prerequisites land. Section 7 verification runs sequentially after all batches return. Each subagent gets the section's task list + relevant spec/design pointers and reports back with file diffs + checklist of completed tasks.
