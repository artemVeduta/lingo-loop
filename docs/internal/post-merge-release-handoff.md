# Post-Merge Release Handoff — PR #12 (OSS distribution)

What to do **after PR #12 merges to `main`**. Goal: publish `lingo-loop` to PyPI
via the existing automated workflow, then flip the install docs from
source-install to `uv tool install lingo-loop`.

Pre-merge work tracked separately in `pr12-merge-checklist.md`. Do that first.

---

## Context — what is already prepared

- `.github/workflows/workflow.yml` — automated publish. Trusted Publisher bound
  to PyPI for `lingo-loop`. **Do not rename the file** (PyPI publisher config is
  filename-bound).
- Tag routing:
  - `vX.Y.Z`          → `pypi` env → pypi.org → GitHub Release
  - `vX.Y.Z-rc.N`     → `testpypi` env → test.pypi.org → prerelease
  - `-alpha.N` / `-beta.N` → testpypi
- `pyproject.toml`: name `lingo-loop`, version `0.1.0`.
- `scripts/version-guard.sh` enforces tag == pyproject version.

As of handoff: **no git tags, package 404 on PyPI and TestPyPI.** Nothing
published yet. The "PyPI publish is pending; install from source" line in the
install docs is therefore still correct until step 3 below.

---

## Step 1 — Confirm main is releasable

```bash
git checkout main && git pull
git tag -l                      # expect: still empty
./scripts/version-guard.sh v0.1.0   # tag matches pyproject 0.1.0
uv build                        # sdist + wheel, no errors
uv run pytest                   # green on main
```

- [ ] `main` has the merged PR #12 content
- [ ] version-guard passes for `v0.1.0`
- [ ] build + tests green on `main`

> Tag MUST point at a `main` commit. Never tag a feature branch — the workflow
> fires on any `v*.*.*` tag regardless of branch.

## Step 2 — Publish to PyPI

Use the `release-tag` skill (`/release-tag`) or do manually.

> RC dry-run on TestPyPI was dropped: `scripts/version-guard.sh` (run by the
> workflow on every tag) requires `pyproject.toml` version to equal the tag, so
> an `-rc.N` tag needs a tagged commit carrying `version = "0.1.0-rc.1"`. The
> repo has no such bump and adding one is more plumbing than the dry-run is
> worth here. `pyproject.toml` is already `0.1.0`, so the real tag below passes
> the guard with no changes. If a future release needs a TestPyPI rehearsal,
> bump `pyproject.toml` to the `-rc.N` version via a release PR first.

```bash
git tag v0.1.0 && git push origin v0.1.0
```

- [ ] Workflow `publish (pypi)` job green
- [ ] https://pypi.org/project/lingo-loop/ shows 0.1.0
- [ ] GitHub Release created with attached dist
- [ ] Clean-venv smoke: `uv tool install lingo-loop` → `tutor doctor --json` → `status: ok`

## Step 3 — Flip install docs (only after PyPI 200)

Once `lingo-loop` is live on pypi.org, replace the source-install block in all
four docs. Current block:

```bash
# PyPI publish is pending; install from source for now:
uv tool install git+https://github.com/artemVeduta/lingo-loop
tutor doctor --json
```

Replace with:

```bash
uv tool install lingo-loop
tutor doctor --json
```

Files (Step 0 / install-CLI block, line ~13 each):

- [ ] `docs/install/claude.md`
- [ ] `docs/install/codex.md`
- [ ] `docs/install/hermes.md`
- [ ] `docs/install/openclaw.md`

Keep `git+https://...` as a documented "install from source" fallback if
desired, but it must no longer be the primary path.

Also clear when verified:
- [ ] Remove/settle "Verification pending" banners (line 3 each) once confirmed
  against a host CLI release — separate from PyPI publish.
- [ ] Screenshot / cast "pending" placeholders → see `launch-checklist.md`.

## Step 4 — Verify docs guard + ship

```bash
uv run pytest tests/docs/test_install_docs.py
```

- [ ] Doc tests pass with new install command
- [ ] Open doc-flip PR, merge to main

---

## Rollback / gotchas

- PyPI is **immutable** — `0.1.0` cannot be re-uploaded. A bad release needs
  `0.1.1`. With the RC dry-run dropped (see Step 2), the local `uv build` +
  `uv run pytest` on `main` are the only pre-publish gates — run them.
- If publish job fails on auth → check Trusted Publisher entry on PyPI still
  points at `workflow.yml` in this repo.
