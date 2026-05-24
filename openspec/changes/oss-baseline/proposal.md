# Change: oss-baseline

## Status
Proposed — 2026-05-24

## Summary
Prepare the `language-tutor` repository for public open-source release on GitHub by adding the legal, contributor, and discoverability artifacts that signal a serious OSS project, and by restructuring the README so a non-developer language learner can install and run the tutor inside their AI host without reading source code.

This change is mostly **docs and config**, but now also bundles **PyPI publish automation** (tag-triggered workflow via Trusted Publishing / OIDC), **five release-management skills** (`pre-release-checks`, `release-cut`, `release-tag`, `hotfix`, `feature-flow`) under `.claude/skills/`, and a narrow **interactive provider installer** (`tutor init`) for Claude, Codex, Hermes, and OpenClaw. The previously planned standalone `publish-pypi` and `interactive-installer` changes are folded into this distribution baseline so a first-time user gets one clear path from install to host wiring.

## Motivation
The repository currently has functioning code, OpenSpec process, and per-host plugin manifests, but is missing every conventional OSS signal: no `LICENSE`, no `CONTRIBUTING.md`, no `SECURITY.md`, no `CODE_OF_CONDUCT.md`, no `.github/` (CI badges, issue/PR templates, dependabot), and the README is internally framed ("Spec 006 implements…") rather than user-framed.

Without these artifacts:
- License absence makes the project legally **unusable** by anyone — default copyright is "all rights reserved".
- Plugin manifests advertise `"license": "MIT"` while no `LICENSE` file exists — the claim is unenforceable without a matching `LICENSE` file at the repo root.
- Contributors cannot open issues or PRs in a structured way.
- `hermes-profile/distribution.yaml` declares `source_url: https://github.com/synesthesias/hermes` (wrong — points to upstream Hermes, not this repo).
- Language learners (the target audience) bounce off a README that opens with `rtk uv venv` and references internal spec numbers.

## Goals
1. Make the repository **legally usable** under MIT.
2. Make the README scannable for an end-user language learner: hook in the first screen, install in three commands, host-specific detail in `docs/`.
3. Provide contributor infrastructure (CONTRIBUTING, CoC, SECURITY, issue/PR templates, CI on PRs).
4. Establish per-host install documentation (`docs/install/<host>.md`) that honestly states the Python prerequisite and gives copy-paste install + verify + uninstall + troubleshooting blocks.
5. Fix existing OSS-correctness bugs (license field mismatches, wrong `source_url`).
6. Provide a provider-aware first-run installer: user installs the package, runs `tutor init`, sees detected hosts, selects one or more providers, and gets install/verify/repair output without reading source.

## Non-goals
- Installing host CLIs themselves (Claude Code, Codex, Hermes, OpenClaw) — the installer detects them and prints repair guidance.
- Collecting API keys or secrets — host credentials stay owned by each host.
- Standalone `curl | sh` bootstrapper — may be added later as a thin wrapper over `uv tool install lingo-loop && tutor init`.
- Module/CLI rename (`language_tutor` → `lingo_loop`) — deferred to `rename-lingo-loop` (sequenced before the first production PyPI tag; see §8.6).
- Standalone binaries (PyInstaller / shiv) — out of scope.
- Renaming the project, changing the package name, or breaking the existing CLI surface.
- Antigravity host support — remains out of scope per existing spec.
- Translating docs to other languages — English only for v0.1.
- Marketing launch (HN, Reddit, awesome-lists) — separate post-baseline activity.

## License Decision
**MIT** — chosen for:
- Permissive (maximum adoption among end-user learners and downstream forks).
- Brevity and ubiquity — universally recognized by GitHub, PyPI, and downstream tooling.
- Matches the license already declared by every existing plugin manifest, so adopting MIT aligns the `LICENSE` file with manifests instead of churning manifests.
- Compatible with permissive Apache-2.0 dependencies (including the `uv` install path used by `tutor init`).

Copyright line: `Copyright (c) 2026 Artem Veduta`.

All plugin manifests already say `"license": "MIT"`; no manifest changes required for license field.

## Project Rename
Repo + PyPI package renamed from `language-tutor` to **`lingo-loop`** as part of this change.
- GitHub: `artemVeduta/language-tutor` → `artemVeduta/lingo-loop` (GitHub auto-301s the old URL).
- PyPI: future package name `lingo-loop` (verified free: PyPI 404, npm 404, `artemVeduta/lingo-loop` 404; `github.com/lingo-loop` org/user is taken so future org migration to `lingo-loop/lingo-loop` is unavailable — personal repo path is fine).
- **Scope of rename is name-only** for this change: Python module remains `language_tutor`, CLI command remains `tutor`, internal imports unchanged. Full module/CLI rename deferred to follow-up change `rename-lingo-loop`, sequenced before the first production PyPI tag.
- Rationale: zero rename churn keeps this distribution change focused; downstream release work inherits the final public name without forcing a second rename later.

## Audience & Tone
Primary audience: **end-user language learners** who use Claude Code, Codex, Hermes, or OpenClaw as their AI assistant and want a structured tutor inside it. They are comfortable copy-pasting terminal commands but not reading Python source.

Secondary audience: contributors (developers extending hosts, fixing bugs).

README must serve audience #1. Contributor detail moves to `CONTRIBUTING.md` and `docs/`.

## Scope (Artifacts)

### Root files (new)
- `LICENSE` — verbatim MIT text (SPDX `MIT`, copyright holder: Artem Veduta).
- `CONTRIBUTING.md` — how to set up dev env, run tests (`uv pip install -e .[dev]`, `pytest`), open issues/PRs, branch naming, the OpenSpec proposal flow for non-trivial changes.
- `CODE_OF_CONDUCT.md` — Contributor Covenant v2.1 verbatim, with `veduta.artem20@gmail.com` as the enforcement contact.
- `SECURITY.md` — supported versions table, private vulnerability reporting via GitHub Security Advisories, response SLA (best-effort within 14 days for solo maintainer).
- `CHANGELOG.md` — Keep-a-Changelog format, seeded with `[Unreleased]` section.

### README rewrite
Replace current README with a learner-first structure:
1. Banner + one-line tagline ("Learn languages inside your AI coding assistant — local-first, no telemetry").
2. Badges row: license, Python version, CI status (placeholders OK until the first green run on `main`).
3. Demo asciinema cast (linked from `docs/assets/demo.cast`; cast file generation tracked in tasks, may ship empty placeholder in v0.1 if recording not ready).
4. **Why** section (3 bullets: local-first / no telemetry / works in your IDE).
5. **Features** (5–7 bullets, learner-facing language).
6. **Quick start** — Claude path only (most popular host), full happy path in ≤6 commands.
7. **Other hosts** — three lines linking to `docs/install/codex.md`, `docs/install/hermes.md`, `docs/install/openclaw.md`.
8. **How it works** — one ASCII diagram (host → skill → `tutor` CLI → SQLite/YAML).
9. **Privacy** — one paragraph.
10. **Roadmap** — bullet list pointing to GitHub Projects / Milestones.
11. **Contributing** — link to `CONTRIBUTING.md`.
12. **License** — MIT.

Internal jargon (Spec 006, Spec 007, `rtk`-prefixed commands) **removed from README**. `rtk` is a personal proxy — public users won't have it. All commands shown in public docs use plain `uv` / `pip` / host CLI invocations.

### docs/ tree (new)
```
docs/
├── install/
│   ├── claude.md
│   ├── codex.md
│   ├── hermes.md
│   └── openclaw.md
├── configuration.md
├── privacy.md
├── troubleshooting.md
└── architecture.md
```

Each `install/<host>.md` follows a consistent template:
1. Prerequisites box (Python 3.12+, host CLI installed).
2. Step 0 — install `tutor` CLI (`uv tool install lingo-loop` after the package is published; local preview uses `uv tool install .` from a clone).
3. Guided wiring via `tutor init`, followed by a host-specific manual fallback block.
4. Screenshot of host UI showing plugin enabled (PNG in `docs/assets/`).
5. asciinema cast of first session (`.cast` in `docs/assets/`).
6. Verify section.
7. Troubleshooting (3 most common errors + fix).
8. Uninstall.

Screenshots and casts may ship as placeholder TODOs in v0.1 if not yet captured; placeholders must be tracked tasks, not silent gaps.

### Interactive provider installer (new)

Add `tutor init` as the learner-facing setup entry point after package install:

```bash
uv tool install lingo-loop
tutor init
```

`tutor init` detects supported hosts, presents provider choices, installs only the selected host package/profile wiring, and runs a provider-specific verify step. It MUST be safe to rerun: existing installs are reported as `installed`, missing pieces as `needs-repair`, and unsupported hosts as `blocked` with a concrete next step.

Required modes:
- Interactive: `tutor init` shows a menu with Claude, Codex, Hermes, and OpenClaw.
- Non-interactive: `tutor init --provider claude --provider codex --yes`.
- Audit-only: `tutor init --dry-run --json` returns planned actions without writing files.
- Repair: rerunning the same command repairs missing managed files and never overwrites learner profile/history.

Architecture boundary: installer code may touch the CLI surface and a small distribution/provider-installer module only. Pedagogy, SRS, feedback, persistence schemas, and tutor skills remain unchanged.

### .github/ scaffold (new)
- `.github/workflows/ci.yml` — on push/PR to `main`: `ruff check` + `pyright` + `pytest` with coverage gate (matches existing `pyproject.toml` settings).
- `.github/ISSUE_TEMPLATE/bug_report.yml`
- `.github/ISSUE_TEMPLATE/feature_request.yml`
- `.github/ISSUE_TEMPLATE/config.yml` — disable blank issues, link to Discussions.
- `.github/PULL_REQUEST_TEMPLATE.md`
- `.github/dependabot.yml` — weekly `pip` and `github-actions` updates.
- `.github/FUNDING.yml` — optional, deferred decision; ship empty file with a comment listing supported keys.

### Release & workflow conventions (new)
- `RELEASING.md` at repo root — SemVer policy, CHANGELOG promotion ritual, `vX.Y.Z` annotated tag, `gh release create` step, post-release verification, authorized releaser.
- `CONTRIBUTING.md` extended with: **Branching model** (trunk-based, allowed prefixes `feature|fix|docs|chore|refactor|test`, short-lived, squash-merge), **Commit messages** (Conventional Commits 1.0, allowed types, ≤72-char subject, `!`/`BREAKING CHANGE:` for breaks).
- Branch protection on `main` (manual GitHub Settings): PR required, `ci` check required, linear history required, no force-push, no deletion.
- Automated release for v0.1 via `.github/workflows/workflow.yml`; manual `gh release create` remains only as a break-glass path in `RELEASING.md`.

### Fixes to existing files
- `.claude-plugin/plugin.json` — already `"license": "MIT"`; verify unchanged.
- `.codex-plugin/plugin.json` — already `"license": "MIT"`; verify unchanged.
- `openclaw-plugin/package.json` — already `"license": "MIT"`; verify unchanged.
- `hermes-profile/distribution.yaml`:
  - `license: see repository` → `license: MIT`.
  - `source_url: https://github.com/synesthesias/hermes` → `source_url: https://github.com/artemVeduta/lingo-loop`.
- `pyproject.toml`:
  - Add `license = { text = "MIT" }` (or SPDX `license = "MIT"` once hatchling supports PEP 639 in your version — see design).
  - Add `[project.urls]` block: Homepage, Source, Issues, Changelog.
  - Add `classifiers` (Python versions, license, intended audience, topic).
  - Add `keywords`.

## Out of Scope (explicit)
- No changes to pedagogy, SRS, feedback, lifecycle persistence, learner profile/history schemas, or tutor skill behavior.
- Application-code changes are limited to the `tutor init` distribution installer surface and tests.
- No changes to skill files under `skills/` (only documentation references them).
- No token-based PyPI publishing, manual wheel upload, or extra package registry beyond PyPI/TestPyPI.
- No README translations.

## Risks & Mitigations
| Risk | Mitigation |
|---|---|
| MIT lacks an explicit patent grant — future contributors might submit code touching patented techniques (audio/ML) | Acceptable for v0.1: scope is end-user language learning, dependencies (TTS/STT) handle patent terms upstream; revisit at first contribution involving novel processing; CONTRIBUTING.md adds DCO sign-off requirement to keep provenance clear. |
| README rewrite drops internal `rtk` and spec-number references that some maintainer workflows depend on | Preserve them in `AGENTS.md` / `CLAUDE.md` (maintainer-facing); public README is the only thing rewritten. |
| Screenshots and asciinema casts not ready at merge time | Allow placeholder markers (`<!-- TODO: cast -->`) in v0.1; track each placeholder as an explicit task; do not silently omit. |
| `docs/install/<host>.md` may go stale as host CLIs evolve | Add a "last verified" date line at the bottom of each install doc; refresh during each release. |
| Contributor Covenant designates a contact email — sets expectation of response | Solo maintainer; SECURITY.md and CoC both state "best-effort response within 14 days". |
| Wrong `hermes-profile` `source_url` may already be cached by users who installed before fix | Document in CHANGELOG under "Fixed"; users can re-run `hermes profile update`. |
| PyPI name `language-tutor` may already be squatted | Resolved: project renamed to `lingo-loop`; PyPI/npm/GitHub all free for repo path. Trusted Publishing uses the `lingo-loop` pending publisher. |
| `github.com/lingo-loop` user/org slug already taken | Personal repo path `artemVeduta/lingo-loop` is free and used; future migration to an org named `lingo-loop` is blocked. Acceptable for solo-maintainer v0.1; if an org is needed later, use a different org name (e.g. `lingoloop-dev`). |
| Inbound links to `language-tutor` after rename | GitHub auto-redirects renamed-repo URLs (HTTP 301) indefinitely; CHANGELOG notes the rename; old clones continue to work because `git` follows the redirect on fetch. |
| Provider installer damages user-owned state | `tutor init` only writes managed plugin/profile files and never writes learner YAML/SQLite history except by calling existing `doctor`/verify read paths. Dry-run JSON and idempotence tests cover this. |
| Provider CLIs differ across versions | Detection is best-effort and provider-specific; every blocked state includes a host install/update command and links to `docs/install/<host>.md`. |

## Open Questions (resolved 2026-05-24)
1. ~~PyPI name availability~~ — resolved: project renamed to `lingo-loop`; verified free on PyPI, npm, and `artemVeduta/lingo-loop`.
2. ~~FUNDING.yml~~ — resolved: ship empty file with commented examples.
3. ~~Discussions vs Issues~~ — resolved: enable GitHub Discussions; `ISSUE_TEMPLATE/config.yml` links to it.

## PyPI Automation (folded in 2026-05-25)

Tag-driven publish replaces step 5–7 of the manual `RELEASING.md` flow.

- **Workflow file**: `.github/workflows/workflow.yml` (filename bound to the PyPI Trusted Publisher registration for project `lingo-loop`; **must not** be renamed without simultaneously updating PyPI publisher config).
- **Trigger**: `push: tags: ['v*.*.*']` and `workflow_dispatch`.
- **Pipeline**:
  1. `build` job — checkout, `astral-sh/setup-uv`, version-guard (tag `vX.Y.Z` MUST equal `pyproject.toml` `[project].version`, else fail), `uv build`, upload sdist+wheel artifact.
  2. `publish` job — gated on `environment: pypi` (GitHub Environment), `id-token: write`, downloads artifact, calls `pypa/gh-action-pypi-publish@release/v1` with `attestations: true` (sigstore/SLSA provenance), then `softprops/action-gh-release@v2` to create the GitHub Release with notes from tag and the dist files attached.
  3. `testpypi` route — when tag matches `-rc.N` or `-alpha.N`, `publish` job targets `repository-url: https://test.pypi.org/legacy/` against environment `testpypi` and marks the GitHub Release as prerelease.
- **PyPI side (manual, one-time)**: `lingo-loop` is registered as a **pending publisher** on PyPI (and TestPyPI) bound to `artemVeduta/lingo-loop`, workflow filename `workflow.yml`, environment `pypi` (resp. `testpypi`). First successful publish promotes pending → active publisher.
- **Manual fallback**: `RELEASING.md` keeps the manual `gh release create` path under a §Break-glass section for use when the workflow is unavailable.

## Release-management Skills (folded in 2026-05-25)

Five project-local skills under `.claude/skills/<name>/SKILL.md`. Ship with the repo so contributors get them. Triggered by both slash commands (e.g. `/release-cut`) and natural-language description matching.

| Skill | Trigger | Stops at |
|---|---|---|
| `pre-release-checks` | `/pre-release [version]` | PASS/FAIL table; blockers must clear before `release-cut` |
| `release-cut` | `/release-cut X.Y.Z` (prereq: pre-release passed) | PR URL; human reviews + merges |
| `release-tag` | `/release-tag X.Y.Z` (prereq: PR merged) | Tag pushed; GitHub Actions takes over (auto-publish via workflow.yml) |
| `hotfix` | `/hotfix <bug-ref>` | Hotfix PR URL; on merge, hand off to `release-cut` with patch bump |
| `feature-flow` | `/feature <slug> "<intent>"` | Feature PR URL; on merge, hand off to `openspec-archive` |

Boundary rules:
- Skills assume the **automated** PyPI workflow exists. Manual fallback lives in `RELEASING.md`, not in skills (avoids dual-mode branching).
- Skills invoke pure-mechanics helpers in `scripts/` (`version-guard.sh`, `changelog-promote.sh`, `build-check.sh`) rather than reimplementing shell logic in markdown.
- `feature-flow` is a thin orchestrator that calls existing `openspec-propose` / `openspec-apply` / `openspec-archive` skills — it does NOT reimplement their judgment.
- Each skill is authored by a dispatched subagent using the local `writing-skills` helper at `/Users/artem.veduta/.claude/plugins/cache/claude-plugins-official/superpowers/5.1.0/skills/writing-skills` (per repo CLAUDE.md constraint).

## Success Criteria
- `LICENSE` exists at repo root, contains verbatim MIT text with correct copyright year and holder.
- All plugin manifests, `hermes-profile/distribution.yaml`, and `pyproject.toml` declare `MIT`.
- README opens with a one-line pitch, not an install command; contains a working Claude quick-start block.
- A first-time visitor can navigate from README to `docs/install/<host>.md` for their host of choice without reading source.
- `gh repo view` shows License, Topics, and Description populated.
- CI runs lint + typecheck + tests on every PR.
- No reference to internal `rtk` or "Spec NNN" in any file under `docs/` or in `README.md`.
- `openspec validate oss-baseline --strict` passes.
- `.github/workflows/workflow.yml` exists, triggers on `v*.*.*` tag, publishes via OIDC (no PyPI token secret).
- TestPyPI dry-run with `v0.1.0-rc.1` (or later rc) tag succeeds end-to-end before any production tag is cut.
- All five skills exist under `.claude/skills/<name>/SKILL.md`, each authored via subagent + `writing-skills` helper.
- `RELEASING.md` references the automated flow as primary and keeps the manual flow under §Break-glass.
- `tutor init` supports interactive provider selection plus `--provider`, `--yes`, `--dry-run`, and `--json`; it installs/verifies selected host wiring idempotently for Claude, Codex, Hermes, and OpenClaw.
