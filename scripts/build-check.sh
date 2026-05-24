#!/usr/bin/env bash
# Build sdist + wheel via `uv build` then validate with `twine check`.
# Exits non-zero on any build or metadata problem. Used by pre-release-checks.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

rm -rf dist
uv build

# twine is not a runtime/dev dep; fetch on demand via uvx.
uvx --from twine twine check dist/*

echo "build-check: OK"
