#!/usr/bin/env bash
# Promote CHANGELOG.md [Unreleased] section to a numbered release.
# Renames the existing `## [Unreleased]` heading to `## [X.Y.Z] - YYYY-MM-DD`
# (today, UTC) and inserts a fresh empty `## [Unreleased]` block on top with
# Added / Changed / Fixed / Removed subsections.
#
# Idempotent guard: refuses to run if `## [X.Y.Z]` already exists in the file.
#
# Usage: scripts/changelog-promote.sh X.Y.Z [path-to-changelog]
set -euo pipefail

VERSION="${1:?usage: changelog-promote.sh X.Y.Z [changelog-path]}"
FILE="${2:-CHANGELOG.md}"

if [[ ! "$VERSION" =~ ^[0-9]+\.[0-9]+\.[0-9]+(-[0-9A-Za-z.-]+)?$ ]]; then
  echo "error: version '${VERSION}' is not SemVer" >&2
  exit 2
fi

if [[ ! -f "$FILE" ]]; then
  echo "error: ${FILE} not found" >&2
  exit 2
fi

if grep -qE "^## \[${VERSION//./\\.}\]" "$FILE"; then
  echo "error: ${FILE} already has a [${VERSION}] section" >&2
  exit 2
fi

if ! grep -qE '^## \[Unreleased\]' "$FILE"; then
  echo "error: ${FILE} has no [Unreleased] section to promote" >&2
  exit 2
fi

TODAY=$(date -u +%Y-%m-%d)

TMP=$(mktemp)
trap 'rm -f "$TMP"' EXIT

awk -v ver="$VERSION" -v date="$TODAY" '
  !done && /^## \[Unreleased\]/ {
    print "## [Unreleased]"
    print ""
    print "### Added"
    print ""
    print "### Changed"
    print ""
    print "### Fixed"
    print ""
    print "### Removed"
    print ""
    print "## [" ver "] - " date
    done = 1
    next
  }
  { print }
' "$FILE" > "$TMP"

mv "$TMP" "$FILE"
trap - EXIT

echo "changelog-promote: [Unreleased] -> [${VERSION}] - ${TODAY}"
