#!/usr/bin/env bash
# Compare a git tag of the form vX.Y.Z[-suffix] against the version declared
# in pyproject.toml [project].version. Exits non-zero on mismatch.
# Used by the publish workflow before `uv build`.
set -euo pipefail

TAG="${1:?usage: version-guard.sh <tag>}"
TAG_VER="${TAG#v}"

PYPROJ_VER=$(python3 -c "import tomllib; print(tomllib.load(open('pyproject.toml','rb'))['project']['version'])")

if [[ "$TAG_VER" != "$PYPROJ_VER" ]]; then
  echo "::error::tag ${TAG} (${TAG_VER}) != pyproject.toml version (${PYPROJ_VER})" >&2
  exit 1
fi

echo "version-guard: OK (${TAG_VER})"
