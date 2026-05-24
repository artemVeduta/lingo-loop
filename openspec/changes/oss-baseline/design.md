# Design: oss-baseline

## Context
This change is the foundation layer of the OSS-release sequence. It is primarily legal artifacts, contributor docs, README restructure, GitHub scaffolding, release automation, and manifest correctness fixes. It also includes one narrow user-facing distribution behavior: `tutor init`, an interactive provider installer that wires the already-supported host packages/profiles for Claude, Codex, Hermes, and OpenClaw. Pedagogy, persistence, SRS, feedback, and tutor skills remain unchanged.

The repository today has a working Python CLI (`tutor`), four host plugin/profile packages (Claude, Codex, Hermes, OpenClaw), and an internal-facing README that assumes the reader is a contributor running `rtk`-prefixed proxy commands. We are flipping the framing to public end-user language learners while keeping the maintainer-facing material (`AGENTS.md`, `CLAUDE.md`, `CLAUDE.copy.md`, internal spec numbers) intact for ongoing development.

## Goals (recap)
Legally usable repo, learner-first README, contributor infrastructure, per-host install docs, manifest correctness fixes.

## Non-goals (recap)
Installing host CLIs, collecting API keys, standalone binaries, full module rename, antigravity support, doc translations, marketing launch, and any pedagogy/data-model changes.

---

## 0. Project Rename (`language-tutor` → `lingo-loop`)

**Scope of rename in this change = name-only**:
- GitHub repo: `artemVeduta/language-tutor` → `artemVeduta/lingo-loop` (GitHub 301-redirects the old URL).
- PyPI distribution name: `lingo-loop`.
- Python module name (`language_tutor`), CLI entry point (`tutor`), and all internal imports are **unchanged** to keep the rename itself name-only in this change.

A separate follow-up change, **`rename-lingo-loop`**, will execute the full code-level rename (module `language_tutor` → `lingo_loop`, CLI command, manifest `name` fields, skill references). It is sequenced **after** `oss-baseline` and **before the first production PyPI tag**, so the first production publish happens under the final module name.

Availability check (2026-05-24):
- PyPI `lingo-loop`: 404 (free).
- npm `lingo-loop`: 404 (free).
- `github.com/artemVeduta/lingo-loop`: 404 (free).
- `github.com/lingo-loop` (user/org slug): 200 (taken — blocks a future `lingo-loop/lingo-loop` org migration; acceptable for solo-maintainer v0.1).

All references in this change (README, install docs, `pyproject.toml` URLs, `hermes-profile/distribution.yaml` `source_url`, CHANGELOG, `.github/`) use the new name. References to the Python module remain `language_tutor` until `rename-lingo-loop` lands.

## 1. License Selection Rationale

**Decision: MIT.**

| Candidate | For | Against | Verdict |
|---|---|---|---|
| **MIT** | Maximum brevity, universally recognized, matches the license already declared by every existing plugin manifest, no NOTICE file required | No explicit patent grant | **Accept.** Patent risk for an end-user language tutor wrapping upstream TTS/STT libraries is low; provenance handled via DCO sign-off in CONTRIBUTING.md. |
| Apache-2.0 | Explicit patent grant, ecosystem-standard in modern Python AI tooling (`uv`, `ruff`, `vllm`) | Longer header, NOTICE file convention, would require flipping the three plugin manifests that already say MIT | Reject — patent grant benefit does not outweigh churn and added complexity for a v0.1 distribution baseline. |
| GPL-3.0 / AGPL-3.0 | Strong copyleft, SaaS-safe (AGPL) | Scares corporate adopters, blocks plugin embedding in proprietary hosts (Claude Code, Codex are commercial) | Reject — adopters live in commercial host ecosystems. |
| MPL-2.0 | File-level copyleft | Uncommon in Python CLI tooling, mental overhead | Reject. |

MIT also matches the spirit of "local-first, no telemetry, user-owned data" — minimal friction for end users and downstream forks, no contributor agreement overhead.

### Manifest license field synchronization
Plugin manifests already declare `MIT`; the gap is the missing `LICENSE` file at the repo root and `hermes-profile/distribution.yaml` (`license: see repository`). After this change, **every license declaration in the repo must read `MIT`**. Audit list:
- `LICENSE` (new file).
- `pyproject.toml` `[project.license]`.
- `.claude-plugin/plugin.json` `"license"` (already MIT — verify).
- `.codex-plugin/plugin.json` `"license"` (already MIT — verify).
- `openclaw-plugin/package.json` `"license"` (already MIT — verify).
- `hermes-profile/distribution.yaml` `license:` (change from `see repository` to `MIT`).

No NOTICE file required for MIT.

Copyright line (single-year, per maintainer decision 2026-05-24): `Copyright (c) 2026 Artem Veduta`.

### `pyproject.toml` license syntax
Hatchling supports both:
- Legacy: `license = { text = "MIT" }`
- PEP 639 (SPDX): `license = "MIT"` (requires hatchling ≥1.26 + setuptools-PEP-639 tooling chain).

Pin: use legacy `license = { text = "MIT" }` to avoid forcing a hatchling upgrade in this distribution baseline. PEP 639 migration is a later packaging cleanup.

---

## 2. README Restructure

### Why rewrite, not patch
Current README mixes three audiences (maintainer running `rtk`, contributor reading spec numbers, end user installing the tool) and prioritizes the wrong one for OSS. Patching in place would require deleting more than half the file anyway; a clean rewrite is shorter than a defensible diff.

### Structural decisions

**Section order is load-bearing.** The order optimizes the "5-second decision" a GitHub visitor makes:

```
SECOND     VISITOR LEARNS                        FROM SECTION
─────      ──────────────                        ────────────
1          What it is                            Tagline
2          Whether to trust it                   Badges (license, CI, py version)
3          What it looks like                    Demo cast
4          Why it exists                         Why (3 bullets)
5          Whether features match their need     Features (5–7 bullets)
6          How to start                          Quick start (Claude)
7+         Anything deeper                       Links into docs/
```

Quick start uses Claude only because forcing learners to compare four install paths before they've tried anything causes paralysis. Other hosts get one-line links; their full flow lives in `docs/install/`.

### Internal references removal
Strip from README and all `docs/`:
- `rtk` prefix on any command (replace with bare command or `uv`).
- "Spec 006", "Spec 007", "spec NNN" references.
- Internal subagent names ("implementation subagent owned by...").

Preserve in `AGENTS.md`, `CLAUDE.md`, `CLAUDE.copy.md` (maintainer-facing).

### ASCII architecture diagram
Embed one diagram in the "How it works" section:

```
┌──────────────┐       ┌────────────────┐       ┌─────────────────┐
│  AI Host     │──────▶│  Tutor skill   │──────▶│  tutor CLI      │
│  (Claude/    │       │  (markdown +   │       │  (Python)       │
│  Codex/...)  │       │  prompts)      │       │                 │
└──────────────┘       └────────────────┘       └─────────────────┘
                                                          │
                                          ┌───────────────┼────────────────┐
                                          ▼               ▼                ▼
                                   ┌──────────┐   ┌──────────────┐   ┌─────────┐
                                   │ profile  │   │  learning    │   │  data/  │
                                   │  YAML    │   │   SQLite     │   │ defaults│
                                   └──────────┘   └──────────────┘   └─────────┘

       All state local. No network calls except the host's own LLM API.
```

---

## 3. `docs/install/<host>.md` Template

A consistent template across the four host docs reduces maintenance and lets us spot drift. Template sections, in order:

```
# Install Lingo Loop for <Host>

> Last verified: YYYY-MM-DD against <Host> version X.Y

## Prerequisites
- Python 3.12+
- <Host> CLI installed
- (host-specific extras, e.g. ANTHROPIC_API_KEY for Hermes)

## Step 0 — Install the tutor CLI
```bash
uv tool install lingo-loop   # local preview before publish: `uv tool install .`
tutor doctor --json
```

## Install the <Host> plugin
[copy-paste block]

## Screenshot
![<host> plugins panel showing language-tutor enabled](../assets/<host>-plugin-enabled.png)

## First session
[asciinema embed]

## Verify
[what the user should see]

## Troubleshooting
### Error: <common message>
**Cause:** ...
**Fix:** ...
(× 3 errors)

## Uninstall
[copy-paste block]
```

### Placeholder convention
If a screenshot or cast is not ready at merge time:

```markdown
<!-- TODO(oss-baseline-assets): capture screenshot of <host> plugins panel -->
*(Screenshot pending — see issue #NN)*
```

Every placeholder must have a corresponding tracked task in `tasks.md` and a follow-up GitHub issue once the repo is public.

### Mix of media (per user decision: "mix")
- **Screenshots (PNG)** for host UI states: Claude `/plugin` menu, Codex marketplace pane, Hermes profile listing, OpenClaw plugins panel.
- **asciinema casts (.cast)** for CLI flows: `tutor doctor`, `tutor setup write`, first reading/lesson session.
- Casts ship as static `.cast` files in `docs/assets/`; rendering is done client-side by GitHub's asciinema-player widget or via an `<a href>` link to asciinema.org if we choose to upload.

Decision for v0.1: store casts in-repo (no asciinema.org dependency), link to a player page once we have GitHub Pages set up in a later docs-site change. **GitHub README strips JavaScript**, so the asciinema-player widget will not render inline; ship a static **GIF** rendered from the `.cast` (via `agg` or `asciinema-agg`) as the in-README visual, with a link to the raw `.cast` for users who want to replay interactively.

---

## 4. CONTRIBUTING.md Structure

Sections:
1. **Project status** — solo maintainer, response time best-effort 14 days.
2. **Dev setup** — `uv venv && uv pip install -e ".[dev]"`, `pytest`, `ruff check`, `pyright`.
3. **OpenSpec workflow** — non-trivial changes go through a proposal under `openspec/changes/<name>/`. Link to `openspec-propose` skill description.
4. **Branch naming** — `feature/<short>`, `fix/<short>`, `docs/<short>`.
5. **Commit conventions** — Conventional Commits (matches existing history: `feat(scope): ...`, `fix(scope): ...`).
6. **PR checklist** — tests pass, lint clean, OpenSpec proposal exists for non-trivial changes, README/docs updated.
7. **Code of Conduct** — link.

Keep brief. Contributors who need more detail can read existing `openspec/changes/archive/`.

---

## 5. SECURITY.md Structure

Single page:
- **Supported versions** — `0.x` currently; once `1.0` ships, last two minor lines.
- **Reporting** — use GitHub Security Advisories ("Report a vulnerability" button on Security tab). Do not open public issues for vulnerabilities.
- **Response** — best-effort acknowledgment within 14 days.
- **Scope** — what's in scope (the `tutor` CLI, the four host plugins as shipped) and out of scope (the host CLIs themselves, user-supplied LLM API keys).
- **Disclosure** — coordinated disclosure, fix-then-publish.

---

## 6. .github/ Scaffold

### Workflows

`ci.yml`:
- Triggers: `push` to `main`, `pull_request` to `main`.
- Matrix: Python 3.12 (3.13 added later when fully supported by deps).
- Steps: checkout → setup-uv → `uv sync --all-extras` → `ruff check .` → `pyright` → `pytest`.
- Coverage gate already enforced via `pyproject.toml addopts = "--cov-fail-under=80"`; CI inherits.

Publish workflow lives in `.github/workflows/workflow.yml` (Section 11). CI for pull requests stays separate in `.github/workflows/ci.yml`.

### Issue templates

`bug_report.yml` (form schema): host (Claude/Codex/Hermes/OpenClaw/other), version of `tutor`, version of host, OS, expected behavior, actual behavior, reproduction steps, logs.

`feature_request.yml`: problem, proposed solution, alternatives considered, host(s) affected.

`config.yml`:
```yaml
blank_issues_enabled: false
contact_links:
  - name: Discussion / Question
    url: https://github.com/artemVeduta/lingo-loop/discussions
    about: Ask a question or start a discussion.
```

(Discussions must be enabled in repo settings — manual step, captured in tasks.md.)

### PR template
- Summary
- Linked issue / OpenSpec change
- Test plan
- Screenshots (if UI/docs)
- Checklist (tests, lint, docs, CHANGELOG)

### Dependabot
Weekly cadence for `pip` and `github-actions`. Group minor/patch updates to reduce PR noise.

### FUNDING.yml
Per open question — ship empty file with commented examples:
```yaml
# github: [artemVeduta]
# ko_fi: ...
# custom: ...
```
Avoids cluttering the repo with a "Sponsor" button before any sponsor target exists, while making it trivial to enable later.

---

## 7. CHANGELOG.md Seed

Keep-a-Changelog format. Initial content:

```markdown
# Changelog

All notable changes to this project will be documented in this file.
The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- MIT LICENSE file.
- CONTRIBUTING.md, SECURITY.md, CODE_OF_CONDUCT.md.
- Per-host install documentation under `docs/install/`.
- `.github/` scaffold: CI workflow, issue/PR templates, dependabot.

### Changed
- README restructured for end-user language learners (was contributor-focused).
- License made explicit and consistent: MIT across LICENSE, `pyproject.toml`, plugin manifests (already MIT), and `hermes-profile/distribution.yaml` (was `see repository`).

### Fixed
- `hermes-profile/distribution.yaml` `source_url` corrected from upstream Hermes URL to this repository's URL.
```

---

## 7a. Branching Model, Commits, Release Procedure

### Branching: trunk-based
Single long-lived branch (`main`). Short-lived working branches off `main` with typed prefixes (`feature/`, `fix/`, `docs/`, `chore/`, `refactor/`, `test/`), squash-merged back. No `develop`, no `release/*`, no `hotfix/*` — solo maintainer with a single supported line (`0.x` per SECURITY.md) does not justify GitFlow overhead. Matches existing repository behavior (current branch `feature/oss-distribution`).

### Commit messages: Conventional Commits + DCO
Subject pattern: `^(feat|fix|docs|chore|refactor|test|build|ci|perf|style|revert)(\([a-z0-9-]+\))?!?: .+`, ≤72 chars. Breaking changes marked with `!` after the type/scope or via a `BREAKING CHANGE:` footer. Body explains *why*, not *what*. DCO `Signed-off-by:` trailer required on every commit; enforced socially in v0.1 (CONTRIBUTING.md guidance + PR review). Programmatic DCO check via GitHub App is deferred to later repository-hardening work.

Rationale: matches existing git history (`feat(scope): ...`, `fix(scope): ...`), unlocks future `git-cliff`/`release-please`-style CHANGELOG generation without re-writing history.

### Branch protection on `main`
Required settings (configured via GitHub Settings → Branches):
- `required_pull_request_reviews`: enabled (review count = 0 for solo maintainer, but PR is still required — prevents accidental direct push)
- `required_status_checks.contexts`: includes `ci`
- `required_linear_history`: `true` (squash or rebase only, no merge commits — keeps `git log` readable, simplifies future changelog tooling)
- `allow_force_pushes`: `false`
- `allow_deletions`: `false`

Solo-maintainer note: GitHub enforces these against the maintainer too only if "Do not allow bypassing the above settings" is checked. Recommend leaving bypass enabled for the maintainer in v0.1 (escape hatch for emergencies), disable once a second contributor exists.

### Release procedure: automated primary, manual break-glass

```
RELEASE FLOW (v0.1, automated)
───────────────────────────────────────────────
  1. open release branch `chore/release-0.1.0`
  2. promote CHANGELOG:
       [Unreleased]  →  [0.1.0] - YYYY-MM-DD
       insert new empty [Unreleased] on top
  3. bump pyproject.toml version (if not auto-derived)
  4. PR → squash-merge to main → CI green
  5. on main, cut annotated tag:
       git tag -a v0.1.0 -m "release 0.1.0"
       git push origin v0.1.0
  6. GitHub Actions workflow.yml publishes to PyPI via OIDC
  7. verify: PyPI page, GitHub Release, artifacts, attestations
```

Manual `gh release create` remains documented only under `RELEASING.md` §Break-glass for GitHub Actions outage or PyPI incident. See §11.

### Versioning: SemVer 2.0
- `0.x.y` permits breaking changes between minors (SemVer §4). Set expectations in `CHANGELOG.md` and `RELEASING.md`.
- First tag: `v0.1.0`, cut on the merge commit of `oss-baseline`.
- Pre-releases use `-rc.N` / `-alpha.N` suffixes when needed (`v0.2.0-rc.1`).

### `RELEASING.md` placement
Root-level, alongside `CONTRIBUTING.md` / `SECURITY.md` / `CODE_OF_CONDUCT.md`. Discoverable via GitHub's repo-root file listing; matches OSS convention (Kubernetes, Rust, Node.js all use root `RELEASING.md`/`RELEASE.md`).

---

## 8. Risk Analysis

### License clarification risk
Plugin manifests advertise MIT, but no LICENSE file exists, so legally the project is "all rights reserved" today. Adopting MIT formally aligns the repo with the manifests' existing claim — **strictly more permissive** than the de-facto current state. There are no public downstream consumers (pre-OSS-launch). Risk: zero practical, zero legal.

### Patent grant absence (MIT-specific)
MIT does not include an explicit patent grant the way Apache-2.0 does. For a v0.1 language-tutor wrapping upstream TTS/STT libraries and prompting LLM hosts, real-world patent risk is low — patented techniques live in upstream dependencies whose own licenses govern them. Mitigation: require DCO sign-off in `CONTRIBUTING.md` so contributor provenance is auditable; revisit license choice if a future contribution introduces novel processing techniques.

### Documentation drift risk
Per-host install docs reference host CLI behaviors that evolve faster than our release cadence. Mitigation: "Last verified: YYYY-MM-DD" header on each install doc; refresh during each release; add a CI check in a later change that warns if any install doc has a `Last verified` date older than 90 days.

### Placeholder asset risk
Shipping README with placeholder screenshots/casts looks unprofessional. Mitigation: every placeholder is a tracked task in `tasks.md`; the change is mergeable with placeholders but the OSS launch announcement is gated on placeholders being filled. Captured as a launch checklist, not in this change.

### Internal jargon leakage risk
`rtk`-prefixed commands, `Spec 006`, etc. could leak back into public docs during future edits. Mitigation: add or keep a one-line CI/doc check that greps README and public `docs/` for `rtk ` and `Spec [0-9]` and fails the build.

### PyPI name squat risk
Resolved by the `lingo-loop` rename. PyPI, npm, and the personal GitHub repo path were verified free; production publish uses the `lingo-loop` Trusted Publisher registration.

---

## 9. Cross-change Sequencing

```
oss-baseline  ─▶  rename-lingo-loop  ─▶  release candidate
   (this)         (module rename)        (TestPyPI dry-run)
```

Why this order:

- **oss-baseline first**: legal artifacts, release automation, and the `tutor init` provider installer must exist before the project is public. PyPI publish to a no-LICENSE repo is malpractice; an OSS launch without a guided install path makes every host doc carry too much setup burden.
- **rename-lingo-loop second**: module `language_tutor` → `lingo_loop`, CLI entry-point, plugin manifest `name`. Sequenced before any production PyPI tag so the first published artifact ships under the final module name. Pre-release `-rc.N` tags in this change publish to TestPyPI only (no production name burn).
- **release candidate third**: after the rename lands, `v0.1.0-rc.1` proves TestPyPI publishing and the end-to-end `uv tool install lingo-loop && tutor init` path before production.

This change explicitly does NOT ship unrelated features just because the installer exists. `tutor init` wires provider packages/profiles only; it does not install host CLIs, manage API keys, change lesson behavior, or create a GUI.

---

## 10. Acceptance Conditions

- `LICENSE` file present, byte-identical to MIT canonical text with `Copyright (c) 2026 Artem Veduta`.
- All six license declarations agree on `MIT`.
- README first 30 lines contain no `rtk`, no "Spec", no internal subagent names.
- `docs/install/{claude,codex,hermes,openclaw}.md` exist with the agreed template, all sections present (placeholders allowed for assets only).
- `tutor init` exists, lists Claude/Codex/Hermes/OpenClaw, supports interactive selection, supports `--provider`, `--yes`, `--dry-run`, and `--json`, and is idempotent across reruns.
- `.github/workflows/ci.yml` runs on PR open and exits 0 on a clean main.
- `CONTRIBUTING.md` (including DCO sign-off section), `SECURITY.md`, `CODE_OF_CONDUCT.md`, `CHANGELOG.md` exist.
- `hermes-profile/distribution.yaml` `source_url` points to `https://github.com/artemVeduta/lingo-loop`.
- `pyproject.toml` declares MIT, urls (pointing at `lingo-loop`), classifiers (including `Topic :: Education :: Computer Aided Instruction (CAI)`), keywords.
- Current test coverage measured (`pytest --cov`) and confirmed ≥ `pyproject.toml`'s `--cov-fail-under=80` gate; if below, gate temporarily lowered with tracked debt and an issue link.
- GitHub repo renamed to `lingo-loop`; old URL returns 301.
- `openspec validate oss-baseline --strict` passes.

---

## 11. PyPI Publish Automation (`workflow.yml`)

### Why folded in here, not deferred

Manual `gh release create` is a foot-gun: easy to push a tag without a matching CHANGELOG, easy to forget `uv build` artifacts, easy to leak a PyPI API token. Trusted Publishing eliminates the token entirely. Folding the workflow into `oss-baseline` means the very first tag (`v0.1.0`) ships through the automated path — no transitional "manual for v0.1, automated later" phase where the runbook diverges from reality.

### Filename constraint (critical)

The workflow file MUST be `.github/workflows/workflow.yml`. PyPI's pending-publisher entry for project `lingo-loop` (registered 2026-05-25) is bound to that exact filename. Renaming the file silently breaks OIDC token verification (`invalid-publisher` error). A header comment in the file documents the binding:

```yaml
# PyPI release workflow.
# Filename `workflow.yml` is bound to the PyPI Trusted Publisher
# config for `lingo-loop`. Do NOT rename without simultaneously
# updating the PyPI publisher entry (Manage → Publishing).
```

### Architecture

```
TAG PUSH (v*.*.*)            workflow_dispatch (manual)
        │                              │
        └──────────────┬───────────────┘
                       ▼
              ┌────────────────┐
              │   build job    │  ubuntu-latest, no env gate
              │                │  - checkout
              │                │  - setup-uv
              │                │  - version-guard.sh
              │                │  - uv build
              │                │  - upload-artifact (dist/)
              └────────┬───────┘
                       ▼
            ┌──────────────────────┐
            │  pick environment    │  rc tag → testpypi
            │  (job conditional)   │  final  → pypi
            └──────────┬───────────┘
                       ▼
              ┌────────────────┐
              │  publish job   │  environment: {pypi | testpypi}
              │                │  permissions: id-token: write,
              │                │               contents: write
              │                │  - download-artifact
              │                │  - pypa/gh-action-pypi-publish
              │                │    (attestations: true,
              │                │     repository-url for testpypi)
              │                │  - softprops/action-gh-release
              │                │    (prerelease=true for rc)
              └────────────────┘
```

### Version-guard script

`scripts/version-guard.sh`:
```bash
#!/usr/bin/env bash
set -euo pipefail
TAG="${1:?usage: version-guard.sh <tag>}"
TAG_VER="${TAG#v}"
PYPROJ_VER=$(python -c "import tomllib,sys; print(tomllib.load(open('pyproject.toml','rb'))['project']['version'])")
if [[ "$TAG_VER" != "$PYPROJ_VER" ]]; then
  echo "::error::tag $TAG ($TAG_VER) != pyproject.toml version ($PYPROJ_VER)"
  exit 1
fi
```

Invoked in the build job before `uv build`. Cheap guard, prevents the classic "tagged v0.2.0 but pyproject still says 0.1.0" footgun.

### TestPyPI routing

Tags matching the regex `^v[0-9]+\.[0-9]+\.[0-9]+-(rc|alpha|beta)\.[0-9]+$` route to TestPyPI, else PyPI. Implemented as a job `if:` condition over `github.ref_name`. The TestPyPI environment is a separate GitHub Environment with its own pending publisher on test.pypi.org. Marks GitHub Release as `prerelease: true`.

This gives `v0.1.0-rc.1` as a free dry-run before any production publish — required by Success Criteria.

### Environments and approvers

Two GitHub Environments, both created manually (one-time):

| Env | Approvers | URL bound | Purpose |
|---|---|---|---|
| `pypi` | None for solo maintainer (add reviewer if/when contributors exist) | pypi.org | Production publish |
| `testpypi` | None | test.pypi.org | Dry-run / rc tags |

Environments give the publish job a separate secret/policy boundary even when empty. They also enable adding required-reviewer gates later without changing the workflow.

### Sigstore attestations

`pypa/gh-action-pypi-publish@release/v1` with `attestations: true` automatically generates and uploads sigstore/SLSA provenance attestations alongside the artifacts. Free downstream verification (`twine check`, `pip install --require-hashes`). No additional config.

### Failure modes and mitigations

| Failure | Cause | Mitigation |
|---|---|---|
| `invalid-publisher` from PyPI | workflow filename ≠ PyPI config, or repo/env mismatch | Filename comment in workflow.yml; environment names checked into workflow.yml; dry-run with rc tag catches this before prod |
| version-guard fails | tagger forgot to bump pyproject | Guard halts the build before publish; tag is harmless until pushed; user fixes pyproject, force-deletes tag, re-tags |
| `gh release create` step fails after publish succeeds | transient gh API | Publish step is idempotent under sigstore; rerun the publish job manually — PyPI rejects duplicate version upload, gh release step proceeds |
| TestPyPI rate limit | running many rc tags in burst | Use `workflow_dispatch` instead of tagging for repeat dry-runs |

### `RELEASING.md` rewrite

§Manual procedure becomes §Break-glass (kept for offline / GH-outage scenarios). New top-of-doc §Automated procedure documents: bump pyproject, promote CHANGELOG, PR-merge to main, push tag, watch Actions. §Automation roadmap section is removed (no longer roadmap, now reality).

---

## 12. Release-management Skills (`.claude/skills/<name>/SKILL.md`)

### Boundary: skill vs script vs hook

```
SKILL                          SCRIPT                         HOOK
──────────────────────────     ──────────────────────────     ─────────────────
multi-step, contextual,        deterministic, no judgment     event-triggered,
Claude reasons about each      pure shell logic, called       no Claude
step (which CHANGELOG          by skill OR by user            (pre-commit,
entries belong, what PR        directly                       on-save format)
body says, rc-vs-final, ...)
                               scripts/version-guard.sh       (not used here)
.claude/skills/release-cut/    scripts/changelog-promote.sh
.claude/skills/release-tag/    scripts/build-check.sh
.claude/skills/hotfix/
.claude/skills/feature-flow/
.claude/skills/pre-release-checks/
```

Skills call scripts for mechanics; never reimplement shell logic in markdown prose.

### Per-skill design

#### `pre-release-checks`
- Trigger: `/pre-release [version]` or phrase match ("before I cut a release").
- Inputs: optional version (defaults to "next patch from current pyproject").
- Checks (all must PASS to clear):
  - Working tree clean (`git status --porcelain` empty).
  - On `main`, up-to-date with `origin/main`.
  - `CHANGELOG.md` `[Unreleased]` has at least one non-empty subsection.
  - Tag `vX.Y.Z` does not already exist locally or remotely.
  - `uv build` succeeds; `twine check dist/*` passes.
  - Tests green (`pytest`), lint clean (`ruff check`), types clean (`pyright`).
  - Coverage ≥ pyproject `--cov-fail-under` gate.
- Output: PASS/FAIL table; on any FAIL, lists exact blocker + suggested fix.
- Does NOT mutate repo state.

#### `release-cut`
- Trigger: `/release-cut X.Y.Z` or "cut release X.Y.Z".
- Prereq (skill checks): `pre-release-checks` ran clean in this session, OR auto-invokes it.
- Steps:
  1. `git checkout -b chore/release-X.Y.Z`.
  2. `scripts/changelog-promote.sh X.Y.Z` (rename `[Unreleased]` → `[X.Y.Z] - YYYY-MM-DD`, insert empty `[Unreleased]` on top).
  3. Bump `pyproject.toml` `version` if not already X.Y.Z.
  4. Show diff for user confirmation (irreversible step boundary).
  5. `git commit -s -m "chore(release): X.Y.Z"` (DCO sign-off included).
  6. `git push -u origin chore/release-X.Y.Z`.
  7. `gh pr create --fill` (body templated from CHANGELOG entries of this version).
- Output: PR URL + next-step instruction ("after merge, run `/release-tag X.Y.Z`").

#### `release-tag`
- Trigger: `/release-tag X.Y.Z`.
- Prereq: release PR for X.Y.Z has merged to `main`.
- Steps:
  1. `git checkout main && git pull --ff-only`.
  2. `scripts/version-guard.sh vX.Y.Z` (sanity check pyproject matches).
  3. Confirm with user (irreversible: tag push triggers PyPI publish).
  4. `git tag -a vX.Y.Z -m "release X.Y.Z"` (uses `-s` if signing key available).
  5. `git push origin vX.Y.Z`.
  6. Print link to GitHub Actions run page (`gh run watch` if user wants live).
- Output: tag URL + actions URL.
- Does NOT wait for workflow completion; the GH Actions workflow.yml owns publish.

#### `hotfix`
- Trigger: `/hotfix <bug-ref>` (bug-ref = GH issue # or short slug).
- Prereq: working tree clean.
- Steps:
  1. Determine latest production tag (`git describe --tags --abbrev=0 --match 'v*.*.*' --exclude '*-rc*'`).
  2. `git checkout -b fix/<slug> <latest-tag>` (off tag, not main, to isolate fix).
  3. Hand off to user for fix + tests.
  4. On user signal "done", verify tests green.
  5. Add CHANGELOG entry under `[Unreleased]` → `### Fixed`.
  6. `git commit -s -m "fix(scope): <subject>"`.
  7. `git push -u origin fix/<slug>`; `gh pr create`.
  8. On merge: hand off to `release-cut` with patch bump (X.Y.Z+1).
- Refuses if working tree dirty or current branch is not `main` (after step 1).

#### `feature-flow`
- Trigger: `/feature <slug> "<intent>"`.
- Thin orchestrator. Steps:
  1. Invoke `openspec-propose` skill with intent.
  2. `git checkout -b feature/<slug>`.
  3. Invoke `openspec-apply` skill in a loop over tasks.md.
  4. Run verify (tests, lint, types).
  5. `git push -u origin feature/<slug>`; `gh pr create --fill` (body from proposal.md summary).
  6. On merge: invoke `openspec-archive` skill.
- Does NOT reimplement any openspec-* judgment; defers to them.

### Authoring constraint

Each skill is created/updated by a **dispatched subagent** using the local `writing-skills` helper at `/Users/artem.veduta/.claude/plugins/cache/claude-plugins-official/superpowers/5.1.0/skills/writing-skills` (per repo CLAUDE.md). Main thread never edits a SKILL.md directly. Subagent receives: skill name, design section above, target path under `.claude/skills/<name>/SKILL.md`.

### Trigger style

Each `SKILL.md` frontmatter declares:
- `name: <kebab-case>`
- `description: <one-line, includes natural-language phrases for auto-invoke matching>` (e.g. "cut a release", "publish to PyPI", "start a feature")
- Slash command derived from skill name (Claude Code convention).

Both slash and description matching active. No cost to enabling both.

---

## 13. Interactive Provider Installer (`tutor init`)

### User flow

The happy path should feel like this:

```bash
uv tool install lingo-loop
tutor init
```

Then:

```text
Lingo Loop setup

Detected providers
  [x] Claude Code  installed    ~/.claude
  [x] Codex        detected     ~/.codex
  [ ] Hermes       not found    install Hermes first
  [ ] OpenClaw     not found    install OpenClaw first

Install providers:
  > Claude Code
    Codex
    Hermes
    OpenClaw

Plan
  Claude Code: install plugin package, verify tutor doctor

Apply? [y/N]
```

The command name stays `tutor init` because `tutor` is the current installed console script and maps to user intent better than the distribution name. If `rename-lingo-loop` later adds a `lingo-loop` console alias, it can point to the same command; this change does not require the alias.

### Flow shape

```text
GET PACKAGE              RUN INIT                 CHOOSE PROVIDER
────────────             ─────────                ───────────────
uv tool install          tutor init               Claude / Codex /
lingo-loop                    │                   Hermes / OpenClaw
                              ▼                         │
                       detect host CLIs                  ▼
                       and config roots           build install plan
                              │                         │
                              ▼                         ▼
                         show status             apply selected steps
                              │                         │
                              └──────────────┬──────────┘
                                             ▼
                                      verify + summary
```

### Scope boundary

`tutor init` is distribution glue only. It may:

- Read supported host metadata from the existing `HostId` / `HostSetupTarget` registry.
- Inspect host CLI availability and conventional config/plugin directories.
- Copy or register managed plugin/profile files for selected providers.
- Run provider verification plus existing `tutor doctor`.
- Print repair guidance and links to `docs/install/<host>.md`.

It must not:

- Install Claude Code, Codex, Hermes, or OpenClaw themselves.
- Prompt for or store API keys.
- Write learner profile YAML, SQLite history, sessions, checkpoints, memories, logs, or host secrets.
- Change tutor skills, pedagogy, SRS, feedback, lifecycle persistence, or profile schemas.

### Provider installer contract

Use composition: one small installer per provider behind a shared Protocol. The CLI orchestrates; provider modules own host-specific paths and commands.

```python
class ProviderInstaller(Protocol):
    id: HostId
    display_name: str

    def detect(self) -> ProviderStatus: ...
    def plan(self, request: InitRequest) -> InitPlan: ...
    def apply(self, plan: InitPlan) -> InitResult: ...
    def verify(self) -> InitResult: ...
    def uninstall_hint(self) -> str: ...
```

Keep the source of truth DRY:

- Supported providers come from `language_tutor.adapters.base.supported_host_targets()`.
- Capabilities come from `language_tutor.adapters.registry.capability_profile_for()`.
- New installer-specific status/result contracts live in `schemas.py` and get JSON schema mirrors.
- Host-specific file operations live in provider installer modules, not in `cli.py`.

### CLI modes

| Mode | Command | Purpose |
|---|---|---|
| Interactive | `tutor init` | Detect providers, menu-select, confirm before write. |
| Single provider | `tutor init --provider claude` | Install/repair one provider. |
| Multi-provider | `tutor init --provider claude --provider codex` | Install/repair selected providers. |
| CI/headless | `tutor init --provider codex --yes --json` | No prompts; machine-readable result. |
| Audit only | `tutor init --dry-run --json` | Detect and plan; no writes. |

`--provider` validates against `claude|codex|hermes|openclaw`. Unsupported values fail before any write. `--yes` is required for non-interactive writes when stdin is not a TTY.

### Status model

Each provider returns one status:

| Status | Meaning | Write allowed |
|---|---|---|
| `available` | Host CLI/config root detected, not installed yet. | Yes |
| `installed` | Managed files already present and verify passes. | No-op |
| `needs-repair` | Some managed files missing/stale. | Yes |
| `blocked` | Host CLI/config root missing or unsupported version. | No |
| `unknown` | Detection failed safely. | No unless user passes explicit provider + confirm |

The final summary groups providers by status and always includes the next command, e.g. `open Claude Code and run /plugin reload` or `restart Codex`.

### Dependency decision

Use existing `click` for prompts, colors, and tables in v0.1. Do not add `rich`, `textual`, `questionary`, or `prompt_toolkit` yet.

| Option | Pros | Cons | Decision |
|---|---|---|---|
| `click` only | Already installed, tiny scope, works in plain terminals and CI. | Less polished than a TUI library. | Use now. |
| `rich` | Better tables/progress output, mature. | New dependency for mostly cosmetic output. | Defer until install UX needs it. |
| `textual` | Full TUI possible. | Too heavy for one setup menu. | Reject for v0.1. |
| `questionary` | Nice prompts. | Extra dependency and less value than existing Click. | Reject for v0.1. |

### Provider write strategy

| Provider | Installer action |
|---|---|
| Claude Code | Register/copy the shipped Claude plugin package, then verify manifest visibility and `tutor doctor`. |
| Codex | Register/copy the local marketplace plugin entry and `.codex-plugin/plugin.json`, then verify Codex plugin discovery path. |
| Hermes | Install or update the shipped `hermes-profile/distribution.yaml` profile reference, then verify profile metadata points to `https://github.com/artemVeduta/lingo-loop`. |
| OpenClaw | Prepare/install the shipped `openclaw-plugin` package through the host CLI when available; otherwise block with docs link and exact missing CLI message. |

If a host has no documented non-interactive install command, the provider action may stop at "prepared" and print the exact manual host command from the host setup profile. That is still better than making users read source.

### Tests and gates

- Unit tests for provider detection/planning with fake filesystem + fake command runner.
- Contract tests for `InitRequest`, `InitPlan`, `ProviderStatus`, and `InitResult` JSON.
- CLI integration tests for interactive defaults, `--provider`, `--yes`, `--dry-run`, invalid provider, and blocked host.
- Idempotence test: running the same provider install twice returns `installed`/no-op on the second run.
- Privacy test: installer never writes under learner profile/history/session/checkpoint paths.
- Docs test/update: README quick start and each `docs/install/<host>.md` use `tutor init` as the primary path, with manual host docs as fallback.
