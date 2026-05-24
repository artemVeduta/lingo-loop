# Releasing

This runbook describes how to cut a release of this project.

## Versioning policy

This project follows [Semantic Versioning 2.0.0](https://semver.org/spec/v2.0.0.html).

- `MAJOR.MINOR.PATCH` for stable releases.
- While on `0.x`, **minor** releases MAY contain breaking changes (SemVer §4).
  Document every break under `### Changed` in `CHANGELOG.md` with a
  `BREAKING:` prefix.
- Pre-releases use `-rc.N` or `-alpha.N` suffixes (e.g. `v0.2.0-rc.1`).

Git tags are always prefixed with `v` and match
`^v(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)(-[0-9A-Za-z.-]+)?$`.

## Authorized releaser

Releases are cut by the maintainer listed in `pyproject.toml` under
`[project].authors`. For v0.1 this is Artem Veduta
(`veduta.artem20@gmail.com`).

## Automated procedure (primary)

The publish step is automated via `.github/workflows/workflow.yml`, triggered
on any `v*.*.*` tag push. The workflow builds sdist + wheel with `uv build`
and publishes to PyPI (or TestPyPI for `-rc.N` / `-alpha.N` / `-beta.N` tags)
via PyPI Trusted Publishing (OIDC). No API token is stored in repo secrets.

The release-lifecycle Claude Code skills live under
[`.claude/skills/`](.claude/skills/README.md). The three involved in a
standard release are:

- `/pre-release-checks` — verify the working tree, CHANGELOG, build, and gates
  before cutting anything. Read-only.
- `/release-cut X.Y.Z` — open a `chore/release-X.Y.Z` PR that promotes the
  CHANGELOG and bumps `pyproject.toml`. Invokes
  [`scripts/changelog-promote.sh`](scripts/changelog-promote.sh).
- `/release-tag X.Y.Z` — after the release PR merges, cut and push the
  annotated tag. Invokes [`scripts/version-guard.sh`](scripts/version-guard.sh)
  to fail fast on a tag/`pyproject.toml` mismatch. The tag push triggers
  `workflow.yml`.

```
AUTOMATED RELEASE FLOW
───────────────────────────────────────────────
  1. /pre-release-checks       (skill, read-only verification)
  2. /release-cut X.Y.Z        (skill -> PR with CHANGELOG + version bump)
  3. squash-merge release PR   (CI green required)
  4. /release-tag X.Y.Z        (skill -> annotated tag + push)
  5. workflow.yml runs         (build, version-guard, publish, GH Release)
  6. verify                    (PyPI page, GitHub Release, attestations)
```

### Tag routing

| Tag pattern                                    | Environment | Index            | GH Release   |
|------------------------------------------------|-------------|------------------|--------------|
| `vX.Y.Z`                                       | `pypi`      | pypi.org         | release      |
| `vX.Y.Z-rc.N` / `vX.Y.Z-alpha.N` / `-beta.N`   | `testpypi`  | test.pypi.org    | prerelease   |

### CHANGELOG promotion

`scripts/changelog-promote.sh X.Y.Z` rewrites `CHANGELOG.md` with this exact
diff (run as part of `release-cut`, but valid to run by hand):

```diff
-## [Unreleased]
+## [Unreleased]
+
+### Added
+
+### Changed
+
+### Fixed
+
+### Removed
+
+## [X.Y.Z] - YYYY-MM-DD
```

### Post-release verification

- The GitHub Actions run for the tag is green.
- `https://pypi.org/project/lingo-loop/X.Y.Z/` (or test.pypi.org for prereleases) shows the new artifacts.
- Sigstore/PEP 740 attestations appear under "Provenance" on the release page.
- `gh release view vX.Y.Z` shows the release with auto-generated notes.
- The repository's **Releases** sidebar lists `vX.Y.Z` as the latest.
- `CHANGELOG.md` on `main` has both the new `[X.Y.Z]` section and an empty
  `[Unreleased]` block on top.

## Break-glass procedure (manual)

Use this path only when GitHub Actions or PyPI Trusted Publishing is
unavailable. The automated flow above is the supported path.

```
RELEASE FLOW (manual break-glass)
───────────────────────────────────────────────
  1. open release branch    chore/release-X.Y.Z
  2. promote CHANGELOG       [Unreleased] -> [X.Y.Z] - YYYY-MM-DD
                             insert new empty [Unreleased] on top
  3. bump pyproject.toml     version = "X.Y.Z" (if not auto-derived)
  4. PR -> squash-merge to main -> CI green
  5. on main, annotated tag  git tag -a vX.Y.Z -m "release X.Y.Z"
                             git push origin vX.Y.Z
  6. gh release create       gh release create vX.Y.Z --notes-from-tag
  7. verify                  gh release view vX.Y.Z, repo Releases sidebar
```

### Step-by-step

#### 1. Open a release branch

```bash
git checkout main && git pull --ff-only
git checkout -b chore/release-X.Y.Z
```

#### 2. Promote the CHANGELOG

Open `CHANGELOG.md` and apply this exact diff:

```diff
-## [Unreleased]
+## [Unreleased]
+
+### Added
+
+### Changed
+
+### Fixed
+
+### Removed
+
+## [X.Y.Z] - YYYY-MM-DD
```

In words: rename the existing `## [Unreleased]` heading to
`## [X.Y.Z] - YYYY-MM-DD` (using today's date in `YYYY-MM-DD`), and insert a
fresh empty `## [Unreleased]` block with empty `Added`, `Changed`, `Fixed`,
`Removed` subsections on top.

Trim any subsections that have no entries in the released version.

#### 3. Bump the version

Update `version = "X.Y.Z"` under `[project]` in `pyproject.toml` if it is not
already correct (and not derived automatically).

#### 4. Open the release PR

```bash
git add CHANGELOG.md pyproject.toml
git commit -s -m "chore(release): X.Y.Z"
git push -u origin chore/release-X.Y.Z
gh pr create --fill
```

Wait for CI to go green and squash-merge.

#### 5. Cut the tag

On `main`, after the release PR has merged:

```bash
git checkout main && git pull --ff-only
git tag -a vX.Y.Z -m "release X.Y.Z"        # add -s to sign if a key is configured
git push origin vX.Y.Z
```

Use `git tag -s` instead of `-a` when a signing key is available on the
release machine.

#### 6. Publish the GitHub release

```bash
gh release create vX.Y.Z --notes-from-tag
```

#### 7. Post-release verification

- `gh release view vX.Y.Z` shows the release with the correct notes.
- The repository's **Releases** sidebar lists `vX.Y.Z` as the latest.
- `git tag -l 'v*'` includes the new tag.
- `CHANGELOG.md` on `main` has both the new `[X.Y.Z]` section and an empty
  `[Unreleased]` block on top.

